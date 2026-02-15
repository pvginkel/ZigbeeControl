"""Tracks per-tab status and delivers events through SSE Gateway."""

from __future__ import annotations

import logging

from app.schemas.status import StatusPayload, StatusState
from app.services.config_service import ConfigService
from app.services.sse_connection_manager import SSEConnectionManager

logger = logging.getLogger(__name__)


class TabStatusService:
    """Publishes per-tab status updates via SSE Gateway."""

    def __init__(self, config_service: ConfigService, sse_connection_manager: SSEConnectionManager) -> None:
        self._sse = sse_connection_manager
        tab_count = config_service.tab_count()
        self._last: list[StatusPayload] = [
            StatusPayload(state=StatusState.RUNNING) for _ in range(tab_count)
        ]
        self._sse.register_on_connect(self._on_client_connect)
        logger.info("TabStatusService initialised with %d tabs", tab_count)

    def current(self, idx: int) -> StatusPayload:
        """Return the last known status for the given tab."""
        return self._last[idx]

    def emit(self, idx: int, payload: StatusPayload) -> None:
        """Record and broadcast a new status payload to all connected clients."""
        self._last[idx] = payload
        event_data = {"tab_index": idx, "state": payload.state.value, "message": payload.message}
        self._sse.send_event(None, event_data, "tab_status", "status")

    def _on_client_connect(self, request_id: str) -> None:
        """Send current status for ALL tabs to a newly connected client."""
        for idx, payload in enumerate(self._last):
            event_data = {"tab_index": idx, "state": payload.state.value, "message": payload.message}
            self._sse.send_event(request_id, event_data, "tab_status", "status")
