from uuid import uuid4

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.errors import (
    EventStartedError,
    HoldExpiredError,
    HoldNotActiveError,
    HoldNotFoundError,
    NotOwnerError,
    ReservationNotFoundError,
    UserNotFoundError,
)
from app.events.models import Event
from app.holds.models import Hold, HoldItem
from app.holds.schemas import HoldSeatOut
from app.reservations.models import Reservation
from app.reservations.schemas import ReservationCreate, ReservationListOut, ReservationOut
from app.seats.models import Seat
from app.users.models import User


def _to_reservation_out(db: Session, reservation: Reservation, message: str | None = None) -> ReservationOut:
    hold_items = db.query(HoldItem).filter(HoldItem.hold_id == reservation.hold_id).all()
    seat_ids = [item.seat_id for item in hold_items]
    seats_by_id = {s.id: s.seat_no for s in db.query(Seat).filter(Seat.id.in_(seat_ids)).all()}
    return ReservationOut(
        reservation_id=reservation.id,
        hold_id=reservation.hold_id,
        user_id=reservation.user_id,
        event_id=reservation.event_id,
        total_amount=reservation.total_amount,
        seats=[
            HoldSeatOut(seat_no=seats_by_id[item.seat_id], price=item.price_snapshot)
            for item in hold_items
        ],
        created_at=reservation.created_at,
        message=message,
    )


def create_reservation(db: Session, user_id: str, body: ReservationCreate) -> tuple[ReservationOut, bool]:
    """
    홀드된 좌석에 대한 예약 생성.
    """
    hold = db.get(Hold, body.hold_id)
    if hold is None:
        raise HoldNotFoundError()

    if hold.user_id != user_id:
        raise NotOwnerError()

    if hold.status == "CONVERTED":
        existing = db.query(Reservation).filter(Reservation.hold_id == hold.id).first()
        return _to_reservation_out(db, existing, message="이미 생성된 예약입니다."), False

    event = db.get(Event, hold.event_id)
    now = now_utc()
    if now >= event.starts_at:
        raise EventStartedError()

    if hold.status != "ACTIVE":
        raise HoldNotActiveError()

    if not hold.is_active(now):
        raise HoldExpiredError()

    hold_items = db.query(HoldItem).filter(HoldItem.hold_id == hold.id).all()
    total_amount = sum(item.price_snapshot for item in hold_items)

    new_reservation = Reservation(
        id=str(uuid4()),
        hold_id=hold.id,
        user_id=user_id,
        event_id=hold.event_id,
        total_amount=total_amount,
        created_at=now,
    )
    db.add(new_reservation)
    hold.status = "CONVERTED"

    seat_ids = [item.seat_id for item in hold_items]
    db.execute(update(Seat).where(Seat.id.in_(seat_ids)).values(status="RESERVED"))

    db.commit()
    db.refresh(new_reservation)

    return _to_reservation_out(db, new_reservation, message="예약이 생성되었습니다."), True


def get_reservation(db: Session, reservation_id: str) -> ReservationOut:
    """
    예약 단일 조회.
    """
    reservation = db.get(Reservation, reservation_id)
    if reservation is None:
        raise ReservationNotFoundError()
    return _to_reservation_out(db, reservation)


def list_reservations(db: Session, user_id: str | None, event_id: str | None) -> ReservationListOut:
    """
    예약 목록 전체 조회
    """
    query = db.query(Reservation)
    if user_id is not None:
        if db.get(User, user_id) is None:
            raise UserNotFoundError()
        query = query.filter(Reservation.user_id == user_id)
    if event_id is not None:
        query = query.filter(Reservation.event_id == event_id)

    reservations = query.all()
    return ReservationListOut(reservations=[_to_reservation_out(db, r) for r in reservations])