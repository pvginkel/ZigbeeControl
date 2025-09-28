from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Generator

import pytest

from app import create_app


@pytest.fixture(autouse=True)
def _mock_kube_config(monkeypatch):
    monkeypatch.setattr(
        "app.services.kubernetes_service.config.load_kube_config",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.services.kubernetes_service.config.load_incluster_config",
        lambda: None,
    )


@pytest.fixture
def tabs_config_path(tmp_path: Path) -> Path:
    path = tmp_path / "tabs.yml"
    path.write_text(
        textwrap.dedent(
            """
            tabs:
              - text: Primary Dashboard
                iconUrl: https://example.com/icon-a.svg
                iframeUrl: https://example.com/dashboard
              - text: Code Server
                iconUrl: https://example.com/icon-b.svg
                iframeUrl: https://example.com/code
                k8s:
                  namespace: default
                  deployment: code-server
            """
        ).strip()
    )
    return path


@pytest.fixture
def app(tabs_config_path: Path):
    flask_app = create_app(config_path=str(tabs_config_path))
    flask_app.testing = True
    return flask_app


@pytest.fixture
def client(app) -> Generator:
    with app.test_client() as client:
        yield client
