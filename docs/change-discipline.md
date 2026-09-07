# Change discipline

The rules every code change in this repo obeys, across all three components. This is the doc
`.aiworkflowrc` names as `design_philosophy`: it is handed to every `code-writer`, `code-reviewer`,
`plan-writer` and `plan-reviewer` the pipeline dispatches, and it is what a reviewer cites when
sending work back. It states the rules; the *design* they apply to lives in each subproject's
`docs/` — `backend/docs/product_brief.md` and `frontend/docs/product_brief.md` remain canonical on
scope and behaviour.

## Clean breaking changes

Greenfield, no external consumers. Nothing outside this repo imports its code, and the HTTP API is
consumed by exactly one client — the frontend in the same commit. So when an interface changes,
**fix the callers**: do not add a shim, an adapter, a compatibility route, or a response field that
keeps the old shape alive alongside the new one. The backend and the frontend ship together from
one Jenkins build, so there is no window in which an old client talks to a new server.

The one boundary that is not internal is the **tabs YAML** at `APP_TABS_CONFIG`. That file lives
outside the repo, on the operator's host, and is not deployed by this build. Changing its schema
breaks a file nobody here can migrate — so a change there is a compatible addition, or it comes with
an explicit note in the close-out that the operator must edit their config.

## No tombstones

Delete replaced code completely. No "moved to X" comments, no stub functions that forward, no
deprecated aliases, no commented-out blocks, no dead re-exports, no unused settings left in
`app/config.py` because something used to read them. The same applies to prose: when a convention is
superseded, **rewrite the doc** rather than appending a note that the old rule no longer holds. Git
history is the record of what things used to be; the working tree is only ever a statement of what
is true now.

`vulture` runs in `kc project lint` over `backend/app/` precisely to catch the code half of this.
When it flags something genuinely reachable, the whitelist entry goes in
`backend/vulture_whitelist.py` with the reason — not a `# noqa` at the site.

## No defensive coding, no "just in case" infrastructure

No `try`/`except` that swallows an error, no drop-the-bad-input-and-keep-going path, no null-guard
for a condition Pydantic or the framework already prevents, no silent fallback for configuration the
app requires. Prefer obvious-now failure over silent-corruption-later: the backend refusing to start
without `APP_TABS_CONFIG` is the right behaviour, and widening that fallback so it quietly serves the
test tabs in production would be the wrong one.

**Boundary validation is the exception, and it is the point.** The tabs YAML, the HTTP request
bodies, and the Kubernetes API's answers all cross into the system from outside — validate those.
Trust what the system already established: a tab index that reached a service layer has already been
range-checked at the API edge, and re-checking it there is noise.

Per-component readings of the same rule:

- **`backend/`** — validate the tabs file and request bodies with Pydantic/Spectree at the edge, and
  let Kubernetes and configuration errors propagate to the API or the SSE stream with useful
  context. The restart flow is *optimistic*, not forgiving: a rollout that fails becomes an `error`
  status, never a silently-retried one.
- **`frontend/`** — the API's shape is guaranteed by the generated client and the backend's schema,
  so components do not defend against it. SSE reconnection is genuine resilience against a dropped
  connection, not a defensive fallback, and it stays.
- **`root/`** — `Procfile.dev`, `scripts/` and `tools/suite_runner/` are developer tooling; they
  fail loudly and early rather than degrading.

## Testability is critical

Every change ships with a test. A feature without one is incomplete, and "I verified it by hand" is
not a substitute — the point of the test is that it runs again next time.

| Component | Suite | Runs as |
|---|---|---|
| `backend` | pytest, under `backend/tests/` | `kc project test --project backend` |
| `frontend` | Playwright E2E, under `frontend/tests/` | `kc project test --project frontend` |
| `root` | none — honcho and the suite runner ship no suite | green by definition |

The Playwright suite boots a real backend and a real SSE gateway per worker
(`frontend/tests/support/process/servers.ts`), so a frontend change is proven against the actual
API, not a mock. Kubernetes is the one thing that is faked: pytest injects a fake `AppsV1Api` and
the E2E suite never clicks Restart. A change that genuinely cannot be covered by either suite is a
change whose testability problem is the first thing to solve — say so and fix the seam, rather than
shipping it uncovered.

## Never hand-edit generated artifacts

The frontend's OpenAPI client is generated from the backend's own spec:

- `frontend/openapi-cache/openapi.json` is **committed** and is the build's input. It is produced by
  booting the backend and fetching `/api/docs/openapi.json` — `scripts/regenerate-openapi.py
  --frontend` does the whole dance.
- `frontend/src/lib/api/generated/` and `routeTree.gen.ts` are build outputs, regenerated by
  `pnpm build` (`generate:api:build`, `generate:routes`). They are not committed.

So an API change is a backend change: edit the Pydantic schemas and the Spectree annotations, then
regenerate. Hand-editing either the cache or the generated client produces a client that disagrees
with the server and a build that silently overwrites the edit.

## This is a public repo

`github.com/pvginkel/ZigbeeControl` is world-readable. The spec repo it is planned from,
`pvginkel/ZigbeeControlSpecs`, is **private** — slices, plans and close-outs may name internal
things; this repo may not. No secrets, credentials, internal hostnames or IP addresses, and no
non-public names — in code, in tests, in fixtures, in `backend/test/tabs.yaml`, or in commit
messages. The homelab's Keycloak issuer, cluster namespaces and Zigbee2MQTT addresses belong in the
operator's `.env` and their own tabs YAML, never in the tree. Assume every line is read by someone
outside the homelab, because it can be.
