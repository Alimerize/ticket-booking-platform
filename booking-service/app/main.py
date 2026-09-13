from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator
import pika
import json
import os
import time
from . import models
from prometheus_client import Counter

app = FastAPI()

BOOKINGS_CREATED = Counter(
    'bookings_created_total',
    'Total number of bookings created'
)

Instrumentator().instrument(app).expose(app)

models.Base.metadata.create_all(bind=models.engine)

def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Booking Service is running!"}

@app.post("/bookings/")
def create_booking(user_id: int, event_name: str, seat_number: str, db: Session = Depends(get_db)):
    db_booking = models.Booking(user_id=user_id, event_name=event_name, seat_number=seat_number)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='booking_notifications')

        message = {
            "booking_id": db_booking.id,
            "user_id": user_id,
            "event_name": event_name,
            "seat_number": seat_number
        }
        channel.basic_publish(exchange='', routing_key='booking_notifications', body=json.dumps(message))
        connection.close()
        print(" [x] Sent booking notification")
    except Exception as e:
        print(f"Failed to send message to RabbitMQ: {e}")

    BOOKINGS_CREATED.inc()
    return {"booking": db_booking, "status": "created"}