# `/dev:build` Command — Design & Implementation Plan (v2.2)

> **Status:** Draft · **Owner:** dev plugin · **Depends on:** `/dev:plan` output present · **Related:** [dev-commit-command.md](dev-commit-command.md)
>
> This is the build-ready plan for the v2.2 refactor of `/dev:build`. Every §-number is a checkable spec.

---

## 1. Purpose

Turn a planned task (parent-alone OR a single sub-task in a split feature) into working, tested code **on an isolated branch** — under the developer's supervision but with zero mid-run prompts. `/dev:build` implements the plan `/dev:plan` produced, writes stack-adaptive tests, actually executes them, runs a scoped security review, and validates the result against the parent's Acceptance Criteria + Business Rules + Test Scenarios + NFRs. Bounded fix loop until 100%. Never pushes, never raises a PR — that's `/dev:commit`.

Two shifts from v2.1:

1. **`/dev:validate` command retired** — validation is now an internal phase of `/dev:build`, not a standalone command. The old `dev-validation` skill becomes internal reference.
2. **`READY_FOR_COMMIT` local state dropped** — use MC's existing status enum. Local delivery-status stays semantically expressive; MC status is the source of truth.

---

## 2. Command shape

**File:** [plugins/dev/commands/build.md](../../plugins/dev/commands/build.md) (rewrite)

```yaml
---
description: Build a planned task through the full loop — branch, implement per implementation.md, write and execute stack-adaptive tests, run a scoped security review, and validate against the parent's Acceptance Criteria + Business Rules + Test Scenarios + NFRs. Bounded fix loop until 100% or escalation. Refuses to run without a /dev:plan-generated plan; halts if quality-gates.md needs greenfield bootstrap and auto-runs qa-greenfield-harness inline. Accepts any task identifier (MC task number, feature slug or folder, sub-task folder, FEAT-<AREA>-NN). Sub-task builds work in the sub-task's repo only, on a branch named feature/FEAT-<AREA>-NN-<slug>-<repo>. Never merges, never pushes, never raises a PR — /dev:commit does that.
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | features/<slug>/subtask/<repo> | FEAT-<AREA>-NN | (blank = next PLANNED task)> [initiative=<name>] [--resume] [--no-security-review]"
---
```

**Arguments** — same resolution as `/dev:plan` Stage 0 (see `/dev:plan` command). One task target per invocation.

**Flags:**
- `--resume` — continue from the last completed phase recorded in `dev/build-run.md`
- `--no-security-review` — SKIP the diff security review (dev-time flag; commit-time always runs)

---

## 3. High-level flow (11 stages)

```
/dev:build <task>
│
├── Stage 0 — Identity resolution + plan verification (halt if no plan)
│
├── Stage 1 — Acquire lock + mount context
│     Local: IN_PLANNING (from PLANNED)  ·  MC: inProgress
│
├── Stage 2 — Pre-flight (MC status + local drift + cross-sub-task deps)
│
├── Stage 3 — Branch creation (FIRST — before any code work)
│     feature/FEAT-<AREA>-NN-<slug>  (parent-alone)
│     feature/FEAT-<AREA>-NN-<slug>-<repo>  (sub-task)
│
├── Stage 4 — QA harness gate
│     ├─ quality-gates.md Active → follow it
│     └─ Missing / Draft / Broken → qa-greenfield-harness (auto, no prompt)
│
├── Stage 5 — Implementation (dev-stack-adaptive-implementation skill)
│     Local: IN_DEVELOPMENT  ·  MC: inProgress
│
├── Stage 6 — Write stack-adaptive tests (part of the same skill)
│
├── Stage 7 — Execute tests locally (actually run them)
│     Local: TESTING  ·  MC: inProgress
│
├── Stage 8 — Validate against parent AC + BR + TS + NFRs
│     Build acceptance-map.md; mark deferred-to-e2e where cross-sub-task
│
├── Stage 9 — Security review (Claude Code security-review skill, feature-diff scoped)
│     Threshold: block on Critical only (Commit-time is stricter)
│
├── Stage 10 — Update code-context units (designed → implemented)
│     Adds implemented_at, implemented_by_commit, mapped_from, updates
│     Source References with [code › <path>]
│
├── Stage 11 — Report summary + local-runbook.md
│     Local: IN_PROGRESS → (stays IN_PROGRESS; /dev:commit flips to REVIEW)
│     MC: inProgress (unchanged; /dev:commit sets devReview)
│
└── Return: summary of what was built, tests run + results, security findings,
    acceptance-map state, and the exact command to run /dev:commit next
```

