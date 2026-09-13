import os

class Settings:
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"
    )
    RABBITMQ_QUEUE: str = os.getenv("QUEUE_NAME", "booking_events")
    RECONNECT_DELAY: int = int(os.getenv("RECONNECT_DELAY", "5"))
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()