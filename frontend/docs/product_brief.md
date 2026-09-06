# Z2M Wrapper — Product Brief

*(Structured to match your brief style and aligned with your existing FE/BE architecture docs.)*   

## 1) What this app is for

A tiny “wrapper” UI that shows three tabs—**Zigbee2MQTT – 1**, **Zigbee2MQTT – 2**, and **Code Server**—each loading the target UI in a persistent IFRAME. The Z2M tabs include a restart button that triggers a Kubernetes rollout restart. The app streams simple status via SSE so the tab’s icon reflects **running / restarting / error** without page refresh, and the wrapper itself sits behind a single shared-password login backed by the API.

## 2) Who will use it

You, on a home network. Authenticated via a single shared password (cookie-backed).

## 3) Scope (exactly what it does)

* **Tabs (from YAML config):** icon (URL), text, iframe URL, optional Kubernetes restart info.
* **IFRAMEs:** one per tab; created **lazily on first open** and **never destroyed**—subsequent tab switches hide/show only.
* **Restart control (Z2M tabs):** click the restart icon → backend triggers **`kubectl rollout restart` equivalent** via Kubernetes Python client → SSE stream updates the icon state.
* **Status stream:** on app load, the frontend opens an **SSE connection per restartable tab** to receive `running | restarting | error`.
* **Password gate:** verify `GET /api/auth/check`, show a one-field password form that posts to `POST /api/auth/login`, then mount the tab shell once the cookie is issued.

## 4) Out of scope (won’t do now or later)

* Multi-user account management, RBAC dashboards, or token provisioning flows (shared secret only).
* Metrics/Prometheus, dashboards, analytics.
* Extending features beyond adding more tabs via config.
* NGINX/Kubernetes ingress setup (you’ll handle it).

## 5) Configuration (YAML) — minimal by design

Loaded from a file path provided by an environment variable (see §12).

```yaml
tabs:
  - text: "Zigbee2MQTT – 1"
    iconUrl: "https://example.local/assets/z2m.svg"
    iframeUrl: "https://z2m1.example.local/"
    k8s:
      namespace: "zigbee2mqtt"
      deployment: "zigbee2mqtt1"

  - text: "Zigbee2MQTT – 2"
    iconUrl: "https://example.local/assets/z2m.svg"
    iframeUrl: "https://z2m2.example.local/"
    k8s:
      namespace: "zigbee2mqtt"
      deployment: "zigbee2mqtt2"

  - text: "Code Server"
    iconUrl: "https://example.local/assets/code-server.svg"
    iframeUrl: "https://code.example.local/"
    # no k8s block → no restart button
```

**Notes**

* Presence of `k8s` makes a tab **restartable**; absence hides the restart button (per your instruction).
* No extra fields (timeouts, flags) in YAML—keep defaults in code, mirroring your script behaviour.

## 6) UX spec

* **Tabs across the top** with left-aligned icon, text label, and (if restartable) a right-aligned restart icon.
* **Active tab** is visually highlighted; on initial load, the **first tab opens** and its IFRAME is created.
* **Icons & states (restartable tabs):**

  * `running`: normal Z2M icon.
  * `restarting`: switch to a “refresh/restart” icon with a **CSS blink** (e.g., 0.8s cadence).
  * `error`: switch to a small error/badge icon (red), no blinking.
* **No toasts** or banners—icon-only state, as requested.
* **Accessibility:** `role="tablist"`, `role="tab"`, `aria-selected`, focus ring, keyboard navigation.

## 7) Key workflows

1. **Open app →** FE runs `GET /api/auth/check`; when unauthorized it blocks on the password prompt until `POST /api/auth/login` succeeds, then loads the config and makes the first tab visible (IFRAME created). For tabs with `k8s`, FE opens an SSE stream for live status.
2. **Switch tabs →** previously created IFRAMEs are **hidden, not unmounted**, and instantly shown again.
3. **Restart (Z2M tabs) →** click icon → FE sends `POST /api/restart/:tabIndex` → icon switches to blinking **restarting** immediately → SSE later flips to **running** or **error**.

## 8) Success criteria

* Tab switch shows existing IFRAME **<100 ms** (no reload).
* From restart click to **SSE “restarting”** event: **instant** (optimistically set by FE; then confirmed by BE).
* Successful rollout recognized and shown as **running** within the default rollout window (backend uses a **180s** cutoff, like your script).
* App runs unattended; if backend restarts, FE **auto-reconnects** SSE.

## 9) Non-functional

* **Simplicity:** no database, no queues; in-memory only.
* **Resilience:** SSE auto-retry with backoff; backend guards against duplicate restarts on the same deployment.
* **Security:** shared-secret password issuing an HttpOnly cookie; still assumes LAN deployment plus the framing considerations in §11.

## 10) Architecture (mirrors your existing patterns)

### Frontend (same stack & patterns)

