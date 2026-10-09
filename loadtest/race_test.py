import argparse
import os
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import httpx

_DATABASE_PATH = os.environ.get("DATABASE_PATH")
if not _DATABASE_PATH or _DATABASE_PATH == "app.db":
    sys.exit("DATABASE_PATH를 app.db가 아닌 값으로 지정해야 합니다.")

from app.core.db import SessionLocal  # noqa: E402
from app.reservations.models import Reservation  # noqa: E402

from loadtest import constants as c  # noqa: E402


def _fire(barrier: threading.Barrier, fn):
    barrier.wait()
    return fn()


def _run_concurrent(requests: list):

    barrier = threading.Barrier(len(requests))

    def call(method, url, kwargs):
        with httpx.Client() as client:
            resp = client.request(method, url, **kwargs)
            try:
                body = resp.json()
            except ValueError:
                body = {"code": "NON_JSON_RESPONSE", "raw_text": resp.text[:300]}
            return resp.status_code, body

    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        futures = [
            pool.submit(_fire, barrier, lambda m=m, u=u, k=k: call(m, u, k))
            for m, u, k in requests
        ]
        return [f.result() for f in futures]


def scenario_b(host: str) -> None:
    """같은 user_id로 서로 다른 좌석 여러 개 요청 -> 최대 4개까지 홀드 가능."""
    requests = [
        (
            "POST",
            f"{host}/events/{c.EVENT_ID}/holds",
            {"json": {"seat_nos": [seat_no]}, "headers": {"X-User-Id": c.USER_B_FIXED}},
        )
        for seat_no in c.SEATS_B
    ]
    results = _run_concurrent(requests)

    statuses = Counter(code for code, _ in results)
    succeeded = [body for code, body in results if code == 201]
    print(f"응답 코드 분포: {dict(statuses)}")
    print(f"성공(201) 건수: {len(succeeded)} / 요청 {len(requests)}건 (좌석 1석씩이므로 성공 건수 = 점유 좌석 수)")

    codes = Counter(body.get("code") for code, body in results if code != 201)
    print(f"실패 사유 분포: {dict(codes)}")

    ok = len(succeeded) <= 4
    print("[PASS]" if ok else "[FAIL]", "4석 제한 준수" if ok else "4석 제한 초과! 레이스 컨디션 버그 의심")


def scenario_d(host: str) -> None:
    """이미 만료된 홀드가 걸린 좌석 1개를 여러 유저가 동시에 재점유 시도 → 1명만 성공"""
    requests = [
        (
            "POST",
            f"{host}/events/{c.EVENT_ID}/holds",
            {"json": {"seat_nos": [c.SEAT_D]}, "headers": {"X-User-Id": user_id}},
        )
        for user_id in c.USERS_D
    ]
    results = _run_concurrent(requests)

    statuses = Counter(code for code, _ in results)
    succeeded = [body for code, body in results if code == 201]
    print(f"응답 코드 분포: {dict(statuses)}")
    print(f"성공(201) 건수: {len(succeeded)} / 요청 {len(requests)}건")

    ok = len(succeeded) == 1
    print("[PASS]" if ok else "[FAIL]", "정확히 1명만 재점유 성공" if ok else "0명 또는 2명 이상 성공! 만료 경계 레이스 버그 의심")


def scenario_e(host: str) -> None:
    """같은 hold_id로 동시에 예약 생성 N건 요청 → Reservation이 1개만 생성."""
    n = 20
    requests = [
        (
            "POST",
            f"{host}/reservations",
            {"json": {"hold_id": c.HOLD_ID_E}, "headers": {"X-User-Id": c.USER_E_OWNER}},
        )
        for _ in range(n)
    ]
    results = _run_concurrent(requests)

    statuses = Counter(code for code, _ in results)
    reservation_ids = {body["reservation_id"] for code, body in results if code in (200, 201)}
    print(f"응답 코드 분포: {dict(statuses)}")
    print(f"응답에 담긴 서로 다른 reservation_id 개수: {len(reservation_ids)} (요청 {n}건)")

    db = SessionLocal()
    try:
        row_count = db.query(Reservation).filter(Reservation.hold_id == c.HOLD_ID_E).count()
    finally:
        db.close()
    print(f"DB에 실제 생성된 Reservation row 개수: {row_count}")

    ok = row_count == 1 and len(reservation_ids) == 1
    print("[PASS]" if ok else "[FAIL]", "중복 생성 없음" if ok else "Reservation 중복 생성 확인! TOCTOU 레이스 버그 확정")


_SCENARIOS = {"b": scenario_b, "d": scenario_d, "e": scenario_e}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=sorted(_SCENARIOS))
    parser.add_argument("--host", default="http://localhost:8001")
    args = parser.parse_args()

    _SCENARIOS[args.scenario](args.host)


if __name__ == "__main__":
    main()
