"""Tests for KubernetesService."""

from __future__ import annotations

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from kubernetes.client import ApiException

from app.schemas.config import KubernetesConfig, TabConfig
from app.schemas.status import StatusState
from app.services.kubernetes_service import KubernetesService
from app.services.tab_status_service import TabStatusService


@dataclass
class _FakeStatus:
    available_replicas: int | None = None
    updated_replicas: int | None = None
    ready_replicas: int | None = None
    replicas: int | None = None
    observed_generation: int | None = None
    conditions: list[object] | None = None


@dataclass
class _FakeSpec:
    replicas: int | None = None


@dataclass
class _FakeDeployment:
    metadata: object
    status: _FakeStatus
    spec: _FakeSpec


@dataclass
class _FakeMetadata:
    generation: int


@dataclass
class _FakeCondition:
    type: str
    status: str
    reason: str | None = None
    message: str | None = None
    observed_generation: int | None = None


class _FakeAppsApi:
    def __init__(self, stream_events, status_obj=None):
        self.stream_events = stream_events
        self.patched = []
        self.list_calls = []
        self.status_obj = status_obj

    def patch_namespaced_deployment(self, name: str, namespace: str, body):
        self.patched.append((name, namespace, body))

    def read_namespaced_deployment_status(self, name: str, namespace: str):
        if self.status_obj is not None:
            return self.status_obj
        return self.stream_events[-1]["object"] if self.stream_events else None

    def list_namespaced_deployment(self, namespace: str, field_selector: str | None = None, **kwargs):
        self.list_calls.append(
            {
                "namespace": namespace,
                "field_selector": field_selector,
                "kwargs": kwargs,
            }
        )
        return None


class _FakeWatch:
    def __init__(self, events):
        self._events = list(events)
        self.stopped = False
        self.calls = []

    def stream(self, func, *args, **kwargs):
        kwargs.setdefault("watch", True)
        func(*args, **kwargs)
        self.calls.append((func, args, kwargs))
        yield from self._events

    def stop(self):
        self.stopped = True


def _make_tab() -> TabConfig:
    return TabConfig(
        text="Code Server",
        iconUrl="https://example.com/icon-b.svg",
        iframeUrl="https://example.com/code",
        k8s=KubernetesConfig(namespace="default", deployment="code-server"),
    )


def _make_tab_status_service() -> TabStatusService:
    """Create a TabStatusService with a mocked SSE connection manager."""
    from app.services.config_service import ConfigService

    tabs = [
        TabConfig(
            text="Tab",
            iconUrl="https://example.com/icon.svg",
            iframeUrl="https://example.com/tab",
        ),
    ]
    config_svc = ConfigService(tabs)
    mock_sse = MagicMock()
    return TabStatusService(config_svc, mock_sse)


def _wait_for_idle(service: KubernetesService, timeout: float = 2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not service._inflight:
            return
        time.sleep(0.05)
    pytest.fail("worker thread did not complete")


def test_restart_success_sets_running():
    target_generation = 2
    status_before = _FakeStatus(
        available_replicas=1,
        updated_replicas=1,
        ready_replicas=1,
        replicas=1,
        observed_generation=1,
        conditions=[
            _FakeCondition(
                type="Progressing",
                status="True",
                reason="NewReplicaSetAvailable",
                observed_generation=1,
            )
        ],
    )
    status_after = _FakeStatus(
        available_replicas=1,
        updated_replicas=1,
        ready_replicas=1,
        replicas=1,
        observed_generation=target_generation,
        conditions=[
            _FakeCondition(
                type="Progressing",
                status="True",
                reason="NewReplicaSetAvailable",
                observed_generation=target_generation,
            ),
            _FakeCondition(
                type="Available",
                status="True",
                observed_generation=target_generation,
            ),
        ],
    )
    status_mid = _FakeStatus(
        available_replicas=0,
        updated_replicas=0,
        ready_replicas=0,
        replicas=1,
        observed_generation=target_generation,
        conditions=[
            _FakeCondition(
                type="Progressing",
                status="True",
                reason="ReplicaSetUpdated",
                observed_generation=target_generation,
            ),
            _FakeCondition(
                type="Available",
                status="False",
                reason="MinimumReplicasUnavailable",
                message="Deployment does not have minimum availability.",
                observed_generation=target_generation,
            ),
        ],
    )
    events = [
        {
            "object": _FakeDeployment(
                metadata=_FakeMetadata(generation=target_generation),
                status=status_before,
                spec=_FakeSpec(replicas=1),
            )
        },
        {
            "object": _FakeDeployment(
                metadata=_FakeMetadata(generation=target_generation),
                status=status_mid,
                spec=_FakeSpec(replicas=1),
            )
        },
        {
            "object": _FakeDeployment(
                metadata=_FakeMetadata(generation=target_generation),
                status=status_after,
                spec=_FakeSpec(replicas=1),
            )
        },
    ]
    apps_api = _FakeAppsApi(
        events,
        status_obj=_FakeDeployment(
            metadata=_FakeMetadata(generation=target_generation),
            status=status_before,
            spec=_FakeSpec(replicas=1),
        ),
    )
    tab_status_service = _make_tab_status_service()
    watcher = _FakeWatch(events)
    service = KubernetesService(
        tab_status_service=tab_status_service,
        apps_api=apps_api,
        watch_factory=lambda: watcher,
        restart_timeout=2,
    )

    tab = _make_tab()
    service.request_restart(0, tab)
    _wait_for_idle(service)

    assert watcher.stopped
    assert watcher.calls
    assert apps_api.patched
    # Final status should be RUNNING
    assert tab_status_service.current(0).state == StatusState.RUNNING


def test_restart_timeout_emits_error():
    events: list[dict] = []
    apps_api = _FakeAppsApi(
        events,
        status_obj=_FakeDeployment(
            metadata=_FakeMetadata(generation=1),
            status=_FakeStatus(observed_generation=0),
            spec=_FakeSpec(replicas=1),
        ),
    )
    tab_status_service = _make_tab_status_service()
    watcher = _FakeWatch(events)
    service = KubernetesService(
        tab_status_service=tab_status_service,
        apps_api=apps_api,
        watch_factory=lambda: watcher,
        restart_timeout=1,
    )

    tab = _make_tab()
    service.request_restart(0, tab)
    _wait_for_idle(service)

    assert watcher.stopped
    payload = tab_status_service.current(0)
    assert payload.state == StatusState.ERROR
    assert "did not finish" in (payload.message or "")


def test_restart_api_failure_reports_error():
    events = []

    class _FailingAppsApi(_FakeAppsApi):
        def patch_namespaced_deployment(self, name: str, namespace: str, body):
            raise ApiException(status=500, reason="boom")

    apps_api = _FailingAppsApi(events)
    tab_status_service = _make_tab_status_service()
    service = KubernetesService(
        tab_status_service=tab_status_service,
        apps_api=apps_api,
        watch_factory=lambda: _FakeWatch(events),
        restart_timeout=1,
    )

    tab = _make_tab()
    service.request_restart(0, tab)
    _wait_for_idle(service)

    payload = tab_status_service.current(0)
    assert payload.state == StatusState.ERROR
    assert "Kubernetes API error" in (payload.message or "")
