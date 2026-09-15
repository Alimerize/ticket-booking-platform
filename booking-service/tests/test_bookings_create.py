"""Тесты POST /bookings/."""

import pytest


@pytest.mark.unit
def test_create_booking_success(client, mock_publish):
    payload = {"user_id": 42, "event_name": "Rock", "seat_number": "A1"}
    r = client.post("/bookings/", json=payload)

    assert r.status_code == 201
    body = r.json()
    assert body["user_id"] == 42
    assert body["event_name"] == "Rock"
    assert body["seat_number"] == "A1"
    assert body["is_confirmed"] is False
    assert isinstance(body["id"], int)

    mock_publish.assert_called_once()
    event = mock_publish.call_args.args[0]
    assert event["booking_id"] == body["id"]
    assert event["user_id"] == 42
    assert event["event_name"] == "Rock"
    assert event["seat_number"] == "A1"


@pytest.mark.unit
def test_create_booking_persists_to_db(client, db_session, mock_publish):
    r = client.post(
        "/bookings/",
        json={"user_id": 7, "event_name": "Jazz", "seat_number": "B2"},
    )
    booking_id = r.json()["id"]

    from app import models

    row = db_session.get(models.Booking, booking_id)
    assert row is not None
    assert row.user_id == 7
    assert row.event_name == "Jazz"
