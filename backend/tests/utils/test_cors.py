from __future__ import annotations

from flask import Flask

from app.utils.cors import configure_cors, parse_allowed_origins


def test_parse_allowed_origins_handles_empty_values():
    assert parse_allowed_origins(None) is None
    assert parse_allowed_origins("   ") is None


def test_parse_allowed_origins_deduplicates_and_trims():
    origins = parse_allowed_origins(" https://a.test ,https://b.test https://a.test")
    assert origins == ("https://a.test", "https://b.test")


def test_parse_allowed_origins_wildcard_wins():
    origins = parse_allowed_origins("*, https://irrelevant.test")
    assert origins == ("*",)


def test_configure_cors_allows_specific_origin():
    app = Flask(__name__)
    configure_cors(app, ("https://allowed.test",))

    @app.route("/ping", methods=["GET", "POST"])
    def _ping():
        return {"ok": True}

    client = app.test_client()
    response = client.get("/ping", headers={"Origin": "https://allowed.test"})

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "https://allowed.test"
    assert "Origin" in response.headers.getlist("Vary")

    blocked = client.get("/ping", headers={"Origin": "https://blocked.test"})
    assert "Access-Control-Allow-Origin" not in blocked.headers


def test_configure_cors_allows_wildcard():
    app = Flask(__name__)
    configure_cors(app, ("*",))

    @app.route("/ping", methods=["GET", "POST"])
    def _ping():
        return {"ok": True}

    client = app.test_client()
    response = client.get("/ping", headers={"Origin": "https://anything.test"})
    assert response.headers["Access-Control-Allow-Origin"] == "*"


def test_preflight_request_receives_cors_headers():
    app = Flask(__name__)
    configure_cors(app, ("https://allowed.test",))

    @app.route("/ping", methods=["GET", "POST"])
    def _ping():
        return {"ok": True}

    client = app.test_client()
    response = client.options(
        "/ping",
        headers={
            "Origin": "https://allowed.test",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization",
        },
    )

    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == "https://allowed.test"
    assert (
        response.headers["Access-Control-Allow-Headers"]
        == "Content-Type, Authorization"
    )
    assert response.headers["Access-Control-Allow-Methods"] == "POST"
