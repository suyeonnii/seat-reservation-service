"""
부하테스트용 DB를 시나리오별로 초기화하고 시딩한다.

운영 DB(app.db)를 절대 건드리지 않도록, DATABASE_PATH 환경변수가 명시적으로 설정되어 있고 app.db가 아닐 때만 동작.
"""

import argparse
import os
import sys
from datetime import timedelta

_DATABASE_PATH = os.environ.get("DATABASE_PATH")
if not _DATABASE_PATH or _DATABASE_PATH == "app.db":
    sys.exit(
        "DATABASE_PATH를 app.db가 아닌 값(예: loadtest.db)으로 지정해야 합니다. "
        "운영 DB를 보호하기 위한 안전장치입니다."
    )

from app.core.clock import now_utc
from app.core.config import HOLD_TTL_MINUTES
from app.core.db import Base, SessionLocal, engine
from app.events.models import Event, EventGradePrice
from app.holds.models import Hold, HoldItem
from app.reservations.models import Reservation
from app.seats.models import Seat
from app.users.models import User

from loadtest import constants as c


def _reset_schema() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def _seed_event(db) -> None:
    db.add(Event(id=c.EVENT_ID, title="부하테스트 공연", venue="부하테스트홀", starts_at=now_utc() + timedelta(days=30)))
    db.add(EventGradePrice(event_id=c.EVENT_ID, grade=c.GRADE, price=c.PRICE))


def _seed_users(db, user_ids: list[str]) -> None:
    db.add_all(User(id=uid, display_name=uid) for uid in user_ids)


def _seed_seats(db, seat_nos: list[str]) -> None:
    db.add_all(Seat(event_id=c.EVENT_ID, seat_no=no, grade=c.GRADE) for no in seat_nos)


def seed_a(db) -> None:
    _seed_event(db)
    _seed_users(db, c.USERS_A)
    _seed_seats(db, c.SEATS_A)


def seed_b(db) -> None:
    _seed_event(db)
    _seed_users(db, [c.USER_B_FIXED])
    _seed_seats(db, c.SEATS_B)


def seed_c(db) -> None:
    _seed_event(db)
    _seed_users(db, c.USERS_C)
    _seed_seats(db, c.SEATS_C_CONTENTION)
    _seed_seats(db, c.SEATS_C_BULK)


def seed_d(db) -> None:
    _seed_event(db)
    _seed_users(db, [c.USER_D_GHOST, *c.USERS_D])
    _seed_seats(db, [c.SEAT_D])
    db.flush()

    expired_at = now_utc() - timedelta(minutes=HOLD_TTL_MINUTES + 1)
    hold = Hold(id=c.HOLD_ID_D_EXPIRED, user_id=c.USER_D_GHOST, event_id=c.EVENT_ID, status="ACTIVE", created_at=expired_at)
    db.add(hold)
    db.flush()

    seat = db.query(Seat).filter_by(event_id=c.EVENT_ID, seat_no=c.SEAT_D).one()
    db.add(HoldItem(hold_id=hold.id, seat_id=seat.id, price_snapshot=c.PRICE))
    seat.status = "HELD"
    seat.hold_id = hold.id


def seed_e(db) -> None:
    _seed_event(db)
    _seed_users(db, [c.USER_E_OWNER])
    _seed_seats(db, [c.SEAT_E])
    db.flush()

    hold = Hold(id=c.HOLD_ID_E, user_id=c.USER_E_OWNER, event_id=c.EVENT_ID, status="ACTIVE", created_at=now_utc())
    db.add(hold)
    db.flush()

    seat = db.query(Seat).filter_by(event_id=c.EVENT_ID, seat_no=c.SEAT_E).one()
    db.add(HoldItem(hold_id=hold.id, seat_id=seat.id, price_snapshot=c.PRICE))
    seat.status = "HELD"
    seat.hold_id = hold.id


_SEEDERS = {"a": seed_a, "b": seed_b, "c": seed_c, "d": seed_d, "e": seed_e}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=sorted(_SEEDERS))
    args = parser.parse_args()

    _reset_schema()
    db = SessionLocal()
    try:
        _SEEDERS[args.scenario](db)
        db.commit()
    finally:
        db.close()

    print(f"[{args.scenario}] 시딩 완료 (DATABASE_PATH={_DATABASE_PATH})")


if __name__ == "__main__":
    main()
