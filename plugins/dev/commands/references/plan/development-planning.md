## Stage 2 — Per-task analysis (v2.3 refactor — was Stage 3)

**Purpose.** For each task (parent-alone OR each sub-task in a split feature), run the ANALYSIS that fills `implementation.md`'s sections 2, 3, 8, 9 — pre-flight the environment, validate readiness, analyse impact across 12 dimensions, and produce the build sequence + test strategy + risks. **Output goes to an intermediate scratchpad `dev/<repo>-analysis.md`** (sub-task) or `dev/analysis.md` (parent-alone). **This stage does NOT write `implementation.md` — that happens at Stage 4 AFTER blocker detection.**

**Runs after Stage 1 finishes**, per-feature, and **per-task inside each feature** (parent-alone → 1 task; split → N sub-tasks). Parallelised across features (outer axis) and within a feature across sub-tasks (inner axis).

**Why the v2.3 reorder:** in v2.2 this stage wrote `dev-plan.md` + `impacted-components.md` (two separate files) AFTER Stage 2 (compose+push) had already written a half-baked `implementation.md` and pushed it to MC. In v2.3, `implementation.md` is a single 10-section source of truth — writing it before analysis is done produces stub sections. So analysis (this stage) runs FIRST, blocker detection (Stage 2) runs on the analysis output, and compose+push (Stage 4) reads the analysis to write ALL sections in one pass.

**On completion:** every task has a `dev/<repo>-analysis.md` scratchpad with `doc_type: analysis-scratchpad` and populated `build_sequence` / `impact_matrix` / `risks_and_rollback` blocks. (v2.3.16: the former `coverage:` / `test_strategy:` block is removed — plan-time coverage lives in `build_sequence`'s `satisfies` field per row + the `qa/quality-gates.md` tier pool resolved at §1e; build-time evidence lives in `dev/acceptance-map.md`.) Task state stays PLANNED_PENDING_STAGE_3 (not written to MC — MC still shows `readyForDev`). Skill invocations logged to `plan-run.md`.

---

### 2a. Target set for this stage

Determined from `dev/plan-run.md`'s `stage-1-results.split_decision`:

- **`branch: parent-alone`** → target = 1 task (the parent). Analysis scratchpad written to `features/<slug>/dev/analysis.md`.
- **`branch: split`** → target = N sub-tasks. Each sub-task's analysis scratchpad written flat under the ONE feature-level `dev/` folder with repo-slug prefix — e.g. `features/<slug>/dev/backend-analysis.md`, `features/<slug>/dev/frontend-analysis.md`. **NO nested `subtask/` folder inside `dev/`.** **NO nested `dev/` inside `subtask/<repo>/`.**

**Parallel per task** — spawn N `dev-agent` subagents for the split branch; one for parent-alone.

Each subagent runs §2b (pre-flight) → §2c (readiness) → §2d (impact) → §2e (dev-plan) → §2f (write scratchpad) on its own task.

---

### 2b. Pre-flight — MC status + local drift (per task, 2 parallel checks)

Two independent checks fire concurrently — both consult external state so the dev-agent doesn't start on a task the team has flagged as blocked or on files the user hasn't synced.

**MC task status (halt if `blocked`):**

Skip when the target's frontmatter has no `jetrix_task_object_id` (never pushed to MC — but with Stage 2 done that should be present unless we're in `--dry-run`).

```
task-mcp.get_task_by_id_or_number(
  solution_id = <from project.json>,
  ref         = <feature.md frontmatter feature_id for parent, OR jetrix_subtask_number for sub-task>
)
→ { ok: bool, task?: { status: str, ... }, error?: str }
```

- `ok: false` → skip silently (nothing on MC to check against; can only happen in `--dry-run`).
- `ok: true AND task.status == "blocked"` → halt this ONE task cleanly:

```
✗ Task <task_number> is currently BLOCKED on Jetrix.
  Resolve the blockers locally, push updates, then re-run /dev:plan --resume for this feature.
```

