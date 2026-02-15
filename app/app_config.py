"""Application-specific configuration.

This module implements app-specific configuration that is separate from the
infrastructure configuration in config.py.
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AppEnvironment(BaseSettings):
    """Raw environment variable loading for app-specific settings."""

    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_TABS_CONFIG: str = ""
    APP_K8S_RESTART_TIMEOUT: int = 180


class AppSettings(BaseModel):
    """Application-specific settings."""

    model_config = ConfigDict(from_attributes=True)

    tabs_config_path: str = ""
    k8s_restart_timeout: int = 180

    @classmethod
    def load(cls, env: "AppEnvironment | None" = None, flask_env: str = "development") -> "AppSettings":
        """Load app settings from environment variables."""
        if env is None:
            env = AppEnvironment()
        return cls(
            tabs_config_path=env.APP_TABS_CONFIG,
            k8s_restart_timeout=env.APP_K8S_RESTART_TIMEOUT,
        )
