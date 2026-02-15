"""Tests for TabStatusService."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.schemas.config import TabConfig
from app.schemas.status import StatusPayload, StatusState
from app.services.config_service import ConfigService
from app.services.tab_status_service import TabStatusService


def _make_service(tab_count: int = 2) -> tuple[TabStatusService, MagicMock]:
    """Create a TabStatusService with a mocked SSE connection manager."""
    tabs = [
        TabConfig(
            text=f"Tab {i}",
            iconUrl=f"https://example.com/icon-{i}.svg",
            iframeUrl=f"https://example.com/tab-{i}",
        )
        for i in range(tab_count)
    ]
    config_svc = ConfigService(tabs)
    mock_sse = MagicMock()
    service = TabStatusService(config_svc, mock_sse)
    return service, mock_sse


def test_initial_state_is_running():
    service, _ = _make_service(2)
    for idx in range(2):
        assert service.current(idx).state == StatusState.RUNNING
        assert service.current(idx).message is None


def test_emit_updates_state_and_broadcasts():
    service, mock_sse = _make_service(2)
    payload = StatusPayload(state=StatusState.RESTARTING)
    service.emit(0, payload)

    assert service.current(0).state == StatusState.RESTARTING
    mock_sse.send_event.assert_called_with(
        None,
        {"tab_index": 0, "state": "restarting", "message": None},
        "tab_status",
        "status",
    )


def test_emit_with_message():
    service, mock_sse = _make_service(1)
    payload = StatusPayload(state=StatusState.ERROR, message="something broke")
    service.emit(0, payload)

    assert service.current(0).state == StatusState.ERROR
    assert service.current(0).message == "something broke"
    mock_sse.send_event.assert_called_with(
        None,
        {"tab_index": 0, "state": "error", "message": "something broke"},
        "tab_status",
        "status",
    )


def test_on_client_connect_sends_current_state():
    service, mock_sse = _make_service(2)
    # Set tab 1 to a non-default state
    service.emit(1, StatusPayload(state=StatusState.ERROR, message="broken"))
    mock_sse.reset_mock()

    # Simulate client connect
    service._on_client_connect("req-123")

    assert mock_sse.send_event.call_count == 2
    mock_sse.send_event.assert_any_call(
        "req-123",
        {"tab_index": 0, "state": "running", "message": None},
        "tab_status",
        "status",
    )
    mock_sse.send_event.assert_any_call(
        "req-123",
        {"tab_index": 1, "state": "error", "message": "broken"},
        "tab_status",
        "status",
    )


def test_registers_on_connect_callback():
    _, mock_sse = _make_service(1)
    mock_sse.register_on_connect.assert_called_once()
    callback = mock_sse.register_on_connect.call_args[0][0]
    assert callable(callback)
