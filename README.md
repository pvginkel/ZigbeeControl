# Z2M Wrapper Backend

Backend service exposing configuration, restart controls, and status streaming for the Z2M Wrapper UI.

## Running

1. Copy `.env.example` to `.env` and set `APP_TABS_CONFIG`, network bindings, and `FLASK_ENV` (`development` or `production`).
2. Install dependencies and run:

```bash
poetry install
poetry run dev
```

In production mode (`FLASK_ENV=production`) the service is served by Waitress; development mode keeps the Flask reloader/debugger enabled.

## API Endpoints

All endpoints are served under `/api` and return JSON unless noted otherwise.

### GET `/api/config`
- **Description:** Fetches the tab configuration that the frontend should render.
- **Response:**
  ```json
  {
    "tabs": [
      {
        "text": "Primary Dashboard",
        "iconUrl": "https://example.com/icon.svg",
        "iframeUrl": "https://example.com/dashboard",
        "restartable": false
      }
    ]
  }
  ```
- **Status codes:** `200 OK` on success.

### POST `/api/restart/<idx>`
- **Description:** Triggers an optimistic restart for the tab at index `<idx>` when it has Kubernetes metadata.
- **Response:**
  ```json
  {
    "status": "restarting",
    "message": null
  }
  ```
- **Status codes:**
  - `200 OK` when the restart request is accepted.
  - `400 Bad Request` if the tab is not restartable.
  - `404 Not Found` if the index is out of range.
  - `409 Conflict` if a restart for the deployment is already in progress.
  - `500 Internal Server Error` for unexpected Kubernetes or configuration issues.

### GET `/api/status/<idx>/stream`
- **Description:** Server-Sent Events stream that emits status updates for tab `<idx>`.
- **Usage:** Subscribe via an `EventSource` in the browser or any SSE-capable client. Example event payload:
  ```text
  retry: 3000
  event: status
  data: {"state": "running", "message": null}

  ```
- **Initial behaviour:** The latest known state (`running`, `restarting`, or `error`) is sent immediately upon connection.

