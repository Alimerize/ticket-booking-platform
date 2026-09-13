import logging

from fastapi import Depends, FastAPI, HTTPException
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

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="booking-service")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        return JSONResponse(status_code=503, content={"status": "not ready"})


@app.post("/bookings/", status_code=201)
def create_booking(
    user_id: int,
    event_name: str,
    seat_number: str,
    db: Session = Depends(get_db),
):
    booking = models.Booking(
        user_id=user_id,
        event_name=event_name,
        seat_number=seat_number,
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

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "event_name": booking.event_name,
        "seat_number": booking.seat_number,
    }


@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.get(models.Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)