# task-mcp — sub-task additions required by `/dev:plan`

> **Audience:** Dharma / task-mcp maintainer
> **Consumer:** `/dev:plan` command in the `dev` plugin (see [dev-plan-command.md](dev-plan-command.md))
> **MC side is ready.** MC already exposes sub-task endpoints, has the `taskType: subtask` enum value, `parentTaskId` field, and the 4-tab `TASK_TYPE_TAB_CONFIG['subtask']` shape (description, acceptanceCriteria, testScenarios, implementationDetails). See:
> - [jetrix-mission-control/src/routes/taskManagement.routes.ts](../../../jetrix-mission-control/src/routes/taskManagement.routes.ts) — the sub-task endpoints
> - [jetrix-mission-control/src/schemas/task.schema.ts](../../../jetrix-mission-control/src/schemas/task.schema.ts) — `parentTaskId`, `subtasks[]`, `subtasksNeeded`
> - [jetrix-mission-control/src/types/taskTabConfig.ts](../../../jetrix-mission-control/src/types/taskTabConfig.ts) — `subtask: [description, acceptanceCriteria, testScenarios, implementationDetails]`
>
> **task-mcp side is empty.** `grep subtask plugins/task-mcp/` returns nothing. We need three tools (or two + reuse of one existing). This document is the spec — no implementation preferences beyond "match existing task-mcp patterns."

---

## Why we need these

`/dev:plan` (see [dev-plan-command.md](dev-plan-command.md)) is a new command that runs just-in-time before `/dev:build`. On a multi-repo feature it decides to split the parent Task into one **sub-task per repo**, composes each sub-task's Description (business flow narrative) + Implementation (detailed 5-section spec), and pushes them into MC. On a single-repo or bug/story task, it composes the parent Task's Implementation tab as a full detailed spec (current behavior).

Today's task-mcp exposes:
- `feature_upsert_bundle` — parent tasks (7 BA tabs)
- `feature_update_implementation` — narrow Implementation-only writer
- `task_upsert_bundle` — generic tasks
- `feature_pull_bundle` / `task_pull_bundle` — reads

None of these handles sub-tasks. We need the three tools below.

---

## Tool 1 — `subtask_upsert_bundle` (create/update)

**Purpose:** batch create-or-update sub-tasks under one parent. Called once per parent per `/dev:plan` run.

**Input:**

```python
subtask_upsert_bundle(
  solution_id:    str,                       # Solution _id (from .jetrix/project.json)
  parent_task_id: str,                       # Parent Task's Mongo _id (task_object_id)
  subtasks: list[
    {
      # Identity (client-driven)
      subtask_object_id: Optional[str],      # Present on UPDATE, omitted on CREATE.
                                             # When present, PUT that specific sub-task.
                                             # When absent, POST (find-or-create by
                                             # metadata.externalId — see idempotency below).
      title:            str,                 # e.g. "Supplier Onboarding — backend"

      # Tab content (maps 1:1 to MC's subtask tab schema)
      description:            str,           # HTML/Markdown, sub-task Description tab
      implementation_details: str,           # HTML/Markdown, sub-task Implementation tab
      acceptance_criteria:    Optional[str], # Usually omitted — parent owns AC.
                                             # When provided, MC writes it verbatim.
      test_scenarios:         Optional[str], # Usually omitted — parent owns TS.

      # Metadata (carries reverse mapping for cold-pull reconstruction)
      metadata: {
        externalId:       str,               # e.g. "FEAT-SUP-001-1" — stable per sub-task,
                                             # used as the idempotency key
        parentExternalId: str,               # e.g. "FEAT-SUP-001" — matches parent.metadata.externalId
        subtaskNumber:    int,               # 1..N execution sequence within parent
        subtaskRepo:      str,               # repo slug, e.g. "backend" / "frontend" / "mobile"
        source:           "ai",              # matches feature_upsert_bundle convention
        aiGenerated:      True
      },

      # Status
      status: str,                           # "todo" (default) | "blocked" (if the compose flagged HELD)

      # Optional
      priority: Optional[str],
      expected_version: Optional[int],       # Optimistic concurrency; matches existing pattern

      # Local echo-through (task-mcp forwards unchanged in response)
      _local_content_hash: str               # sha256 of the assembled payload; used by
                                             # apply-*-responses.py to update sync-state
    },
    ...
  ]
)
```

