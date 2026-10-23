---
description: "Just-in-time planning for one or many tasks. Verifies the technical context graph is current (auto-runs forward planning if missing), decides whether each task needs sub-tasks (multi-repo → one sub-task per repo, single-repo or bug/story → parent alone), composes each sub-task's Description + Implementation and creates them in Mission Control, writes the local development plan, and (v2.2) surfaces every plan-time decision that would require build-time input as PB-### blockers in units/<repo>/plan-blockers.md — so /dev:build never has to prompt. Blank plans every unplanned feature (MC todo) in the requirement as one batch, the same shape as /ba:features. Also accepts a single MC task number (Task-N, Feature-N, Subtask-N), a local feature slug or folder path, the internal FEAT-<AREA>-NN id, or a multi-target form — an MC List name, requirement=<slug>, or --all — which fans out across every matching feature in parallel. Runs 4 stages: identity resolution → code-context readiness → implementation preparation → development planning + blocker detection. With --resume: if a task has an OPEN units/<repo>/plan-blockers.md, folds every filled Resolution: field into implementation.md §1-§9 + registers deterministically per category, logs each fold as a DEC-###, and moves the task from blocked to readyForDev. Two parallelism axes: across features (bounded by --concurrency, default 5) and within a feature (per-sub-task compose + per-task planning). One consolidated user checkpoint after stage 1 to confirm the split for every targeted feature. Failure of one feature never halts the batch — failed features report at the end with escalations or plan-blockers. Never merges, never runs code — leaves each task at status readyForDev for /dev:build. Blockers are asked in the conversation as they arise — answered ones fold and the task plans on; only deferred ones land at blocked for /dev:resolve later."
argument-hint: "<task-number | Task-N | slug | features/<slug> | tasks/<slug>.md | <any-task.md> | "<plain description>" | FEAT-<AREA>-NN | list=<name> | requirement=<slug> | --all | (blank = every unplanned feature in the requirement)> [--split | --no-split] [--resume] [--dry-run] [--concurrency=N]"
---

# /dev:plan

You are the entry point for `/dev:plan`. **Orchestrator only** — this file parses arguments, does Stage 0 (identity resolution + target-set expansion + BA-file pull check), then routes to three stage reference files that carry the detailed logic. Do NOT paraphrase the stage files' instructions — Read them and execute verbatim, exactly the way `/jetrix:push` routes to its per-stage files.

Read the **`delivery-os-conventions`** skill first if it's not in context — the workspace layout, frontmatter standard, stable-ID rules, and the sub-task section (§v2.1). Then read this feature's context:

- `.jetrix/project.json` — solution + apps + `repolocation.json` for repo → path mapping
- The BA feature files (`features/<slug>/*.md`) for whichever features Stage 0 resolves
- `shared-context/decision-log.md` — you'll append `DEC-###` rows for material planning decisions. **Only the batch owner mints an id.** Workers run concurrently and the log is shared, so a worker that reads the last id and adds one will collide with its siblings — two features in a 7-feature run were handed the same `DEC-###` and a human had to separate them. A worker returns its proposed rows; the owner assigns ids and appends them in one write after the batch settles. Never append to the shared log from inside a worker.

Everything you write goes to `.jetrix/requirements/<slug>/features/<slug>/units/<repo>/` or `.jetrix/plan-runs/`. **There is no `dev/` folder** — each unit holds its own work. Never modify code, never merge, never touch secrets.

---

## 0. Preflight — confirm the workspace and MCP registration

Standard checks before any work:

1. Walk up from `$PWD` looking for `.jetrix/project.json` (up to 3 parent levels). If missing → tell the user to run `/jetrix:init` first and stop.
2. Read `solution_id`, `solution_slug`, and `apps[]` from `project.json`. Note the folder that CONTAINS `.jetrix/` as `workspace_root`; the container at `<workspace_root>/.jetrix/` as `project_root`.
3. Read `.jetrix/cache/repolocation.json` — for each app in `apps[]`, resolve its absolute local path. `SKIPPED` or absent means that repo is unavailable — log and continue, but name it and the fix in the run summary rather than burying it: `<repo> has no local path — /jetrix:init refresh`. A feature that turns out to span it will halt at `/dev:build` otherwise.
4. Confirm `task-mcp` is available. MCP tools may be listed directly **or deferred**, so resolve it rather than eyeballing: if `mcp__task-mcp__*` tools are already in your tool list, that's your answer; otherwise run `ToolSearch` with `select:mcp__task-mcp__get_task_by_id_or_number`. A returned schema means registered; `No matching deferred tools found` means it isn't → tell the user to run `/delivery-os:setup` and stop.

   **Never run `claude mcp list` for this.** It health-checks *every* registered MCP server over the network — including unrelated claude.ai connectors — so on a machine with many of them it blocks for minutes or never returns, and `/dev:plan` appears to hang with no output before doing any work.

   **Never conclude "not registered" from an empty tool list alone.** Where the harness defers MCP tools they are absent until searched, so that check alone reports a false negative and stops a run whose MCP is perfectly healthy.

   The check must stay here rather than deferring to the first real call: only the `Task-N` and blank forms hit `task-mcp` during Stage 0. A local slug or `FEAT-<AREA>-NN` resolves from local files, so its first MCP call is Stage 4 — by which point the analysis subagents have already run and written `units/<repo>/analysis.md` and `units/<repo>/plan-blockers.md`.
5. Confirm `features/` **or** `tasks/` exists under `project_root`. Both are valid sources: `features/<slug>/` holds BA-decomposed features, `tasks/<slug>.md` holds non-feature tickets (bug / story / ad-hoc task) pulled straight from MC. If neither exists → tell the user to run `/ba:features`, `/jetrix:pull scope`, or `/jetrix:pull task <ref>` and stop.

