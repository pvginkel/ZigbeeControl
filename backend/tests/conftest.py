"""Pytest configuration and fixtures.

Infrastructure fixtures (app, client, OIDC, SSE) are defined in
conftest_infrastructure.py. This file re-exports them and adds app-specific
domain fixtures.
"""

import textwrap
from pathlib import Path

import pytest

from app.app_config import AppSettings
from app.services.config_service import ConfigService
from app.utils.config_loader import load_tabs_config

# Import all infrastructure fixtures
from tests.conftest_infrastructure import *  # noqa: F401, F403


@pytest.fixture
def tabs_config_path(tmp_path: Path) -> Path:
    """Write a temporary tabs config YAML and return its path."""
    path = tmp_path / "tabs.yml"
    path.write_text(
        textwrap.dedent("""\
            tabs:
              - text: Primary Dashboard
                iconUrl: https://example.com/icon-a.svg
                iframeUrl: https://example.com/dashboard
                tabColor: "#123456"
              - text: Code Server
                iconUrl: https://example.com/icon-b.svg
                iframeUrl: https://example.com/code
                tabColor: "#654321"
                k8s:
                  namespace: default
                  deployment: code-server
        """)
    )
    return path


@pytest.fixture
def test_app_settings(tabs_config_path: Path) -> AppSettings:
    """Override infrastructure test_app_settings to include tabs config path."""
    return AppSettings(
        tabs_config_path=str(tabs_config_path),
        k8s_restart_timeout=5,
    )


@pytest.fixture(autouse=True)
def _mock_kube_config(monkeypatch):
    """Prevent Kubernetes config loading during tests."""
    monkeypatch.setattr(
        "app.services.kubernetes_service.config.load_kube_config",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.services.kubernetes_service.config.load_incluster_config",
        lambda: None,
    )


@pytest.fixture
def config_service(tabs_config_path: Path) -> ConfigService:
    """Create a ConfigService from the test tabs config."""
    tabs_config = load_tabs_config(str(tabs_config_path))
    return ConfigService(tabs_config.tabs)
