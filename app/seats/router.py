from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.seats.schemas import SeatListOut, SeatOut
from app.seats.service import get_seat_list, get_seat_detail

router = APIRouter()


@router.get("/events/{event_id}/seats",
            response_model=SeatListOut,
            summary="공연별 좌석 목록 조회",
            description="공연의 전체 좌석과 각 좌석의 상태·가격·점유자를 조회합니다.",)
def list_seats(event_id: str, db: Session = Depends(get_db)) -> SeatListOut:
    return get_seat_list(db, event_id)
@router.get("/events/{event_id}/seats/{seat_no}",
            response_model=SeatOut,
            summary="공연의 각 좌석 조회",
            description="각 좌석의 상태·가격·점유자를 조회합니다.",
            )
def get_seat(event_id: str, seat_no: str, db: Session = Depends(get_db)) -> SeatOut:
    return get_seat_detail(db, event_id, seat_no)