Mark the task `BLOCKED_MC_STATUS`, continue with siblings.

`ok: true` with `todo | readyForDev | inProgress | agentExecuting | devReview | inQaReview | reopen | done` → continue to readiness.

**Local drift check:**

Invoke the shared drift helper (`plugins/jetrix/commands/references/drift.md`) on the target task's local files (parent's feature root for parent-alone target; `subtask/<repo>/` for a sub-task target).

- **Clean** → continue.
- **Drift** → prompt the user (this is the one Stage-3 mid-run prompt, cheap and safe):
  - `y` → plan with local as-is; note "drift ignored" in the summary
  - `s` → stop this task cleanly, tell user to `/jetrix:push` then re-run `--resume`

---

### 2c. Readiness validation

Before writing any plan, confirm each item. A failure on a **critical** item means set state `BLOCKED`, write an escalation note, drop the task from the batch, continue with siblings.

| Check | Source | Critical? |
|---|---|---|
| Feature is approved / at MC `readyForDev` (local `PLANNED`) | parent's `status.md`, `feature-index.md` | ✕-critical |
| Acceptance criteria exist and are non-empty | parent's `acceptance-criteria.md` | ✕-critical |
| No blocking open question is still `Open` | parent's `open-questions.md` (Impact = "Blocks…") | ✕-critical |
| TL technical context exists for the feature's units | `<repo>/context/code-context/` + indexes | ✕-critical → **already satisfied by Stage 1** (planning gate); revalidate quickly, don't repeat the full check |
| Dependencies are available or explicitly mockable | parent's `dependencies.md`, integration-register | ✕-critical |
| A usable product repository exists for THIS task's repo; base build is green | product repo (`git status`, build) | ✕-critical → **project-zero** routes to bootstrap (§2c.i), not a plain block |
| A usable test harness exists; quality gates are defined | `qa/quality-gates.md` (`harness_status: Active`) | ✕-critical → **no harness** routes to QA (§2c.ii), not a plain block |
| Required env vars, credentials, tools are available | repo config / environment | ✕-critical |
| Task ownership is not locked by another agent | task's `status.md` owner | ✕-critical |
| Major workflow is unambiguous | parent's `workflow.md` | non-critical → note assumption |
| Coding standards are known | `coding-standards.md` / repo conventions | non-critical → infer + note |

**Non-critical gaps:** record a marked assumption in `implementation.md` and proceed.

**Critical gaps:** escalate. Examples that must not be guessed past — no acceptance criteria, conflicting workflow definitions, unknown source of truth for data, missing API contract, missing authn/permission rules, an unresolved schema requirement, or a dependency on an unavailable external system.

**Sub-task scoping** — a sub-task inherits its readiness signal from the PARENT for shared checks (AC exist, open questions resolved). Sub-task-specific checks (repo/harness for THIS repo) apply per sub-task. This prevents duplicate work when N sub-tasks share the same parent-level fact.

Passing readiness → set task state `READY_FOR_PLAN`.

#### 2c.i. Repository gate — brownfield vs project-zero (per task's repo)

The "usable product repository" check for THIS task's repo has two failure modes:

- **Brownfield, but broken** — the repo exists yet its base build/lint/test is already red *before* changes. Genuine escalation — set `BLOCKED`, escalate.
- **Project-zero** — there is no product repository at all (no app skeleton, no build tooling) because the workspace is design-only.

For project-zero, route to bootstrap rather than plain-blocking:

1. If a confirmed architecture exists (`shared-context/architecture.md` / `technology-stack.md`) and no stack decision is missing → auto-bootstrap via the TL `tl-project-scaffold` skill (same work `/tl:scaffold` / `/dev:bootstrap` does), then re-check and continue.
2. If required stack decisions are missing → hand off to `/dev:bootstrap` (recommend-and-ask flow). Do not scaffold with a guessed stack.
3. If the TL scaffold skill isn't available → escalate: `BLOCKED`, tell the user to run `/tl:scaffold` or install the tl plugin.

