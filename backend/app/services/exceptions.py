"""Custom exception hierarchy used across services."""

from __future__ import annotations


class ConfigError(RuntimeError):
    """Base class for configuration related failures."""


class ConfigNotLoaded(ConfigError):
    """Raised when configuration is accessed before initial load."""


class ConfigLoadFailed(ConfigError):
    """Raised when reading or validating the YAML configuration fails."""

    def __init__(self, message: str, *, path: str | None = None):
        detail = message if path is None else f"{message} (path={path})"
        super().__init__(detail)
        self.path = path


class TabLookupError(RuntimeError):
    """Base class for problems locating or working with a tab."""


class TabNotFound(TabLookupError):
    """Raised when a tab index is out of range."""

    def __init__(self, idx: int):
        super().__init__(f"tab index {idx} is out of range")
        self.idx = idx


class TabNotRestartable(TabLookupError):
    """Raised when restart is requested for a tab without K8s settings."""

    def __init__(self, idx: int):
        super().__init__(f"tab index {idx} is not restartable")
        self.idx = idx


class RestartError(RuntimeError):
    """Base class for Kubernetes restart problems."""

    def __init__(self, message: str, *, namespace: str | None = None, deployment: str | None = None):
        context = []
        if namespace:
            context.append(f"namespace={namespace}")
        if deployment:
            context.append(f"deployment={deployment}")
        detail = message if not context else f"{message} ({', '.join(context)})"
        super().__init__(detail)
        self.namespace = namespace
        self.deployment = deployment


class RestartInProgress(RestartError):
    """Raised when a restart is already underway for the deployment."""

    def __init__(self, *, namespace: str, deployment: str):
        super().__init__("restart already in progress", namespace=namespace, deployment=deployment)


class RestartTimeout(RestartError):
    """Raised when rollout confirmation does not complete in time."""

    def __init__(self, *, namespace: str, deployment: str, timeout_seconds: int):
        super().__init__(
            f"restart did not finish within {timeout_seconds} seconds",
            namespace=namespace,
            deployment=deployment,
        )
        self.timeout_seconds = timeout_seconds


class RestartFailed(RestartError):
    """Raised when the Kubernetes API returns an error during restart."""

    def __init__(self, message: str, *, namespace: str, deployment: str):
        super().__init__(message, namespace=namespace, deployment=deployment)

