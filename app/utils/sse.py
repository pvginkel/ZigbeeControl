"""Helpers for producing Server-Sent Events responses."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Generator, Iterable, Union

from flask import Response, stream_with_context

from app.schemas.status import StatusPayload

DEFAULT_RETRY_MILLISECONDS = 3000


@dataclass(frozen=True)
class HeartbeatEvent:
    """Represents an SSE heartbeat message."""

    retry: int = DEFAULT_RETRY_MILLISECONDS
    data: str = "{}"


SseMessage = Union[StatusPayload, HeartbeatEvent]


def format_status_event(payload: StatusPayload, *, retry: int = DEFAULT_RETRY_MILLISECONDS) -> str:
    body = payload.model_dump()
    return "\n".join(
        [
            f"retry: {retry}",
            "event: status",
            f"data: {json.dumps(body)}",
            "",
        ]
    ) + "\n"


def format_heartbeat_event(event: HeartbeatEvent) -> str:
    return "\n".join(
        [
            f"retry: {event.retry}",
            "event: heartbeat",
            f"data: {event.data}",
            "",
        ]
    ) + "\n"


def iter_sse_events(source: Iterable[SseMessage]) -> Generator[str, None, None]:
    for message in source:
        if isinstance(message, HeartbeatEvent):
            yield format_heartbeat_event(message)
        else:
            yield format_status_event(message)


def sse_response(source: Iterable[SseMessage]) -> Response:
    """Wrap an iterable of SSE messages into a Flask streaming response."""

    def _generate() -> Generator[str, None, None]:
        yield from iter_sse_events(source)

    response = Response(stream_with_context(_generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers.setdefault("X-Accel-Buffering", "no")
    return response
