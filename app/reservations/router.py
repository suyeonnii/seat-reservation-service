from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.reservations.schemas import ReservationCreate, ReservationListOut, ReservationOut
from app.reservations.service import create_reservation, get_reservation, list_reservations

router = APIRouter(tags=["reservations"])

@router.post("/reservations",
             response_model=ReservationOut,
             summary="홀드된 좌석 예약 생성.",
             description="홀드된 좌석을 예약합니다."
             )
def post_reservation(
    body: ReservationCreate,
    response: Response,
    x_user_id: str = Header(alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> ReservationOut:
    result, created = create_reservation(db, x_user_id, body)
    response.status_code = 201 if created else 200
    return result

@router.get("/reservations/{reservation_id}",
            response_model=ReservationOut,
            summary = "예약 단일 조회",
            description = "예약 한 건을 조회합니다."
            )
def get_reservation_detail(reservation_id: str, db: Session = Depends(get_db)) -> ReservationOut:
    return get_reservation(db, reservation_id)

@router.get("/reservations",
            response_model=ReservationListOut,
            summary = "예약 전체 조회",
            description = "예약 목록을 조회합니다."
            )
def get_reservation_list(
    user_id: str | None = None,
    event_id: str | None = None,
    db: Session = Depends(get_db),
) -> ReservationListOut:
    return list_reservations(db, user_id, event_id)

