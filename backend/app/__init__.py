"""Application factory for the Z2M Wrapper backend."""

from __future__ import annotations

import os

from flask import Flask
from spectree import SpecTree

from app.api import create_api_blueprint
from app.services.config_service import ConfigService
from app.services.exceptions import ConfigLoadFailed
from app.services.kubernetes_service import KubernetesService
from app.services.status_broadcaster import StatusBroadcaster
from app.utils.config_loader import load_tabs_config


def create_app(*, config_path: str | None = None) -> Flask:
    """Application factory used by both tests and runtime."""

    app = Flask(__name__)

    path = config_path or os.environ.get("APP_TABS_CONFIG")
    if not path:
        raise ConfigLoadFailed("APP_TABS_CONFIG environment variable is required")

    tabs_config = load_tabs_config(path)
    config_service = ConfigService(tabs_config.tabs)
    status_broadcaster = StatusBroadcaster(config_service.tab_count())
    kubernetes_service = KubernetesService(status_broadcaster=status_broadcaster)

    app.extensions.setdefault("z2m", {})
    app.extensions["z2m"].update(
        {
            "config_service": config_service,
            "status_broadcaster": status_broadcaster,
            "kubernetes_service": kubernetes_service,
        }
    )

    spectree = SpecTree("flask", title="Z2M Wrapper API", version="1.0.0")
    api_blueprint = create_api_blueprint(
        config_service=config_service,
        kubernetes_service=kubernetes_service,
        status_broadcaster=status_broadcaster,
        spectree=spectree,
    )
    app.register_blueprint(api_blueprint)
    spectree.register(app)

    return app

