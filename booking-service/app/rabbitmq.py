import json
import logging
import time
import pika
from .config import settings

logger = logging.getLogger(__name__)


def publish_event(payload: dict) -> bool:
    """
    Publish a message to RabbitMQ with exponential backoff.
    Returns True on success, False on final failure.
    """
    attempt = 0
    delay = settings.RABBITMQ_RETRY_DELAY

    while attempt < settings.RABBITMQ_RETRY_ATTEMPTS:
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
            channel.basic_publish(
                exchange="",
                routing_key=settings.RABBITMQ_QUEUE,
                body=json.dumps(payload),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent
                    content_type="application/json",
                ),
            )
            connection.close()
            logger.info("Event published", extra={"event": payload.get("event_type")})
            return True
        except pika.exceptions.AMQPError as exc:
            attempt += 1
            logger.warning(
                f"RabbitMQ publish failed (attempt {attempt}/{settings.RABBITMQ_RETRY_ATTEMPTS}): {exc}"
            )
            time.sleep(delay)
            delay *= 2  # exponential backoff

    logger.error("RabbitMQ publish failed after all retries — event dropped")
    return False