The dev agent never chooses the stack itself — bootstrap executes a confirmed one and asks (with a recommendation) for the rest.

#### 2c.ii. Test-harness gate — can `/dev:build` actually verify?

Before implementing, confirm a usable test harness exists and the loop knows the bar:

1. **Read `qa/quality-gates.md`.** If it exists with `harness_status: Active` → the harness is proven and the file tells `/dev:build` Stages 7-8 which checks are **Required**, their commands, and the thresholds. Carry the required gates into `implementation.md`. Proceed.
2. **No contract, or `harness_status` is `Draft`/`Broken`** → not a per-feature bug (it blocks every feature); the fix — which frameworks, what coverage floor — is a QA strategy decision. In v2.2, `/dev:build` Stage 4 auto-bootstraps a greenfield harness via `qa-greenfield-harness` inline (deterministic, no prompts) — plan proceeds normally. Note in the plan summary that harness was Draft/missing → will be auto-bootstrapped at build. If the QA plugin isn't installed → degrade: fall back to detecting the repo's own tooling for this run.
3. **A `Broken` harness** (Required gate red before changes) → genuine escalation — `BLOCKED`, tell the user to run `/qa:health` and fix the harness first.

The dev agent never designs the test strategy itself — QA owns that.

---

### 2d. Impact analysis

Identify what this task actually touches, at the file/module level where you can name it, and write to scratchpad § `impact_matrix`. Walk every dimension — mark `N/A` where a dimension doesn't apply rather than dropping it:

- **Frontend** — pages and components (map to the TL `PAGE-<AREA>-NN` units this task owns)
- **Backend** — APIs and services (map to `EP-<AREA>-NN`)
- **Database** — schema, tables/collections, migrations (map to `ENT-<AREA>-NN` → `DATA-###`)
- **Authn / authz** — new roles, permissions, or checks
- **Integrations** — external APIs/services + outbound message-broker producers (cite `INT-###`)
- **Background jobs / queues** — scheduled or async work
- **Notifications** — email, push, in-app
- **Monitoring / observability** — logs, metrics, traces, alerts
- **Existing tests** — which suites cover or must extend to cover the change
- **Documentation** — what needs updating
- **Feature flags** — gating for rollout
- **Analytics / event tracking** — events to emit

Ground each entry in a real file/route/entity where possible; the TL graph and the codebase are your evidence. A schema or migration impact that risks data loss, or an integration whose contract you can't find, is an escalation — flag it here and raise it.

**Sub-task scoping** — a sub-task's impact analysis covers only the units it owns (in its repo). Cross-task impact — "this sub-task depends on task 1 (backend) creating the endpoint" — belongs in the `Dependencies on other features or teams` section of `implementation.md` (§2e), not in impact.

Frontmatter:
```yaml
---
doc_type: impacted-components
schema_version: 1.0
produced_by: dev
feature_id: FEAT-SUP-001
subtask_number: 1                   # OMIT for parent-alone
subtask_repo: backend               # OMIT for parent-alone
generated_at: <ISO>
---
```

---

### 2e. Implementation planning

Write or refresh the analysis scratchpad `dev/<repo>-analysis.md`. It must be actionable enough for another developer or agent to pick up mid-stream. Include:

The scratchpad feeds implementation.md's §1/§2/§7/§8 at Stage 4 (compose). Aligned block names (matches the v2.3.15 frame):

