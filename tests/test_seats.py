from datetime import timedelta
from uuid import uuid4

from app.core.clock import now_utc
from app.holds.models import Hold, HoldItem
from app.seats.models import Seat


def test_list_seats_returns_available_by_default(client, db_session, seeded):
    event_id = seeded["event_id"]

    response = client.get(f"/events/{event_id}/seats")

    assert response.status_code == 200
    body = response.json()
    seat_a1 = next(s for s in body["seats"] if s["seat_no"] == "A1")
    assert seat_a1["status"] == "AVAILABLE"
    assert seat_a1["occupant_user_id"] is None
    assert seat_a1["price"] == 100000


def test_seat_detail_shows_held_seat(client, db_session, seeded):
    event_id = seeded["event_id"]
    seat = db_session.query(Seat).filter_by(event_id=event_id, seat_no="A2").first()

    hold = Hold(id=str(uuid4()), user_id="U-001", event_id=event_id, status="ACTIVE", created_at=now_utc())
    db_session.add(hold)
    db_session.flush()
    db_session.add(HoldItem(hold_id=hold.id, seat_id=seat.id, price_snapshot=100000))
    seat.hold_id = hold.id
    db_session.commit()

    response = client.get(f"/events/{event_id}/seats/A2")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "HELD"
    assert body["occupant_user_id"] == "U-001"


def test_seat_detail_shows_reserved_seat(client, db_session, seeded):
    event_id = seeded["event_id"]
    seat = db_session.query(Seat).filter_by(event_id=event_id, seat_no="A3").first()

    hold = Hold(id=str(uuid4()), user_id="U-001", event_id=event_id, status="CONVERTED", created_at=now_utc())
    db_session.add(hold)
    db_session.flush()
    db_session.add(HoldItem(hold_id=hold.id, seat_id=seat.id, price_snapshot=100000))
    seat.hold_id = hold.id
    seat.status = "RESERVED"
    db_session.commit()

    response = client.get(f"/events/{event_id}/seats/A3")

    assert response.status_code == 200
    assert response.json()["status"] == "RESERVED"


def test_seats_for_nonexistent_event_returns_404(client, db_session, seeded):
    response = client.get("/events/EV-NOPE/seats")

    assert response.status_code == 404
    assert response.json()["code"] == "EVENT_NOT_FOUND"