**Loop:** Stages 5–9 form a bounded fix loop. Any of them failing → repair (up to 3 focused / 2 broad) → re-run downstream stages → summary. Stages 10–11 fire only when 5–9 come back 100%.

**Progress log:** every stage writes to `dev/build-run.md` — same shape as `/dev:plan`'s `plan-run.md` so `--resume` semantics match.

---

## 4. Stage 0 — Identity resolution + plan verification

**Purpose:** resolve the target into a canonical `(feature_id, task_object_id, task_kind, task_folder)` and refuse to run without a plan.

### 4a. Resolve target

Same 4-way resolution as `/dev:plan` Stage 0 — see [dev-plan-command.md §4a](dev-plan-command.md). If target is a `Subtask-N` or `subtask/<repo>/` folder → `task_kind = subtask`; else `parent-alone`.

### 4b. Verify plan exists (hard gate)

Under the task folder, require:

- `dev/implementation.md`
- `dev/implementation.md §3 Impacted components`
- `dev/status.md` with `current_state: PLANNED` or later (`IN_PROGRESS`, `REVIEW` for `--resume`)

Missing → halt with:

```
✗ No plan for <target>. Run:
    /dev:plan <target>
  Then re-run:
    /dev:build <target>
```

Never re-plan inline. If the plan looks stale (unit files moved since it was written) → halt with *"Run `/dev:plan <target> --resume`"* and stop.

---

## 5. Stage 1 — Acquire lock + mount context

Write owner into `status.md`. Transition state:

- **Local:** `PLANNED → IN_PLANNING` (broadcast)
- **MC:** `readyForDev → inProgress` (via `task-mcp.update_task_status`)

**Mount context — read in order:**

1. Parent's BA files: `feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md`.
2. Task's Implementation content:
   - Parent-alone → `features/<slug>/tl-plan.md` (detailed mode)
   - Sub-task → `features/<slug>/subtask/<repo>/description.md` + `implementation.md`; plus parent's `tl-plan.md` (rollup) for cross-sub-task deps
3. `dev/implementation.md` — the ordered build script
4. `dev/implementation.md §3 Impacted components` — 12-dimension impact map
5. `shared-context/decision-log.md` — DEC-### to honour, and where you'll append your own

Record which sources were consulted in `dev/implementation-log.md`. Do not proceed until you can state what "done" is in terms of every AC.

---

## 6. Stage 2 — Pre-flight

Three cheap re-checks (a lot may have flipped since `/dev:plan`):

- **MC status** — refetch this task's status; if MC now says `blocked` → halt with the block reason
- **Local drift** — invoke the shared drift helper on the task's local files. Prompt (Y build as-is / S stop and push first)
- **Cross-sub-task deps** (sub-task target only) — read parent's rollup Sub-tasks table. If any `Depends on` sub-task is NOT `DONE` in MC AND this task's `implementation.md` marks the dep as hard → halt with escalation

---

## 7. Stage 3 — Branch creation (FIRST)

**Resolve target repo:**

- Parent-alone → workspace's primary product repo (from `.jetrix/cache/repolocation.json`)
- Sub-task → repo matching `subtask_repo` frontmatter → look up in `repolocation.json`

If the resolved repo is `SKIPPED` in `repolocation.json` → halt with escalation.

**Base branch resolution:**

Read `.jetrix/project.json` `apps[].env_branches` for THIS repo. Default to the `dev` environment branch (usually `develop`) as the base for the feature branch. If the developer wants to branch off `staging` or `master`, they pass `--base=staging` (deferred to v2.3 if we need it — for now, always `dev`).

**Create branch:**

- Parent-alone → `feature/FEAT-<AREA>-NN-<slug>`
- Sub-task → `feature/FEAT-<AREA>-NN-<slug>-<repo>`

