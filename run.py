"""Entry point for running the Z2M Wrapper backend."""

from __future__ import annotations

import os
import logging

from app import create_app

_DEV = "development"
_PROD = "production"
_VALID_ENVS = {_DEV, _PROD}


def _resolve_env() -> str:
    value = os.getenv("FLASK_ENV", _DEV).strip().lower()
    if value not in _VALID_ENVS:
        raise SystemExit(
            "FLASK_ENV must be one of {development, production}; "
            f"got '{value or '<empty>'}'"
        )
    return value


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    app = create_app()

    host = os.getenv("Z2M_BACKEND_HOST", "0.0.0.0")
    port_value = os.getenv("Z2M_BACKEND_PORT", "5000")
    try:
        port = int(port_value)
    except ValueError as exc:  # pragma: no cover - defensive parsing guard
        raise SystemExit(f"Invalid port number '{port_value}'") from exc

    env = _resolve_env()

    if env == _PROD:
        from waitress import serve  # type: ignore[import-not-found]

        serve(app, host=host, port=port, threads=20)
    else:
        app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()

