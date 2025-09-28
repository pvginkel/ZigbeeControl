"""API blueprint factory."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify
from pydantic import ValidationError
from spectree import SpecTree

from app.api.config import register_config_routes
from app.api.restart import register_restart_routes
from app.api.status import register_status_routes
from app.services.config_service import ConfigService
from app.services.exceptions import (
    ConfigError,
    RestartError,
    RestartInProgress,
    TabLookupError,
    TabNotRestartable,
)
from app.services.kubernetes_service import KubernetesService
from app.services.status_broadcaster import StatusBroadcaster


def create_api_blueprint(
    *,
    config_service: ConfigService,
    kubernetes_service: KubernetesService,
    status_broadcaster: StatusBroadcaster,
    spectree: SpecTree,
) -> Blueprint:
    blueprint = Blueprint("api", __name__, url_prefix="/api")

    register_config_routes(blueprint, config_service, spectree)
    register_restart_routes(blueprint, config_service, kubernetes_service, spectree)
    register_status_routes(blueprint, config_service, status_broadcaster)

    @blueprint.errorhandler(TabLookupError)
    def _handle_tab_lookup_error(exc: TabLookupError):
        status = HTTPStatus.NOT_FOUND
        if isinstance(exc, TabNotRestartable):
            status = HTTPStatus.BAD_REQUEST
        return jsonify({"error": str(exc)}), status

    @blueprint.errorhandler(RestartInProgress)
    def _handle_restart_in_progress(exc: RestartInProgress):
        return jsonify({"error": str(exc)}), HTTPStatus.CONFLICT

    @blueprint.errorhandler(RestartError)
    def _handle_restart_error(exc: RestartError):
        return jsonify({"error": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @blueprint.errorhandler(ConfigError)
    def _handle_config_error(exc: ConfigError):
        return jsonify({"error": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @blueprint.errorhandler(ValidationError)
    def _handle_validation_error(exc: ValidationError):
        return jsonify({"error": exc.errors()}), HTTPStatus.UNPROCESSABLE_ENTITY

    return blueprint

