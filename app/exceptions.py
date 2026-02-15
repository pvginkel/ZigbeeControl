"""Base exceptions with user-ready messages.

These are template-provided base exceptions that all apps need. Add
app-specific exceptions below these base classes.
"""


class ConfigurationError(Exception):
    """Raised when application configuration is invalid."""

    pass


class BusinessLogicException(Exception):
    """Base exception class for business logic errors.

    All business logic exceptions include user-ready messages that can be
    displayed directly in the UI without client-side message construction.
    """

    def __init__(self, message: str, error_code: str) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class RecordNotFoundException(BusinessLogicException):
    """Exception raised when a requested record is not found."""

    def __init__(self, resource_type: str, identifier: str | int) -> None:
        message = f"{resource_type} {identifier} was not found"
        super().__init__(message, error_code="RECORD_NOT_FOUND")


class ResourceConflictException(BusinessLogicException):
    """Exception raised when attempting to create a resource that already exists."""

    def __init__(self, resource_type: str, identifier: str | int) -> None:
        message = f"A {resource_type.lower()} with {identifier} already exists"
        super().__init__(message, error_code="RESOURCE_CONFLICT")


class InvalidOperationException(BusinessLogicException):
    """Exception raised when an operation cannot be performed due to business rules."""

    def __init__(self, operation: str, cause: str) -> None:
        self.operation = operation
        self.cause = cause
        message = f"Cannot {operation} because {cause}"
        super().__init__(message, error_code="INVALID_OPERATION")


class RouteNotAvailableException(BusinessLogicException):
    """Exception raised when accessing endpoints that are not available in the current mode."""

    def __init__(self, message: str = "This endpoint is only available when the server is running in testing mode") -> None:
        super().__init__(message, error_code="ROUTE_NOT_AVAILABLE")


class AuthenticationException(BusinessLogicException):
    """Exception raised when authentication fails (missing, invalid, or expired token)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="AUTHENTICATION_REQUIRED")


class AuthorizationException(BusinessLogicException):
    """Exception raised when the authenticated user lacks required permissions."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="AUTHORIZATION_FAILED")


class ValidationException(BusinessLogicException):
    """Exception raised for request validation failures (malformed input, invalid redirect, etc.)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="VALIDATION_FAILED")


# --- Domain-specific exceptions ---


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
