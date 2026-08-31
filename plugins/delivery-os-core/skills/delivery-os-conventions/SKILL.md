---
name: delivery-os-conventions
description: The Techjays Delivery OS shared document contract. Read this before producing or consuming any Delivery OS document (scope, registers, shared, run summaries). Defines the workspace layout (v2.0 — role-centric, no <slug>/ wrapper), the document frontmatter standard, stable ID conventions, and the shared vocabulary (artifact statuses, confidence values, usage modes) that every agent — ba, doc, tl, qa — must speak so their outputs stay interoperable.
---

# Delivery OS — Shared Document Contract

This is the single source of truth that makes Delivery OS documents **shareable across agents and across weeks**. The BA Agent produces documents today; the Doc, TL, and QA agents consume them later. They only interoperate if every agent honors this contract.

> **Contract version: 2.3.** Bump `schema_version` in document frontmatter and update this file together when the contract changes.
>
> **2.3 (flat sub-task tabs + flat dev/ + single implementation source of truth — breaking).** File structure simplified per user's design intent. Under each `<feature-slug>/` (parent-alone) or each `<feature-slug>/subtask/<repo>/` (sub-task), MC-facing content is now **3 flat files**: `description.md` (→ MC Description tab), `implementation.md` (→ MC Implementation tab — SINGLE SOURCE OF TRUTH with 10 sections: business flow, build sequence, impacted components, API endpoints, database, frontend UI, touch points, test strategy, risks + rollback, how to verify locally), and `status.md` (MC-mirrored + local loop state — absorbs the retired `delivery-status.md`). **All local audit lives under ONE FLAT `dev/` folder at feature root** — `features/<slug>/dev/`. **NO nested `subtask/` folder inside `dev/`** — per-sub-task audit files use repo-slug PREFIX in the filename (e.g. `dev/backend-plan-blockers.md`, `dev/frontend-traceability.md`). Two folders with the same name (`subtask/` at feature root AND `subtask/` inside `dev/`) is a mistake, not a design. **No nested `dev/` inside sub-task roots** either — sub-task folders hold only the 3 MC-facing files. New per-feature file `dev/traceability.md` (parent-alone) or `dev/<repo>-traceability.md` (per sub-task) — the ID cross-reference map (AC ↔ BR ↔ EP ↔ implementation-step ↔ test ↔ PB ↔ DEC), local-only. **Retired doc_types:** `dev-plan`, `impacted-components`, `delivery-status`, `subtask-description` (folded into `description`), `subtask-implementation` (folded into `implementation`), `subtask-status` (folded into `status`), `local-runbook` (folded into `implementation.md § 10`). **Retired files/paths:** `dev/dev-plan.md`, `dev/impacted-components.md`, `dev/delivery-status.md`, `dev/local-runbook.md`, `subtask/<repo>/dev/*` (nested dev/ inside sub-task), `dev/subtask/<repo>/*` (nested subtask/ inside dev/ — replaced by flat repo-prefix filenames), `subtask/task-decision.md` (moved to `dev/task-decision.md`), `tl-plan.md` for parent-alone (split rollup still uses `tl-plan.md`). Backward compatibility: migration handled by `/jetrix:init` when it detects v2.2 layout on disk.
>
> **2.2 (plan-time blocker resolution — additive).** Added the plan-time blocker resolution loop so `/dev:build` never has to make build-time decisions. New per-task file `dev/plan-blockers.md` (`doc_type: plan-blockers`) captures decisions the user must make BEFORE build starts — missing integration contracts, undecided auth models, ambiguous schemas, unknown config, unclear business rule edge cases. `/dev:plan` Stage 3 detects them from 5 sources (`tl-plan.md` `[HELD]` markers, BA `open-questions.md` "Blocks build" rows, `integrations.md` unresolved entries, `system-landscape.md` gaps, `implementation.md § 3 Impacted components` `unknown` entries). User fills `Resolution:` per blocker → `/dev:plan --resume` deterministically folds resolutions into `implementation.md` and logs each as a `DEC-###`. New state `BLOCKED_ON_PLAN` (distinct from execution-time `BLOCKED`) — both map to MC `blocked`. New ID prefix `PB-###` (Plan Blocker, sequential per task). `/dev:build` Stage 0 refuses to run if `plan-blockers.md` `status:` is `OPEN` or `RESOLVING`. Additive: features whose plan is already fully-decidable never get a `plan-blockers.md` file.
>
> **2.1 (sub-task delivery layer — additive).** Added the sub-task tree under each feature: `features/<slug>/subtask/<repo>/` holds one sub-task per involved repo when `/dev:plan` decides to split a multi-repo feature. Each sub-task's tab files (`description.md`, `implementation.md`, `status.md`) map 1:1 to MC's 4-tab sub-task schema (`taskType: subtask`; the `acceptanceCriteria` and `testScenarios` tabs stay empty on MC — validation reads parent). Dev artifacts for each sub-task live under `subtask/<repo>/dev/`. New `doc_type`s: `subtask-description`, `subtask-implementation`, `subtask-status`, `plan-run`, `task-decision`. `/dev:plan` batch runs write summaries under `.jetrix/dev/batch-runs/plan-run-<ts>.md`. Reverse mapping (MC metadata → local layout) uses `metadata.subtaskNumber` + `metadata.subtaskRepo` on each sub-task so `/jetrix:pull scope` can reconstruct the tree cold. Additive — single-repo and bug/story features never get a `subtask/` folder and are unaffected.
>
> **2.0 (role-centric workspace layout).** Major rework of the workspace tree — the `<slug>/` folder wrapper inside `.jetrix/` is retired (a workspace binds one Solution; the slug lives in `project.json`). Every path drops two segments. Role folders drop the `-output` suffix (`ba/`, `tl/`, `qa/`, `doc/`); `shared-context/` keeps its name and simply moves up out of `<slug>/`. `context/features/` is promoted to `features/` at the top level (features are a deliverable, not code context). Workspace-level `context/frontend|backend|database|project/` folders are deleted — that graph lives per-repo at `<repo>/context/code-context/` (Model B, unchanged from 1.3). BA registers are grouped under `ba/registers/`; BA logs under `ba/logs/`; QA under `qa/{audits,health,escalations}/`; DOC under `doc/{decks,walkthroughs,workflows,boards}/`. `/jetrix:init §0.5` performs a soft, idempotent migration from v1 to v2 layouts on first run.
>
> **1.3 (in-repo code context).** Added the brownfield **code-context** layer: a committed `<repo>/context/code-context/` tree written by the TL's `tl-code-map` **inside the mapped repository** — a `context/` folder at the repo root with `code-context/` inside it (not in the workspace, and not inside `.jetrix/`, which is gitignored), holding one markdown unit per page, endpoint and database object, grouped by business domain — with database objects grouped on disk by **kind** (`tables/ collections/ views/ procedures/ functions/ triggers/`) — plus **semantic layer indexes** (a `## Domain Map` in prose alongside the unit table) that exist so a consumer can pick the right file without opening any other. New doc_types: `code-context-readme`, `code-context-index`, `code-map-registry`, `map-coverage`; the layer indexes keep the existing `page-index` / `endpoint-index` / `entity-index` doc_types so current consumers keep working by doc_type rather than filename. Workspace-level pointer file: `tl/code-map-registry.md` (v2.0 path; was `context/code-map-registry.md` in v1.3). IDs are unchanged. Additive: greenfield projects that never run `/tl:code-map` are unaffected.
>
> **1.2 (eval layer).** Added the applied-AI **eval** layer: the `EVAL-<AREA>-NN` id (§3) and the *applied-AI / LLM feature* classification (§5) that gates it. Eval units live per-feature under `features/<slug>/evals/` (v2.0 path; was `context/evals/<feature-slug>/` in v1.2). The TL's `tl-feature-planning` **designs** eval units for AI-bearing features, the dev `feature-delivery-loop` **runs and inspects** them, and QA's harness hosts them — see the core **`eval-engineering`** skill. Additive — deterministic features are unaffected.
>
> **1.1 (use-case model).** Made **use cases** first-class: added the `<MODULE>-UC-NN` id and `use-case-register.md`; the scope §3.x now carries a **§3.x.3 Master Flow** and a **§3.x.4 Use Cases** layer (renumbered through §3.x.11); added the **Mermaid diagram convention** (§8) where Mermaid is the living source and the Doc Agent's branded SVG swimlane is its projection. The change is **additive** — a `schema_version: 1.1` document remains readable; new documents are written at `1.1`.

