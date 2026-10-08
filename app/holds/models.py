from datetime import datetime, timedelta

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.config import HOLD_TTL_MINUTES

class Hold(Base):
    __tablename__ = "holds"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','CANCELLED','CONVERTED','EXPIRED')",
                        name="ck_holds_status"),
        Index("ix_holds_user_event_status","user_id", "event_id","status"),
        Index("ix_holds_event_status","event_id","status"),
        Index("ix_holds_status_created","status","created_at"),
    )

    id:Mapped[str] =mapped_column(primary_key=True)
    user_id:Mapped[str] =mapped_column(ForeignKey("users.id"),nullable=False)
    event_id:Mapped[str] =mapped_column(ForeignKey("events.id"),nullable=False)
    status:Mapped[str] =mapped_column(nullable=False)
    created_at:Mapped[datetime] =mapped_column(nullable=False)

    def is_active(self, now: datetime) -> bool:
        if self.status != "ACTIVE":
            return False
        return now < self.created_at + timedelta(minutes=HOLD_TTL_MINUTES)


class HoldItem(Base):
    __tablename__ = "hold_items"
    __table_args__ = (
        CheckConstraint("price_snapshot > 0", name="ck_hold_items_price_positive"),
    )

    hold_id:Mapped[str] =mapped_column(ForeignKey("holds.id"),primary_key=True)
    seat_id:Mapped[int] =mapped_column(ForeignKey("seats.id"),primary_key=True)
    price_snapshot:Mapped[int] = mapped_column(nullable=False)