---

## 1. Parse arguments

`$ARGUMENTS` may contain:

**Target (required, unless blank for "every unplanned feature in the requirement"):**

*Single-target forms:*
- **Task number** — `11` (bare) or `Task-11` / `Feature-11` / `Subtask-11`. A bare integer is accepted wherever a target is, and means `Task-<n>`. This is the normal form — it is what Mission Control shows, and it needs no knowledge of where anything sits on disk.
- Local slug: `supplier-onboarding`
- Local folder path: `features/supplier-onboarding`
- Internal id: `FEAT-<AREA>-NN`
- Blank: **every unplanned feature** (MC `todo`) in the workspace's requirement, fanned out as one batch — the same shape as `/ba:features`, which plans a whole scope rather than one item. Ask only when the workspace holds more than one requirement, and then only to pick which. Never target `readyForDev`: that is this command's own output.

*Multi-target forms:*
- `list=<name>` or `list="Supplier Management"` (bare quoted string with no other match also treated as list name)
- `requirement=<slug>` (matches `tl-feature-planning` (internal), `/dev:build` convention)
- `--all` (every unplanned feature at MC `todo`; combined with `requirement=<slug>` filters to that initiative)

**Flags:**
- `--split` — force sub-task creation regardless of repo count
- `--no-split` — force parent-alone regardless of repo count
- `--resume` — continue from last completed stage per `status.md` § `## Run history` (batch and per-feature)
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
   - Decide the track per **§2a.1** below — `taskType` alone is not sufficient.
   - Result: `(feature_id from metadata.externalId, task_object_id, task_number, task_type, track)`.

#### 2a.1 Which track — BA feature, or a ticket someone filed by hand?

The two tracks read different inputs, so mis-routing is not cosmetic: send a hand-filed ticket down the feature track and §2c looks for 8 BA files that will never exist, marks it `SKIPPED_MISSING_BA`, and drops it. Decide in this order and stop at the first that answers.

**1 — What is on disk wins.** It reflects what actually exists, not what a field claims.

| Found locally | Track |
|---|---|
| `features/<slug>/feature.md` carrying this `feature_id` | feature |
| `tasks/<slug>.md` carrying this `task_object_id` | non-feature |

**2 — Nothing local yet: `taskType` *and* the id shape together.** BA-authored features always carry `taskType: feature` **and** an `externalId` matching `FEAT-<AREA>-NNN` (`FEAT-SUP-001`, per `delivery-os-conventions` §3). Both → feature track; pull it and proceed.

**3 — `taskType: feature` without the BA shape → non-feature track.** A person opened MC, created a ticket and picked "feature" from the type dropdown. It is labelled like a BA feature and structurally is not one. This is decidable, not a judgement call: `/jetrix:push feature` has `REQUIRED_FILES = ("feature.md", "acceptance-criteria.md")` and **halts** without them, so every feature that reached MC through the BA path has a `FEAT-<AREA>-NNN` id *and* non-empty `acceptanceCriteria`. Missing either → it did not come from `/ba:features` → non-feature track. Note it in the run summary; do not ask.

**4 — Anything else** (`bug`, `story`, `task`, `epic`) → non-feature track (§2f). The target is `tasks/<slug>.md`, auto-pulled via `/jetrix:pull task <ref>` §7 if not already on disk.

Routing is deterministic at every step — no prompt. A target resolved here reads only its own track's instructions.

**Do not route on `metadata.source` or `aiGenerated`.** Every plugin push stamps `source: "ai"` — `/jetrix:push feature` and `/jetrix:push task` alike — so it separates *plugin-pushed* from *typed-into-MC*, which is not the question being asked here. A bug pushed by the plugin is still a bug.
2. **Local slug or folder path** — match against `features/<slug>/`, read `feature.md` frontmatter → `(feature_id, jetrix_task_object_id, jetrix_task_number)`. A path or slug matching `tasks/<slug>.md` instead resolves to the **non-feature track** (§2f), reading `task_type` from that file's frontmatter.
2a. **Any other `.md` path — adopt it.** A markdown file outside `features/` and `tasks/` is a task someone wrote by hand. Do not refuse it and do not make them learn the convention first:

   - Derive the slug from the filename, or from the H1 where the filename is generic (`notes.md`, `task.md`, `untitled.md`).
   - Infer `task_type` from the content — steps-to-reproduce reads `bug`, "as a … I want" reads `story`, otherwise `task`. **State the inferred type in one line** so it can be corrected.
   - **Copy** it to `tasks/<slug>.md` with the frontmatter the non-feature track needs, and **leave the original where it is.** It is the author's input, not ours to relocate — moving it breaks their open editor tab and loses the thing they typed.
   - Write **no** `jetrix_task_object_id` or `task_object_id`. The adopted task is local until `/jetrix:push task <slug>` is run deliberately; minting an id here would create a duplicate ticket on the first push.
   - `tasks/<slug>.md` already exists → **stop and ask.** Never overwrite someone else's task.

   Then continue on the non-feature track (§2f) exactly as a pulled ticket would. Thin content is fine — a missing required input becomes a `PB-###` and `/dev:resolve` walks it.

3. **Internal `FEAT-<AREA>-NN`** — grep `features/*/feature.md` frontmatter for the id.
4. **Blank** — call `task-mcp.feature_list_bundle(solution_id, status='todo')` → take **all** of them as the target set, grouped by `requirement`. One requirement → plan the batch without asking. More than one → ask which requirement, not which feature. Fallback: scan `features/*/status.md` for `status: todo` if MC unavailable. Add any local `tasks/<slug>.md` not yet planned (no `tasks/<slug>/units/<repo>/status.md`) to the same set — a hand-filed ticket is legitimate unplanned work, and `feature_list_bundle` cannot see one because it filters to `taskType="feature"`. Report the set you are about to plan; do not ask the user to pick from it.