---

## 1. Workspace layout (v2.0 — role-centric)

Every Delivery OS workspace is bound to **one** Jetrix Solution. Everything lives at the `.jetrix/` root — no `<slug>/` wrapper. The entire `.jetrix/` folder is gitignored; it is a local working copy of Jetrix state. Agents read and write **only** at these paths.

```text
<workspace>/
└── .jetrix/                              # gitignored (whole folder)
    ├── README.md                         # workspace map — seeded by /delivery-os:init
    ├── project.json                      # Jetrix binding (solutionId, apps, envs) — /jetrix:init writes this
    ├── connection-map.md                 # solution-level architecture doc (if the portal built one)
    │                                     # AUTHORITATIVE for cross-repo Wiring (transport per pair — REST/gRPC/queue),
    │                                     # auth boundary, and external integrations. Read by tl-read-code-context,
    │                                     # /dev:plan Stage 1, tl-feature-planning, tl-feature-compose before any
    │                                     # cross-repo integration is planned or described.
    ├── cache/
    │   ├── repolocation.json             # per-app local repo paths
    │   └── sync-state.json               # drift hashes for /jetrix:push and /jetrix:pull
    │
    ├── shared-context/                           # cross-role context — BA writes, everyone reads
    │   ├── project-profile.md
    │   ├── glossary.md
    │   ├── stakeholder-map.md
    │   ├── system-landscape.md
    │   ├── decision-log.md               # append-only DEC-### from every role
    │   └── baseline-profile.md           # optional QA baseline override
    │
    ├── ba/                               # STAGE 01 — Business Analyst
    │   ├── intake.index.md               # LIVING source registry — maintained by /ba:scope
    │   ├── scope.md                      # the living scope document (primary handoff)
    │   ├── client-questions.md
    │   ├── artifacts/                    # generated normalized summaries — categories created on demand
    │   │   └── <category>/<name>.summary.md
    │   ├── registers/                    # the eight canonical registers
    │   │   ├── requirements.md
    │   │   ├── workflows.md
    │   │   ├── use-cases.md
    │   │   ├── business-rules.md
    │   │   ├── examples.md
    │   │   ├── data.md
    │   │   ├── integrations.md
    │   │   └── assumptions.md
    │   ├── logs/                         # the four canonical logs
    │   │   ├── clarifications.md
    │   │   ├── contradictions.md
    │   │   ├── indexing-assistance-needed.md
    │   │   └── changes.md
    │   ├── intake-runs/
    │   │   └── run-###.md
    │   └── reviews/                      # /ba:review output triples (html + md + json)
    │       └── scope-review-<ts>.{html,md,json}
    │
    ├── features/                         # BA authors, TL enriches, Dev delivers
    │   ├── feature-index.md              # roll-up (pushed as scope-context doc)
    │   ├── tracker.md                    # cross-feature dev roll-up (state per feature)
    │   └── <feature-slug>/               # v2.2 layout — see §1.a.i for the design rationale
    │       ├── feature.md                # BA — Description tab source
    │       ├── workflow.md               # BA — folds into feature.md at push
    │       ├── acceptance-criteria.md    # BA — Acceptance tab
    │       ├── business-rules.md         # BA — Business Rules tab
    │       ├── nfrs.md                   # BA — NFRs tab
    │       ├── test-scenarios.md         # BA — Test Scenarios tab
    │       ├── dependencies.md           # BA — Dependencies tab
    │       ├── open-questions.md         # BA — folds into dependencies at push
    │       ├── implementation-plan.md    # BA scratchpad, local-only
    │       ├── evals/                    # TL — applied-AI features only (EVAL-<AREA>-NN)
    │       │   ├── eval-index.md
    │       │   └── <eval-slug>.md
    │       │
    │       │# ────────── PARENT-ALONE CASE — no sub-tasks (single-repo feature) ──────────
    │       ├── description.md            # TL — business narrative (→ MC Description tab)
    │       ├── implementation.md         # TL — SINGLE SOURCE OF TRUTH (→ MC Implementation tab)
    │       │                             # 10 sections: business flow (§1) + build sequence (§2) +
    │       │                             # impacted components (§3) + API endpoints (§4) +
    │       │                             # database (§5) + frontend UI (§6) + touch points (§7) +
    │       │                             # test strategy (§8) + risks + rollback (§9) +
    │       │                             # how to verify locally (§10 — dev-only; stripped on MC push)
    │       ├── status.md                 # dev — single state file (MC-mirrored + local loop state)
    │       │                             # includes mc_status + current_state + branch + owner_lock +
    │       │                             # ready_for_dev_build + ready_for_dev_commit + blocker_ids +
    │       │                             # mc_status_pushed + acceptance status table + run history
    │       ├── dev/                      # Dev — LOCAL AUDIT for this feature (never pushed to MC)
    │       │   ├── plan-run.md           # /dev:plan stage journal — for --resume
    │       │   ├── plan-blockers.md      # PB-### user-decision file — only when blockers OPEN
    │       │   ├── traceability.md       # AC ↔ BR ↔ EP ↔ implementation-step ↔ test ↔ PB ↔ DEC map
    │       │   ├── acceptance-map.md     # parent AC → verification result (built by /dev:build)
    │       │   ├── build-run.md          # /dev:build stage journal
    │       │   ├── commit-run.md         # /dev:commit stage journal
    │       │   ├── implementation-log.md # step-by-step build attempt log
    │       │   ├── security-findings-build.md   # /dev:build Stage 9 output
    │       │   ├── security-findings-commit.md  # /dev:commit Stage 3 output
    │       │   ├── code-review-findings.md      # /dev:commit Stage 4 output
    │       │   ├── context-merge-log.md         # /dev:commit Stage 7 output
    │       │   ├── merge-conflicts.md    # only during Stage 7 halt — user resolves + --resume
    │       │   └── escalation-<n>.md     # only when BLOCKED
    │       │
    │       │# ────────── SPLIT CASE — sub-tasks (multi-repo feature) ──────────
    │       │# When split, the parent has NO parent-alone description.md/implementation.md/status.md.
    │       │# Sub-tasks carry those. Parent state is DERIVED from sub-tasks (all DONE → parent DONE).
    │       │# feature.md frontmatter carries the split decision (rule + repos).
    │       ├── dev/                      # ONE FLAT dev/ folder (as above) — sub-task audit files
    │       │   │                         # use repo-slug PREFIX in filename. NO nested subtask/ folder.
    │       │   ├── plan-run.md
    │       │   ├── task-decision.md      # WHY split; which repos; rule that applied
    │       │   ├── <repo>-plan-blockers.md            # e.g. backend-plan-blockers.md, frontend-plan-blockers.md
    │       │   ├── <repo>-traceability.md
    │       │   ├── <repo>-acceptance-map.md
    │       │   ├── <repo>-build-run.md
    │       │   ├── <repo>-commit-run.md
    │       │   ├── <repo>-implementation-log.md
    │       │   ├── <repo>-security-findings-build.md
    │       │   ├── <repo>-security-findings-commit.md
    │       │   ├── <repo>-code-review-findings.md
    │       │   ├── <repo>-context-merge-log.md
    │       │   ├── <repo>-merge-conflicts.md   # conditional
    │       │   └── <repo>-escalation-<n>.md    # conditional
    │       │
    │       └── subtask/                  # ONLY exists when /dev:plan split the feature
    │           │                         # (multi-repo feature → one folder per repo, named by repo slug)
    │           └── <repo-slug>/          # e.g. backend/, frontend/, mobile/
    │               │                     # matches key in .jetrix/cache/repolocation.json
    │               ├── description.md    # sub-task Description tab (business flow narrative)
    │               ├── implementation.md # sub-task Implementation tab (10-section source of truth)
    │               └── status.md         # sub-task status (MC-mirrored + local loop state)
    │                                     # NO nested dev/ folder here either — audit lives flat at
    │                                     # features/<slug>/dev/<repo>-<filename>.md
    │
    ├── tl/                               # STAGE 02 — Tech Lead outputs (cross-feature)
    │   ├── code-map-registry.md          # pointer to each mapped repo's <repo>/context/code-context/ tree
    │   ├── reviews/                      # /tl:review output triples
    │   │   └── spec-review-<ts>.{html,md,json}
    │   └── maturity/                     # /tl:maturity check-in triples
    │       └── maturity-<ts>.{html,md,json}
    │
    ├── qa/                               # STAGE 03 — Quality Assurance
    │   ├── quality-gates.md              # the harness contract every dev iteration reads
    │   ├── test-setup-plan.md
    │   ├── setup-log.md
    │   ├── testing-conventions.md
    │   ├── decisions.md
    │   ├── audits/                       # /qa:audit output rounds
    │   │   └── test-audit-<ts>.{html,md,json}
    │   ├── health/                       # /qa:health check-in reports
    │   │   └── health-<ts>.md
    │   └── escalations/
    │       └── escalation-<n>.md
    │
    ├── doc/                              # STAGE 05 — Documentation deliverables, grouped by artifact kind
    │   ├── decks/                        # /doc:deck, /doc:proposal — pptx
    │   │   └── deck-<name>-<ts>.pptx
    │   ├── walkthroughs/                 # /doc:walkthrough — html
    │   │   └── walkthrough-<topic>-<ts>.html
    │   ├── workflows/                    # /doc:workflow — html
    │   │   └── workflow-<topic>-<ts>.html
    │   └── boards/                       # /doc:magic-board — html
    │       └── board-<topic>-<ts>.html
    │
    ├── tasks/                            # non-feature MC tasks (ad-hoc)
    │   └── <slug>.md
    │
    └── dev/                              # cross-feature dev artifacts
        └── batch-runs/                   # /dev:plan batch run summaries (multi-target)
            └── plan-run-<ts>.md          # per-invocation record: targets, decisions, outcomes
```

