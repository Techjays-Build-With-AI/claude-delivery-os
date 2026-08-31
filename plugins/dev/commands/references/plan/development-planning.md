## Stage 3 — Development planning

**Purpose.** For each task (parent-alone OR each sub-task in a split feature), write the local development plan — pre-flight the environment, validate readiness, analyse impact across 12 dimensions, and produce a `implementation.md` that `/dev:build` picks up. The five planning stages that used to live inside `/dev:build` — relocated here so `/dev:build` starts at branch creation.

**Runs after Stage 2 finishes**, per-feature, and **per-task inside each feature** (parent-alone → 1 task; split → N sub-tasks). Parallelised across features (outer axis) and within a feature across sub-tasks (inner axis).

**On completion:** every task's `status.md` set to `PLANNED`; MC's task status updated to match; feature reported as `PLANNED` in the batch summary.

---

### 3a. Target set for this stage

Determined from `dev/plan-run.md`'s `stage-2.branch`:

- **`branch: parent-alone`** → target = 1 task (the parent). Writes go to `features/<slug>/dev/`.
- **`branch: split`** → target = N sub-tasks. Each sub-task's dev audit writes go to the ONE feature-level `dev/` folder with repo-slug prefix in the filename — e.g. `features/<slug>/dev/backend-plan-blockers.md`, `features/<slug>/dev/frontend-traceability.md`. **NO nested `subtask/` folder inside `dev/`.** **NO nested `dev/` inside `subtask/<repo>/`** either — the sub-task folder holds only the 3 MC-facing files (`description.md`, `implementation.md`, `status.md`).

**Parallel per task** — spawn N `dev-agent` subagents for the split branch; one for parent-alone.

Each subagent runs §3b (pre-flight) → §3c (readiness) → §3d (impact) → §3e (plan) → §3f (finalize) on its own task.

---

### 3b. Pre-flight — MC status + local drift (per task, 2 parallel checks)

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

### 3c. Readiness validation

Before writing any plan, confirm each item. A failure on a **critical** item means set state `BLOCKED`, write an escalation note, drop the task from the batch, continue with siblings.

| Check | Source | Critical? |
|---|---|---|
| Feature is approved / at MC `readyForDev` (local `PLANNED`) | parent's `status.md`, `feature-index.md` | ✕-critical |
| Acceptance criteria exist and are non-empty | parent's `acceptance-criteria.md` | ✕-critical |
| No blocking open question is still `Open` | parent's `open-questions.md` (Impact = "Blocks…") | ✕-critical |
| TL technical context exists for the feature's units | `<repo>/context/code-context/` + indexes | ✕-critical → **already satisfied by Stage 1** (planning gate); revalidate quickly, don't repeat the full check |
| Dependencies are available or explicitly mockable | parent's `dependencies.md`, integration-register | ✕-critical |
| A usable product repository exists for THIS task's repo; base build is green | product repo (`git status`, build) | ✕-critical → **project-zero** routes to bootstrap (§3c.i), not a plain block |
| A usable test harness exists; quality gates are defined | `qa/quality-gates.md` (`harness_status: Active`) | ✕-critical → **no harness** routes to QA (§3c.ii), not a plain block |
| Required env vars, credentials, tools are available | repo config / environment | ✕-critical |
| Task ownership is not locked by another agent | task's `status.md` owner | ✕-critical |
| Major workflow is unambiguous | parent's `workflow.md` | non-critical → note assumption |
| Coding standards are known | `coding-standards.md` / repo conventions | non-critical → infer + note |

**Non-critical gaps:** record a marked assumption in `implementation.md` and proceed.

**Critical gaps:** escalate. Examples that must not be guessed past — no acceptance criteria, conflicting workflow definitions, unknown source of truth for data, missing API contract, missing authn/permission rules, an unresolved schema requirement, or a dependency on an unavailable external system.

**Sub-task scoping** — a sub-task inherits its readiness signal from the PARENT for shared checks (AC exist, open questions resolved). Sub-task-specific checks (repo/harness for THIS repo) apply per sub-task. This prevents duplicate work when N sub-tasks share the same parent-level fact.

Passing readiness → set task state `READY_FOR_PLAN`.

#### 3c.i. Repository gate — brownfield vs project-zero (per task's repo)

The "usable product repository" check for THIS task's repo has two failure modes:

- **Brownfield, but broken** — the repo exists yet its base build/lint/test is already red *before* changes. Genuine escalation — set `BLOCKED`, escalate.
- **Project-zero** — there is no product repository at all (no app skeleton, no build tooling) because the workspace is design-only.

For project-zero, route to bootstrap rather than plain-blocking:

1. If a confirmed architecture exists (`shared-context/architecture.md` / `technology-stack.md`) and no stack decision is missing → auto-bootstrap via the TL `tl-project-scaffold` skill (same work `/tl:scaffold` / `/dev:bootstrap` does), then re-check and continue.
2. If required stack decisions are missing → hand off to `/dev:bootstrap` (recommend-and-ask flow). Do not scaffold with a guessed stack.
3. If the TL scaffold skill isn't available → escalate: `BLOCKED`, tell the user to run `/tl:scaffold` or install the tl plugin.

The dev agent never chooses the stack itself — bootstrap executes a confirmed one and asks (with a recommendation) for the rest.

#### 3c.ii. Test-harness gate — can `/dev:build` actually verify?

Before implementing, confirm a usable test harness exists and the loop knows the bar:

1. **Read `qa/quality-gates.md`.** If it exists with `harness_status: Active` → the harness is proven and the file tells `/dev:build` Stages 7-8 which checks are **Required**, their commands, and the thresholds. Carry the required gates into `implementation.md`. Proceed.
2. **No contract, or `harness_status` is `Draft`/`Broken`** → not a per-feature bug (it blocks every feature); the fix — which frameworks, what coverage floor — is a QA strategy decision. In v2.2, `/dev:build` Stage 4 auto-bootstraps a greenfield harness via `qa-greenfield-harness` inline (deterministic, no prompts) — plan proceeds normally. Note in the plan summary that harness was Draft/missing → will be auto-bootstrapped at build. If the QA plugin isn't installed → degrade: fall back to detecting the repo's own tooling for this run.
3. **A `Broken` harness** (Required gate red before changes) → genuine escalation — `BLOCKED`, tell the user to run `/qa:health` and fix the harness first.

The dev agent never designs the test strategy itself — QA owns that.

---

### 3d. Impact analysis

Identify what this task actually touches, at the file/module level where you can name it, and write to `implementation.md §3 Impacted components` (parent's `dev/` OR sub-task's `dev/`). Walk every dimension — mark `N/A` where a dimension doesn't apply rather than dropping it:

- **Frontend** — pages and components (map to the TL `PAGE-<AREA>-NN` units this task owns)
- **Backend** — APIs and services (map to `EP-<AREA>-NN`)
- **Database** — schema, tables/collections, migrations (map to `ENT-<AREA>-NN` → `DATA-###`)
- **Authn / authz** — new roles, permissions, or checks
- **Third-party integrations** — external APIs/services (cite `INT-###`)
- **Background jobs / queues** — scheduled or async work
- **Notifications** — email, push, in-app
- **Monitoring / observability** — logs, metrics, traces, alerts
- **Existing tests** — which suites cover or must extend to cover the change
- **Documentation** — what needs updating
- **Feature flags** — gating for rollout
- **Analytics / event tracking** — events to emit

Ground each entry in a real file/route/entity where possible; the TL graph and the codebase are your evidence. A schema or migration impact that risks data loss, or an integration whose contract you can't find, is an escalation — flag it here and raise it.

**Sub-task scoping** — a sub-task's impact analysis covers only the units it owns (in its repo). Cross-task impact — "this sub-task depends on task 1 (backend) creating the endpoint" — belongs in the `Dependencies on other features or teams` section of `implementation.md` (§3e), not in impact.

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

### 3e. Implementation planning

Write or refresh `implementation.md` (parent's `dev/` OR sub-task's `dev/`). It must be actionable enough for another developer or agent to pick up mid-stream. Include:

