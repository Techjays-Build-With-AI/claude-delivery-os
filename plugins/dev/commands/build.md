---
description: Build a planned task through the full 11-stage loop — branch, QA harness gate (auto-bootstraps greenfield via qa-greenfield-harness), implement per implementation.md using dev-stack-adaptive-implementation (dynamic per stack, reads repo conventions, matches idiomatic patterns), write stack-adaptive tests, execute them locally, validate against parent's Acceptance Criteria + Business Rules + Test Scenarios + NFRs, run a scoped security review (feature-diff only, Critical-blocking at build-time; /dev:commit is stricter), update code-context units to origin:implemented, and produce a summary + local-runbook.md. Bounded fix loop until 100% or escalation. Refuses to run without a /dev:plan-generated plan OR with unresolved plan-blockers.md. Accepts any task identifier (MC task number, feature slug or folder, sub-task folder, FEAT-<AREA>-NN). Sub-task builds work in the sub-task's repo only, on a branch named feature/FEAT-<AREA>-NN-<slug>-<repo>. Never merges, never pushes, never raises a PR — /dev:commit does that.
argument-hint: "<task-number | Task-N | slug | features/<slug> | tasks/<slug>.md | FEAT-<AREA>-NN | (blank = next PLANNED task)> [initiative=<name>] [--resume] [--no-security-review] [--skip-qa]"
---

# /dev:build

You are the entry point for the 11-stage build loop. **Orchestrator only** — this file parses args, resolves identity, verifies the plan + no unresolved blockers, then routes each stage to its reference file under `plugins/dev/commands/references/build/`. Do NOT paraphrase the stage files' instructions — `Read` them and execute verbatim.

Read the **`delivery-os-conventions`** skill first if it's not in context — the v2.2 loop-control state model + MC status mapping. Then read the task's plan (produced by `/dev:plan`).

**The single invariant:** `/dev:build` runs on a decidable plan or refuses. Never prompts the user mid-run.

**Never commits, never stages, never pushes (v2.3.20 clarified — the git-write boundary belongs to `/dev:commit`).** All source files, test files, and context-unit updates that `/dev:build` produces LAND IN THE WORKING TREE. Never `git add`, never `git commit`, never `git push`, never open a PR — that's the separation of concerns the plugin has always documented, and this is the invariant that enforces it. `/dev:commit` gathers everything from the working tree, structures the commit(s), pushes, and opens the PR after its stricter security + review gates pass. Stage 10 (context-graph update) writes updated units to the working tree without committing them; Stage 11 writes `dev/local-runbook.md` without committing it; all Stages 5-6 code + test writes land in the working tree without commits per §1 build step.

---

## 1. Parse arguments

`$ARGUMENTS` may contain:

**Task target** (required, unless blank for "next PLANNED"):
- **Task number** — `11` (bare) or `Task-11` / `Feature-11` / `Subtask-11`. A bare integer is accepted wherever a target is, and means `Task-<n>`. This is the normal form — it is what Mission Control shows, and it needs no knowledge of where anything sits on disk.
- Local feature slug: `supplier-onboarding`
- Local feature folder: `features/supplier-onboarding`
- Sub-task folder: `features/supplier-onboarding/subtask/backend`
- Internal id: `FEAT-<AREA>-NN`
- **Non-feature ticket**: `tasks/<slug>.md` (bug / story / task / epic planned via `/dev:plan` §2f). Its plan lives at `tasks/<slug>/dev/` — read `implementation.md`, `status.md`, and `plan-blockers.md` from there, not from `features/`. Never split: a non-feature builds in one repo, on `fix/<slug>` for a bug, `feature/<slug>` otherwise.
- Blank: pick next task at `PLANNED` — scan `features/tracker.md` **and** `tasks/*/dev/status.md`. If both have candidates, list them and ask.

**Flags:**
- `initiative=<name>` — scope selection to one work-batch
- `--resume` — continue from last completed stage per `dev/build-run.md`
- `--no-security-review` — skip Stage 9's diff security review (dev-time convenience; `/dev:commit` always runs security)
- `--skip-qa` — **skip Stage 4's harness bootstrap and write no tests.** For a change whose risk does not justify standing up a test framework: a CSS value, a copy fix, a config default. Stage 4 logs `qa_gate_state: skipped-by-user` and Stages 5–6 write code without tests; Stage 8 builds the acceptance-map from inspection instead of test evidence and marks every row `verified: manually`. `/dev:commit` still runs its full security and code review — this flag buys you out of *testing*, never out of *review*.

