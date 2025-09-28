"""Config endpoint implementation."""

from __future__ import annotations

from flask import Blueprint
from spectree import Response, SpecTree

from app.schemas.config import ConfigResponse
from app.services.config_service import ConfigService


def register_config_routes(bp: Blueprint, config_service: ConfigService, spectree: SpecTree) -> None:
    """Register configuration routes on the blueprint."""

    @bp.get("/config")
    @spectree.validate(resp=Response(HTTP_200=ConfigResponse))
    def get_config() -> dict:
        response = config_service.to_response()
        return response.model_dump()