**Never** on `main` / `master` / `staging` / `production` / `develop` directly. Confirm base build is green in the target repo before touching anything (a pre-existing broken build is an escalation, not this feature's bug).

Write branch name into `status.md`. Ready for code.

---

## 8. Stage 4 — QA harness gate

**Read `qa/quality-gates.md`** (workspace-level, from `/qa:setup`):

| Situation | Action |
|---|---|
| Exists, `harness_status: Active` | Follow it — use the Required checks + commands + thresholds |
| Exists, `Draft` / `Broken` | If truly broken (Required gates red before changes) → halt with escalation, route to `/qa:health`. If Draft → treat as missing → auto-bootstrap. |
| Missing entirely | Auto-bootstrap via `qa-greenfield-harness` inline (see §17) |

**Never** prompt the user during `/dev:build`. If `qa-greenfield-harness` needs a decision that can't be made deterministically (e.g. two equally valid test frameworks), it picks the more idiomatic one for the stack and logs the choice in `dev/test-decision.md`. Later `/qa:audit` can override.

---

## 9. Stage 5 — Implementation (`dev-stack-adaptive-implementation` skill)

Local: `IN_PLANNING → IN_DEVELOPMENT` (broadcast). MC: still `inProgress`.

**Delegate to the `dev-stack-adaptive-implementation` skill** — see §17 for the full skill spec. Summary of what the skill does:

1. Detect the stack (language, framework, ORM, testing framework, package manager) via `shared-context/technology-stack.md` if present, else by scanning repo top-level for `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` / etc.
2. For each ordered step in `implementation.md`:
   - Read the relevant TL unit files (endpoints, entities, pages) for the target repo
   - Locate the target file(s) in the repo, using naming conventions inferred from the stack
   - Write the code idiomatically per the stack — using patterns already present in the repo (imports, error handling, logging, config), not generic templates
   - Log every material technical choice as a `DEC-###` in `shared-context/decision-log.md`
3. Follow `coding-standards.md` (from `shared-context/`) if present
4. Reuse existing patterns and abstractions — never introduce a parallel abstraction
5. Stay inside the scope boundary — touching another repo requires a scope escalation

---

## 10. Stage 6 — Write stack-adaptive tests

Same skill (`dev-stack-adaptive-implementation`), separate sub-phase. Uses the test framework from `qa/quality-gates.md` (Active) OR from `dev/test-decision.md` (greenfield bootstrap output).

**Test scope per task kind:**

| Task kind | Tests written |
|---|---|
| Parent-alone (single-repo) | Unit + integration + e2e for every AC + TS the feature declares |
| Sub-task, backend | Unit + integration for every AC/BR/TS validatable at the backend layer; contract tests for API endpoints |
| Sub-task, frontend | Unit for components + integration for surfaces + E2E for every AC/TS validatable at the UI layer |
| Sub-task, mobile | Unit + widget + integration; E2E if the harness supports it |

**Never write tests that just call the SUT with hardcoded responses.** Each test must:
- Assert on real behaviour (state change, response shape, error handling)
- Match at least one AC / BR / TS from parent
- Have a clear failure message

Test file locations follow the stack's convention (e.g. `*.test.ts` next to source for TS/JS, `tests/` folder for Python, `_test.go` for Go).

---

## 11. Stage 7 — Execute tests locally

**Actually run the test command.** No planning-mode, no "would run" — the command from `qa/quality-gates.md` (or `dev/test-decision.md`) executes in the target repo.

- Capture stdout + stderr into `dev/implementation-log.md` under a `test_run_<timestamp>` block
- Parse the exit code + framework output for pass/fail per test
- Any failure → jump to §14 (repair loop) before proceeding to Stage 8

If the test command doesn't exist (e.g. `npm test` fails with *"command not found"*) → surface as a critical failure and route to Stage 4's harness gate for re-bootstrap. Do not silently skip.

---

## 12. Stage 8 — Validate against parent AC + BR + TS + NFRs

Local: `IN_DEVELOPMENT → TESTING` (broadcast). MC: still `inProgress`.

Build `dev/acceptance-map.md`. Every parent-owned assertion gets a row:

```markdown
| Kind | ID | Statement | Verified by | Result | Evidence |
|---|---|---|---|---|---|
| AC | AC-B1 | POST /supplier returns 201 with created record | test:endpoint.spec.ts::create-happy | ✅ pass | log:test_run_2026-08-31-11-24 |
| AC | AC-1  | (E2E) user submits form, sees toast, record in list | E2E — not owned by this sub-task | ⏸ deferred-to-e2e | last sub-task closes |
| BR | BR-1  | (tax_id, country) uniqueness | DB constraint + pre-insert check | ✅ pass | code:migration + test:duplicate.spec.ts |
| TS | TS-U-1 | Happy-path — new supplier | test:supplier.spec.ts::happy | ✅ pass | log:test_run |
| NFR | NFR-B1 | Endpoint responds < 300ms p95 | benchmark:perf.spec.ts | ✅ pass | log:perf_run |
```

**Any row that's `❌ fail`** → jump to §14 (repair loop). Any row `⏸ deferred-to-e2e` is legit for a sub-task not last-to-land.

**100% complete** = every applicable row is `✅ pass` or `⏸ deferred-to-e2e`. Missing rows are a design bug — fail loud, escalate.

---

## 13. Stage 9 — Security review (feature-diff scoped)

Local: `TESTING` (still). MC: still `inProgress`.

Invoke Claude Code's built-in **`security-review`** skill:

- **Scope:** the diff between the base branch (per §7 resolution) and the current branch HEAD. NOT the whole repo.
- **Threshold at build-time:** block on `Critical` findings only. `High` findings surface as warnings but don't halt (`/dev:commit` will re-run with High-as-blocker).
- **Focus areas (build-time):**
  - Injection (SQL, command, path traversal)
  - Authentication/authorization on new endpoints
  - Secret leaks in new code
  - Insecure deserialization
  - Basic input validation

`--no-security-review` flag skips this stage entirely (for prototyping / spike branches — user takes responsibility).

**Any Critical** → jump to §14 (repair loop). Fix the finding, re-run.

---

## 14. Repair loop (bounded)

**Bounded retries** — inherited from `feature-delivery-loop`, tightened per phase:

| Phase | Focused attempts per failure | Broad re-runs |
|---|---|---|
| Stage 6 (test write) | 2 | 1 |
| Stage 7 (test execute) | 3 | 2 |
| Stage 8 (validate) | 3 | 2 |
| Stage 9 (security) | 3 (per finding) | 1 (whole security pass) |

Same failure surviving the limit → escalate with a structured note. Never blind-retry.

**Local: `TESTING → REVIEW_FIXES`** during repair. MC stays `inProgress`.

---

## 15. Stage 10 — Update code-context units (`designed → implemented`)

For every TL unit this task built (endpoints, pages, entities), update the unit file in the target repo's `<repo>/context/code-context/`:

**Frontmatter changes:**

```yaml
---
# Before (from /tl:plan)
origin: designed
design_confidence: Likely

# After /dev:build stage 10
origin: implemented
design_confidence: Confirmed              # promote from Likely once actually built
implemented_at: 2026-08-31T14:22:07Z
implemented_by_commit: <HEAD SHA>
implemented_by_task: FEAT-SUP-001-1       # feature id or sub-task external id
mapped_from: src/routes/supplier.ts       # actual code file
mapped_from_line: 42                      # optional; line of the export
---
```

**Body changes:**

Append to `## Source References`:

```markdown
## Source References

- [feature › FEAT-SUP-001]                             ← already there from designed
- [code › src/routes/supplier.ts:42]                   ← ADD
- [test › tests/endpoints/supplier.spec.ts::create]    ← ADD (references first test file)
```

Also update:
- `## Status` block → set to `active` (was `draft` for designed units)
- Layer index rows (`frontend-index.md` / `backend-index.md` / `database-index.md`) — update the `Status` column to `active` and add a short one-line "Built by FEAT-… on <commit>" to the row

**Merge boundary:** these updates go on the FEATURE BRANCH only — the base branch's units keep `origin: designed` until `/dev:commit`'s semantic merge (v2.3 skill, see `/dev:commit` plan) or a later `/tl:code-map --refresh` on `main`.

---

## 16. Stage 11 — Report summary + `local-runbook.md`

Two artifacts:

### 16a. In-terminal summary (the developer sees this immediately)

```
✓ /dev:build FEAT-SUP-001-1 complete

Branch:            feature/FEAT-SUP-001-supplier-onboarding-backend  (in acme-backend)
Base:              develop
Files changed:     8  (+624 / -12)
Tests written:     14  (11 unit, 3 integration)
Tests executed:    14/14 passing
Security review:   ✓ 0 Critical (2 High deferred to /dev:commit's stricter gate)
Acceptance map:    9/12 verified locally · 3 deferred-to-e2e (last sub-task closes)
Code-context:      3 units updated (EP-SUP-01, EP-SUP-02, ENT-SUP-01) → implemented

MC status:    inProgress
Local state:  IN_PROGRESS  (build phase complete; awaiting /dev:commit)

Next:
  1. Review dev/local-runbook.md if you haven't set up env / config
  2. Verify the change locally (see runbook)
  3. When ready:  /dev:commit FEAT-SUP-001-1
```

### 16b. `dev/local-runbook.md` (developer-facing setup guide)

**Not the PR summary.** This is the "how to run this locally on my machine" guide. Written to `.jetrix/features/<slug>/dev/local-runbook.md` (parent-alone) or `.jetrix/features/<slug>/dev/<repo>-local-runbook.md` (sub-task).

Sections:

1. **What this feature is** — 2-line business summary (from parent's Description)
2. **Prerequisites** — tools, versions, accounts needed
3. **Environment / config setup** — every env var, credential, or config file needed. If any need real values from the user, mark them with `[SET REQUIRED]`
4. **Database changes** — migrations to run, seed data if any
5. **How to start the service** — exact command (e.g. `pnpm dev`, `python manage.py runserver`, `dotnet run`)
6. **How to verify the feature manually** — the happy path + at least one error path, step by step
7. **How to run the tests locally** — exact command; expected output shape
8. **Known follow-ups** — anything the plan flagged as `[HELD]` or `deferred-to-e2e`
9. **Rollback** — how to reverse the feature if needed (migration down, feature flag off)

This file is what the developer reads at their desk. The PR summary is what the reviewer reads on GitHub. Different audiences, different content.

---

## 17. The two new skills (specs)

### 17a. `dev-stack-adaptive-implementation`

**Location:** `plugins/dev/skills/dev-stack-adaptive-implementation/SKILL.md`

**Purpose:** Guide code-writing during `/dev:build` Stages 5 + 6. Not a "here's how to write React" playbook. Instead: detect the stack, read the repo's existing conventions, and write feature code that fits.

**Skill file structure:**

- `SKILL.md` — the frontmatter, top-level workflow, hard rules
- `references/stack-detection.md` — how to detect language/framework/ORM/testing/package-manager (deterministic ladder — file-based, no LLM guessing)
- `references/pattern-inference.md` — how to read a repo's conventions (folder structure, naming, error-handling style, DI style, config style) in ≤ 10 file reads
- `references/test-patterns.md` — how to write tests for the detected framework, mapping to AC/BR/TS

**Absolute rules:**

- No global patterns — always read what the repo already does before writing
- Reuse existing abstractions (services, repositories, view-models) — never introduce a parallel one
- Follow the repo's error-handling style — if it uses `try/catch + custom errors`, do the same; if it uses `Result<T, E>`, do that
- Follow the repo's testing framework choice (from `qa/quality-gates.md` OR the greenfield harness's decision)
- Never leak framework names in comments/documentation
- Never invent behaviour not in `implementation.md`

### 17b. `qa-greenfield-harness`

**Location:** `plugins/dev/skills/qa-greenfield-harness/SKILL.md`

**Purpose:** Auto-bootstrap tests + `quality-gates.md` when `/dev:build` finds a greenfield or no-gates situation. **Fully automatic — no user prompts.** Logs decisions to `dev/test-decision.md` for audit.

**Trigger conditions (Stage 4 evaluates):**

- Greenfield: `<repo>/context/code-context/` is empty OR the repo has ≤ 3 source files (skeleton)
- No gates: `qa/quality-gates.md` missing OR `harness_status != Active`

**Decision ladder — deterministic, no LLM guessing:**

Per detected stack, pick from this fixed matrix:

| Layer | Stack | Unit / Integration | E2E |
|---|---|---|---|
| Frontend | React/TS | Vitest + Testing Library | Playwright |
| Frontend | Vue/TS | Vitest + Vue Test Utils | Playwright |
| Frontend | Angular | Jest + Testing Library | Playwright |
| Frontend | Svelte | Vitest + Testing Library | Playwright |
| Backend | Node/Express | Vitest + Supertest | Playwright API |
| Backend | Node/NestJS | Jest + Supertest | Playwright API |
| Backend | Python/FastAPI | pytest + httpx.AsyncClient | Schemathesis |
| Backend | Python/Django | pytest + pytest-django | Schemathesis |
| Backend | Go | Go std testing + testify | Go std + httptest |
| Backend | .NET | xUnit + WebApplicationFactory | RestAssured.Net |
| Mobile | Flutter | flutter_test | patrol / integration_test |
| Mobile | React Native | Jest + RN Testing Library | Detox |
| DB | Postgres | pgTAP or in-code migration tests | — |
| DB | MongoDB | in-code fixture tests | — |

Unknown stack → fall back to `<stack> + <best-known-testing-tool>` and log the choice as an assumption.

**What the skill writes:**

1. Test dependency additions (via package manager — `npm i -D <pkg>`, `pip install <pkg>`, etc.)
2. Test config files (`vitest.config.ts`, `pytest.ini`, `playwright.config.ts`, etc.) — minimal but working
3. `qa/quality-gates.md` — a minimal Active harness contract:
   ```yaml
   ---
   doc_type: quality-gates
   schema_version: 1.0
   produced_by: dev
   harness_status: Active
   bootstrapped_by: qa-greenfield-harness
   bootstrapped_at: <ISO>
   ---

   ## Required gates

   | QG | Check | Command | Threshold | Layer |
   |---|---|---|---|---|
   | QG-001 | unit tests    | pnpm test:unit    | pass 100% | any |
   | QG-002 | integration   | pnpm test:int     | pass 100% | any |
   | QG-003 | e2e           | pnpm test:e2e     | pass 100% | frontend |
   | QG-004 | coverage      | pnpm test:coverage | ≥ 60%    | any |
   | QG-005 | lint          | pnpm lint         | pass 100% | any |
   | QG-006 | type-check    | pnpm typecheck    | pass 100% | any |

   ## Notes
   Bootstrapped by /dev:build's qa-greenfield-harness on <date>.
   Overridable via /qa:audit → /qa:plan → /qa:setup (interactive flow).
   ```
4. `dev/test-decision.md` — audit log of what was chosen and why (for future `/qa:audit` runs)

**Never prompts.** Every choice is deterministic per the matrix. If the developer wants a different framework, they run `/qa:audit` after and override.

---

## 18. Local file layout (per task)

```
.jetrix/features/<slug>/
├── (BA files unchanged)
├── tl-plan.md                           (rollup or detailed)
│
└── dev/                                 (parent-alone) OR
└── dev/ (with <repo>- prefix)                  (sub-task)
    │
    │  (from /dev:plan — read by /dev:build)
    ├── implementation.md
    ├── implementation.md §3 Impacted components
    ├── status.md
    ├── plan-run.md
    │
    │  (written by /dev:build)
    ├── build-run.md                     ← stage-by-stage progress (new)
    ├── implementation-log.md            ← per-step, per-test-run
    ├── acceptance-map.md                ← every AC/BR/TS/NFR verified locally
    ├── decisions.md                     ← DEC-### local mirror
    ├── local-runbook.md                 ← developer-facing setup + run guide (new)
    ├── test-decision.md                 ← only if qa-greenfield-harness fired
    └── escalation-<n>.md                ← if BLOCKED
```

**Cross-repo state:** feature branches with names + status carried in `status.md` per task. Parent's derived status pulled from sub-tasks per `/dev:plan` §10.

---

## 19. Status mapping — local + MC

Per your instruction (2026-08-31 chat): use MC's existing enum. No new invented states.

| /dev:build phase | Local state (`status.md`) | MC status (`task-mcp.update_task_status`) |
|---|---|---|
| Start (Stage 1 lock) | `IN_PLANNING` | `inProgress` |
| Implementation (Stage 5) | `IN_DEVELOPMENT` | `inProgress` |
| Test write (Stage 6) | `IN_DEVELOPMENT` | `inProgress` |
| Test execute (Stage 7) | `TESTING` | `inProgress` |
| Validate (Stage 8) | `TESTING` | `inProgress` |
| Repair (§14) | `REVIEW_FIXES` | `inProgress` |
| Security review (Stage 9) | `TESTING` | `inProgress` |
| Update context (Stage 10) | `TESTING` | `inProgress` |
| Complete (Stage 11) | `IN_PROGRESS` (build phase done; awaits `/dev:commit`) | `inProgress` (unchanged) |
| Escalation | `BLOCKED` | `blocked` |

**`/dev:commit` will flip MC status to `devReview` on start** (see [dev-commit-command.md](dev-commit-command.md)). On merge → MC `done`.

**Parent's status derived** from sub-tasks — automatic (see `/dev:plan` §10).

---

## 20. Files to create / modify / delete

### Create

| Path | Purpose |
|---|---|
| [plugins/dev/skills/dev-stack-adaptive-implementation/SKILL.md](../../plugins/dev/skills/dev-stack-adaptive-implementation/) | Dynamic implementation guide (§17a) |
| [plugins/dev/skills/dev-stack-adaptive-implementation/references/stack-detection.md](../../plugins/dev/skills/dev-stack-adaptive-implementation/references/) | Detection ladder |
| [plugins/dev/skills/dev-stack-adaptive-implementation/references/pattern-inference.md](../../plugins/dev/skills/dev-stack-adaptive-implementation/references/) | How to read a repo's conventions |
| [plugins/dev/skills/dev-stack-adaptive-implementation/references/test-patterns.md](../../plugins/dev/skills/dev-stack-adaptive-implementation/references/) | Per-framework test-writing patterns |
| [plugins/dev/skills/qa-greenfield-harness/SKILL.md](../../plugins/dev/skills/qa-greenfield-harness/) | Auto-bootstrap harness (§17b) |
| [plugins/dev/skills/qa-greenfield-harness/references/stack-matrix.md](../../plugins/dev/skills/qa-greenfield-harness/references/) | The deterministic per-stack test-tool matrix |
| [plugins/dev/skills/qa-greenfield-harness/references/gates-template.md](../../plugins/dev/skills/qa-greenfield-harness/references/) | The minimal quality-gates.md template |
| [plugins/dev/commands/references/build/stage-4-qa-gate.md](../../plugins/dev/commands/references/build/) | QA harness gate runbook |
| [plugins/dev/commands/references/build/stage-5-6-implement.md](../../plugins/dev/commands/references/build/) | Implementation + test-write runbook |
| [plugins/dev/commands/references/build/stage-7-test-execute.md](../../plugins/dev/commands/references/build/) | Test execution runbook |
| [plugins/dev/commands/references/build/stage-8-validate.md](../../plugins/dev/commands/references/build/) | Acceptance-map building runbook |
| [plugins/dev/commands/references/build/stage-9-security.md](../../plugins/dev/commands/references/build/) | Security review invocation |
| [plugins/dev/commands/references/build/stage-10-context-update.md](../../plugins/dev/commands/references/build/) | designed → implemented update rules |
| [plugins/dev/commands/references/build/stage-11-summary.md](../../plugins/dev/commands/references/build/) | Report + local-runbook.md builder |

### Modify

| Path | Change |
|---|---|
| [plugins/dev/commands/build.md](../../plugins/dev/commands/build.md) | Full rewrite to the 11-stage orchestrator + skill delegations |
| [plugins/dev/skills/feature-delivery-loop/SKILL.md](../../plugins/dev/skills/feature-delivery-loop/) | Retire the old §3-inline validation flow (already partly done in v2.1); refer to Stage 5-11 orchestration in commands/references/build/ |
| [plugins/dev/dev_readme.md](../../plugins/dev/dev_readme.md) | Add the two new skills; note `/dev:validate` retired |
| [plugins/delivery-os-core/skills/delivery-os-conventions/SKILL.md](../../plugins/delivery-os-core/skills/delivery-os-conventions/) | Bump to v2.2 — add `implemented` origin state on code-context units + new frontmatter fields; document MC status mapping table |

### Delete

| Path | Reason |
|---|---|
| [plugins/dev/commands/validate.md](../../plugins/dev/commands/validate.md) | `/dev:validate` retired; validation is `/dev:build` Stage 8 |
| [plugins/dev/skills/dev-validation/](../../plugins/dev/skills/dev-validation/) | Skill retired; logic absorbed into `dev-stack-adaptive-implementation` + stage-8-validate.md |

---

## 21. Order of implementation

1. **`delivery-os-conventions` v2.2 bump** — MC status mapping table + `implemented` origin state → lock the contract other skills read.
2. **Create `dev-stack-adaptive-implementation` skill** — SKILL.md + 3 reference files. Fully local, no MC dependency.
3. **Create `qa-greenfield-harness` skill** — SKILL.md + 2 reference files. Fully local. Deterministic stack matrix.
4. **Create the 8 stage reference files** under `plugins/dev/commands/references/build/`. Each captures its stage's verbatim spec.
5. **Rewrite `plugins/dev/commands/build.md`** — the 11-stage orchestrator, routes to the 8 reference files.
6. **Delete `plugins/dev/commands/validate.md`** and the `dev-validation` skill folder.
7. **Update `dev_readme.md`** — new skills, retired `/dev:validate`.
8. **Update `feature-delivery-loop/SKILL.md`** — point at the new orchestration model.
9. **Smoke test on a real feature** — greenfield first (exercises `qa-greenfield-harness`), then brownfield-with-gates (exercises the gates path).

Steps 1–8 are pure text authoring — no runtime dependency. Step 9 requires a real repo.

---

## 22. Success criteria

- `/dev:build FEAT-…-1` on a fully-planned sub-task → runs Stages 3-11 without prompting; produces a working branch with tests passing, security clean, acceptance-map full, code-context updated
- Greenfield + no `qa/quality-gates.md` → `qa-greenfield-harness` fires inline, writes tests + gates + `test-decision.md`, continues without user input
- Brownfield with `qa/quality-gates.md` Active → follows the gates verbatim
- `/dev:build` before `/dev:plan` → clean halt with "run /dev:plan first"
- `/dev:build` with `--resume` → skips completed stages via `build-run.md`
- Test failure in Stage 7 → repair loop bounded per §14; escalates cleanly after limit
- Critical security finding → repair loop; escalates after limit
- Completion → both `pr-summary.md` (still exists, PR-focused) and NEW `local-runbook.md` (developer-focused) are written
- MC status transitions: `readyForDev → inProgress` (Stage 1) → stays `inProgress` through completion → `/dev:commit` flips to `devReview`

---

## 23. Explicitly out of scope

- Pushing the branch — `/dev:commit` does that
- Raising the PR — `/dev:commit` does that
- Code review — `/dev:commit`'s second-gate does that (via `dev-stack-adaptive-code-review` skill)
- Semantic context merge with base — `/dev:commit`'s `tl-semantic-context-merge` skill does that
- `/qa:audit` / `/qa:plan` / `/qa:setup` — those are project-level, user-initiated setup; NOT triggered by `/dev:build`
- E2E validation of cross-sub-task ACs — closed by the LAST sub-task in a split feature (its `/dev:build` picks up all deferred rows)

---

## 24. Blockers / open questions

**BB-01** — Base branch: hardcode to `dev` environment branch for v2.2? Or add `--base=<env>` flag now? Recommendation: hardcode `dev`, add flag later if needed. **Owner:** us. **Non-blocking.**

**BB-02** — Does `qa-greenfield-harness` write to the repo directly, or to a staging folder first for the developer to review? Recommendation: direct write; `test-decision.md` is the audit trail. **Owner:** us. **Non-blocking; matches your "no prompts in /dev:build" rule.**

**BB-03** — When `feature-delivery-loop` skill still refers to the old 12-step loop, do we retire it entirely or slim it to a "loop control" reference? Recommendation: slim it to just the state model + retry limits + escalation vocabulary; delegate the actual stage work to `commands/references/build/`. **Owner:** us. **Non-blocking.**

---

**End of `/dev:build` plan.** Every §-number is a checkable spec. See [dev-commit-command.md](dev-commit-command.md) for the second half of the flow.
