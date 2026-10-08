from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("total_amount > 0", name="ck_reservations_total_amount_positive"),
        Index("ix_reservations_user", "user_id"),
        Index("ix_reservations_event", "event_id"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    hold_id: Mapped[str] = mapped_column(ForeignKey("holds.id"), nullable=False, unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    total_amount: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)