For **multi-target** forms:

5. **`list=<name>`** — call `task-mcp.feature_list_bundle(solution_id, list_name=<arg>)` → array of features → expand to N targets.
6. **`requirement=<slug>`** — grep `features/*/feature.md` frontmatter for `requirement: <arg>` → N targets. Cross-check with MC via `feature_list_bundle` to catch features not yet local (feeds §2c).
7. **`--all`** — call `task-mcp.feature_list_bundle(solution_id, status='todo')`; combined with `requirement=<slug>`, take every unplanned feature in that initiative.

**Free text — take it as the task.** An argument that matches nothing above and reads as prose rather than an identifier — it contains spaces, has no `/` or `.md`, and is not a `Task-N` / `FEAT-` form — is someone describing what they want. `/dev:plan "login page design, we want it animated"` is the most natural thing to type and must not be answered with a list of unrelated slugs.

Treat it exactly as §2a treats an adopted file, with one addition: **confirm before writing.** A path is something the user already made; a description is not, so say what you are about to create and let them correct it in one line — the slug you derived, the `task_type` you inferred, and the path you will write:

```
Creating tasks/login-page-animation.md  ·  task_type: task
  "login page design, we want it animated"
Planning from there — say the word if the slug or type is wrong.
```

Then continue on the non-feature track (§2f). A one-line description is thin by design: the inputs it lacks become `PB-###` and are asked in this same conversation, so typing a sentence and answering a few questions is a complete path from idea to plan.

Any input that is neither of these and still resolves to nothing → halt with the 5 nearest slugs / task numbers.

### 2a.1. Locate the work before planning it (unit-less targets)

A target created from a description or an adopted file carries **no `related_pages` / `related_apis` / `related_entities`**, so Stage 1's detection — which reads those from `feature.md` — has nothing to resolve and is skipped. Planning then runs on the sentence alone, and a plan that cannot name the file it changes is a guess.

Resolve the surfaces from the graph first — that is what it is for, and one index read beats searching every file:

1. **`context/code-context/` layer indexes**, where the repo has been mapped. A semantic index exists so the right unit is found without opening every file; one read gives you `PAGE-AUTH-01` and the files it cites. This is the fast path and should almost always hit.
2. **`.jetrix/connection-map.md`**, to pick the right repo first on a multi-repo solution before searching inside it.
3. **No code-context for the area → a blocker, not a grep.** Mint a *missing context* `PB-###` pointing at `/tl:code-map` (`blocker-detection.md` §5.2a) and ask it in this conversation like any other. Never auto-run the map: it writes a committed tree into the product repo, which is not a side effect one sentence should cause.

   This matches the non-feature track's existing rule and its reason — searching the source before the graph has said which unit owns the behaviour is how you fix the first plausible match instead of the actual cause.

   **One exception:** a task that *creates* a surface which does not exist yet has no unit to find, and that is not a missing-context blocker. Say which surface is new and plan it as new.

**Verify the hit, do not trust it.** A code-context unit is as-built at the commit it was generated from. Open one file it cites and confirm the thing is still there — where the repo has moved on, say the index is stale and raise it rather than planning against a unit that no longer matches the code.

**Record what you resolved**, so the plan is auditable rather than assumed:

```
Resolved from code-context (index): PAGE-AUTH-01 — src/components/Home.jsx, src/components/Home.css
```

**Record it either way.** "Resolved `PAGE-AUTH-01` from the index" and "no unit owns a login page in either mapped repo — is this new, or is the map behind?" are both useful. A confident plan against a file nobody confirmed exists is not.

### 2b. Write the resolved target set

Create `.jetrix/plan-runs/<timestamp>.md` (timestamp = `YYYY-MM-DD-HHMMSS`). This is the workspace-level batch summary. Each feature ALSO writes a per-feature journal at `features/<slug>/units/<repo>/status.md § ## Run history` — same schema, feature-scoped, so users can `cat features/<slug>/units/<repo>/status.md § ## Run history` and see every stage's skill invocations for that feature.

**Batch run schema** (workspace-level):

```yaml
---
doc_type: plan-run-batch
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

**Per-feature run schema** (`features/<slug>/units/<repo>/status.md § ## Run history`) — one section per stage, with skill-invocation logging so you can verify every stage's skills fired correctly:

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
          inputs: [feature.md, shared-context/data.md, shared-context/integrations.md]
          outputs: {dimensions_covered: 12, n_a_dimensions: 6, impacted_files: N}
          duration_ms: N
        - name: dev-agent (dev-plan)
          inputs: [tl units, feature.md, dependencies.md]
          outputs: {ordered_steps: N, test_scenarios: N, risks: N, decs_proposed: [DEC-...]}
          duration_ms: N
      scratchpad_written: units/backend/analysis.md
      finished_at: <ISO>

## Stage 3 — Blocker detection
stage_3:
  status: DONE | HALTED   # HALTED = blockers detected, this task
  tasks:
    - subtask_number: 1
      subtask_repo: backend
      invocations:
        - name: inline_5_source_scan
          sources: [tl-plan.md HELDs, dependencies.md, shared-context/integrations.md, shared-context/system-landscape.md, units/backend/analysis.md unknowns]
          outputs: {blockers_detected: N, ids: [PB-1-001, PB-1-002]}
          duration_ms: N
      blockers_file: units/backend/plan-blockers.md
      state_set: blocked | PROCEED_TO_STAGE_4
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
          inputs: [tl units, units/backend/analysis.md]
          outputs: {sections_written: [1,2,3,4,5,7,8,9], stubbed: [10], size_chars: N}
          duration_ms: N
        - name: tl-feature-compose (description mode)   # only when N > 1
          # One to two paragraphs of CONTINUOUS PROSE. No headings, bullets,
          # tables, code fences, HTTP codes or field lists — the skill is the
          # authority here, and it says prose. An earlier version of this log
          # named six headed sections, which is what it must never produce.
          inputs: [feature.md, tl units, units/backend/analysis.md § Overview]
          outputs: {paragraphs: N, size_chars: N}   # prose — the skill forbids headings
          duration_ms: N
        - name: task-mcp.subtask_upsert_bundle
          inputs: {solution_id, parent_task_id, subtasks: [<count>]}
          outputs: {ok: true, task_number: Subtask-7, version: 1, action: created}
          duration_ms: N
      files_written: [units/backend/description.md, units/backend/implementation.md, units/backend/status.md]
      finished_at: <ISO>
