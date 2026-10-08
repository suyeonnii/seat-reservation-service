from datetime import datetime

from pydantic import BaseModel

from app.holds.schemas import HoldSeatOut


class ReservationCreate(BaseModel):
    hold_id: str


class ReservationOut(BaseModel):
    reservation_id: str
    hold_id: str
    user_id: str
    event_id: str
    total_amount: int
    seats: list[HoldSeatOut]
    created_at: datetime
    message: str | None = None


class ReservationListOut(BaseModel):
    reservations: list[ReservationOut]