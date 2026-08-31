## Stage 4 — Compose + MC push (v2.3 refactor — was Stage 2)

**Purpose.** Read the Stage 2 analysis scratchpad + the TL context graph, produce a COMPLETE `implementation.md` (all 10 sections filled in ONE pass via `tl-feature-compose`), write `description.md` (professional 6-section format), write `status.md`, and push to MC. Two branches: **split** (composes one sub-task per repo, creates sub-tasks in MC, writes parent rollup) or **parent-alone** (composes parent Implementation as a full 10-section spec).

**v2.3 refactor rationale:** in v2.2 this ran BEFORE analysis and blocker detection — pushed a half-baked `implementation.md` to MC with sections 2/3/8/9 as stubs, filled later locally. In v2.3, analysis runs FIRST (Stage 2), blocker detection runs on the analysis (Stage 3), and only after clean → this stage composes ONE complete file with all sections populated from real analysis. MC's Implementation tab sees the finished document, not a stub.

**Runs per-feature × per-task after Stage 3 clears (no blockers OR --resume fold succeeded).** Parallelised across features (outer axis) and — within a split feature — across sub-tasks (inner axis).

**On completion:** each task's local files exist (`{description, implementation, status}.md`) AND MC has been written (unless `--dry-run`).

---

### 4a. Hard preconditions (v2.3 — MUST all pass or refuse to run)

Before Stage 4 runs on this task:

1. Stage 1 finished with `stage_1.status: DONE` in this feature's `dev/plan-run.md`.
2. Stage 2 finished with `stage_2.tasks.<this-task>.scratchpad_written` naming a file that exists:
   - Parent-alone: `features/<slug>/dev/analysis.md`
   - Sub-task: `features/<slug>/dev/<repo>-analysis.md`
3. The scratchpad has `doc_type: analysis-scratchpad` in frontmatter + non-empty `build_sequence`, `impact_matrix`, `test_strategy`, `risks_and_rollback` blocks.
4. Stage 3 finished with `stage_3.tasks.<this-task>.state_set: PROCEED_TO_STAGE_4` (blockers cleared or absent). If `dev/<repo>-plan-blockers.md` exists, its frontmatter `status:` must be `RESOLVED`.
5. The consolidated user checkpoint (§4 of `plan.md`) said `Y` for this feature.
6. `stage-1-results.split_decision.repos_touched` + `task_type` present in `plan-run.md`.

**If any precondition fails → abort THIS task's Stage 4 with a `stage_4_precondition_failed` error naming exactly which precondition + which file** (do NOT halt the batch, do NOT write a partial `implementation.md`, do NOT push to MC). Log to `plan-run.md` under `stage_4.tasks.<this-task>.status: HALTED` with reason.

---

### 4b. Sub-task decision rule

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

### 4c. Compose branch A — sub-tasks needed

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
jetrix_subtask_object_id: null            # filled by MC push (§4e)
jetrix_subtask_number: null               # filled by MC push (§4e)
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

### 4d. Compose branch B — parent alone

**Single tl-agent subagent** running `tl-feature-compose` in **`implementation` mode** on the parent. Reads BOTH the TL context units AND `dev/analysis.md` scratchpad. Output → `.jetrix/features/<slug>/implementation.md` with `compose_mode: implementation` in frontmatter (v2.3 — parent-alone Implementation now writes to `implementation.md` at feature root, not `tl-plan.md`). Writes ALL 10 sections in one pass; §10 stubbed for /dev:build Stage 11.

Skip §4e's `subtask_upsert_bundle` call — there are no sub-tasks. Proceed directly to §4f (parent Implementation push).

---

### 4e. MC push — sub-task creation

**Only in split branch (§4c). Skip in `--dry-run` mode.**

Build the `subtask_upsert_bundle` payload from each sub-task's local files. **Send the payload verbatim — do NOT modify or omit fields based on tool-schema optionality hints.** task-mcp is the translation boundary between the plugin's convention and MC's whitelisted schema.

**Payload shape (unchanged since v2.1):**

