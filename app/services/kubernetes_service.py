"""Orchestrates Kubernetes rollout restarts and status monitoring."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Dict, Tuple

from kubernetes import client, watch
from kubernetes.client import ApiException

from app.schemas.config import TabConfig
from app.schemas.status import StatusPayload, StatusState
from app.services.exceptions import (
    RestartFailed,
    RestartInProgress,
    RestartTimeout,
)
from app.services.status_broadcaster import StatusBroadcaster


DeploymentKey = Tuple[str, str]


class KubernetesService:
    """Handles rollout restarts for Kubernetes deployments."""

    def __init__(
        self,
        status_broadcaster: StatusBroadcaster,
        *,
        apps_api: client.AppsV1Api | None = None,
        watch_factory: type[watch.Watch] | None = None,
        restart_timeout: int = 180,
    ) -> None:
        self._status_broadcaster = status_broadcaster
        self._apps_api = apps_api or client.AppsV1Api()
        self._watch_factory = watch_factory or watch.Watch
        self._restart_timeout = restart_timeout
        self._lock = threading.Lock()
        self._inflight: Dict[DeploymentKey, threading.Thread] = {}

    def request_restart(self, tab_index: int, tab: TabConfig) -> None:
        if tab.k8s is None:
            raise ValueError("restart requested for non-restartable tab")

        key: DeploymentKey = (tab.k8s.namespace, tab.k8s.deployment)
        with self._lock:
            if key in self._inflight:
                raise RestartInProgress(namespace=key[0], deployment=key[1])
            worker = threading.Thread(
                target=self._perform_restart,
                args=(tab_index, tab, key),
                daemon=True,
            )
            self._inflight[key] = worker

        self._status_broadcaster.emit(
            tab_index,
            StatusPayload(state=StatusState.RESTARTING),
        )
        worker.start()

    def _perform_restart(self, tab_index: int, tab: TabConfig, key: DeploymentKey) -> None:
        namespace, deployment = key
        try:
            self._trigger_restart(namespace, deployment)
            self._wait_for_rollout(namespace, deployment)
        except RestartTimeout as timeout_exc:
            self._status_broadcaster.emit(
                tab_index,
                StatusPayload(state=StatusState.ERROR, message=str(timeout_exc)),
            )
        except (RestartFailed, ApiException, Exception) as exc:  # broad catch to surface message via SSE
            message = str(exc)
            if not isinstance(exc, RestartFailed):
                message = f"restart failed: {message}"
            self._status_broadcaster.emit(
                tab_index,
                StatusPayload(state=StatusState.ERROR, message=message),
            )
        else:
            self._status_broadcaster.emit(
                tab_index,
                StatusPayload(state=StatusState.RUNNING),
            )
        finally:
            with self._lock:
                self._inflight.pop(key, None)

    def _trigger_restart(self, namespace: str, deployment: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": timestamp,
                        }
                    }
                }
            }
        }
        try:
            self._apps_api.patch_namespaced_deployment(
                name=deployment,
                namespace=namespace,
                body=body,
            )
        except ApiException as exc:
            raise RestartFailed(
                f"Kubernetes API error: {getattr(exc, 'reason', exc.status)}",
                namespace=namespace,
                deployment=deployment,
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise RestartFailed(
                f"unexpected error triggering restart: {exc}",
                namespace=namespace,
                deployment=deployment,
            ) from exc

    def _wait_for_rollout(self, namespace: str, deployment: str) -> None:
        deadline = time.monotonic() + self._restart_timeout
        watcher = self._watch_factory()
        try:
            stream = watcher.stream(
                self._apps_api.read_namespaced_deployment_status,
                name=deployment,
                namespace=namespace,
                timeout_seconds=self._restart_timeout,
            )
            for event in stream:
                obj = event.get("object") if isinstance(event, dict) else event
                if obj and self._deployment_ready(obj):
                    return
                if time.monotonic() >= deadline:
                    raise RestartTimeout(namespace=namespace, deployment=deployment, timeout_seconds=self._restart_timeout)
        finally:
            try:
                watcher.stop()
            except Exception:  # pragma: no cover - best effort cleanup
                pass
        raise RestartTimeout(namespace=namespace, deployment=deployment, timeout_seconds=self._restart_timeout)

    @staticmethod
    def _deployment_ready(obj: object) -> bool:
        status = getattr(obj, "status", None)
        spec = getattr(obj, "spec", None)
        desired = getattr(spec, "replicas", None)
        available = getattr(status, "available_replicas", None)
        updated = getattr(status, "updated_replicas", None)
        ready = getattr(status, "ready_replicas", None)

        if desired is None:
            desired = getattr(status, "replicas", None)
        if desired is None:
            # No replica count to compare against; rely on ready pods info when available.
            return bool(ready or available)

        try:
            desired_val = int(desired)
        except (TypeError, ValueError):
            return False

        checks = []
        for value in (available, updated, ready):
            if value is None:
                continue
            try:
                if int(value) < desired_val:
                    return False
                checks.append(True)
            except (TypeError, ValueError):
                return False
        return bool(checks)

