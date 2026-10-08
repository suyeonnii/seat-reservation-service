from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

class Event(Base):
    __tablename__ = 'events'

    id:Mapped[str] = mapped_column(primary_key=True)
    title:Mapped[str] = mapped_column(nullable=False)
    venue:Mapped[str] = mapped_column(nullable=False)
    starts_at:Mapped[datetime] = mapped_column(nullable=False)

class EventGradePrice(Base):
    __tablename__ = 'event_grade_prices'
    __table_args__ = (
        CheckConstraint("grade IN ('VIP', 'R', 'S')", name="ck_event_grade_prices_grade"),
        CheckConstraint("price > 0", name="ck_event_grade_prices_price_positive")
    )
    event_id:Mapped[str] = mapped_column(ForeignKey('events.id'),primary_key=True)
    grade:Mapped[str] = mapped_column(primary_key=True)
    price:Mapped[int] = mapped_column(nullable=False)