"""Pydantic models describing the configuration contract."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class KubernetesConfig(BaseModel):
    namespace: str = Field(min_length=1)
    deployment: str = Field(min_length=1)

    @field_validator("namespace", "deployment")
    @classmethod
    def _strip_and_require(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("must not be empty")
        return trimmed


class TabConfig(BaseModel):
    text: str = Field(min_length=1)
    iconUrl: str = Field(min_length=1)
    iframeUrl: str = Field(min_length=1)
    k8s: Optional[KubernetesConfig] = None

    @field_validator("text", "iconUrl", "iframeUrl")
    @classmethod
    def _strip_and_require(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("must not be empty")
        return trimmed


class TabsConfig(BaseModel):
    tabs: List[TabConfig]

    @field_validator("tabs")
    @classmethod
    def _require_tabs(cls, value: List[TabConfig]) -> List[TabConfig]:
        if not value:
            raise ValueError("at least one tab must be defined")
        return value


class TabResponse(BaseModel):
    text: str
    iconUrl: str
    iframeUrl: str
    restartable: bool


class ConfigResponse(BaseModel):
    tabs: List[TabResponse]

