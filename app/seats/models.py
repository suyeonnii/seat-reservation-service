from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

class Seat(Base):
    __tablename__ = 'seats'
    __table_args__ = (
        UniqueConstraint("event_id", "seat_no", name="up_seats_event_seat_no"),
        CheckConstraint("grade IN ('VIP','R','S')", name="ck_seats_grade"),
        CheckConstraint("status IN ('AVAILABLE','HELD','RESERVED')", name="ck_seats_status"),
        Index("ix_seats_hold", "hold_id")
    )

    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    event_id:Mapped[str]=mapped_column(ForeignKey('events.id'), nullable=False)
    seat_no:Mapped[str]=mapped_column(nullable=False)
    grade:Mapped[str]=mapped_column(nullable=False)
    status:Mapped[str]=mapped_column(nullable=False, default="AVAILABLE")
    hold_id:Mapped[str | None]=mapped_column(ForeignKey('holds.id'), nullable=True)