### 1.b The per-repo code-context tree (Model B — TL owns the graph, but it lives with the code)

The **as-built code graph** (pages, endpoints, entities) does NOT live under `.jetrix/`. Each linked app repo carries its own `<repo>/context/code-context/` tree, committed with the code. Written by `/tl:code-map` (brownfield reverse-map) and extended by `/tl:plan` (forward planning of new units), read by `/dev:plan` (Stage 2 compose), `/dev:build` (Stage 10 `designed → implemented` flip), `/dev:commit` (Stage 7 semantic-context-merge via `tl-semantic-context-merge`), and doc/qa consumers. Structure:

```text
<repo>/context/code-context/
├── README.md
├── code-context-index.md
├── map-coverage.md
├── backend/
│   ├── backend-index.md                  # endpoint-index doc_type
│   ├── _overview.md
│   └── domains/<domain>/endpoints/<slug>.md      # EP-<AREA>-NN
├── frontend/
│   ├── frontend-index.md                 # page-index doc_type
│   ├── _overview.md
│   └── pages/<area>/<slug>.md            # PAGE-<AREA>-NN
└── database/
    ├── database-index.md                 # entity-index doc_type
    ├── _overview.md
    └── {tables,collections,views,procedures,functions,triggers}/<slug>.md    # ENT-<AREA>-NN
```

