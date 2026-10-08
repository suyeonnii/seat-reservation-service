from datetime import timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.config import HOLD_TTL_MINUTES
from app.core.locks import lock
from app.holds.models import Hold
from app.seats.models import Seat

_CLEANUP_LOCK_KEY = "cleanup:holds"


def cleanup_expired_holds(db: Session) -> int:
    """
    만료된 ACTIVE 홀드를 찾아 EXPIRED로 바꾸고 점유중이던 좌석 홀드 해제.
    """

    if not lock.acquire(_CLEANUP_LOCK_KEY):
        return 0

    try:
        now = now_utc()
        cutoff = now - timedelta(minutes=HOLD_TTL_MINUTES)

        expired_holds = (
            db.query(Hold)
            .filter(Hold.status == "ACTIVE", Hold.created_at <= cutoff)
            .all()
        )

        for hold in expired_holds:
            hold.status = "EXPIRED"
            db.execute(
                update(Seat)
                .where(Seat.hold_id == hold.id)
                .values(status="AVAILABLE", hold_id=None)
            )

        db.commit()
        return len(expired_holds)
    finally:
        lock.release(_CLEANUP_LOCK_KEY)