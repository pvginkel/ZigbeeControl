"""Helpers for producing Server-Sent Events responses."""

from __future__ import annotations

import json
from typing import Generator, Iterable

from flask import Response, stream_with_context

from app.schemas.status import StatusPayload


def format_status_event(payload: StatusPayload, *, retry: int = 3000) -> str:
    body = payload.model_dump()
    return "\n".join(
        [
            f"retry: {retry}",
            "event: status",
            f"data: {json.dumps(body)}",
            "",
        ]
    ) + "\n"


def iter_status_events(source: Iterable[StatusPayload]) -> Generator[str, None, None]:
    for payload in source:
        yield format_status_event(payload)


def sse_response(source: Iterable[StatusPayload]) -> Response:
    """Wrap an iterable of status payloads into a Flask streaming response."""

    def _generate() -> Generator[str, None, None]:
        yield from iter_status_events(source)

    response = Response(stream_with_context(_generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers.setdefault("X-Accel-Buffering", "no")
    return response
