from datetime import datetime, date, time
from sqlalchemy import String, Integer, Date, Time, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(32), unique=True)


class Cook(Base):
    __tablename__ = "cooks"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(32), unique=True)
    area: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    channel: Mapped[str] = mapped_column(String(10))  # sms | voice
    batch_limit: Mapped[int] = mapped_column(Integer, default=5)
    completed_orders: Mapped[int] = mapped_column(Integer, default=0)


class Listing(Base):
    __tablename__ = "listings"
    id: Mapped[int] = mapped_column(primary_key=True)
    cook_id: Mapped[int] = mapped_column(ForeignKey("cooks.id"))
    dish: Mapped[str] = mapped_column(String(120))
    region: Mapped[str] = mapped_column(String(80))
    portions: Mapped[int] = mapped_column(Integer)
    price_inr: Mapped[int] = mapped_column(Integer)
    date: Mapped[date] = mapped_column(Date)
    pickup_start: Mapped[time] = mapped_column(Time)
    pickup_end: Mapped[time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(10), default="open")  # open | closed

    cook: Mapped["Cook"] = relationship(lazy="joined")


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    qty: Mapped[int] = mapped_column(Integer)
    amount_inr: Mapped[int] = mapped_column(Integer)
    pickup_slot: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|paid|closed|handed_over

    listing: Mapped["Listing"] = relationship(lazy="joined")
    user: Mapped["User"] = relationship(lazy="joined")


class Payout(Base):
    __tablename__ = "payouts"
    id: Mapped[int] = mapped_column(primary_key=True)
    cook_id: Mapped[int] = mapped_column(ForeignKey("cooks.id"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    kind: Mapped[str] = mapped_column(String(16))  # advance | settlement
    amount_inr: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    cook_id: Mapped[int] = mapped_column(ForeignKey("cooks.id"))
    direction: Mapped[str] = mapped_column(String(4))  # in | out
    channel: Mapped[str] = mapped_column(String(10))  # sms | voice
    text: Mapped[str] = mapped_column(String(2000))
    audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