The workspace `.jetrix/tl/code-map-registry.md` is the one workspace-level TL file — it lists each mapped repo, its context root, its indexes and its area tokens, so `/tl:plan` can find as-built units to reuse and cross-repo links resolve. Unit IDs and match keys are identical to forward-planned ones; reverse-mapped units add `origin: reverse-mapped`, `mapped_from`, `mapped_from_commit`, and `map_confidence`. Nothing sensitive is written into this tree — it is committed and shared.

### 1.c Jetrix binding — `.jetrix/` (owned by the **jetrix** plugin)

Jetrix is the **single source of truth** for all project context (glossary, scope, registers, feature breakdown). The local `.jetrix/` folder is a disposable **working copy** — the ENTIRE folder is gitignored, including `project.json`, the cache, and every role subfolder. Binding a workspace and syncing it are owned by the separate **`jetrix`** plugin — read its **`jetrix-sync`** skill for the full contract: `.jetrix/project.json` (regenerable identity + app/environment→branch wiring — no secrets), the cache, and the pull/push model. Commands: `/jetrix:init` (bind + run the v1→v2 migration on old workspaces), `/jetrix:pull` (refresh the cache from Jetrix, incremental), `/jetrix:push` (publish local work back as structured records — upsert by stable id, transactional, pull-before-push). The canonical form in Jetrix is **structured records** (the IDs in §3); `scope.md` and the branded `.docx` are projections rendered from them.