```

**How to verify every skill fired correctly:**

```bash
cat features/<slug>/units/<repo>/status.md § ## Run history
```

Every stage lists its skill invocations with inputs + outputs + duration. If a stage halted, `status: HALTED` + `skipped_reason` on later stages make it obvious. Missing inputs / failed preconditions surface with a specific error naming which file was missing.

`--resume` reads this file first — if `stage_status: completed` on a feature, skip.

### 2c. BA-file presence check (auto-detect missing files, prompt to pull)

**Feature-track targets only.** A non-feature target (§2f) has no BA folder by design — skip this entire step for it and use §2f's per-type input check instead. Running this check against a bug is the bug that made `/dev:plan` reject every non-feature ticket: all 8 files are "missing", `/jetrix:pull scope` cannot produce them, and the target is dropped as `SKIPPED_MISSING_BA`.

For each targeted feature, check `features/<slug>/` for the 8 BA files: `feature.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`.

**If any features are missing files**, print a consolidated summary:

```
✗ Missing BA files for 2 of 5 features:
    · Feature-4  Supplier Onboarding      (missing: nfrs.md)
    · Feature-9  Outlet Discovery         (missing: acceptance-criteria.md)

  Pull them from Jetrix now? [Y/n]
```

- `Y` (default) → invoke `/jetrix:pull scope` inline for just the affected features. Re-check after. Continue with anything now complete; mark still-missing as `SKIPPED_MISSING_BA` and log.
- `n` → mark affected features `SKIPPED_MISSING_BA`, continue with the rest.

All 8 BA files present → skip this step silently.

**Then, if the user asks for it, refresh comments + attachments.** This costs 2 MCP calls per
task — ~36 round-trips on a 19-feature batch — and every one of them is spent before any planning
starts. A team that leaves clarifications on the ticket needs them; a developer planning their own
batch usually does not. So ask **once, for the whole run, before any per-task work**:

```
Pull teammate comments and attachments from the tracker first?
  <N> tasks → ~<2N> calls.  Last fetched: <newest comments.md mtime, or "never">

  [y] fetch first    [N] start planning now (default)
```

- **`N` (default)** — skip the fetch and plan immediately. Say plainly in the run summary that
  comments were not fetched this run, so Stage 3 Source 6 contributed nothing: an unresolved thread
  on the ticket will NOT have become a `PB-###`. That is the whole cost of the default, and the
  summary must not leave the user to infer it.
- **`y`** — run the per-task refresh below, then continue.

Already-present `comments.md` files are left in place either way — skipping a refresh is not the
same as having no comments, and Stage 3 still reads whatever is on disk.

Never ask this per task, and never ask it again later in the run.

When the user answers `y`, run
`plugins/jetrix/commands/references/pull/comments-attachments.md` per target,
following the same rule `/jetrix:pull task` §8 uses — **once per task, and a
sub-task is a task**:

- the parent → `--target-dir` = `features/<slug>/`
- **every existing `features/<slug>/units/<repo>/` folder** → that folder,
  using that sub-task's own `jetrix_subtask_number` + `jetrix_subtask_object_id`
  from its `status.md` frontmatter (fall back to `subtask_list` if either is
  absent). Pass the parent's ids for the parent only — a sub-task carries its
  own MC task number and its own comment thread.

On a first plan the feature is not split yet, so only the parent is fetched —
sub-tasks do not exist until Stage 2 creates them. On a re-plan they do, and
skipping them is how a clarification left on the backend sub-task gets missed
by `/dev:build Subtask-N`, which reads `units/<repo>/comments.md` but never
fetches it.

`/jetrix:pull scope` deliberately does not fetch any of this — 2 calls per
task across a whole solution — so this is where the planner picks up
clarifications the team left on the ticket and any mockup or spreadsheet
attached to it. Unresolved comments become `PB-###` blockers in Stage 3
(Source 6). Non-blocking: a fetch failure logs and continues.

### 2d. Backfill `jetrix_task_number` if missing

For every remaining target, if `feature.md` frontmatter has `jetrix_task_object_id` but no `jetrix_task_number`, fetch it via `get_task_by_id_or_number` and patch the file. Non-blocking.

### 2e. Verify sub-task target resolution

If the user passed a `Subtask-N` (rare — usually they open the parent), we already walked up to parent in §2a step 1. Log this fact so the summary tells them we planned the parent (which touches this sub-task).

### 2f. Non-feature track — bug / story / task / epic

Target resolved to a non-feature by §2a.1 → **Read
`plugins/dev/commands/references/plan/non-feature-track.md` and execute it
verbatim.** It carries the whole track: read order, per-type input check,
compose, write-back, and push.

Then skip §2c and §3 for this target — they describe BA-feature inputs it does
not have. Rejoin the batch at the run summary.
---

## 3. Route to Stage 1 (per-feature, parallel)

For each successfully-resolved feature, spawn a **worker** (concurrency-bounded per `--concurrency=N`, default 5) that:

