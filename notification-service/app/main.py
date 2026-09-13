import json
import logging
import threading
import time

import pika
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_client import Counter, make_asgi_app

from .config import settings
from .logging_config import setup_logging

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

NOTIFICATIONS_SENT = Counter(
    "notifications_sent_total",
    "Total number of notifications sent",
)
NOTIFICATIONS_FAILED = Counter(
    "notifications_failed_total",
    "Total number of failed notifications",
)

shutdown_event = threading.Event()
_conn_lock = threading.Lock()
_connection: pika.BlockingConnection | None = None


def _set_connection(conn: pika.BlockingConnection | None) -> None:
    global _connection
    with _conn_lock:
        _connection = conn


def _is_rabbitmq_ready() -> bool:
    with _conn_lock:
        return _connection is not None and _connection.is_open


app = FastAPI(title="notification-service")
app.mount("/metrics", make_asgi_app())


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    if _is_rabbitmq_ready():
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "not ready"})


def callback(ch, method, properties, body):
    try:
        payload = json.loads(body)
        logger.info("Received notification event: booking_id=%s", payload.get("booking_id"))

        # Эмуляция отправки (заменить на реальный email/SMS-провайдер)
        time.sleep(0.5)

        NOTIFICATIONS_SENT.inc()
        logger.info("Notification sent: booking_id=%s", payload.get("booking_id"))
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        NOTIFICATIONS_FAILED.inc()
        logger.exception("Failed to process notification: %s", exc)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def _consume_loop() -> None:
    
    while not shutdown_event.is_set():
        conn = None
        try:
            params = pika.URLParameters(settings.RABBITMQ_URL)
            params.heartbeat = 30
            params.blocked_connection_timeout = 10
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
            ch.basic_qos(prefetch_count=10)
            ch.basic_consume(
                queue=settings.RABBITMQ_QUEUE,
                on_message_callback=callback,
                auto_ack=False,
            )
            _set_connection(conn)
            logger.info("Consumer connected to RabbitMQ, waiting for messages...")

            # process_data_events позволяет периодически проверять shutdown_event
            while not shutdown_event.is_set():
                conn.process_data_events(time_limit=1)

        except pika.exceptions.AMQPConnectionError as exc:
            if shutdown_event.is_set():
                break
            logger.warning(
                "RabbitMQ unavailable (%s), retrying in %ss",
                exc, settings.RECONNECT_DELAY,
            )
            time.sleep(settings.RECONNECT_DELAY)
        except Exception as exc:
            logger.exception("Unexpected error in consumer: %s", exc)
            time.sleep(settings.RECONNECT_DELAY)
        finally:
            _set_connection(None)
            if conn is not None:
                try:
                    if conn.is_open:
                        conn.close()
                except Exception:
                    pass

    logger.info("Consumer loop stopped")



def main() -> None:
    consumer_thread = threading.Thread(
        target=_consume_loop, name="rabbitmq-consumer", daemon=True
    )
    consumer_thread.start()

    # Uvicorn сам корректно обрабатывает SIGTERM/SIGINT
    config = uvicorn.Config(
        app, host="0.0.0.0", port=settings.METRICS_PORT, log_level="info",
    )
    server = uvicorn.Server(config)
    logger.info("Starting HTTP server on :%s", settings.METRICS_PORT)

    try:
        server.run()   # блокируется до SIGTERM/SIGINT
    finally:
        logger.info("HTTP server stopped, signalling consumer to exit...")
        shutdown_event.set()
        consumer_thread.join(timeout=10)
        logger.info("Notification service stopped")


if __name__ == "__main__":
    main()