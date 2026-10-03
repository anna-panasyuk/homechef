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
from .pages import router as pages_router
from .orders import router as orders_router
from .cook import router as cook_router


def init_db() -> None:
    for _ in range(30):
        try:
            Base.metadata.create_all(engine)
            break
        except OperationalError:
            time.sleep(1)
    else:
        Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.scalar(select(models.Cook.id).limit(1)):
            seed = Path("scripts/seed.sql").read_text()
            for stmt in [s.strip() for s in seed.split(";") if s.strip()]:
                db.execute(text(stmt))
            db.commit()


app = FastAPI(title="HomeChef")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "dev-secret"))
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()

app.include_router(pages_router)
app.include_router(orders_router)
app.include_router(cook_router)