**When `--skip-qa` is the right call, and when it is not.** A repo with no test framework forces a real choice: install one, or accept that this change is verified by eye. For a one-line presentational fix the harness costs more than the change and protects nothing — take the flag. For anything touching behaviour, data, auth, or money, the absence of tests is the reason to build the harness, not to skip it. `/dev:build` never decides this for you: without the flag it bootstraps, with it it does not.

## 2. Stage 0 — Identity resolution + plan verification (hard gate)

Same 4-way resolution as `/dev:plan` Stage 0 — see `plugins/dev/commands/plan.md` §2a. Determine `task_kind` (parent-alone or sub-task) and canonical `(feature_id, task_object_id, task_number, task_folder)`.

**Verify the plan exists.** Check for `implementation.md` (with sections §1–§9 per v2.3.11 frame — Build sequence through Shared contract) and `status.md` under the task folder. Missing OR `status.md` `current_state` not `PLANNED` / later → halt with the "run /dev:plan first" message.

**Verify no unresolved plan blockers (v2.2 hard gate).** Check for `dev/plan-blockers.md`:

- Missing → continue
- Exists, `status: RESOLVED` → log the resolved `DEC-###` refs into `build-run.md`; continue
- Exists, `status: OPEN` or `RESOLVING` → halt with "run /dev:plan --resume first" message. Never make build-time decisions.

**Verify engineering standards contract (v2.3.11 hard gate).** Check for `shared-context/coding-standards.md`:

- Missing → halt with `blocker: coding-standards-missing`. Message points at `plugins/tl/skills/tl-project-scaffold/references/scaffold-guide.md` §4 for the required-sections template (greenfield: re-run `tl-project-scaffold` if the scaffold skipped it; brownfield: author the file directly using the template).
- Present, but §6 (function complexity budget), §7 (duplication policy), §8 (recursion policy), §9 (constants & magic values), §10 (state & side effects), or §12 (anti-patterns forbidden) is blank / absent → halt with `blocker: coding-standards-incomplete`, listing which section(s).
- Present + all required sections filled → continue. Log `coding_standards_checked: true` + the file's `updated_at` timestamp to `build-run.md`.

Rationale: `dev-stack-adaptive-implementation` Rule 13/14 and code-review Dimension 8 are hard consumers of this file. Without it, Rule 13's write-time checks have no thresholds to compare against and Dimension 8's review checks have no policy to enforce — the "100% engineering standard" guarantee collapses to hope. Catching the gap at Stage 0 means the fix lands before any code is written, not after review flags it.

**Verify QA gate contract (v2.3.16 gate — soft-when-Stack-Inferred).** Check for `qa/quality-gates.md`:

**This is a read, not a gate — Stage 4 owns bootstrapping.** Stage 0 halts on exactly one state. Anything Stage 4 can fix automatically it must be allowed to reach; halting here made Stage 4's auto-bootstrap unreachable and forced users to stand up a harness by hand before a one-line fix.

- Present, `harness_status: Active` (or the legacy spelling `Ready`) → strict mode. Read Required tiers per capability class. Rule 7 in `dev-stack-adaptive-implementation` writes tests at every declared tier for every §1 step. Log `qa_gate_state: Active`.
- Present, `harness_status: Stack-Inferred` → soft mode. Tier pools were inferred from stack detection at plan time; NEW feature coverage is still 100% at every applicable tier from the inferred pool. Rule 7 writes tests at every inferred tier. Log `qa_gate_state: Stack-Inferred` + `stack_inferred_from: <source>`.
- **Missing, `harness_status: Draft`, or no `harness_status` key at all → continue.** Log `qa_gate_state: needs-bootstrap` and carry on; **Stage 4 auto-bootstraps it** after the branch exists. Never halt for these. A file with no `harness_status` key is the scaffold placeholder — the same thing as missing, and it must not read as "not Active".
- Present, `harness_status: Broken` → **halt** with `blocker: quality-gates-broken`. This is the one state Stage 4 refuses to bootstrap over, because a broken harness means a previously-working setup regressed and silently replacing it would hide that. Route to `/qa:health`.

Keep `harness_status` vocabulary aligned with Stage 4: `Active` · `Stack-Inferred` · `Draft` · `Broken`. `Ready` is the legacy spelling of `Active` and is accepted on read, never written.

