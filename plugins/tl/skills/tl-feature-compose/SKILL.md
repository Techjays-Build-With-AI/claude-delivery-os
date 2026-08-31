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

Body sections (v2.3 — target 10 sections; **`tl-feature-compose` writes ALL sections §§1-9 in ONE pass** at `/dev:plan` Stage 4; §10 is appended later by `/dev:build` Stage 11):

1. **Business flow** — 2-3 sentence overview, business terms (from parent's `feature.md`)
2. **Build sequence** — ordered steps table (# / Step / Units / Satisfies / Notes) + mermaid step-graph (from Stage 2 analysis scratchpad `dev/<repo>-analysis.md § Build sequence`)
3. **Impacted components** — 12-dimension impact matrix — Frontend/Backend/DB/Authz/Integrations/Jobs/Notifications/Monitoring/Tests/Docs/Flags/Analytics (from Stage 2 analysis scratchpad § Impact matrix)
4. **API endpoints** — request/response tables, execution order, refusals (from TL context graph — owned endpoint units)
5. **Database changes** — new + modified tables/collections, indexes (from TL context graph — owned entity units)
6. **Frontend UI** — surfaces + API wiring (from TL context graph — owned page units; omitted for backend-only sub-tasks)
7. **Touch points** — Reuse / New table (from TL context graph + `code-context-index.md`)
8. **Test strategy** — unit / integration / e2e / concurrency coverage per step (from Stage 2 analysis scratchpad § Test strategy)
9. **Risks + rollback** — assumptions carried, schema-trap notes, rollback plan (from Stage 2 analysis scratchpad § Risks)
10. **How to verify locally** — developer runbook (stubbed here as `_(populated by /dev:build Stage 11)_`; filled after build)

**Hard precondition (v2.3 refactor):** this mode REFUSES to run if the Stage 2 analysis scratchpad is missing OR blockers are still OPEN. Sections 2, 3, 8, 9 need the analysis scratchpad; running without it produces stub sections which we deliberately reject. See §"Hard rules" Rule 12 below.

**Input contract for §§2, 3, 8, 9 (Stage 2 analysis scratchpad):**

```yaml
# dev/<repo>-analysis.md — Stage 2's output
---
doc_type: analysis-scratchpad
schema_version: 1.0
produced_by: dev
feature_id: FEAT-...
subtask_number: 1
subtask_repo: backend
generated_at: <ISO>
---
build_sequence:      # → §2
  - step: "..."
    units: [EP-...]
    satisfies: [BR-..., AC-...]
    notes: "..."
impact_matrix:       # → §3
  frontend: N/A | <impact>
  backend: <impact>
  database: <impact>
  authz: <impact>
  integrations: <impact>
  jobs: N/A | <impact>
  notifications: N/A | <impact>
  monitoring: <impact>
  tests: <impact>
  docs: <impact>
  feature_flags: N/A | <impact>
  analytics: N/A | <impact>
test_strategy:       # → §8
  - level: unit
    covers: [AC-1, AC-9]
    evidence: "..."
risks_and_rollback:  # → §9
  risks:
    - description: "..."
      severity: medium | high | low
      mitigation: "..."
  rollback: "..."
```

Output path:
- Parent-alone → `features/<slug>/implementation.md`
- Per sub-task → `features/<slug>/subtask/<repo>/implementation.md`

### Mode: `description` (sub-task Description tab — v2.3.5 user-story format)

A **user story** describing what a user can do, plus the business context around it. This is the format a Product Owner or stakeholder reads — voiced from the USER's perspective ("As an operations coordinator, I want to add a holiday…"), not from the dev's perspective ("This sub-task delivers a holiday endpoint…"). Replaces the v2.3.4 dev-centric "what this sub-task delivers" phrasing which read as internal-facing capability description rather than a real user story.

Six deterministic sections, in this order:

1. **User story** — the classic three-line format: `**As a** <role>, **I want** <action>, **So that** <benefit>`. Role comes from parent's `feature.md` `users:` frontmatter or `workflow.md` actors. Action is what the user WANTS to do (not what the system does). Benefit is the business outcome the user gets. Framing sentence follows: 2-3 sentences of business context establishing WHY this matters to the user — the pain point being solved, the current workaround being replaced.
2. **User scenarios** — bulleted list of the user's flows in business terms, one bullet per scenario (not per endpoint). Format each: **bold action name** — 1-2 sentences describing what the user does, sees, and gets. Written in present-tense active voice from the user's POV: "The user selects a date and name, and the system…" not "The system accepts a POST body with…". If a scenario involves a decision or fork, describe it business-terms.
3. **Business rules that apply** — cite the parent's `BR-N` references + a 1-line paraphrase per rule. Only BRs that shape what the USER sees or does in THIS sub-task's flows.
4. **What users see when refused** — bulleted list of business situations where the user doesn't get what they asked for. Framed as what the user READS or PERCEIVES, not what the API returns: "The user is told the date is already taken and shown the name of the existing holiday" not "409 with DUPLICATE_TAX_ID".
5. **Out of scope for this user story** — bulleted list of what the user CAN'T do in this sub-task and where they'd go for it. Includes cross-sub-task boundary from the user's perspective: "Filling in the calendar visually — that user story is delivered by sub-task 2 (frontend)."
6. **Related user stories** — cross-references to sibling sub-tasks (only present when the feature was split; omit for parent-alone). One line per sibling, framed as a companion user story: "**Sub-task 2 (frontend)** delivers the user story for how the user actually TOUCHES this — the visual calendar and add form."

**Formatting rules:**
- Headings: `## <Section title>` — never level 1, never level 3+
- Bullets: `-` prefix, indent-preserved sub-bullets allowed for elaboration
- Bold role names: **Add a holiday**, **Duplicate holiday** — first two words of each bullet
- No HTTP status codes (`400`, `409`, `201`), no field names (`added_by`), no file paths, no framework names, no method names (POST/GET/DELETE), no tables, no code fences, no mermaid.
- Business vocabulary from parent's `feature.md` + `workflow.md` — actor names, system names, data terms — never technical translations

### Per-section character budget (v2.3.4 — HARD budget planned upfront, not trimmed after)

**Plan lengths BEFORE composing.** The description mode is intentionally short — MC's Description tab is a scanning surface, not a reading surface. Every section has a hard byte budget the compose MUST hit on the first write. If a section would exceed its budget, drop the least-load-bearing sub-claim BEFORE writing — never compose freely then trim after, because the trim step is where nuance gets flattened and where inconsistent pacing between features shows up.

| Section | Target (chars) | Max (chars) | What fits |
|---|---|---|---|
| **Overview** | 180 | 250 | 2 short sentences — what the sub-task delivers + who benefits |
| **What this sub-task delivers** | 500 | 700 | 3-5 bulleted operations, each 100-150 chars (bold role name + 1-2 sentence business behavior) |
| **Business rules honored** | 250 | 400 | 4-6 BR-N references with a 1-line paraphrase each (~50 chars per row) |
| **Distinct refusal cases** | 250 | 400 | 3-4 bulleted refusals (bold situation name + 1 short sentence, ~60-80 chars each) |
| **Out of scope for this sub-task** | 150 | 250 | 2-3 short bullets (30-70 chars each) |
| **Related sub-tasks** | 80 | 150 | 1-2 sibling refs (50-80 chars each), only present when split |
| **Total (soft target)** | **~1400** | **~2000** | leaves ~1 KB headroom under the 3 KB warn line |

**Composing to budget — the drop rules (apply BEFORE writing each section):**

- **Overview** — if you'd write 3 sentences, drop the middle one. Keep first (what) + last (why/who).
- **What this sub-task delivers** — if you'd write 6+ operations, group by verb ("Add / List / Remove" → 3 bullets). If a bullet needs 3+ sentences to explain, drop the third — you're leaking mechanism.
- **Business rules honored** — cite only the BRs THIS sub-task's operations enforce. If a BR is inherited from parent scope but the code path here doesn't touch it, skip.
- **Distinct refusal cases** — one bullet per DISTINCT business situation. Similar refusals (missing name / missing date) merge into one bullet: "Missing required field — the response names which field."
- **Out of scope** — only list boundary items the reader would otherwise expect. If it's obviously not this sub-task (e.g. billing, admin), don't burn a bullet on it.
- **Related sub-tasks** — one line per sibling. If parent-alone (no split), omit this section entirely.

**Never do a "check size, then trim" pass.** If the first-pass size is over 2 KB, the drop rules above were violated in the compose — rewrite the offending section within budget, don't shave prose.

**Full worked example** (holiday-calendar-management backend sub-task):

```markdown
---
doc_type: description
schema_version: 2.0
produced_by: dev
feature_id: FEAT-HCAL-01
subtask_number: 1
subtask_repo: backend
compose_mode: description
composed_at: 2026-08-31T15:00:00Z
inputs_hash: sha256:...
---

## User story

**As a** signed-in portal user (HR admin or any employee),  
**I want to** add, view, and remove the company's official holidays for a chosen year,  
**So that** everyone consults one authoritative list instead of asking "is this day a holiday?" in Slack and waiting for someone with the annually-emailed PDF to answer.

Today the holiday calendar lives in a PDF that HR emails once a year, and the same "is [date] a holiday?" question gets asked in Slack every week — with wrong or missing answers. This user story delivers a live, shared calendar the whole company reads from and every action is attributable so a wrong entry has a clear author.

## User scenarios

- **Adding a holiday** — The user picks a date and types a name (up to 100 characters). The system saves the entry, records who added it and when from the signed-in session (not from what the user types), and the entry appears in that year's list.
- **Viewing the year's holidays** — The user opens the calendar and sees the current year's holidays sorted by date, showing each holiday's date, name, and who added it. The user can switch to the year before or the year after — no other year is offered.
- **Removing a holiday** — The user selects Remove on a row and confirms; the entry disappears from every future view. The system keeps who removed it and when for the audit trail, but there is no way to bring it back through the interface.

## Business rules that apply

- **BR-1** — a date can hold only one holiday; the second add on the same date is refused.
- **BR-2** — holidays can only be added for the current calendar year or later.
- **BR-4** — no permission gate; any signed-in user can add or remove.
- **BR-5** — "added by" and "added at" are captured from the session and server clock, not the request body.
- **BR-9** — removal is a soft delete: the record is retained with attribution, but hidden from every view.

## What users see when refused

- **Date already taken** — the user is told which holiday already occupies that date, by name.
- **Year is in the past** — the user is told the year must be current or later.
- **Missing date or name** — the user is told which required field they left blank.
- **Someone else already removed it** — the user is told the holiday was already removed, rather than a silent success.

## Out of scope for this user story

- Filling in the visual calendar view — that user story is delivered by **sub-task 2 (frontend)**.
- Any offer of a restore path — removal is deliberately unrecoverable through the UI.
- Any effect on the Leave module — Leave continues counting inclusive calendar days regardless of holidays.

## Related sub-tasks

- **Sub-task 2 (frontend)** consumes all three endpoints delivered here.
```

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

**Rule 10 — Size budget (mode-dependent; description mode is HARD-planned upfront in v2.3.4).**
- `implementation` mode: target 10–15 KB. Warn at 55 KB. **Refuse to write over 60 KB** — MC caps every tab at 60 000 characters. If oversized, do NOT truncate; surface the overflow and ask the user to split the feature.
- `rollup` mode: target 2–5 KB (short by design — detail lives per sub-task). Warn at 20 KB. If a rollup is exceeding 20 KB, you're probably duplicating detail that belongs on sub-tasks — check for that first.
- `description` mode (v2.3.4): **HARD per-section budget, planned upfront, not trimmed after.** Total target ~1400 chars, max ~2000 chars, absolute refuse-line 3000 chars. See §"Per-section character budget" in the description mode spec above for the section-by-section allocation + drop rules. **Do NOT compose freely then trim** — trim-after produces flat, uneven prose and inconsistent pacing across features. If the compose output is > 2000 chars on first write, one of the section drop rules was violated — rewrite the offending section within its budget, don't shave prose after.

**Rule 11 — No invention.** Every endpoint contract, every DB field, every UI surface traces to the context graph or the feature files. When silent, mark the affected step `[HELD · waiting on OQ-<id>]` and name the gap. Do not guess.

**Rule 11.5 — Markdown rendering discipline (v2.3.5 — for `implementation` mode).** MC's tab renders the markdown as-is; malformed markdown displays as garbage. The most common failure modes and their explicit rules:

- **Tables MUST have exactly one row per line.** No pipe-run-on. Every `|` row ends with a `\n` before the next row starts. WRONG: `| Step | Units | Notes |\n|---|---|---| | 1 | ... | ... | | 2 | ... | ... |` (rows crammed on one line — renders as one giant messy row). RIGHT: each row on its own line, separator row (`|---|---|---|`) on its own line between header and body.
- **Mermaid diagrams MUST use `\`\`\`mermaid` fenced code blocks with real mermaid syntax.** A numbered list is NOT a mermaid diagram. WRONG: `1. Service ops\n2. Section shell\n3. Year list\n4. …` — renders as a list, no diagram. RIGHT: `\`\`\`mermaid\nflowchart TD\n    S1[Service ops] --> S2[Section shell]\n    S2 --> S3[Year list]\n    …\n\`\`\`` — renders as a flowchart in MC.
- **Section headings use `##` (level 2) only.** Never `#` (level 1 — that's the MC tab title) and never level 3+ nested inside a section.
- **Code fences for anything that MUST render as monospace** — JSON examples, curl commands, unit ID lists. Language hint after the opening triple-backticks (```json, ```bash, ```mermaid).
- **Bullet lists use `-` prefix consistently.** Never mix `*` and `-`.
- **Blank line before/after every table, code fence, and heading.** Missing blank lines make markdown parsers concatenate blocks.

**Rule 11.6 — Frontend sub-task API section INCLUDES consumed contracts in full (v2.3.5).** A frontend sub-task doesn't OWN any endpoint — but the developer needs the FULL request/response/refusal shape of every endpoint it consumes to build correctly. §4 API endpoints for a frontend sub-task MUST include:

- One `### <Method + Path>` heading per consumed endpoint (e.g. `### POST /api/holidays — Add a holiday (owned by sub-task 1 backend, consumed here)`)
- Request body table (fields, types, required, constraints) — copied verbatim from the owning sub-task's endpoint unit
- Response body JSON example — copied verbatim
- Refusals table — one row per distinct message (409 DATE_ALREADY_HOLIDAY, 400 NAME_TOO_LONG, etc.) — copied verbatim
- One-line pointer to the owning unit: `Owned by: EP-HCAL-01 (Inhouse-server/context/code-context/backend/domains/holiday/endpoints/add-holiday.md)`

The v2.3.4 output that only said "None owned. This sub-task consumes the three operations delivered by sub-task 1" was WRONG shape for §4 — it leaves the frontend developer with no contract in view. The prose about "three details of those contracts are load-bearing" belonged in §7 Touch points (as caveats on the consumed contracts), not as a substitute for §4's contract tables.

**Rule 11.7 — Every sub-task's §4-§7 must reach the same structural completeness bar.** A frontend sub-task's §5 (Database changes) is legitimately "N/A" — but its §4 (API endpoints), §6 (Frontend UI), §7 (Touch points) must each be as concrete as the backend's are for the sections that DO apply to it. If a frontend sub-task's §4 is 3 sentences of prose while its backend sibling's §4 is 500 lines of contract tables, that's a completeness gap — the frontend section pulls the consumed contracts up per Rule 11.6.

**Rule 12 — Analysis scratchpad precondition (v2.3, `implementation` mode only).** Before writing `implementation.md`, verify:
1. `dev/<repo>-analysis.md` (sub-task) OR `dev/analysis.md` (parent-alone) exists with `doc_type: analysis-scratchpad` frontmatter and non-empty `build_sequence`, `impact_matrix`, `test_strategy`, `risks_and_rollback` blocks.
2. `dev/<repo>-plan-blockers.md` (or `dev/plan-blockers.md` for parent-alone) is either absent OR has `status: RESOLVED` in frontmatter.

If either precondition fails, REFUSE to compose. Return a `stage_4_precondition_failed` error naming which precondition + which file. Never fabricate sections 2, 3, 8, 9 without the scratchpad — that produces the half-baked file this refactor exists to prevent. The caller (`/dev:plan` Stage 4 in `implementation-preparation.md`) checks the same preconditions before invoking this skill; both are belt-and-suspenders.

**Rule 13 — Description mode: user-story voice + no HTTP codes / no field names / no framework leakage.** In `description` mode (v2.3.5):

- **User-story voice mandatory** — §1 opens with the classic "**As a** … **I want** … **So that** …" three-liner. Every scenario in §2 is written from the user's perspective, present-tense active voice ("The user picks a date and types a name…"), NOT from the system's ("This sub-task saves a holiday…").
- **NO dev-centric phrasing** — no "This sub-task delivers…", no "The service saves…", no "The endpoint accepts…". Reframe from what the SYSTEM does to what the USER does and sees.
- **NO response codes** (`400`, `409`, `201`), NO field names (`added_by`, `is_removed`), NO file paths, NO framework names, NO HTTP methods (POST/GET/DELETE), NO tables, NO code fences, NO mermaid.
- **All content in business vocabulary** from parent's `feature.md` + `workflow.md` + `workflow.md`'s actors — never technical translations.

Rule 2's "no framework names" applies here too, more strictly. See §"Compose modes" > "Mode: description" for the 6-section structure + example.

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
