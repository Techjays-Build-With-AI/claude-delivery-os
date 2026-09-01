---
description: Just-in-time planning for one or many tasks. Verifies the technical context graph is current (auto-runs /tl:plan if missing), decides whether each task needs sub-tasks (multi-repo → one sub-task per repo, single-repo or bug/story → parent alone), composes each sub-task's Description + Implementation and creates them in Mission Control, writes the local development plan, and (v2.2) surfaces every plan-time decision that would require build-time input as PB-### blockers in dev/plan-blockers.md — so /dev:build never has to prompt. Accepts a single MC task number (Task-N, Feature-N, Subtask-N), a local feature slug or folder path, the internal FEAT-<AREA>-NN id, or a multi-target form — an MC List name, initiative=<name>, or --all — which fans out across every matching feature in parallel. Runs 4 stages: identity resolution → code-context readiness → implementation preparation → development planning + blocker detection. With --resume: if a task has an OPEN dev/plan-blockers.md, folds every filled Resolution: field into implementation.md §1-§9 + registers deterministically per category, logs each fold as a DEC-###, and moves the task from BLOCKED_ON_PLAN to PLANNED. Two parallelism axes: across features (bounded by --concurrency, default 5) and within a feature (per-sub-task compose + per-task planning). One consolidated user checkpoint after stage 1 to confirm the split for every targeted feature. Failure of one feature never halts the batch — failed features report at the end with escalations or plan-blockers. Never merges, never runs code — leaves each task at status PLANNED for /dev:build (or BLOCKED_ON_PLAN awaiting user resolution).
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

Create `.jetrix/dev/batch-runs/plan-run-<timestamp>.md` (timestamp = `YYYY-MM-DD-HHMMSS`). This is the workspace-level batch summary. Each feature ALSO writes a per-feature journal at `features/<slug>/dev/plan-run.md` — same schema, feature-scoped, so users can `cat features/<slug>/dev/plan-run.md` and see every stage's skill invocations for that feature.

**Batch run schema** (workspace-level):

```yaml
---
doc_type: plan-run
schema_version: 2.0        # v2.3 refactor — added skill-invocation logging + Stage 2/3/4 reorder
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

**Per-feature run schema** (`features/<slug>/dev/plan-run.md`) — one section per stage, with skill-invocation logging so you can verify every stage's skills fired correctly:

```yaml
---
doc_type: plan-run
schema_version: 2.0
produced_by: dev
feature_id: FEAT-HCAL-01
started_at: <ISO>
---

## Stage 1 — Code-context readiness + QA-gate check
stage_1:
  status: DONE | HALTED
  invocations:
    - name: inline_detection
      inputs: {feature_md_frontmatter: {related_pages: [...], related_apis: [...], related_entities: [...]}}
      outputs: {units_resolved: N, units_linked: N, link_integrity: PASS | FAIL}
      duration_ms: N
    - name: tl-feature-planning (auto-plan)  # only when Stage 1a returned NOT_PLANNED
      inputs: [feature.md, tl indexes]
      outputs: {units_created: N, decs_logged: [DEC-...]}
      duration_ms: N
    - name: qa-audit / qa-plan / qa-test-setup    # only when user answered "Yes" at §1e QA prompt
      inputs: [existing repo state, capabilities]
      outputs: {qa_setup_completed: true, harness_status: Ready}
      duration_ms: N
    - name: qa-skip-marker                        # only when user answered "Skip" at §1e QA prompt
      inputs: [shared-context/technology-stack.md OR repo package manifest]
      outputs: {qa_setup_skipped: true, qa/quality-gates.md: written with stack_inferred: true + tier pools per capability class}
      duration_ms: N
  qa_gate_state: Ready | Stack-Inferred          # ← reflects user's answer at §1e
  finished_at: <ISO>

