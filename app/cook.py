import re
from datetime import date as dtdate, time as dttime
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, Response, JSONResponse
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

PRICE_WORDS = re.compile(r"\b(price|rate|cost|paisa|rupay|rupee|dam|bhav|kitna)\b", re.IGNORECASE)


def _parse_pickup(window: str) -> tuple[dttime, dttime]:
    a, b = window.split("-", 1)
    return dttime.fromisoformat(a.strip()), dttime.fromisoformat(b.strip())


def _get_or_create_cook(db: Session, phone: str) -> tuple[Cook, bool]:
    cook = db.scalar(select(Cook).where(Cook.phone == phone))
    if cook:
        return cook, False
    cook = Cook(name=f"Cook {phone[-4:]}", phone=phone, area="Demo",
                address="Demo address", channel="sms", batch_limit=5, completed_orders=0)
    db.add(cook)
    db.commit()
    db.refresh(cook)
    return cook, True


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


def handle_cook_text(db: Session, cook: Cook, text: str, is_new: bool = False) -> str:
    db.add(Message(cook_id=cook.id, direction="in", channel=cook.channel, text=text))
    db.commit()

    if is_new:
        reply_text = reply("WELCOME", channel=cook.channel)
        db.add(Message(cook_id=cook.id, direction="out", channel=cook.channel, text=reply_text))
        db.commit()
        return reply_text

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

    if data["missing"]:
        key = ASK_KEY.get(data["missing"][0], "ASK_DISH")
        reply_text = reply(key, channel=cook.channel)
    elif int(data["portions"]) > cook.batch_limit:
        reply_text = reply("OVER_LIMIT", channel=cook.channel, limit=cook.batch_limit)
    else:
        start, end = _parse_pickup(data["pickup_window"])
        listing = Listing(
            cook_id=cook.id, dish=data["dish"], region=cook.area,
            portions=int(data["portions"]), price_inr=int(data["price_inr"]),
            date=dtdate.fromisoformat(data["date"]),
            pickup_start=start, pickup_end=end, status="open",
        )
        db.add(listing)
        db.commit()
        reply_text = reply("CONFIRM", channel=cook.channel,
                           dish=listing.dish, portions=listing.portions,
                           price_inr=listing.price_inr, date=listing.date.isoformat(),
                           pickup=data["pickup_window"])
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
    cook, is_new = _get_or_create_cook(db, cook_phone)
    reply_text = handle_cook_text(db, cook, text, is_new=is_new)
    return JSONResponse({"reply_text": reply_text})


@router.post("/sms/incoming")
async def sms_incoming(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    phone = (form.get("From") or "").strip()
    body = (form.get("Body") or "").strip()
    cook, is_new = _get_or_create_cook(db, phone)
    reply_text = handle_cook_text(db, cook, body, is_new=is_new)
    xml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{reply_text}</Message></Response>"
    return Response(content=xml, media_type="application/xml")
