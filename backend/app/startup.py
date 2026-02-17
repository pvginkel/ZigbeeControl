"""App-specific startup hooks.

Hook points called by create_app():
  - create_container()
  - register_blueprints()
  - register_root_blueprints()
  - register_error_handlers()

Hook points called by CLI command handlers:
  - register_cli_commands()
  - post_migration_hook()
  - load_test_data_hook()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from flask import Blueprint, Flask, jsonify

if TYPE_CHECKING:
    import click

from app.exceptions import (
    ConfigError,
    RestartError,
    RestartInProgress,
    TabLookupError,
    TabNotRestartable,
)
from app.services.container import ServiceContainer

logger = logging.getLogger(__name__)


def create_container() -> ServiceContainer:
    """Create and configure the application's service container."""
    return ServiceContainer()


def register_blueprints(api_bp: Blueprint, app: Flask) -> None:
    """Register all app-specific blueprints on api_bp (under /api prefix)."""
    if not api_bp._got_registered_once:  # type: ignore[attr-defined]
        from app.api.config import config_bp
        from app.api.restart import restart_bp

        api_bp.register_blueprint(config_bp)
        api_bp.register_blueprint(restart_bp)

    # Force TabStatusService singleton initialization so it registers the
    # on_connect callback with the SSE connection manager.
    app.container.tab_status_service()


def register_root_blueprints(app: Flask) -> None:
    """Register app-specific blueprints directly on the app (not under /api prefix)."""
    pass


def register_error_handlers(app: Flask) -> None:
    """Register app-specific error handlers."""
    from app.utils import get_current_correlation_id

    @app.errorhandler(TabNotRestartable)
    def handle_tab_not_restartable(exc: TabNotRestartable):
        return jsonify({"error": str(exc), "correlationId": get_current_correlation_id()}), 400

    @app.errorhandler(TabLookupError)
    def handle_tab_lookup_error(exc: TabLookupError):
        return jsonify({"error": str(exc), "correlationId": get_current_correlation_id()}), 404

    @app.errorhandler(RestartInProgress)
    def handle_restart_in_progress(exc: RestartInProgress):
        return jsonify({"error": str(exc), "correlationId": get_current_correlation_id()}), 409

    @app.errorhandler(RestartError)
    def handle_restart_error(exc: RestartError):
        logger.exception("Restart error: %s", exc)
        return jsonify({"error": str(exc), "correlationId": get_current_correlation_id()}), 500

    @app.errorhandler(ConfigError)
    def handle_config_error(exc: ConfigError):
        logger.exception("Configuration error: %s", exc)
        return jsonify({"error": str(exc), "correlationId": get_current_correlation_id()}), 500


def register_cli_commands(cli: click.Group) -> None:
    """Register app-specific CLI commands."""
    pass


def post_migration_hook(app: Flask) -> None:
    """Run after database migrations (e.g., sync master data)."""
    pass


def load_test_data_hook(app: Flask) -> None:
    """Load test fixtures after database recreation."""
    pass
