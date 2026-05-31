# Seed notes — zigbee-control-ui

First architecture artifact for the ZigbeeControlUI repo, seeded headless.
Mode: **hand-authored** (no generator; the YAML is the source of truth).

Producer id: `zigbee-control-ui`. `introduced` on every element = this repo's
first commit date, `2025-09-27`.

## What this repo is

A React 19 + TypeScript + Vite single-page app — the "Z2M Wrapper" UI. It is
built to static assets and served by nginx (`nginx.conf`, listen 3200). It is
the web UI for the Zigbee Control backend: a tab shell, a shared-secret/OIDC
auth gate, Kubernetes rollout-restart controls, and live per-tab status. All of
its server-side logic lives in the separate `zigbee-control` (backend) and
`ssegateway` producers; this repo owns only the frontend product.

## Elements minted (all uuid4, mint-once)

| id | kind | label |
|---|---|---|
| `app:zigbee-control-ui,880df297-2b73-4198-8f92-028d84118be9` | ApplicationComponent «SoftwareProduct» | Zigbee Control UI |
| `svc:zigbee-control-ui-web,13c8cfe4-27ab-47fb-bae7-035d08176913` | ApplicationService | Zigbee Control UI web app |
| `if:zigbee-control-ui-browser,23738d07-7368-494a-a643-d7c71557212d` | ApplicationInterface | Zigbee Control UI (browser) |

`app:zigbee-control-ui` carries `sourceRepository: git:pvginkel/ZigbeeControlUI`
and `stats.image: registry:5000/zigbee-control-ui` (both fixed facts for this seed).

## Relations

- `app:zigbee-control-ui —Realization→ svc:zigbee-control-ui-web` — the product
  realizes the web UI it serves.
- `if:zigbee-control-ui-browser —Assignment→ svc:zigbee-control-ui-web` — one
  interface for the single consumer class (the end-user browser).
- `app:zigbee-control-ui —Association→ svc:zigbee-control-api,ce8d7938-…` —
  **frontend → backend** consumption edge (cross-producer, see below).
- `app:zigbee-control-ui —Association→ svc:ssegateway,59a7d043-…` —
  **frontend → SSE gateway** subscribe edge (cross-producer, see below).

## Exposed surface decision

Modeled the served SPA as **one** ApplicationService (`svc:zigbee-control-ui-web`)
with **one** ApplicationInterface (the browser consumer). Rationale: the deployer
(HelmCharts) that publishes this UI publicly attaches the public ingress host as
an ApplicationInterface on the product's realized service; that requires the
product to carry an `app —Realization→ svc` edge, so the frontend declares its
own service rather than leaving the deployer to mint one. Single consumer class
(end-user browser, including the iframe embed in the webathome.org portal) → a
single interface, per the "one interface per distinct consumer" rule.

Borderline: a pure static-asset SPA delivered to humans could instead be read as
a BusinessService. Chose ApplicationService to match the deployer-attaches-host
mechanic and the standard frontend pattern. Open question for a human below.

## Cross-producer references

Both resolved from the **local sibling backfill checkouts** (these producers are
part of the same backfill batch and may not be published yet — refs may dangle
in the merged `validation-report.json` until their first builds register; the
validator reports, does not fail, on this):

- `svc:zigbee-control-api,ce8d7938-5d7d-4eee-abab-294cf19315e7` — from
  `../ZigbeeControl/docs/architecture/architecture.yaml` (the backend's exposed
  API ApplicationService). This is the frontend→backend edge the seed brief
  required.
- `svc:ssegateway,59a7d043-bb0c-4e44-a8b8-3e943338f807` — from
  `../SSEGateway/docs/architecture/architecture.yaml`. The gateway's own artifact
  declares an `if:ssegateway-stream` interface explicitly for "browser SSE
  clients", which is exactly what this UI consumes via `/api/sse/stream`.

## boundBy decisions

**No `boundBy` on either outbound edge.** Every server the SPA talks to is
reached through a **same-origin relative path** that this repo's own nginx
reverse-proxies to a same-pod sidecar (hardcoded in `nginx.conf`), not through a
container env var:

- `/api/` → `127.0.0.1:3201` (backend) — `src/**` calls `/api/...` relatively.
- `/api/sse/stream` → `127.0.0.1:3202` (SSE gateway) — `src/workers/sse-worker.ts`
  and `src/contexts/sse-context-provider.tsx` open `EventSource('/api/sse/stream')`.

`boundBy` is `env:<VAR>` only; with no env var carrying an endpoint, it is
correctly omitted (and it is optional anyway for `svc:` targets).

## Excluded / out

- **Google Fonts stylesheet** (`index.html` → `https://fonts.googleapis.com/...`)
  — a static font asset CDN, not an API this app calls. `out` (the manual's
  "URL-rewriter / helper that is not an API you call is OUT"; don't invent a
  capability for it).
- **nginx `/health`** endpoint and the nginx security headers — operational
  surface of the deployment/ingress, not the app's architecture. `out`.
- **nginx reverse-proxy targets** (`127.0.0.1:3201/3202`) — deploy-time wiring,
  captured as the consumption edges above, not as separate elements.
- **No IAM edge for the frontend.** Auth is handled by the backend: the SPA only
  calls the backend's `/api/auth/{self,login,logout}` endpoints (OIDC role check
  lives server-side). The IdP dependency is the backend's (`zigbee-control`
  already models `app:zigbee-control —Association→ cap:iam`). Modeling it here
  too would double-count a dependency the frontend does not hold directly.
- **No capability realizations.** The UI provides no platform capability.
- `thumbnail-urls.ts` / CAS URL helper — generic template leftover, not wired to
  any external service here. `out`.

## Open questions for a human (decided headless, flag for review)

1. **Frontend as ApplicationService vs BusinessService.** Modeled the served SPA
   as an ApplicationService + browser ApplicationInterface. If the convention for
   pure frontends in this federation is to leave the served surface to the
   deployer (mint nothing here) or to model it as a BusinessService, revise. This
   is the **first UI producer seeded**, so it sets the pattern for the sibling
   `*UI` repos (DHCPAppUI, ElectronicsInventoryUI, IoTSupportUI).
2. **frontend → SSE gateway edge.** Included it because the SPA subscribes to the
   gateway's browser-client stream directly (distinct from the backend's
   publish-side edge). If the intent is to treat the gateway purely as a backend
   concern and collapse all UI realtime under the frontend→backend edge, drop
   `rel:zigbee-control-ui-consumes-sse-gateway`.
3. **CLAUDE.md vs AGENTS.md.** This repo has no `CLAUDE.md`; it uses `AGENTS.md`.
   Appended the federated-architecture snippet to `AGENTS.md`.
