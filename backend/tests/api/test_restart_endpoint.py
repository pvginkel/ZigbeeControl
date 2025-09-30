from __future__ import annotations

import pytest

from app.services.exceptions import RestartInProgress


def test_restart_requires_auth(client):
    response = client.post("/api/restart/1")
    assert response.status_code == 403
    assert response.get_json() == {"error": "missing authentication cookie"}


def test_restart_triggers_service(app, client, authenticate, monkeypatch):
    service = app.extensions["z2m"]["kubernetes_service"]
    captured = {}

    def fake_request(idx, tab):
        captured["called"] = (idx, tab)

    monkeypatch.setattr(service, "request_restart", fake_request)

    authenticate()
    response = client.post("/api/restart/1")
    assert response.status_code == 200
    assert response.get_json() == {"status": "restarting", "message": None}
    assert captured["called"][0] == 1
    assert captured["called"][1].k8s is not None


def test_restart_duplicate_guard(client, app, authenticate, monkeypatch):
    service = app.extensions["z2m"]["kubernetes_service"]

    def raise_in_progress(idx, tab):
        raise RestartInProgress(namespace="default", deployment="code-server")

    monkeypatch.setattr(service, "request_restart", raise_in_progress)

    authenticate()
    response = client.post("/api/restart/1")
    assert response.status_code == 409
    payload = response.get_json()
    assert "restart already in progress" in payload["error"]


def test_restart_non_restartable_tab(client, authenticate):
    authenticate()
    response = client.post("/api/restart/0")
    assert response.status_code == 400
    payload = response.get_json()
    assert "not restartable" in payload["error"]