**Server-side behavior:**

- **Enforce `taskType: subtask`** on every created/updated task in this call. Under no circumstances create these as `feature` / `task` / any other type. If MC's create endpoint accepts `taskType` in the body, pass it explicitly; if it defaults it based on the sub-task route, use `POST /solutions/:solutionId/tasks/:taskId/subtasks` (parent from URL) which the MC controller treats as `subtask`.
- **Batch under the hood.** MC exposes a single-shot `POST /solutions/:solutionId/tasks/:taskId/subtasks`. Loop per sub-task server-side; expose one batched call to the client.
- **Idempotency:**
  1. Prefer `subtask_object_id` when present (client already knows the _id) → PUT.
  2. Otherwise, look up existing sub-tasks under `parent_task_id` and match on `metadata.externalId`. If a match is found → PUT. If none → POST.
  3. This ensures `/dev:plan` re-runs never create duplicate sub-tasks.
- **Per-item error isolation.** A partial-batch failure (one sub-task 4xxs, others succeed) should return each row's outcome instead of failing the whole batch. Match the shape `feature_upsert_bundle` uses for parity.

**Output:**

```python
{
  "results": [
    {
      "subtask_number":    int,              # echoed from input for correlation
      "subtask_object_id": str,              # Mongo _id (present on ok=True)
      "task_number":       str,              # MC display number, e.g. "Subtask-7"
      "version":           int,
      "action":            "created" | "updated" | "recreated",
      "ok":                bool,
      "error":             Optional[str],    # present when ok=False
      "_local_content_hash": str             # echoed back for apply-responses to write sync-state
    },
    ...
  ]
}
```

**Backed by MC endpoint:** `POST /solutions/:solutionId/tasks/:taskId/subtasks` (see `taskManagement.routes.ts:594` — `taskController.createSubtask`) for creates, and `PUT /solutions/:solutionId/tasks/:taskId` for updates.

---

## Tool 2 — `subtask_list` (read)

**Purpose:** list every sub-task under a parent. Used by:
- `/dev:plan` Stage 2 idempotency check (does this parent already have sub-tasks?)
- `/jetrix:pull scope` to reconstruct the local `subtask/<repo>/` tree from MC

**Input:**

```python
subtask_list(
  solution_id:    str,
  parent_task_id: str
)
```

**Output:**

```python
{
  "subtasks": [
    {
      "subtask_object_id": str,
      "task_number":       str,              # "Subtask-7"
      "task_type":         "subtask",        # always "subtask" — assert this
      "title":             str,
      "status":            str,              # todo | inProgress | devReview | done | blocked | reopen
      "priority":          Optional[str],
      "created_at":        str,              # ISO 8601
      "updated_at":        str,

      # Tab content — all four fields, empty string when the tab is empty
      "description":            str,
      "implementation_details": str,
      "acceptance_criteria":    str,
      "test_scenarios":         str,

      # Metadata (as written by subtask_upsert_bundle)
      "metadata": {
        "externalId":       str,
        "parentExternalId": str,
        "subtaskNumber":    int,
        "subtaskRepo":      str,
        "source":           "ai",
        "aiGenerated":      bool
      }
    },
    ...
  ]
}
```

**Backed by MC endpoint:** `GET /solutions/:solutionId/tasks/:taskId/subtasks` (see `taskManagement.routes.ts:530` — `taskController.getSubtasks`).

**Ordering:** by `metadata.subtaskNumber` ascending. If any sub-task lacks metadata (edge case — someone created it via the UI), sort those after by `task_number`.

---

## Verification — one existing tool to test, no new tool needed

### `feature_update_implementation` on a sub-task's object_id

