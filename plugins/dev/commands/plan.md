---
description: Just-in-time planning for one or many tasks. Verifies the technical context graph is current (auto-runs /tl:plan if missing), decides whether each task needs sub-tasks (multi-repo → one sub-task per repo, single-repo or bug/story → parent alone), composes each sub-task's Description + Implementation and creates them in Mission Control, writes the local development plan, and (v2.2) surfaces every plan-time decision that would require build-time input as PB-### blockers in dev/plan-blockers.md — so /dev:build never has to prompt. Accepts a single MC task number (Task-N, Feature-N, Subtask-N), a local feature slug or folder path, the internal FEAT-<AREA>-NN id, or a multi-target form — an MC List name, initiative=<name>, or --all — which fans out across every matching feature in parallel. Runs 4 stages: identity resolution → code-context readiness → implementation preparation → development planning + blocker detection. With --resume: if a task has an OPEN dev/plan-blockers.md, folds every filled Resolution: field into implementation.md + implementation.md §3 Impacted components + registers deterministically per category, logs each fold as a DEC-###, and moves the task from BLOCKED_ON_PLAN to PLANNED. Two parallelism axes: across features (bounded by --concurrency, default 5) and within a feature (per-sub-task compose + per-task planning). One consolidated user checkpoint after stage 1 to confirm the split for every targeted feature. Failure of one feature never halts the batch — failed features report at the end with escalations or plan-blockers. Never merges, never runs code — leaves each task at status PLANNED for /dev:build (or BLOCKED_ON_PLAN awaiting user resolution).
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | FEAT-<AREA>-NN | list=<name> | initiative=<name> | --all | (blank = next READY task)> [--split | --no-split] [--resume] [--dry-run] [--concurrency=N]"
---

# /dev:plan

You are the entry point for `/dev:plan`. **Orchestrator only** — this file parses arguments, does Stage 0 (identity resolution + target-set expansion + BA-file pull check), then routes to three stage reference files that carry the detailed logic. Do NOT paraphrase the stage files' instructions — Read them and execute verbatim, exactly the way `/jetrix:push` routes to its per-stage files.

Read the **`delivery-os-conventions`** skill first if it's not in context — the workspace layout, frontmatter standard, stable-ID rules, and the sub-task section (§v2.1). Then read this feature's context:

- `.jetrix/project.json` — solution + apps + `repolocation.json` for repo → path mapping
- The BA feature files (`features/<slug>/*.md`) for whichever features Stage 0 resolves
- `shared-context/decision-log.md` — you'll append `DEC-###` rows for material planning decisions

Everything you write goes to `.jetrix/features/<slug>/dev/`, `.jetrix/features/<slug>/subtask/<repo>/`, or `.jetrix/dev/batch-runs/`. Never modify code, never merge, never touch secrets.

---

## 0. Preflight — confirm the workspace and MCP registration

Standard checks before any work:

1. Walk up from `$PWD` looking for `.jetrix/project.json` (up to 3 parent levels). If missing → tell the user to run `/jetrix:init` first and stop.
2. Read `solution_id`, `solution_slug`, and `apps[]` from `project.json`. Note the folder that CONTAINS `.jetrix/` as `workspace_root`; the container at `<workspace_root>/.jetrix/` as `project_root`.
3. Read `.jetrix/cache/repolocation.json` — for each app in `apps[]`, resolve its absolute local path. `SKIPPED` values mean that repo is unavailable — log and continue.
4. Confirm `task-mcp` is registered (`claude mcp list`). If missing → tell user to run `/delivery-os:setup` and stop.
5. Confirm `features/` exists under `project_root`. If missing → tell user to run `/ba:features` or `/jetrix:pull scope` and stop.

---

## 1. Parse arguments

`$ARGUMENTS` may contain:

**Target (required, unless blank for "next task at MC `readyForDev`"):**

*Single-target forms:*
- MC task number: `Task-N`, `Feature-N`, `Subtask-N` (case-insensitive prefix)
- Local slug: `supplier-onboarding`
- Local folder path: `features/supplier-onboarding`
- Internal id: `FEAT-<AREA>-NN`
- Blank: pick next feature at MC `readyForDev` (v2.2)

*Multi-target forms:*
- `list=<name>` or `list="Supplier Management"` (bare quoted string with no other match also treated as list name)
- `initiative=<name>` (matches `/tl:plan`, `/dev:build` convention)
- `--all` (every feature at MC `readyForDev`; combined with `initiative=<name>` filters to that initiative)

