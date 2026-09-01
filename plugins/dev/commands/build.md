---
description: Build a planned task through the full 11-stage loop — branch, QA harness gate (auto-bootstraps greenfield via qa-greenfield-harness), implement per implementation.md using dev-stack-adaptive-implementation (dynamic per stack, reads repo conventions, matches idiomatic patterns), write stack-adaptive tests, execute them locally, validate against parent's Acceptance Criteria + Business Rules + Test Scenarios + NFRs, run a scoped security review (feature-diff only, Critical-blocking at build-time; /dev:commit is stricter), update code-context units to origin:implemented, and produce a summary + local-runbook.md. Bounded fix loop until 100% or escalation. Refuses to run without a /dev:plan-generated plan OR with unresolved plan-blockers.md. Accepts any task identifier (MC task number, feature slug or folder, sub-task folder, FEAT-<AREA>-NN). Sub-task builds work in the sub-task's repo only, on a branch named feature/FEAT-<AREA>-NN-<slug>-<repo>. Never merges, never pushes, never raises a PR — /dev:commit does that.
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | features/<slug>/subtask/<repo> | FEAT-<AREA>-NN | (blank = next PLANNED task)> [initiative=<name>] [--resume] [--no-security-review]"
---

# /dev:build

You are the entry point for the 11-stage build loop. **Orchestrator only** — this file parses args, resolves identity, verifies the plan + no unresolved blockers, then routes each stage to its reference file under `plugins/dev/commands/references/build/`. Do NOT paraphrase the stage files' instructions — `Read` them and execute verbatim.

Read the **`delivery-os-conventions`** skill first if it's not in context — the v2.2 loop-control state model + MC status mapping. Then read the task's plan (produced by `/dev:plan`).

**The single invariant:** `/dev:build` runs on a decidable plan or refuses. Never prompts the user mid-run.

---

## 1. Parse arguments

`$ARGUMENTS` may contain:

**Task target** (required, unless blank for "next PLANNED"):
- MC task number: `Task-N`, `Feature-N`, `Subtask-N`
- Local feature slug: `supplier-onboarding`
- Local feature folder: `features/supplier-onboarding`
- Sub-task folder: `features/supplier-onboarding/subtask/backend`
- Internal id: `FEAT-<AREA>-NN`
- Blank: pick next task at `PLANNED` from `features/tracker.md`

**Flags:**
- `initiative=<name>` — scope selection to one work-batch
- `--resume` — continue from last completed stage per `dev/build-run.md`
- `--no-security-review` — skip Stage 9's diff security review (dev-time convenience; `/dev:commit` always runs security)

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

- Missing → halt with `blocker: quality-gates-missing`. Point at `/dev:plan` §1e QA-check with skip prompt: user must re-run `/dev:plan` and either author gates for existing repo OR choose Skip (which writes a `Stack-Inferred` marker file with tier pools).
- Present, `harness_status: Ready` → strict mode. Read Required tiers per capability class. Rule 7 in `dev-stack-adaptive-implementation` writes tests at every declared tier for every §1 step. Log `qa_gate_state: Ready` to `build-run.md`.
- Present, `harness_status: Stack-Inferred` → soft mode. Tier pools were inferred from stack detection at plan time; NEW feature coverage is still 100% at every applicable tier from the inferred pool. Rule 7 writes tests at every inferred tier. Log `qa_gate_state: Stack-Inferred` + `stack_inferred_from: <source>` to `build-run.md`. Print a one-line warning: `qa/quality-gates.md is Stack-Inferred (user skipped QA setup at /dev:plan). Existing repo coverage is not audited; new feature will get 100% coverage at inferred tiers. Backfill existing coverage via /qa:audit → /qa:plan → /qa:setup when convenient.`
- Present, `harness_status: Draft` or `Broken` → halt with `blocker: quality-gates-not-ready`. Point at `/qa:health` for Broken; `/qa:setup` for Draft.

The Stack-Inferred path is the intentional escape hatch for teams that want to plan+build a new feature WITHOUT first backfilling test coverage on an existing codebase. The NEW feature still gets 100% coverage at every applicable tier — the inference just skips the audit-of-existing-code step. Backfill of existing coverage is deferred to a later `/qa:audit → /qa:plan → /qa:setup` run.

## 3. Route to stages 1–11 (serial per task; resume-aware)

For the resolved target, spawn ONE build-loop worker per task (parent-alone → 1; sub-task → 1). No cross-task parallelism at build-time — each `/dev:build` targets one task.

Read each stage's reference file and execute verbatim. Stages 1–3 (mount + preflight + branch) are inline in this command file below; Stages 4–11 delegate.

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
- Never `main` / `master` / `staging` / `production` / `develop`. Confirm base build is green in target repo. Write branch name into `status.md`.

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
