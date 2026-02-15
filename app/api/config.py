"""Config endpoint implementation."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from flask import Blueprint
from spectree import Response

from app.schemas.config import ConfigResponse
from app.services.config_service import ConfigService
from app.services.container import ServiceContainer
from app.utils.spectree_config import api

config_bp = Blueprint("config", __name__)


@config_bp.get("/config")
@api.validate(resp=Response(HTTP_200=ConfigResponse))
@inject
def get_config(
    config_service: ConfigService = Provide[ServiceContainer.config_service],
) -> dict:
    return config_service.to_response().model_dump()
