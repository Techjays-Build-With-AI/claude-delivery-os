## Stage 2 — Implementation preparation

**Purpose.** Turn the graph (verified in Stage 1) into MC-ready content. Two branches: **split** (composes one sub-task per repo, creates sub-tasks in MC, writes parent rollup) or **parent-alone** (composes parent Implementation as a full 5-section spec).

**Runs per-feature after Stage 1 succeeds AND the user confirmed at the consolidated checkpoint.** Parallelised across features (outer axis) and — within a split feature — across sub-tasks (inner axis).

**On completion:** each task's local files exist AND MC has been written (unless `--dry-run`).

---

### 2a. Preconditions

Before Stage 2 runs on this feature:

1. Stage 1 finished with `stage-1.status: DONE` in this feature's `dev/plan-run.md`.
2. The consolidated user checkpoint said `Y` for this feature (either the whole batch confirmed, or this feature was in `pick=N,M,...`).
3. `stage-1-results:` block in `dev/plan-run.md` has `repos_touched` + `task_type`.

If any precondition is missing → abort THIS feature's Stage 2 (do NOT halt the batch), log to `plan-run.md` with reason.

---

### 2b. Sub-task decision rule

Deterministic. Same rule stated in the plan document and the `delivery-os-conventions` skill:

| Condition | Result | Reason |
|---|---|---|
| `taskType == bug` | Parent alone | Bugs are point fixes — MC's `PLANNING_NOT_REQUIRED_TYPES` includes bug |
| `taskType == story` | Parent alone | Small work — MC's `PLANNING_NOT_REQUIRED_TYPES` includes story |
| `taskType == feature / epic / task` AND `repos == 1` | Parent alone | Nothing to split across |
| `taskType == feature / epic / task` AND `repos ≥ 2` | Split — one sub-task per repo | Multi-repo work has natural per-team boundaries |
| `--split` flag on the invocation | Force split | User override |
| `--no-split` flag on the invocation | Force parent alone | User override |

Write rule + reasoning to:
- `features/<slug>/subtask/task-decision.md` **when split**
- `features/<slug>/dev/task-decision.md` **when parent-alone**

Format:

```yaml
---
doc_type: task-decision
schema_version: 1.0
produced_by: dev
feature_id: FEAT-SUP-001
decided_at: 2026-08-29T14:31:12Z
---

# Task decision

**Decision:** split (3 sub-tasks — backend, frontend, mobile)

## Signals
- MC task type: feature
- Repos touched: backend, frontend, mobile (from Stage 1 unit resolution)

## Rule applied
`taskType == feature/epic/task AND repos ≥ 2 → Split, one sub-task per repo`

## Planned sub-tasks
| # | Repo     | Local path                                       | Owned units                           |
|---|----------|--------------------------------------------------|---------------------------------------|
| 1 | backend  | features/supplier-onboarding/subtask/backend/    | EP-SUP-01, EP-SUP-02, ENT-SUP-01      |
| 2 | frontend | features/supplier-onboarding/subtask/frontend/   | PAGE-SUP-01, PAGE-SUP-02              |
| 3 | mobile   | features/supplier-onboarding/subtask/mobile/     | PAGE-SUP-M01                          |

## Overrides
None. (This file records any `--split`/`--no-split` used.)
```

---

### 2c. Compose branch A — sub-tasks needed

**Invariant — sub-task type stays `subtask`.** Every sub-task created here MUST carry `taskType: subtask` in its MC payload. Never converted to `feature`, `epic`, `task` at any point. MC's parent-child hierarchy carries the relationship; converting the type would break `subtask_list` lookups and hide sub-tasks from MC's UI breadcrumb (`Feature-4 → Subtask-7`).

**Parallel per repo — N concurrent `tl-agent` subagents.** For each repo, spawn one `tl-agent` subagent to run the `tl-feature-compose` skill **twice**:

1. **Narrative mode** → sub-task **Description** (one to two paragraphs of business flow narrative, no framework/paths/HTTP codes; see the skill's §narrative).
2. **Detailed mode, scoped to that repo's units only** → sub-task **Implementation** (full 5-section template — Build sequence, API endpoints, Database mods, Frontend UI, Touch points).

Each subagent writes to disk directly:

- `.jetrix/features/<slug>/subtask/<repo>/description.md`
- `.jetrix/features/<slug>/subtask/<repo>/implementation.md`

Frontmatter shape per the skill's `references/implementation-plan-template.md` §narrative and §detailed. `inputs_hash` = sha256 over the sub-task's own inputs (parent files + this sub-task's owned unit bodies) — different from parent's hash.

**Also write** `.jetrix/features/<slug>/subtask/<repo>/status.md`:

```yaml
---
doc_type: subtask-status
schema_version: 1.0
produced_by: dev
feature_id: FEAT-SUP-001
parent_task_object_id: 6a61...
parent_task_number: Feature-4
subtask_number: 1
subtask_repo: backend
jetrix_subtask_object_id: null            # filled by MC push (§2e)
jetrix_subtask_number: null               # filled by MC push (§2e)
composed_at: 2026-08-29T14:31:47Z
---
current_state: PLANNED
owner_lock: null
branch: null
```

**After all N sub-task subagents return successfully:**

Sequential: compose the **parent's rollup**. One call to `tl-feature-compose` in **rollup mode** on the parent — reads each sub-task's `description.md` + `implementation.md` + frontmatter to build the Sub-tasks table (rows sorted by `subtask_number`; `Depends on`/`Blocks` derived from cross-sub-task references found in each Implementation's Touch points).

Write to `.jetrix/features/<slug>/tl-plan.md` with `compose_mode: rollup` in frontmatter.

---

### 2d. Compose branch B — parent alone

**Single tl-agent subagent** running `tl-feature-compose` in **detailed mode** on the parent. Output → `.jetrix/features/<slug>/tl-plan.md` with `compose_mode: detailed` in frontmatter. Behavior unchanged from what `/tl:compose` used to do.

Skip §2e's `subtask_upsert_bundle` call — there are no sub-tasks. Proceed directly to §2f (parent Implementation push).

---

### 2e. MC push — sub-task creation

**Only in split branch (§2c). Skip in `--dry-run` mode.**

Build the `subtask_upsert_bundle` payload from each sub-task's local files:

```python
task-mcp.subtask_upsert_bundle(
  solution_id    = <from .jetrix/project.json>,
  parent_task_id = <feature.md frontmatter jetrix_task_object_id>,
  subtasks = [
    {
      subtask_object_id: None,                              # None = create; existing id triggers PUT (idempotency)
      title:             "<parent title> — <repo>",         # e.g. "Supplier Onboarding — backend"
      description:            <description.md body verbatim, frontmatter stripped>,
      implementation_details: <implementation.md body verbatim, frontmatter stripped>,
      acceptance_criteria:    "",                           # deliberately empty — parent owns AC
      test_scenarios:         "",                           # deliberately empty — parent owns TS
      metadata: {
        externalId:       "FEAT-SUP-001-1",                 # <feature_id>-<subtask_number>
        parentExternalId: "FEAT-SUP-001",
        subtaskNumber:    1,
        subtaskRepo:      "backend",
        source:           "ai",
        aiGenerated:      True
      },
      status: "todo",                                       # "blocked" if compose flagged HELD
      _local_content_hash: <sha256 of description.md + implementation.md>
    },
    ...
  ]
)
```

**Idempotency check first (§6d in the plan doc):** call `task-mcp.subtask_list(solution_id, parent_task_id)` before upsert. For each existing sub-task, match on `metadata.externalId`:
- Match found → include the returned `task_object_id` in the upsert payload's `subtask_object_id` field → PUT (update in place)
- No match → leave `subtask_object_id: None` → POST (create)
- Unchanged content (matching `_local_content_hash` in sync-state) → skip entirely, mark as `skipped_unchanged` in the response

**Idempotency + content-hash skip cuts re-run wall-clock to near-zero** on features where nothing changed.

**Response handling.** For each result row (`ok: True`):
- Write back into that sub-task's frontmatter (`description.md`, `implementation.md`, `status.md`):
  - `jetrix_subtask_object_id: <task_object_id>`
  - `jetrix_subtask_number: <task_number>` (e.g. `Subtask-7`)
- Update sync-state `subtasks/<subtask_object_id>` entry (see §2g)

For rows `ok: False` — log the error, mark that sub-task `BLOCKED_MC_PUSH` in its `status.md`, continue with the others (per-item isolation).

---

### 2f. MC push — Implementation tab writes

**Skip in `--dry-run` mode.**

Two cases:

**Split feature — push parent's rollup + each sub-task's implementation:**

Sequential calls (parent first, then sub-tasks in `subtask_number` order):

```python
# 1. Parent rollup
task-mcp.feature_update_implementation(
  task_object_id       = <parent's jetrix_task_object_id>,
  implementation_details = <tl-plan.md body verbatim, frontmatter stripped>,
  status               = "readyForDev"
)

# 2..N+1. Each sub-task's Implementation
for sub in subtasks_sorted_by_number:
  task-mcp.feature_update_implementation(
    task_object_id       = sub.jetrix_subtask_object_id,
    implementation_details = <sub's implementation.md body verbatim>,
    status               = "todo"
  )
```

**Parent-alone feature — push parent's Implementation only:**

```python
task-mcp.feature_update_implementation(
  task_object_id       = <parent's jetrix_task_object_id>,
  implementation_details = <tl-plan.md body verbatim, frontmatter stripped>,
  status               = "readyForDev"
)
```

**Note.** If Dharma confirms `feature_update_implementation` accepts sub-task object_ids (see the task-mcp addition spec), the above works verbatim. If not, replace step 2..N+1 with `subtask_update_implementation` (identical signature).

---

### 2g. Sync-state update

After all MC calls succeed, update `.jetrix/cache/sync-state.json` (merge-safe, one key at a time):

**Parent-alone:**

```json
{
  "tasks/FEAT-SUP-001": {
    "implementationHash": "sha256:...",
    "version":            <from response>,
    "lastPushed":         "<ISO>"
  }
}
```

**Split — one entry per sub-task (in addition to parent's tasks/ entry):**

```json
{
  "subtasks/<subtask_object_id>": {
    "taskNumber":         "Subtask-7",
    "taskObjectId":       "<subtask_object_id>",
    "parentTaskObjectId": "<parent_task_object_id>",
    "featureId":          "FEAT-SUP-001",
    "subtaskRepo":        "backend",
    "subtaskNumber":      1,
    "contentHash":        "sha256:...",             // description.md + implementation.md
    "implementationHash": "sha256:...",             // implementation.md alone
    "version":            <from response>,
    "lastPushed":         "<ISO>"
  }
}
```

---

### 2h. `--dry-run` mode

Skips §2e and §2f entirely. Composes locally (§2c or §2d) and writes files to disk with `jetrix_subtask_object_id: null` and `jetrix_subtask_number: null`. Prints:

```
✓ [dry-run] Composed 3 sub-tasks + parent rollup locally.
  Nothing pushed to MC.
  Review:
    features/supplier-onboarding/subtask/backend/description.md
    features/supplier-onboarding/subtask/backend/implementation.md
    features/supplier-onboarding/subtask/frontend/description.md
    ...
    features/supplier-onboarding/tl-plan.md    (rollup)

  Re-run without --dry-run to push, or delete local files to redo.
```

`--resume` does not re-do a `--dry-run` — the user must re-invoke explicitly.

---

### 2i. Failure handling — per-feature isolation

Same isolation model as Stage 1:

- **All N sub-task composes fail** → feature `BLOCKED_STAGE_2`, log escalation, drop from Stage 3, continue batch
- **Some sub-tasks compose OK, some fail** → push the successful ones to MC, mark the failed ones `BLOCKED_MC_PUSH`, feature partially complete — surface in batch summary
- **MC push fails (network / MC 5xx)** → sub-tasks composed but not published; write local files with null MC ids; user re-runs `/dev:plan --resume` after MC is back and MC-push retries
- **`task-mcp.subtask_upsert_bundle` returns `permission_denied`** → halt this feature only; report which permission is missing; continue batch

---

### Progress log format (`dev/plan-run.md`, per feature)

```yaml
stage-2:
  status: RUNNING                                     # RUNNING | DONE | BLOCKED | DRY_RUN_COMPLETE
  started_at: 2026-08-29T14:31:12Z
  branch: split                                       # split | parent-alone
  split_decision:
    task_type: feature
    repos: [backend, frontend, mobile]
    rule: "taskType == feature/epic/task AND repos ≥ 2 → Split"
  subtasks_composed:                                  # only in split branch
    - {number: 1, repo: backend,  narrative_ok: true, detailed_ok: true, size_narrative: 1120, size_detailed: 12400}
    - {number: 2, repo: frontend, narrative_ok: true, detailed_ok: true, size_narrative: 940,  size_detailed: 8900}
    - {number: 3, repo: mobile,   narrative_ok: true, detailed_ok: true, size_narrative: 810,  size_detailed: 6500}
  parent_rollup_composed: true
  mc_pushed:
    parent_implementation:  {ok: true, task_number: Feature-4,  version: 3}
    subtask_upserts:
      - {number: 1, task_number: Subtask-7, ok: true, action: created}
      - {number: 2, task_number: Subtask-8, ok: true, action: created}
      - {number: 3, task_number: Subtask-9, ok: true, action: created}
    subtask_implementations:
      - {number: 1, ok: true, version: 1}
      - {number: 2, ok: true, version: 1}
      - {number: 3, ok: true, version: 1}
  finished_at: 2026-08-29T14:34:22Z
```

---

### Skills / agents invoked

- **N × `tl-agent` subagents** running the **`tl-feature-compose` skill** in narrative + detailed modes (split branch). One per repo, parallel.
- **1 × `tl-agent` subagent** running `tl-feature-compose` in rollup mode (split branch), after N above complete.
- **1 × `tl-agent` subagent** running `tl-feature-compose` in detailed mode (parent-alone branch).
- **`task-mcp`** — `subtask_list`, `subtask_upsert_bundle`, `feature_update_implementation` (and `subtask_update_implementation` if separate).

Never invoke `tl-feature-planning` from Stage 2 — that's Stage 1's job. Never invoke `dev-agent` from Stage 2 — that's Stage 3's job.
