import asyncio
import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import CLEANUP_INTERVAL_SECONDS
from app.core.db import SessionLocal
from app.core.errors import DomainError
from app.holds.cleanup import cleanup_expired_holds
from app.holds.router import router as holds_router
from app.seats.router import router as seats_router
from app.reservations.router import router as reservations_router

async def _cleanup_loop() -> None:
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            await asyncio.to_thread(cleanup_expired_holds, db)
        finally:
            db.close()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()

app = FastAPI(title="seat-reservation-service", lifespan=lifespan)

app.include_router(seats_router)
app.include_router(holds_router)
app.include_router(reservations_router)


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "details": exc.details},
    )