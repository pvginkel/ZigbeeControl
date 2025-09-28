# Z2M Wrapper Backend

Backend service exposing configuration, restart controls, and status streaming for the Z2M Wrapper UI.

## Running

1. Copy `.env.example` to `.env` and set `APP_TABS_CONFIG`, network bindings, and `FLASK_ENV` (`development` or `production`).
2. Install dependencies and run:

```bash
poetry install
poetry run z2m-backend
```

In production mode the service is served by Waitress; development mode keeps the Flask reloader/debugger enabled.
