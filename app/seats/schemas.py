from pydantic import BaseModel


class SeatOut(BaseModel):
    seat_no: str
    grade: str
    price: int
    status: str
    occupant_user_id: str | None

class SeatListOut(BaseModel):
    event_id: str
    seats: list[SeatOut]