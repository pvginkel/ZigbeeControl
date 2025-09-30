Brief description
- Implement cookie-based protection for all backend API routes except the login endpoint, driven by an "Environment variable with a secret token" and a POST path that issues the cookie. Provide a dedicated probe endpoint that returns 200 when the cookie is valid and 403 otherwise so NGINX can use auth_request, adapting the supplied JWT cookie sample (partitioned, SameSite=None) to this application. Note that `AGENTS.md` must be updated to reflect that authentication is now in scope.

Relevant files and functions
- app/__init__.py: load the auth token from the environment, initialise Flask secret key as needed, register auth helpers on the API blueprint, and ensure the JWT library is configured.
- app/api/__init__.py and new app/api/auth.py: add authentication routes (`POST /api/auth/login`, `GET /api/auth/check`) plus before_request protection for existing routes, using the provided sample as behavioural reference.
- app/schemas/auth.py (new): define Spectree/Pydantic models for the login request payload, login response, unauthorized error, and check response used by `/api/auth/*` endpoints.
- app/utils/auth.py (new): encapsulate PyJWT encode/decode, cookie header composition (including Partitioned attribute), and validation helpers.
- app/services/__init__.py (if needed) and related modules: expose the auth helper via app.extensions for reuse in handlers and tests.
- app/api/config.py, app/api/restart.py, app/api/status.py: confirm they operate behind the auth guard; no direct logic changes anticipated beyond imports.
- tests/conftest.py: seed the auth environment variable, configure Flask SECRET_KEY, and add fixtures for authenticated test clients using the JWT cookie flow.
- tests/api/...: extend coverage for login success/failure, cookie verification, guard enforcement on existing endpoints, and the new probe endpoint responses.
- pyproject.toml / poetry.lock: add PyJWT dependency required by the sample.
- docs/README or dedicated auth documentation: describe environment variables, JWT-backed cookie behaviour (SameSite=None; Secure; HttpOnly; Partitioned), login flow, and `/api/auth/check` for NGINX auth_request.
- AGENTS.md: record that authentication is required so the agent brief and product scope stay consistent.
- docs/product_brief.md: expand the scope section to acknowledge authentication support before implementation proceeds.

Implementation steps
1. Define configuration
   - Introduce environment variables such as `APP_AUTH_TOKEN` for the shared secret, `APP_AUTH_COOKIE_NAME` for clarity, optionally `APP_SECRET_KEY` for Flask session/signing needs, and `APP_AUTH_DISABLED` (or similar) to allow an explicit dev bypass.
   - Treat authentication as mandatory unless the bypass flag is enabled; fail fast when `APP_AUTH_TOKEN` is missing. When disabled, ensure the backend never returns HTTP 403 from `/api/auth/check` and the guard admits all requests.

2. Build auth utilities from the sample
   - Implement helpers that wrap PyJWT encode/decode using the shared secret and HS256, mirroring the sample’s behaviour (no exp claim, constant-time comparison not required because signature verification handles integrity).
   - Centralise cookie emission so `set_cookie` covers HttpOnly, Secure, SameSite=None, and an additional raw header appends `Partitioned` (as demonstrated in the sample).
   - Provide verification helpers that decode the cookie, handle exceptions, and return explicit status values for the guard and probe endpoint.

3. Define schemas and validation
   - Add `LoginRequest`, `LoginResponse`, `AuthErrorResponse`, and `AuthCheckResponse` Pydantic models under `app/schemas/auth.py`, matching the exact JSON structures the endpoints exchange.
   - Register these schemas with Spectree decorators so `/api/auth/login` and `/api/auth/check` benefit from validation and documentation updates alongside existing endpoints.

4. Add auth endpoints
   - Create `POST /api/auth/login` that consumes `LoginRequest`, compares the provided token with `APP_AUTH_TOKEN`, issues the signed cookie on success (including both headers), and returns a `LoginResponse`; reject invalid tokens with HTTP 403 and `AuthErrorResponse`.
   - Create `GET /api/auth/check` that reads the cookie, verifies the JWT signature, and returns 200 with `AuthCheckResponse` when valid. When `APP_AUTH_DISABLED` is active, short-circuit to success. Otherwise, return HTTP 403 with `AuthErrorResponse` when the cookie is missing/invalid so NGINX auth_request can propagate the failure.
   - Optionally expose a logout route (similar to the sample) that clears both cookie variants if deemed useful; scope this as nice-to-have for documentation.

5. Protect existing APIs
   - Register a `before_request` guard on the API blueprint that bypasses only the login (and optional logout) endpoints while enforcing JWT cookie validation for config, restart, and status routes; respond with `AuthErrorResponse` and HTTP 403 on failures to align with the probe behaviour unless `APP_AUTH_DISABLED` permits the request.
   - Confirm that SSE responses remain streamable after the guard (consider verifying headers in tests) and that restart POST still returns existing payloads when authenticated.

6. Update configuration and dependency injection
   - Store the auth utility/service inside `app.extensions["z2m"]` alongside existing services for easy access during testing and potential future features.
   - Log helpful context when auth initialises (e.g., cookie name, disabled mode) without exposing secrets, and surface clear exceptions when misconfigured.

7. Testing
   - Extend pytest fixtures to populate the auth env vars, instantiate PyJWT for tests, and provide a helper that performs the login POST to capture the cookie headers used for subsequent requests (including the Partitioned header path).
   - Add tests covering: successful login (returns cookie headers), failed login (403), `/api/auth/check` responses with/without valid cookie, unauthorized access to `/api/config`, `/api/restart/<idx>`, `/api/status/<idx>/stream` when missing cookie, and successful access once the cookie is supplied or bypassed via `APP_AUTH_DISABLED`.
   - Adjust existing endpoint tests to call the login helper before hitting protected routes or update expectations to account for the 403 guard when not authenticated.

8. Documentation
   - Update README or new auth doc to explain how to set `APP_AUTH_TOKEN`, mention PyJWT-based cookie format, reference the Partitioned attribute requirement for iframe compatibility, detail the login flow, clarify the `/api/auth/check` usage for NGINX `auth_request`, and document `APP_AUTH_DISABLED` semantics.
   - Update `AGENTS.md` so it reflects that authentication is now part of the supported scope.
   - Update `docs/product_brief.md` so the product narrative aligns with the new authentication requirement before shipping the feature.

Phasing considerations
- Phase 1: Add PyJWT dependency, environment configuration, auth utilities, and new endpoints with isolated tests.
- Phase 2: Apply the guard to existing routes, retrofit tests, and complete documentation updates.