* **React 19 + TypeScript + Vite**, TanStack Query for the restart mutation + very light cache, and the same project layout conventions you already use (routes/components/hooks split, config under `src/lib/config/`). 
* A tiny `useSseStatus(tab)` hook wraps `EventSource`.
* No routing beyond the single page; tabs are internal state (Zustand or simple reducer).

### Backend (same shape as your Flask service)

* **Flask** app via `create_app`, with layered modules: `api/` (Blueprints), `services/` (K8s orchestration), `schemas/` (Pydantic for request/response), `utils/` (SSE helper, config loader). Error mapping as in your pattern. 
* **Dependency injection** via the same container style; a `KubernetesService` encapsulates rollout and status watch; API layer is thin and validated. 
* **No DB**; config YAML is read at boot and on SIGHUP (optional—simple reload).

## 11) API design

* `GET /api/auth/check` → returns 200 when the auth cookie is valid; 403 otherwise so the FE shows the password screen.
* `POST /api/auth/login` → accepts `{password}` and issues the auth cookie (SameSite=None + Partitioned) on success; 403 on mismatch.
* `GET /api/config` → FE bootstrap (normalized config: tabs + restartable flags).
* `POST /api/restart/:idx` → triggers a **rollout restart** (patch `spec.template.metadata.annotations.kubectl.kubernetes.io/restartedAt` to current timestamp). Returns `{ok:true}` immediately.
* `GET /api/status/:idx/stream` (SSE) → emits one-line JSON payloads with `status`:

  * `{"status":"running"}` (initial + steady state),
  * `{"status":"restarting"}`,
  * `{"status":"error","message":"…optional…"}`
* **SSE semantics:** `event: status` lines, UTF-8, `Cache-Control: no-transform`, retry header set (e.g., `retry: 3000`).

**Rollout detection (server-side)**

* On `restart`, backend:

  * Patches the Deployment to trigger a new ReplicaSet (Python K8s client).
  * Waits for “progressing” then “available” conditions on the Deployment **or** observes all Pods for that Deployment become `Ready` (whichever is simpler to implement cleanly).
  * Emits `restarting` → `running` (or `error` on timeout ~180s, mirroring your script).

## 12) Configuration & deployment

* **Env var:** `APP_TABS_CONFIG` → absolute path to the YAML shown in §5.
* **Containerization:** single Docker image for the wrapper (FE built into static assets served by the Flask app or sidecar NGINX—either is fine).
* **K8s:** one Deployment + Service for the wrapper; you’ll wire Ingress/NGINX.

## 13) IFRAME / CSP headers (what to tweak in NGINX)

You’ll ensure each embedded app allows being framed by the wrapper’s origin. Practical tips:

* **Prefer CSP over X-Frame-Options:**

  * Remove backend `X-Frame-Options` if present: `proxy_hide_header X-Frame-Options;`
  * Add a **frame-ancestors** policy on the proxied apps:
    `add_header Content-Security-Policy "frame-ancestors 'self' https://wrapper.your.lan" always;`
* If you terminate TLS at NGINX for subpaths like `/z2m1/`, normalize cookies (if any) to the shared parent domain with `proxy_cookie_domain`.
* **No cross-window messaging** is required; different origins are fine since we don’t need cookies or postMessage.
* If an app hard-codes a base path, you may need a subpath proxy (e.g., `/z2m1/ → http://z2m1:8080`) and, if necessary, rewrite asset URLs.

## 14) Visual details (so it’s “sleek & simple”)

* Minimal top bar with tabs as rounded pills; active pill slightly elevated.
* Restart icon on Z2M tabs:

  * **Normal:** outlined restart glyph.
  * **Blinking:** same glyph with CSS `@keyframes` opacity toggle (~0.8s).
  * **Error:** small circle-with-cross badge overlay on the tab icon.
* Hide/show IFRAMEs via CSS (`display:none`), never remove from DOM.

## 15) Risks & mitigations

* **Iframe blocking:** some services send restrictive `X-Frame-Options`/CSP → mitigate with NGINX overrides (see §13).
* **SSE drops:** home Wi-Fi hiccups → FE auto-reconnect with exponential backoff; backend is idempotent on restart.
* **Rollout ambiguity:** detecting “ready” on Deployments can be racy if probes are slow—use Deployment conditions and a sensible timeout (180s).
* **Cookie scoping:** auth cookie must stay Partitioned + SameSite=None so the wrapper loads inside the Home Assistant iframe without third-party cookie blocks.

---

## Mapping to your existing patterns (for reviewers)

* FE stacks and layering mirror your **React 19 + TS + Vite + TanStack** front-end conventions. 
* BE follows your **Flask / DI / Blueprints / Pydantic + Spectree** approach, just without persistence or metrics. 
* Brief format and crisp scoping match your prior product brief style. 

If you want, I can next turn this into a tiny OpenAPI + FE skeleton (routes, `useSseStatus`, restart mutation, and the config loader).
