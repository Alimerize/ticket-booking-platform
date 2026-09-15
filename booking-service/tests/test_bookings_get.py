"""Тесты GET /bookings/{id}."""

import pytest


@pytest.mark.unit
def test_get_booking_returns_existing(client, mock_publish):
    created = client.post(
        "/bookings/",
        json={"user_id": 3, "event_name": "Opera", "seat_number": "C3"},
    ).json()

    r = client.get(f"/bookings/{created['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == created["id"]
    assert body["event_name"] == "Opera"


@pytest.mark.unit
def test_get_booking_returns_404_when_missing(client):
    r = client.get("/bookings/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Booking not found"
