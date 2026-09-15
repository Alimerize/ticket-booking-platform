import json
import logging
import time

import pika

from .config import settings

logger = logging.getLogger(__name__)


def _make_connection() -> pika.BlockingConnection:
    params = pika.URLParameters(settings.RABBITMQ_URL)
    params.heartbeat = 30
    params.blocked_connection_timeout = 10
    return pika.BlockingConnection(params)


def publish_event(payload: dict) -> bool:
    body = json.dumps(payload, default=str).encode("utf-8")
    last_exc: Exception | None = None

    for attempt in range(1, settings.PUBLISH_MAX_RETRIES + 1):
        try:
            conn = _make_connection()
            try:
                ch = conn.channel()
                ch.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
                ch.basic_publish(
                    exchange="",
                    routing_key=settings.RABBITMQ_QUEUE,
                    body=body,
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # persistent
                        content_type="application/json",
                    ),
                )
                logger.info(
                    "Published event to %s (attempt %d)",
                    settings.RABBITMQ_QUEUE,
                    attempt,
                )
                return True
            finally:
                if conn.is_open:
                    conn.close()
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Publish attempt %d/%d failed: %s",
                attempt,
                settings.PUBLISH_MAX_RETRIES,
                exc,
            )
            if attempt < settings.PUBLISH_MAX_RETRIES:
                time.sleep(settings.PUBLISH_RETRY_DELAY * attempt)  # backoff

    logger.error(
        "Failed to publish event after %d attempts: %s",
        settings.PUBLISH_MAX_RETRIES,
        last_exc,
    )
    return False
