import re
from datetime import date as dtdate, time as dttime
from urllib.parse import quote
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, Response, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Cook, Listing, Message
from .replies import reply
from .llm import parse_listing, answer_help

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ASK_KEY = {
    "dish": "ASK_DISH",
    "portions": "ASK_PORTIONS",
    "price_inr": "ASK_PRICE",
    "date": "ASK_DATE",
    "pickup_window": "ASK_PICKUP",
}
FIELDS = ("dish", "portions", "price_inr", "date", "pickup_window")
_DRAFTS: dict[int, dict] = {}

PRICE_WORDS = re.compile(r"\b(price|rate|cost|paisa|rupay|rupee|dam|bhav|kitna)\b", re.IGNORECASE)


def _parse_pickup(window: str) -> tuple[dttime, dttime]:
    a, b = window.split("-", 1)
    return dttime.fromisoformat(a.strip()), dttime.fromisoformat(b.strip())


def _find_cook(db: Session, phone: str) -> Cook | None:
    return db.scalar(select(Cook).where(Cook.phone == phone))


def _price_hint(db: Session, cook: Cook, text: str) -> str:
    if not PRICE_WORDS.search(text):
        return ""
    tokens = {w.lower() for w in re.findall(r"[A-Za-z]+", text) if len(w) > 2}
    tokens -= {"kitna", "price", "rate", "cost", "paisa", "rupay", "rupee",
               "dam", "bhav", "the", "and", "rakhu", "milega", "mera", "mujhe"}
    if not tokens:
        return ""
    listings = db.scalars(select(Listing).where(Listing.region == cook.area)).all()
    prices = []
    for l in listings:
        dish_tokens = {w.lower() for w in re.findall(r"[A-Za-z]+", l.dish)}
        if dish_tokens & tokens:
            prices.append(l.price_inr)
    if not prices:
        return ""
    return f"Similar dishes in {cook.area} are priced {min(prices)}-{max(prices)} INR per portion."


def handle_cook_text(db: Session, cook: Cook, text: str) -> str:
    db.add(Message(cook_id=cook.id, direction="in", channel=cook.channel, text=text))
    db.commit()

    data = parse_listing(text)

    if data.get("intent") == "question":
        hint = _price_hint(db, cook, text)
        answer = answer_help(text, channel=cook.channel, price_hint=hint)
        reply_text = answer or reply("HELP_FALLBACK", channel=cook.channel)
        db.add(Message(cook_id=cook.id, direction="out", channel=cook.channel, text=reply_text))
        db.commit()
        return reply_text

    if data.get("intent") == "other":
        reply_text = reply("HELP_FALLBACK", channel=cook.channel)
        db.add(Message(cook_id=cook.id, direction="out", channel=cook.channel, text=reply_text))
        db.commit()
        return reply_text

    draft = _DRAFTS.setdefault(cook.id, {})
    for f in FIELDS:
        if draft.get(f) in (None, "") and data.get(f) not in (None, ""):
            draft[f] = data[f]
    if draft.get("pickup_window") in (None, "") and cook.default_pickup:
        draft["pickup_window"] = cook.default_pickup
    missing = [f for f in FIELDS if draft.get(f) in (None, "")]

    if missing:
        key = ASK_KEY.get(missing[0], "ASK_DISH")
        reply_text = reply(key, channel=cook.channel)
    elif int(draft["portions"]) > cook.batch_limit:
        reply_text = reply("OVER_LIMIT", channel=cook.channel, limit=cook.batch_limit)
        _DRAFTS.pop(cook.id, None)
    else:
        start, end = _parse_pickup(draft["pickup_window"])
        listing = Listing(
            cook_id=cook.id, dish=draft["dish"], region=cook.area,
            portions=int(draft["portions"]), price_inr=int(draft["price_inr"]),
            date=dtdate.fromisoformat(draft["date"]),
            pickup_start=start, pickup_end=end, status="open",
        )
        db.add(listing)
        db.commit()
        reply_text = reply("CONFIRM", channel=cook.channel,
                           dish=listing.dish, portions=listing.portions,
                           price_inr=listing.price_inr, date=listing.date.isoformat(),
                           pickup=draft["pickup_window"])
        _DRAFTS.pop(cook.id, None)
    db.add(Message(cook_id=cook.id, direction="out", channel=cook.channel, text=reply_text))
    db.commit()
    return reply_text


@router.get("/phone", response_class=HTMLResponse)
def phone_page(request: Request, cook_phone: str | None = None, db: Session = Depends(get_db)):
    cooks = db.scalars(select(Cook).order_by(Cook.id)).all()
    selected = db.scalar(select(Cook).where(Cook.phone == cook_phone)) if cook_phone else (cooks[0] if cooks else None)
    messages = []
    if selected:
        messages = db.scalars(select(Message).where(Message.cook_id == selected.id)
                              .order_by(Message.id)).all()
    return templates.TemplateResponse("phone.html", {
        "request": request, "cooks": cooks, "selected": selected, "messages": messages,
    })


@router.post("/phone/sms")
def phone_sms(cook_phone: str = Form(...), text: str = Form(...), db: Session = Depends(get_db)):
    cook = _find_cook(db, cook_phone)
    if not cook:
        return JSONResponse({"reply_text": reply("NOT_REGISTERED", channel="sms")})
    reply_text = handle_cook_text(db, cook, text)
    return JSONResponse({"reply_text": reply_text})


@router.post("/sms/incoming")
async def sms_incoming(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    phone = (form.get("From") or "").strip()
    body = (form.get("Body") or "").strip()
    cook = _find_cook(db, phone)
    reply_text = reply("NOT_REGISTERED", channel="sms") if not cook else handle_cook_text(db, cook, body)
    xml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{reply_text}</Message></Response>"
    return Response(content=xml, media_type="application/xml")


@router.get("/register-cook", response_class=HTMLResponse)
def register_cook_form(request: Request):
    return templates.TemplateResponse("register_cook.html", {"request": request})


@router.post("/register-cook", response_class=HTMLResponse)
def register_cook_submit(request: Request,
                         name: str = Form(...), phone: str = Form(...), area: str = Form(...),
                         address: str = Form(...), channel: str = Form(...),
                         default_pickup: str = Form(...),
                         db: Session = Depends(get_db)):
    phone = phone.strip()
    channel = channel if channel in ("sms", "voice") else "sms"
    if db.scalar(select(Cook).where(Cook.phone == phone)):
        return templates.TemplateResponse("register_cook.html",
            {"request": request, "error": "A cook with that phone already exists.",
             "name": name, "phone": phone, "area": area, "address": address,
             "channel": channel, "default_pickup": default_pickup}, status_code=400)
    cook = Cook(name=name, phone=phone, area=area, address=address, channel=channel,
                default_pickup=default_pickup, batch_limit=5, completed_orders=0)
    db.add(cook)
    db.commit()
    db.refresh(cook)
    welcome = reply("WELCOME", channel=cook.channel)
    db.add(Message(cook_id=cook.id, direction="out", channel=cook.channel, text=welcome))
    db.commit()
    return RedirectResponse(f"/phone?cook_phone={quote(cook.phone, safe='')}", status_code=303)
