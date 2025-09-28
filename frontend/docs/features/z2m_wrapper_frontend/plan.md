Brief description

Implement the single-page React 19 + TypeScript + Vite frontend that renders the three-tab Zigbee2MQTT wrapper UI from `GET /api/config`, keeps each tab’s iframe alive after the first open, and drives the restart and status icon flow using TanStack Query plus one SSE stream per restartable tab, exactly as outlined in `docs/product_brief.md`.

API endpoints

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

Relevant files and functions

- `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`: scaffold Vite + React 19 + TypeScript project and declare TanStack Query, Zustand (or alternative lightweight state) dependencies, and build scripts.
- `src/main.tsx`: create the React root, wrap `App` with `QueryClientProvider`, and inject the global stylesheet.
- `src/styles/index.css` (or `src/index.css`): define base styles for body, tab bar, pills, icon states (`running`, `restarting` blink via `@keyframes`, `error` badge overlay), and iframe layout consistent with §6 and §14 of the brief.
- `src/lib/api.ts`: expose typed helpers `fetchConfig()`, `restartTab(tabIndex: number)`, and `openStatusStream(tabIndex: number)` that call `GET /api/config`, `POST /api/restart/:idx`, and `GET /api/status/:idx/stream` without OpenAPI schema reliance.
- `src/lib/types.ts`: declare `TabConfig`, `K8sInfo`, and `TabStatus = 'running' | 'restarting' | 'error'` interfaces matching the YAML structure in §5 and the SSE payloads in §11.
- `src/state/useTabsStore.ts` (or `useTabs.ts`): manage active tab index, lazily mark iframes as mounted, and expose actions for keyboard navigation (Left/Right) to satisfy the accessibility requirement.
- `src/hooks/useConfigQuery.ts`: wrap TanStack Query `useQuery` to fetch and normalize the tab list on load.
- `src/hooks/useRestartMutation.ts`: TanStack `useMutation` calling `restartTab` with optimistic `setStatus(tabIndex, 'restarting')` update and rollback on failure.
- `src/hooks/useSseStatus.ts`: manage the single EventSource per restartable tab, reconnect with incremental backoff when closed, parse `event: status` JSON payloads, and push updates into shared status state.
- `src/components/AppShell.tsx`: high-level layout that renders the tablist, restart icon, and iframe container region.
- `src/components/TabButton.tsx`: accessible tab trigger (`role="tab"`, `aria-selected`, `tabIndex`) displaying the icon, label, and per-state overlays.
- `src/components/RestartButton.tsx`: icon-only button that triggers the restart mutation and stops propagation when clicked.
- `src/components/TabContent.tsx`: render the iframe element for each tab, create it on first render via `useRef`, and toggle `hidden` / `display` without unmounting.
- `src/utils/accessibility.ts`: optional utilities for handling focus movement and keyboard behavior while keeping code tidy.
- `public/manifest.json`, icons: include placeholder icons if required by Vite build (can be minimal per product brief’s scope).

Algorithms and flow details

1. **Configuration bootstrap**
   - On `App` mount, call `useConfigQuery()` → `fetchConfig()` → `GET /api/config` to obtain the YAML-derived tab definitions (`text`, `iconUrl`, `iframeUrl`, optional `k8s`).
   - Normalize response into `tabs: TabConfig[]` with explicit `isRestartable = Boolean(k8s)` since the YAML is source of truth.
   - Set initial active tab to index `0`, mark it as mounted, and immediately initiate SSE subscriptions for **all** restartable tabs so their icons stay in sync even before a user visits them.
2. **Tab state and accessibility**
   - Store `activeIndex`, `mounted` set, and `statuses` in a shared store/hook so buttons and content stay in sync.
   - Keyboard handler on the tablist listens for `ArrowLeft`, `ArrowRight`, `Home`, `End`, and focuses the next/prev tab per WAI-ARIA Authoring Practices.
   - Clicking a tab sets `activeIndex`. If the tab has not been mounted, flag it so the iframe is created during the next render. Switching tabs only toggles `hidden`/`aria-hidden` while preserving DOM nodes.
3. **Iframe lifecycle**
   - Render a single `<iframe>` element per tab stored in an array; initial render returns `null` until the tab is marked mounted.
   - Once mounted, keep the iframe element in the DOM regardless of active tab; use CSS classes to hide inactive frames (`display:none`) to meet the <100 ms activation requirement.
4. **Restart mutation**
   - `RestartButton` triggers `useRestartMutation` with the tab index. Before the network call resolves, optimistically set status to `'restarting'` for that tab.
   - Mutation calls `POST /api/restart/:idx`; on success, rely on SSE to eventually send `'running'` or `'error'`. On HTTP failure, revert the optimistic status to the previous value and optionally surface a console warning (no toast per brief).
   - Disable the restart button while status is already `'restarting'` to avoid duplicate clicks; backend also guards duplicates but UI reflects that rule.
5. **SSE status handling**
   - `useSseStatus(tabIndex, enabled)` creates an `EventSource` pointed at `/api/status/:idx/stream` as soon as a tab is known to be restartable, independent of whether the tab has been opened.
   - Listen for `message` events with `event.type === 'status'`; parse the JSON line (`{"status":"running"}` etc.) and update the shared `statuses` store.
   - Handle `error` events by closing the EventSource and scheduling a reconnect with exponential backoff (e.g., 3s, 6s, 12s) capped at a sensible limit. Preserve the last known status while disconnected; when reconnect succeeds, process the initial event the backend sends so background tabs stay current without user interaction.
   - Ensure cleanup via `useEffect` return function when the component using the hook unmounts (unlikely, but keeps the stream isolated per tab).
6. **Status-driven UI**
   - Tab buttons read `statuses[tabIndex]` and swap icons: default `iconUrl` for `'running'`, restart glyph (with blinking CSS class) for `'restarting'`, and overlay error badge for `'error'`.
   - Maintain a `data-status` attribute for each tab to simplify CSS selectors for blink and error styling.
7. **Global error boundaries and loading**
   - Show a minimal loading spinner while config is fetched. For fetch errors, render an inline retry button that refires the query (no toasts, minimal UI).
   - Use React Error Boundary (optional) to catch runtime iframe issues, but avoid over-engineering beyond the brief.

Phases

- **Phase 1 – Project scaffolding & config fetch:** initialize Vite React 19 app, global styles, TanStack Query provider, `useConfigQuery`, and render tabs list/toggle without restart or SSE wiring.
- **Phase 2 – Restart + status plumbing:** implement `useRestartMutation`, `useSseStatus`, shared status store, and icon state transitions for restartable tabs.
- **Phase 3 – Polish & accessibility:** finalize keyboard navigation, CSS blink/error treatments, disable restart button when appropriate, and tighten cleanup/backoff logic.
