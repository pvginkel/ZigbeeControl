# ZigbeeControl

A web UI that wraps three existing services — two Zigbee2MQTT dashboards and a code-server instance
— in persistent iframe tabs, with a restart control for the Kubernetes-backed ones and live status
over SSE. Tabs come from a YAML file the operator supplies at `APP_TABS_CONFIG`; there is no
database and no persisted state. One Jenkins build ships both images and deploys them; the only
environment is production.

## Repo structure

Three components, as `kc project list` reports them:

- **`root`** — the honcho dev stack (`Procfile.dev`, `scripts/dev.py`), the suite runner behind
  `poetry run run-suite` that CI calls, and the Jenkinsfiles. Ships no suite.
- **`backend/`** — Flask, layered `api/` → `services/` → `schemas/` → `utils/`, with DI. Serves tab
  config, triggers rollout restarts, streams status. pytest under `backend/tests/`.
- **`frontend/`** — React 19 + TypeScript + Vite + TanStack, with an OpenAPI client generated from
  the backend's spec. Playwright E2E under `frontend/tests/`, which boots a real backend and SSE
  gateway per worker.

Slices, plans and run state live in **`../ZigbeeControlSpecs`** — a separate, private git repo,
shared between environments. Commit there early and often, and separately from this repo; parallel
sessions work in the same tree, so stage by name.

## Running it

Everything needing a toolchain runs in the `modern-app` sidecar, via `cexec`; the dev container has
neither poetry nor pnpm. Run every `kc project` verb from the repo root — the CLI is cwd-bound.

```bash
kc project setup                 # poetry + pnpm install, Playwright chromium, seeds both .env files
kc project build                 # frontend build (the only component that builds)
kc project test                  # backend pytest + frontend Playwright
kc project lint                  # backend ruff + mypy + vulture, frontend eslint + tsc + knip
scripts/dev.py                   # the dev stack: frontend :3200, backend :3201, SSE gateway :3202
```

`backend/.env` and `frontend/.env` are git-ignored and seeded by `kc project setup`; a fresh clone
has neither, and the backend refuses to start without `APP_TABS_CONFIG` outside `FLASK_ENV=testing`.

## Design philosophy

The full rules are in [`docs/change-discipline.md`](docs/change-discipline.md), and every dev agent
is handed it. In short: break cleanly and fix the callers, since the backend and frontend ship
together and nothing outside the repo consumes either; delete replaced code rather than leaving
tombstones; validate what crosses into the system and trust what it already established, with no
defensive fallbacks; ship a test with every change; never hand-edit the generated OpenAPI client or
its committed cache — change the backend schema and regenerate with
`scripts/regenerate-openapi.py --frontend`. This repo is public and the spec repo is not: no
secrets, internal hostnames or non-public names in the tree.

## Where the rest is written down

- [`docs/slice-test-plan.md`](docs/slice-test-plan.md) — how a slice is verified, and what the push
  at the end of it deploys.
- [`docs/slice-doc-plan.md`](docs/slice-doc-plan.md) — which doc surfaces a shipped slice updates.
- `backend/AGENTS.md`, `frontend/AGENTS.md` — per-component orientation: API surface, expectations,
  local commands.
- `backend/docs/product_brief.md`, `frontend/docs/product_brief.md` — canonical on scope and
  behaviour.
- `.kubecoder/config.yaml` and `.kubecoder/project.yaml` — the environment and the curated
  automation, both commented in place.

## One thing that is knowingly red

- **`root` has no `lint:`** — `tools/` and `scripts/` have never been linted, here or in CI. One
  real finding among them: a missing `import io` at `scripts/dev.py:41` and `:45`.