### Source handling — reference, never copy or move
Original source files (local folders/files, Google Drive, etc.) **stay where they are**. The workspace never copies, moves, or deletes a user's originals. Intake only:
1. **records** each source in `intake.index.md` (its real location + classification + status), and
2. **generates** a normalized markdown summary under `artifacts/<category>/` for eligible sources.
So the workspace holds only the **index + generated summaries** — it is a knowledge layer *over* the user's files, not a copy of them.

### `ba/intake.index.md` is the single source registry
It is **agent-maintained** (the user can still hand-edit it) and folds together what were previously separate artifact-map / artifact-ledger / source-classification files: each source's description, original location, detected category, usage mode (the classification + reason), summary path, content hash, and status all live in one registry. Add sources conversationally via `/ba:scope add "..."` — the agent classifies, summarizes, and registers them.

**Handoff rule:** an agent reads another agent's **published** files (`ba/`, `shared-context/`, `features/`); it never reaches into another agent's working notes. `shared-context/` and `ba/scope.md` are the primary handoff surfaces.

---

## 2. Document frontmatter standard

**Every generated Markdown document** starts with YAML frontmatter so any consumer can validate compatibility before reading the body:

```yaml
---
doc_type: scope            # scope | requirement-register | use-case-register | glossary | run-summary | source-summary | intake-index | description | implementation | status | plan-run | task-decision | plan-blockers | traceability | acceptance-map | build-run | commit-run | implementation-log | security-findings | code-review-findings | context-merge-log | merge-conflicts | escalation | ...
schema_version: 1.3        # the contract version this file conforms to
produced_by: ba            # ba | doc | tl | qa | delivery-os
last_intake_run: run-003   # the run that last touched this file (omit if N/A)
status: Emerging           # see §5 maturity values
initiative: payments-v2    # OPTIONAL — the initiative/work-batch this file belongs to (feature files only; see §3)
generated_at: 2026-06-18   # ISO date of last write
---
```

A **normalized source summary** (`artifacts/<category>/<name>.summary.md`) carries extra provenance so a fact extracted from it traces all the way back to the untouched original:

```yaml
---
doc_type: source-summary
schema_version: 1.1
produced_by: ba
source_id: SRC-002              # matches the intake.index registry row
summary_of: "D:/acme/meetings/2026-06-12-kickoff.docx"   # the ORIGINAL location (path or Drive link), referenced not copied
source_hash: "sha256:…"         # so re-runs detect change
usage_mode: Deep Analysis
status: Processed
generated_at: 2026-06-18
---
```

A consuming agent that finds `schema_version` newer than it understands must **stop and warn** rather than guess — with one standing exception, because the contract has so far only ever grown: where a minor bump is declared **additive** in the version note above (1.1, 1.2 and 1.3 all are), a consumer written for an earlier minor may read the document, use the fields it knows, and ignore the rest. It must still warn if a *major* version is newer, or if a minor bump is not marked additive. Concretely: a `/tl:plan` written against 1.1 may read, reuse and extend a 1.3 `code-context/` unit — the sections it knows are present under their original headings — and should not refuse it.

### Sub-task frontmatter (written by `/dev:plan` when a feature is split)

Every file inside `features/<slug>/subtask/<repo>/` carries this frontmatter. The three tab files (`description.md`, `implementation.md`, `status.md`) share the identity fields; `doc_type` distinguishes each file. **Folder name = repo slug** (matches key in `.jetrix/cache/repolocation.json`); **execution sequence lives in frontmatter** (`subtask_number`), not the folder name.

```yaml
---
doc_type:                 description   # description | implementation | status   (v2.3 — subtask-* prefixes retired; distinguished by folder location)
schema_version:           1.0
produced_by:              dev
feature_id:               FEAT-SUP-001          # parent feature (matches parent feature.md)
parent_task_object_id:    6a61…                 # parent Task's Mongo _id in MC
parent_task_number:       Feature-4             # parent's MC display number
subtask_number:           1                     # 1..N execution sequence within parent
subtask_repo:             backend               # matches folder name + repolocation.json key
jetrix_subtask_object_id: 6b72…                 # this sub-task's Mongo _id (set after /jetrix:push)
jetrix_subtask_number:    Subtask-7             # MC display number (set after push)
composed_at:              2026-08-29T14:24:11Z
inputs_hash:              sha256:…              # hash of the compose inputs; used by idempotency check
---
```

`status.md` adds `current_state`, `owner_lock`, and `branch` for the loop-state model (§5) — same fields the parent's `status.md` uses.

**MC-side reverse mapping** — the plugin sends this shape to `task-mcp.subtask_upsert_bundle`:

