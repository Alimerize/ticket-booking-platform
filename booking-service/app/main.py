import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .database import get_db
from .logging_config import setup_logging
from .metrics import bookings_created_total
from .rabbitmq import publish_event
from .schemas import BookingCreate, BookingRead

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="booking-service",
    description="Сервис бронирования билетов",
    version="0.2.0",
)


@app.get("/healthz", tags=["health"])
def healthz():
    return {"status": "ok"}


@app.get("/readyz", tags=["health"])
def readyz(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready"},
        )


@app.post(
    "/bookings/",
    response_model=BookingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать бронирование",
    description="Создаёт новую бронь и отправляет событие в очередь для уведомления.",
    tags=["bookings"],
)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    booking = models.Booking(
        user_id=payload.user_id,
        event_name=payload.event_name,
        seat_number=payload.seat_number,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    bookings_created_total.inc()

    publish_event({
        "booking_id": booking.id,
        "user_id": booking.user_id,
        "event_name": booking.event_name,
        "seat_number": booking.seat_number,
    })

    logger.info(
        "Booking created: id=%d user_id=%d event=%s seat=%s",
        booking.id, booking.user_id, booking.event_name, booking.seat_number,
    )

    return booking


@app.get(
    "/bookings/{booking_id}",
    response_model=BookingRead,
    summary="Получить бронирование по ID",
    tags=["bookings"],
)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.get(models.Booking, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    return booking


# Metrics
Instrumentator().instrument(app).expose(
    app, endpoint="/metrics", include_in_schema=False
)