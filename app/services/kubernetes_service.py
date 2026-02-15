"""Orchestrates Kubernetes rollout restarts and status monitoring."""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import UTC, datetime
from typing import Any

from kubernetes import client, config, watch
from kubernetes.client import ApiException

from app.exceptions import (
    RestartFailed,
    RestartInProgress,
    RestartTimeout,
)
from app.schemas.config import TabConfig
from app.schemas.status import StatusPayload, StatusState
from app.services.tab_status_service import TabStatusService

logger = logging.getLogger(__name__)

DeploymentKey = tuple[str, str]


class KubernetesService:
    """Handles rollout restarts for Kubernetes deployments."""

    SERVICE_ACCOUNT_PATH = "/var/run/secrets/kubernetes.io/serviceaccount"

    def __init__(
        self,
        tab_status_service: TabStatusService,
        *,
        apps_api: client.AppsV1Api | None = None,
        watch_factory: type[watch.Watch] | None = None,
        restart_timeout: int = 180,
    ) -> None:
        self._tab_status_service = tab_status_service
        self._watch_factory = watch_factory or watch.Watch
        self._restart_timeout = restart_timeout
        self._lock = threading.Lock()
        self._inflight: dict[DeploymentKey, threading.Thread] = {}

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
        self._tab_status_service.emit(
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
            generation = self._trigger_restart(namespace, deployment)
            self._wait_for_rollout(namespace, deployment, generation)
        except RestartTimeout as timeout_exc:
            logger.error(
                "Restart timed out for deployment %s/%s after %ss",
                namespace,
                deployment,
                self._restart_timeout,
                exc_info=timeout_exc,
            )
            self._tab_status_service.emit(
                tab_index,
                StatusPayload(state=StatusState.ERROR, message=str(timeout_exc)),
            )
        except (RestartFailed, ApiException, Exception) as exc:
            message = str(exc)
            if not isinstance(exc, RestartFailed):
                message = f"restart failed: {message}"
            logger.exception(
                "Restart error for deployment %s/%s: %s",
                namespace,
                deployment,
                message,
            )
            self._tab_status_service.emit(
                tab_index,
                StatusPayload(state=StatusState.ERROR, message=message),
            )
        else:
            logger.info(
                "Restart completed for deployment %s/%s",
                namespace,
                deployment,
            )
            self._tab_status_service.emit(
                tab_index,
                StatusPayload(state=StatusState.RUNNING),
            )
        finally:
            with self._lock:
                self._inflight.pop(key, None)
            logger.debug(
                "Worker finished for deployment %s/%s", namespace, deployment
            )

    def _trigger_restart(self, namespace: str, deployment: str) -> int:
        timestamp = datetime.now(UTC).isoformat()
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
        except Exception as exc:
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

        try:
            deployment_obj = self._apps_api.read_namespaced_deployment_status(
                name=deployment,
                namespace=namespace,
            )
        except ApiException as exc:
            logger.exception(
                "Unable to read deployment status %s/%s after restart trigger",
                namespace,
                deployment,
            )
            raise RestartFailed(
                f"failed to read deployment status: {getattr(exc, 'reason', exc.status)}",
                namespace=namespace,
                deployment=deployment,
            ) from exc
        except Exception as exc:
            logger.exception(
                "Unexpected error reading deployment status for %s/%s",
                namespace,
                deployment,
            )
            raise RestartFailed(
                f"unexpected error reading deployment status: {exc}",
                namespace=namespace,
                deployment=deployment,
            ) from exc

        generation = self._extract_generation(deployment_obj)
        if generation is None:
            raise RestartFailed(
                "unable to determine deployment generation",
                namespace=namespace,
                deployment=deployment,
            )

        logger.debug(
            "Restart triggered for %s/%s targeting generation %s",
            namespace,
            deployment,
            generation,
        )
        return generation

    def _wait_for_rollout(self, namespace: str, deployment: str, target_generation: int) -> None:
        deadline = time.monotonic() + self._restart_timeout
        field_selector = f"metadata.name={deployment}"
        watcher = self._watch_factory()
        timeout_seconds = max(1, int(self._restart_timeout))
        logger.debug(
            "Watching rollout status for deployment %s/%s (timeout=%ss, selector=%s, targetGeneration=%s)",
            namespace,
            deployment,
            self._restart_timeout,
            field_selector,
            target_generation,
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
                if not obj:
                    continue

                failure_message = self._detect_rollout_failure(obj, target_generation)
                if failure_message:
                    raise RestartFailed(
                        failure_message,
                        namespace=namespace,
                        deployment=deployment,
                    )

                if self._deployment_ready(obj, target_generation):
                    logger.debug(
                        "Deployment %s/%s generation %s reports ready state",
                        namespace,
                        deployment,
                        target_generation,
                    )
                    return
                if time.monotonic() >= deadline:
                    break
        finally:
            try:
                watcher.stop()
            except Exception:
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
        if isinstance(items, list | tuple):
            return items[0] if items else None

        return obj

    @staticmethod
    def _deployment_ready(obj: object, target_generation: int) -> bool:
        metadata = KubernetesService._get_field(obj, "metadata")
        status = KubernetesService._get_field(obj, "status")
        spec = KubernetesService._get_field(obj, "spec")

        if status is None:
            return False

        observed_generation = KubernetesService._get_int_field(
            status, "observed_generation", "observedGeneration"
        )
        if observed_generation is None or observed_generation < target_generation:
            return False

        desired = KubernetesService._get_int_field(spec, "replicas")
        if desired is None:
            desired = KubernetesService._get_int_field(status, "replicas")

        ready = KubernetesService._get_int_field(status, "ready_replicas", "readyReplicas")
        available = KubernetesService._get_int_field(
            status, "available_replicas", "availableReplicas"
        )
        updated = KubernetesService._get_int_field(status, "updated_replicas", "updatedReplicas")

        if desired is None:
            if ready is None and available is None:
                return False
        else:
            for value in (ready, available, updated):
                if value is None or value < desired:
                    return False

        if metadata is not None:
            generation = KubernetesService._get_int_field(metadata, "generation")
            if generation is not None and generation > observed_generation:
                return False

        conditions = KubernetesService._get_field(status, "conditions") or []
        for condition in conditions:
            cond_type = KubernetesService._get_field(condition, "type")
            if cond_type != "Available":
                continue
            cond_status = KubernetesService._get_field(condition, "status")
            if str(cond_status).lower() != "true":
                return False
            cond_gen = KubernetesService._get_int_field(
                condition, "observed_generation", "observedGeneration"
            )
            if cond_gen is None or cond_gen >= target_generation:
                return True
        return bool((ready and ready > 0) or (available and available > 0))

    @staticmethod
    def _detect_rollout_failure(obj: object, target_generation: int) -> str | None:
        status = KubernetesService._get_field(obj, "status")
        if status is None:
            return None

        conditions = KubernetesService._get_field(status, "conditions") or []
        for condition in conditions:
            cond_type = KubernetesService._get_field(condition, "type")
            if cond_type not in {"Progressing", "Available"}:
                continue
            cond_status = str(KubernetesService._get_field(condition, "status") or "").lower()
            cond_reason = KubernetesService._get_field(condition, "reason")
            cond_message = KubernetesService._get_field(condition, "message")
            cond_gen = KubernetesService._get_int_field(
                condition, "observed_generation", "observedGeneration"
            )

            if cond_gen is not None and cond_gen < target_generation:
                continue

            if cond_type == "Progressing" and cond_status == "false":
                reason = cond_reason or "rollout halted"
                if cond_reason == "ProgressDeadlineExceeded":
                    reason = "progress deadline exceeded"
                message = cond_message or reason
                return f"deployment rollout failed: {message}"

        return None

    @staticmethod
    def _get_field(obj: object | None, *names: str) -> Any | None:
        if obj is None:
            return None
        for name in names:
            value = getattr(obj, name, None)
            if value is not None:
                return value
            if isinstance(obj, dict) and name in obj:
                return obj[name]
        return None

    @staticmethod
    def _get_int_field(obj: object | None, *names: str) -> int | None:
        value = KubernetesService._get_field(obj, *names)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_generation(obj: object) -> int | None:
        metadata = KubernetesService._get_field(obj, "metadata")
        return KubernetesService._get_int_field(metadata, "generation")
