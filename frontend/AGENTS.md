# Z2M Wrapper – Agent Notes

Quick orientation for agents; full specs live in the linked docs.

## Core References

- `docs/product_brief.md` — authoritative scope, workflows, architecture, and success criteria for the wrapper UI.
- Command templates for structured tasks: `docs/commands/create_brief.md`, `docs/commands/plan_feature.md`, `docs/commands/review_plan.md`, `docs/commands/code_review.md`.

## Product Snapshot

- Single-page React 19 wrapper exposing three tabs (Zigbee2MQTT – 1, Zigbee2MQTT – 2, Code Server) sourced from YAML config.
- Tabs create their iframe the first time they are opened and keep it mounted; switching tabs only toggles visibility.
- Kubernetes-enabled tabs (those with a `k8s` block in config) surface a restart button; clicking triggers the rollout restart flow and optimistic `restarting` state.
- Frontend opens an SSE stream per restartable tab to keep the tab icon in sync (`running` / `restarting` / `error`) without manual refresh.
- Wrapper presents a single-field password gate that checks `/api/auth/check`, posts to `/api/auth/login`, and only mounts the tab UI once the shared cookie is present.

## Working Guidelines

1. Keep scope tight to the brief: tab wrapper, restart control, auth gate, and status indicators—no metrics or extra tab settings.
2. Treat the YAML at `APP_TABS_CONFIG` as the source of truth; avoid hard-coded tab definitions or one-off overrides.
3. Use the restart mutation + SSE pattern described in the brief (optimistic UI, auto-reconnect, icon-only feedback).
4. Preserve accessibility for the tablist (roles, aria attributes, keyboard navigation) while maintaining the minimal visual design.

## Boundaries & Risks

- Do not unmount iframes on tab switch; hide/show to guarantee <100 ms tab activation.
- No toast/banners for restart status—icons convey state changes.
- Watch for services that block being embedded (`X-Frame-Options`, CSP); mitigations are in the brief’s deployment notes.
- Backend mirrors the Flask layering pattern; stay aligned with the documented API surface (`/api/auth/check`, `/api/auth/login`, `/api/config`, `/api/restart/:idx`, `/api/status/:idx/stream`).

For anything beyond this quick reminder, return to `docs/product_brief.md`; it stays canonical.
