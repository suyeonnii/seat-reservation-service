from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.clock import now_utc
from app.core.db import Base, get_db
from app.events.models import Event, EventGradePrice
from app.holds.models import Hold, HoldItem  # noqa: F401
from app.main import app
from app.reservations.models import Reservation  # noqa: F401
from app.seats.models import Seat
from app.users.models import User


@pytest.fixture()
def db_session() -> Generator:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session) -> Generator:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded(db_session) -> dict:

    db_session.add_all([
        User(id="U-001", display_name="테스트1"),
        User(id="U-002", display_name="테스트2"),
    ])

    event = Event(
        id="EV-TEST",
        title="테스트 공연",
        venue="테스트홀",
        starts_at=now_utc() + timedelta(days=30),
    )
    db_session.add(event)
    db_session.add_all([
        EventGradePrice(event_id="EV-TEST", grade="VIP", price=100000),
        EventGradePrice(event_id="EV-TEST", grade="R", price=70000),
    ])
    db_session.add_all([
        Seat(event_id="EV-TEST", seat_no=no, grade="VIP")
        for no in ["A1", "A2", "A3", "A4", "A5"]
    ] + [Seat(event_id="EV-TEST", seat_no="B1", grade="R")])
    db_session.commit()

    return {"event_id": "EV-TEST"}