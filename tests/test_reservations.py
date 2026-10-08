from datetime import timedelta
from uuid import uuid4

from app.core.clock import now_utc
from app.holds.models import Hold, HoldItem
from app.seats.models import Seat


def _create_hold_directly(
    db_session, event_id: str, user_id: str, seat_nos: list[str], created_at, status: str = "ACTIVE"
):
    hold = Hold(id=str(uuid4()), user_id=user_id, event_id=event_id, status=status, created_at=created_at)
    db_session.add(hold)
    db_session.flush()
    for seat_no in seat_nos:
        seat = db_session.query(Seat).filter_by(event_id=event_id, seat_no=seat_no).first()
        db_session.add(HoldItem(hold_id=hold.id, seat_id=seat.id, price_snapshot=100000))
        seat.hold_id = hold.id
        if status == "ACTIVE":
            seat.status = "HELD"
        elif status == "CONVERTED":
            seat.status = "RESERVED"
    db_session.commit()
    return hold


def test_create_reservation_succeeds_and_sums_price(client, db_session, seeded):
    """
    총 가격 계산
    """
    event_id = seeded["event_id"]

    hold_response = client.post(
        f"/events/{event_id}/holds",
        json={"seat_nos": ["A1", "A2"]},
        headers={"X-User-Id": "U-001"},
    )
    hold_id = hold_response.json()["hold_id"]

    response = client.post(
        "/reservations",
        json={"hold_id": hold_id},
        headers={"X-User-Id": "U-001"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["total_amount"] == 200000  # VIP 100000 x 2
    assert len(body["seats"]) == 2
    assert body["message"] == "예약이 생성되었습니다."


def test_create_reservation_retry_returns_existing_reservation(client, db_session, seeded):
    """
    같은 홀드로 예약을 두 번 요청할 경우
    """
    event_id = seeded["event_id"]
    hold_response = client.post(
        f"/events/{event_id}/holds",
        json={"seat_nos": ["A1"]},
        headers={"X-User-Id": "U-001"},
    )
    hold_id = hold_response.json()["hold_id"]

    first = client.post("/reservations", json={"hold_id": hold_id}, headers={"X-User-Id": "U-001"})
    second = client.post("/reservations", json={"hold_id": hold_id}, headers={"X-User-Id": "U-001"})

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["reservation_id"] == second.json()["reservation_id"]


def test_create_reservation_with_expired_hold_is_rejected(client, db_session, seeded):
    """
    홀드 시간이 만료된 좌석을 예약할 경우
    """
    event_id = seeded["event_id"]
    six_minutes_ago = now_utc() - timedelta(minutes=6)
    hold = _create_hold_directly(db_session, event_id, "U-001", ["A1"], six_minutes_ago)

    response = client.post("/reservations", json={"hold_id": hold.id}, headers={"X-User-Id": "U-001"})

    assert response.status_code == 409
    assert response.json()["code"] == "HOLD_EXPIRED"


def test_create_reservation_with_cancelled_hold_is_rejected(client, db_session, seeded):
    """
    취소된 홀드로 예약 요청할 경우
    """
    event_id = seeded["event_id"]
    hold = _create_hold_directly(db_session, event_id, "U-001", ["A1"], now_utc(), status="CANCELLED")

    response = client.post("/reservations", json={"hold_id": hold.id}, headers={"X-User-Id": "U-001"})

    assert response.status_code == 409
    assert response.json()["code"] == "HOLD_NOT_ACTIVE"


def test_create_reservation_by_non_owner_is_forbidden(client, db_session, seeded):
    """
    다른 사용자의 홀드를 예약 요청할 경우
    """
    event_id = seeded["event_id"]
    hold = _create_hold_directly(db_session, event_id, "U-001", ["A1"], now_utc())

    response = client.post("/reservations", json={"hold_id": hold.id}, headers={"X-User-Id": "U-002"})

    assert response.status_code == 403


def test_get_reservation_by_id(client, db_session, seeded):
    """
    단일 예약 조회 - 성공
    """
    event_id = seeded["event_id"]
    hold_id = client.post(
        f"/events/{event_id}/holds", json={"seat_nos": ["A1"]}, headers={"X-User-Id": "U-001"}
    ).json()["hold_id"]
    created = client.post("/reservations", json={"hold_id": hold_id}, headers={"X-User-Id": "U-001"})
    reservation_id = created.json()["reservation_id"]

    response = client.get(f"/reservations/{reservation_id}")

    assert response.status_code == 200
    assert response.json()["reservation_id"] == reservation_id


def test_get_reservation_not_found(client, db_session, seeded):
    """
    단일 예약 조회 - 실패
    """
    response = client.get("/reservations/no-such-id")

    assert response.status_code == 404
    assert response.json()["code"] == "RESERVATION_NOT_FOUND"


def test_list_reservations_filters_by_user_and_event(client, db_session, seeded):
    """
    사용자별, 공연별, (사용자+공연)별 예약 조회
    """
    event_id = seeded["event_id"]

    hold1 = client.post(
        f"/events/{event_id}/holds", json={"seat_nos": ["A1"]}, headers={"X-User-Id": "U-001"}
    ).json()["hold_id"]
    client.post("/reservations", json={"hold_id": hold1}, headers={"X-User-Id": "U-001"})

    hold2 = client.post(
        f"/events/{event_id}/holds", json={"seat_nos": ["A2"]}, headers={"X-User-Id": "U-002"}
    ).json()["hold_id"]
    client.post("/reservations", json={"hold_id": hold2}, headers={"X-User-Id": "U-002"})

    by_user = client.get("/reservations?user_id=U-001").json()
    assert len(by_user["reservations"]) == 1
    assert by_user["reservations"][0]["user_id"] == "U-001"

    by_event = client.get(f"/reservations?event_id={event_id}").json()
    assert len(by_event["reservations"]) == 2

    all_reservations = client.get("/reservations").json()
    assert len(all_reservations["reservations"]) == 2
