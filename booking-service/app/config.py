import os

class Settings:
    """Centralized configuration loaded from environment variables."""
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@postgres:5432/booking_db"
    )
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_QUEUE: str = os.getenv("RABBITMQ_QUEUE", "booking_notifications")
    RABBITMQ_RETRY_ATTEMPTS: int = int(os.getenv("RABBITMQ_RETRY_ATTEMPTS", "5"))
    RABBITMQ_RETRY_DELAY: float = float(os.getenv("RABBITMQ_RETRY_DELAY", "2.0"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()