```json
{
  "metadata": {
    "externalId":       "FEAT-SUP-001-1",
    "parentExternalId": "FEAT-SUP-001",
    "subtaskNumber":    1,
    "subtaskRepo":      "backend",
    "source":           "ai",
    "aiGenerated":      true
  }
}
```

task-mcp **translates** this to MC's whitelisted metadata schema on the write path (MC only accepts `externalId` / `externalSlug` / `externalInitiative` / `externalUrl` / `source` / `aiGenerated` / `aiGeneratedAt`), then **reverses** the mapping in `subtask_list` so consumers read the same shape. Concretely:

| Plugin field | Write path | Read path (`subtask_list`) |
|---|---|---|
| `externalId` | → `metadata.externalId` (whitelisted) | ← `metadata.externalId` |
| `subtaskRepo` | → `metadata.externalSlug` (whitelisted) | ← derived from `metadata.externalSlug` |
| `subtaskNumber` | dropped (not stored) | ← derived from sort position (`taskNumber` ascending, index+1) |
| `parentExternalId` | dropped (parent link is URL path `:taskId`) | ← derived from parent's `metadata.externalId` (single MC lookup per listing) |

This metadata is what `/jetrix:pull scope` reads to reconstruct the local `subtask/<repo>/` tree from MC on a cold clone — task-mcp's read-side derivation preserves the round-trip.

---

## 3. Stable ID conventions

IDs are the threads that let one agent cite what another produced. They are **append-only** — never renumber, never reuse a retired ID.

| Entity            | Prefix | Example  | Lives in                     |
|-------------------|--------|----------|------------------------------|
| Requirement       | `<MODULE>-<FR\|AI\|DET\|HUM>` | INTK-AI-02 | ba/registers/requirements.md / scope §3 |
| Use case          | `<MODULE>-UC` | INVP-UC-01 | ba/registers/use-cases.md / scope §3.x.4 |
| Workflow          | `WF`   | WF-001   | ba/registers/workflows.md    |
| Business rule     | `BR`   | BR-001   | ba/registers/business-rules.md |
| Data entity       | `DATA` | DATA-001 | ba/registers/data.md         |
| Integration       | `INT`  | INT-001  | ba/registers/integrations.md |
| Example/scenario  | `EX`   | EX-001   | ba/registers/examples.md     |
| Assumption        | `ASM`  | ASM-001  | ba/registers/assumptions.md  |
| Clarification     | `CLR`  | CLR-001  | ba/logs/clarifications.md    |
| Contradiction     | `CON`  | CON-001  | ba/logs/contradictions.md    |
| Decision          | `DEC`  | DEC-001  | shared-context/decision-log.md       |
| Artifact source   | `SRC`  | SRC-001  | ba/intake.index.md (registry) |
| Feature           | `FEAT-<AREA>` | FEAT-SUP-001 | features/ (ba)         |
| Page              | `PAGE-<AREA>` | PAGE-SUP-01 | <repo>/context/code-context/frontend/ (tl) |
| Endpoint          | `EP-<AREA>`   | EP-SUP-02   | <repo>/context/code-context/backend/ (tl) |
| Entity            | `ENT-<AREA>`  | ENT-SUP-01  | <repo>/context/code-context/database/ (tl) — realises a `DATA-###` |
| Eval              | `EVAL-<AREA>` | EVAL-SUP-01 | features/<slug>/evals/ (tl) — verifies an AC, exercises EP-/ENT- (applied-AI features) |
| QA finding        | `QAF`  | QAF-001  | qa/audits/test-audit-*.md (qa)    |
| Quality gate      | `QG`   | QG-001   | qa/quality-gates.md (qa)           |
| Initiative        | *(human slug)* | payments-v2 | feature frontmatter + features/feature-index.md (ba) |
| Plan blocker      | `PB` (or `PB-<N>` for sub-task N) | PB-001 · PB-1-002 | dev/plan-blockers.md (dev) — v2.2 |

### Initiative — grouping features by work batch (multi-developer)

An **initiative** groups the features produced by one scoping effort so a developer can focus on just their batch even when many developers' in-flight features share `features/`. It is a **human-named, lowercase-kebab slug** (`payments-v2`, `supplier-portal`), not a numbered ID — chosen by the developer when they run `/ba:features initiative=<name>` (auto-generated as `intake-<YYYY-MM-DD>` if omitted). It is stamped into every feature the run creates/updates (`initiative:` in `feature.md`/`status.md` frontmatter and an `Initiative` column in `feature-index.md`), and it is the filter `/tl:plan initiative=<name>` and `/dev:build initiative=<name>` use to act on only that group. On a re-run, an existing feature **keeps** its initiative unless a new one is passed explicitly — so grouping is stable across merges. A feature with no initiative is treated as ungrouped (`unassigned`).

The `context/` graph IDs (`FEAT-`/`PAGE-`/`EP-`/`ENT-`) carry a short uppercase **area** token and a sequence within that area/layer (`PAGE-SUP-01`, `EP-SUP-02`). A database entity **cites the BA `DATA-###`** it realises rather than inventing a parallel data ID; likewise endpoints cite `INT-###` for integrations. Never mint a `context/` ID that shadows a BA register ID.

