---
name: tl-feature-compose
description: Compose self-contained implementation content for a feature or sub-task in one of three modes — detailed (full 5-section technical spec for a parent Task's Implementation tab, or for a single sub-task's Implementation tab scoped to one repo), narrative (business flow narrative for a sub-task's Description tab), or rollup (parent Implementation tab when the feature was split into sub-tasks — names each sub-task, sequence, cross-task dependencies, and touch points). Use whenever a feature has been planned technically (units exist in `context/frontend|backend|database/`) and needs a document a developer or coding agent can build from without opening the other files. Point it at one feature folder, a `FEAT-<AREA>-NN` id, an `initiative=<name>` slice, or the whole `features/` set; it reads the feature, its owned pages/endpoints/entities, and (when the repo is cloned locally) the target repo's file layout, and writes the appropriate document per mode. It never restates business rationale (that's in `feature.md`), never invents an endpoint/contract/schema/path the source can't ground, never leaks framework names or file paths, and never composes above Mission Control's 60 KB tab cap.
---

# TL Feature Compose (context graph + feature breakdown → buildable per-feature plan)

You are turning the **linked technical context graph** the TL feature-planning skill produces into a **self-contained per-feature implementation plan** — one document a developer or coding agent can hand straight to Claude and say "build this," without opening the feature folder, the workflow, the acceptance criteria, or any unit file. The graph is a memory for reuse across features; `tl-plan.md` is the buildable output for one feature.

The defining behaviour of this skill is **composition, not authoring**. You do not design new pages, new endpoints, new entities, or new integrations — that is the `tl-feature-planning` skill's job, and if you find genuinely undecided design points you record them as open questions in §9 rather than inventing them. What you *do* is arrange the design that already exists into a document a developer can read top-to-bottom and build from, inlining what needs to be inlined (endpoint contracts, entity columns, page shape) and citing IDs where a follow-through is enough (a reused endpoint the feature does not modify, a `DEC-###` decision the developer does not need to re-derive).

This skill **authors context, not code**. It produces the per-feature buildable spec that precedes implementation; it does not write production code, and it is distinct from `tl-feature-planning` (which authors the graph) and `tl-spec-review` (which scores a finished spec). Compose runs *after* planning; a feature with no owned units in the three indexes cannot be composed.

## Operating contract

Read the **`delivery-os-conventions`** contract first if it isn't already in context — the workspace layout, frontmatter standard, stable-ID rules, source-citation form, and controlled vocabulary. Your inputs are:

- **`.jetrix/connection-map.md` FIRST** (if present) — the workspace-level solution architecture doc. It names each repo's role, Wiring edges (transport per pair — `Frontend → Backend over REST`), auth boundary, and external integrations. Consult it BEFORE describing any cross-repo integration in your compose output — a sub-task's Implementation tab that says "the frontend consumes this endpoint" must trace through an EXISTING wiring edge; if it needs a NEW edge, that's a `[HELD]` open item, not an assumption.
- The feature folder — `features/<slug>/feature.md`, `implementation-plan.md` (BA's build-areas, optional context), `workflow.md`, `acceptance-criteria.md`, `dependencies.md`, `open-questions.md`.
- The feature's **owned unit files** — pages under `<repo>/context/code-context/frontend/pages/`, endpoints under `<repo>/context/code-context/backend/domains/`, entities under `<repo>/context/code-context/database/entities/` — resolved via the three layer indexes and the feature-cell matching rule (`Used by Features` cell can hold multiple ids, comma-separated; match on word boundary).
- The BA registers the units cite (`ba/registers/data.md`, `ba/registers/integrations.md`, `ba/registers/workflows.md`, `ba/registers/business-rules.md`) and `shared-context/decision-log.md`.
- The target app repos declared in `.jetrix/cache/repolocation.json` — read the file, and for each repo that exists locally, do a shallow layout scan (top-level + one level down) to establish routing/handler/model conventions. Never read env files, secrets, credentials, or files that look like credentials — treat any file matching `.env*`, `*.pem`, `*.key`, `*credentials*`, `*secret*` as off-limits.

**Output** (v2.3 layout — flat 3 files at task root, no nested dev/). Depends on the mode (see §"Compose modes" below):

- **`implementation` mode** on a parent-alone feature → `features/<slug>/implementation.md` (v2.3; was `tl-plan.md` before)
- **`implementation` mode** on a sub-task → `features/<slug>/subtask/<repo>/implementation.md`
- **`description` mode** on a sub-task → `features/<slug>/subtask/<repo>/description.md`
- **`rollup` mode** on a parent whose feature was split → `features/<slug>/tl-plan.md` (kept — the parent rollup remains `tl-plan.md` on split; the sub-task Implementation tabs carry the detail)

The body structure depends on the mode — see `references/implementation-plan-template.md`. Read the template before composing.

**Frontmatter** on parent-alone `implementation.md` OR sub-task `implementation.md`:

```yaml
---
doc_type: implementation              # v2.3 — was `tl-plan` (parent-alone) or `subtask-implementation` (sub-task)
schema_version: 2.0
produced_by: tl
feature_id: FEAT-<AREA>-NN
parent_task_object_id: <MC _id>       # sub-task only — OMIT for parent-alone
parent_task_number: Feature-N         # sub-task only — OMIT for parent-alone
subtask_number: 1..N                  # sub-task only — OMIT for parent-alone
subtask_repo: <repo-slug>             # sub-task only — OMIT for parent-alone
jetrix_subtask_object_id: <MC _id>    # sub-task only — set after /jetrix:push subtask
jetrix_subtask_number: Subtask-N      # sub-task only — set after push
compose_mode: implementation
composed_at: <ISO date>
inputs_hash: <sha256 of feature.md + owned unit files, for re-run skip>
---
```

**Frontmatter** on sub-task `description.md`:

```yaml
---
doc_type: description                 # v2.3 — was `subtask-description`
schema_version: 2.0
produced_by: dev                      # invoked by /dev:plan Stage 2 (compose_mode: description)
feature_id: FEAT-<AREA>-NN
parent_task_object_id: <MC _id>
parent_task_number: Feature-N
subtask_number: 1..N
subtask_repo: <repo-slug>
jetrix_subtask_object_id: <MC _id>    # set after /jetrix:push subtask
jetrix_subtask_number: Subtask-N      # set after push
compose_mode: description
composed_at: <ISO date>
inputs_hash: <sha256 of the compose inputs>
---
```

**Frontmatter** on split-parent rollup `tl-plan.md` (unchanged):

```yaml
---
doc_type: tl-plan
schema_version: 1.2
produced_by: tl
feature_id: FEAT-<AREA>-NN
compose_mode: rollup
composed_at: <ISO date>
inputs_hash: <sha256 of feature.md + owned unit files, for re-run skip>
---
```

## Compose modes

Three distinct modes drive what body content this skill produces. The caller (`/dev:plan` Stage 2, or `/tl:plan`'s downstream) specifies the mode; the workflow branches on it in step 5.

### Mode: `implementation` (default — parent-alone or per-sub-task Implementation tab)

The **single source of truth** for the task. Used for:
- A **parent Task's Implementation tab** when the feature was NOT split (`--no-split` or single-repo feature)
- A **sub-task's Implementation tab** — scoped to that one sub-task's repo (its owned units only)

Body sections (v2.3 — target 10 sections; `tl-feature-compose` writes §§1, 4–7, 8-title; sections §§2, 3, 8-body, 9 are appended by `/dev:plan` Stage 3; §10 is appended by `/dev:build` Stage 11):

1. **Business flow** — 2-3 sentence overview, business terms
2. **Build sequence** — `/dev:plan` writes: ordered steps table (# / Step / Units / Satisfies / Notes) + mermaid step-graph
3. **Impacted components** — `/dev:plan` writes: 12-dimension impact matrix (Frontend/Backend/DB/Authz/Integrations/Jobs/Notifications/Monitoring/Tests/Docs/Flags/Analytics)
4. **API endpoints** — request/response tables, execution order, refusals (this skill writes)
5. **Database changes** — new + modified tables/collections, indexes (this skill writes)
6. **Frontend UI** — surfaces + API wiring (this skill writes; omitted for backend-only sub-tasks)
7. **Touch points** — Reuse / New table (this skill writes)
8. **Test strategy** — `/dev:plan` writes: unit / integration / e2e / concurrency coverage per step
9. **Risks + rollback** — `/dev:plan` writes: assumptions carried, schema-trap notes, rollback plan
10. **How to verify locally** — `/dev:build` Stage 11 writes: developer runbook (env setup, DB migrations, curl examples, expected outputs)

At compose time (Stage 2), `tl-feature-compose` emits §§1, 4-7 populated. Sections §§2, 3, 8, 9 are stubbed with `_(populated by /dev:plan Stage 3)_`. Section §10 is stubbed with `_(populated by /dev:build Stage 11)_`.

Output path:
- Parent-alone → `features/<slug>/implementation.md`
- Per sub-task → `features/<slug>/subtask/<repo>/implementation.md`

### Mode: `description` (sub-task Description tab)

A **professional business-flow narrative**, one to two paragraphs, telling the story of what THIS sub-task does in business terms — the kind of description a stakeholder or QA lead reads without any code context. No file paths, no framework names, no HTTP codes, no fields. Uses business terminology from the feature's `workflow.md` and the parent's `feature.md`, scoped to the operations this sub-task's repo owns.

Body: continuous prose in one or two paragraphs. **No bullet lists, no tables, no headings, no code fences.** See `references/implementation-plan-template.md` §narrative for the template with an example.

Output path: `features/<slug>/subtask/<repo>/description.md`

### Mode: `rollup` (parent Implementation tab when the feature was split)

A **short document** listing each sub-task by repo + sequence, cross-task dependencies, and touch points at the parent level. Used only when the feature was split — replaces the detailed 5-section spec on the parent's Implementation tab since detail now lives on each sub-task.

Body sections (see `references/implementation-plan-template.md` §rollup):

1. **Build sequence** — one paragraph naming each sub-task by role (backend, frontend, mobile) + dependency order, plus one mermaid step-graph showing the sub-task sequence.
2. **Sub-tasks** — a table with columns `# | Repo | MC Task | Depends on | Blocks | State`. One row per sub-task. `Depends on` and `Blocks` reference other rows by their `#` (execution sequence within parent, from each sub-task's `subtask_number` frontmatter). `MC Task` column shows the sub-task's `jetrix_subtask_number` (e.g. `Subtask-7`) so a reader can click through in the MC UI.
3. **Touch points** — Reuse / New table at the parent level, aggregated across all sub-tasks. Same shape as detailed-mode §5 but combined — a component reused across two sub-tasks appears once with both sub-tasks listed.

Body absent from rollup mode: no API endpoints section (each sub-task's Implementation has them), no Database modifications section (each sub-task's Implementation has them), no Frontend UI section (each sub-task's Implementation has them).

Output path: `features/<slug>/tl-plan.md`

### Mode selection — how the caller decides

`/dev:plan` picks the mode based on the sub-task decision (see the `/dev:plan` command's Stage 2 spec):

| Situation | Modes invoked |
|---|---|
| Feature is parent-alone (single-repo, bug, story, `--no-split`) | 1× `implementation` on parent → writes `features/<slug>/implementation.md` |
| Feature is split (multi-repo, `--split`) | N× parallel: `description` on each sub-task → writes `subtask/<repo>/description.md`, AND `implementation` on each sub-task → writes `subtask/<repo>/implementation.md`. Then 1× `rollup` on parent → writes `features/<slug>/tl-plan.md` |

## Workflow

### 1. Resolve the target feature(s)
Take the target from the user: one feature folder / slug / id, or the whole set. If an `initiative=<name>` filter is present, restrict to features whose `feature.md` `initiative` matches (report which features the filter selected). If the target resolves to nothing, tell the user and stop — do not compose a made-up feature.

### 2. Skip-unchanged check (unless `--force`)
For each targeted feature, compute the `inputs_hash` — sha256 over the concatenation of `feature.md` + each owned unit file's body (frontmatter stripped, CRLF normalised). If a `tl-plan.md` exists with the same `inputs_hash` in its frontmatter, skip it and report `skipped-unchanged`. This is the same idempotence pattern `/jetrix:push` uses via `sync-state.json`.

### 3. Read the feature and its graph slice
For each feature to compose:
- Read `feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md`. (`implementation-plan.md` and `status.md` are local-only and irrelevant here — do NOT read them.)
- **Ensure the graph is local.** The graph lives per-repo under `<repo>/context/code-context/{frontend|backend|database}/`. If any of the 3 indexes is missing for a required repo, tell the user to run `/tl:plan` (for missing units) or `/tl:code-map` (to reverse-map an existing repo) first — no indexes, no graph — and stop.
- Resolve owned units from the three indexes using the awk recipe from `references/index-resolution.md` (same matching rule `/jetrix:push implementation` uses — feature-cell word-boundary match, and the 2-hop endpoint→entity chain via each endpoint row's `Reads/Writes Entities` cell). Reject a feature with **zero owned units** — tell the user to run `/tl:plan` first, do not fabricate units.
- **Any unit file whose path resolves in an index but doesn't exist locally** becomes `[HELD · unit file unavailable — <id>]` in §9 with `TBD — unit-detail file unavailable` at its heading. Ask the user to sync the involved repo (`git pull` inside it) and re-run.
- Read every owned page, endpoint, and entity file.

### 4. Repo-scan preflight
For each app declared in `.jetrix/project.json`, resolve its absolute local path following **`plugins/jetrix/references/repo-paths.md`** — read `.jetrix/cache/repolocation.json`; if a path is missing or its folder has moved, ask the teammate and update the JSON; if it's marked `"SKIPPED"`, treat it as unavailable without asking. Then, for each resolved path:
- `ls` the top-level and one level down to discover the routing / handler / model layout. Look for the entry points: `app/`, `src/`, `pages/`, `routes/`, `controllers/`, `domains/`, `models/`, `entities/`, `schemas/`, and their language-specific analogues.
- **Never recurse further, never `Read` a source file, and never touch anything matching the off-limits patterns above.** This is a *shape* check to name plausible target file paths in §2/§3 — not to grep the codebase.
- For an app that ends up unavailable (missing or `SKIPPED`) → mark every file path in §2 and §3 that would have landed in that repo as `TBD — repo not cloned locally, resolve at build time` and surface it as an open item in §9.

### 5. Compose per mode

**Follow `references/implementation-plan-template.md`.** The template contains the body shape for all three modes; branch on the mode the caller specified.

Regardless of mode: Description, Business Rules, Acceptance Criteria, NFRs, Test Scenarios, and Dependencies of the PARENT feature are populated by BA push from the parent's BA files and never appear in this document. When composing a sub-task, `acceptance_criteria` and `test_scenarios` tabs stay empty (validation reads parent).

#### If mode == `implementation` (parent-alone or per-sub-task Implementation)

Five subsections, in this order. Cross-feature "must exist first" waits are captured in the **Dependencies tab** (BA-owned); code-reuse targets are captured in **Touch points** at the end of this document — never both.

1. **Build sequence** — one paragraph naming the phases and their dependency order, one mermaid step-graph. **No step table.** Each step's exit condition is captured inline in the API and Frontend sections below; the diagram is the sequence map only. A phase that depends on an undecided open question is marked `[HELD · waiting on OQ-<id>]` in the paragraph rather than pretending to be buildable.
2. **API endpoints** — one heading per endpoint the feature (or sub-task, if per-sub-task) creates or modifies (`### Create — <role>`, `### Update — <role>`). Each carries: path parameter table (if applicable), request body table + JSON example, **normative execution-order table** (steps 1..N, each with failure code), success JSON with the exact response code, refusals table with **one row per distinct `message`** (three `409` variants → three rows, never collapsed), and a paragraph on invariants (idempotency, partial-write behaviour, side effects).
3. **Database modifications** — one line describing the affected data object by role. "Fields written by this feature" table listing ONLY the fields this feature writes. One "Never touched" line naming existing fields the feature does not write (for reviewer boundary awareness). A paragraph on any state semantics the write relies on.
4. **Frontend UI** — an API-wiring table (`Surface | Trigger | Calls`), one heading per user-facing surface described by role (row action, dialog, list, etc.). The **row / list / summary** surface section starts with a one-line entry-point sentence naming where the parent page is reached from and whether it's a landing page (author-specific; not a fixed string). The dialog section names the surface, submits-to sentence, control table, on-success + on-refusal blocks, refusal-placement table, and a one-paragraph API service description. The dialog's trigger is implicit from the API-wiring table's "opens the <dialog>" row — do not add a separate "Location & hosting" ceremony section.
5. **Touch points** — Reuse / New table naming existing and new components **by role**. The Reuse rows capture what the feature reuses from the existing codebase; the New rows capture what this feature creates. Includes the internal review caveat about re-verifying reuse entries.

**Per-sub-task scoping when composing a sub-task's `implementation.md`:** only include units this sub-task owns (units in this sub-task's repo). API endpoints, Database modifications, and Frontend UI sections are scoped to the sub-task's repo. Cross-repo dependencies show up in Touch points as references to other sub-tasks by their sequence number (e.g. *"consumes API from sub-task 1 (backend)"*).

#### If mode == `description` (sub-task Description tab)

**One or two paragraphs of continuous prose** telling the story of what THIS sub-task does in business terms. No headings, no bullet lists, no tables, no code fences, no HTTP codes, no field lists.

**Inputs:** parent's `feature.md` (Objective + In/Out of Scope), `workflow.md` (flow steps), scoped to the operations THIS sub-task's repo owns via its owned units. Read each sub-task's owned endpoints/pages/entities to understand what happens in this slice — but describe the outcome in business language, never the mechanism.

**Business vocabulary:** use the actors, systems, and data terms the parent's BA files use ("supplier", "operations coordinator", "compliance service"), not the technical terms ("controller", "middleware", "collection").

**Distinct refusals surface in prose:** where an endpoint has multiple distinct refusals (e.g. `DUPLICATE_TAX_ID` vs `COMPLIANCE_UNAVAILABLE`), the narrative names each as a distinct business situation the actor sees ("the operator sees a specific reason when the supplier is already known, and a different message when the compliance check itself cannot run") — not the response code, the business situation.

**Length:** one to two paragraphs. Longer means you're leaking implementation detail — cut.

See `references/implementation-plan-template.md` §narrative for a full worked example.

#### If mode == `rollup` (parent Implementation tab when split)

Three sections in this order:

1. **Build sequence** — one paragraph naming each sub-task **by role** (backend, frontend, mobile) and describing the dependency order at the sub-task level, plus one mermaid step-graph showing sub-task nodes and their arrows. No endpoint/entity/page detail — those live in each sub-task's Implementation tab.
2. **Sub-tasks** — a table:
   ```
   |  #  | Repo     | MC Task    | Depends on | Blocks   | State    |
   |-----|----------|------------|------------|----------|----------|
   |  1  | backend  | Subtask-7  | —          | 2, 3     | PLANNED  |
   |  2  | frontend | Subtask-8  | 1          | —        | PLANNED  |
   |  3  | mobile   | Subtask-9  | 1          | —        | PLANNED  |
   ```
   `#` = execution sequence (from each sub-task's `subtask_number` frontmatter). `MC Task` = `jetrix_subtask_number` from the same. `Depends on` / `Blocks` = other rows referenced by `#`. `State` = each sub-task's `current_state` from its `status.md`.
3. **Touch points** — aggregated Reuse / New table at the parent level. A component reused across multiple sub-tasks appears once with all consumers listed. Includes the internal review caveat about re-verifying reuse entries.

**No API endpoints, Database modifications, or Frontend UI sections in rollup mode** — those live per sub-task.

See `references/implementation-plan-template.md` §rollup for the full template.

### 6. Enforce the hard rules
Before writing the file. These are absolute — any violation means the composition is wrong and must be redone.

**Rule 1 — No file paths, anywhere.** Not in Touch points, not in headings, not in prose, not in code fences. Every component is named by its **role** — the leave controller, the decision dialog, the API service layer, the leave list, the row action. `controllers/Leave.js`, `src/components/**/*.jsx`, `models/LeaveRequest.js`, `routes/router.js`, and every other repo path is forbidden. The context graph (which the composer reads as input) has file paths — that is TL design detail; it is not for the reader of this document. The dev-agent, at build time, maps role names back to files via the local context graph, not via this document.

**Rule 2 — No framework, library, or version names, anywhere.** No `React`, `React 18`, `Vite`, `Express`, `Mongoose`, `mongoose.Schema`, `TipTap`, `Redux`, `Playwright`, `Jest`, `axios`, `@uiw/react-md-editor`, `Prisma`, `SQLAlchemy`. Describe the data object by role and by the fields written; do NOT include a schema code fence in any framework's syntax. Version numbers are always forbidden.

**Rule 3 — No duplication of other tabs.** This document contains ONLY the sections defined by its mode (5 subsections for `implementation`; 3 sections for `rollup`; one to two paragraphs of prose for `description`). No Business Goal, no AC list, no NFR list, no Business Rule list, no Test Scenarios, no Dependencies / Assumptions / Open Questions, no Prerequisites section (cross-feature waits live in the Dependencies tab; code-reuse targets live in Touch points). If a fact belongs in another tab, do not restate it here — even briefly. **In narrative mode**, the workflow diagram belongs on the parent's Description tab (BA-owned) — do not include a mermaid diagram in a sub-task Description.

**Rule 4 — No feature identity in visible content.** Feature id, initiative, slug, and provenance live in the frontmatter and MC task metadata. Never a `# FEAT-…` H1. Never a "Provenance:" line. Never a reference to `feature.md`, `workflow.md`, `acceptance-criteria.md`, `ba/*`, `context/*`, or any scope-review filename. The Description and Dependencies tabs (BA-owned) carry any provenance the reader needs.

**Rule 5 — Existing schema fields the feature does not write are named in one line, not tabled.** If the feature writes four fields on an existing data object, the Database modifications table contains those four — and only those four. Fields not written are named on a single "Never touched: `<field-a>`, `<field-b>`, `<field-c>`" line. That is the whole allowance.

**Rule 6 — Response codes and messages are discriminated explicitly.** If an endpoint returns three distinct `409` messages, the Refusals table has three rows. Never collapse a code's variants into one row. Similarly for `400` variants.

**Rule 7 — No client-narrative, no provenance callouts, no author commentary.** Forbidden: *"the client chose transparency knowingly"*, *"this document being complete is not consent"*, *"a module HR uses daily"*, `⚠ PROVENANCE — PLANNED, NOT BUILD-READY` blockquotes, *"acceptance criteria are authored as bullets without ids"*, *"SIMULATED response round"* preambles. The Description and Dependencies tabs carry any client-facing note.

**Rule 8 — No aspirational text.** No *"consider"*, *"might"*, *"could"*, *"we should think about"*. Either the decision is made and stated, or the phase is marked `[HELD · waiting on OQ-<id>]`.

**Rule 9 — No secrets.** Env var **names** only if referenced at all — never values or credentials, even if the repo scan surfaced them.

**Rule 10 — Size budget (mode-dependent).**
- `implementation` mode: target 10–15 KB. Warn at 55 KB. **Refuse to write over 60 KB** — MC caps every tab at 60 000 characters. If oversized, do NOT truncate; surface the overflow and ask the user to split the feature.
- `rollup` mode: target 2–5 KB (short by design — detail lives per sub-task). Warn at 20 KB. If a rollup is exceeding 20 KB, you're probably duplicating detail that belongs on sub-tasks — check for that first.
- `description` mode: target 500–1500 characters. Warn at 3 KB. Longer means implementation detail has leaked into the narrative — cut.

**Rule 11 — No invention.** Every endpoint contract, every DB field, every UI surface traces to the context graph or the feature files. When silent, mark the affected step `[HELD · waiting on OQ-<id>]` and name the gap. Do not guess.

### 7. Write the file + update inputs_hash
Write to the mode-appropriate output path with the mode-appropriate frontmatter (see the two frontmatter shapes at the top of the Operating contract section). `inputs_hash` is set to the sha256 computed in step 2 — for `description` and per-sub-task `implementation`, hash the sub-task's owned unit files, not the whole feature's owned units. Use CRLF-safe I/O — write with `\n` line endings; the push stage handles CRLF normalisation.

**Mode → output path recap:**
- `implementation` on parent-alone → `features/<slug>/implementation.md` (frontmatter: `doc_type: implementation`, `compose_mode: implementation`)
- `implementation` on a sub-task → `features/<slug>/subtask/<repo>/implementation.md` (frontmatter: `doc_type: implementation`, `compose_mode: implementation`)
- `description` on a sub-task → `features/<slug>/subtask/<repo>/description.md` (frontmatter: `doc_type: description`, `compose_mode: description`)
- `rollup` on parent → `features/<slug>/tl-plan.md` (frontmatter: `doc_type: tl-plan`, `compose_mode: rollup`)

**Never write both `tl-plan.md` and sub-task files from the same call** — one call, one mode, one output. Callers that need both (`/dev:plan` Stage 2 in split branch) make multiple calls.

Preserve any manual developer edits marked with `<!-- KEEP -->` HTML comment sentinels — read the existing file first, extract fenced regions between `<!-- KEEP -->` and `<!-- /KEEP -->`, and reinsert them at the same section anchor on write. If a KEEP region has no matching anchor in the newly composed body, keep it at the section tail and warn the user.

### 8. Log material decisions
If composing forced a real design choice (e.g. picking one of two plausible target file paths, choosing which of two reused endpoints a page consumes), append a `DEC-###` row to `shared-context/decision-log.md`. Composition choices that are pure arrangement (order of sections, choice of table vs list) don't need a decision — only technical choices that later reviewers might contest.

### 9. Report per feature
Return: features composed vs skipped-unchanged (with reason each), the size per feature, open items surfaced (grouped by feature), and any features where the repo-scan preflight left file paths as `TBD`. Link to each `tl-plan.md`. If any feature refused to compose (missing units, size overflow, unresolved TBD in a critical field), name it and the reason — never silently swallow.

## Completion criteria

Depends on the mode.

**`implementation` mode** — a feature (or sub-task) is composed when: the output file exists at the mode-appropriate path with the correct frontmatter; contains exactly the five subsections (Build sequence · API endpoints · Database modifications · Frontend UI · Touch points); the Build sequence has intro paragraph + mermaid (no step table); every endpoint owned has its Execution-order and Refusals tables with one row per distinct response `message`; the Database modifications table lists only the fields written with a one-line "Never touched" boundary; every UI surface is named by role with its API wiring; every REUSE from the context graph is captured in Touch points (not a separate Prerequisites section); the file is ≤ 60 KB; and none of the Rules 1–11 above are violated.

**`description` mode** — a sub-task Description is composed when: `subtask/<repo>/description.md` exists with the correct frontmatter; the body is one or two paragraphs of continuous prose (no headings, no lists, no tables, no code fences); business vocabulary used throughout; distinct refusals named as distinct business situations (not response codes); length between 500–1500 characters (warn at 3 KB); none of the Rules 1–11 above are violated.

**`rollup` mode** — a parent's rollup Implementation is composed when: `features/<slug>/tl-plan.md` exists with `compose_mode: rollup` in frontmatter; contains exactly the three sections (Build sequence · Sub-tasks · Touch points); the Build sequence names each sub-task by role and has a mermaid step-graph of sub-task nodes; the Sub-tasks table has one row per sub-task with `#`/`Repo`/`MC Task`/`Depends on`/`Blocks`/`State` columns; no API endpoints / Database modifications / Frontend UI sections present (those live per sub-task); target ≤ 5 KB; none of the Rules 1–11 above are violated.

**Path / framework / duplication pre-write scan.** Before writing, verify the document does NOT contain any of these patterns:
- File-path fragments: `src/`, `app/`, `controllers/`, `routes/`, `models/`, `components/`, `.js`, `.jsx`, `.ts`, `.tsx`, `.py`, `.go`.
- Framework / library names: `React`, `Vite`, `Express`, `Mongoose`, `TipTap`, `Redux`, `Playwright`, `Jest`, `axios`, `Prisma`, `SQLAlchemy`, `mongoose.Schema`, `new Schema`.
- Version numbers next to a technology name: `React 18`, `Node 20`, etc.
- Feature-id headings: `# FEAT-` or the feature id in any H1/H2 heading.
- Business goal / user flow / acceptance criteria / NFR / test scenario / dependency prose (they belong in other tabs).

Any hit means the composition is wrong. Rewrite before writing to disk.

## Principles

- **Compose, don't author.** The design lives in the graph. You arrange it for one feature.
- **Inline what a developer needs; cite what they don't.** Endpoint contracts of endpoints the feature owns are inlined. Endpoint contracts of endpoints the feature *reuses* are cited by id and their repo path.
- **Never invent.** Where the source is silent, surface the gap. `TBD` cells and §9 rows are the honest way; a plausible guess is the wrong way.
- **Bridge to business, don't restate it.** A short `## Business Goal` section (~2–3 sentences + a one-line Users) sits above §1 so a developer opening MC's Implementation tab knows the *what and for whom*. Everything beyond that — full objective, in/out of scope, personas, journeys — stays in `feature.md`.
- **Never leak secrets.** Env var names, never values. Off-limits files during repo scan.
- **Stay under the cap.** MC rejects >60 KB. If the composed doc would exceed the cap, ask the user to split the feature — don't truncate.
- **Preserve developer edits.** `<!-- KEEP -->` blocks survive re-composition.
- **Idempotent by inputs_hash.** A re-run against unchanged inputs is a no-op.
