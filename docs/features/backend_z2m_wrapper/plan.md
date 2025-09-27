Brief
- Build the Flask backend that powers the "Z2M Wrapper" by serving the tab configuration from YAML, exposing `GET /api/config`, `POST /api/restart/<idx>`, and `GET /api/status/<idx>/stream`, and orchestrating Kubernetes rollouts while emitting SSE `status` events (`running`, `restarting`, `error`).

Files & Modules
- `app/__init__.py`: define `create_app()` that loads config via `APP_TABS_CONFIG`, wires dependency injection, registers API blueprints, and initializes Spectree + CORS-free settings.
- `app/api/__init__.py`: create blueprint factory, attach routes, and centralize error handlers for validation and service-layer exceptions.
- `app/api/config.py`: implement `GET /api/config` handler that returns normalized tab payloads and leverages Spectree response schemas.
- `app/api/restart.py`: implement `POST /api/restart/<idx>` route with request validation (index bounds, restartable flag) and invoke the restart service.
- `app/api/status.py`: implement `GET /api/status/<idx>/stream` SSE endpoint using a streaming response generator from `utils.sse`.
- `app/schemas/config.py`: define Pydantic models for YAML tabs (`text`, `iconUrl`, `iframeUrl`, optional `k8s.namespace` and `k8s.deployment`) and API responses.
- `app/services/config_service.py`: encapsulate config loading, caching, optional reload hook, and provide tab metadata to routes while preventing mutation.
- `app/services/kubernetes_service.py`: wrap Kubernetes Python client to trigger rollout restarts, dedupe concurrent restarts per deployment, and report status updates to listeners using dedicated worker threads.
- `app/utils/config_loader.py`: read the YAML pointed to by `APP_TABS_CONFIG`, validate against schemas, and surface detailed errors.
- `app/utils/sse.py`: expose helpers to format `event: status` blocks with `retry: 3000`, JSON payloads, and proper headers for Flask streaming responses.
- `app/services/status_broadcaster.py`: manage per-tab thread-safe status channels, retain last known `running`/`restarting`/`error` state for late subscribers, and interface with the SSE generator.
- `tests/api/test_config_endpoint.py`: cover happy path, missing config, and malformed YAML responses.
- `tests/api/test_restart_endpoint.py`: mock Kubernetes service to ensure optimistic `restarting`, duplicate restart guard, and error propagation.
- `tests/services/test_kubernetes_service.py`: simulate success, timeout (~180s), and failure scenarios using fake watch streams from the Kubernetes client.
- `tests/utils/test_sse.py`: verify formatting of SSE payloads and retry headers.

Core Flows & Algorithms
1. Config bootstrap
   - On `create_app()`, read `APP_TABS_CONFIG` via `config_loader`, validate against `schemas.config`, and store the immutable tab list in `ConfigService`.
   - Provide `ConfigService.get_tabs()` for API use; expose helper `assert_restartable(idx)` to centralize index bounds and `k8s` presence checks.
2. Restart orchestration
   - `POST /api/restart/<idx>`: resolve tab metadata, call `KubernetesService.request_restart(tab.k8s)` which immediately emits `restarting` to `StatusBroadcaster` and spins up a dedicated worker thread for the rollout.
   - The worker thread patches the Deployment (`spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = iso timestamp`), then polls Deployment status watching conditions or pod readiness until success or timeout (~180 seconds mirroring the existing script).
   - On success: emit `running`; on timeout or API error: emit `error` with diagnostic message; dedupe by tracking in-flight restarts per `namespace/deployment`.
3. SSE streaming
   - `GET /api/status/<idx>/stream`: fetch broadcaster channel for the tab, yield last-known status immediately, then stream future events using the SSE helper to format `event: status` + JSON payload + `retry: 3000` lines.
   - Handle client disconnects gracefully (StopIteration on generator); when reconnecting, the cached state ensures instant `running`/`restarting`/`error` replay.
4. Status propagation
   - `StatusBroadcaster` maintains per-tab thread-safe queues (e.g., `queue.Queue` with `threading.Condition`) and ensures only the latest state is kept while still broadcasting fresh events to all listeners.

Validation & Error Handling
- Raise structured exceptions (`ConfigNotLoaded`, `TabNotRestartable`, `RestartInProgress`, `RestartTimeout`) in services, map them to JSON error bodies in the API layer with HTTP 4xx/5xx codes and messages surfaced to SSE `error` payloads.
- Spectree + Pydantic enforce schema contract for both responses (`GET /api/config`) and simple request params (tab index path parameter).
- Log Kubernetes API failures with namespace/deployment context for operator debugging without leaking stack traces to clients.

Testing Notes
- Mock filesystem reads to feed YAML fixtures that match the product brief example and edge cases (missing `k8s`, malformed fields).
- Patch Kubernetes Python client (`AppsV1Api`, `Watch`) to simulate rollout progressions, errors, and timeouts; ensure dedupe logic prevents overlapping rollouts.
- Use Flask test client with streaming responses to confirm SSE generator yields correctly formatted `event: status` messages and closes on disconnect.
