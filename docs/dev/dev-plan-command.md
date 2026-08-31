# `/dev:plan` Command — Design & Implementation Plan

> **Status:** Draft · **Owner:** dev plugin · **Depends on:** small `task-mcp` addition (see §12)
>
> This document is the build-ready plan for a new `/dev:plan` command that splits the "planning" half out of today's `/dev:build`, adds just-in-time sub-task decomposition, and pushes each sub-task's Description + Implementation into Mission Control. It is the source of truth for the implementation; treat every §-number below as a checkable spec.

---

## 1. Purpose

Introduce `/dev:plan` as the just-in-time planning entry point on the dev side. When a developer picks up a parent task, `/dev:plan`:

1. Ensures the technical context graph (`<repo>/context/code-context/`) is present and current for the feature — auto-runs `/tl:plan` if it isn't
2. Decides whether the task needs sub-tasks (multi-repo → one sub-task per repo; bug or single-repo → parent alone)
3. Composes each sub-task's **Description** (business flow narrative) + **Implementation** (detailed 5-section spec) and creates them in MC via `task-mcp`
4. Writes a local development plan per task (readiness, impact, dev-plan.md)
5. Leaves everything at status `PLANNED`, ready for `/dev:build` to pick up

The command replaces today's implicit planning inside `/dev:build`. After this change `/dev:build` starts at branch creation and refuses to run if the plan is missing.

## 2. Command shape

**File:** [plugins/dev/commands/plan.md](../../plugins/dev/commands/plan.md) (new)

```yaml
---
description: Just-in-time planning for one or many tasks. Verifies the technical context graph is current (auto-runs /tl:plan if missing), decides whether each task needs sub-tasks (multi-repo → one sub-task per repo, single-repo or bug/story → parent alone), composes each sub-task's Description + Implementation and creates them in Mission Control, and writes the local development plan. Accepts a single MC task number (Task-N, Feature-N, Subtask-N), a local feature slug or folder path, the internal FEAT-<AREA>-NN id, or a multi-target form — an MC List name, initiative=<name>, or --all — which fans out across every matching feature in parallel. Runs 4 stages: identity resolution (expands multi-targets, prompts to /jetrix:pull if BA files are missing) → code-context readiness → implementation preparation → development planning. Two parallelism axes: across features (bounded by --concurrency, default 5) and within a feature (per-sub-task compose + per-task planning). One consolidated user checkpoint after stage 1 to confirm the split for every targeted feature. Failure of one feature never halts the batch — failed features report at the end with escalations. Never merges, never runs code — leaves each task at status PLANNED for /dev:build.
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | FEAT-<AREA>-NN | list=<name> | initiative=<name> | --all | (blank = next READY task)> [--split | --no-split] [--resume] [--dry-run] [--concurrency=N]"
---
```

**Arguments accepted (Stage 0 resolves any of them to one or many canonical targets):**

*Single-target forms* — plan one feature:

| Input form | Example | Notes |
|---|---|---|
| MC task number (parent) | `Task-1`, `Feature-4` | Primary form — this is what MC's UI shows |
| MC task number (sub-task) | `Subtask-7` | Resolves upward to its parent, then plans the whole parent |
| Local feature slug | `supplier-onboarding` | Matches `features/<slug>/` |
| Local folder path | `features/supplier-onboarding` | Same as slug |
| Internal id | `FEAT-SUP-001` | Local-only reference |
| (blank) | | Picks next task at status `READY_FOR_DEV` |

*Multi-target forms* — plan many features in parallel:

| Input form | Example | Notes |
|---|---|---|
| List name | `list="Supplier Management"` or bare `"Supplier Management"` | Every feature under that MC List |
| Initiative | `initiative=supplier-portal` | Every feature stamped with that initiative (matches `/tl:plan` and `/dev:build` convention) |
| All | `--all` | Every feature at status `READY_FOR_DEV` in the workspace |
| Combined | `--all initiative=supplier-portal` | Every feature in that initiative regardless of status |

**Flags:**

- `--split` — force sub-task creation regardless of repo count
- `--no-split` — force parent-alone regardless of repo count
- `--resume` — continue from the last completed stage recorded in `plan-run.md` (works at both batch and per-feature level)
- `--dry-run` — do everything locally; skip the MC writes (previews the plan)
- `--concurrency=N` — cap outer parallelism (features running simultaneously). Default `5`. Inner per-sub-task parallelism is separate and always on.

## 3. High-level flow (4 stages)

```
/dev:plan <target>
│
├── Stage 0 — Identity resolution + target-set expansion
│     Single-target → resolve to one (feature_id, task_object_id, task_number, feature_folder)
│     Multi-target (list / initiative / --all) → expand to an explicit list of the same tuples
│     BA-file presence check: prompt to /jetrix:pull scope inline if any feature is missing files
│
├── Stage 1 — Code-context readiness   (per feature, parallel across features)
│     Verify TL graph resolves and is linked; auto-trigger /tl:plan if not
│     ► ONE CONSOLIDATED USER CHECKPOINT: confirm the split decision for every targeted feature
│
├── Stage 2 — Implementation preparation   (per feature, parallel across features)
│     Compose Description + Implementation per sub-task (parallel per repo within each feature)
│     Create sub-tasks in MC via task-mcp
│     Compose parent Implementation (rollup mode if split, detailed if not)
│
└── Stage 3 — Development planning   (per feature × per task, parallel)
      Pre-flight, readiness, impact analysis, dev-plan.md
      Set status → PLANNED locally + MC
```

