## Stage 11 — Report summary + `pr-summary.md` § `## How to verify`

**Purpose.** Two artifacts. First: in-terminal summary so the developer knows what happened. Second: `units/<repo>/pr-summary.md § ## How to verify` — a developer-facing setup + run guide for verifying locally (NOT the PR summary — that's `/dev:commit`'s job). The runbook lives at `units/<repo>/pr-summary.md § ## How to verify` (v2.3.11) — implementation.md is plan-only and does not carry the verify runbook.

**Runs after Stage 10.** Final stage. status `inProgress` · phase `built` (build phase done; local state stays inProgress until `/dev:commit` flips to devReview)

**On completion:** developer has a clear, actionable summary of the build + the runbook they need to verify the feature manually.

---

### 11a. Preconditions

- `units/<repo>/status.md § ## Run history` Stages 1-10 all `status: DONE`
- Branch has commits (from Stage 10's context update + earlier code commits)

---

### 11b. Compose the in-terminal summary

Print to stdout with clear structure:

```
✓ /dev:build FEAT-SUP-001-1 complete

Task:              Subtask-7 (backend)  ·  Feature-4 Supplier Onboarding
MC parent:         https://mission-control.techjays.com/task/6a94fe0ebc48d4e7d1cab15b
MC sub-task:       https://mission-control.techjays.com/task/6b72a1c48d4e7d1cab2c7

Branch:            feature/FEAT-SUP-001-supplier-onboarding-backend  (in acme-backend)
Base:              develop
Commits:           8  (7 code + 1 context-update)
Files changed:     18  (+624 / -12)

Implementation:
  · Detected stack:    TypeScript + NestJS + Prisma + Jest + Playwright + pnpm
  · Steps completed:   12/12
  · DECs logged:       23

Tests:
  · Unit written:      14
  · Integration:       11
  · E2E:               3 (skeleton + happy path)
  · Coverage:          72.4% lines (≥60% required)
  · All Required gates: 7/7 pass

Security review (build-time, Critical-blocking only):
  · Critical:  0
  · High:      2 (deferred to /dev:commit's stricter gate)
  · Medium:    1
  · Low:       1
  See: units/<repo>/findings.md § ## Security — build

Acceptance map: 12/12 rows resolved
  · Pass locally:    12  (Unit + Integration + Component + Concurrency tiers per qa/quality-gates.md)
  · Cross-layer E2E: owned by <sibling sub-task>  (referenced in §6 Touch points; runs after all sub-tasks land)
  · Fail:            0

Code-context:
  · 3 units updated:
      - EP-SUP-01 create @ src/routes/supplier.ts:42
      - EP-SUP-02 duplicate-check @ src/routes/supplier.ts:78
      - ENT-SUP-01 supplier @ src/db/migrations/20260831142400_add_supplier_table.ts
  · Indexes: backend-index.md, database-index.md updated
  · Commit: a1b2c3d

Status:        inProgress   (will transition to devReview on /dev:commit)
MC parent:     https://mission-control.techjays.com/task/6a94fe0ebc48d4e7d1cab15b
MC sub-task:   https://mission-control.techjays.com/task/6b72a1c48d4e7d1cab2c7

Next steps:
  1. Review units/<repo>/pr-summary.md § ## How to verify — env vars + how to run manually
  2. Verify the feature locally (see runbook)
  3. When ready, run:  /dev:commit FEAT-SUP-001-1

Navigation sources (v2.3.17 — task-mcp is the URL source of truth):
  · MC parent URL   ← task-mcp `get_task_by_id_or_number(solution_id, feature.md `jetrix_task_object_id`)` response `.view_url`
  · MC sub-task URL ← task-mcp `get_task_by_id_or_number(solution_id, units/<repo>/status.md `jetrix_subtask_object_id`)` response `.view_url`
    /dev:build did NOT push (that was /dev:plan Stage 4), so read the URLs via task-mcp lookup, not by constructing locally.
    Never build the URL from `.jetrix/project.json` `mission_control_ui_url` directly — task-mcp's env var is the source of truth and may differ.

Files written by this run:
  - units/<repo>/status.md § ## Run history
  - units/<repo>/status.md § ## Run history
  - units/<repo>/status.md § ## Acceptance
  - units/<repo>/findings.md § ## Security — build
  - units/<repo>/pr-summary.md § ## How to verify
  - dev/decisions.md
```

---

### 11c. Compose `units/<repo>/pr-summary.md § ## How to verify` — developer-facing setup guide

**Not** the PR summary. `units/<repo>/pr-summary.md § ## How to verify` is what the developer reads at their desk to verify the feature works on their machine. Persisted as a discrete file so implementation.md stays plan-only.

Frontmatter:

```yaml
---
doc_type: `pr-summary.md` § `## How to verify`
schema_version: 1.0
produced_by: dev
feature_id: FEAT-<AREA>-NN
subtask_number: <N>            # OMIT for parent-alone
subtask_repo: <repo-slug>
generated_at: <ISO>
build_id: <build-timestamp>
---
```

Body — 9 sections in order:

```markdown
# Local runbook — <feature title>

## 1. What this feature does

<2-line business summary from parent's `feature.md` Objective. No implementation detail. No framework names. Business language only.>

Example: "Enable operations coordinators to onboard new suppliers, with automatic
duplicate detection against the compliance service. This backend sub-task delivers
the supplier creation + validation endpoint; the frontend sub-task provides the form."

## 2. Prerequisites

<Tools + versions the developer needs before running. From detected stack + `qa/quality-gates.md` implicit deps.>

- Node.js ≥ 20 (detected: package.json engines.node = ">=20")
- pnpm ≥ 8 (detected: pnpm-lock.yaml present)
- Postgres running locally (dep: prisma with PostgreSQL provider)
- Playwright browsers installed (`pnpm exec playwright install --with-deps chromium`)

## 3. Environment / config setup (v2.3.23 — from real startup, not grep-guess)

**Env var detection MUST use both signals** — source grep AND Stage 7's `external_services_started.env_vars_verified` list:

1. **Grep the source** for `process.env.<NAME>`, `os.environ["<NAME>"]`, `os.getenv("<NAME>")`, `System.getenv("<NAME>")`, `settings.<NAME>` accessors, and the repo's config module lookups.
2. **Cross-reference with Stage 7's actual startup** — the `external_services_started[].env_vars_verified` list contains every env var the backend REQUIRED to reach `status: healthy` at Stage 7 time. If Stage 7 halted with `blocker: required-env-vars-missing`, THOSE are the ones the developer MUST provide.
3. **Cross-reference with the repo's `.env.example`** — every var listed there is a documented required var for the service.
4. Union all three sources → deduplicate → categorize per var:

   | Category | Detection | Marker in `pr-summary.md` § `## How to verify` |
   |---|---|---|
   | Required, from repo's `.env.example` with placeholder | Present in `.env.example` with `<placeholder>` value | `[SET REQUIRED — see <where to get>]` |
   | Required, verified at Stage 7 startup | Present in `external_services_started[].env_vars_verified` | `[SET REQUIRED — service won't start without it]` |
   | Optional with sensible default | Present in source with a default in the code | `[OPTIONAL — default: <value>]` |
   | Auth / credential — MUST NOT commit | Matches pattern `*SECRET*`, `*TOKEN*`, `*KEY*`, `*PASSWORD*`, `*CREDENTIAL*`, `FIREBASE_SERVICE_ACCOUNT`, `GOOGLE_APPLICATION_CREDENTIALS` | `[SET REQUIRED — credential; do NOT commit; from <where to get>]` |
   | Endpoint / URL for external service | Ends with `_URL`, `_ENDPOINT`, `_HOST` | `[OK — dev value from technology-stack.md]` if declared there, else `[SET REQUIRED — the actual URL for your env]` |

**"Where to get" hints per common var (extend as new patterns are encountered):**

- `FIREBASE_SERVICE_ACCOUNT`: Firebase Console → Project Settings → Service Accounts → Generate new private key → paste JSON body (single-line, escape as needed) OR set `GOOGLE_APPLICATION_CREDENTIALS=<path to downloaded file>`
- `DATABASE_URL`: your local database — install Postgres/MongoDB/etc. and create a database
- `<SERVICE>_TOKEN` where `<SERVICE>` is an internal one: team's shared dev secrets vault / Bitwarden / 1Password
- `JWT_SECRET`, `SESSION_SECRET`: generate with `openssl rand -hex 32`
- `SMTP_*`: dev-mail service (Mailtrap / MailHog) OR real credentials from the marketing/ops owner

Copy `.env.example` to `.env` (or `.env.local`) and set:

```
DATABASE_URL=<paste your local DB URL>                         [SET REQUIRED — install Postgres locally]
FIREBASE_SERVICE_ACCOUNT=<paste single-line JSON>              [SET REQUIRED — credential; do NOT commit; from Firebase Console]
COMPLIANCE_SERVICE_URL=https://compliance.acme.internal/v1     [OK — dev value from shared-context/technology-stack.md]
COMPLIANCE_TOKEN=<paste team dev token>                        [SET REQUIRED — credential; do NOT commit; from Vault / Bitwarden]
```

**If the developer runs the feature and something 401s or 500s, the FIRST thing to check is this section** — a missing env var is the single most common cause of "tests passed but real endpoint failed" bugs.

## 4. Stored data changes

<From `implementation.md §4 Stored data changes` + `§2 Impacted components` Stored data row + `§1 Build sequence` migration steps>

Run migrations:

```
pnpm prisma migrate deploy
```

New tables:
- `supplier` — new (from migration 20260831142400)
- Composite index: `supplier_tax_id_country_uniq` on (tax_id, country)

## 5. How to start the service

<From detected stack — the framework's dev command>

```
pnpm dev
```

Service starts on `http://localhost:3000`. Wait for the "Nest application successfully started" log line.

## 6. Verify the feature manually — happy path

<Step-by-step, one path from parent's `test-scenarios.md`. Curl-based for backend; browser-based for frontend.>

Create a supplier:

```
curl -X POST http://localhost:3000/supplier \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-dev-token>" \
  -d '{"taxId":"111","country":"US","name":"Test Supplier"}'
```

Expected: `201 Created` with body:

```json
{"id":"SUP-...","taxId":"111","country":"US","name":"Test Supplier","status":"draft"}
```

## 7. Verify one error path

<Choose one non-trivial refusal — usually the AC's "distinct message" case>

Duplicate submission:

```
# Run the create request again with the same taxId + country
curl -X POST http://localhost:3000/supplier \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-dev-token>" \
  -d '{"taxId":"111","country":"US","name":"Duplicate Attempt"}'
```

Expected: `409 Conflict` with body:

```json
{"code":"DUPLICATE_TAX_ID"}
```

## 8. How to run the tests locally

Run all Required gates:

```
pnpm test                # Unit + integration
pnpm test:coverage       # Coverage (must be ≥ 60% lines)
pnpm test:e2e            # E2E (Playwright)
pnpm lint                # ESLint
pnpm typecheck           # tsc --noEmit
pnpm format:check        # Prettier
```

Use the repo's real commands and package manager, not this example. **Give each runner its own line and its own test count** — a unit runner and a browser runner are separate commands with separate totals, and a reader handed one combined figure will run one command, see a smaller number, and assume the run was broken.

Expected: all gates pass. `units/<repo>/status.md § ## Acceptance` was built assuming these all pass.

**CI:** name the workflow that already runs these gates (`.github/workflows/*.yml` or equivalent) and which of them it covers, so nobody re-wires what exists. Build never watches CI — so tell the reader to confirm the run is green on the PR rather than claiming it here. Where no workflow runs them, say so: local is then the only place they have ever passed.

## 9. Known follow-ups

<From `[HELD]` markers in the plan, `deferred-to-e2e` rows in `## Acceptance` table, and any Medium/Low security findings>

- E2E: 4 ACs marked deferred-to-e2e — closed by the last sub-task to land (per parent Feature-4's rollup Sub-tasks table)
- Security warnings deferred to /dev:commit's stricter gate: SR-B-001 (auth guard on POST /supplier), SR-B-002 (axios version pin)
- Rate-limiting on POST /supplier NOT added — parent NFR doesn't require it; add via /qa:setup if needed

## 10. Rollback

If merged and needs reversal:

```
# Revert the migration
pnpm prisma migrate resolve --rolled-back 20260831142400

# Revert the branch
git revert <merge-commit-sha>
```

Or feature-flag: if `SUPPLIER_ONBOARDING_ENABLED=false` is set, the endpoint refuses with 404 (dev-plan step 8 wired the flag).
```

Every section is filled from the actual build's data — no placeholders. If a section genuinely doesn't apply (e.g. no database changes for a pure-frontend feature), omit or write `*(none for this task — no DB changes)*`.

---

### 11d. State transitions

- Local state: `agentExecuting → inProgress` (build phase done; `/dev:commit` will flip to `devReview`)
- MC status: `inProgress` (unchanged — `/dev:commit` transitions to `devReview`)
- Update `status.md`:

```yaml
status: inProgress
phase: built
owner_lock: <current agent id>
branch: feature/FEAT-SUP-001-supplier-onboarding-backend
build_completed_at: 2026-08-31T15:23:12Z
ready_for_dev_commit: true
```

- Update parent's derived status if this is a sub-task (see conventions §5)

---

### 11e. Progress log format

Append to `units/<repo>/status.md § ## Run history`:

```yaml
stage-11:
  status: DONE
  started_at: 2026-08-31T15:23:12Z
  summary_printed: true
  local_runbook_written: units/<repo>/pr-summary.md § ## How to verify
  pr_summary_pre_generated: false                # /dev:commit generates units/<repo>/pr-summary.md
  finished_at: 2026-08-31T15:23:44Z
```

Also close the top-level frontmatter:

```yaml
build_completed_at: 2026-08-31T15:23:44Z
final_state: inProgress
next_command: /dev:commit <task-ref>
```

---

### 11f. On `--resume`

If `--resume` finds `stage-11.status: DONE`, print the same summary from `status.md` § `## Run history` + `units/<repo>/pr-summary.md § ## How to verify`'s existence, don't rebuild.

If Stage 11 was interrupted mid-write (rare — file writes are usually atomic), re-run.

---

### Skills / agents invoked

- Direct file writes (`units/<repo>/pr-summary.md § ## How to verify`, `units/<repo>/status.md § ## Run history`, `status.md`)
- Direct stdout print for the terminal summary
- No subagents

Never invoke `dev-pr-handoff` from Stage 11 — that's `/dev:commit`'s Stage 9. Never modify `pr-summary.md` here — it's not this stage's file.