**Flags:**
- `--split` — force sub-task creation regardless of repo count
- `--no-split` — force parent-alone regardless of repo count
- `--resume` — continue from last completed stage per `plan-run.md` (batch and per-feature)
- `--dry-run` — compose locally; skip all MC writes
- `--concurrency=N` — outer parallelism cap (features running simultaneously). Default `5`.

Parse into a normalized target spec + flags before Stage 0. If the argument is ambiguous, ask the user before guessing.

---

## 2. Stage 0 — Identity resolution + target-set expansion

**Read** `plugins/dev/commands/references/plan/code-context-readiness.md` for the full detection algorithm you'll run in Stage 1 (helps you plan Stage 0's target-set expansion).

Stage 0 has its own logic; execute the steps below directly (not via a separate reference file — it's small enough to inline):

### 2a. Resolve the target (first match wins)

For **single-target** forms:

1. **MC task number** (`Task-N`, `Feature-N`, `Subtask-N`):
   - Call `task-mcp.get_task_by_id_or_number(solution_id, ref=<arg>)`.
   - If `task.taskType == subtask` → walk up to `parentTaskId`, re-fetch → parent Task.
   - Result: `(feature_id from metadata.externalId, task_object_id, task_number)`.
2. **Local slug or folder path** — match against `features/<slug>/`, read `feature.md` frontmatter → `(feature_id, jetrix_task_object_id, jetrix_task_number)`.
3. **Internal `FEAT-<AREA>-NN`** — grep `features/*/feature.md` frontmatter for the id.
4. **Blank** — call `task-mcp.feature_list_bundle(solution_id, status='readyForDev')` → pick first (or picker if many). Fallback: scan `features/*/status.md` for `current_state: PLANNED` if MC unavailable.

For **multi-target** forms:

5. **`list=<name>`** — call `task-mcp.feature_list_bundle(solution_id, list_name=<arg>)` → array of features → expand to N targets.
6. **`initiative=<name>`** — grep `features/*/feature.md` frontmatter for `initiative: <arg>` → N targets. Cross-check with MC via `feature_list_bundle` to catch features not yet local (feeds §2c).
7. **`--all`** — call `task-mcp.feature_list_bundle(solution_id, status='readyForDev')`; combined with `initiative=<name>`, take every feature in that initiative regardless of status.

Any unresolvable input → halt with the 5 nearest slugs / task numbers.

### 2b. Write the resolved target set

Create `.jetrix/dev/batch-runs/plan-run-<timestamp>.md` (timestamp = `YYYY-MM-DD-HHMMSS`). Write:

```yaml
---
doc_type: plan-run
schema_version: 1.0
produced_by: dev
started_at: <ISO>
concurrency: 5
flags: {split: null, resume: false, dry_run: false}
---

# /dev:plan run

## Resolved targets

- feature_id: FEAT-SUP-001
  feature_folder: features/supplier-onboarding
  parent_task_object_id: 6a61...
  parent_task_number: Feature-4
  list_name: Supplier Management
  ba_files_check: pending
  stage_status: pending
- feature_id: FEAT-SUP-002
  ...
```

`--resume` reads this file first — if `stage_status: completed` on a feature, skip.

### 2c. BA-file presence check (auto-detect missing files, prompt to pull)

For each targeted feature, check `features/<slug>/` for the 8 BA files: `feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md`.

**If any features are missing files**, print a consolidated summary:

```
✗ Missing BA files for 2 of 5 features:
    · Feature-4  Supplier Onboarding      (missing: workflow.md, nfrs.md)
    · Feature-9  Outlet Discovery         (missing: acceptance-criteria.md)

  Pull them from Jetrix now? [Y/n]
```

- `Y` (default) → invoke `/jetrix:pull scope` inline for just the affected features. Re-check after. Continue with anything now complete; mark still-missing as `SKIPPED_MISSING_BA` and log.
- `n` → mark affected features `SKIPPED_MISSING_BA`, continue with the rest.

All 8 BA files present → skip this step silently.

### 2d. Backfill `jetrix_task_number` if missing

For every remaining target, if `feature.md` frontmatter has `jetrix_task_object_id` but no `jetrix_task_number`, fetch it via `get_task_by_id_or_number` and patch the file. Non-blocking.

### 2e. Verify sub-task target resolution

If the user passed a `Subtask-N` (rare — usually they open the parent), we already walked up to parent in §2a step 1. Log this fact so the summary tells them we planned the parent (which touches this sub-task).

---

## 3. Route to Stage 1 (per-feature, parallel)

For each successfully-resolved feature, spawn a **worker** (concurrency-bounded per `--concurrency=N`, default 5) that:

1. Reads `plugins/dev/commands/references/plan/code-context-readiness.md`.
2. Executes it verbatim on THIS feature.
3. Writes progress to this feature's `dev/plan-run.md` per the reference file's spec.
4. Reports outcome (planned / auto-planned / blocked) to the batch summary.

Once EVERY feature's Stage 1 is complete (or reported as blocked), the orchestrator proceeds to §4.

---

## 4. Consolidated user checkpoint (single prompt for the whole batch)

Read each successful feature's `dev/plan-run.md` `stage-1-results` block → compose the consolidated prompt.

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

**Multi-target run:**

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

- `Y` (default) → all approved
- `pick=1,3,5` → only those approved; others `SKIPPED_USER_DECLINED`
- `n` → halt cleanly; write batch summary with `outcome: user_cancelled`; nothing pushed to MC

`--dry-run` skips this prompt entirely (implicit no on MC writes, continues to Stage 2's compose so user can review the drafts).

Write the checkpoint result to the batch summary's `checkpoint_decision:` field.

---

## 5. Route to Stage 2 (per-feature, parallel, bounded)

For each approved feature, spawn a worker that:

1. Reads `plugins/dev/commands/references/plan/implementation-preparation.md`.
2. Executes it verbatim on THIS feature.
3. Uses its own inner-axis parallelism (per-sub-task compose).
4. Reports outcome to the batch summary.

**Order of operations within a Stage 2 worker (from the reference file):**
1. Read this feature's `stage-1-results` block
2. Apply the sub-task decision rule (§6a of the reference)
3. Fan out N `tl-agent` subagents (split) or 1 (parent-alone) for compose
4. Wait for all composes to return
5. Sequential MC push: `subtask_upsert_bundle` → `feature_update_implementation` (parent rollup) → `feature_update_implementation` (each sub-task's Implementation)
6. Update sync-state

---

## 6. Route to Stage 3 (per-feature × per-task, parallel, bounded)

For each Stage-2-successful feature, spawn a worker that:

1. Reads `plugins/dev/commands/references/plan/development-planning.md`.
2. Executes it verbatim on THIS feature.
3. Uses its own inner-axis parallelism (per-sub-task planning for split; single task for parent-alone).

Each per-task worker inside Stage 3 spawns a `dev-agent` subagent to run readiness / impact / dev-plan for that task.

### 6a. Stage 3.5 — Blocker detection (v2.2)

After each task's Stage 3 finishes writing `implementation.md` + `implementation.md §3 Impacted components`, **immediately run the blocker detection sub-phase** — reads `plugins/dev/commands/references/plan/blocker-detection.md` and executes verbatim on that task.

**Outcomes per task:**

- **No blockers detected** → task proceeds to state `PLANNED`, MC status `readyForDev`. Continue.
- **Blockers detected** → task writes `dev/plan-blockers.md` (`status: OPEN`), sets state to `BLOCKED_ON_PLAN`, MC status `blocked`. Halt THIS task's Stage 3.5; siblings continue independently.

**Batch behaviour:**

- Blockers on ONE task never halt the batch — same failure-isolation as Stages 1 + 2. Other tasks reach `PLANNED` normally.
- Batch summary (§7) surfaces every task's blocker state.

### 6b. Stage 3.5 on `--resume` — Blocker fold

When invoked with `--resume`, for each task whose `dev/plan-blockers.md` exists AND `status: OPEN` or `RESOLVING`:

1. Reads `plugins/dev/commands/references/plan/blocker-fold.md` and executes verbatim.
2. If every `PB-###` has a filled `Resolution:` → folds each per the per-category rules, updates target files, logs `DEC-###`, sets file `status: RESOLVED`, task → `PLANNED`, MC → `readyForDev`.
3. If any `PB-###` still has a placeholder `Resolution:` → halts THIS task's fold with a targeted message listing the unresolved PB-###; task stays `BLOCKED_ON_PLAN`.
4. If a fold error occurs (missing target file / section) → halts, preserves user's Resolution field, sets `status: OPEN`, writes an error line.

Tasks whose `plan-blockers.md` is already `RESOLVED` (or never had one) skip §6b entirely — pure Stage 3 finalise runs.

### 6c. Halt output when blockers surface

When Stage 3.5 detects blockers and halts, print (per task):

```
✗ /dev:plan halted for <task-ref> — <N> plan-time decisions require resolution:

  PB-001  <short title>              [Blocks <AC/BR/dev-plan step>]
  PB-002  <short title>              [Blocks <...>]

Resolve them:
  1. Open: <task-folder>/dev/plan-blockers.md
  2. Fill in the "Resolution:" field under each PB-###
  3. Re-run: /dev:plan --resume <task-ref>

Status: BLOCKED_ON_PLAN (MC: blocked)
```

For multi-target batches, print the union of these halts at the end of the batch alongside the successes.

### 6d. Halt output on `--resume` partial resolution

```
✗ /dev:plan --resume halted for <task-ref> — <M> of <N> blockers still need decisions:

  Folded:      PB-001, PB-003
  Still open:  PB-002, PB-004

Fill the remaining Resolution: fields and re-run.
```

### 6e. Success output on `--resume` complete fold

```
✓ /dev:plan --resume complete for <task-ref> — <N> blockers folded into the plan

  PB-001 → resolved (option 1: internal compliance service)
            applied to: implementation.md §3 Impacted components §3rd-party, implementation.md step 3
            logged as DEC-042
  PB-002 → resolved (option 1: composite uniqueness)
            applied to: implementation.md §3 Impacted components §Database, implementation.md step 1
            logged as DEC-043

Local state:  PLANNED
MC status:    readyForDev

Next: /dev:build <task-ref>
```

---

## 7. Batch summary

After all workers complete (or fail), print the summary:

```
✓ /dev:plan complete

Batch summary: .jetrix/dev/batch-runs/plan-run-2026-08-29-143207.md

Succeeded (4):
  · Feature-4   Supplier Onboarding      → 3 sub-tasks, PLANNED
      · Subtask-7 (backend)  https://jetrix/…/Subtask-7
      · Subtask-8 (frontend) https://jetrix/…/Subtask-8
      · Subtask-9 (mobile)   https://jetrix/…/Subtask-9
  · Feature-9   Outlet Discovery         → 2 sub-tasks, PLANNED
  · Feature-12  RFP Generation           → parent-alone, PLANNED
  · Feature-15  Reporting Dashboard      → 2 sub-tasks, PLANNED

Failed (1):
  ✗ Feature-7  Supplier Approval        → BLOCKED_STAGE_1
     Reason: TL auto-plan can't complete — integration contract missing for compliance service
     See: features/supplier-approval/dev/escalation-1.md

Skipped (0)

Next:
  Address Feature-7's escalation, then re-run:  /dev:plan Feature-7
  Start building:                                /dev:build Subtask-7   (Feature-4's backend)
                                                 /dev:build Feature-12  (parent-alone)
```

Also write the same content to `.jetrix/dev/batch-runs/plan-run-<ts>.md` (append the `## Summary` section to the file created in §2b).

---

## 8. Failure surfaces to always report

- **Stage 1 blocked** — feature `BLOCKED_STAGE_1` with escalation note
- **User cancelled at checkpoint** — batch summary shows `outcome: user_cancelled`; nothing published
- **Stage 2 blocked** — feature `BLOCKED_STAGE_2` with escalation note; other approved features unaffected
- **MC push refused** (permission_denied) — halt THIS feature; report which permission; continue batch
- **task-mcp subtask_upsert_bundle unavailable** (Dharma's addition not yet deployed) — Stage 2 halts with the specific tool name; recommend `--dry-run` in the meantime so composes still land locally
- **task-mcp `metadata.parentExternalId is not allowed`** on retry — task-mcp is running the pre-fix version. DO NOT hand-craft a payload that omits the field. task-mcp (v56c8212+) handles the metadata translation transparently — the plugin ALWAYS sends `parentExternalId` + `subtaskNumber` + `subtaskRepo`; task-mcp drops the first two and maps the third to `externalSlug` before forwarding to MC. Parent linkage is via `parent_task_id` (the tool input parameter), NOT `metadata.parentExternalId`. See `plugins/dev/commands/references/plan/implementation-preparation.md` §2e.i for the full translation table. If the error still happens, task-mcp needs to reload the fixed version — restart it; do not work around at the plugin.

---

## Guardrails

- Never invent BA content — Stage 0's BA-file check + prompt is the only path to fill missing files.
- Never invent TL graph units — Stage 1 auto-plans via `tl-feature-planning`, or escalates.
- Never convert a sub-task's `taskType` from `subtask` to anything else — invariant in Stage 2c.
- Never merge, never push code, never modify secrets.
- Retry limits mirror `/dev:build`: 1 auto-plan per Stage 1 pass; per-item error isolation on MC calls (a bad sub-task doesn't stop the batch).
- Every material design choice → `DEC-###` in `shared-context/decision-log.md`.
