"""Authentication helpers for issuing and validating JWT-backed cookies."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from flask import Request, Response
from werkzeug.http import dump_cookie

logger = logging.getLogger(__name__)

_COOKIE_LIFETIME = timedelta(days=3650)  # Approximately 10 years.
_COOKIE_SUBJECT = "z2m-wrapper"


class AuthValidationError(RuntimeError):
    """Raised when authentication state cannot be verified."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(slots=True)
class AuthConfig:
    login_token: str | None
    cookie_name: str
    jwt_secret: str
    disabled: bool
    secure_cookies: bool


class AuthManager:
    """Handles JWT-backed authentication cookies for the API."""

    def __init__(self, config: AuthConfig) -> None:
        self._config = config
        if not config.disabled:
            if not config.login_token:
                raise ValueError("login_token is required when authentication is enabled")
            if not config.jwt_secret:
                raise ValueError("jwt_secret is required when authentication is enabled")
        logger.info(
            "Authentication initialised (cookie=%s, disabled=%s)",
            config.cookie_name,
            config.disabled,
        )

    @property
    def disabled(self) -> bool:
        return self._config.disabled

    @property
    def cookie_name(self) -> str:
        return self._config.cookie_name

    def validate_login_token(self, provided: str) -> bool:
        if self.disabled:
            return True
        assert self._config.login_token is not None  # for type checkers
        return provided == self._config.login_token

    def _encode_cookie_value(self) -> str:
        payload = {"sub": _COOKIE_SUBJECT}
        return jwt.encode(payload, self._config.jwt_secret, algorithm="HS256")

    def set_login_cookie(self, response: Response) -> None:
        if self.disabled:
            return
        cookie_value = self._encode_cookie_value()
        cookie = dump_cookie(
            key=self.cookie_name,
            value=cookie_value,
            max_age=int(_COOKIE_LIFETIME.total_seconds()),
            httponly=True,
            secure=self._config.secure_cookies,
            samesite="None" if self._config.secure_cookies else "Lax",
            path="/",
            expires=datetime.now(timezone.utc) + _COOKIE_LIFETIME,
        )
        if self._config.secure_cookies:
            cookie += "; Partitioned"
        response.headers.add("Set-Cookie", cookie)

    def clear_cookie(self, response: Response) -> None:
        cookie = dump_cookie(
            key=self.cookie_name,
            value="",
            max_age=0,
            expires=0,
            httponly=True,
            secure=self._config.secure_cookies,
            samesite="None" if self._config.secure_cookies else "Lax",
            path="/",
        )
        if self._config.secure_cookies:
            cookie += "; Partitioned"
        response.headers.add("Set-Cookie", cookie)

    def _decode_cookie(self, value: str) -> dict:
        try:
            payload = jwt.decode(value, self._config.jwt_secret, algorithms=["HS256"])
        except jwt.InvalidTokenError as exc:  # pragma: no cover - logged for clarity
            logger.warning("Failed to decode auth cookie: %s", exc)
            raise AuthValidationError("invalid authentication cookie") from exc
        if payload.get("sub") != _COOKIE_SUBJECT:
            raise AuthValidationError("invalid authentication cookie")
        return payload

    def require_request_auth(self, request: Request) -> None:
        if self.disabled:
            return
        cookie = request.cookies.get(self.cookie_name)
        if not cookie:
            raise AuthValidationError("missing authentication cookie")
        self._decode_cookie(cookie)

    def check_request_auth(self, request: Request) -> bool:
        if self.disabled:
            return True
        cookie = request.cookies.get(self.cookie_name)
        if not cookie:
            return False
        try:
            self._decode_cookie(cookie)
        except AuthValidationError:
            return False
        return True
