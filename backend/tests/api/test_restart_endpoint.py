"""Tests for the /api/restart endpoint."""

from __future__ import annotations

from app.exceptions import RestartInProgress


def test_restart_triggers_service(app, client, monkeypatch):
    kubernetes_service = app.container.kubernetes_service()
    captured = {}

    def fake_request(idx, tab):
        captured["called"] = (idx, tab)

    monkeypatch.setattr(kubernetes_service, "request_restart", fake_request)

    response = client.post("/api/restart/1")
    assert response.status_code == 200
    assert response.get_json() == {"status": "restarting", "message": None}
    assert captured["called"][0] == 1
    assert captured["called"][1].k8s is not None


def test_restart_duplicate_guard(app, client, monkeypatch):
    kubernetes_service = app.container.kubernetes_service()

    def raise_in_progress(idx, tab):
        raise RestartInProgress(namespace="default", deployment="code-server")

    monkeypatch.setattr(kubernetes_service, "request_restart", raise_in_progress)

    response = client.post("/api/restart/1")
    assert response.status_code == 409
    payload = response.get_json()
    assert "restart already in progress" in payload["error"]


def test_restart_non_restartable_tab(client):
    response = client.post("/api/restart/0")
    assert response.status_code == 400
    payload = response.get_json()
    assert "not restartable" in payload["error"]


def test_restart_invalid_tab_index(client):
    response = client.post("/api/restart/99")
    assert response.status_code == 404
    payload = response.get_json()
    assert "out of range" in payload["error"]
