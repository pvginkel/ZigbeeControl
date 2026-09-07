# Slice testing strategy

How a slice is proven once its phases are merged. This is the doc `.aiworkflowrc` names as
`test_phase.strategy`: the run loop's test phase is "read this and execute it", and nothing else
names it. Read it top to bottom and do what it says.

## What this phase proves, and what it does not

**Verification here is local.** This repo has exactly one deployment — production — and no dev
instance to roll. So the test phase does not deploy anything and does not verify against a deployed
instance. It runs the suites tree-wide and boots the dev stack in this environment, from the merged
working tree.

**The push at the end deploys to production.** `Jenkinsfile` builds both images with kaniko
(`zigbee-control`, `zigbee-control-ui`) and its final stage is `cicd.helmDeploy()`. There is no
DTAP: the only environment this repo has is the live one. That is the repo's standing behaviour, not
something this phase controls, and it is the whole reason for the ordering below — **everything is
verified before the push, because after the push it is live.**

There is no `devlock`: with no dev instance, nothing contends.

## 0. Preconditions

The driver has ff-merged every code phase into the base branch. Confirm the tree is clean
(`git status --short`) before starting — a dirty tree here means an earlier phase left something
behind, and that is a finding, not something to tidy away. Run every `kc project` verb from the
repo root; the CLI is cwd-bound.

## 1. The suites, tree-wide

```bash
kc project build      # frontend only: generate:api + tsr generate + pnpm check + vite build + verify
kc project test       # backend pytest, frontend Playwright E2E
kc project lint       # backend ruff + vulture, frontend eslint + tsc + knip
```

All three must be green. `kc project build` is also what preflight demands, so a red build here
means the slice never should have reached this phase.

**Two gates are knowingly not wired, and neither is a regression from your slice:**

