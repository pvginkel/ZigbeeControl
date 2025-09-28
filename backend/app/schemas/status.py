"""Schemas for status reporting."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StatusState(str, Enum):
    RUNNING = "running"
    RESTARTING = "restarting"
    ERROR = "error"


class StatusPayload(BaseModel):
    state: StatusState = Field(description="Current state of the tab")
    message: Optional[str] = Field(default=None, description="Optional diagnostic message")


class RestartResponse(BaseModel):
    status: StatusState
    message: Optional[str] = None

