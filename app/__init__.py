"""Application factory for the Z2M Wrapper backend."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from flask import Flask
from spectree import SpecTree

from app.api import create_api_blueprint
from app.services.config_service import ConfigService
from app.services.exceptions import AuthConfigError, ConfigError, ConfigLoadFailed
from app.services.kubernetes_service import KubernetesService
from app.services.status_broadcaster import StatusBroadcaster
from app.utils.auth import AuthConfig, AuthManager
from app.utils.config_loader import load_tabs_config
from app.utils.cors import configure_cors, parse_allowed_origins

logger = logging.getLogger(__name__)


def create_app(*, config_path: str | None = None) -> Flask:
    """Application factory used by both tests and runtime."""

    logger.info("Creating app")

    app = Flask(__name__)

    load_dotenv()

    flask_env = os.environ.get("FLASK_ENV", "production")

    path = config_path or os.environ.get("APP_TABS_CONFIG")
    if not path:
        raise ConfigLoadFailed("APP_TABS_CONFIG environment variable is required")

    tabs_config = load_tabs_config(path)
    config_service = ConfigService(tabs_config.tabs)
    status_broadcaster = StatusBroadcaster(config_service.tab_count())
    kubernetes_service = KubernetesService(status_broadcaster=status_broadcaster)

    heartbeat_interval = _resolve_heartbeat_interval(
        flask_env=flask_env,
        raw_value=os.environ.get("APP_SSE_HEARTBEAT_SECONDS"),
    )

    allowed_origins = parse_allowed_origins(os.environ.get("APP_ALLOWED_ORIGINS"))
    if allowed_origins:
        configure_cors(app, allowed_origins)

    auth_disabled = os.environ.get("APP_AUTH_DISABLED", "").lower() in {"1", "true", "yes", "on"}
    auth_token = os.environ.get("APP_AUTH_TOKEN")
    auth_cookie_name = os.environ.get("APP_AUTH_COOKIE_NAME", "z2m_auth")
    jwt_secret = os.environ.get("APP_AUTH_JWT_SECRET") or auth_token or ""

    if not auth_disabled and not auth_token:
        raise AuthConfigError("APP_AUTH_TOKEN environment variable is required when authentication is enabled")

    secret_key = os.environ.get("APP_SECRET_KEY") or (jwt_secret if jwt_secret else None)
    if secret_key:
        app.secret_key = secret_key

    secure_cookies = flask_env.lower() == "production"

    auth_manager = AuthManager(
        AuthConfig(
            login_token=auth_token,
            cookie_name=auth_cookie_name,
            jwt_secret=jwt_secret,
            disabled=auth_disabled,
            secure_cookies=secure_cookies,
        )
    )

    app.extensions.setdefault("z2m", {})
    app.extensions["z2m"].update(
        {
            "config_service": config_service,
            "status_broadcaster": status_broadcaster,
            "kubernetes_service": kubernetes_service,
            "auth_manager": auth_manager,
            "sse_heartbeat_seconds": heartbeat_interval,
        }
    )

    app.config.setdefault("SSE_HEARTBEAT_SECONDS", heartbeat_interval)

    spectree = SpecTree("flask", title="Z2M Wrapper API", version="1.0.0")
    api_blueprint = create_api_blueprint(
        config_service=config_service,
        kubernetes_service=kubernetes_service,
        status_broadcaster=status_broadcaster,
        auth_manager=auth_manager,
        spectree=spectree,
        status_heartbeat_interval=heartbeat_interval,
    )
    app.register_blueprint(api_blueprint)
    spectree.register(app)

    return app


def _resolve_heartbeat_interval(*, flask_env: str, raw_value: str | None) -> float:
    """Return a positive heartbeat interval based on environment defaults."""

    default = 5.0 if flask_env.lower() == "development" else 30.0
    if raw_value is None or not raw_value.strip():
        return default
    try:
        interval = float(raw_value)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ConfigError("APP_SSE_HEARTBEAT_SECONDS must be a positive number") from exc
    if interval <= 0:
        raise ConfigError("APP_SSE_HEARTBEAT_SECONDS must be greater than zero")
    return interval
