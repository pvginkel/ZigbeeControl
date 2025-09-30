from __future__ import annotations

from flask import Flask

from app.schemas.status import StatusPayload, StatusState
from app.utils.sse import format_status_event, sse_response


def test_format_status_event_contains_expected_lines():
    payload = StatusPayload(state=StatusState.RESTARTING, message="deploying")
    event = format_status_event(payload)
    assert event.startswith("retry: 3000\nevent: status\n")
    assert '"state": "restarting"' in event
    assert event.endswith("\n\n")


def test_sse_response_sets_headers_and_streams_payload():
    payloads = [StatusPayload(state=StatusState.RUNNING)]
    app = Flask(__name__)
    with app.test_request_context():
        response = sse_response(payloads)
        assert response.mimetype == "text/event-stream"
        assert response.headers["Cache-Control"] == "no-cache"
        body = "".join(response.response)
        assert "event: status" in body