- **`backend` mypy is red** — 36 pre-existing errors across 11 files, tracked as Trello card #864
  ("ZigbeeControl: backend mypy is red"). It is commented out of `lint:` in
  `.kubecoder/project.yaml` rather than left failing, so `kc project lint` is green while
  `cexec modern-app poetry run check` (the backend's own all-checks command) is not. If your slice
  touched `backend/`, run `cexec modern-app sh -c 'cd backend && poetry run mypy .'` and check the
  count has not *grown*; report it if it has. Delete this bullet when #864 is closed.
- **`root` declares no `lint:`** — `tools/` and `scripts/` have never been linted, here or in CI.
  `ruff check --isolated` there reports 14 findings, including a real `F821 Undefined name 'io'` at
  `scripts/dev.py:41` and `:45`. Open with the operator; no card.

## 2. The live check

Boot the dev stack the way this repo does — honcho over `Procfile.dev`, inside the `modern-app`
sidecar — and probe the three ports `.kubecoder/config.yaml` publishes: frontend 3200, backend 3201,
SSE gateway 3202. Do this whenever the slice touched `backend/`, `frontend/`, `Procfile.dev` or
`scripts/`; a docs-only slice can skip to step 3 and say so.

Run honcho directly rather than through `scripts/dev.py`: the wrapper spawns honcho under a pty and
a PID namespace, which is right for a human at a terminal and unkillable from a script.

```bash
mkdir -p logs
nohup cexec modern-app poetry run honcho -f Procfile.dev start > logs/dev-stack.log 2>&1 &
```

All three ports answer in about two seconds. Then:

```bash
for u in http://localhost:3200/ http://localhost:3200/api/config \
         http://localhost:3200/version.json \
         http://localhost:3201/health/readyz http://localhost:3202/readyz; do
  printf '%-40s ' "$u"; curl -sS -o /dev/null -w '%{http_code}\n' --max-time 10 "$u"
done
curl -sk -o /dev/null -w '%{http_code}\n' "https://frontend.$KUBECODER_ENVIRONMENT_ID.home/"
```

Every one answers `200`. `/api/config` is served by Vite's proxy from the backend, so a `200` there
proves both processes and the proxy at once; the published `sslOffload` address proves the port is
actually reachable from outside the pod. Add whatever else the slice's own criteria need.

### Stopping it

**Send `SIGINT` to honcho itself, by pid.** Killing the `cexec` client instead takes honcho down
without its shutdown cascade and leaves Vite, Flask and the gateway holding all three ports — that
was observed here, and cleaning it up is manual.

```bash
HONCHO=$(cexec modern-app ps -eo pid,ppid,args --no-headers \
  | awk '$3 ~ /^\/.*python/ && /bin\/honcho -f Procfile.dev/ {print $1}' | sort -n | head -1)
kill -INT "$HONCHO"
```

Two things about that selector. The pod shares one PID namespace, so `ps` in the sidecar also lists
this container's processes — including **your own command line**, which is why `pgrep -f honcho`
self-matches and returns a pid that is not honcho. The `$3 ~ /^\/` test keeps only processes whose
argv[0] is an absolute path, which excludes both your shell and the `cexec` client. `sort -n | head
-1` then picks honcho's parent over its three per-line children.

honcho exits in about a second, logging `sending SIGTERM` per process to `logs/dev-stack.log`.
Confirm the three ports are free and no stragglers remain
(`cexec modern-app ps -eo pid,args --no-headers`), then confirm `git status --short` is clean —
`logs/` is git-ignored, but the tree must go back to how it started.

## 3. Check off `verification.json`

Mark each acceptance criterion with the evidence that settled it — the command run and what it
returned, or the surface loaded and what was seen. A criterion nothing in steps 1–2 exercised is not
"passed by inspection"; it is either an untested criterion (a finding) or one whose check belongs in
this doc and is missing from it.

The one thing this environment cannot exercise is a **real** Kubernetes rollout restart: pytest
injects a fake `AppsV1Api`, the E2E suite never clicks Restart, and the mounted kubeconfig carries no
write access to the `zigbee2mqtt` namespace. A slice whose criteria depend on a live restart reports
those as *not verified*, and says so.

## 4. Push, then follow the build

Pushing is this phase's job — the driver ff-merges locally and never pushes a code phase, then
checks before the doc phase that every repo in `state.json`'s `bases` reached `origin`. Push each
one, honouring any repo named in `plan.md`'s `## Push holds`. **This is the production deploy**;
do not reach it with anything from steps 1–3 unresolved.

Record the build number *before* pushing, so you can tell the new build from the old one:

```
mcp__jenkins__getJob  jobFullName="ZigbeeControl/ZigbeeControl"
                      tree="lastBuild[number,result,building]"
```

Then push, and poll the same call until `lastBuild.number` has incremented, then
`mcp__jenkins__getBuild` on that number until `building` is `false` and read `result`. A build takes
about five and a half minutes. Without the Jenkins MCP tools in the session, the same two reads are
`curl -s 'https://jenkins.webathome.org/job/ZigbeeControl/job/ZigbeeControl/api/json?tree=lastBuild[number,result,building]'`
and `.../job/ZigbeeControl/job/ZigbeeControl/<n>/api/json?tree=number,result,building`.

This is a **did-I-break-CI check, not a verification gate** — the slice was already proven in steps
1–2. What it catches is the class of failure only CI can see: both Dockerfiles building end to end,
and the Helm deploy landing. Jenkins runs the same two suites this phase already ran, through
`poetry run run-suite`, so a suite failure there means something environment-shaped, not a new bug.
A red build is a blocking finding even though every local check passed — and because the deploy
stage is last, a red build usually means production is still on the previous image.

## Findings

Blocking findings come back as appended phases. Sub-bar findings go in the close-out report for the
operator to triage. A live check that cannot be run at all is reported as *not verified*, never as
passed: the phase is allowed to end with a criterion unproven and said so, and is not allowed to end
with one assumed.

## The operator gate

The operator's gate is the close-out report, after the run. Production has by then already taken the
change, which is what makes steps 1–2 the real gate and why they precede the push.
