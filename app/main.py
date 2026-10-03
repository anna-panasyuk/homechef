import os
import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from starlette.middleware.sessions import SessionMiddleware

from .db import Base, engine, SessionLocal
from . import models
from .auth import hash_password
from .pages import router as pages_router
from .orders import router as orders_router
from .cook import router as cook_router


def _drop_stale_tables() -> None:
    """Hackathon-grade schema drift fix: drops tables missing new columns.
    Only runs when RESET_DB=1 so we never destroy data by default."""
    if os.getenv("RESET_DB") != "1":
        return
    with engine.begin() as conn:
        rows = conn.execute(text(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema='public'"
        )).all()
        by_table: dict[str, set[str]] = {}
        for t, c in rows:
            by_table.setdefault(t, set()).add(c)
        if "users" in by_table and "email" not in by_table["users"]:
            conn.execute(text("DROP TABLE IF EXISTS orders CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        if "cooks" in by_table and "default_pickup" not in by_table["cooks"]:
            conn.execute(text("DROP TABLE IF EXISTS messages CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS payouts CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS orders CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS listings CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS cooks CASCADE"))


def init_db() -> None:
    for _ in range(30):
        try:
            with engine.connect() as c:
                c.execute(text("SELECT 1"))
            break
        except OperationalError:
            time.sleep(1)
    _drop_stale_tables()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.scalar(select(models.Cook.id).limit(1)):
            seed = Path("scripts/seed.sql").read_text()
            for stmt in [s.strip() for s in seed.split(";") if s.strip()]:
                db.execute(text(stmt))
            db.commit()
        if not db.scalar(select(models.User.id).limit(1)):
            db.add(models.User(name="Rohit Demo", email="rohit@example.com",
                               password_hash=hash_password("demo1234")))
            db.commit()


app = FastAPI(title="HomeChef")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "dev-secret"))
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()

app.include_router(pages_router)
app.include_router(orders_router)
app.include_router(cook_router)
