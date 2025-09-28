"""Helpers for configuring CORS headers."""

from __future__ import annotations

import re
import logging
from http import HTTPStatus
from typing import Sequence

from flask import Flask, Response, make_response, request

logger =  logging.getLogger(__name__)


def parse_allowed_origins(raw: str | None) -> tuple[str, ...] | None:
    """Parse a comma or whitespace separated list of allowed origins."""

    if not raw:
        return None

    tokens = [token.strip() for token in re.split(r"[\s,]+", raw) if token.strip()]
    if not tokens:
        return None

    if "*" in tokens:
        return ("*",)

    seen: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.append(token)
    return tuple(seen)


def configure_cors(app: Flask, allowed_origins: Sequence[str]) -> None:
    """Register request hooks that apply CORS headers for allowed origins."""

    origins = tuple(allowed_origins)
    if not origins:
        return

    allow_all = "*" in origins
    explicit = {origin for origin in origins if origin != "*"}

    if not allow_all and not explicit:
        return

    def _apply_headers(response: Response) -> Response:
        logger.info("APPLY HEADERS")
        origin = request.headers.get("Origin")
        if allow_all:
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif origin and origin in explicit:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers.add("Vary", "Origin")
        else:
            return response

        methods = request.headers.get("Access-Control-Request-Method", "GET,POST,OPTIONS")
        response.headers.setdefault("Access-Control-Allow-Methods", methods)

        requested_headers = request.headers.get("Access-Control-Request-Headers")
        if requested_headers:
            response.headers["Access-Control-Allow-Headers"] = requested_headers
        else:
            response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")

        response.headers.setdefault("Access-Control-Max-Age", "1800")
        return response

    @app.after_request
    def _add_cors_headers(response: Response):  # type: ignore[override]
        return _apply_headers(response)

    @app.before_request
    def _handle_preflight() -> Response | None:  # type: ignore[override]
        if request.method != "OPTIONS":
            return None

        origin = request.headers.get("Origin")
        if allow_all or (origin and origin in explicit):
            response = make_response("", HTTPStatus.NO_CONTENT)
            return _apply_headers(response)
        return None
