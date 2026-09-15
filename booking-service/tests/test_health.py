import pytest


@pytest.mark.unit
def test_healthz_returns_ok(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.unit
def test_readyz_returns_ready_when_db_ok(client):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


@pytest.mark.unit
def test_readyz_returns_503_when_db_down(client, db_session):
    """Если SELECT 1 падает — /readyz отдаёт 503."""
    from sqlalchemy.exc import OperationalError

    def boom(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection lost"))

    original_execute = db_session.execute
    db_session.execute = boom
    try:
        r = client.get("/readyz")
        assert r.status_code == 503
        assert r.json()["status"] == "not ready"
    finally:
        db_session.execute = original_execute
