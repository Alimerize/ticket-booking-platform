"""Тесты валидации входных данных (Pydantic)."""

import pytest


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload, expected_field",
    [
        ({"user_id": 0, "event_name": "Rock", "seat_number": "A1"}, "user_id"),
        ({"user_id": -1, "event_name": "Rock", "seat_number": "A1"}, "user_id"),
        ({"user_id": 1, "event_name": "", "seat_number": "A1"}, "event_name"),
        ({"user_id": 1, "event_name": "Rock", "seat_number": ""}, "seat_number"),
    ],
)
def test_create_booking_rejects_invalid_payload(client, payload, expected_field):
    r = client.post("/bookings/", json=payload)

    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(expected_field in e["loc"] for e in errors)


@pytest.mark.unit
def test_create_booking_rejects_missing_fields(client):
    r = client.post("/bookings/", json={"user_id": 1})
    assert r.status_code == 422

    locs = [e["loc"][-1] for e in r.json()["detail"]]
    assert "event_name" in locs
    assert "seat_number" in locs


@pytest.mark.unit
def test_create_booking_rejects_wrong_type(client):
    r = client.post(
        "/bookings/",
        json={"user_id": "not-a-number", "event_name": "Rock", "seat_number": "A1"},
    )
    assert r.status_code == 422
