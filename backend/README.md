# Z2M Wrapper Backend

Backend service exposing configuration, restart controls, and status streaming for the Z2M Wrapper UI.

## Running

1. `kc project setup`, from the repository root, installs the dependencies for the
   whole monorepo. It also seeds a minimal `backend/.env` pointing `APP_TABS_CONFIG`
   at the checked-in `test/tabs.yaml`, because the app will not start without a tabs
   file outside `FLASK_ENV=testing`. An existing `.env` is never overwritten.
2. To go further, copy `.env.example` over it and set `APP_TABS_CONFIG`, network
   bindings, `FLASK_ENV` (`development` or `production`) and the `OIDC_*` settings.
3. Start the whole dev stack — backend on :3201, frontend on :3200, SSE gateway on
   :3202 — with `scripts/dev.py` from the repository root. To run this service on its
   own, from `backend/` (poetry lives in the `modern-app` tool container, not the dev
   container):

```bash
cexec modern-app poetry run dev
```

In production mode (`FLASK_ENV=production`) the service is served by Waitress; development mode keeps the Flask reloader/debugger enabled.

## API Endpoints

All endpoints are served under `/api` and return JSON unless noted otherwise.

Authentication is OIDC, authorization code with PKCE, with this backend as the confidential client.
When `OIDC_ENABLED=true`, every endpoint below other than the `/api/auth/*` flow itself requires the
session cookie named by `OIDC_COOKIE_NAME` (default `access_token`), which `/api/auth/callback` sets.
Development turns it off with `OIDC_ENABLED=false` — the default when the variable is unset: no
cookie is then required and `/api/auth/self` answers with a synthetic `local-user`.

### GET `/api/auth/login`
- **Description:** Starts the OIDC flow. Takes a required `redirect` query parameter — where to land after login — validated against `BASEURL` to prevent open redirects. The PKCE verifier, nonce and redirect target are encrypted into the OAuth `state` parameter rather than held in a cookie, so the flow also works when the UI runs inside a cross-origin iframe.
- **Status codes:**
  - `302 Found` to the provider's authorization endpoint.
  - `400 Bad Request` when `redirect` is missing or fails validation, or when `OIDC_ENABLED=false`.

### GET `/api/auth/callback`
- **Description:** The provider's redirect target. Decrypts `state`, exchanges `code` for tokens, validates the access token, then redirects to the `redirect` URL the login carried, with cookies set: `OIDC_COOKIE_NAME` (access token), `OIDC_REFRESH_COOKIE_NAME` (refresh token, when the provider issues one) and `id_token` (kept for logout). Cookie flags come from the `OIDC_COOKIE_*` group; `Secure` is inferred from `BASEURL` when `OIDC_COOKIE_SECURE` is left unset.
- **Status codes:**
  - `302 Found` to the original redirect URL.
  - `400 Bad Request` for a missing or undecryptable `code`/`state`, or when `OIDC_ENABLED=false`.
  - `401 Unauthorized` when the token exchange or token validation fails.

### GET `/api/auth/logout`
- **Description:** Clears the three auth cookies and, when `OIDC_ENABLED=true`, redirects to the provider's `end_session_endpoint` with `id_token_hint` so the session ends at the IdP too; with OIDC off, or when the provider advertises no end-session endpoint, it redirects straight to `redirect`. Takes an optional `redirect` query parameter (default `/`), validated against `BASEURL`.
- **Status codes:** `302 Found`.

### GET `/api/auth/self`
- **Description:** Reports the current user. This one endpoint is public in the routing sense — it authenticates the caller itself — so an unauthenticated request gets a status rather than a redirect. With `OIDC_ENABLED=false` it returns a `local-user` holding `admin` and everything that role expands to.
- **Response:**
  ```json
  {
    "subject": "3f9a…",
    "email": "someone@example.com",
    "name": "Someone",
    "roles": ["admin", "editor", "reader"]
  }
  ```
- **Status codes:**
  - `200 OK` with the user's identity and expanded roles.
  - `401 Unauthorized` when no valid token is presented.
  - `403 Forbidden` when the token is valid but carries no recognised role.

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
- **Auth:** The tab must be restartable.
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
- **Description:** Server-Sent Events stream that emits status updates for tab `<idx>`, interleaved with lightweight `event: heartbeat` frames when no state changes occur.
- **Usage:** Subscribe via an `EventSource` in the browser or any SSE-capable client. Example event payload:
  ```text
  retry: 3000
  event: status
  data: {"state": "running", "message": null}

  ```
- **Initial behaviour:** The latest known state (`running`, `restarting`, or `error`) is sent immediately upon connection.
- **Heartbeat:** The backend sends `event: heartbeat` frames every `SSE_HEARTBEAT_INTERVAL` seconds (5 in development, forced to 30 in production) so intermediaries such as Waitress can notice disconnected clients.
