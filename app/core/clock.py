from datetime import datetime, timezone


def now_utc() -> datetime:
    """현재 UTC 시각을 반환한다. 테스트에서는 이 함수를 monkeypatch하여 가짜 시각을 주입한다."""
    return datetime.now(timezone.utc)