## Stage 2 — Per-task analysis
stage_2:
  status: DONE | HALTED
  tasks:
    - subtask_number: 1
      subtask_repo: backend
      invocations:
        - name: dev-agent (readiness)
          inputs: [qa/quality-gates.md, git-status, .jetrix/project.json]
          outputs: {readiness: PASS, harness: repo-own, base_build: green, critical_gaps: []}
          duration_ms: N
        - name: dev-agent (impact analysis)
          inputs: [feature.md, workflow.md, ba/registers/data.md, ba/registers/integrations.md]
          outputs: {dimensions_covered: 12, n_a_dimensions: 6, impacted_files: N}
          duration_ms: N
        - name: dev-agent (dev-plan)
          inputs: [tl units, implementation-plan.md]
          outputs: {ordered_steps: N, test_scenarios: N, risks: N, decs_proposed: [DEC-...]}
          duration_ms: N
      scratchpad_written: dev/backend-analysis.md
      finished_at: <ISO>

## Stage 3 — Blocker detection
stage_3:
  status: DONE | HALTED   # HALTED = blockers detected, this task
  tasks:
    - subtask_number: 1
      subtask_repo: backend
      invocations:
        - name: inline_5_source_scan
          sources: [tl-plan.md HELDs, open-questions.md, integrations.md, system-landscape.md, dev/backend-analysis.md unknowns]
          outputs: {blockers_detected: N, ids: [PB-1-001, PB-1-002]}
          duration_ms: N
      blockers_file: dev/backend-plan-blockers.md
      state_set: BLOCKED_ON_PLAN | PROCEED_TO_STAGE_4
      finished_at: <ISO>

## Stage 4 — Compose + push
stage_4:
  status: DONE | HALTED | SKIPPED
  skipped_reason: null | "Stage 3 detected blockers"
  tasks:
    - subtask_number: 1
      subtask_repo: backend
      preconditions_check:
        analysis_scratchpad_exists: true
        blockers_resolved_or_absent: true
      invocations:
        - name: tl-feature-compose (implementation mode)
          inputs: [tl units, dev/backend-analysis.md]
          outputs: {sections_written: [1,2,3,4,5,7,8,9], stubbed: [10], size_chars: N}
          duration_ms: N
        - name: tl-feature-compose (description mode)   # only for split
          inputs: [feature.md, workflow.md, tl units, dev/backend-analysis.md § Overview]
          outputs: {sections_written: [Overview, What, BRs, Refusals, OOS, Related], size_chars: N}
          duration_ms: N
        - name: task-mcp.subtask_upsert_bundle
          inputs: {solution_id, parent_task_id, subtasks: [<count>]}
          outputs: {ok: true, task_number: Subtask-7, version: 1, action: created}
          duration_ms: N
      files_written: [subtask/backend/description.md, subtask/backend/implementation.md, subtask/backend/status.md]
      finished_at: <ISO>
