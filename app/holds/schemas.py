from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class HoldCreate(BaseModel):
    seat_nos: list[str] = Field(min_length=1, max_length=4)

    @field_validator("seat_nos")
    @classmethod
    def no_duplicates(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("좌석 번호가 중복되었습니다.")
        return value

class HoldPatch(BaseModel):
    status: Literal["CANCELLED"]


class HoldSeatOut(BaseModel):
    seat_no: str
    price: int


class HoldOut(BaseModel):
    message: str | None = None
    hold_id: str
    event_id: str
    user_id: str
    status: str
    created_at: datetime
    expires_at: datetime
    seats: list[HoldSeatOut]