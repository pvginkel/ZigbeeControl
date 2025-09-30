from __future__ import annotations

from flask import Flask

from app.schemas.status import StatusPayload, StatusState
from app.utils.sse import (
    HeartbeatEvent,
    format_heartbeat_event,
    format_status_event,
    sse_response,
)


def test_format_status_event_contains_expected_lines():
    payload = StatusPayload(state=StatusState.RESTARTING, message="deploying")
    event = format_status_event(payload)
    assert event.startswith("retry: 3000\nevent: status\n")
    assert '"state": "restarting"' in event
    assert event.endswith("\n\n")


def test_format_heartbeat_event_contains_expected_lines():
    event = format_heartbeat_event(HeartbeatEvent(retry=5000))
    assert event.startswith("retry: 5000\nevent: heartbeat\n")
    assert "data: {}" in event
    assert event.endswith("\n\n")


def test_sse_response_sets_headers_and_streams_payload():
    payloads = [
        StatusPayload(state=StatusState.RUNNING),
        HeartbeatEvent(),
        StatusPayload(state=StatusState.ERROR, message="boom"),
    ]
    app = Flask(__name__)
    with app.test_request_context():
        response = sse_response(payloads)
        assert response.mimetype == "text/event-stream"
        assert response.headers["Cache-Control"] == "no-cache"
        body = "".join(response.response)
        assert body.count("event: status") == 2
        assert body.count("event: heartbeat") == 1


def test_sse_response_streams_heartbeat_only_sequence():
    app = Flask(__name__)
    with app.test_request_context():
        response = sse_response([HeartbeatEvent() for _ in range(3)])
        body = "".join(response.response)
        assert "event: status" not in body
        assert body.count("event: heartbeat") == 3
