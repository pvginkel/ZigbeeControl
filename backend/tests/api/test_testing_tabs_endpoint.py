"""Tests for the /api/testing/tabs/<idx>/status endpoint."""

from __future__ import annotations

from app.schemas.status import StatusState


def test_emit_tab_status_records_and_broadcasts(app, client):
    response = client.post(
        "/api/testing/tabs/1/status", json={"state": "error", "message": "boom"}
    )
    assert response.status_code == 204

    payload = app.container.tab_status_service().current(1)
    assert payload.state == StatusState.ERROR
    assert payload.message == "boom"


def test_emit_tab_status_rejects_unknown_state(client):
    response = client.post("/api/testing/tabs/1/status", json={"state": "sleeping"})
    assert response.status_code == 400


def test_emit_tab_status_invalid_tab_index(client):
    response = client.post("/api/testing/tabs/99/status", json={"state": "running"})
    assert response.status_code == 404