- **`build_sequence`** — the ordered steps you'll build in (data model / stored-data changes → operations exposed → user-facing surfaces → wiring → background jobs / notifications → tests → edge cases), each row citing the TL units and parent AC/BR/TS IDs it satisfies. **→ §1 Build sequence.**
- **`impact_matrix`** — 12-dimension impact map with stack-agnostic dimension names (Surfaces / Operations / Stored data / Authz / Integrations / Background jobs / Notifications / Observability / Existing tests / Docs / Flags / Analytics), each row substantive per Rule 11.12. **→ §2 Impacted components.**
<!-- v2.3.16 — the former `coverage:` block is REMOVED from the scratchpad. Every parent AC/BR/TS in scope is named in some `build_sequence` step's `satisfies:` field (or explicitly marked `not_applicable` with a layer-specific reason on the build step where it would otherwise apply, or `carried_by: sub-task-<N>` when a sibling sub-task's step covers it). The tier pool (Unit / Integration / Component / E2E / Concurrency / Accessibility / Load / Idempotency / Retry-behaviour) is resolved from `qa/quality-gates.md` at §1e — the scratchpad does not re-declare it. Build-time test evidence lives in `dev/acceptance-map.md`, not in the plan. -->
- **`risks_and_rollback`** — risks table (R-N / Risk / Severity / Mitigation-cites-AC-BR-TS-ID + applicable tier from `qa/quality-gates.md`) + Out of scope for this sub-task (max 3 bullets — each names a specific implementation NOT delivered) + two-tier rollback (cheapest lever + full). **→ §7 Risks and rollback.** No "Assumptions" heading — boring decisions (no pagination, no rate limit, no permission model) live in §3 Invariants/Authz clauses or §5 Effects/on-success clauses per Rule 11.13 §5.
- **Dependencies on other features or teams** (scratchpad-only note) — cross-feature ordering, shared units, external teams. **Sub-task:** also cross-sub-task ordering ("depends on sub-task 1 backend endpoint existing"). These land in §6 Touch points as Cross-sub-task rows, not in a standalone dependencies section.

Respect the **2 plans per task** limit. Reuse the TL contracts and schemas as given — planning is sequencing and grounding the build, not redesigning what the TL already decided. Where the plan reveals a genuinely undecided design point that changes behaviour, raise it as an open question / escalation rather than baking a guess into the plan.

Frontmatter:
```yaml
---
doc_type: dev-plan
schema_version: 1.0
produced_by: dev
feature_id: FEAT-SUP-001
subtask_number: 1                   # OMIT for parent-alone
subtask_repo: backend               # OMIT for parent-alone
generated_at: <ISO>
---
```

---

### 2e.5 — Blocker detection (v2.2, before finalise)

**After §2e writes the analysis scratchpad `dev/<repo>-analysis.md`, run blocker detection.** This is what makes `/dev:build` safe to run without prompts — every plan-time decision that would need user input is surfaced here.

**Read [`blocker-detection.md`](blocker-detection.md) and execute verbatim on THIS task.**

Two possible outcomes per task:

- **No blockers detected** → continue to §2f Finalise (task lands at `PLANNED` / MC `readyForDev`).
- **Blockers detected** → the reference file writes `dev/plan-blockers.md` (`status: OPEN`), sets `status.md` `current_state: BLOCKED_ON_PLAN`, pushes MC status `blocked`. **HALT §2f for this task** — it does NOT reach `PLANNED`. Print the halt message from `/dev:plan` §6c. Siblings continue in parallel.

**On `/dev:plan --resume`** — before running §2e (impact/dev-plan) at all, check for `dev/plan-blockers.md`:

- **Exists, `status: OPEN` or `RESOLVING`** → read [`blocker-fold.md`](blocker-fold.md) and execute verbatim.
  - Fold succeeds (all PBs had Resolutions, all folds applied) → file → `RESOLVED`, task → `PLANNED`, MC → `readyForDev`. Proceed to §2f finalise.
  - Fold partially succeeds (some PBs still unresolved) → halt with the §6d partial-resolution message. Task stays `BLOCKED_ON_PLAN`.
  - Fold error (target file/section missing) → per `blocker-fold.md` §6.4, halt this task; siblings continue.
- **Exists, `status: RESOLVED`** → nothing to fold; continue to §2f finalise.
- **Doesn't exist** → normal resume; re-run detection (§2e.5) at the end of §2e as usual.

**Idempotency:** re-running a plain `/dev:plan` (not `--resume`) on a task with an existing `plan-blockers.md` never wipes the file. Per `blocker-detection.md` §5.8, new blockers append to the file; user's Resolutions are preserved.

---

