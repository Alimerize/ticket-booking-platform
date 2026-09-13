import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

from . import models
from .config import settings
from .logging_config import setup_logging
from .rabbitmq import publish_event

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="Booking Service", version="1.0.0")

Instrumentator().instrument(app).expose(app)

BOOKINGS_CREATED = Counter(
    "bookings_created_total",
    "Total number of bookings created",
)

models.Base.metadata.create_all(bind=models.engine)


def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Booking Service is running!", "version": "1.0.0"}


@app.get("/healthz")
def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/readyz")
def ready(db: Session = Depends(get_db)):
    """Readiness probe: проверяем, что БД доступна."""
    try:
        db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as exc:
        logger.error(f"Readiness check failed: {exc}")
        raise HTTPException(status_code=503, detail="Database not ready")


@app.post("/bookings/")
def create_booking(
    user_id: int,
    event_name: str,
    seat_number: str,
    db: Session = Depends(get_db),
):
    try:
        db_booking = models.Booking(
            user_id=user_id,
            event_name=event_name,
            seat_number=seat_number,
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to create booking: {exc}")
        raise HTTPException(status_code=500, detail="Database error")

    BOOKINGS_CREATED.inc()

    publish_event({
        "event_type": "booking.created",
        "booking_id": db_booking.id,
        "user_id": user_id,
        "event_name": event_name,
        "seat_number": seat_number,
    })

    logger.info(f"Booking created: id={db_booking.id}, user_id={user_id}")
    return {"booking": db_booking, "status": "created"}