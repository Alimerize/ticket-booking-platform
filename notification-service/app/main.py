import sys
import time
import json
import signal
import logging
import pika
from prometheus_client import Counter, start_http_server

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

shutdown_requested = False


def handle_shutdown(signum, frame):
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


def callback(ch, method, properties, body):
    try:
        payload = json.loads(body)
        logger.info(f"Received notification event: booking_id={payload.get('booking_id')}")

        # Эмуляция отправки (заменить на реальный email/SMS-провайдер)
        time.sleep(0.5)

        NOTIFICATIONS_SENT.inc()
        logger.info(f"Notification sent: booking_id={payload.get('booking_id')}")

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        NOTIFICATIONS_FAILED.inc()
        logger.error(f"Failed to process notification: {exc}")
        # Отправляем в dead-letter или nack без requeue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main() -> None:
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    start_http_server(settings.METRICS_PORT)
    logger.info(f"Metrics server started on :{settings.METRICS_PORT}")

    while not shutdown_requested:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    heartbeat=30,
                    blocked_connection_timeout=10,
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(
                queue=settings.RABBITMQ_QUEUE,
                on_message_callback=callback,
                auto_ack=False,
            )
            logger.info("Waiting for messages...")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as exc:
            if shutdown_requested:
                break
            logger.warning(f"RabbitMQ unavailable ({exc}), retrying in {settings.RECONNECT_DELAY}s")
            time.sleep(settings.RECONNECT_DELAY)

    logger.info("Notification service stopped")


if __name__ == "__main__":
    main()