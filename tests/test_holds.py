from datetime import timedelta
from uuid import uuid4

from app.core.clock import now_utc
from app.holds.models import Hold, HoldItem
from app.seats.models import Seat


def _create_hold_directly(db_session, event_id: str, user_id: str, seat_no: str, created_at, status: str = "ACTIVE"):
    """
    DB에 홀드 직접 생성
    """
    seat = db_session.query(Seat).filter_by(event_id=event_id, seat_no=seat_no).first()
    hold = Hold(id=str(uuid4()), user_id=user_id, event_id=event_id, status=status, created_at=created_at)
    db_session.add(hold)
    db_session.flush()
    db_session.add(HoldItem(hold_id=hold.id, seat_id=seat.id, price_snapshot=100000))
    seat.hold_id = hold.id
    if status == "ACTIVE":
        seat.status = "HELD"
    db_session.commit()
    return hold


def test_create_hold_succeeds(client, db_session, seeded):
    """
    정상적으로 홀드 생성
    """
    event_id = seeded["event_id"]

    response = client.post(
        f"/events/{event_id}/holds",
        json={"seat_nos": ["A1", "A2"]},
        headers={"X-User-Id": "U-001"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ACTIVE"
    assert len(body["seats"]) == 2
    assert body["message"] == "홀드가 생성되었습니다."


def test_create_hold_rejects_duplicate_seat_nos(client, db_session, seeded):
    """
    동일한 좌석을 두 번 보내는 경우
    """
    event_id = seeded["event_id"]

    response = client.post(
        f"/events/{event_id}/holds",
        json={"seat_nos": ["A1", "A1"]},
        headers={"X-User-Id": "U-001"},
    )

    assert response.status_code == 422


def test_create_hold_fails_when_seat_already_held(client, db_session, seeded):
    """
    홀드 요청한 좌석들 중에 이미 다른 사용자가 홀드한 좌석이 포함된 경우
    """
    event_id = seeded["event_id"]
    _create_hold_directly(db_session, event_id, "U-002", "A1", now_utc())

    response = client.post(
        f"/events/{event_id}/holds",
        json={"seat_nos": ["A1", "A2"]},
        headers={"X-User-Id": "U-001"},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "SEAT_UNAVAILABLE"
    assert body["details"]["blocked_seats"] == ["A1"]

    seat_a2 = client.get(f"/events/{event_id}/seats/A2").json()
    assert seat_a2["status"] == "AVAILABLE"


def test_create_hold_allows_reclaiming_expired_seat(client, db_session, seeded):
    """
    만료된 홀드를 다른 사용자가 홀드 요청할 경우
    """
    event_id = seeded["event_id"]
    six_minutes_ago = now_utc() - timedelta(minutes=6)
    _create_hold_directly(db_session, event_id, "U-002", "A1", six_minutes_ago)

    response = client.post(
        f"/events/{event_id}/holds",
        json={"seat_nos": ["A1"]},
        headers={"X-User-Id": "U-001"},
    )

    assert response.status_code == 201


def test_create_hold_exceeding_seat_limit_is_rejected(client, db_session, seeded):
    """
    홀드 요청한 총 좌석의 수가 4석을 넘는 경우
    """
    event_id = seeded["event_id"]

    first = client.post(
        f"/events/{event_id}/holds",
        json={"seat_nos": ["A1", "A2", "A3"]},
        headers={"X-User-Id": "U-001"},
    )
    assert first.status_code == 201

    second = client.post(
        f"/events/{event_id}/holds",
        json={"seat_nos": ["A4", "A5"]},
        headers={"X-User-Id": "U-001"},
    )

    assert second.status_code == 409
    assert second.json()["code"] == "SEAT_LIMIT_EXCEEDED"


def test_get_hold_shows_expired_status_without_cleanup_job(client, db_session, seeded):
    """
    정리 작업이 실행되지 않아도 홀드가 만료된 좌석의 상태가 EXPIRED인지 확인
    """
    event_id = seeded["event_id"]
    six_minutes_ago = now_utc() - timedelta(minutes=6)
    hold = _create_hold_directly(db_session, event_id, "U-001", "A1", six_minutes_ago)

    response = client.get(f"/holds/{hold.id}")

    assert response.status_code == 200
    assert response.json()["status"] == "EXPIRED"


def test_cancel_hold_by_non_owner_is_forbidden(client, db_session, seeded):
    """
    사용자가 다른 사용자의 홀드를 취소하려고 할 경우
    """
    event_id = seeded["event_id"]
    hold = _create_hold_directly(db_session, event_id, "U-001", "A1", now_utc())

    response = client.patch(
        f"/holds/{hold.id}",
        json={"status": "CANCELLED"},
        headers={"X-User-Id": "U-002"},
    )

    assert response.status_code == 403


def test_cancel_hold_frees_the_seat_immediately(client, db_session, seeded):
    """
    홀드 취소 정상 작동
    """
    event_id = seeded["event_id"]
    hold = _create_hold_directly(db_session, event_id, "U-001", "A1", now_utc())

    response = client.patch(
        f"/holds/{hold.id}",
        json={"status": "CANCELLED"},
        headers={"X-User-Id": "U-001"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"

    seat = client.get(f"/events/{event_id}/seats/A1").json()
    assert seat["status"] == "AVAILABLE"
    assert seat["occupant_user_id"] is None


def test_cancel_hold_twice_is_idempotent(client, db_session, seeded):
    """
    같은 홀드를 두 번 연속 취소할 경우
    """
    event_id = seeded["event_id"]
    hold = _create_hold_directly(db_session, event_id, "U-001", "A1", now_utc())

    first = client.patch(
        f"/holds/{hold.id}", json={"status": "CANCELLED"}, headers={"X-User-Id": "U-001"}
    )
    second = client.patch(
        f"/holds/{hold.id}", json={"status": "CANCELLED"}, headers={"X-User-Id": "U-001"}
    )

    assert first.status_code == 200
    assert second.status_code == 200


def test_cancel_converted_hold_is_rejected(client, db_session, seeded):
    """
    이미 예약된 좌석의 홀드를 취소할 경우
    """
    event_id = seeded["event_id"]
    hold = _create_hold_directly(db_session, event_id, "U-001", "A1", now_utc(), status="CONVERTED")

    response = client.patch(
        f"/holds/{hold.id}", json={"status": "CANCELLED"}, headers={"X-User-Id": "U-001"}
    )

    assert response.status_code == 409
    assert response.json()["code"] == "HOLD_CONVERTED"
