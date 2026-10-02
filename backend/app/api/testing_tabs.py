"""Testing endpoint that broadcasts a tab status without touching Kubernetes.

The Playwright suite has no cluster to restart, so it drives the UI's restart
handling by pushing the same `tab_status` events KubernetesService emits.
"""

from __future__ import annotations

from typing import Any

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, request
from spectree import Response

from app.schemas.status import StatusPayload
from app.services.config_service import ConfigService
from app.services.container import ServiceContainer
from app.services.tab_status_service import TabStatusService
from app.utils.spectree_config import api

testing_tabs_bp = Blueprint("testing_tabs", __name__, url_prefix="/testing")


@testing_tabs_bp.before_request
def check_testing_mode() -> Any:
    """Reject requests when the server is not running in testing mode."""
    from app.api.testing_guard import reject_if_not_testing

    return reject_if_not_testing()


@testing_tabs_bp.post("/tabs/<int:idx>/status")
@api.validate(json=StatusPayload, resp=Response(HTTP_204=None))
@inject
def emit_tab_status(
    idx: int,
    config_service: ConfigService = Provide[ServiceContainer.config_service],
    tab_status_service: TabStatusService = Provide[ServiceContainer.tab_status_service],
) -> tuple[str, int]:
    """Broadcast a tab status event to every connected client."""
    config_service.get_tab(idx)
    payload = StatusPayload.model_validate(request.get_json())
    tab_status_service.emit(idx, payload)
    return "", 204
