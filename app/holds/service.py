import time
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.config import HOLD_TTL_MINUTES, MAX_SEATS_PER_USER_PER_EVENT
from app.core.errors import (
    EventNotFoundError,
    EventStartedError,
    SeatLimitExceededError,
    SeatNotFoundError,
    SeatUnavailableError,
    UserNotFoundError,
    HoldConvertedError,
    HoldNotFoundError,
    NotOwnerError
)
from app.core.locks import lock
from app.events.models import Event, EventGradePrice
from app.holds.models import Hold, HoldItem
from app.holds.schemas import HoldCreate, HoldOut, HoldSeatOut
from app.seats.models import Seat
from app.users.models import User

_LOCK_RETRY_ATTEMPTS = 20
_LOCK_RETRY_DELAY_SECONDS = 0.02


def _claim_seat(db: Session, seat: Seat, hold_id: str, ttl_cutoff) -> bool:
    """
    좌석을 조건부로 선점한다. 성공하면 True.
    """
    db.execute(
        update(Seat)
        .where(
            Seat.id == seat.id,
            Seat.hold_id.in_(
                select(Hold.id).where(Hold.status == "ACTIVE", Hold.created_at <= ttl_cutoff)
            ),
        )
        .values(status="AVAILABLE", hold_id=None)
    )

    result = db.execute(
        update(Seat)
        .where(Seat.id == seat.id, Seat.hold_id.is_(None))
        .values(status="HELD", hold_id=hold_id)
    )
    return result.rowcount == 1


def create_hold(db: Session, event_id: str, user_id: str, body: HoldCreate) -> HoldOut:
    """
    사용자가 지정한 좌석들을 5분간 홀드한다.
    """
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError()

    event = db.get(Event, event_id)
    if event is None:
        raise EventNotFoundError()

    now = now_utc()
    if now >= event.starts_at:
        raise EventStartedError()

    seats = db.query(Seat).filter(Seat.event_id == event_id, Seat.seat_no.in_(body.seat_nos)).all()
    seats_by_no = {seat.seat_no: seat for seat in seats}
    missing = [no for no in body.seat_nos if no not in seats_by_no]
    if missing:
        raise SeatNotFoundError(details={"seat_nos": missing})

    lock_key = f"user:{user_id}:event:{event_id}"
    acquired = False
    for _ in range(_LOCK_RETRY_ATTEMPTS):
        acquired = lock.acquire(lock_key)
        if acquired:
            break
        time.sleep(_LOCK_RETRY_DELAY_SECONDS)
    if not acquired:
        raise SeatUnavailableError(message="요청이 몰려 처리하지 못했습니다. 다시 시도해주세요.")

    try:
        ttl_cutoff = now - timedelta(minutes=HOLD_TTL_MINUTES)

        current_count = (
            db.query(HoldItem)
            .join(Hold, HoldItem.hold_id == Hold.id)
            .filter(Hold.user_id == user_id, Hold.event_id == event_id)
            .filter(
                (Hold.status == "CONVERTED")
                | ((Hold.status == "ACTIVE") & (Hold.created_at > ttl_cutoff))
            )
            .count()
        )
        if current_count + len(body.seat_nos) > MAX_SEATS_PER_USER_PER_EVENT:
            raise SeatLimitExceededError()

        new_hold_id = str(uuid4())
        new_hold = Hold(id=new_hold_id, user_id=user_id, event_id=event_id, status="ACTIVE", created_at=now)
        db.add(new_hold)
        db.flush()

        blocked = [
            seat_no
            for seat_no in body.seat_nos
            if not _claim_seat(db, seats_by_no[seat_no], new_hold_id, ttl_cutoff)
        ]
        if blocked:
            db.rollback()
            raise SeatUnavailableError(details={"blocked_seats": blocked})

        prices = {
            p.grade: p.price
            for p in db.query(EventGradePrice).filter(EventGradePrice.event_id == event_id).all()
        }
        for seat_no in body.seat_nos:
            seat = seats_by_no[seat_no]
            db.add(HoldItem(hold_id=new_hold_id, seat_id=seat.id, price_snapshot=prices[seat.grade]))

        db.commit()
        db.refresh(new_hold)
    finally:
        lock.release(lock_key)

    return HoldOut(
        hold_id=new_hold.id,
        event_id=new_hold.event_id,
        user_id=new_hold.user_id,
        status=new_hold.status,
        created_at=new_hold.created_at,
        expires_at=new_hold.created_at + timedelta(minutes=HOLD_TTL_MINUTES),
        seats=[HoldSeatOut(seat_no=no, price=prices[seats_by_no[no].grade]) for no in body.seat_nos],
        message="홀드가 생성되었습니다.",
    )


def _effective_status(hold: Hold, now) -> str:

    if hold.status == "ACTIVE" and not hold.is_active(now):
        return "EXPIRED"
    return hold.status


def _to_hold_out(db: Session, hold: Hold, now, message: str | None = None) -> HoldOut:
    hold_items = db.query(HoldItem).filter(HoldItem.hold_id == hold.id).all()
    seat_ids = [item.seat_id for item in hold_items]
    seats_by_id = {s.id: s.seat_no for s in db.query(Seat).filter(Seat.id.in_(seat_ids)).all()}
    return HoldOut(
        hold_id=hold.id,
        event_id=hold.event_id,
        user_id=hold.user_id,
        status=_effective_status(hold, now),
        created_at=hold.created_at,
        expires_at=hold.created_at + timedelta(minutes=HOLD_TTL_MINUTES),
        seats=[
            HoldSeatOut(seat_no=seats_by_id[item.seat_id], price=item.price_snapshot)
            for item in hold_items
        ],
        message=message,
    )


def get_hold(db: Session, hold_id: str) -> HoldOut:
    """
    홀드 하나를 조회한다.
    """
    hold = db.get(Hold, hold_id)
    if hold is None:
        raise HoldNotFoundError()
    return _to_hold_out(db, hold, now_utc())


def cancel_hold(db: Session, hold_id: str, user_id: str) -> HoldOut:
    """
    사용자가 자신의 홀드를 취소한다.
    """
    hold = db.get(Hold, hold_id)
    if hold is None:
        raise HoldNotFoundError()

    if hold.user_id != user_id:
        raise NotOwnerError()

    if hold.status == "CONVERTED":
        raise HoldConvertedError()

    now = now_utc()
    if hold.status == "ACTIVE" and hold.is_active(now):
        hold.status = "CANCELLED"
        db.execute(
            update(Seat).where(Seat.hold_id == hold.id).values(status="AVAILABLE", hold_id=None)
        )
        db.commit()
        db.refresh(hold)

    return _to_hold_out(db, hold, now, message="홀드가 취소되었습니다.")