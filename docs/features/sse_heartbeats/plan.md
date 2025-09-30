Brief
- Ensure the SSE status stream sends a heartbeat event every interval so Waitress cleans up dead connections, with the interval controlled by a new environment variable that defaults to 5 seconds in develop and 30 seconds in production.

Files & Modules
- `app/__init__.py`: parse `APP_SSE_HEARTBEAT_SECONDS`, apply the 5s/30s defaults based on `FLASK_ENV`, validate it is positive, and expose the interval (e.g. via `app.config` and `app.extensions["z2m"]`).
- `app/api/__init__.py`: thread the resolved heartbeat interval into the status route factory.
- `app/api/status.py`: request the broadcaster stream with the heartbeat interval and pass it along to the SSE response helper.
- `app/services/status_broadcaster.py`: extend `listen()` to optionally emit heartbeat ticks when idle, ensure subscribers still receive the immediate cached status, and guarantee the subscription tears down cleanly when the generator closes.
- `app/utils/sse.py`: add helpers to format `event: heartbeat` messages, adjust the streaming generator to handle both status and heartbeat events, and keep existing headers (`retry: 3000`, `Cache-Control: no-cache`).
- `tests/services/test_kubernetes_service.py`: update `_consume` (and any related helpers) so it ignores heartbeat ticks while waiting for concrete status payloads.
- `tests/utils/test_sse.py`: add coverage for heartbeat formatting and verify the streaming response emits heartbeat frames at the configured cadence when no status updates arrive.
- `.env.example`, `README.md`, and any operator docs that enumerate environment variables: document `APP_SSE_HEARTBEAT_SECONDS`, noting the "send a heartbeat event every interval" behaviour and the develop/production defaults.
- Update `AGENTS.md` so the SSE contract explicitly covers heartbeat frames once implementation lands.

Algorithm & Flow
1. Interval resolution
   - At app startup read `APP_SSE_HEARTBEAT_SECONDS`; if unset, treat `FLASK_ENV` case-insensitively and pick 5 seconds for development, 30 seconds otherwise; coerce to float/int seconds, enforce it is > 0, and store the final number where both the status blueprint and utilities can access it.
2. Status stream heartbeat ticks
   - When `listen()` receives a `heartbeat_interval`, keep using the per-tab queue for real status payloads; track `last_sent` via `time.perf_counter()`.
   - On each `queue.Empty`, compare `now - last_sent`; once it reaches the configured interval, yield a heartbeat marker and reset `last_sent`; continue looping so that we still propagate late statuses immediately.
   - Preserve existing behaviour for initial cached status and for cases where no interval is provided (e.g. tests that call `listen()` directly).
3. SSE response formatting
   - Update `sse_response()` (and its helpers) to accept the new marker objects: serialize status payloads exactly as today, and serialize heartbeat markers as lightweight `event: heartbeat` messages (blank or `{}` data is sufficient) so that "Waitress should detect the disconnect when we attempt to send a heartbeat".
   - Make sure generator teardown still closes the broadcaster subscription even if the client disconnects during a heartbeat write.

Testing
- Extend service-layer tests to tolerate injected heartbeat markers by skipping them inside `_consume`, keeping assertions on the sequence of status states.
- Add a dedicated unit test that patches `time.perf_counter()` to simulate idle periods and asserts `StatusBroadcaster.listen(..., heartbeat_interval=...)` yields heartbeat markers at the requested cadence.
- Configure the test suite to pass a 1-second heartbeat interval (via environment override or fixture) so unit runs are not delayed.
- Update SSE utility tests to verify the new `event: heartbeat` format and that `sse_response()` emits both status and heartbeat frames in order for a synthetic idle stream.
- Consider a Flask test that exercises `/api/status/<idx>/stream` with a short heartbeat interval to ensure the integration path surfaces both event types without extra buffering.

Documentation
- Note the new `APP_SSE_HEARTBEAT_SECONDS` knob (defaults: 5 seconds for develop, 30 seconds for production) in `.env.example`, `README.md`, and any relevant operator guidance so the interval remains configurable during deployment.
