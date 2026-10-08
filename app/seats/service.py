from datetime import datetime

from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.errors import EventNotFoundError, SeatNotFoundError
from app.events.models import Event, EventGradePrice
from app.holds.models import Hold
from app.seats.models import Seat
from app.seats.schemas import SeatListOut, SeatOut


def _resolve_status(hold: Hold | None, now: datetime) -> tuple[str, str | None]:
    """
    홀드 정보로부터 좌석 상태와 점유자 ID 계산.
    """
    if hold is None:
        return "AVAILABLE", None
    if hold.status == "CONVERTED":
        return "RESERVED", hold.user_id
    if hold.is_active(now):
        return "HELD", hold.user_id
    return "AVAILABLE", None


def get_seat_list(db: Session, event_id: str) -> SeatListOut:
    """
    공연의 좌석별 현재 상태, 가격, 점유자 조회.
    공연이 존재하지 않으면 EventNotFoundError 발생.
    """
    event = db.get(Event, event_id)
    if event is None:
        raise EventNotFoundError()

    seats = db.query(Seat).filter(Seat.event_id == event_id).all()

    prices = {
        p.grade: p.price
        for p in db.query(EventGradePrice).filter(EventGradePrice.event_id == event_id).all()
    }

    hold_ids = {seat.hold_id for seat in seats if seat.hold_id is not None}
    holds_by_id: dict[str, Hold] = {}
    if hold_ids:
        for hold in db.query(Hold).filter(Hold.id.in_(hold_ids)).all():
            holds_by_id[hold.id] = hold

    now = now_utc()
    seat_outs = []
    for seat in seats:
        hold = holds_by_id.get(seat.hold_id) if seat.hold_id else None
        status, occupant_user_id = _resolve_status(hold, now)
        seat_outs.append(
            SeatOut(
                seat_no=seat.seat_no,
                grade=seat.grade,
                price=prices[seat.grade],
                status=status,
                occupant_user_id=occupant_user_id,
            )
        )

    return SeatListOut(event_id=event_id, seats=seat_outs)


def get_seat_detail(db: Session, event_id: str, seat_no: str) -> SeatOut:
    """
    공연의 좌석 하나의 현재 상태, 가격, 점유자 조회.
    공연이 없으면 EventNotFoundError, 좌석 번호가 없으면 SeatNotFoundError 발생.
    """
    event = db.get(Event, event_id)
    if event is None:
        raise EventNotFoundError()

    seat = db.query(Seat).filter(Seat.event_id == event_id, Seat.seat_no == seat_no).first()
    if seat is None:
        raise SeatNotFoundError()

    price = db.get(EventGradePrice, (event_id, seat.grade))
    hold = db.get(Hold, seat.hold_id) if seat.hold_id else None
    status, occupant_user_id = _resolve_status(hold, now_utc())

    return SeatOut(
        seat_no=seat.seat_no,
        grade=seat.grade,
        price=price.price,
        status=status,
        occupant_user_id=occupant_user_id,
    )