```

**How to verify every skill fired correctly:**

```bash
cat features/<slug>/dev/plan-run.md
```

Every stage lists its skill invocations with inputs + outputs + duration. If a stage halted, `status: HALTED` + `skipped_reason` on later stages make it obvious. Missing inputs / failed preconditions surface with a specific error naming which file was missing.

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

## 5. Route to Stage 2 — PER-TASK ANALYSIS (per-feature × per-task, parallel, bounded)

**v2.3 refactor: this stage was Stage 3 in v2.2.** Analysis now runs BEFORE compose+push, so `implementation.md` is written ONCE with all sections filled from real analysis outputs — no half-baked file ever gets pushed to MC.

For each approved feature, spawn a worker that:

1. Reads `plugins/dev/commands/references/plan/development-planning.md`.
2. Executes it verbatim on THIS feature.
3. Uses inner-axis parallelism (per-sub-task analysis for split; single task for parent-alone).

Each per-task worker inside Stage 2 spawns a `dev-agent` subagent to run readiness + impact + dev-plan analysis. **Writes to `dev/<repo>-analysis.md` (sub-task) or `dev/analysis.md` (parent-alone)** — an intermediate scratchpad with `doc_type: analysis-scratchpad`. **Does NOT write `implementation.md` yet. Does NOT push to MC yet.**

**Order of operations within a Stage 2 worker:**
1. Read this feature's `stage-1-results` block from `plan-run.md`
2. Pre-flight (MC status + local drift + cross-sub-task deps)
3. Readiness validation (base build green? harness ok? critical gaps?)
4. Impact analysis — 12-dimension matrix (frontend/backend/DB/authz/integrations/jobs/notifications/monitoring/tests/docs/flags/analytics)
5. Development planning — ordered build steps + test strategy + risks + rollback
6. Write `dev/<repo>-analysis.md` (or `dev/analysis.md` for parent-alone) with yaml sections: `build_sequence`, `impact_matrix`, `test_strategy`, `risks_and_rollback`
7. Emit skill invocations log to `plan-run.md` (each dev-agent invocation with inputs + outputs + duration)

---

## 6. Route to Stage 3 — BLOCKER DETECTION (per-feature × per-task, parallel, bounded)

**v2.3 refactor: this stage was Stage 3.5 in v2.2.** Now runs on Stage 2's analysis scratchpad (not on a partially-written implementation.md).

For each Stage-2-successful task, spawn a worker that:

1. Reads `plugins/dev/commands/references/plan/blocker-detection.md`.
2. Executes it verbatim on THIS task.

Blocker detection scans 5 sources:
- `tl-plan.md` `[HELD]` markers
- BA `open-questions.md` "Blocks build" rows
- BA `integrations.md` unresolved entries
- BA `system-landscape.md` gaps
- `dev/<repo>-analysis.md` `unknown` / `TBD` entries

**Outcomes per task:**

- **No blockers detected** → task proceeds to Stage 4 (compose + push).
- **Blockers detected** → task writes `dev/<repo>-plan-blockers.md` (`status: OPEN`), sets state to `BLOCKED_ON_PLAN`, MC status `blocked`. HALT THIS task at Stage 3. Do NOT proceed to Stage 4 for this task; siblings continue independently.

**Batch behaviour:**

- Blockers on ONE task never halt the batch — same failure-isolation as Stages 1 + 2. Other tasks that are clean reach Stage 4 normally.
- Batch summary (§8) surfaces every task's blocker state.

### 6a. Stage 3 on `--resume` — Blocker fold

When invoked with `--resume`, for each task whose `dev/<repo>-plan-blockers.md` exists AND `status: OPEN` or `RESOLVING`:

1. Reads `plugins/dev/commands/references/plan/blocker-fold.md` and executes verbatim.
2. If every `PB-###` has a filled `Resolution:` → folds each per the per-category rules **INTO THE `dev/<repo>-analysis.md` SCRATCHPAD** (not into `implementation.md` — the analysis is the source of truth; `implementation.md` gets composed AFTER at Stage 4). Logs `DEC-###`, sets file `status: RESOLVED`, task advances to Stage 4.
3. If any `PB-###` still has a placeholder `Resolution:` → halts THIS task's fold with a targeted message listing the unresolved PB-###; task stays `BLOCKED_ON_PLAN`.
4. If a fold error occurs (missing scratchpad section) → halts, preserves user's Resolution field, sets `status: OPEN`, writes an error line.

Tasks whose `plan-blockers.md` is already `RESOLVED` (or never had one) skip §6a entirely — proceed directly to Stage 4.

---

## 7. Route to Stage 4 — COMPOSE + MC PUSH (per-feature × per-task, parallel, bounded)

**v2.3 refactor: this stage was Stage 2 in v2.2.** Now runs AFTER analysis + blocker detection, so `implementation.md` is written ONCE with ALL sections filled.

For each Stage-3-clean task, spawn a worker that:

1. Reads `plugins/dev/commands/references/plan/implementation-preparation.md`.
2. Executes it verbatim on THIS task.

**Hard preconditions — this stage REFUSES to run if:**
- `dev/<repo>-analysis.md` (sub-task) OR `dev/analysis.md` (parent-alone) is missing OR has empty required sections
- `dev/<repo>-plan-blockers.md` exists with `status: OPEN` or `RESOLVING`