IDs are zero-padded to 3 digits (functional-requirement `NN` is 2 digits within its module, per the scope template). Cross-references are written inline as the bare ID (e.g. "validated by EX-014" or "see WF-002").

**Requirement IDs** follow the Techjays Scope Document convention: `<MODULE>-<FR|AI|DET|HUM>-<NN>` where the module prefix is a short uppercase abbreviation (Intake → `INTK`, Validation → `VALD`), the middle token is `FR` or the responsibility code, and `NN` is sequential within that module. The same ID is used in `ba/registers/requirements.md` and in `scope.md` §3.x.5 so they trace 1:1.

**Use-case IDs** follow the same module-prefix convention: `<MODULE>-UC-<NN>` (e.g. `INVP-UC-01`), `NN` sequential within the module. A use case is a **distinct scenario or route** through a module — one that differs from its siblings in a *material* way (different steps, actors, business rules, systems, or outcome), not merely in a data value. The canonical use case lives in `scope.md` §3.x.4 (nested under its module) and in `ba/registers/use-cases.md`; the two trace 1:1. Functional requirements, workflows, examples, and business rules cite the use case(s) they serve by ID, and a use case cites the requirements/workflows/examples/rules that realise it — so a route is traceable in both directions. See `ba-extraction` for the rule that decides when a branch becomes its own use case versus an alternative flow.

---

## 4. Source traceability

Every extracted fact must trace back to where it came from. Use this citation form everywhere:

```text
[SRC-002 › meeting-transcripts/2026-06-10-kickoff.md]
```

A requirement, rule, or workflow with no source citation is **not allowed** — if its origin is unknown, raise a clarification (CLR) instead.

---

## 5. Shared vocabulary (controlled values)

All agents use these exact values — no synonyms.

**Artifact status** (per source/file):
`New` · `Processed` · `Changed` · `Unchanged` · `Missing` · `Inaccessible` · `Superseded` · `Archived` · `Access Required` · `Needs User Guidance`

**Confidence** (per extracted fact):
`Confirmed` · `Likely` · `Assumed` · `Conflicting` · `Needs Clarification`

**Usage mode** (per source, how deeply to process it):
`Deep Analysis` · `Reference Only` · `Sample and Summarize` · `Index Only` · `Future Agent Input` · `Needs User Guidance`

**Scope maturity** (document-level status, in frontmatter):
`Draft` · `Emerging` · `Reviewed` · `Frozen` — surfaced on the scope cover block as `Draft` / `In Review` / `Approved`.

**Responsibility** (`Resp.` on every functional requirement, per the Techjays Scope Document):
`AI` (AI capability) · `DET` (deterministic logic) · `HUM` (human action)

