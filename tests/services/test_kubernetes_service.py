from __future__ import annotations

import time
from dataclasses import dataclass

import pytest
from kubernetes.client import ApiException

from app.schemas.config import KubernetesConfig, TabConfig
from app.schemas.status import StatusPayload, StatusState
from app.services.kubernetes_service import KubernetesService
from app.services.status_broadcaster import StatusBroadcaster


@dataclass
class _FakeStatus:
    available_replicas: int | None = None
    updated_replicas: int | None = None
    ready_replicas: int | None = None
    replicas: int | None = None


@dataclass
class _FakeSpec:
    replicas: int | None = None


@dataclass
class _FakeDeployment:
    status: _FakeStatus
    spec: _FakeSpec


class _FakeAppsApi:
    def __init__(self, stream_events):
        self.stream_events = stream_events
        self.patched = []
        self.list_calls = []

    def patch_namespaced_deployment(self, name: str, namespace: str, body):
        self.patched.append((name, namespace, body))

    def read_namespaced_deployment_status(self, name: str, namespace: str):  # pragma: no cover - stub for API parity
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
        self.calls.append((func, args, kwargs))
        func(*args, **kwargs)
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


def _wait_for_idle(service: KubernetesService, timeout: float = 2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not service._inflight:  # type: ignore[attr-defined]
            return
        time.sleep(0.05)
    pytest.fail("worker thread did not complete")


def _consume(stream, timeout: float = 2.0) -> StatusPayload:
    deadline = time.time() + timeout
    while True:
        if time.time() > deadline:
            pytest.fail("timed out waiting for status event")
        try:
            return next(stream)
        except StopIteration:  # pragma: no cover - defensive
            pytest.fail("status stream terminated unexpectedly")


def test_restart_success_sets_running():
    events = [
        {"object": _FakeDeployment(status=_FakeStatus(available_replicas=1, updated_replicas=1, ready_replicas=1), spec=_FakeSpec(replicas=1))}
    ]
    apps_api = _FakeAppsApi(events)
    broadcaster = StatusBroadcaster(1)
    watcher = _FakeWatch(events)
    service = KubernetesService(
        status_broadcaster=broadcaster,
        apps_api=apps_api,
        watch_factory=lambda: watcher,
        restart_timeout=2,
    )

    stream = broadcaster.listen(0)
    assert _consume(stream).state == StatusState.RUNNING

    tab = _make_tab()
    service.request_restart(0, tab)

    assert _consume(stream).state == StatusState.RESTARTING
    assert _consume(stream).state == StatusState.RUNNING
    _wait_for_idle(service)
    assert watcher.stopped
    assert watcher.calls
    func, args, kwargs = watcher.calls[0]
    assert getattr(func, "__self__", None) is apps_api
    assert getattr(func, "__name__", "") == "list_namespaced_deployment"
    assert kwargs["field_selector"] == "metadata.name=code-server"
    assert apps_api.list_calls
    list_call = apps_api.list_calls[0]
    assert list_call["namespace"] == "default"
    assert list_call["field_selector"] == "metadata.name=code-server"
    assert list_call["kwargs"].get("watch") is True
    assert list_call["kwargs"].get("timeout_seconds") == 2
    stream.close()
    assert apps_api.patched


def test_restart_timeout_emits_error():
    events: list[dict] = []
    apps_api = _FakeAppsApi(events)
    broadcaster = StatusBroadcaster(1)
    watcher = _FakeWatch(events)
    service = KubernetesService(
        status_broadcaster=broadcaster,
        apps_api=apps_api,
        watch_factory=lambda: watcher,
        restart_timeout=1,
    )

    stream = broadcaster.listen(0)
    assert _consume(stream).state == StatusState.RUNNING

    tab = _make_tab()
    service.request_restart(0, tab)

    assert _consume(stream).state == StatusState.RESTARTING
    payload = _consume(stream)
    assert payload.state == StatusState.ERROR
    assert "did not finish" in (payload.message or "")
    _wait_for_idle(service)
    assert watcher.stopped
    assert apps_api.list_calls
    list_call = apps_api.list_calls[0]
    assert list_call["kwargs"].get("watch") is True
    assert list_call["kwargs"].get("timeout_seconds") == 1
    stream.close()


def test_restart_api_failure_reports_error():
    events = []

    class _FailingAppsApi(_FakeAppsApi):
        def patch_namespaced_deployment(self, name: str, namespace: str, body):  # type: ignore[override]
            raise ApiException(status=500, reason="boom")

    apps_api = _FailingAppsApi(events)
    broadcaster = StatusBroadcaster(1)
    service = KubernetesService(
        status_broadcaster=broadcaster,
        apps_api=apps_api,
        watch_factory=lambda: _FakeWatch(events),
        restart_timeout=1,
    )

    stream = broadcaster.listen(0)
    assert _consume(stream).state == StatusState.RUNNING

    tab = _make_tab()
    service.request_restart(0, tab)

    assert _consume(stream).state == StatusState.RESTARTING
    payload = _consume(stream)
    assert payload.state == StatusState.ERROR
    assert "Kubernetes API error" in (payload.message or "")
    _wait_for_idle(service)
    stream.close()
