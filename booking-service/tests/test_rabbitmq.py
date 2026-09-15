"""Unit-тесты publish_event — с моком pika."""

import json

import pika
import pytest
from unittest.mock import MagicMock

from app import rabbitmq


@pytest.mark.unit
def test_publish_event_success(monkeypatch):
    fake_channel = MagicMock()
    fake_connection = MagicMock()
    fake_connection.channel.return_value = fake_channel
    fake_connection.is_open = True

    def fake_make_connection():
        return fake_connection

    monkeypatch.setattr(rabbitmq, "_make_connection", fake_make_connection)

    ok = rabbitmq.publish_event({"booking_id": 1, "user_id": 1})
    assert ok is True

    fake_channel.queue_declare.assert_called_once()
    fake_channel.basic_publish.assert_called_once()
    call = fake_channel.basic_publish.call_args
    body = json.loads(call.kwargs["body"])
    assert body["booking_id"] == 1
    assert call.kwargs["properties"].delivery_mode == 2  # persistent


@pytest.mark.unit
def test_publish_event_returns_false_after_all_retries(monkeypatch):
    from app.config import settings

    def boom():
        raise pika.exceptions.AMQPConnectionError("nope")

    monkeypatch.setattr(rabbitmq, "_make_connection", boom)
    monkeypatch.setattr(settings, "PUBLISH_RETRY_DELAY", 0)

    ok = rabbitmq.publish_event({"booking_id": 2})
    assert ok is False
