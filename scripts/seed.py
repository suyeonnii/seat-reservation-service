import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.db import SessionLocal
from app.events.models import Event, EventGradePrice
from app.seats.models import Seat
from app.users.models import User
from app.holds.models import Hold, HoldItem
from app.reservations.models import Reservation

SEED_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_data.json"


def _parse_utc(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string).astimezone(timezone.utc).replace(tzinfo=None)


def seed() -> None:
    with open(SEED_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        for user in data["users"]:
            if db.get(User, user["user_id"]) is None:
                db.add(User(id=user["user_id"], display_name=user["display_name"]))

        for event in data["events"]:
            if db.get(Event, event["event_id"]) is not None:
                continue  # 이미 적재된 공연은 통째로 건너뜀

            db.add(
                Event(
                    id=event["event_id"],
                    title=event["title"],
                    venue=event["venue"],
                    starts_at=_parse_utc(event["starts_at"]),
                )
            )

            for grade, price in event["prices"].items():
                db.add(
                    EventGradePrice(event_id=event["event_id"], grade=grade, price=price)
                )

            for seat in event["seats"]:
                db.add(
                    Seat(event_id=event["event_id"], seat_no=seat["seat_no"], grade=seat["grade"])
                )

        db.commit()
        print("시드 적재 완료")
    finally:
        db.close()


if __name__ == "__main__":
    seed()