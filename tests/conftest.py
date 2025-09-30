from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Callable, Generator

import pytest

from app import create_app


TEST_AUTH_TOKEN = "unit-test-token"


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
                tabColor: "#123456"
              - text: Code Server
                iconUrl: https://example.com/icon-b.svg
                iframeUrl: https://example.com/code
                tabColor: "#654321"
                k8s:
                  namespace: default
                  deployment: code-server
            """
        ).strip()
    )
    return path


@pytest.fixture
def app(tabs_config_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("APP_ALLOWED_ORIGINS", raising=False)
    monkeypatch.setenv("APP_AUTH_TOKEN", TEST_AUTH_TOKEN)
    monkeypatch.delenv("APP_AUTH_DISABLED", raising=False)
    monkeypatch.setenv("APP_SECRET_KEY", "unit-test-secret")
    monkeypatch.setenv("FLASK_ENV", "production")
    flask_app = create_app(config_path=str(tabs_config_path))
    flask_app.testing = True
    return flask_app


@pytest.fixture
def client(app) -> Generator:
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_token() -> str:
    return TEST_AUTH_TOKEN


@pytest.fixture
def authenticate(client, auth_token) -> Callable[[str | None], None]:
    """Authenticate the Flask test client using the login endpoint."""

    def _authenticate(token: str | None = None) -> None:
        payload = {"token": token or auth_token}
        response = client.post("/api/auth/login", json=payload)
        assert response.status_code == 200

    return _authenticate