Today this tool writes `implementationDetails` on a task by `task_object_id`. Its Pydantic schema is deliberately narrow (`task_object_id`, `implementation_details`, `status` — nothing else) so it can't clobber BA-owned tabs.

**Question for Dharma:** does the current `feature_update_implementation` accept a sub-task's `task_object_id`, or is there a server-side taskType guard restricting it to features?

**If yes** (works for sub-tasks): we reuse it verbatim. `/dev:plan` calls it once per sub-task to push each sub-task's Implementation tab. No new tool needed.

**If no** (feature-only guard): add a mirror tool with identical shape:

```python
subtask_update_implementation(
  solution_id:            str,
  subtask_object_id:      str,
  implementation_details: str,
  status:                 Optional[str]      # e.g. flip to "todo" on push, "blocked" if compose flagged HELD
)
→ { ok: bool, task_number: str, version: int, error?: str }
```

Same narrow shape, same "can't clobber other tabs" property.

---

## Sync-state key convention (client side, for reference)

`/dev:plan` and `/jetrix:push` write per-sub-task entries under a new sync-state key:

```json
{
  "subtasks/<subtask_object_id>": {
    "taskNumber":         "Subtask-7",
    "taskObjectId":       "6b72...",
    "parentTaskObjectId": "6a61...",
    "subtaskRepo":        "backend",
    "subtaskNumber":      1,
    "contentHash":        "sha256:...",       # of description.md + implementation.md
    "implementationHash": "sha256:...",       # of implementation.md alone (mirrors the parent's implementation_hash pattern)
    "version":            3,
    "lastPushed":         "2026-08-29T14:31:07Z"
  }
}
```

Consistent with existing `tasks/<feature_id>` shape. Nothing task-mcp needs to do — this is client-side plumbing.

---

## What task-mcp does NOT need to do

- **No sub-task planning/AI prediction.** MC already excludes sub-tasks from AI prediction (`PREDICTABLE_TYPES` in `taskTabConfig.ts:80` — `subtask` not in the set). Client-composed only.
- **No auto-derivation of AC/TS on sub-task.** `/dev:plan` deliberately leaves those tabs empty (parent is the validation source). Sub-task's `acceptance_criteria` and `test_scenarios` fields default to empty string on `subtask_upsert_bundle` input.
- **No sub-task-of-sub-task hierarchy.** Only one level deep. If MC ever adds nested sub-tasks, `subtask_list` can be extended, but `/dev:plan` won't emit them.

---

## Test scenarios Dharma should smoke-test after adding these

1. **Create 3 sub-tasks under a fresh parent** — `subtask_upsert_bundle` with 3 items, all `subtask_object_id` omitted → 3 POSTs, 3 results with distinct `Subtask-N` numbers.
2. **Re-run with the same 3** — `subtask_upsert_bundle` again with the same `metadata.externalId`s → 3 PUTs (idempotent), same object_ids, `action: "updated"`.
3. **List them** — `subtask_list(parent_task_id)` → returns all 3, ordered by `metadata.subtaskNumber`.
4. **Update only one's Implementation tab** — `feature_update_implementation(subtask_object_id, implementation_details, "todo")` (or `subtask_update_implementation` if separate). Confirm the sub-task's Implementation renders in the MC UI.
5. **Verify tabs empty by default** — a sub-task created without `acceptance_criteria` / `test_scenarios` shows those tabs empty in the MC UI, no phantom content.

---

## Timeline / dependency

`/dev:plan` implementation on our side will proceed in parallel. Stage 2 of `/dev:plan` will block with a clear error message *"task-mcp subtask_upsert_bundle not yet available"* until these tools land. `--dry-run` mode skips MC entirely and works today (composes locally, writes to disk, no MCP calls).

Once the tools land, `/dev:plan` picks them up automatically — no coordination needed beyond deploying the updated task-mcp.

---

## Contact

Delivery-os side: **Selvam Murugaiah** (selvam.murugaiah@techjays.com) — see `/dev:plan` design doc for the full command flow.