### 2f. Finalise — status transition + MC push

For each task **whose §2e.5 came back clean** (no blockers OR all folded):

1. **Write `status.md`** (parent's `dev/` OR sub-task's `dev/`):
   ```yaml
   ---
   doc_type: delivery-status
   schema_version: 1.0
   produced_by: dev
   feature_id: FEAT-SUP-001
   subtask_number: 1                   # OMIT for parent-alone
   subtask_repo: backend               # OMIT for parent-alone
   generated_at: <ISO>
   ---
   current_state: PLANNED
   owner_lock: null
   branch: null
   ready_for_dev_build: true
   ```

2. **Also update the sub-task's top-level `status.md`** (`subtask/<repo>/status.md`) to `current_state: PLANNED` (mirrors the status.md; simpler for consumers that just want to know the status).

3. **Push status to MC** (skip in `--dry-run`):
   ```python
   task-mcp.update_task_status(
     solution_id    = <from project.json>,
     task_object_id = <this task's jetrix_task_object_id OR jetrix_subtask_object_id>,
     status         = "readyForDev"
   )
   ```
   MC's status naming: `todo | readyForDev | inProgress | agentExecuting | devReview | inQaReview | reopen | done | blocked`. Our local `PLANNED` maps to MC `readyForDev`.

4. **Update parent's derived status:** re-compute parent's status from sub-task states (all PLANNED → PLANNED); write parent's `status.md`.

---

### 3g. Failure handling — per-task isolation

Same isolation model as Stages 1 & 2:

- **Pre-flight halt** (§2b MC blocked or drift stop) → task `BLOCKED_STAGE_3`, other tasks in this feature continue; feature reports partial.
- **Readiness critical gap** → task `BLOCKED_STAGE_3` with escalation note.
- **Project-zero routing** → the feature-level bootstrap is a batch-wide concern; halt the whole batch cleanly with "run /dev:bootstrap first" (all features share the same repo state).
- **Test-harness routing** → same as project-zero; halt with "run /qa:setup first".
- **All tasks in a feature fail Stage 2** → feature `BLOCKED_STAGE_3`.
- **Some tasks succeed, some fail** → the feature is partial; failed tasks reported individually.

---

### Progress log format (`dev/plan-run.md`, per feature)

```yaml
stage-3:
  status: RUNNING                                # RUNNING | DONE | BLOCKED
  started_at: 2026-08-29T14:34:22Z
  tasks:                                          # 1 for parent-alone, N for split
    - number: 1
      repo:   backend
      preflight: {mc_status: readyForDev, drift: clean}
      readiness:
        critical_gaps: []
        assumptions:  []
      impact_written:  true
      dev_plan_written: true
      status_pushed:   {ok: true, mc_status: readyForDev, version: 4}
    - number: 2
      ...
  finished_at: 2026-08-29T14:36:10Z
```

---

### Skills / agents invoked

- **`dev-agent` subagents** — one per task (parent-alone → 1; split → N), parallel.
- **`task-mcp.get_task_by_id_or_number`** — pre-flight MC status.
- **`task-mcp.update_task_status`** — final status push.
- **Shared drift helper** — `plugins/jetrix/commands/references/drift.md`.
- **`tl-project-scaffold` skill (via delegation to tl-agent)** — only when §2c.i routes to bootstrap.

Never invoke `tl-feature-planning` from Stage 2 — that's Stage 1's job. Never invoke `tl-feature-compose` from Stage 2 — that's Stage 2's job.

---

### Transition to `/dev:build`

At end of Stage 2:

- Every task has: `status.md`, `implementation.md §2 Impacted components`, `implementation.md` in its `dev/` folder (parent's or sub-task's).
- Every task has `current_state: PLANNED` locally and `status: readyForDev` on MC.
- `/dev:build <task-id>` will resolve the task via Stage 0 identity resolution (same as `/dev:plan`), find the pre-existing plan, and start at branch creation.

`/dev:plan` is complete for this feature. The orchestrator (`plan.md`) proceeds to the batch summary.
