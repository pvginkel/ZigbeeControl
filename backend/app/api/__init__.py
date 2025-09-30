"""API blueprint factory."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from spectree import SpecTree

from app.api.auth import register_auth_routes
from app.api.config import register_config_routes
from app.api.restart import register_restart_routes
from app.api.status import register_status_routes
from app.schemas.auth import AuthErrorResponse
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
from app.utils.auth import AuthManager, AuthValidationError


def create_api_blueprint(
    *,
    config_service: ConfigService,
    kubernetes_service: KubernetesService,
    status_broadcaster: StatusBroadcaster,
    auth_manager: AuthManager,
    spectree: SpecTree,
) -> Blueprint:
    blueprint = Blueprint("api", __name__, url_prefix="/api")

    register_auth_routes(blueprint, auth_manager, spectree)
    register_config_routes(blueprint, config_service, spectree)
    register_restart_routes(blueprint, config_service, kubernetes_service, spectree)
    register_status_routes(blueprint, config_service, status_broadcaster)

    _auth_exempt_endpoints = {"api.login", "api.auth_check"}

    @blueprint.before_request
    def _require_authentication():
        if auth_manager.disabled:
            return None
        if request.endpoint in _auth_exempt_endpoints:
            return None
        try:
            auth_manager.require_request_auth(request)
        except AuthValidationError as exc:
            response = AuthErrorResponse(error=exc.message)
            return jsonify(response.model_dump()), HTTPStatus.FORBIDDEN

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
