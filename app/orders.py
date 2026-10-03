from datetime import date as dtdate
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .db import get_db
from .models import Cook, Listing, Order, Payout, Message
from .replies import reply

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def notify_cook(db: Session, cook: Cook, key: str, **kwargs) -> None:
    text = reply(key, channel=cook.channel, **kwargs)
    db.add(Message(cook_id=cook.id, direction="out", channel=cook.channel, text=text))


def close_orders(db: Session, day: dtdate) -> None:
    listings = db.scalars(select(Listing).where(Listing.date == day, Listing.status == "open")).all()
    by_cook: dict[int, dict] = {}
    for lst in listings:
        paid = db.scalars(select(Order).where(Order.listing_id == lst.id, Order.status == "paid")).all()
        agg = by_cook.setdefault(lst.cook_id, {"count": 0, "amount": 0, "listing_id": lst.id})
        agg["count"] += len(paid)
        agg["amount"] += sum(o.amount_inr for o in paid)
        lst.status = "closed"
        for o in paid:
            o.status = "closed"
    for cook_id, agg in by_cook.items():
        advance = agg["amount"] * 40 // 100
        db.add(Payout(cook_id=cook_id, listing_id=agg["listing_id"], kind="advance", amount_inr=advance))
        notify_cook(db, db.get(Cook, cook_id), "CLOSED_NOTICE", count=agg["count"], advance=advance)
    db.commit()


def handover(db: Session, order_id: int) -> None:
    order = db.get(Order, order_id)
    if not order or order.status != "closed":
        return
    settlement = order.amount_inr * 60 // 100
    db.add(Payout(cook_id=order.listing.cook_id, listing_id=order.listing_id,
                  kind="settlement", amount_inr=settlement))
    order.status = "handed_over"
    cook = order.listing.cook
    cook.completed_orders += 1
    if cook.completed_orders % 5 == 0:
        cook.batch_limit += 5
    notify_cook(db, cook, "HANDOVER_NOTICE", amount=settlement)
    db.commit()


@router.get("/admin", response_class=HTMLResponse)
def admin(request: Request, db: Session = Depends(get_db)):
    orders = db.scalars(select(Order).order_by(Order.id.desc())).all()
    listings = db.scalars(select(Listing).order_by(Listing.date, Listing.id)).all()
    dates = sorted({l.date for l in listings})
    return templates.TemplateResponse("admin.html", {
        "request": request, "orders": orders, "dates": dates,
    })


@router.post("/admin/close-orders")
def admin_close(date: str, db: Session = Depends(get_db)):
    close_orders(db, dtdate.fromisoformat(date))
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/handover/{order_id}")
def admin_handover(order_id: int, db: Session = Depends(get_db)):
    handover(db, order_id)
    return RedirectResponse("/admin", status_code=303)