The Stack-Inferred path is the intentional escape hatch for teams that want to plan+build a new feature WITHOUT first backfilling test coverage on an existing codebase. The NEW feature still gets 100% coverage at every applicable tier — the inference just skips the audit-of-existing-code step. Backfill of existing coverage is deferred to a later `/qa:audit → /qa:plan → /qa:setup` run.

## 3. Route to stages 1–11 (per-task workers; parallel fan-out for split-parent targets; resume-aware)

**Target-based routing (v2.3.20 — parallel fan-out for split features):**

| Resolved target | Workers | Concurrency |
|---|---|---|
| Sub-task ID (`Subtask-N`, `subtask/<repo>` folder, or feature ID + `--subtask=<repo>`) | 1 worker for THIS sub-task | Single |
| Feature ID / slug / folder of a PARENT-ALONE feature | 1 worker for the parent | Single |
| Feature ID / slug / folder of a SPLIT feature (has `subtask/<repo>/` children) | ONE worker PER sub-task, FAN OUT in PARALLEL | Bounded by `--concurrency=N` (default: 5) |
| Blank → next PLANNED from tracker | If next PLANNED is a split-parent, fan out per above; else 1 worker | Same as above |

**Fan-out semantics for split-parent targets:**

- Each sub-task worker is fully independent: its own repo, its own branch (created in Stage 3), its own Stages 1–11, its own `dev/build-run.md` under `features/<slug>/subtask/<repo>/dev/build-run.md`.
- Workers run in parallel up to `--concurrency=N`. A default of 5 matches the `/dev:plan` batch behavior.
- Per-worker isolation: one sub-task's Stage 8 failure halts THAT worker only — sibling workers keep running.
- `--resume` on a split-parent target resumes each sub-task worker independently based on its own `build-run.md`.
- Sub-task builds are safe to parallelize because the wire contract is locked in §8 Shared contract of every sub-task's plan (Rule 11.3 verbatim inheritance); the frontend tests against a mocked backend that matches §8, not against the running backend.

**Consolidated report after all workers complete (or halt):**

```
✓ /dev:build <feature-ref> complete — <N> sub-tasks built (or halted)

Per sub-task results:
  ✓ Subtask-2 (backend)   — 12/12 §1 steps, 273+28 tests green, 0 Critical security
    ↳ Branch: feature/FEAT-HCAL-01-holiday-calendar-management-backend
    ↳ MC:     https://mission-control.techjays.com/task/6a95e0a0...   ↳ Local state: IN_PROGRESS
  ✓ Subtask-3 (frontend)  — 9/9 §1 steps, 148 tests green, 0 Critical security
    ↳ Branch: feature/FEAT-HCAL-01-holiday-calendar-management-frontend
    ↳ MC:     https://mission-control.techjays.com/task/6a95e0a1...   ↳ Local state: IN_PROGRESS

Working tree (per repo):
  · Inhouse-server:   <M> files changed (+624/-12), uncommitted   ← /dev:commit Subtask-2 gathers these
  · Inhouse-client:   <K> files changed (+412/-8),  uncommitted   ← /dev:commit Subtask-3 gathers these

Next:
  · /dev:commit Subtask-2   ← runs stricter security + review + gathers Inhouse-server working tree → commits + pushes + PR
  · /dev:commit Subtask-3   ← same for Inhouse-client
```

**Per-worker execution:** Read each stage's reference file and execute verbatim. Stages 1–3 (mount + preflight + branch) are inline in this command file below; Stages 4–11 delegate. No stage in any worker calls `git add` / `git commit` / `git push` — the "Never commits, never stages, never pushes" invariant at the top of this file applies uniformly.

### Stage 1 — Acquire lock + mount context

- Write owner into `status.md`
- Local: `PLANNED → IN_PLANNING` (broadcast)
- MC: `readyForDev → inProgress` via `task-mcp.update_task_status`
- Read parent BA files (`feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md`) — validation contract
- Read task's Implementation content (`implementation.md` at feature root for parent-alone; `subtask/<repo>/{description,implementation}.md` for sub-task; plus parent's `tl-plan.md` rollup for split cross-sub-task dep context only)
- Read `shared-context/decision-log.md`, `shared-context/coding-standards.md` (Rule 13/Dimension 8 contract)
- Record sources consulted in `dev/implementation-log.md`

### Stage 2 — Pre-flight

