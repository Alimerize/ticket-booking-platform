"""
Фикстуры для тестов booking-service.

Стратегия:
- SQLite in-memory для скорости (SQLAlchemy работает с ним через тот же API)
- publish_event мокается, чтобы не ходить в RabbitMQ
- TestClient из FastAPI для HTTP-тестов
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("METRICS_PORT", "8000")
os.environ.setdefault("LOG_LEVEL", "WARNING")

from typing import Generator  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app import main as app_main  # noqa: E402
from app import models  # noqa: E402,F401  -- ensure models registered


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture()
def db_session(engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def mock_publish(monkeypatch) -> MagicMock:
    from app import main as main_module

    mock = MagicMock(return_value=True)
    monkeypatch.setattr(main_module, "publish_event", mock)
    return mock


@pytest.fixture()
def client(
    db_session: Session, mock_publish: MagicMock
) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app_main.app.dependency_overrides[get_db] = override_get_db

    with TestClient(app_main.app) as c:
        yield c

    app_main.app.dependency_overrides.clear()
