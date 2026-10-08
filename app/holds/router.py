from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.holds.schemas import HoldCreate, HoldOut, HoldPatch
from app.holds.service import cancel_hold, create_hold, get_hold

router = APIRouter(tags=["holds"])


@router.post("/events/{event_id}/holds",
             response_model=HoldOut,
             status_code=201,
             summary="좌석에 대한 홀드 생성",
             description="좌석을 지정해 홀드를 생성합니다.")
def post_hold(
    event_id: str,
    body: HoldCreate,
    x_user_id: str = Header(alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> HoldOut:

    return create_hold(db, event_id, x_user_id, body)


@router.get("/holds/{hold_id}",
            response_model=HoldOut,
            summary="홀드 단일 조회",
            description="홀드 하나를 조회합니다.")
def get_hold_detail(hold_id: str, db: Session = Depends(get_db)) -> HoldOut:
    return get_hold(db, hold_id)


@router.patch("/holds/{hold_id}",
              response_model=HoldOut,
              summary="좌석에 대한 홀드 취소",
              description="홀드를 취소합니다.")
def patch_hold(
    hold_id: str,
    body: HoldPatch,
    x_user_id: str = Header(alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> HoldOut:

    return cancel_hold(db, hold_id, x_user_id)