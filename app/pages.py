from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import User, Listing, Order
from .auth import hash_password, verify_password

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def current_user(request: Request, db: Session) -> User | None:
    uid = request.session.get("user_id")
    return db.get(User, uid) if uid else None


@router.get("/", response_class=HTMLResponse)
def index(request: Request, area: str | None = None, db: Session = Depends(get_db)):
    q = select(Listing).where(Listing.status == "open", Listing.portions > 0).order_by(Listing.date, Listing.id)
    listings = db.scalars(q).all()
    if area:
        listings = [l for l in listings if l.cook.area.lower() == area.lower()]
    return templates.TemplateResponse("index.html", {"request": request, "listings": listings, "area": area})


@router.get("/dish/{listing_id}", response_class=HTMLResponse)
def dish(request: Request, listing_id: int, db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    return templates.TemplateResponse("dish.html", {"request": request, "listing": listing})


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, email: str = Form(...), password: str = Form(...),
                 db: Session = Depends(get_db)):
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html",
            {"request": request, "error": "Invalid email or password", "email": email},
            status_code=400)
    request.session["user_id"] = user.id
    request.session["user"] = {"name": user.name, "email": user.email}
    return RedirectResponse("/", status_code=303)


@router.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup", response_class=HTMLResponse)
def signup_submit(request: Request, name: str = Form(...), email: str = Form(...),
                  password: str = Form(...), db: Session = Depends(get_db)):
    email = email.strip().lower()
    if len(password) < 6:
        return templates.TemplateResponse("signup.html",
            {"request": request, "error": "Password must be at least 6 characters",
             "name": name, "email": email}, status_code=400)
    if db.scalar(select(User).where(User.email == email)):
        return templates.TemplateResponse("signup.html",
            {"request": request, "error": "Email already registered",
             "name": name, "email": email}, status_code=400)
    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    request.session["user"] = {"name": user.name, "email": user.email}
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@router.get("/checkout/{listing_id}", response_class=HTMLResponse)
def checkout_form(request: Request, listing_id: int, db: Session = Depends(get_db)):
    if not current_user(request, db):
        return RedirectResponse("/login", status_code=303)
    listing = db.get(Listing, listing_id)
    return templates.TemplateResponse("checkout.html", {"request": request, "listing": listing})


@router.post("/checkout/{listing_id}")
def checkout_submit(request: Request, listing_id: int, qty: int = Form(...),
                    db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    listing = db.get(Listing, listing_id)
    if not listing or listing.status != "open" or qty < 1 or qty > listing.portions:
        raise HTTPException(400, "Invalid quantity")
    slot = f"{listing.pickup_start.strftime('%H:%M')}-{listing.pickup_end.strftime('%H:%M')}"
    order = Order(user_id=user.id, listing_id=listing.id, qty=qty,
                  amount_inr=qty * listing.price_inr, pickup_slot=slot, status="pending")
    listing.portions -= qty
    db.add(order)
    db.commit()
    db.refresh(order)
    return RedirectResponse(f"/order/{order.id}", status_code=303)


@router.post("/pay/{order_id}")
def pay(request: Request, order_id: int, db: Session = Depends(get_db)):
    user = current_user(request, db)
    order = db.get(Order, order_id)
    if not user or not order or order.user_id != user.id:
        raise HTTPException(404)
    if order.status == "pending":
        order.status = "paid"
        db.commit()
    return RedirectResponse(f"/order/{order.id}", status_code=303)


@router.get("/order/{order_id}", response_class=HTMLResponse)
def order_page(request: Request, order_id: int, db: Session = Depends(get_db)):
    user = current_user(request, db)
    order = db.get(Order, order_id)
    owns = bool(user and order and order.user_id == user.id)
    return templates.TemplateResponse("order.html",
        {"request": request, "order": order, "owns": owns})


@router.get("/my-orders", response_class=HTMLResponse)
def my_orders(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    orders = db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.id.desc())).all()
    return templates.TemplateResponse("my_orders.html", {"request": request, "orders": orders})
