# Z2M Wrapper - Agent Guidelines

This document distills the current product brief so agents and contributors stay aligned while iterating on the Z2M Wrapper project.

## Purpose & Audience
- **Goal:** Deliver a lightweight web UI that wraps three existing services (two Zigbee2MQTT dashboards and a code-server instance) inside persistent IFRAME tabs.
- **Users:** Single-operator, LAN-only usage. Authentication is a shared secret that issues an HttpOnly cookie; no multi-tenant requirements.
- **Scope:** Tabbed interface, optional restart controls for Kubernetes-backed tabs, live status via Server-Sent Events (SSE), and lightweight shared-secret cookie authentication. Nothing beyond those concerns.

## Architecture Overview
- **Frontend:** React 19 + TypeScript + Vite. Tabs as internal state (no router). Zustand or reducer-based state is acceptable. Use TanStack Query for the restart mutation and any light caching.
- **Backend:** Flask application with layered modules: `api/` (Blueprints & validation), `services/` (Kubernetes orchestration), `schemas/` (Pydantic models), `utils/` (SSE helpers, config loader). Dependency injection mirrors existing Flask projects, minus persistence.
- **Persistence:** None. All runtime state is in memory; configuration originates from YAML.
- **Config Source:** YAML file path supplied by `APP_TABS_CONFIG` environment variable. Keep schema minimal: `text`, `iconUrl`, `iframeUrl`, and optional `k8s` block with `namespace` and `deployment` strings.

## Backend Expectations
- Keep API surface tiny: `POST /api/auth/login`, `GET /api/auth/check`, `GET /api/config`, `POST /api/restart/<idx>`, `GET /api/status/<idx>/stream`.
- Use Pydantic schemas (Spectree integration) for request/response validation.
- `KubernetesService` (or equivalent) handles rollout restarts and status watching using the official Python client. Guard against duplicate restarts on the same deployment.
- SSE streaming helpers should emit `event: status` messages with JSON payloads limited to `running`, `restarting`, or `error` (with optional `message`). Include sensible retry headers (`retry: 3000`).
- Treat restart workflow as optimistic: immediately report `restarting`, observe Kubernetes conditions/pod readiness, then flip to `running` or `error` within ~180 seconds. Timeout should mirror existing script behaviour.
- Favor clear error propagation-no silent failures. Expose useful context in exceptions that wind up on the SSE or REST responses.

## Frontend Expectations
- Render tabs with icon + label on the left; restart icon aligned right when the tab is restart-capable.
- Instantiate each tab's IFRAME lazily on first activation and never unmount it; subsequent tab switches hide/show via CSS.
- Maintain per-tab status state that defaults to `running`. On restart action, set `restarting` immediately, then rely on SSE updates.
- `useSseStatus(tabConfig)` hook should wrap `EventSource` with automatic reconnect/backoff. Ensure cleanup on unmount.
- Visual states: `running` (default icon), `restarting` (blink animation), `error` (error badge overlay). No toasts or banners.
- Accessibility: Implement `role="tablist"`, `role="tab"`, `aria-selected`, keyboard navigation, and visible focus styles.

## Restart & Status Flow
1. Frontend loads config via `GET /api/config`; initial tab becomes active and its IFRAME mounts immediately.
2. For restartable tabs, frontend opens an SSE stream targeting `GET /api/status/<idx>/stream` as soon as the tab exists.
3. Clicking restart triggers `POST /api/restart/<idx>`; UI flips to `restarting`. Backend patches the Deployment (`kubectl rollout restart` equivalent) and monitors progress.
4. SSE emits `restarting` then `running` on success, or `error` with diagnostic text if timeout/rollout failure occurs.

## Non-Functional Constraints
- Shared-secret cookie authentication only; no RBAC or metrics. Keep dependencies minimal.
- Prioritize simplicity and resilience: SSE should auto-retry, and backend should gracefully handle reconnects.
- LAN deployment assumed. Coordinate iframe hosting origins via reverse proxy/CSP headers (see product brief section 13 for operator guidance).

## Out of Scope
- Extending beyond tabs + restart control.
- Persisted state, analytics, or Prometheus metrics.
- Ingress, TLS, or NGINX setup (handled externally).

## Testing & Validation
- Unit test services responsible for Kubernetes interactions, including successful restart, timeout, and error paths.
- Exercise SSE utilities to ensure correct event formatting and retry headers.
- Frontend tests should cover tab switching, lazy iframe behaviour, restart button state changes, and SSE-driven updates (using mocks where appropriate).
- Integration smoke tests may simulate the restart endpoint and SSE flow without reaching a real cluster (mock Kubernetes client).

## Developer Workflow Checklist
1. Load and understand the YAML config schema before implementing features.
2. Build backend service/API logic with thorough tests for restart orchestration.
3. Implement frontend tab mechanics and SSE handling with matching UI states.
4. Verify end-to-end restart flow (happy path and timeout). Document any manual steps for the operator.
5. Keep documentation synchronized with config changes or new behaviours.
6. Run project commands through Poetry (e.g. `poetry run pytest`, `poetry run flask --help`).