**Priority** (`Pri.`, MoSCoW):
`M` (Must) · `S` (Should) · `C` (Could) · `W` (Won't-this-phase)

**Dev delivery state** (per task — parent Task or sub-task; local `status.md` + mirrored on MC's status field):
`PLANNED` · `IN_PROGRESS` · `REVIEW` · `DONE` · `BLOCKED` · `BLOCKED_ON_PLAN` (v2.2)
Written by `/dev:plan` at `PLANNED` (or `BLOCKED_ON_PLAN` when plan-blockers exist); advanced by `/dev:build` (→ `IN_PROGRESS`) and `/dev:commit` (→ `REVIEW`); flipped to `DONE` by human on merge; any stage can escalate to `BLOCKED` (execution-time blocker). `BLOCKED_ON_PLAN` is distinct — set only by `/dev:plan` when the plan itself has undecided decisions the user must resolve in `dev/plan-blockers.md` before `/dev:build` can run. Both `BLOCKED` and `BLOCKED_ON_PLAN` map to MC `blocked`. For a split feature the parent's state is **derived** from its sub-tasks (all `DONE` → parent `DONE`; any `BLOCKED` or `BLOCKED_ON_PLAN` → parent `BLOCKED`; any `IN_PROGRESS` → parent `IN_PROGRESS`; else `PLANNED`) — parent state is never written directly.

**Applied-AI / LLM feature** (does a feature need eval-engineering?):
A feature is **AI-bearing** when its behaviour depends on a model's output — generation, classification/extraction, ranking or semantic search, RAG, or agentic tool use — or it declares `ai_component: true` / cites an `INT-###` to an LLM/AI provider. AI-bearing features get an **eval layer** (`context/evals/`, `EVAL-<AREA>-NN`, see the `eval-engineering` skill); every other feature is **deterministic** and is proven by the dev acceptance-map alone. When it's genuinely unclear, record an **open question** rather than assuming — don't skip evals on a feature that turns out to be AI-bearing, or invent them for one that isn't.

---

## 6. Producer / consumer map

| Surface                              | Produced by | Consumed by        |
|--------------------------------------|-------------|--------------------|
| `ba/intake.index.md` (source registry) | ba (human-editable) | ba         |
| `ba/artifacts/**/*.summary.md`       | ba          | ba (extraction)    |
| `shared-context/*`                           | ba          | doc, tl, qa        |
| `ba/scope.md`                        | ba          | doc, tl, qa        |
| `ba/registers/requirements.md`       | ba          | doc, tl, qa        |
| `ba/registers/use-cases.md`          | ba          | doc, tl, qa        |
| `ba/registers/integrations.md`       | ba          | tl                 |
| `ba/registers/data.md`               | ba          | tl                 |
| `features/*` (BA files)              | ba          | tl, doc, qa        |
| `features/<slug>/tl-plan.md`         | tl (feature-compose) | dev, doc, qa · pushed verbatim to `MC.Task.implementationDetails` by `/jetrix:push implementation` |
| `<repo>/context/code-context/*` (committed with the code — Model B) | tl (code-map reverse, feature-planning forward) | tl (spec-review, feature-compose), dev, doc, qa, coding agents |
| `tl/code-map-registry.md`            | tl (code-map) | tl (feature-planning), dev |
| `features/<slug>/evals/*` (applied-AI) | tl (feature-planning designs) | dev (feature-delivery-loop runs + inspects), qa (harness hosts) |
| `features/tracker.md`                | dev         | dev, tl (roll-up)  |
| `doc/**/*`                           | doc         | human, final       |
| `tl/reviews/*` `tl/maturity/*`       | tl          | human, delivery    |
| `qa/quality-gates.md`                | qa          | dev (`/dev:plan` harness gate; `/dev:build` Stages 4/7/8; `/dev:commit` Stage 5) |
| `qa/audits/*` `qa/test-setup-plan.md` | qa         | human, qa          |

When a downstream agent (doc/tl/qa) runs, it should prefer `ba/scope.md` as its primary input and **not re-run BA analysis** unless explicitly asked.

---

## 7. Canonical deliverable formats (Techjays D&D pack)

Client-facing deliverables conform to the Techjays **Design & Discovery** templates. These are the authority for structure and style; the markdown an agent maintains is the living source that the Doc Agent renders into the branded `.docx` at freeze time. The **Scope Document** template is bundled with this core plugin at `${CLAUDE_PLUGIN_ROOT}/templates/d&d/scope-document/` (versioned via its `manifest.json` + `CHANGELOG.md`); the rest still live in the repo `docs/D&D Documentation/` and will be bundled as their agents are built.

| Deliverable | D&D template | Maintained as | Owner |
|-------------|--------------|---------------|-------|
| Scope Document | **bundled** → `templates/d&d/scope-document/scope-document-template.docx` | `ba/scope.md` (module-centric) | ba |
| RAID Register | `docs/…/04 - RAID Register Template.docx` | ba/registers/assumptions + ba/logs/clarifications + ba/logs/contradictions (feeds A/D/R/Q rows) | ba |
| Executive Summary | `docs/…/01 - Executive Summary Template.docx` | `doc/decks/` | doc (Phase 2) |
| Technical Architecture | `docs/…/03 - Technical Architecture Template.docx` | `tl/reviews/` or handoff to doc | tl (Phase 3) |
| Implementation Plan | `docs/…/05 - Implementation Plan Template.docx` | `doc/decks/` | doc (Phase 2) |

**RAID alignment** — the BA registers map onto the RAID Register's four registers:
`ba/registers/assumptions.md` → Assumptions `A-##` · dependencies → Dependencies `D-##` · `ba/logs/contradictions.md` / risk notes → Risks `R-##` · `ba/logs/clarifications.md` → Open Questions `Q-##` (classified: *Must close before estimate · Proceed with assumption · Minor implementation detail · Too uncertain (exclude/T&M) · Future phase*). Scope §7 only references RAID — it never duplicates these.

---

## 8. Diagram convention (Mermaid is the living source; branded SVG is the projection)

Flows are authored as **Mermaid** fenced code blocks directly in the markdown the BA maintains — a module master flow in `scope.md` §3.x.3, and a per-use-case flow in each §3.x.4 use case (and, downstream, in each feature's `workflow.md`). Mermaid is chosen because it is diffable, reviewable in a pull request, and renders in most markdown viewers, so the diagram evolves with the words around it instead of drifting out of date in a separate file. The **Doc Agent** renders these same flows into the branded **SVG swimlanes** of the Techjays deliverables at doc/freeze time (`doc-workflow`) — so Mermaid is the *source*, SVG is the *client-facing projection* of the same journey, never a second hand-authored diagram to keep in sync.

Authoring rules so the diagrams stay uniform and machine-mappable:

- Use `flowchart TD` (top-down) for a use-case route and `flowchart TD` or `LR` for a module master flow — pick one orientation per module and keep it.
- **Decision/branch points are diamond nodes** (`{...}`), and **every branch edge is labelled with the condition** that selects it (`-->|credit memo| ...`). In a module master flow, each terminal branch names the use case it leads to by ID and name, so the master flow and the nested use cases line up 1:1.
- Terminal/outcome nodes use rounded ends (`([...])`); systems of record or integrations referenced in a step name the `INT-###` they map to in the node text where it helps.
- Keep the master flow to the decision skeleton (trigger → branch points → which use case) and push step-level detail into each use case's own flow — the master answers *which route*, the use-case flow answers *how that route runs*.
- Fence every diagram as ` ```mermaid ` … ` ``` ` and keep the label text short; long prose belongs in the surrounding narrative, not inside a node.
