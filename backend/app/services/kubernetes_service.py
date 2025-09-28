"""Orchestrates Kubernetes rollout restarts and status monitoring."""

from __future__ import annotations

import threading
import time
import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from kubernetes import client, watch, config
from kubernetes.client import ApiException
from kubernetes.config.config_exception import ConfigException

from app.schemas.config import TabConfig
from app.schemas.status import StatusPayload, StatusState
from app.services.exceptions import (
    RestartFailed,
    RestartInProgress,
    RestartTimeout,
)
from app.services.status_broadcaster import StatusBroadcaster

logger = logging.getLogger(__name__)

DeploymentKey = Tuple[str, str]


class KubernetesService:
    """Handles rollout restarts for Kubernetes deployments."""

    SERVICE_ACCOUNT_PATH = "/var/run/secrets/kubernetes.io/serviceaccount"

    def __init__(
        self,
        status_broadcaster: StatusBroadcaster,
        *,
        apps_api: client.AppsV1Api | None = None,
        watch_factory: type[watch.Watch] | None = None,
        restart_timeout: int = 180,
    ) -> None:
        self._status_broadcaster = status_broadcaster
        self._watch_factory = watch_factory or watch.Watch
        self._restart_timeout = restart_timeout
        self._lock = threading.Lock()
        self._inflight: Dict[DeploymentKey, threading.Thread] = {}

        if apps_api:
            self._apps_api = apps_api
        else:
            if os.path.exists(self.SERVICE_ACCOUNT_PATH):
                config.load_incluster_config()
            else:
                config.load_kube_config()

            logger.warning(
                "Disabling SSL verification because of https://github.com/canonical/microk8s/issues/4864"
            )

            configuration = client.Configuration.get_default_copy()
            configuration.verify_ssl = False

            api_client = client.ApiClient(configuration=configuration)
            self._apps_api = client.AppsV1Api(api_client=api_client)

    def request_restart(self, tab_index: int, tab: TabConfig) -> None:
        if tab.k8s is None:
            raise ValueError("restart requested for non-restartable tab")

        key: DeploymentKey = (tab.k8s.namespace, tab.k8s.deployment)
        with self._lock:
            if key in self._inflight:
                logger.info(
                    "Restart already in progress for %s/%s", key[0], key[1]
                )
                raise RestartInProgress(namespace=key[0], deployment=key[1])
            worker = threading.Thread(
                target=self._perform_restart,
                args=(tab_index, tab, key),
                daemon=True,
            )
            self._inflight[key] = worker

        logger.info(
            "Scheduling restart for tab=%s deployment=%s/%s",
            tab_index,
            key[0],
            key[1],
        )
        self._status_broadcaster.emit(
            tab_index,
            StatusPayload(state=StatusState.RESTARTING),
        )
        worker.start()

    def _perform_restart(self, tab_index: int, tab: TabConfig, key: DeploymentKey) -> None:
        namespace, deployment = key
        logger.debug(
            "Worker starting restart sequence for tab=%s deployment=%s/%s",
            tab_index,
            namespace,
            deployment,
        )

        try:
            self._trigger_restart(namespace, deployment)
            self._wait_for_rollout(namespace, deployment)
        except RestartTimeout as timeout_exc:
            logger.error(
                "Restart timed out for deployment %s/%s after %ss",
                namespace,
                deployment,
                self._restart_timeout,
                exc_info=timeout_exc,
            )
            self._status_broadcaster.emit(
                tab_index,
                StatusPayload(state=StatusState.ERROR, message=str(timeout_exc)),
            )
        except (RestartFailed, ApiException, Exception) as exc:  # broad catch to surface message via SSE
            message = str(exc)
            if not isinstance(exc, RestartFailed):
                message = f"restart failed: {message}"
            logger.exception(
                "Restart error for deployment %s/%s: %s",
                namespace,
                deployment,
                message,
            )
            self._status_broadcaster.emit(
                tab_index,
                StatusPayload(state=StatusState.ERROR, message=message),
            )
        else:
            logger.info(
                "Restart completed for deployment %s/%s",
                namespace,
                deployment,
            )
            self._status_broadcaster.emit(
                tab_index,
                StatusPayload(state=StatusState.RUNNING),
            )
        finally:
            with self._lock:
                self._inflight.pop(key, None)
            logger.debug(
                "Worker finished for deployment %s/%s", namespace, deployment
            )

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
        logger.debug(
            "Patching deployment %s/%s with restartedAt=%s",
            namespace,
            deployment,
            timestamp,
        )

        try:
            self._apps_api.patch_namespaced_deployment(
                name=deployment,
                namespace=namespace,
                body=body,
            )
        except ApiException as exc:
            logger.exception(
                "Kubernetes API error while patching deployment %s/%s",
                namespace,
                deployment,
            )
            raise RestartFailed(
                f"Kubernetes API error: {getattr(exc, 'reason', exc.status)}",
                namespace=namespace,
                deployment=deployment,
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Unexpected error while triggering restart for %s/%s",
                namespace,
                deployment,
            )
            raise RestartFailed(
                f"unexpected error triggering restart: {exc}",
                namespace=namespace,
                deployment=deployment,
            ) from exc

    def _wait_for_rollout(self, namespace: str, deployment: str) -> None:
        deadline = time.monotonic() + self._restart_timeout
        field_selector = f"metadata.name={deployment}"
        watcher = self._watch_factory()
        timeout_seconds = max(1, int(self._restart_timeout))
        logger.debug(
            "Watching rollout status for deployment %s/%s (timeout=%ss, selector=%s)",
            namespace,
            deployment,
            self._restart_timeout,
            field_selector,
        )
        try:
            stream = watcher.stream(
                self._apps_api.list_namespaced_deployment,
                namespace=namespace,
                field_selector=field_selector,
                timeout_seconds=timeout_seconds,
                _request_timeout=self._restart_timeout,
            )
            for event in stream:
                obj = self._extract_deployment_from_event(event)
                if obj and self._deployment_ready(obj):
                    logger.debug(
                        "Deployment %s/%s reports ready state", namespace, deployment
                    )
                    return
                if time.monotonic() >= deadline:
                    break
        finally:
            try:
                watcher.stop()
            except Exception:  # pragma: no cover - best effort cleanup
                pass
        logger.debug(
            "Deployment %s/%s did not become ready within timeout",
            namespace,
            deployment,
        )
        raise RestartTimeout(
            namespace=namespace,
            deployment=deployment,
            timeout_seconds=self._restart_timeout,
        )

    @staticmethod
    def _extract_deployment_from_event(event: Any) -> Any | None:
        if event is None:
            return None
        obj: Any
        if isinstance(event, dict):
            obj = event.get("object")
        else:
            obj = getattr(event, "object", event)

        if obj is None:
            return None

        items = getattr(obj, "items", None)
        if isinstance(items, (list, tuple)):
            return items[0] if items else None

        return obj

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