```python
task-mcp.subtask_upsert_bundle(
  solution_id    = <from .jetrix/project.json>,
  parent_task_id = <feature.md frontmatter jetrix_task_object_id>,   # ← THIS is the parent link
  subtasks = [                                                        #   (task-mcp resolves to URL :taskId)
    {
      subtask_object_id: None,                              # None = create; existing id triggers PUT (idempotency)
      title:             "<parent title> — <repo>",         # e.g. "Supplier Onboarding — backend"
      description:            <description.md body verbatim, frontmatter stripped>,
      implementation_details: <implementation.md body verbatim, frontmatter stripped>,
      acceptance_criteria:    "",                           # deliberately empty — parent owns AC
      test_scenarios:         "",                           # deliberately empty — parent owns TS
      metadata: {
        externalId:       "FEAT-SUP-001-1",                 # <feature_id>-<subtask_number>
        parentExternalId: "FEAT-SUP-001",                   # SEND IT — task-mcp translates (see note below)
        subtaskNumber:    1,                                # SEND IT — task-mcp translates
        subtaskRepo:      "backend",                        # SEND IT — task-mcp translates
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

### 4e.i. Translation boundary — how task-mcp handles the payload (CRITICAL: do not second-guess)

**Parent linkage is via `parent_task_id` (the tool input parameter), NOT via `metadata.parentExternalId`.** task-mcp uses `parent_task_id` to route the write to `POST /solutions/<sid>/tasks/<parent's_taskNumber>/subtasks` — that URL path IS the parent link per MC's `createSubtask` controller. The body's `metadata.parentExternalId` is caller-convention noise that MC's Joi schema rejects.

**Since v2.3 (task-mcp `subtask_upsert_bundle` fix, commit `56c8212` on develop), task-mcp handles the metadata translation transparently:**

| Plugin field the payload sends | What task-mcp does on write | What task-mcp does on read (subtask_list) |
|---|---|---|
| `metadata.externalId` | Forwarded to MC (whitelisted) | Read from MC |
| `metadata.parentExternalId` | **Silently dropped before forwarding** — parent link is via URL path | Re-derived from parent's `metadata.externalId` (one MC lookup per listing) |
| `metadata.subtaskNumber` | **Silently dropped before forwarding** — subtask sequence is preserved by POST order (MC's monotonic `taskNumber`) | Re-derived as `index+1` after `taskNumber`-ascending sort |
| `metadata.subtaskRepo` | **Mapped to `metadata.externalSlug`** (whitelisted; 255-char cap fits repo slug) | Reversed: `externalSlug` → `subtaskRepo` on the response |
| `metadata.source: "ai"` | Forwarded (whitelisted) | Read |
| `metadata.aiGenerated: True` | Forwarded (whitelisted) | Read |

**Do NOT:**
- Manually omit `parentExternalId` / `subtaskNumber` / `subtaskRepo` from the metadata block because the tool schema marks them optional. **They ARE optional at the schema level for backward-compat and future-proofing, but the plugin should ALWAYS send them.** Omitting `subtaskRepo` in particular breaks the read-side derivation because `externalSlug` won't be set.
- Try to hand-craft an "MC-compliant" body that skips these fields. The translation is task-mcp's job, and it's already correct.
- Re-derive from tool schema hints. The schema is intentionally permissive; the caller convention is prescriptive.

**Do:**
- Send the payload exactly as `assemble-features.py` builds it (per §4e above).
- Trust `parent_task_id` as the parent link. It's the only field that matters for the URL.
- If the MC push still fails with "metadata.X is not allowed", task-mcp isn't running the fixed version (`develop` at 56c8212 or later). Restart it; don't work around it in the plugin.

### 4e.ii. Making the call

**Idempotency check first (§6d in the plan doc):** call `task-mcp.subtask_list(solution_id, parent_task_id)` before upsert. For each existing sub-task, match on `metadata.externalId`:
- Match found → include the returned `task_object_id` in the upsert payload's `subtask_object_id` field → PUT (update in place)
- No match → leave `subtask_object_id: None` → POST (create)
- Unchanged content (matching `_local_content_hash` in sync-state) → skip entirely, mark as `skipped_unchanged` in the response

**Idempotency + content-hash skip cuts re-run wall-clock to near-zero** on features where nothing changed.

**Response handling.** For each result row (`ok: True`):
- Write back into that sub-task's frontmatter (`description.md`, `implementation.md`, `status.md`):
  - `jetrix_subtask_object_id: <task_object_id>`
  - `jetrix_subtask_number: <task_number>` (e.g. `Subtask-7`)
- Update sync-state `subtasks/<subtask_object_id>` entry (see §4g)

For rows `ok: False` — log the error, mark that sub-task `BLOCKED_MC_PUSH` in its `status.md`, continue with the others (per-item isolation).

---

### 4f. MC push — Implementation tab writes

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

### 4g. Sync-state update

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

### 4h. `--dry-run` mode

Skips §4e and §4f entirely. Composes locally (§4c or §4d) and writes files to disk with `jetrix_subtask_object_id: null` and `jetrix_subtask_number: null`. Prints:

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