Every stage writes its progress to [.jetrix/features/<slug>/dev/plan-run.md](#8-local-file-layout) — the log a `--resume` reads at the per-feature level. A **batch summary** at `.jetrix/dev/batch-runs/plan-run-<timestamp>.md` records the whole run (targets, decisions, results, failures) — `--resume` reads this at the batch level.

**Two parallelism axes:**

- **Outer** — features run concurrently, bounded by `--concurrency` (default 5)
- **Inner** — within a feature, per-sub-task compose (Stage 2) and per-task planning (Stage 3) run concurrently

**Failure isolation.** One feature failing (bad graph, auto-plan can't complete, MC write refused) never halts the others. Failed features are collected and reported at the end with their escalation notes.

## 4. Stage 0 — Identity resolution + target-set expansion + BA-file check

**Purpose:** turn whatever the user typed into an **explicit list** of canonical targets `(feature_id, feature_folder, parent_task_object_id, parent_task_number, list_name)` — one entry for a single-target run, N entries for a batch — then guarantee every entry has its BA files locally.

### 4a. Resolve the target (first match wins)

**Single-target forms:**

1. **MC task number** (`Task-N`, `Feature-N`, `Subtask-N`)
   - Call `task-mcp.get_task_by_id_or_number(solution_id, ref)`
   - If the returned task's `taskType == subtask` → walk up to `parentTaskId`, re-fetch parent
   - Result → parent's `task_object_id` + `task_number` + `metadata.externalId` (which is our `feature_id`)
2. **Local slug or folder path** (`supplier-onboarding` or `features/supplier-onboarding`)
   - Match against `features/<slug>/` folders on disk
   - Read `features/<slug>/feature.md` frontmatter → `feature_id`, `jetrix_task_object_id`, `jetrix_task_number`
3. **Internal `FEAT-<AREA>-NN`** id
   - Grep `features/*/feature.md` frontmatter for `feature_id` match → resolves to a folder
4. **No arg**
   - Scan `features/*/status.md` for status `READY_FOR_DEV` → pick the first (or offer picker if many)

**Multi-target forms — expand to an explicit set of features:**

5. **`list=<name>`** or bare quoted string that matches a List
   - Call `task-mcp.feature_list_bundle(solution_id, list_name=<arg>)` → return every feature under that list
   - Expand → N targets
6. **`initiative=<name>`**
   - Scan `features/*/feature.md` frontmatter for `initiative: <arg>` → N targets
   - Cross-check with MC via `feature_list_bundle` if some features aren't local (feeds into §4c below)
7. **`--all`**
   - Scan `features/*/status.md` for status `READY_FOR_DEV` (default) or every feature if `--all initiative=<name>`
   - Expand → N targets

**On failure** — no match on any path — halt with the 5 nearest slugs / task numbers and exit cleanly. Never guess.

### 4b. Write resolved target set

Write the expanded target list to `.jetrix/dev/batch-runs/plan-run-<timestamp>.md` under `resolved_targets:` — one YAML entry per feature. `--resume` reads this and skips already-completed features.

### 4c. BA-file presence check (auto-detect missing files, prompt to pull)

Every targeted feature needs its 8 BA files locally at feature root for Stages 1–3 to run: `feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md`.

Sub-task files under `subtask/<repo>/` are NOT required at this check — `/dev:plan` is what creates them. But if `/dev:plan` is being re-run against a feature whose sub-tasks already exist locally (from a prior run or a `/jetrix:pull`), the existing `subtask/*/description.md` + `implementation.md` are read to preserve `<!-- KEEP -->` blocks and honour idempotency (§6d).

Walk the target set; for each feature check the parent files. If **any** feature is missing any file, print a consolidated summary and prompt once:

```
✗ Missing BA files for 2 of 5 features:
    · Feature-4  Supplier Onboarding      (missing: workflow.md, nfrs.md)
    · Feature-9  Outlet Discovery         (missing: acceptance-criteria.md)

  Pull them from Jetrix now? [Y/n]
```

- `Y` (default) → invoke `/jetrix:pull scope` inline for just the affected features (per-task pull via `task <ref>` if task-mcp supports the targeted form; else full scope pull). Re-check after. Continue with any feature now complete; mark still-missing ones as skipped.
- `n` → skip the affected features (record them in the batch summary as `SKIPPED_MISSING_BA`) and continue with the rest.

If all files present → step 4c is silent.

### 4d. Missing metadata backfill

For every target: if `feature.md` frontmatter is missing `jetrix_task_number` (older workspaces), fetch it from MC via `get_task_by_id_or_number` and patch the file inline. Non-blocking.

## 5. Stage 1 — Code-context readiness

**Reference file:** [plugins/dev/commands/references/plan/code-context-readiness.md](../../plugins/dev/commands/references/plan/code-context-readiness.md) (new)

**Purpose:** guarantee the feature's owned units (pages, endpoints, entities) all resolve to real unit files and are linked to this `FEAT-<id>` in the three layer indexes. If not, auto-plan.

**Steps (moved verbatim from [feature-delivery-loop/references/readiness-and-planning.md §0](../../plugins/dev/skills/feature-delivery-loop/references/readiness-and-planning.md)):**

1. Read `features/<slug>/feature.md` → collect declared **Related Pages**, **Related APIs**, **Related Data Entities**
2. Load the three TL layer indexes in each involved repo (**parallelised** — 3 concurrent reads per repo)
3. For each declared unit, verify:
   - **Resolves** — file exists at path the index points to
   - **Linked** — this `FEAT-id` appears in the unit's `Used by Features` cell
4. Verdict: `Planned` / `Partially planned` / `Not planned`
5. If not or partially planned → delegate to `tl-agent` subagent running `tl-feature-planning` on this one feature. Re-verify after it returns
6. If verify still fails after one plan pass → escalation → set task status `BLOCKED`, write `escalation-1.md`, halt

**Also derives — the input to the checkpoint:**

- **Repos touched** — union of `Source Reference` file paths across all owned units → set of repos via `.jetrix/cache/repolocation.json`
- **Task type** — from Stage 0's MC fetch

### 5a. USER CHECKPOINT (one consolidated prompt, whether one feature or many)

After Stage 1 succeeds across every targeted feature, print **one** consolidated proposal table and wait for **one** confirmation — never per-feature prompting:

**Single-target run:**

```
Feature: FEAT-SUP-001 Supplier Onboarding  (Feature-4 in MC)
Task type: feature
Repos touched: backend, frontend, mobile
Split decision: 3 sub-tasks
   subtask/backend    (sequence 1)
   subtask/frontend   (sequence 2)
   subtask/mobile     (sequence 3)

Proceed with sub-task creation in MC? [Y/n]
```

**Multi-target run (list / initiative / --all):**

```
Planning 5 features (concurrency=5):

  Feature-4   Supplier Onboarding      → split 3 (backend, frontend, mobile)
  Feature-7   Supplier Approval        → parent alone (1 repo: backend)
  Feature-9   Outlet Discovery         → split 2 (backend, frontend)
  Feature-12  RFP Generation           → parent alone (1 repo: backend)
  Feature-15  Reporting Dashboard      → split 2 (frontend, backend)

Total: 5 features, 10 sub-tasks to create in MC

Proceed with all? [Y/n]  or  [pick=1,3,5] to only continue with some
```

- `Y` (default) → runs Stage 2 + 3 across every feature in parallel, no more prompts
- `pick=1,3,5` → continue with only those; the rest are untouched (no MC writes)
- `n` → stops cleanly, nothing pushed to MC, no local writes beyond `plan-run.md`

`--dry-run` skips the prompt (implicit no on MC writes) and continues to Stage 2's compose so the user can review the drafts locally.

## 6. Stage 2 — Implementation preparation

**Reference file:** [plugins/dev/commands/references/plan/implementation-preparation.md](../../plugins/dev/commands/references/plan/implementation-preparation.md) (new)

**Purpose:** decide whether the task splits into sub-tasks, compose each sub-task's Description + Implementation, create them in MC, and write the parent's Implementation tab.

### 6a. Sub-task decision rule (locked)

Deterministic. Signals: MC `taskType` + repo count from Stage 1. Matches MC's own `PLANNING_NOT_REQUIRED_TYPES` set.

| Condition | Result |
|---|---|
| `taskType == bug` | Parent alone (bugs are point fixes; MC's `PLANNING_NOT_REQUIRED`) |
| `taskType == story` | Parent alone (small work; MC's `PLANNING_NOT_REQUIRED`) |
| `taskType == feature / epic / task` AND `repos == 1` | Parent alone |
| `taskType == feature / epic / task` AND `repos ≥ 2` | Split — one sub-task per repo |
| `--split` flag | Force split |
| `--no-split` flag | Force parent alone |

Rule + reasoning written to `.jetrix/features/<slug>/subtask/task-decision.md` (when split) or `.jetrix/features/<slug>/dev/task-decision.md` (when parent-alone) — the location matches where the rest of the run's artifacts land.

### 6b. Compose branch A — sub-tasks

**Invariant — sub-task type stays `subtask`.** Every sub-task created here MUST carry `taskType: subtask` in its MC payload and MUST NOT be converted to `feature`, `epic`, `task`, or any other type at any point in the lifecycle. MC's parent-child hierarchy is what carries the relationship; converting the type would break `subtask_list` lookups and hide sub-tasks from MC's UI breadcrumb (`Feature-4 → Subtask-7`).

**Parallel per repo.** For each repo, spawn one `tl-agent` subagent to run the `tl-feature-compose` skill twice:

- **Narrative mode** → sub-task **Description** (business flow narrative, no framework names, no file paths, no HTTP codes; one or two paragraphs)
- **Detailed mode, scoped to that repo's units** → sub-task **Implementation** (full 5-section template: Build sequence, API endpoints, Database mods, Frontend UI, Touch points)

Once all N subagents return:

- Batch call `task-mcp.subtask_upsert_bundle` with all sub-tasks in one MCP call (payload always sets `taskType: subtask` per the invariant above) — MC creates them and returns their `task_object_id` + `task_number`
- Write each sub-task's local files under `.jetrix/features/<slug>/subtask/<repo>/`:
  - `description.md` — the narrative-mode compose (Description tab)
  - `implementation.md` — the detailed-mode compose (Implementation tab)
  - `status.md` — sub-task status (starts at `PLANNED`)
  - Frontmatter on each ties back to parent + carries `subtask_number` (§9b)
- Compose parent's **Implementation** in **rollup mode**: a short document listing each sub-task by repo + sequence, and cross-task dependencies (backend → frontend → mobile). Uses `subtask_number` from each sub-task's frontmatter for the ordering; MC display names (`Subtask-7`, `Subtask-8`) are also referenced so a reader can jump to the MC UI
- Push parent's rollup via `task-mcp.feature_update_implementation`

### 6c. Compose branch B — parent alone

- Call `tl-feature-compose` in **detailed mode** on the parent — full 5-section template (unchanged from current `/tl:compose` behaviour)
- Write local `.jetrix/features/<slug>/dev/plan.md`
- Push parent's Implementation via `task-mcp.feature_update_implementation`

### 6d. Idempotency

On re-run of `/dev:plan` for the same feature:

- Sub-tasks matched by `metadata.externalId` (which is `FEAT-<id>-<N>`) — existing ones **update in place** via `subtask_upsert_bundle`
- Unchanged content skipped via `_local_content_hash` in `sync-state.json` (same pattern as `/jetrix:push feature`)
- User checkpoint (§5a) is re-shown if the split decision would differ from last run

## 7. Stage 3 — Development planning

**Reference file:** [plugins/dev/commands/references/plan/development-planning.md](../../plugins/dev/commands/references/plan/development-planning.md) (new)

**Purpose:** the five planning stages that today live inside `/dev:build`. Relocated here; adapted to run per-task when sub-tasks exist.

**Sub-sections (moved from [readiness-and-planning.md](../../plugins/dev/skills/feature-delivery-loop/references/readiness-and-planning.md)):**

- §0a — Pre-flight (MC status check + local drift check) — **parallel: both checks fire concurrently**
- §1 — Readiness validation (acceptance criteria present, open questions resolved, dependencies available, base build green, etc.)
- §1a — Repository gate (brownfield vs project-zero) — routes to `/dev:bootstrap` if project-zero
- §1b — Test-harness gate (`qa/quality-gates.md` active) — routes to `/qa:audit` → `/qa:setup` if not
- §2 — Impact analysis (12 dimensions per task)
- §3 — Implementation planning — writes `dev-plan.md` (ordered steps, files, API/schema changes, test strategy, rollback, risks, complexity)

**Parallel per task** — when sub-tasks exist, §1/§2/§3 run once per sub-task in parallel subagents. Each writes into its own `subtask/<repo>/dev/` folder (dev-side work artifacts) alongside the sub-task's tab files at `subtask/<repo>/{description,implementation,status}.md`.

**End of Stage 3** — each task's `delivery-status.md` set to `PLANNED`; MC's task status updated to match.

## 8. Local file layout

**Design principle — sub-task mirrors parent's shape.** Parent has *tab files at feature root* + `dev/` for work artifacts. Every sub-task has the same shape one level down: *tab files at its own root* + `dev/` for work artifacts. Every local file maps 1:1 to an MC tab or a dev-side work concern.

**Full per-feature layout under `.jetrix/features/<slug>/`:**

```
features/supplier-onboarding/                 ← PARENT
│
├── feature.md                                ← Description tab (BA, merged with workflow.md at push)
├── workflow.md                               ← merged into Description
├── acceptance-criteria.md                    ← AC tab (BA)
├── business-rules.md                         ← BR tab (parent-only — sub-task schema has no BR)
├── nfrs.md                                   ← NFRs tab (parent-only)
├── test-scenarios.md                         ← TS tab (BA)
├── dependencies.md                           ← Dependencies tab (parent-only)
├── open-questions.md                         ← merged into Dependencies
├── status.md                                 ← parent status (derived from sub-tasks if split)
├── tl-plan.md                                ← parent Implementation tab
│                                                (rollup mode if split, detailed if parent-alone)
│
├── dev/                                       parent-level dev artifacts (ONLY when parent-alone)
│   ├── plan-run.md                            /dev:plan's stage log for this feature — --resume reads this
│   ├── task-decision.md                       WHY parent-alone; rule that applied
│   ├── dev-plan.md                            parent development plan
│   ├── impacted-components.md
│   ├── delivery-status.md
│   ├── acceptance-map.md
│   ├── implementation-log.md
│   ├── pr-summary.md
│   └── escalation-<n>.md                      only if BLOCKED
│
└── subtask/                                   ONLY exists when the feature was split
    │
    │  (top-level plan-run.md for this feature also moves here when split:)
    ├── plan-run.md                            /dev:plan's stage log — feature-level view of the split run
    ├── task-decision.md                       WHY split; which repos; rule that applied
    │
    ├── backend/                              ← named by repo slug (from .jetrix/cache/repolocation.json)
    │   │
    │   │  Sub-task TAB files (map 1:1 to MC's 4-tab schema):
    │   ├── description.md                     Description tab — business flow narrative
    │   ├── implementation.md                  Implementation tab — detailed 5-section compose
    │   │   (acceptance-criteria.md, test-scenarios.md deliberately absent —
    │   │    sub-task schema has these tabs but they stay empty on MC;
    │   │    validation reads parent's tabs)
    │   ├── status.md                          sub-task status (5-state)
    │   │
    │   └── dev/                               sub-task's dev work-log
    │       ├── dev-plan.md                    this sub-task's development plan
    │       ├── impacted-components.md
    │       ├── delivery-status.md
    │       ├── acceptance-map.md              parent AC → this sub-task's evidence
    │       ├── implementation-log.md
    │       ├── pr-summary.md
    │       └── escalation-<n>.md              only if BLOCKED
    │
    ├── frontend/
    │   └── (same shape as backend)
    │
    └── mobile/
        └── (same shape as backend)
```

**Batch-run level — under `.jetrix/dev/batch-runs/`:**

```
.jetrix/dev/batch-runs/
└── plan-run-<timestamp>.md                 One file per /dev:plan invocation, single- or multi-target
                                              · Resolved target set (§4b)
                                              · BA-file pull decision (§4c)
                                              · Checkpoint decision (Y / pick=… / n)
                                              · Per-feature outcome (planned / skipped / failed)
                                              · Concurrency + timing
```

`--resume` reads the batch file at the top level → knows which features are done, which failed, which are pending — then delegates to each feature's own `plan-run.md` (at `features/<slug>/dev/plan-run.md` or `features/<slug>/subtask/plan-run.md`) for per-feature stage state.

**Why this shape:**

| Reason | Detail |
|---|---|
| **Every file maps 1:1 to an MC tab or a dev concern** | `description.md` → Description tab, `implementation.md` → Implementation tab, `status.md` → task status field. Same principle parent already uses. |
| **Push/pull symmetry** | `/jetrix:push`/`/jetrix:pull` walk the same file names at both parent-root and `subtask/<repo>/` — one code path, no special cases beyond "walk `subtask/*/` if it exists". |
| **Human-readable folder names** | `subtask/backend/` reads naturally; developers think "the backend work", not "task 1". Sequence lives in frontmatter, not the folder. |
| **Dev artifacts live where the work happens** | `subtask/backend/dev/` mirrors parent's `dev/` at the level where the code is actually written. |
| **Empty AC/TS tabs are omitted locally** | Files aren't created for tabs that stay empty on MC — validation reads parent. Keeps the tree lean and clean. |
| **Cold-clone reconstruction works** | A fresh clone + `/jetrix:pull scope` reconstructs the entire tree from MC — parent tabs into feature root, sub-task tabs into `subtask/<repo>/`. No hidden state. |

**Batch-run level — under `.jetrix/dev/batch-runs/`:**

```
.jetrix/dev/batch-runs/
└── plan-run-<timestamp>.md                One file per /dev:plan invocation, single- or multi-target
                                             · Resolved target set (§4b)
                                             · BA-file pull decision (§4c)
                                             · Checkpoint decision (Y / pick=… / n)
                                             · Per-feature outcome (planned / skipped / failed)
                                             · Concurrency + timing
```

`--resume` reads the batch file at the top level → knows which features are done, which failed, which are pending — then delegates to each feature's own `dev/plan-run.md` for per-feature stage state.

**`plan-run.md` shape** (small, YAML-heavy, human-scannable):

```yaml
---
doc_type: plan-run
schema_version: 1.0
started_at: 2026-08-29T14:22:00Z
resolved_target:
  feature_id:              FEAT-SUP-001
  feature_folder:          features/supplier-onboarding
  parent_task_object_id:   6a61...
  parent_task_number:      Feature-4
  list_name:               Supplier Management
stages:
  - name: stage-0-resolution
    status: DONE
    finished_at: 2026-08-29T14:22:01Z
  - name: stage-1-code-context-readiness
    status: DONE
    auto_plan_triggered: true
    finished_at: 2026-08-29T14:22:47Z
  - name: stage-2-implementation-preparation
    status: RUNNING
    split_decision: split
    sub_tasks_composed: 2   # of 3
  - name: stage-3-development-planning
    status: PENDING
---
```

## 9. Frontmatter — identity mapping on both sides

### 9a. Parent — `feature.md` frontmatter (existing + one field added)

```yaml
---
feature_id:              FEAT-SUP-001
slug:                    supplier-onboarding
jetrix_task_object_id:   6a61...             # already exists (set by /jetrix:push feature)
jetrix_task_number:      Feature-4           # ADD — the MC display number
list_name:               Supplier Management
initiative:              supplier-portal
---
```

**Change needed:** [`apply-feature-responses.py`](../../plugins/jetrix/scripts/apply-feature-responses.py) writes `jetrix_task_id` today; extend to also write `jetrix_task_number` from MC's response.

### 9b. Sub-task — frontmatter on each tab file (new)

Every file inside `subtask/<repo>/` carries this frontmatter — `description.md`, `implementation.md`, and `status.md` all share it. `doc_type` distinguishes each file. Folder name = repo slug; sequence lives in frontmatter (`subtask_number`), not the folder name.

**`subtask/<repo>/description.md`:**
```yaml
---
doc_type:                 subtask-description
schema_version:           1.0
feature_id:               FEAT-SUP-001
parent_task_object_id:    6a61...
parent_task_number:       Feature-4
subtask_number:           1                       # 1..N execution sequence within parent
subtask_repo:             backend                 # matches the folder name + repolocation.json key
jetrix_subtask_object_id: 6b72...                 # set after MC push
jetrix_subtask_number:    Subtask-7               # MC display number, set after MC push
composed_at:              2026-08-29T14:24:11Z
inputs_hash:              <sha256>
---
```

**`subtask/<repo>/implementation.md`:** same frontmatter shape, `doc_type: subtask-implementation`, same `inputs_hash` (regenerated when the compose reruns).

**`subtask/<repo>/status.md`:** same identity fields, `doc_type: subtask-status`, plus:
```yaml
---
...(identity fields)...
doc_type:      subtask-status
current_state: PLANNED                            # PLANNED | IN_PROGRESS | REVIEW | DONE | BLOCKED
owner_lock:    null                               # set when /dev:build acquires
branch:        null                               # set when /dev:build creates the branch
---
```

The subtask_number ordering is what parent's rollup-mode Implementation tab references when it says "backend → frontend → mobile" — reading each sub-task's frontmatter, not the folder name.

### 9c. MC sub-task `metadata` block (new — carries reverse mapping)

Set at creation time via `subtask_upsert_bundle`:

```json
{
  "externalId":        "FEAT-SUP-001-1",
  "parentExternalId":  "FEAT-SUP-001",
  "subtaskNumber":     1,
  "subtaskRepo":       "backend",
  "source":            "ai",
  "aiGenerated":       true
}
```

**Why the mapping matters:** on a cold pull (new teammate clones, runs `/jetrix:pull`), the reverse mapping via MC's `metadata.externalId` is what reconstructs the local layout without any state on the client.

## 10. Status model

Five states — kept simple.

| State | Meaning | Owner |
|---|---|---|
| `PLANNED` | `/dev:plan` finished, ready for `/dev:build` | dev |
| `IN_PROGRESS` | `/dev:build` running or paused | dev |
| `REVIEW` | `/dev:commit` finished, PR raised | dev → human |
| `DONE` | PR merged | human (MC records) |
| `BLOCKED` | Escalation raised; cannot continue | dev (reversible) |

**Parent status derivation** (no manual updates):

- All sub-tasks `DONE` → parent `DONE`
- Any sub-task `BLOCKED` → parent `BLOCKED`
- Any sub-task `IN_PROGRESS` → parent `IN_PROGRESS`
- Else → `PLANNED`

Mirrored on MC's task status field so the UI stays truthful.

## 11. Parallel execution model — two axes

Parallel where it actually saves wall-clock. Sequential where MC ordering or dependencies require it.

### 11a. Outer axis — across features (batch runs)

When the target is `list=…`, `initiative=…`, or `--all`, features run concurrently.

- **Concurrency limit:** `--concurrency=N`, default `5`. Excess features queue and run as slots free up.
- **What runs concurrently:** each feature's full 4-stage flow (Stages 0 already done at batch level; Stages 1, 2, 3 run per-feature).
- **Failure isolation:** feature X failing at Stage 1 doesn't block feature Y. Failed features collect in the batch summary; the batch continues.
- **User checkpoint (§5a):** batched — one prompt covers the whole target set.
- **Progress emitted per feature completion:** `✓ Feature-4 planned · Feature-9 running (Stage 2, 2/3 sub-tasks composed) · 3 pending`.

### 11b. Inner axis — within a feature

| Where | Parallelism | What runs concurrently |
|---|---|---|
| Stage 1 — index loading | 3× per repo | frontend + backend + database indexes loaded at once |
| Stage 1 — unit resolution | N (one per declared unit) | Verify each unit resolves + linked |
| Stage 2 — sub-task compose | N (one per repo) | Description + Implementation compose per sub-task |
| Stage 3 — pre-flight | 2 | MC status check + local drift check |
| Stage 3 — per-task planning | N (one per sub-task, or 1 for parent-alone) | Readiness + impact + dev-plan |
| **Sequential (deliberate)** | | MC batch calls (one `subtask_upsert_bundle`, one `feature_update_implementation`); parent rollup after all sub-tasks composed |

Inner-axis parallelism is always on; not tunable via `--concurrency` (that flag only affects outer axis).

## 12. `task-mcp` additions needed (external — waits on Dharma)

The MC HTTP API already exposes all sub-task endpoints. `task-mcp` needs to wrap them.

### Tool 1 — `subtask_upsert_bundle`

Batch create/update sub-tasks under a parent.

```
Input:
  solution_id:     string
  parent_task_id:  string
  subtasks: [
    {
      title:                    string,
      description:              string,  # HTML/Markdown, business flow narrative
      implementation_details:   string,  # HTML/Markdown, detailed 5-section
      metadata: {
        externalId:            string,   # e.g. "FEAT-SUP-001-1"
        parentExternalId:      string,
        subtaskNumber:         int,
        subtaskRepo:           string,
        source:                "ai",
        aiGenerated:           true
      }
    },
    ...
  ]

Output:
  { results: [
    { subtask_number, task_object_id, task_number, ok, error? },
    ...
  ]}
```

Backed by MC's `POST /solutions/:solutionId/tasks/:taskId/subtasks` — called once per sub-task server-side but exposed to us as a batch.

### Tool 2 — `subtask_list`

Fetch all sub-tasks under a parent (for idempotency + cold-pull reconstruction).

```
Input:   solution_id, parent_task_id
Output:  subtasks: [
  { task_object_id, task_number, taskType, status, metadata: {...} },
  ...
]
```

Backed by MC's `GET /solutions/:solutionId/tasks/:taskId/subtasks`.

### Verification — reuse existing tools if possible

- **`feature_update_implementation`** — test whether it accepts a sub-task's `task_object_id`. If yes, reuse it for sub-task Implementation writes. If not, add `subtask_update_implementation` with the same shape.
- **`get_task_by_id_or_number`** — already handles all task types (features + sub-tasks) per its docs. Reuse in Stage 0.

### Until the tools land

`/dev:plan` runs Stage 0 + 1 + 3 fully; Stage 2's MC calls block with:

```
✗ Stage 2 needs task-mcp subtask_upsert_bundle — not yet available.
  Local composes written to features/<slug>/subtask/<repo>/{description,implementation}.md; review them.
  Ask Dharma when the task-mcp update is ready; then re-run /dev:plan --resume.
```

`--dry-run` never hits this because it skips MC writes entirely.

## 13. Files to create / modify / delete

### Create

| Path | Purpose |
|---|---|
| [plugins/dev/commands/plan.md](../../plugins/dev/commands/plan.md) | Orchestrator command; routes to stage reference files |
| [plugins/dev/commands/references/plan/code-context-readiness.md](../../plugins/dev/commands/references/plan/code-context-readiness.md) | Stage 1 verbatim spec |
| [plugins/dev/commands/references/plan/implementation-preparation.md](../../plugins/dev/commands/references/plan/implementation-preparation.md) | Stage 2 verbatim spec (compose modes, MC calls) |
| [plugins/dev/commands/references/plan/development-planning.md](../../plugins/dev/commands/references/plan/development-planning.md) | Stage 3 verbatim spec (pre-flight, readiness, impact, plan) |

### Modify

| Path | Change |
|---|---|
| [plugins/dev/skills/feature-delivery-loop/SKILL.md](../../plugins/dev/skills/feature-delivery-loop/SKILL.md) | Remove sections §0a / §0 / §1 / §2 / §3; add "no plan? run /dev:plan first" gate; loop starts at branch creation; loop-state model unchanged; add sub-task branching (build one task at a time) |
| [plugins/dev/skills/feature-delivery-loop/references/readiness-and-planning.md](../../plugins/dev/skills/feature-delivery-loop/references/readiness-and-planning.md) | Split — content that moves to /dev:plan reference files is deleted here; content /dev:build still needs (loop-control, retry limits) stays |
| [plugins/dev/commands/build.md](../../plugins/dev/commands/build.md) | Accept any task id (parent or sub-task); resolve sub-task's repo from metadata; error with "run /dev:plan first" if `plan-run.md` missing or Stage 3 incomplete; remove auto-plan hop |
| [plugins/tl/skills/tl-feature-compose/SKILL.md](../../plugins/tl/skills/tl-feature-compose/SKILL.md) | Add **narrative mode** (business-flow Description) and **rollup mode** (parent Implementation when sub-tasks exist) alongside existing detailed mode |
| [plugins/tl/skills/tl-feature-compose/references/implementation-plan-template.md](../../plugins/tl/skills/tl-feature-compose/references/implementation-plan-template.md) | Add the two new mode templates; keep the detailed template |
| [plugins/jetrix/scripts/apply-feature-responses.py](../../plugins/jetrix/scripts/apply-feature-responses.py) | Write back `jetrix_task_number` (in addition to `jetrix_task_id`) so Stage 0 identity resolution finds it |
| [plugins/jetrix/scripts/assemble-features.py](../../plugins/jetrix/scripts/assemble-features.py) | When walking a feature folder, ALSO walk `subtask/*/` — assemble each sub-task's `description.md` + `implementation.md` into a `subtasks[]` array on the parent's payload (so `/jetrix:push feature` can push parent + sub-tasks together). Group sub-tasks by parent `feature_id`. |
| [plugins/jetrix/commands/references/push/feature.md](../../plugins/jetrix/commands/references/push/feature.md) | Add sub-task handling: after `feature_upsert_bundle` returns for parent, if the assembled payload has sub-tasks, call `subtask_upsert_bundle` with them (parent_task_id from the parent's response). Skip-unchanged via sync-state per sub-task file hash. |
| [plugins/jetrix/commands/references/push/implementation.md](../../plugins/jetrix/commands/references/push/implementation.md) | Route: push parent's `tl-plan.md` via `feature_update_implementation` (existing); ALSO push each `subtask/<repo>/implementation.md` via `feature_update_implementation` targeting each sub-task's `task_object_id`. Same tool, one call per sub-task. |
| [plugins/jetrix/commands/references/pull/scope.md](../../plugins/jetrix/commands/references/pull/scope.md) | After parent tabs are written to feature root, call `subtask_list(parent_task_id)` and for each sub-task write `subtask/<subtaskRepo>/description.md`, `implementation.md`, `status.md` from MC's tab fields + `metadata.subtaskNumber` / `metadata.subtaskRepo`. |
| [plugins/jetrix/scripts/apply-scope-manifest.py](../../plugins/jetrix/scripts/apply-scope-manifest.py) | Add sub-task write path — given a sub-task's fetched fields + metadata, write the 3 tab files into `subtask/<subtaskRepo>/`. Update sync-state under `subtasks/<subtask_object_id>` keys. |
| [plugins/dev/dev_readme.md](../../plugins/dev/dev_readme.md) | Add `/dev:plan` command row + a section describing the 4-stage flow; note `/dev:build` no longer auto-plans; document the `subtask/<repo>/` local layout |
| [plugins/tl/tl_readme.md](../../plugins/tl/tl_readme.md) | Remove `/tl:compose` from user-facing commands (skill stays, invoked internally by `/dev:plan`). `/tl:plan` is unchanged. |
| [plugins/delivery-os-core/skills/delivery-os-conventions/SKILL.md](../../plugins/delivery-os-core/skills/delivery-os-conventions/SKILL.md) | Add `subtask/<repo>/` layout convention to §1 workspace layout; add sub-task frontmatter shapes (§9b) to the frontmatter standard section; add `SUBTASK-<AREA>-NN` or note sub-task identity conventions if needed |

### Delete

| Path | Reason |
|---|---|
| [plugins/tl/commands/compose.md](../../plugins/tl/commands/compose.md) | `/tl:compose` retires as a slash command; composition now happens inside `/dev:plan` Stage 2 via the `tl-feature-compose` skill |

## 14. Order of implementation

1. **Draft `task-mcp` tool specs** (§12) — hand off to Dharma. No code on our side until they're ready.
2. **Extend `delivery-os-conventions` skill** — add the `subtask/<repo>/` layout to the workspace-layout section and add sub-task frontmatter shapes to the frontmatter standard. This locks the contract other agents will read.
3. **Extend `tl-feature-compose` skill** — add narrative mode + rollup mode. Fully local work, no MC dependency, unblocks compose in Stage 2.
4. **Create the 3 stage reference files** — Stages 1 and 3 are mostly relocation from `readiness-and-planning.md`. Stage 2 is new.
5. **Create `plugins/dev/commands/plan.md`** — the orchestrator + Stage 0 resolution logic.
6. **Delete `plugins/tl/commands/compose.md`.**
7. **Strip planning from `feature-delivery-loop/SKILL.md`.**
8. **Update `plugins/dev/commands/build.md`** — new arg shape (parent OR sub-task), resolve sub-task's repo from frontmatter, no-plan gate.
9. **Update push/pull reference files** — `push/feature.md`, `push/implementation.md`, `pull/scope.md` to walk `subtask/<repo>/` folders.
10. **Update push/pull scripts** — `assemble-features.py` walks `subtask/*/`, `apply-scope-manifest.py` writes sub-task tab files, `apply-feature-responses.py` writes back `jetrix_task_number`.
11. **Update `dev_readme.md` and `tl_readme.md`.**
12. **Wait for `task-mcp` tools to land** — then remove Stage 2's block-with-message, wire the real calls.
13. **Smoke test end-to-end** — single-repo feature first, then multi-repo (backend + frontend), then verify `--resume` recovers a mid-run kill, then verify a cold `/jetrix:pull scope` reconstructs the entire `subtask/<repo>/` tree.

## 15. Success criteria

**Single-target:**

- `/dev:plan Feature-4` on a **single-repo** feature → composes parent Implementation (detailed), pushes to MC, writes `features/<slug>/dev/plan.md` + `dev-plan.md`, status `PLANNED`, one user checkpoint fired between Stage 1 and Stage 2
- `/dev:plan Feature-4` on a **multi-repo** feature → creates N sub-tasks in MC via one `subtask_upsert_bundle` call (payload sets `taskType: subtask`), pushes each Description + Implementation, writes parent rollup, all sub-tasks status `PLANNED`, sub-tasks visible under the parent's breadcrumb in the MC UI, sub-task type stays `subtask` (never converted)
- `/dev:plan Task-1 --resume` → skips completed stages (read from `plan-run.md`) and continues from the failed one
- `/dev:plan Subtask-7` → resolves upward to `Feature-4` and plans the whole parent
- `/dev:plan` (no arg) → picks the next `READY_FOR_DEV` task

**Multi-target (batch runs):**

- `/dev:plan list="Supplier Management"` → expands to every feature under that List, one consolidated checkpoint, runs all in parallel (bounded by `--concurrency=5`), reports per-feature outcome at the end
- `/dev:plan initiative=supplier-portal` → expands to every feature stamped with that initiative, same batch flow
- `/dev:plan --all` → every feature at `READY_FOR_DEV`, same batch flow
- Batch with one feature missing BA files → `/dev:plan` prompts `Pull from Jetrix now? [Y/n]`; `Y` inlines `/jetrix:pull scope` for those features and continues; `n` marks them `SKIPPED_MISSING_BA` and continues with the rest
- Batch with one feature's Stage 1 failing → failed feature reported at end with escalation note; the other N-1 complete successfully

**Cross-command:**

- `/dev:build Task-1` before `/dev:plan` → errors with *"Run /dev:plan first"*
- `/dev:build Subtask-7` after `/dev:plan` → resolves the sub-task's repo via metadata, reads parent for AC/BR/NFRs/TS, works only in that repo
- Re-running `/dev:plan` on the same feature is idempotent — unchanged sub-tasks skipped via content hash

## 16. Explicitly out of scope for this pass

- `/dev:commit` command design (separate follow-up)
- E2E validation across sub-tasks — the last sub-task's `/dev:build` closes any parent-level E2E AC; details deferred to `/dev:build`'s spec
- Cross-repo PR merge coordination — policy call, deferred
- Semantic memory merge on PR merge (Dharma's separate concern raised in the transcript)
- Sub-task **Acceptance Criteria** and **Test Scenarios** tab writes — left empty; parent tabs are the validation source
- Auto-flipping sub-task local status → MC (comes later in `/dev:build`)

## 17. Blockers / open questions

**BQ-01** — Does `feature_update_implementation` accept a sub-task's `task_object_id`, or is it feature-only? **Owner:** Dharma. **Impact:** if feature-only, add `subtask_update_implementation`. Not blocking Stage 2 design, only the tool count.

**BQ-02** — When `subtask_upsert_bundle` receives BR / NFRs / Deps fields (which sub-task's tab schema doesn't allow), does MC silently drop or error? **Owner:** Dharma. **Impact:** we currently plan to send only Description + Implementation, so this is theoretical, but worth confirming.

**BQ-03** — What ordering does MC expose for sub-tasks? Our `subtaskNumber` metadata is client-driven; the UI in the screenshot showed `Subtask-7`, `Subtask-8`, `Subtask-9` — that's an MC-side task-number sequence unrelated to our sequence-within-parent. Confirm the metadata field is preserved and readable on pull. **Owner:** Dharma.

**BQ-04** — Multi-solution behaviour — if a workspace bound to solution A pulls a task whose parent lives in solution B, do we halt or refuse? **Owner:** us. **Recommendation:** halt with a clear message; solutions are 1:1 with workspaces per current v2 layout.

---

**End of plan.** Every §-number above is a checkable spec. Change any of them before we start, then say go.