Three cheap re-checks:
- **MC status:** if MC now says `blocked` → halt with the block reason
- **Local drift:** invoke shared drift helper; prompt Y/S if drift found
- **Cross-sub-task deps** (sub-task only): read parent's rollup Sub-tasks table; if any `Depends on` sub-task not `DONE` in MC AND this task's dev-plan marks the dep as hard → halt

### Stage 3 — Branch creation (FIRST)

- Resolve target repo (parent-alone → primary product repo; sub-task → repo matching `subtask_repo` frontmatter). If `SKIPPED` in `repolocation.json` → escalate.
- Resolve base branch from `.jetrix/project.json` `apps[].env_branches.dev` (default: `develop`).
- Create branch:
  - Parent-alone → `feature/FEAT-<AREA>-NN-<slug>`
  - Sub-task → `feature/FEAT-<AREA>-NN-<slug>-<repo>`
  - **Filed ticket** → `fix/task-<n>-<slug>` when `task_type` is `bug`, else `feature/task-<n>-<slug>`. There is no `FEAT-<AREA>-NN` for these, so the task number carries the identity.
- Never `main` / `master` / `staging` / `production` / `develop`. Confirm base build is green in target repo. Write branch name into `status.md`.

**This stage is not optional, and it runs before any file is touched.** Every change `/dev:build` makes lands on its own branch — a one-line CSS fix on a filed bug as much as a multi-repo feature. If a later gate halts the run, the branch still exists and the working tree is still clean, so nothing is stranded on `main`.

### Stage 4 — QA harness gate

**Read** `plugins/dev/commands/references/build/stage-4-qa-gate.md` and execute verbatim. Auto-bootstraps via `qa-greenfield-harness` skill if `qa/quality-gates.md` is missing / Draft.

### Stages 5 + 6 — Implementation + test writing

**Read** `plugins/dev/commands/references/build/stage-5-6-implement.md` and execute verbatim. Delegates to `dev-stack-adaptive-implementation` skill.

Local: `IN_PLANNING → IN_DEVELOPMENT` (broadcast). MC: `inProgress` (unchanged).

### Stage 7 — Execute tests locally

**Read** `plugins/dev/commands/references/build/stage-7-test-execute.md` and execute verbatim. Runs every Required gate from `qa/quality-gates.md`.

Local: `IN_DEVELOPMENT → TESTING` (broadcast). MC: `inProgress`.

### Stage 8 — Validate against parent AC + BR + TS + NFRs

**Read** `plugins/dev/commands/references/build/stage-8-validate.md` and execute verbatim. Builds `dev/acceptance-map.md`. Any `❌ fail` row → bounded repair loop (3 focused / 2 broad).

### Stage 9 — Security review (build-time, Critical-blocking)

**Read** `plugins/dev/commands/references/build/stage-9-security.md` and execute verbatim. Invokes Claude Code's `security-review` skill on the feature diff. Skipped if `--no-security-review`.

### Stage 10 — Update code-context units (`designed → implemented`)

**Read** `plugins/dev/commands/references/build/stage-10-context-update.md` and execute verbatim. Updates every owned TL unit file's frontmatter + Source References. Commits the changes.

### Stage 11 — Report summary + `local-runbook.md`

**Read** `plugins/dev/commands/references/build/stage-11-summary.md` and execute verbatim. Prints in-terminal summary + writes `dev/local-runbook.md`.

Local: `TESTING → IN_PROGRESS` (build phase done; awaits `/dev:commit`). MC: `inProgress` (unchanged).

## 4. Summary output

The Stage 11 summary IS the final output. See its reference file for the exact terminal format.

## 5. Failure surfaces

- **Any stage BLOCKED** → local state `BLOCKED`, MC `blocked`, `dev/escalation-<n>.md` written, halt. Never partial-ship.
- **Any repair loop bound exceeded** → same as above, cleanly.
- **`/dev:build` on task at `BLOCKED_ON_PLAN`** → refuse (§2 hard gate). Route to `/dev:plan --resume`.

## 6. Guardrails

- Never invent behaviour not in `implementation.md`
- Never make build-time decisions (blockers must be resolved at `/dev:plan` time)
- Never push, merge, or raise PR (that's `/dev:commit`)
- Never modify secrets or `.env` files
- Never scaffold code with a guessed stack (route to `/dev:bootstrap` for project-zero)
- Retry limits per `feature-delivery-loop/references/loop-control.md`
- Every material design choice → `DEC-###` in `shared-context/decision-log.md`
