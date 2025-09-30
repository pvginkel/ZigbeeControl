from __future__ import annotations

"""Pydantic models used by the authentication endpoints."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    token: str


class LoginResponse(BaseModel):
    authenticated: bool
    disabled: bool


class AuthCheckResponse(BaseModel):
    authenticated: bool
    disabled: bool


class AuthErrorResponse(BaseModel):
    error: str

