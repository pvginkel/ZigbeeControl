from __future__ import annotations

from http import HTTPStatus

import pytest

from app import create_app


EXPECTED_MAX_AGE = "Max-Age=315360000"


def test_login_success_sets_cookie(client, auth_token):
    response = client.post("/api/auth/login", json={"token": auth_token})
    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body == {"authenticated": True, "disabled": False}
    cookies = response.headers.getlist("Set-Cookie")
    assert cookies, "expected authentication cookie header"
    assert any("Partitioned" in cookie for cookie in cookies)
    assert any("SameSite=None" in cookie for cookie in cookies)
    assert any(EXPECTED_MAX_AGE in cookie for cookie in cookies)


def test_login_rejects_invalid_token(client):
    response = client.post("/api/auth/login", json={"token": "wrong"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.get_json() == {"error": "invalid authentication token"}


def test_auth_check_requires_cookie(client):
    response = client.get("/api/auth/check")
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.get_json() == {"error": "missing authentication cookie"}


def test_auth_check_valid_cookie(client, authenticate):
    authenticate()
    response = client.get("/api/auth/check")
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"authenticated": True, "disabled": False}


def test_auth_check_disabled(tabs_config_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_AUTH_DISABLED", "1")
    monkeypatch.delenv("APP_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.delenv("APP_ALLOWED_ORIGINS", raising=False)
    app = create_app(config_path=str(tabs_config_path))
    app.testing = True
    with app.test_client() as client:
        response = client.get("/api/auth/check")
        assert response.status_code == HTTPStatus.OK
        assert response.get_json() == {"authenticated": True, "disabled": True}


def test_login_cookie_not_secure_in_dev(tabs_config_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("APP_AUTH_TOKEN", "unit-test-token")
    monkeypatch.setenv("APP_SECRET_KEY", "unit-test-secret")
    monkeypatch.delenv("APP_ALLOWED_ORIGINS", raising=False)
    app = create_app(config_path=str(tabs_config_path))
    app.testing = True
    with app.test_client() as client:
        response = client.post("/api/auth/login", json={"token": "unit-test-token"})
        cookies = response.headers.getlist("Set-Cookie")
        assert all("Partitioned" not in cookie for cookie in cookies)
        assert all("Secure" not in cookie for cookie in cookies)
        assert any("SameSite=Lax" in cookie for cookie in cookies)
        assert any(EXPECTED_MAX_AGE in cookie for cookie in cookies)