1. Reads `plugins/dev/commands/references/plan/code-context-readiness.md`.
2. Executes it verbatim on THIS feature.
3. Writes progress to this feature's `units/<repo>/status.md § ## Run history` per the reference file's spec.
4. Reports outcome (planned / auto-planned / blocked) to the batch summary.

Once EVERY feature's Stage 1 is complete (or reported as blocked), the orchestrator proceeds to §4.

---

## 4. Consolidated user checkpoint (single prompt for the whole batch)

Read each successful feature's `units/<repo>/status.md § ## Run history` `stage-1-results` block → compose the consolidated prompt.

**Single-target run:**

```
Feature: FEAT-SUP-001 Supplier Onboarding  (Feature-4 in MC)
Task type: feature
Repos touched: backend, frontend, mobile
Split decision: 3 sub-tasks
   units/backend    (sequence 1)
   units/frontend   (sequence 2)
   units/mobile     (sequence 3)

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

**This checkpoint confirms the split. It is not a scope picker.** The target set was already decided
— blank meant every unplanned feature, and a named target meant that one. So:

- **`Y` is the default and the recommendation, always.** Never mark a subset as recommended, never
  order the options so a subset reads as the sensible choice, and never describe the full set in
  terms that argue against it ("36 sub-tasks, ~36 analysis agents, a long Q&A session"). How much
  work the batch is, is not a reason for this command to shrink it. `pick=` exists for the user who
  wants a subset, and it stays theirs to reach for.
- **Never forecast blockers here.** Stage 3 has not run, and two of its six sources read
  `analysis.md`, which Stage 2 has not written yet — any count quoted at this point is invented. Do
  not count ledger rows as a proxy either: `Accepted (assumed)` and `Closed` rows are settled, and
  reporting them as open questions turns resolved work back into a reason to hesitate. The only
  questions that become `PB-###` are the ones the six sources in `blocker-detection.md` §5.1 find
  — `dependencies.md` rows marked **Blocks build**, not every row under `## Open questions`.

### The base branch is part of this checkpoint

**Ask it here, once, for the whole batch** — and never at `/dev:build`, which may not prompt mid-run. Every
feature branch this plan leads to is cut from the answer, so a wrong value is not noticed until a PR targets
the wrong place.

Resolve the recommendation from `.jetrix/project.json` `apps[].env_branches.dev`, then **show it and let the
user change it** with `AskUserQuestion`:

```
Which branch should these feature branches be cut from?

  develop                  ← from project.json (Inhouse-server, Inhouse-client)
  dev
  main                     requires --allow-protected-base
  other                    type the exact name
```

- **Never default silently.** `env_branches.dev` goes stale, and the value named a branch the user did not
  intend — that is why `/dev:commit` was changed to ask, and the same reasoning applies a stage earlier.
- **Repos disagreeing is normal.** When two apps resolve to different branches, show one row per repo and
  take an answer per repo; do not force one name across a workspace that does not use one.
- **`main` / `master` / `production`** → refuse unless the run carries `--allow-protected-base`.
- **Branch missing on the remote** → say so and re-ask. Do not offer to create it: a base branch that does
  not exist yet is a repo-setup decision, not a planning one.

**Write the answer to each task's `status.md` `base_branch:`.** That is what makes it a decision rather than
a guess — `/dev:build` Stage 3 reads it, and `/dev:commit` Stage 2 confirms it rather than re-deriving.

