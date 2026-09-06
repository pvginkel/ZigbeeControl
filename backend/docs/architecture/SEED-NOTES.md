# SEED-NOTES — zigbee-control producer

> **Superseded in part (monorepo merge).** ZigbeeControlUI has been merged into
> this repo under `frontend/`, and its artifact now declares this same
> `zigbee-control` producer — one repo publishes one producer. Where the notes
> below call the SPA "a separate producer", that is no longer true. Everything
> below is the original seeding record, kept as written; `architecture.yaml` is
> authoritative.

Headless seed of the first architecture artifact for the ZigbeeControl repo
(Z2M Wrapper backend). Mode: **hand-authored** (no generator; the YAML is the
source of truth). All decisions below were made without operator triage; open
questions are collected at the end.

## Identity (fixed, not re-derived)

- Producer envelope key: `zigbee-control`
- `introduced` on every element: **2025-09-27** (repo's first commit:
  `git log --reverse --format=%ad --date=short | head -1`).

## Minted elements (uuid4, mint-once)

| Element | id | Notes |
|---|---|---|
| «SoftwareProduct» ApplicationComponent | `app:zigbee-control,c7890844-dbf2-4ea2-a468-c3280176d646` | Backend product identity. `stereotype: SoftwareProduct`, `sourceRepository: git:pvginkel/ZigbeeControl`, `stats.image: registry:5000/zigbee-control`. |
| ApplicationService | `svc:zigbee-control-api,ce8d7938-5d7d-4eee-abab-294cf19315e7` | The HTTP API exposed under `/api`. |
| ApplicationInterface | `if:zigbee-control-ui,a07f2ad9-836f-4704-80f7-6546b8b41099` | Single consumer class — the Z2M Wrapper SPA (a separate producer). |

## Relations

- `app —Realization→ svc:zigbee-control-api` — product realizes its API.
- `if:zigbee-control-ui —Assignment→ svc:zigbee-control-api` — one interface per
  distinct consumer; this API has a single consumer (its own UI).
- `app —Association→ cap:iam` **boundBy `env:OIDC_ISSUER_URL`** — substitutable
  OIDC IdP, env carries the issuer URL (`.env.example:53`, `use_oidc: true`).
- `app —Association→ svc:ssegateway,59a7d043-bb0c-4e44-a8b8-3e943338f807`
  **boundBy `env:SSE_GATEWAY_URL`** — in-house SSE gateway (hand-provided UUID;
  not yet in the published dataset, so this cross-producer ref may dangle until
  the gateway's producer registers — reported, not failing).
- `app —Association→ cap:container-orchestration` — **no boundBy** (see below).

## Included / excluded decisions

**Included**

- The backend product, its exposed API service, and one UI interface.
- Three outbound consumption edges: OIDC (cap:iam), SSE gateway (svc:), and the
  Kubernetes API (cap:container-orchestration).

**Excluded**

- **Frontend / SPA** — separate producer per the fixed facts; this repo is
  backend-only. The frontend→backend consumption edge belongs to the frontend
  producer, not here, so it is not authored in this artifact.
- **`FRONTEND_VERSION_URL` ping** (`.env.example:71`,
  `app/services/frontend_version_service.py`) — a trivial backend→frontend
  version check. Per the modeling conventions, trivial backend→frontend calls
  are not modelled. OUT.
- **SSE-gateway callback webhook** the app exposes (connect/disconnect
  callbacks, `SSE_CALLBACK_SECRET`) — an implementation detail of consuming the
  gateway, modelled as the single consumption edge above, not as a second
  interface on this app. OUT as a separate surface.
- **`/metrics` (Prometheus), health, and drain endpoints**
  (`app/api/metrics.py`, `app/api/health.py`, `DRAIN_AUTH_KEY`) — operational
  surfaces; belong to the deployment (helm-charts) lens, not the app. OUT.
- **Testing-only endpoints** (`app/api/testing_*.py`) — active only in testing
  mode; no stable external identity in normal operation. OUT.
- **Database / S3** — `use_database: false`, `use_s3: false` in
  `.copier-answers.yml`; no persistence (AGENTS.md confirms "Persistence:
  None"). No `cap:relational-database` / `cap:object-storage` edge. The S3
  bucket name in copier answers is unused template scaffolding.
- **No capability realized.** The backend proxies config and restarts
  deployments; it does not itself do Zigbee/MQTT sensor/actuator orchestration,
  so it does **not** realize `cap:home-automation`. Most apps realize none.

## Kubernetes dependency — boundBy tension (decision logged)

`app/services/kubernetes_service.py` calls the Kubernetes API
(`patch_namespaced_deployment`, deployment watch) to perform rollout restarts —
the backend's core feature. It authenticates via the **in-cluster service
account** (`/var/run/secrets/kubernetes.io/serviceaccount`, falling back to a
local kubeconfig in dev). There is **no env var carrying the cluster API
endpoint**.

Modeled as `app —Association→ cap:container-orchestration` with **no
`boundBy`**. The manual states `cap:` targets normally *require* `boundBy`
(it's how a deployer resolves the provider), but it also blesses no-`boundBy`
consumption edges when the provider is located by something other than an env
var (explicitly "an in-cluster service account"). This edge therefore documents
a real dependency but will not auto-resolve to a concrete `Serving` edge.

## Cross-producer references

- `svc:ssegateway,59a7d043-bb0c-4e44-a8b8-3e943338f807` — UUID hand-provided in
  the seed brief (gateway not yet in the published dataset). May dangle until
  the gateway producer registers; the validator reports, does not fail.
- `cap:iam`, `cap:container-orchestration` — curated capability enum entries,
  referenced by bare name (resolved centrally by the collector).

## Validation

`./scripts/arch-validate.py docs/architecture/*.yaml` → **exit 0** (clean).

## Open questions for the operator

- **Kubernetes capability edge**: is `app —Association→ cap:container-orchestration`
  with no `boundBy` the intended modeling, or should this instead attach to the
  cluster's running platform instance (e.g. `ss:microk8s-prd,<uuid>`) once that
  UUID is resolvable from the published dataset? The in-cluster service account
  gives no env recipe, so it can't resolve to a `Serving` edge as-is.
- **AGENTS.md vs CLAUDE.md drift**: AGENTS.md/README describe an older
  shared-secret cookie auth, but the live config (`.env.example`,
  `app/config.py`, `use_oidc: true`) uses OIDC. Modeled the current state
  (OIDC). Worth reconciling the docs.
- **Snippet placement**: there is no `CLAUDE.md` in this repo; the federated-
  architecture snippet was appended to `AGENTS.md` (the repo's canonical agent
  doc). Confirm that's the intended home.
- **Interface granularity**: modeled a single UI consumer interface. If a
  distinct admin/IaC consumer class emerges, add a second `ApplicationInterface`.
