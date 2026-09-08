# Slice documentation plan

Which documentation surfaces a shipped slice brings up to date, and the rules for each. This is the
doc `.aiworkflowrc` names as `doc_phase.plan`: the run loop's doc phase is "read this and execute
it", working from the whole slice's merged diff.

Work the diff, not a checklist. Each surface below is owed an update only when the slice's changes
actually reached it.

## The surfaces

### 1. The root — `CLAUDE.md` and `docs/`

`CLAUDE.md` is the monorepo's orientation page: what the project is, what the three components are,
which gates run, where the rules live. It is loaded by every dev session, every turn, so it stays at
about one screen and states each fact once. A slice rarely touches it; when a new standing rule
genuinely belongs there, something else moves out to a `docs/` topic doc rather than the file
growing. Nothing the pipeline reads by machine goes in it — that is `.aiworkflowrc`.

The root `docs/` holds what is true across components: `change-discipline.md`,
`slice-test-plan.md`, `slice-doc-plan.md`. A slice that changed how the repo is verified, how it is
documented, or what the change rules are, changed one of these three. A slice that introduced a
cross-component design worth writing down puts it here as a new topic doc, and links it from
`CLAUDE.md`.

### 2. The subproject `docs/`

| Scope | Owns |
|---|---|
| `backend/docs/` | the Flask app: `product_brief.md` is canonical on scope, workflows and the API surface |
| `frontend/docs/` | the React SPA: `product_brief.md` likewise for the wrapper UI |

Design belongs to the subproject it describes. Design that **spans** the two — the SSE contract, the
restart flow end to end, the shape of the generated client — is a root `docs/` topic, whichever
component's code moved.

`docs/features/*/plan.md` under each subproject are historical plans from the pre-plugin workflow.
They are a record of what was built, not a live surface: **do not update them**. Slices are recorded
in `../ZigbeeControlSpecs`, which is a separate git repo — commit there separately.


### 3. The reader-facing files in each subproject

- **`backend/README.md`** — how to run the service and what its HTTP API is. Owed an update when
  either changed.
- **`frontend/README.md`** — still the stock Vite template. If a slice gives it a reason to become a
  real README, write one; do not rewrite it just because it is generic.
- **`backend/CLAUDE.md` / `frontend/CLAUDE.md`** — the per-subproject orientation an agent reads
  before touching that component: the API surface, the expectations, the gates. Owed an update when
  any of those moved. Same one-screen discipline as `CLAUDE.md`.

### 4. The architecture artifact, when the deployed shape moved

Each subproject carries `docs/architecture/architecture.yaml` for the federated
Architecture-as-Code model, and the `AaC/ZigbeeControl` Jenkins job validates them. The rule for
when to update them, and which agent does it, is already stated in each subproject's `CLAUDE.md` —
follow it there rather than restating it. A slice that added or removed a service, a deployment or
an external identity is the case that matters.

## What "up to date" means here

**State the design as it is**, as implemented, not as the slice authored it. Where the
implementation diverged from the plan, the doc describes what shipped. No changelog entries, no "as
of slice NNN", no tombstones for superseded conventions — rewrite the doc instead, per
[`change-discipline.md`](change-discipline.md).

**Ground every claim in the shipped source.** A doc sentence that cannot be checked against the
merged tree does not go in. This repo has doc rot already (the backend README above); do not add to
it by describing intent.

## Gates

Documentation changes do not compile, but they do live beside code:

```bash
kc project build       # unchanged and green — the doc phase must not have moved code
```

Check relative links resolve, including the ones that leave the repo for `../ZigbeeControlSpecs/`.
Then commit — this repo and the spec repo separately, since they are separate git repos.

## When there is little to do

A slice that changed no design, no convention, and no reader-facing surface owes nothing here, and
saying so plainly is the correct outcome. Do not invent doc work to fill the phase; a README section
nobody needed is worse than no section.