`--dry-run` skips this prompt entirely (implicit no on MC writes, continues to Stage 2's compose so user can review the drafts).

Write the checkpoint result to the batch summary's `checkpoint_decision:` field, and the chosen base branch
(per repo where they differ) to `base_branch:`.

---

## 5. Route to Stage 2 — PER-TASK ANALYSIS (per-feature × per-task, parallel, bounded)

**v2.3 refactor: this stage was Stage 3 in v2.2.** Analysis now runs BEFORE compose+push, so `implementation.md` is written ONCE with all sections filled from real analysis outputs — no half-baked file ever gets pushed to MC.

For each approved feature, spawn a worker that:

1. Reads `plugins/dev/commands/references/plan/development-planning.md`.
2. Executes it verbatim on THIS feature.
3. Uses inner-axis parallelism (per-sub-task analysis for split; single task for parent-alone).

Each per-task worker inside Stage 2 spawns a `dev-agent` subagent to run readiness + impact + dev-plan analysis. **Writes to `units/<repo>/analysis.md` (sub-task) or `units/<repo>/analysis.md` (parent-alone)** — an intermediate scratchpad with `doc_type: analysis-scratchpad`. **Does NOT write `implementation.md` yet. Does NOT push to MC yet.**

**Order of operations within a Stage 2 worker:**
1. Read this feature's `stage-1-results` block from `status.md` § `## Run history`
2. Pre-flight (MC status + local drift + cross-sub-task deps)
3. Readiness validation (base build green? harness ok? critical gaps?)
4. Impact analysis — 12-dimension matrix (frontend/backend/DB/authz/integrations/jobs/notifications/monitoring/tests/docs/flags/analytics)
5. Development planning — ordered build steps + test strategy + risks + rollback
6. Write `units/<repo>/analysis.md` (or `units/<repo>/analysis.md` for parent-alone) with yaml sections: `build_sequence`, `impact_matrix`, `test_strategy`, `risks_and_rollback`
7. Emit skill invocations log to `status.md` § `## Run history` (each dev-agent invocation with inputs + outputs + duration)

---

## 6. Route to Stage 3 — BLOCKER DETECTION (per-feature × per-task, parallel, bounded)

**v2.3 refactor: this stage was Stage 3.5 in v2.2.** Now runs on Stage 2's analysis scratchpad (not on a partially-written implementation.md).

For each Stage-2-successful task, spawn a worker that:

1. Reads `plugins/dev/commands/references/plan/blocker-detection.md`.
2. Executes it verbatim on THIS task.

Blocker detection scans 6 sources:
- `tl-plan.md` `[HELD]` markers
- BA `dependencies.md` § `## Open questions` "Blocks build" rows
- BA `integrations.md` unresolved entries
- BA `system-landscape.md` gaps
- `units/<repo>/analysis.md` `unknown` / `TBD` entries
- `discussion.md` § `## Comments` unresolved threads (team clarifications left on the ticket)

**Outcomes per task:**

- **No blockers detected** → task proceeds to Stage 4 (compose + push).
- **Blockers detected** → task writes `units/<repo>/plan-blockers.md` (`status: OPEN`) and holds at Stage 3. Siblings continue independently.

  **Then ask, rather than halting.** The file is the record, not the mechanism. Once every target in the batch has finished Stage 3, run the `/dev:resolve` loop **inline, in this conversation** — do not make the user leave and type a second command for a question you are already holding:

  - Present each open `PB-###` one at a time with its options and your recommendation, grouped by target so a 7-feature batch is one pass of questions rather than seven `--resume` runs.
  - Fold each answer as it arrives, log the `DEC-###`, and carry that target straight on to Stage 4.
  - Re-screen the remaining blockers after every answer and **drop any the answer just settled**, saying which. One decision often closes three.
  - A target whose blockers are all answered never enters `blocked` at all — that state is for work genuinely left open, not for a question asked and answered in the same sitting.

  **Deferring is one word.** Any blocker the user defers, and any target still carrying one when they stop, sets `blocked` + MC `blocked` as before, with the file holding the unanswered questions. `/dev:resolve` then works exactly as it does today for the walk-away case — it stays the right command for coming back tomorrow, and stops being the price of answering now.

**Batch behaviour:**

- Blockers on ONE task never halt the batch — same failure-isolation as Stages 1 + 2. Other tasks that are clean reach Stage 4 normally.
- Batch summary (§8) surfaces every task's blocker state.

### 6a. Stage 3 on `--resume` — Blocker fold

When invoked with `--resume`, for each task whose `units/<repo>/plan-blockers.md` exists AND `status: OPEN` or `RESOLVING`:

1. Reads `plugins/dev/commands/references/plan/blocker-fold.md` and executes verbatim.
2. If every `PB-###` has a filled `Resolution:` → folds each per the per-category rules **INTO THE `units/<repo>/analysis.md` SCRATCHPAD** (not into `implementation.md` — the analysis is the source of truth; `implementation.md` gets composed AFTER at Stage 4). Logs `DEC-###`, sets file `status: RESOLVED`, task advances to Stage 4.
3. If any `PB-###` still has a placeholder `Resolution:` → halts THIS task's fold with a targeted message listing the unresolved PB-###; task stays `blocked`.
4. If a fold error occurs (missing scratchpad section) → halts, preserves user's Resolution field, sets `status: OPEN`, writes an error line.

Tasks whose `plan-blockers.md` is already `RESOLVED` (or never had one) skip §6a entirely — proceed directly to Stage 4.

---

## 7. Route to Stage 4 — COMPOSE + MC PUSH (per-feature × per-task, parallel, bounded)

**v2.3 refactor: this stage was Stage 2 in v2.2.** Now runs AFTER analysis + blocker detection, so `implementation.md` is written ONCE with ALL sections filled.

For each Stage-3-clean task, spawn a worker that:

1. Reads `plugins/dev/commands/references/plan/implementation-preparation.md`.
2. Executes it verbatim on THIS task.

**Hard preconditions — this stage REFUSES to run if:**
- `units/<repo>/analysis.md` (sub-task) OR `units/<repo>/analysis.md` (parent-alone) is missing OR has empty required sections
- `units/<repo>/plan-blockers.md` exists with `status: OPEN` or `RESOLVING`

**Order of operations within a Stage 4 worker:**

1. Verify Stage 4 preconditions — halt with `stage_4_precondition_failed` naming which precondition + which file, if any fail
2. Apply the sub-task decision rule (§6a of the reference — was Stage 2's rule; unchanged)
3. Fan out N `tl-agent` subagents (split) or 1 (parent-alone) invoking `tl-feature-compose` in `implementation` mode. **The skill reads BOTH the TL context units AND `units/<repo>/analysis.md`; produces ALL 10 sections of `implementation.md` in ONE pass.** For split, also invoke `tl-feature-compose` in `description` mode per sub-task, producing the 6-section `description.md`.
4. Write `units/<repo>/{description.md, implementation.md, status.md}` (sub-task) or `features/<slug>/{implementation.md, status.md}` (parent-alone)
5. Sequential MC push: `subtask_upsert_bundle` → `feature_update_implementation` (parent rollup for split) → `feature_update_implementation` (each sub-task's Implementation)
6. Update sync-state
7. Emit skill invocations log to `status.md` § `## Run history`

### 6c. Halt output when blockers surface

When Stage 3.5 detects blockers and halts, print (per task):

```
✗ /dev:plan paused for <task-ref> — <N> decisions left unanswered:

  PB-001  <short title>              [Blocks <AC/BR/dev-plan step>]
  PB-002  <short title>              [Blocks <...>]

Blockers file: <task-folder>/units/<repo>/plan-blockers.md   (parent-alone: units/<repo>/plan-blockers.md)
               — the full question, options and recommendation for each PB-###

This block prints only for blockers you deferred, or when the run could not reach
you. Anything answered in the conversation is already folded and planned.

Pick them up later with:
  /dev:resolve --plan Feature-7      walks each remaining PB-### with options + a
                                     recommendation, then resumes the plan for you

  or by hand:
  1. Fill in the "Resolution:" field under each PB-### in the file above
  2. Re-run: /dev:plan --resume <task-ref>

Then: /dev:build <task-ref>

Status: blocked (MC: blocked)
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

Status:        readyForDev

Read-back verification: 3/3 pushes byte-identical (v2.3.17 §4f.i)

Next: /dev:build <task-ref>
      /dev:build <task-ref> --skip-qa    # no test harness for this change
                                         # (a CSS value, a copy fix, a config default)
```

**Same Rule 7.0 checklist applies:** every task_object_id has a URL, every push shows the read-back token, table format is forbidden without a URL column. `--resume` success is not "complete" until every pushed task has both a URL AND a read-back result rendered.

---

## 6b. Publish the planned context — branch, push, PR

Stage 1 writes forward-planned units into each repo's `context/code-context/`. That tree is
**committed with the code** (`delivery-os-conventions` §3, Model B), so planning is not finished when
the files exist on disk — it is finished when a teammate can see them.

Until this section existed, `/dev:plan` wrote the units and said nothing about git. The agent
improvised a branch, committed to it, and stopped: the work sat on an unpushed local branch, the user
pushed it by hand, and no PR was ever raised. Nothing in the command was wrong, because nothing in the
command said anything at all.

Per repo whose `context/code-context/` this run changed — skip any repo with no changes:

1. **Branch off the base the user confirmed at §4**, not off whatever is checked out:

   ```bash
   git -C <repo> checkout -b context/plan-<requirement-slug>-<YYYY-MM-DD>
   ```

   Replace `/` in the slug with `-`. Branch exists already (a re-run the same day) → append `-2`,
   `-3`. Never force, never reuse.

2. **Stage only the context tree** — never `git add -A`, never `git add .`. A blanket add sweeps up
   whatever else is dirty in that working tree, and on a real run of `/tl:code-map` that meant a
   committed `.env` holding live database credentials:

   ```bash
   git -C <repo> add context/code-context
   git -C <repo> status --short -- context/code-context
   ```

3. **Commit**, naming what it holds and what it was planned against:

   ```bash
   git -C <repo> commit -m "docs(context): plan <requirement-slug> units (forward-planned, Proposed)

   <N> units across <layers> · <M> features
   planned against <base-branch> @ <sha>"
   ```

4. **Push, and set upstream** — `-u` is not optional. Without it the branch has no tracking ref, and
   every later "is this pushed?" check answers wrongly:

   ```bash
   git -C <repo> push -u origin context/plan-<requirement-slug>-<YYYY-MM-DD>
   ```

5. **Raise the PR into the base branch the user confirmed at §4**, through the four-step ladder in
   [`stage-8-9-push-pr.md`](references/commit/stage-8-9-push-pr.md) §9c — the same one `/dev:commit`,
   `/qa:setup` and `/tl:code-map` use. Read it and follow it; do **not** call `gh pr create` on its
   own, and where the repo has a `PULL_REQUEST_TEMPLATE`, fill that template rather than inventing a
   body.

6. **Print the PR URL and the branch per repo in the batch summary.** A planned context nobody is
   asked to review is a plan nobody agreed to. Report `pushed: no` loudly with the reason if a push or
   PR fails — never let a failure here pass as success, and never leave the user to discover it by
   running `git status` themselves.

**Stay on the new branch.** `/dev:build` cuts feature branches from the confirmed base, not from this
one; switching back here only hides what was just written.

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

**Fallback path — only for tasks NOT pushed this run** (e.g. `skipped-unchanged` features from `sync-state.json`, or `blocked` tasks where Stage 4 didn't reach push):
- Call `get_task_by_id_or_number(solution_id, task_id)` — the response includes `view_url`. This is the SUPPORTED way to get a URL for an existing task.
- Do NOT try to construct URLs locally from `.jetrix/project.json`. The `mission_control_ui_url` in `project.json` is not authoritative — task-mcp's own env var is. If you construct locally and the two drift, your URL is wrong.

**If both paths fail** (fresh feature never pushed AND `get_task_by_id_or_number` returns no view_url) → print `(not yet in MC)` inline, do NOT invent a URL.

**Canonical summary shape (use this exact bullet form, not a table):**

```
✓ /dev:plan complete

Batch summary: .jetrix/plan-runs/2026-08-29-143207.md

Succeeded (4):
  · Feature-4  Supplier Onboarding                    → 3 sub-tasks, readyForDev
    ↳ Parent:               https://mission-control.techjays.com/task/6a94fe0ebc48d4e7d1cab15b   ✓ verified (5,953 chars)
    ↳ Subtask-7 (backend)   readyForDev   https://mission-control.techjays.com/task/6b72a1c48d4e7d1cab2c7   ✓ verified (2,343 + 32,419 chars)
    ↳ Subtask-8 (frontend)  readyForDev   https://mission-control.techjays.com/task/6b72a2d59e5f8e6cbc3d8   ✓ verified (2,432 + 39,454 chars)
    ↳ Subtask-9 (mobile)    readyForDev   https://mission-control.techjays.com/task/6b72a3e6af609f7dcd4e9   ✓ verified (2,187 + 28,102 chars)
  · Feature-9  Outlet Discovery                       → 2 sub-tasks, readyForDev
    ↳ Parent:               https://mission-control.techjays.com/task/6a94ff0e...   ✓ verified (4,213 chars)
    ↳ Subtask-10 (backend)  readyForDev   https://mission-control.techjays.com/task/6b72a4f7...   ✓ verified (2,109 + 29,833 chars)
    ↳ Subtask-11 (frontend) readyForDev   https://mission-control.techjays.com/task/6b72a5g8...   ✓ verified (2,214 + 35,712 chars)
  · Feature-12 RFP Generation                         → parent-alone, readyForDev
    ↳ Parent:               https://mission-control.techjays.com/task/6a95001a...   ✓ verified (33,441 chars)
  · Feature-15 Reporting Dashboard                    → 2 sub-tasks, readyForDev
    ↳ Parent:               https://mission-control.techjays.com/task/6a950122...   ✓ verified (5,201 chars)
    ↳ Subtask-12 (backend)  readyForDev   https://mission-control.techjays.com/task/6b72a6...   ✓ verified (2,301 + 30,105 chars)
    ↳ Subtask-13 (frontend) readyForDev   https://mission-control.techjays.com/task/6b72a7...   ✓ verified (2,388 + 37,220 chars)

Blocked on plan (1):                          ← deferred only; answered blockers are already folded
  ✗ Feature-7  Supplier Approval                     → blocked (2 deferred)
    ↳ Parent:               https://mission-control.techjays.com/task/6a950230...
    ↳ Blockers:             features/supplier-approval/units/backend/plan-blockers.md
    Resolve:                /dev:resolve --plan Feature-7

Failed at Stage 1 (0)

Skipped unchanged (0)

Compose lint findings (WARN, non-blocking):
  · Feature-4 backend §3: missing "Session-expiry handling" one-liner on POST /supplier
  · Feature-9 frontend §5: adjacent-sentence redundancy at line 82–83

Read-back verification: 11/11 pushes byte-identical (v2.3.17 §4f.i)

Next:
  · Review the planned context:   PR #212 Inhouse-server   PR #88 Inhouse-client

  · Build everything:            /dev:build
      11 tasks in 3 waves, ordered by depends_on_features:
        wave 1  Feature-4 backend · Feature-12            (nothing depends on first)
        wave 2  Feature-4 frontend · Feature-9 backend
        wave 3  Feature-9 frontend · Feature-15
      Each wave runs in parallel; the next starts when the one before finishes.

  · Or one at a time, in this order:
        /dev:build Subtask-7      ← start here (wave 1, Feature-4's backend)
        /dev:build Feature-12       (wave 1)
        /dev:build Subtask-8        (wave 2 — needs Subtask-7 merged)
      Building out of order puts a feature on a base without what it needs.

  · Deferred blockers:           /dev:resolve --plan Feature-7
    (add --skip-qa only for a change that does not justify a test harness)
```

**The two build paths are not a choice between more and less work — they are the same work, run
together or run one at a time.** Print both, every time, in this order:

1. **`/dev:build` on its own, first**, with the wave plan under it. This is the whole batch and the
   normal path; the command orders itself from `depends_on_features` (see `/dev:build` § fan-out), so
   the user never has to sequence anything.
2. **The explicit order underneath**, for the user who wants to go task by task and watch each one.
   Name the first task plainly — `← start here` — and say which wave each belongs to, so stopping
   halfway still leaves them somewhere sensible.

Never print only the per-task form; that was the bug where a batch of 18 ended up looking like a list
of 18 commands the user had to run by hand. Never recommend one path over the other on grounds of
size or duration (`delivery-os-conventions` § "What a question may be about") — both do the same
work, and which to use is a preference about watching it happen, not about scope.

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
- For blocked tasks (Stage 4 didn't run because blockers open): same — call `get_task_by_id_or_number` if the parent's `task_object_id` is known from a prior run's sync-state.
- If NO `task_object_id` is available (fresh feature never pushed AND no prior sync-state entry) → print `(not yet in MC)`. Never invent a URL.

**Why we do not build URLs locally:** task-mcp's `mission_control_ui_url` env var is the source of truth. `.jetrix/project.json`'s `mission_control_ui_url` may be a stale mirror. If the two drift (staging vs prod, or config out of sync), a locally-built URL points to the wrong place. task-mcp's own construction is guaranteed correct because it's the same code that would resolve any inbound MC UI redirect.

Also write the same content to `.jetrix/plan-runs/<ts>.md` (append the `## Summary` section to the file created in §2b).

---

## 8. Failure surfaces to always report

- **Stage 1 blocked** — feature `BLOCKED_STAGE_1` with escalation note
- **User cancelled at checkpoint** — batch summary shows `outcome: user_cancelled`; nothing published
- **Stage 2 blocked** — feature `BLOCKED_STAGE_2` with escalation note; other approved features unaffected
- **MC push refused** (permission_denied) — halt THIS feature; report which permission; continue batch
- **task-mcp subtask_upsert_bundle unavailable** (Dharma's addition not yet deployed) — Stage 2 halts with the specific tool name; recommend `--dry-run` in the meantime so composes still land locally
- **task-mcp `metadata.parentExternalId is not allowed`** on retry — task-mcp is running the pre-fix version. DO NOT hand-craft a payload that omits the field. task-mcp (v56c8212+) handles the metadata translation transparently — the plugin ALWAYS sends `parentExternalId` + `subtaskNumber` + `unitRepo`; task-mcp drops the first two and maps the third to `externalSlug` before forwarding to MC. Parent linkage is via `parent_task_id` (the tool input parameter), NOT `metadata.parentExternalId`. See `plugins/dev/commands/references/plan/implementation-preparation.md` §4e.i for the full translation table. If the error still happens, task-mcp needs to reload the fixed version — restart it; do not work around at the plugin.

---

## Guardrails

- Never invent BA content — Stage 0's BA-file check + prompt is the only path to fill missing files.
- Never invent TL graph units — Stage 1 auto-plans via `tl-feature-planning`, or escalates.
- Never convert a sub-task's `taskType` from `subtask` to anything else — invariant in Stage 2c.
- Never merge, never push code, never modify secrets.
- Retry limits mirror `/dev:build`: 1 auto-plan per Stage 1 pass; per-item error isolation on MC calls (a bad sub-task doesn't stop the batch).
- Every material design choice → `DEC-###` in `shared-context/decision-log.md`.
