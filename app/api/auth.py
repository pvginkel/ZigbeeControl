"""Authentication API routes."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from spectree import Response, SpecTree

from app.schemas.auth import AuthCheckResponse, AuthErrorResponse, LoginRequest, LoginResponse
from app.utils.auth import AuthManager, AuthValidationError

_INVALID_TOKEN_MESSAGE = "invalid authentication token"


def register_auth_routes(bp: Blueprint, auth_manager: AuthManager, spectree: SpecTree) -> None:
    """Register authentication routes on the blueprint."""

    @bp.post("/auth/login")
    @spectree.validate(json=LoginRequest, resp=Response(HTTP_200=LoginResponse, HTTP_403=AuthErrorResponse))
    def login():
        if auth_manager.disabled:
            response = jsonify(LoginResponse(authenticated=True, disabled=True).model_dump())
            return response

        payload = LoginRequest.model_validate(request.json or {})
        if not auth_manager.validate_login_token(payload.token):
            error = AuthErrorResponse(error=_INVALID_TOKEN_MESSAGE)
            return jsonify(error.model_dump()), HTTPStatus.FORBIDDEN

        response = jsonify(LoginResponse(authenticated=True, disabled=False).model_dump())
        auth_manager.set_login_cookie(response)
        return response

    @bp.get("/auth/check")
    @spectree.validate(resp=Response(HTTP_200=AuthCheckResponse, HTTP_403=AuthErrorResponse))
    def auth_check():
        if auth_manager.disabled:
            response = AuthCheckResponse(authenticated=True, disabled=True)
            return jsonify(response.model_dump())

        try:
            auth_manager.require_request_auth(request)
        except AuthValidationError as exc:
            error = AuthErrorResponse(error=exc.message)
            return jsonify(error.model_dump()), HTTPStatus.FORBIDDEN

        response = AuthCheckResponse(authenticated=True, disabled=False)
        return jsonify(response.model_dump())

