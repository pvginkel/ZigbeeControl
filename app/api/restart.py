"""Restart endpoint implementation."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from flask import Blueprint
from spectree import Response

from app.schemas.status import RestartResponse, StatusState
from app.services.config_service import ConfigService
from app.services.container import ServiceContainer
from app.services.kubernetes_service import KubernetesService
from app.utils.spectree_config import api

restart_bp = Blueprint("restart", __name__)


@restart_bp.post("/restart/<int:idx>")
@api.validate(resp=Response(HTTP_200=RestartResponse))
@inject
def restart_tab(
    idx: int,
    config_service: ConfigService = Provide[ServiceContainer.config_service],
    kubernetes_service: KubernetesService = Provide[ServiceContainer.kubernetes_service],
) -> dict:
    tab = config_service.assert_restartable(idx)
    kubernetes_service.request_restart(idx, tab)
    return RestartResponse(status=StatusState.RESTARTING).model_dump()