- **Ordered implementation steps** — the sequence you'll build in (usually: data model/migration → backend endpoints → frontend pages → wiring → notifications/jobs → tests → edge cases), each tied to the TL units and the parent acceptance criteria it satisfies.
- **Affected files or modules** — concrete paths from the impact analysis.
- **Required API changes** — new/changed endpoints, request/response shapes (reuse the TL `EP-` contracts; don't reinvent them).
- **Required schema changes** — new columns/tables/indexes and the migration approach, with rollback.
- **Test strategy** — which acceptance criteria are covered by unit vs integration vs e2e, and what evidence each produces. **Sub-task:** which parent ACs THIS sub-task can validate on its own (single-layer), and which are E2E and can only be closed after all sub-tasks land (marked `deferred-to-e2e`).
- **Rollback considerations** — how to reverse the change safely (migration down, flag off).
- **Risks and assumptions** — including every non-critical readiness assumption you carried forward.
- **Validation criteria** — the exact checks that will constitute "done" for this task.
- **Estimated complexity** — Low / Medium / High, with the driver.
- **Dependencies on other features or teams** — cross-feature ordering, shared units, external teams. **Sub-task:** also cross-sub-task ordering ("depends on task 1 backend endpoint existing").

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

### 3e.5 — Blocker detection (v2.2, before finalise)

**After §3e writes `implementation.md` + `implementation.md §3 Impacted components`, run blocker detection.** This is what makes `/dev:build` safe to run without prompts — every plan-time decision that would need user input is surfaced here.

**Read [`blocker-detection.md`](blocker-detection.md) and execute verbatim on THIS task.**

Two possible outcomes per task:

- **No blockers detected** → continue to §3f Finalise (task lands at `PLANNED` / MC `readyForDev`).
- **Blockers detected** → the reference file writes `dev/plan-blockers.md` (`status: OPEN`), sets `status.md` `current_state: BLOCKED_ON_PLAN`, pushes MC status `blocked`. **HALT §3f for this task** — it does NOT reach `PLANNED`. Print the halt message from `/dev:plan` §6c. Siblings continue in parallel.

**On `/dev:plan --resume`** — before running §3e (impact/dev-plan) at all, check for `dev/plan-blockers.md`:

- **Exists, `status: OPEN` or `RESOLVING`** → read [`blocker-fold.md`](blocker-fold.md) and execute verbatim.
  - Fold succeeds (all PBs had Resolutions, all folds applied) → file → `RESOLVED`, task → `PLANNED`, MC → `readyForDev`. Proceed to §3f finalise.
  - Fold partially succeeds (some PBs still unresolved) → halt with the §6d partial-resolution message. Task stays `BLOCKED_ON_PLAN`.
  - Fold error (target file/section missing) → per `blocker-fold.md` §6.4, halt this task; siblings continue.
- **Exists, `status: RESOLVED`** → nothing to fold; continue to §3f finalise.
- **Doesn't exist** → normal resume; re-run detection (§3e.5) at the end of §3e as usual.

**Idempotency:** re-running a plain `/dev:plan` (not `--resume`) on a task with an existing `plan-blockers.md` never wipes the file. Per `blocker-detection.md` §5.8, new blockers append to the file; user's Resolutions are preserved.

---

### 3f. Finalise — status transition + MC push

For each task **whose §3e.5 came back clean** (no blockers OR all folded):

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

- **Pre-flight halt** (§3b MC blocked or drift stop) → task `BLOCKED_STAGE_3`, other tasks in this feature continue; feature reports partial.
- **Readiness critical gap** → task `BLOCKED_STAGE_3` with escalation note.
- **Project-zero routing** → the feature-level bootstrap is a batch-wide concern; halt the whole batch cleanly with "run /dev:bootstrap first" (all features share the same repo state).
- **Test-harness routing** → same as project-zero; halt with "run /qa:setup first".
- **All tasks in a feature fail Stage 3** → feature `BLOCKED_STAGE_3`.
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
- **`tl-project-scaffold` skill (via delegation to tl-agent)** — only when §3c.i routes to bootstrap.

Never invoke `tl-feature-planning` from Stage 3 — that's Stage 1's job. Never invoke `tl-feature-compose` from Stage 3 — that's Stage 2's job.

---

### Transition to `/dev:build`

At end of Stage 3:

- Every task has: `status.md`, `implementation.md §3 Impacted components`, `implementation.md` in its `dev/` folder (parent's or sub-task's).
- Every task has `current_state: PLANNED` locally and `status: readyForDev` on MC.
- `/dev:build <task-id>` will resolve the task via Stage 0 identity resolution (same as `/dev:plan`), find the pre-existing plan, and start at branch creation.

`/dev:plan` is complete for this feature. The orchestrator (`plan.md`) proceeds to the batch summary.