**Order of operations within a Stage 4 worker:**

1. Verify Stage 4 preconditions — halt with `stage_4_precondition_failed` naming which precondition + which file, if any fail
2. Apply the sub-task decision rule (§6a of the reference — was Stage 2's rule; unchanged)
3. Fan out N `tl-agent` subagents (split) or 1 (parent-alone) invoking `tl-feature-compose` in `implementation` mode. **The skill reads BOTH the TL context units AND `dev/<repo>-analysis.md`; produces ALL 10 sections of `implementation.md` in ONE pass.** For split, also invoke `tl-feature-compose` in `description` mode per sub-task, producing the 6-section `description.md`.
4. Write `subtask/<repo>/{description.md, implementation.md, status.md}` (sub-task) or `features/<slug>/{implementation.md, status.md}` (parent-alone)
5. Sequential MC push: `subtask_upsert_bundle` → `feature_update_implementation` (parent rollup for split) → `feature_update_implementation` (each sub-task's Implementation)
6. Update sync-state
7. Emit skill invocations log to `plan-run.md`

### 6c. Halt output when blockers surface

When Stage 3.5 detects blockers and halts, print (per task):

```
✗ /dev:plan halted for <task-ref> — <N> plan-time decisions require resolution:

  PB-001  <short title>              [Blocks <AC/BR/dev-plan step>]
  PB-002  <short title>              [Blocks <...>]

Resolve them:
  1. Open: <task-folder>/dev/<repo>-plan-blockers.md (parent-alone: dev/plan-blockers.md)
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
            applied to: implementation.md §2 Impacted components §Integrations, implementation.md §1 step 3
            logged as DEC-042
  PB-002 → resolved (option 1: composite uniqueness)
            applied to: implementation.md §2 Impacted components §Stored data, implementation.md §1 step 1
            logged as DEC-043

MC tasks (verified):
  ↳ Feature-1 (parent)      https://mission-control.techjays.com/task/6a94fe0e...   ✓ verified (5,953 chars)
  ↳ Subtask-2 (backend)     https://mission-control.techjays.com/task/6a95e0a0...   ✓ verified (2,343 + 32,419 chars)
  ↳ Subtask-3 (frontend)    https://mission-control.techjays.com/task/6a95e0a1...   ✓ verified (2,432 + 39,454 chars)

Local state:  PLANNED
MC status:    readyForDev

Read-back verification: 3/3 pushes byte-identical (v2.3.17 §4f.i)

Next: /dev:build <task-ref>
```

**Same Rule 7.0 checklist applies:** every task_object_id has a URL, every push shows the read-back token, table format is forbidden without a URL column. `--resume` success is not "complete" until every pushed task has both a URL AND a read-back result rendered.

---

## 7. Batch summary

After all workers complete (or fail), print the summary.

**Rule 7.0 — Every task line MUST show its MC UI URL. No exceptions. No table format that drops the URL column. If you print a task_object_id, you print the URL next to it.**

Under v2.3.17, before emitting the summary, verify:
- Every parent task line has a `<UI_BASE>/task/<task_object_id>` URL rendered.
- Every sub-task line has a `<UI_BASE>/task/<subtask_object_id>` URL rendered.
- Every task with a task_object_id but no URL rendered → the summary is INCOMPLETE — recompute URLs and re-render before printing.
- If choosing a table format instead of bullets, the table MUST have a `URL` column; a compact table like `| Task | MC id | Status | Content |` is INSUFFICIENT because it hides the clickable link. Prefer bullets (see canonical shape below) OR a table with an explicit `URL` column.

Additionally (v2.3.17): every pushed task line reports the read-back verification result inline — `✓ verified` (local + server SHA-256 match) or `✗ readback-mismatch <N/M chars>` (local vs server length + first diff offset). This surfaces the silent-content-loss class of bug the /dev:plan Stage 4 §4f.i read-back check catches.

**How task-mcp emits URLs (READ from response, do NOT construct locally).**

task-mcp builds URLs SERVER-SIDE using its own `mission_control_ui_url` env var and returns them in EVERY upsert / list / read response. The plugin just reads the fields — never constructs URLs itself. Fields to read:

| Response call | Field | Contains |
|---|---|---|
| `feature_upsert_bundle` | `.features[].view_url` | Direct URL to each parent task (`<UI_BASE>/task/<task_object_id>`) |
| `feature_upsert_bundle` | `.solution_view_url` | Solution dashboard URL |
| `feature_upsert_bundle` | `.list_view_url` | The MC List the feature lives under |
| `subtask_upsert_bundle` | `.results[].view_url` | Direct URL to each sub-task |
| `subtask_upsert_bundle` | `.parent_view_url` | URL to the parent task |
| `subtask_upsert_bundle` | `.solution_view_url` | Solution dashboard URL |
| `subtask_list` | `.subtasks[].view_url` | Per-sub-task direct URL |
| `subtask_list` | `.parent_view_url` | Parent task URL |
| `feature_update_implementation` | `.solution_view_url` | Solution dashboard URL |
| `subtask_update_implementation` | `.results[].view_url` | Per-sub-task URL |
| `subtask_update_implementation` | `.parent_view_url` | Parent task URL |
| `get_task_by_id_or_number` | `.view_url` | Direct URL for the resolved task |

**Primary path — always prefer the response `view_url`.** After every Stage 4 push, the response objects already carry every URL the summary needs. Collect them:

```python
# After Stage 4 push
parent_url         = feature_upsert_response["features"][0]["view_url"]
subtask_urls       = { r["subtask_object_id"]: r["view_url"] for r in subtask_upsert_response["results"] }
solution_dashboard = feature_upsert_response["solution_view_url"]
```

**Fallback path — only for tasks NOT pushed this run** (e.g. `skipped-unchanged` features from `sync-state.json`, or `BLOCKED_ON_PLAN` tasks where Stage 4 didn't reach push):
- Call `get_task_by_id_or_number(solution_id, task_id)` — the response includes `view_url`. This is the SUPPORTED way to get a URL for an existing task.
- Do NOT try to construct URLs locally from `.jetrix/project.json`. The `mission_control_ui_url` in `project.json` is not authoritative — task-mcp's own env var is. If you construct locally and the two drift, your URL is wrong.

**If both paths fail** (fresh feature never pushed AND `get_task_by_id_or_number` returns no view_url) → print `(not yet in MC)` inline, do NOT invent a URL.

**Canonical summary shape (use this exact bullet form, not a table):**

```
✓ /dev:plan complete

Batch summary: .jetrix/dev/batch-runs/plan-run-2026-08-29-143207.md

Succeeded (4):
  · Feature-4  Supplier Onboarding                    → 3 sub-tasks, PLANNED
    ↳ Parent:               https://mission-control.techjays.com/task/6a94fe0ebc48d4e7d1cab15b   ✓ verified (5,953 chars)
    ↳ Subtask-7 (backend)   PLANNED   https://mission-control.techjays.com/task/6b72a1c48d4e7d1cab2c7   ✓ verified (2,343 + 32,419 chars)
    ↳ Subtask-8 (frontend)  PLANNED   https://mission-control.techjays.com/task/6b72a2d59e5f8e6cbc3d8   ✓ verified (2,432 + 39,454 chars)
    ↳ Subtask-9 (mobile)    PLANNED   https://mission-control.techjays.com/task/6b72a3e6af609f7dcd4e9   ✓ verified (2,187 + 28,102 chars)
  · Feature-9  Outlet Discovery                       → 2 sub-tasks, PLANNED
    ↳ Parent:               https://mission-control.techjays.com/task/6a94ff0e...   ✓ verified (4,213 chars)
    ↳ Subtask-10 (backend)  PLANNED   https://mission-control.techjays.com/task/6b72a4f7...   ✓ verified (2,109 + 29,833 chars)
    ↳ Subtask-11 (frontend) PLANNED   https://mission-control.techjays.com/task/6b72a5g8...   ✓ verified (2,214 + 35,712 chars)
  · Feature-12 RFP Generation                         → parent-alone, PLANNED
    ↳ Parent:               https://mission-control.techjays.com/task/6a95001a...   ✓ verified (33,441 chars)
  · Feature-15 Reporting Dashboard                    → 2 sub-tasks, PLANNED
    ↳ Parent:               https://mission-control.techjays.com/task/6a950122...   ✓ verified (5,201 chars)
    ↳ Subtask-12 (backend)  PLANNED   https://mission-control.techjays.com/task/6b72a6...   ✓ verified (2,301 + 30,105 chars)
    ↳ Subtask-13 (frontend) PLANNED   https://mission-control.techjays.com/task/6b72a7...   ✓ verified (2,388 + 37,220 chars)

Blocked on plan (1):
  ✗ Feature-7  Supplier Approval                     → BLOCKED_ON_PLAN (2 open blockers)
    ↳ Parent:               https://mission-control.techjays.com/task/6a950230...
    ↳ Blockers:             features/supplier-approval/dev/backend-plan-blockers.md
    Resolve:                /dev:resolve --plan Feature-7

Failed at Stage 1 (0)

Skipped unchanged (0)

Compose lint findings (WARN, non-blocking):
  · Feature-4 backend §3: missing "Session-expiry handling" one-liner on POST /supplier
  · Feature-9 frontend §5: adjacent-sentence redundancy at line 82–83

Read-back verification: 11/11 pushes byte-identical (v2.3.17 §4f.i)

Next:
  · Resolve Feature-7's blockers:            /dev:resolve --plan Feature-7
  · Start building unblocked tasks:          /dev:build Subtask-7   (Feature-4's backend)
                                             /dev:build Feature-12  (parent-alone)
```

**Non-negotiable elements in the summary (fail-loud checklist BEFORE printing):**

1. Every task line with a `task_object_id` has a `https://.../task/<id>` URL rendered inline. If ANY line has an id but no URL, the summary is malformed — recompute + re-render.
2. Every pushed task shows a read-back verification token: `✓ verified (<local_char_count>[ + <server_char_count>] chars)` for match, `✗ readback-mismatch <local>/<server> chars` for mismatch.
3. If ANY read-back mismatched, elevate the whole feature to a "⚠ Verification failures" section BEFORE "Next:" — the summary is not "complete" while a mismatch stands.
4. If ANY compose lint WARN findings were emitted (Rule 0b), show the count + short list under a "Compose lint findings (WARN, non-blocking)" section. Zero WARNs → omit the section entirely.
5. Table format is FORBIDDEN unless it includes an explicit `URL` column. Bullets (as shown above) are preferred and canonical.

**How to extract `view_url` from responses (canonical — see Rule 7.0 above for the full field table):**

- Parent: `feature_upsert_bundle` response `.features[].view_url` — one per feature per group
- Sub-task: `subtask_upsert_bundle` response `.results[].view_url` — one per sub-task
- For skipped-unchanged features (no fresh push this run): call `get_task_by_id_or_number(solution_id, task_object_id)` — the response includes `view_url`. Do NOT construct URLs locally from `.jetrix/project.json`.
- For BLOCKED_ON_PLAN tasks (Stage 4 didn't run because blockers open): same — call `get_task_by_id_or_number` if the parent's `task_object_id` is known from a prior run's sync-state.
- If NO `task_object_id` is available (fresh feature never pushed AND no prior sync-state entry) → print `(not yet in MC)`. Never invent a URL.

**Why we do not build URLs locally:** task-mcp's `mission_control_ui_url` env var is the source of truth. `.jetrix/project.json`'s `mission_control_ui_url` may be a stale mirror. If the two drift (staging vs prod, or config out of sync), a locally-built URL points to the wrong place. task-mcp's own construction is guaranteed correct because it's the same code that would resolve any inbound MC UI redirect.

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
