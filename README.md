# ZigbeeControl

A control panel that wraps two Zigbee2MQTT instances and a code-server in persistent iframe tabs, so
the whole Zigbee setup is reachable from one page. Tabs backed by a Kubernetes deployment get a
restart button that triggers a rollout restart, and the panel streams each tab's live status —
`running`, `restarting`, `error` — over Server-Sent Events, so the tab icons stay in sync without a
refresh. The tabs come from a YAML file supplied at `APP_TABS_CONFIG`; there is no database and no
persisted state.

## Layout

- **`backend/`** — Flask. Serves the tab configuration, triggers the rollout restarts and publishes
  the status events. OIDC authentication, off by default in development.
- **`frontend/`** — React 19 + TypeScript + Vite, with an API client generated from the backend's
  OpenAPI spec, covered end to end by Playwright.
- The dev stack also runs an **SSE gateway**, which fans the backend's status events out to connected
  browsers. It ships as a frontend devDependency, so there is nothing extra to check out.

## Building and running

The repo builds and runs inside a KubeCoder environment, which supplies the Python and Node
toolchains. From the repository root:

```bash
kc project setup    # install dependencies and seed the .env files
kc project build    # build the frontend
kc project test     # backend pytest, frontend Playwright
kc project lint     # ruff, mypy and vulture; eslint, tsc and knip
scripts/dev.py      # the dev stack: frontend :3200, backend :3201, SSE gateway :3202
```

## More

- [`backend/README.md`](backend/README.md) — running the service alone, and its HTTP API.
- [`frontend/README.md`](frontend/README.md) — the Vite toolchain notes the app was scaffolded with.
- [`CLAUDE.md`](CLAUDE.md) — orientation for a development session.
