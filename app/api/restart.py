"""Restart endpoint implementation."""

from __future__ import annotations

from flask import Blueprint
from spectree import Response, SpecTree

from app.schemas.status import RestartResponse, StatusPayload, StatusState
from app.services.config_service import ConfigService
from app.services.kubernetes_service import KubernetesService


def register_restart_routes(
    bp: Blueprint,
    config_service: ConfigService,
    kubernetes_service: KubernetesService,
    spectree: SpecTree,
) -> None:
    """Register restart routes on the blueprint."""

    @bp.post("/restart/<int:idx>")
    @spectree.validate(resp=Response(HTTP_200=RestartResponse))
    def restart_tab(idx: int) -> dict:
        tab = config_service.assert_restartable(idx)
        kubernetes_service.request_restart(idx, tab)
        payload = StatusPayload(state=StatusState.RESTARTING)
        response = RestartResponse(status=payload.state)
        return response.model_dump()

