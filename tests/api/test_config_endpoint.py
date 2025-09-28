from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from app import create_app
from app.services.exceptions import ConfigLoadFailed


def test_get_config_success(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {
        "tabs": [
            {
                "text": "Primary Dashboard",
                "iconUrl": "https://example.com/icon-a.svg",
                "iframeUrl": "https://example.com/dashboard",
                "restartable": False,
                "tabColor": "#123456",
            },
            {
                "text": "Code Server",
                "iconUrl": "https://example.com/icon-b.svg",
                "iframeUrl": "https://example.com/code",
                "restartable": True,
                "tabColor": "#654321",
            },
        ]
    }


def test_create_app_missing_config_path(tmp_path: Path):
    missing_path = tmp_path / "missing.yml"
    with pytest.raises(ConfigLoadFailed):
        create_app(config_path=str(missing_path))


def test_create_app_with_malformed_yaml(tmp_path: Path):
    malformed_path = tmp_path / "broken.yml"
    malformed_path.write_text(textwrap.dedent("""
        tabs:
          - text: OK
            iconUrl: https://example.com/icon.svg
            iframeUrl
    """))
    with pytest.raises(ConfigLoadFailed):
        create_app(config_path=str(malformed_path))
