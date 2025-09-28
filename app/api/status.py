"""Status streaming endpoint implementation."""

from __future__ import annotations

from flask import Blueprint

from app.services.config_service import ConfigService
from app.services.status_broadcaster import StatusBroadcaster
from app.utils.sse import sse_response


def register_status_routes(bp: Blueprint, config_service: ConfigService, broadcaster: StatusBroadcaster) -> None:
    """Register status streaming routes on the blueprint."""

    @bp.get("/status/<int:idx>/stream")
    def stream_status(idx: int):
        # Ensure the tab index is valid even for non-restartable tabs.
        config_service.get_tab(idx)
        stream = broadcaster.listen(idx)
        return sse_response(stream)

