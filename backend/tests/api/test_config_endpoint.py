"""Tests for the /api/config endpoint."""

from __future__ import annotations


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
