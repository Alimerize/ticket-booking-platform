import os

class Settings:
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_QUEUE: str = os.getenv("RABBITMQ_QUEUE", "booking_notifications")
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8000"))
    RECONNECT_DELAY: float = float(os.getenv("RECONNECT_DELAY", "5.0"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()