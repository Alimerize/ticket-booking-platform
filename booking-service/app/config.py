import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@postgres:5432/booking_db",
    )

    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@rabbitmq:5672/",
    )
    RABBITMQ_QUEUE: str = os.getenv("QUEUE_NAME", "booking_events")

    PUBLISH_MAX_RETRIES: int = int(os.getenv("PUBLISH_MAX_RETRIES", "3"))
    PUBLISH_RETRY_DELAY: float = float(os.getenv("PUBLISH_RETRY_DELAY", "1.0"))

    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
