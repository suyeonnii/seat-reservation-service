from app.core.db import Base, engine
from app.events.models import Event, EventGradePrice
from app.holds.models import Hold, HoldItem
from app.reservations.models import Reservation
from app.seats.models import Seat
from app.users.models import User


def init_db() -> None:
    Base.metadata.create_all(engine)
    print("테이블 생성 완료")


if __name__ == "__main__":
    init_db()