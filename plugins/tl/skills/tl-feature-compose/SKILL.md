---
name: tl-feature-compose
description: Compose self-contained implementation content for a feature or sub-task in one of three modes — implementation (plan-only 9-section technical spec §1–§9, stack-agnostic vocabulary, for a parent Task's Implementation tab, or for a single sub-task's Implementation tab scoped to one repo), description (user-story format for a sub-task's Description tab), or rollup (parent Implementation tab when the feature was split into sub-tasks — names each sub-task, sequence, cross-task dependencies, and touch points). Use whenever a feature has been planned technically (units exist in `context/frontend|backend|database/`) and needs a document a developer or coding agent can build from without opening the other files. Point it at one feature folder, a `FEAT-<AREA>-NN` id, an `initiative=<name>` slice, or the whole `features/` set; it reads the feature, its owned pages/endpoints/entities, and (when the repo is cloned locally) the target repo's file layout, and writes the appropriate document per mode. It never restates business rationale (that's in `feature.md`), never invents an endpoint/contract/schema/path the source can't ground, never leaks framework names or file paths, and never composes above Mission Control's 60 KB tab cap.
---

# TL Feature Compose (context graph + feature breakdown → buildable per-feature plan)

You are turning the **linked technical context graph** the TL feature-planning skill produces into a **self-contained per-feature implementation plan** — one document a developer or coding agent can hand straight to Claude and say "build this," without opening the feature folder, the workflow, the acceptance criteria, or any unit file. The graph is a memory for reuse across features; `tl-plan.md` is the buildable output for one feature.

The defining behaviour of this skill is **composition, not authoring**. You do not design new pages, new endpoints, new entities, or new integrations — that is the `tl-feature-planning` skill's job, and if you find genuinely undecided design points you record them as open questions in §8 (Risks + rollback) rather than inventing them. What you *do* is arrange the design that already exists into a document a developer can read top-to-bottom and build from, inlining what needs to be inlined (endpoint contracts, entity columns, page shape) and citing IDs where a follow-through is enough (a reused endpoint the feature does not modify, a `DEC-###` decision the developer does not need to re-derive).

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
capabilities: [<role-a>, <role-b>]    # v2.3.11 — machine-readable roles this sub-task plays in the split (see Rule 11.15)
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

Body sections (v2.3.16 — 8 sections §1–§8, stack-agnostic vocabulary; **`tl-feature-compose` writes ALL sections in ONE pass** at `/dev:plan` Stage 4. History: `§1 Business flow` and `§10 How to verify locally` removed in v2.3.10 (plan-only). v2.3.11 renamed §3/§4/§5 stack-agnostic + moved Shared contract to tail. **v2.3.16 removed `§7 Coverage`** — coverage is not a plan-time table; the plan states INTENT via §1 Satisfies column + the stack-driven tier pool (from `qa/quality-gates.md`, or from stack detection when user skipped QA setup at plan time), and EVIDENCE lives in `dev/acceptance-map.md` built at `/dev:build` Stage 8. No "Deferred" concept anywhere — every parent AC/BR/TS in this sub-task's scope is COVERED at every applicable tier for the layer):

1. **Build sequence** — ordered steps table (# / Step / Files / Units / Satisfies) + mermaid step-graph (from Stage 2 analysis scratchpad `dev/<repo>-analysis.md § Build sequence`). The Files column names WHERE the code lands per step (new vs modified paths). **The Satisfies column is the CANONICAL plan-time coverage owner** — each parent AC/BR/TS ID in this sub-task's scope appears in at least one step's Satisfies column, per Rule 11.11.
2. **Impacted components** — 12-dimension impact matrix — Surfaces/Operations/Stored data/Authz/Integrations/Background jobs/Notifications/Observability/Existing tests/Docs/Flags/Analytics (from Stage 2 analysis scratchpad § Impact matrix). Repo/stack-specific dimension names (e.g. "Screens" for UI repos, "Migration" for stateful repos, "Accessibility" for interactive repos) are added by the compose based on repo shape.
3. **Operations exposed and consumed** — every operation this sub-task owns or consumes (from TL context graph — owned endpoint/RPC/job units). Stack-agnostic name — covers REST endpoints, GraphQL resolvers, gRPC methods, queue message handlers, background jobs, CLI commands. Consumer sub-tasks pull owner's contract verbatim per Rule 11.6.
4. **Stored data changes** — every persisted-state change this sub-task makes (from TL context graph — owned entity/collection/table/document units). Stack-agnostic name — covers SQL tables, NoSQL collections, KV keys, object-store paths, cache regions, files-on-disk stores. If the sub-task's repo has no persistence, `None.` (one line, per Rule 11.12).
5. **User-facing surfaces** — every UI/interaction surface this sub-task adds or modifies (from TL context graph — owned page/screen/CLI-command units). Stack-agnostic name — covers web pages, mobile screens, CLI commands, terminal UIs, service dashboards. If the sub-task has no user-facing surface (e.g. backend-only), `None. Delivered by <sibling>.` (one line).
6. **Touch points** — Reuse / New / Cross-sub-task table (from TL context graph + `code-context-index.md`). Cross-sub-task E2E ownership is stated here as a Cross-sub-task row (e.g. `E2E for AC-M owned by sub-task N (<repo>) — tests/e2e/<flow>.spec.js`).
7. **Risks and rollback** — Risks table + Out of scope for this sub-task + two-tier rollback (cheapest lever, then full — see Rule 11.14). NO "Assumptions" heading — boring decisions live in §3 Invariants/Authz clauses and §5 Effects/on-success clauses per Rule 11.13 §5. Mitigation cells reference AC/BR/TS IDs + tier (e.g. `Covered by AC-1 + BR-3 at Unit + Integration tiers`), never a specific test file (test files live in `dev/acceptance-map.md` at build time).
8. **Shared contract** — feature-wide invariants inherited byte-for-byte across every sub-task in a split (see Rule 11.3). Placed LAST so the plan opens with buildable work and closes with the reference contract the reader looks up when a question arises.

**Coverage NOT in the plan** — no `§7 Coverage` table. Plan-time intent lives in §1 Satisfies column + qa/quality-gates.md tier pool (or stack-detected fallback pool when the user skipped QA setup at plan time). Build-time evidence lives in `dev/acceptance-map.md`. The plan does not restate what those two artifacts already own.

**Hard precondition:** this mode REFUSES to run if the Stage 2 analysis scratchpad is missing OR blockers are still OPEN. Sections 1, 2, 7, 8 need the analysis scratchpad; running without it produces stub sections which we deliberately reject. See §"Hard rules" Rule 12 below.

**Input contract for §§1, 2, 7, 8 (Stage 2 analysis scratchpad):**

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
build_sequence:      # → §1
  - step: "..."
    units: [EP-...]
    satisfies: [BR-..., AC-...]
    notes: "..."
impact_matrix:       # → §2
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
coverage:            # → §7 (Coverage)
  - level: unit
    covers: [AC-1, AC-9]
    evidence: "..."
risks_and_rollback:  # → §8
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

A **short document** listing each sub-task by repo + sequence, cross-task dependencies, and touch points at the parent level. Used only when the feature was split — replaces the detailed `implementation`-mode spec on the parent's Implementation tab since detail now lives on each sub-task.

Body sections (see `references/implementation-plan-template.md` §rollup):

1. **Build sequence** — one paragraph naming each sub-task by role (backend, frontend, mobile) + dependency order, plus one mermaid step-graph showing the sub-task sequence.
2. **Sub-tasks** — a table with columns `# | Repo | MC Task | Depends on | Blocks | State`. One row per sub-task. `Depends on` and `Blocks` reference other rows by their `#` (execution sequence within parent, from each sub-task's `subtask_number` frontmatter). `MC Task` column shows the sub-task's `jetrix_subtask_number` (e.g. `Subtask-7`) so a reader can click through in the MC UI.
3. **Touch points** — Reuse / New table at the parent level, aggregated across all sub-tasks. Same shape as `implementation` mode's §6 but combined — a component reused across two sub-tasks appears once with both sub-tasks listed.

Body absent from rollup mode: no Operations section (each sub-task's Implementation has them), no Stored data changes section (each sub-task's Implementation has them), no User-facing surfaces section (each sub-task's Implementation has them).

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
- **Any unit file whose path resolves in an index but doesn't exist locally** becomes `[HELD · unit file unavailable — <id>]` in §8 with `TBD — unit-detail file unavailable` at its heading. Ask the user to sync the involved repo (`git pull` inside it) and re-run.
- Read every owned page, endpoint, and entity file.

### 4. Repo-scan preflight
For each app declared in `.jetrix/project.json`, resolve its absolute local path following **`plugins/jetrix/references/repo-paths.md`** — read `.jetrix/cache/repolocation.json`; if a path is missing or its folder has moved, ask the teammate and update the JSON; if it's marked `"SKIPPED"`, treat it as unavailable without asking. Then, for each resolved path:
- `ls` the top-level and one level down to discover the routing / handler / model layout. Look for the entry points: `app/`, `src/`, `pages/`, `routes/`, `controllers/`, `domains/`, `models/`, `entities/`, `schemas/`, and their language-specific analogues.
- **Never recurse further, never `Read` a source file, and never touch anything matching the off-limits patterns above.** This is a *shape* check to name plausible target file paths in §1/§2 — not to grep the codebase.
- For an app that ends up unavailable (missing or `SKIPPED`) → mark every file path in §1 and §2 that would have landed in that repo as `TBD — repo not cloned locally, resolve at build time` and surface it as an open item in §8.

### 5. Compose per mode

**Follow `references/implementation-plan-template.md`.** The template contains the body shape for all three modes; branch on the mode the caller specified.

Regardless of mode: Description, Business Rules, Acceptance Criteria, NFRs, Test Scenarios, and Dependencies of the PARENT feature are populated by BA push from the parent's BA files and never appear in this document. When composing a sub-task, `acceptance_criteria` and `test_scenarios` tabs stay empty (validation reads parent).

#### If mode == `implementation` (parent-alone or per-sub-task Implementation)

Nine sections (§1–§9), in this order. Cross-feature "must exist first" waits are captured in the **Dependencies tab** (BA-owned); code-reuse targets are captured in **Touch points** — never both. See the top-of-file frame list for the full section spec.

1. **Build sequence** — one paragraph naming the phases and their dependency order, one mermaid step-graph, plus the ordered step table from the analysis scratchpad. Columns: `# | Step | Files | Units | Satisfies`. The Files column names WHERE the code lands per step (`New: <path>` / `Modified: <path>`); it replaces the free-form Notes column so each step has a concrete file target. A phase that depends on an undecided open question is marked `[HELD · waiting on OQ-<id>]` in the paragraph rather than pretending to be buildable.
2. **Impacted components** — 12-dimension impact matrix. Dimension names are stack-agnostic: Surfaces / Operations / Stored data / Authz / Integrations / Background jobs / Notifications / Observability / Existing tests / Docs / Flags / Analytics. Additional per-repo dimensions get added by the compose based on repo shape (e.g. `Screens` for UI-heavy repos, `Migration` for stateful repos, `Accessibility` for interactive repos). Every row substantive per Rule 11.12 — bare `N/A` halts.
3. **Operations exposed and consumed** — one heading per operation the sub-task creates, modifies, or consumes. Stack-agnostic name so it covers REST endpoints, GraphQL resolvers, gRPC methods, queue message handlers, background job triggers, CLI commands. Each carries: inputs table (name, location, type, required, constraint), request payload example, **normative order-of-checks table** (steps 1..N, each with failure code), success payload with the specific response code, refusals table with **one row per distinct `message`** (three `409` variants → three rows, never collapsed), and a paragraph on invariants (idempotency, partial-write behaviour, side effects). Consumer sub-tasks pull owner's contract verbatim per Rule 11.6.
4. **Stored data changes** — one heading per affected store described by role. "Fields written" table listing ONLY the fields this sub-task writes with the source-of-value for each. One "Never touched" line naming existing fields the sub-task does not write (for reviewer boundary awareness). Index declarations. Store-specific declaration hazards if any (e.g. constraint syntax gotchas). Migration block per Rule 11.10 if the store has live rows. If the sub-task's repo has no persistence, one line: `None.`.
5. **User-facing surfaces** — an operation-wiring table (`Surface | Trigger | Calls`), one heading per surface described by role (row action, dialog, list, screen, CLI command, etc.). Each surface heading carries: entry-point sentence naming where it's reached from, prop/input table, state model, control table, on-success + on-refusal blocks, refusal-placement table, and a one-paragraph description of the service/adapter layer that talks to the operation. If the sub-task has no user-facing surface (backend-only, job-only), one line: `None. Delivered by <sibling>.`.
6. **Touch points** — Reuse / New / Cross-sub-task table naming existing and new components **by role and by file path**. Reuse rows capture what the sub-task reuses from the existing codebase; New rows capture what this sub-task creates; Cross-sub-task rows capture "delivers to N" / "consumes from N" symmetric pairings. Includes the internal review caveat about re-verifying reuse entries.
7. **Risks and rollback** — risks table (ID / Risk / Severity / Mitigation) + Out of scope for this sub-task list (max 3) + two-tier rollback (cheapest lever + full) per Rule 11.14. NO "Assumptions" heading — boring decisions live in §3 Invariants/Authz clauses and §5 Effects/on-success clauses per Rule 11.13 §5. Mitigations reference AC/BR/TS IDs + tier (e.g. `Covered by AC-1 + BR-3 at Unit + Integration tiers`).
8. **Shared contract** — the canonical wire-level invariants inherited byte-for-byte across every sub-task in a split, per Rule 11.3. Wire and abstract conditions only — no framework field paths per Rule 11.3a. Parent-alone gets whatever subset applies (auth artefact + time/locale + pagination convention at minimum).

**Per-sub-task scoping when composing a sub-task's `implementation.md`:** only include units this sub-task owns (units in this sub-task's repo). §3, §4, §5 are scoped to the sub-task's repo. Cross-repo dependencies show up in Touch points as references to other sub-tasks by their sequence number (e.g. *"consumes operations from sub-task 1 (backend)"*).

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

**No Operations, Stored data changes, or User-facing surfaces sections in rollup mode** — those live per sub-task.

See `references/implementation-plan-template.md` §rollup for the full template.

### 6. Enforce the hard rules

**Rule 0 — ONE compose, ONE lint, ONE optional auto-fix (v2.3.17 — kills the halt-and-rewrite loop that was making compose take hours).**

Compose runs in **at most two passes**, never more:

1. **Pass 1 — Compose.** Read all inputs (analysis scratchpad, TL context units, parent BA files). Fill all 8 sections in ONE shot. Respect Rule 10 budgets as GUIDES (target numbers), not walls. Write the draft to memory.
2. **Pass 1 — Lint (immediately after compose, single scan).** Run every rule below ONCE against the draft. Collect ALL findings into two buckets:
   - **HALT findings** (mechanical, only these 8 rules — see Rule 0a below) → STOP everything. Report all halt findings at once. Write nothing to disk. Do NOT auto-rewrite. User fixes the input (scratchpad, TL unit, BA file) and re-runs `/dev:plan`.
   - **WARN findings** (everything else — Rules 10a/10b/11.5/11.9/11.10/11.12/11.13 that were previously halts) → collect into a `## Compose lint findings` block. Write draft to disk. Report warnings to the user in the terminal + append the block to `dev/plan-run.md` under this task's Stage 4. **User is not blocked** by warnings.
3. **Pass 2 (OPTIONAL — auto-fix only)** — if the ONLY halt findings are mechanical auto-fixes (remove a stray `## Assumptions` heading, remove a stray `## 7. Coverage` heading, remove `Deferred` status text — all string-level removals with no rewrite), apply the auto-fix, re-lint ONCE, then proceed as Pass 1. If Pass 2's lint still has HALT findings, STOP for real — never a third iteration.

**Rule 0a — The 8 mechanical halt triggers (v2.3.17). Every other rule below is a WARNING that reports but does not block.**

| # | Halt trigger | Auto-fix behavior | Why it must halt |
|---|---|---|---|
| 1 | Total character count > 60 000 | none — halt only | MC rejects the tab payload |
| 2 | `## 7. Coverage` or `**Coverage.**` heading present | remove the heading + orphan rows | Retired concept per v2.3.16 |
| 3 | `Deferred to E2E` / `Deferred` status text | remove the row / cell text | Retired concept per v2.3.16 |
| 4 | `**Assumptions.**` or `## Assumptions` heading | remove the heading + associated bullets | Retired concept per v2.3.15 |
| 5 | Pipe-table rows crammed on one physical line (`\| … \| … \| … \| \d+ \| …` pattern) | split rows at `\| \d+ \|` or `\| — \|` boundary + insert `\n` + ensure header separator row present | Unrenderable in MC — remark-gfm treats inline pipe run as regular paragraph text (this is the exact bug from the user's screenshot) |
| 6 | Unclosed code fence (odd count of ` ``` `) | none — halt only | Parser breaks; downstream content silently swallowed |
| 7 | Framework field paths in §8 Shared contract (`req.`, `res.`, `result.response`, `ctx.`, `.headers[`) | none — halt only | Rule 11.3a — §8 is wire-only |
| 8 | `# FEAT-` H1 heading (feature ID leak) | remove the heading line | Rule 4 |
| 9 (NEW v2.3.17) | Mermaid block without `language-mermaid` tag (fenced but tag missing/wrong) | insert `mermaid` after opening fence | MC's `<MermaidDiagram>` component checks `className === 'language-mermaid'`; without it, block renders as a plain code fence, no diagram |
| 10 (NEW v2.3.17) | Missing blank line before/after a table or code fence | insert `\n\n` at the boundary | remark-gfm silently DROPS blocks without blank-line surrounds — content vanishes from the render |
| 11 (NEW v2.3.26) | Solo-pipe line OR table column-count mismatch (header cells ≠ separator cells) | Transform 0 deletes solo-pipe lines unconditionally; column-count mismatch HALTS (ambiguous fix) | CommonMark parsers see `|---|---|` as an H2 setext underline for the preceding line — the pipe-header renders as a huge false heading and the section's real H2 disappears into the noise |

**Auto-fix scope (v2.3.17 clarification).** Auto-fix operations are pure string transforms applied IN the lint pass — remove a heading line, insert a newline, insert `mermaid` after ` ``` `. They do not count against Rule 0's max-one-auto-fix budget (that budget covers RE-COMPOSE cycles). Auto-fix runs deterministically on the lint scan output; if all halt triggers auto-fix cleanly, the file writes on the same pass. If any halt trigger cannot auto-fix (halt #1, #6, #7 have no auto-fix; auto-fixable ones fail on ambiguous boundaries), the compose HALTS with the byte range.

**Everything else is a WARN.** Rules 10a (required-coverage checklist), 10b (density scan — rationale starters, AC/BR outside allowed sites, paragraph-where-line, adjacent redundancy, sentence>40 words, restated tables, cross-ref narratives), 11.5 (mermaid-not-fenced, mixed bullets, missing blank lines), 11.9 (self-consistency 10 checks), 11.10 (feature-shape adapters), 11.12 (bare N/A), 11.13 (content quality + adversarial read) — all become WARNINGS reported in the `## Compose lint findings` block. The user decides whether to fix and re-run, or accept.

**Why:** the previous behavior (~30 halt triggers, each triggering a top-to-bottom recompose) produced compose runs that took hours. The overwhelming majority of rules require LLM judgment, not mechanical checks; treating them as halts guaranteed halt-and-rewrite loops. Warnings collected in one pass — the user reads a summary of 5–10 findings, decides which matter, edits the source, re-runs — is finite and productive. Halts stay only for mechanical breakage the user cannot fix by editing an input file (payload > cap, unrenderable markdown, retired-concept leaks the compose can auto-remove).

**Rule 0b — Report shape when compose emits warnings.**

Append to the terminal output + `dev/plan-run.md`:

```markdown
## Compose lint findings — <feature-id> <sub-task-repo>

<N> WARN findings (compose proceeded; user can review + fix + re-run at leisure):

- [Rule 10a §5] Missing "Session-expiry handling" one-liner in `<Domain>Panel`.
- [Rule 10b density] Sentence #47 in §5 starts with "This ensures…"; likely rationale leak.
- [Rule 11.9 §3] §3 order-of-checks step 5 refers to `body.length` but §5 has a local Submit-gate at `body.trim().length ≥ 1` — verify one doesn't defeat the other.
- ...

0 HALT findings. File written + pushed.
```

If HALT findings exist, the block instead reports:

```markdown
## Compose HALTED — <feature-id> <sub-task-repo>

<N> HALT findings. Nothing written to disk. Fix the source and re-run /dev:plan.

- [Halt 1: size > 60 000] Draft was 63 421 chars. Consider splitting the sub-task.
- [Halt 5: pipe-table run-on] Line 147: table rows crammed on one physical line.
- ...
```

**Rule 0c — Compose runs the lint pass INLINE with the compose LLM call, not as a separate subagent invocation.** Same context, same pass. No fan-out to a "verifier" subagent that adds token overhead. The compose call's system prompt includes the lint checklist; the compose emits `<lint-findings>` after the draft.

**Rule 0c.i — MANDATORY POST-COMPOSE, PRE-WRITE MECHANICAL FIX PASS (v2.3.21 — CLOSES THE "rules exist but aren't executing" BUG).**

The compose LLM's output is TREATED AS UNRELIABLE for mechanical format. Rules 0a/0d/11.5 describe the CONTRACT; the mechanical fix pass ENFORCES it. Without this step, the compose LLM sometimes emits pipe-run-on tables, unfenced mermaid, or missing blank-lines — and the "auto-fix" described in Rule 0a becomes hopeful text nobody executes.

**The fix pass is an EXPLICIT tool-call sequence, not a mental note. The `tl-feature-compose` skill MUST run this sequence between the LLM's draft emit and the `Write` call:**

1. **Capture the draft as a string in memory** — do NOT `Write` it yet.
2. **Run the deterministic transformations below IN ORDER**, applying each to the string:

   ```pseudocode
   text = compose_llm_output

   # Transform 0 (v2.3.26): strip solo-pipe noise lines
   # Pattern: a physical line containing ONLY pipes + whitespace (no cell content),
   # e.g. "|" or "|  |" or "  |  " on its own line. These are LLM artifacts that
   # (a) break table detection in remark-gfm and (b) cause the following `|---|---|`
   # separator to be interpreted as a setext H2 underline for the row above it —
   # producing the "table header renders larger than the section heading" bug in
   # every viewer that follows the CommonMark setext rule. Delete these lines
   # unconditionally; they carry no semantic content.
   text = strip_solo_pipe_lines(text)   # see reference implementation below

   # Transform 1: table row-per-line — the exact bug from user screenshots
   # Pattern: a physical line containing 2+ pipe-runs looking like `| … | | \d+ | …`
   # or `|---|---|---| \| \d+ \|` — split at row boundaries.
   text = split_table_rows(text)   # regex + newline insertion; see reference implementation below

   # Transform 2: header-separator missing
   # Pattern: pipe-header line followed by a pipe-data line, no `|---|` between them
   text = insert_header_separator(text)

   # Transform 2a (v2.3.26): table column-count integrity
   # Pattern: a `| a | b | c |` header row whose separator `|---|---|` has a
   # DIFFERENT number of columns. remark-gfm rejects this as a table and
   # falls back to setext-heading interpretation, producing the "header row
   # shows as huge heading" bug. Halt with the exact byte range — this is
   # never safe to auto-fix because the LLM's intent (which column got dropped
   # or added) is ambiguous.
   text = check_table_column_counts(text)  # halts on mismatch, per Rule 0a #11

   # Transform 3: blank line before/after every table, code fence, mermaid, heading
   text = ensure_blank_line_surrounds(text, patterns=["|", "```", "```mermaid", "##"])

   # Transform 4: mermaid fence needs language tag
   # Pattern: ``` on its own line followed by `flowchart|graph|sequenceDiagram|stateDiagram|classDiagram|…`
   text = tag_bare_mermaid_fences(text)

   # Transform 5: retired-concept string removal (auto-fixable halts from Rule 0a)
   text = strip_retired_headings(text, retired=[
       "## 7. Coverage", "**Coverage.**",
       "**Assumptions.**", "## Assumptions",
       "Deferred to E2E", "| Deferred |",
       "# FEAT-",
   ])
   ```

**Reference implementation of the solo-pipe strip (Transform 0) — the compose LLM subagent MUST apply this before Transform 1:**

```python
import re

_SOLO_PIPE = re.compile(r"^\s*\|+\s*$")

def strip_solo_pipe_lines(text: str) -> str:
    """Delete lines containing only pipes + whitespace.

    These lines produce the setext-heading-underline bug: the following
    `|---|---|---|` separator row gets misread as an H2 underline for the
    row above, and the pipe-header renders larger than the section heading.
    LLM output sometimes emits a stray `|` between a paragraph and a table
    header; strip it unconditionally.
    """
    return "\n".join(line for line in text.split("\n") if not _SOLO_PIPE.match(line))
```

**Reference implementation of the column-count integrity check (Transform 2a):**

```python
def check_table_column_counts(text: str) -> str:
    """Halt if a table's separator row has a different column count than its header.

    A `| a | b | c |` (3 cells) header followed by `|---|---|` (2 cells) is
    rendered as setext H2 by CommonMark, not as a table. Auto-fixing is not
    safe — we don't know whether to add a column to the separator or drop one
    from the header. Report the byte range and halt.
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        # A header is `| x | y | z |` — count pipes minus 1 for cell count
        if not re.match(r"^\s*\|.+\|\s*$", line):
            continue
        if i + 1 >= len(lines):
            continue
        sep = lines[i + 1]
        # A separator is `|---|---|` (or `|:---|---:|`)
        if not re.match(r"^\s*\|(\s*:?-+:?\s*\|)+\s*$", sep):
            continue
        header_cells = line.count("|") - 1
        sep_cells = sep.count("|") - 1
        if header_cells != sep_cells:
            raise HaltError(
                f"Table column mismatch at line {i+1}: "
                f"header has {header_cells} cells, separator has {sep_cells}. "
                f"Rule 0a #11 (v2.3.26). Re-compose this section."
            )
    return text
```

3. **Re-scan the transformed string** for HALT-only conditions (payload > 60 000 chars, unclosed code fence, framework field path in §8). Any HALT → report + do NOT `Write`.
4. **VERIFY by re-parsing:** attempt to parse the transformed string with the same GFM parser MC uses (or a mental equivalent — scan for any remaining `| \d+ |` run on the same line as a header separator; scan for any `| …` line where the preceding non-empty line is a `|` line but not a separator). Any remaining issue → auto-fix again OR HALT if the fix doesn't converge in ONE additional pass.
5. **ONLY NOW call `Write`** with the transformed string.
6. **AFTER `Write`:** call `Read` on the just-written file, compute SHA-256 of the read-back vs the transformed string. Match → proceed. Mismatch → HALT with `blocker: write-tool-mangled-output` — a rare filesystem or line-ending corruption case.

**Reference implementation of the pipe-run-on split (Transform 1) — the compose LLM subagent is instructed to apply this exact regex logic:**

```python
import re

def split_table_rows(text: str) -> str:
    lines = text.split("\n")
    out = []
    for line in lines:
        # Detect: line contains 2+ occurrences of "| \d+ |" cell boundaries
        # OR contains a table-separator pattern followed by " | \d+ |"
        if re.search(r"\|---.*\|.*\| \d+ \|", line) or len(re.findall(r"\| \d+ \|", line)) >= 2:
            # Attempt split at "|---|" boundary first (separator run into data row)
            if "|---" in line:
                # Split before the first data cell after the separator
                separator_match = re.search(r"(\|(?:---\|)+)(\s*)(\| .*)", line)
                if separator_match:
                    out.append(separator_match.group(1))
                    # Then split the remaining data cells
                    remaining = separator_match.group(3)
                    for row in re.split(r"(?<=\|)\s*(?=\| \d+ \|)", remaining):
                        out.append(row.strip())
                    continue
            # Otherwise split at "| \d+ |" data-row boundaries
            rows = re.split(r"(?<=\|)\s*(?=\| \d+ \|)", line)
            for row in rows:
                out.append(row.strip())
        else:
            out.append(line)
    return "\n".join(out)
```

The `tl-feature-compose` skill's execution instructions MUST include this exact function (or an equivalent it can execute) — this is not a suggestion, it's a mandatory pre-`Write` step.

**Failure to run Rule 0c.i's mechanical fix pass makes v2.3.17.1 Rule 0a/0d/11.5 all cosmetic documentation. Do not skip.**

**Rule 0d — MC rendering contract (v2.3.17 — MUST be included verbatim in the compose LLM's system prompt).**

MC's Task detail view renders `implementationDetails` with `react-markdown v9 + remark-gfm v4 + mermaid v11.6`. Confirmed by reading `BuildWithAIPortal_UI/package.json` and `src/components/Chat/BaDiagnosisPhase.tsx` (mermaid intercept on `className === 'language-mermaid'`). The compose MUST emit markdown that this exact toolchain renders correctly. Non-negotiable format rules:

**§1 Build sequence — per-step H3 sections, NOT a pipe table (v2.3.26):**
- Emit each step as its own `### Step N — <title>` heading, with three bullets: `**Files** — …`, `**Units** — …`, `**Satisfies** — …`, followed by a one-line directive.
- Do NOT emit a `| # | Step | Files | Units | Satisfies |` table. Long `Satisfies` cells wrap, the separator row gets misread as a setext H2 underline, and the pipe-header renders larger than the section H2 — the exact bug in the user screenshot.
- HELD steps: add `**Status:** [HELD · waiting on OQ-<id>]` under the H3 and skip the three bullets.

**Other tables (§2 Impacted components, §b Sub-tasks, etc — remark-gfm strict):**
- Every row on its OWN physical line. Newline (`\n`) between EVERY `|`-starting row.
- Header separator (`|---|---|---|`) on its OWN line between header and body.
- **Header pipe-count MUST equal separator pipe-count.** If they differ, remark-gfm rejects the table and the CommonMark parser reinterprets the separator as an H2 setext underline for the header row — the header shows huge and bold with visible pipes. Rule 0a #11 halts on this.
- Blank line before AND after the table.
- No solo-`|` line before the header (Rule 0a #11 auto-strips these; do not emit them in the first place).
- WRONG — pipe-run-on (renders as inline pipe text, unreadable):
  ```
  | Dimension | Impact | | Surfaces | ... | | Operations | ... |
  ```
- WRONG — solo-`|` before header (renders header as huge setext H2 heading):
  ```
  paragraph text ending here.

  |

  | Dimension | Impact |
  |---|---|
  ```
- RIGHT (renders as a proper table):
  ```

  | Dimension | Impact |
  |---|---|
  | Surfaces | … |
  | Operations | … |

  ```

**Mermaid diagrams:**
- Must be a fenced code block with EXACTLY the language tag `mermaid` (react-markdown checks `className === 'language-mermaid'`).
- Opening fence on its own line: ` ```mermaid`
- Closing fence on its own line: ` ``` `
- Blank line before opening fence and after closing fence.
- Node labels with special characters (numbers with dot, spaces, colons) MUST be quoted: `S1["1. Model"]` not `S1[1. Model]`.
- WRONG: mermaid diagram inline without fence, or with a language tag like `mermaid-flowchart` (won't match; falls back to code block; no diagram).
- RIGHT:
  ```

  ```mermaid
  flowchart LR
      S1["1. Model"] --> S2["2. Handler"]
  ```

  ```

**Fenced code blocks:**
- Triple-backtick fences ` ``` ` for JSON, curl, bash, etc.
- Language hint (`json`, `bash`, `mermaid`, etc.) directly after the opening fence, no space.
- Balanced — every opening ` ``` ` has a matching closing ` ``` ` on its own line.

**Headings:**
- Use `##` (level 2) for numbered sections (§1–§8).
- Use `###` (level 3) for sub-headings inside a section (e.g. per-operation heading in §3, per-surface heading in §5).
- Do NOT use `#` (level 1) — MC's own tab title is level 1; using `#` in body content creates two H1s and breaks visual hierarchy.

**Blank lines:**
- Before AND after every table, code fence, heading, mermaid block.
- remark-gfm silently DROPS tables/blocks that don't have the blank-line surrounds — the content just disappears from the render.

**Bullets:**
- Use `-` consistently. Do NOT mix `-` and `*`.
- Sub-bullets indented with 2 spaces (react-markdown handles nested).

**HTML:**
- Allowed via `rehype-raw` but sanitized via `rehype-sanitize`. Prefer plain markdown over HTML. Do NOT use `<br/>` for line breaks inside table cells — use `<br />` (with the space) if you absolutely need a line break, but prefer restructuring so cells stay one line.

**The pre-write mechanical scan (Rule 11.5) applies these as auto-fix-then-halt:**
1. Detect any run of two or more `|`-cells on the same physical line where each cell is separated only by ` | ` (space-pipe-space) without a newline between rows → **auto-fix**: split on the row-boundary heuristic `| \d+ |` or `| — |` at cell boundary, insert `\n` between rows, re-emit table.
2. If auto-fix succeeds (produces a valid GFM table on the re-parse), continue.
3. If auto-fix cannot resolve (ambiguous row boundaries), HALT per Rule 0a #5 with the exact byte range.
4. Same one-shot auto-fix approach for missing header separator, missing blank line before/after table, mermaid without language tag.

**How this fits into Rule 0's pass structure:** the MC rendering contract lives in the compose LLM's system prompt so the FIRST-PASS output should already be correct. The mechanical scan is a safety net that catches the LLM slipping. Auto-fixes are string-only transforms, not rewrites — they don't count against Rule 0's max-one-auto-fix budget (they apply IN the lint pass, not as a re-compose).

---

Rules 1–15 below are the QUALITY BAR the lint checks against. Under Rule 0, only the 8 mechanical rules in Rule 0a produce HALTS; the rest of Rules 10a/10b/11.5/11.9/11.10/11.12/11.13 produce WARNINGS. Sections describing rule severity ("halt", "compose halts", "REFUSE") in the text below should be read as "WARN" unless the rule is in the 8-halt list. Historical prose is retained for context but Rule 0 governs execution behavior.

**Rule 1 — File paths ARE required in §1 (Files column), §4 (Fields written source), §5 (component paths), §6 (Reuse rows) — but NEVER in §9 (Shared contract) (v2.3.11 revision).** Earlier drafts of this rule forbade file paths anywhere. That was wrong for a build spec — the developer needs to know WHERE the code lands. Now:

- **REQUIRED in §1 Build sequence "Files" column**: each step names the concrete new/modified path (`New: src/models/Comment.js`, `Modified: src/routes/router.js`).
- **REQUIRED in §4 Stored data changes "Source of value" column and declaration-hazard notes**: name the reference file (`use src/models/LeaveRequest.js as the reference for constraint declaration`).
- **REQUIRED in §5 User-facing surfaces**: name component/screen paths so the developer knows the target file.
- **REQUIRED in §6 Touch points**: the Path column names each Reuse/New target explicitly.
- **NEVER in §8 Shared contract**: §9 is the wire-level cross-stack invariant. File paths are stack-specific extractions that belong in the local TL unit files, not §9. Rule 11.3a's regex halt catches this.

**Rule 2 — Framework and library NAMES may appear in impact matrix and hazards, but never as versions or as code idioms (v2.3.11 revision).** Earlier drafts forbade every framework mention. That was wrong — the impact matrix legitimately reports "Jest + Testing Library green at plan time: N suites / M tests" as a fact about the repo, and §4 declaration hazards must name the constraint-syntax gotcha (`use required: true, not require:` in a Mongoose-style repo). What IS still forbidden:

- **Version numbers next to a technology name** (`React 18`, `Node 20`, `Python 3.11`) — the version is deployment detail, not plan detail.
- **Framework-idiomatic code snippets in place of prose** — no `new mongoose.Schema({body: {type: String, required: true}})` code block that dictates syntax; describe the constraint in prose ("declare `body` as required with `required: true`, NOT the near-miss `require:` which is silently ignored in this repo").
- **Framework field paths in §8 Shared contract** — Rule 11.3a's absolute forbid.

What IS allowed: `Jest`, `Mongoose`, `Express`, `React`, `Playwright` etc. named as a fact ("existing suite is Jest + Testing Library"), or as the target of a hazard ("Mongoose ignores `require:` — use `required: true`"). This matches the shape the reader needs.

**Rule 3 — Implementation directives ONLY. No duplication of other tabs. No rationale/theory prose (v2.3.14 — sharpened).** This document contains build-from directives — the WHAT/WHERE/HOW-SHAPE a developer needs to produce the code. It does NOT contain the WHY (business context lives in Description tab), the RATIONALE (BR/AC live in their tabs), the ASSUMPTIONS that belong to the parent (those live on parent's tabs), or the TEST REASONING (that's the test code itself, not the plan).

**The one-question test — apply to every line before writing it:** *"Is this line something the developer TYPES INTO A FILE, or something the developer READS TO UNDERSTAND?"*

- **TYPES INTO A FILE** (KEEP): file paths, component names, prop/state/field names + types, request/response shapes, refusal codes + messages, control behaviour, endpoint contracts, index declarations, order-of-checks steps, rollback commands. These directly translate to code.
- **READS TO UNDERSTAND** (CUT — lives in another tab): the business goal, the user problem being solved, why an AC exists, why a BR is enforced, why an assumption holds, what the reasoning behind a design is, why a test asserts what it asserts. These are context, not code.

**Banned content patterns — halts by category:**

**§5 User-facing surfaces — banned prose forms (compose halts on any of these):**
- Business-rule restatements: `"This is presentation only. The server enforces both rules, and a race that slips through returns 403 or 409, handled per §3."` — BR rationale lives in `business-rules.md`; the plan only NAMES what the surface shows/does.
- AC restatements: `"When the user submits a comment older than 24h, they see the message per AC-3."` — AC lives in `acceptance-criteria.md`; the plan's refusal-placement table names the code + placement, not the AC.
- Theory/rationale sentences starting with: `"This ensures…"`, `"This means…"`, `"This handles…"`, `"The reason for this is…"`, `"This is because…"`, `"So that…"`. If a line explains WHY the code exists rather than what it is, it's rationale — cut.
- Behaviour re-narration: `"On mount, the panel fetches. During the fetch, a spinner is shown. When the fetch completes, the panel renders. When the fetch fails, an error is shown."` — this narrates what the tables and one-liners already list. One line per lifecycle event via table row, not a paragraph re-narrating.
- Race/concurrency narrative: `"A race that slips through returns 403 or 409"` — the refusal-placement table already lists 403 and 409. The narrative adds nothing the developer types into code.

**§7 Risks and rollback — banned patterns (compose halts):**
- **A dedicated `**Assumptions.**` (or `## Assumptions`) heading anywhere in the plan (v2.3.15).** Boring decisions live IN CONTEXT at the section where the code implements them — Rule 11.13 §5. §8 carries Risks + Out of scope + Rollback ONLY.
- Restating parent's assumptions from `feature.md` / `nfrs.md` / `dependencies.md`. Parent assumptions live on the parent's Description tab and Dependencies tab.
- Restating parent's out-of-scope from `feature.md`. Only sub-task-specific out-of-scope items appear here (things this sub-task WON'T do that the reader might expect it to — max 3 bullets).
- Business rationale wrappers around boring decisions (`— expected count ≤ 100 per task`, `— internal audience only`, `— audit-trail immutability`). These re-explain parent scope.
- Future-consideration narratives (`revisit if that changes`, `deferred to v2`, `future decision`). Parent's Dependencies tab handles v2 levers.

**§2 Impacted components — banned in row cells (compose halts):**
- Business rationale in the impact cell. Each cell states the CONCRETE impact (files changed, artefact added, `N/A — <specific reason>`) — never the WHY of that impact.

**§4 Stored data changes — banned:**
- Business-rule enforcement narrative: `"is_removed=false enforces BR-1 by making removed rows invisible to the uniqueness check"`. The BR link belongs in §1 Build sequence Satisfies column (the canonical coverage owner per v2.3.16). §4 states the shape (`partial unique index on (date) where is_removed=false`) without the WHY.

**Section-mode reminders:**
- 9 sections §1–§9 for `implementation`; 3 sections for `rollup`; 6 sections for `description`.
- No Business Goal, no AC list, no NFR list, no Business Rule list, no Test Scenarios list, no Dependencies list, no Open Questions list, no Prerequisites section (cross-feature waits live on Dependencies tab; code-reuse targets live in Touch points).
- If a fact belongs in another tab, do not restate it here — even briefly.
- **In `description` mode**, the workflow diagram belongs on the parent's Description tab (BA-owned) — do not include a mermaid diagram in a sub-task Description.

**The mental model:** implementation.md is a build script for a developer / coding agent. The dev-agent should be able to produce working code from this file plus the local TL context units (endpoint/entity/page files) without ever opening the BA files. Everything IN this file directly enters code; everything NOT in this file is either in a TL unit or on a BA tab. If a line's purpose is to make the reader UNDERSTAND rather than TYPE, that line is duplication and cuts.

**Rule 4 — No feature identity in visible content.** Feature id, initiative, slug, and provenance live in the frontmatter and MC task metadata. Never a `# FEAT-…` H1. Never a "Provenance:" line. Never a reference to `feature.md`, `workflow.md`, `acceptance-criteria.md`, `ba/*`, `context/*`, or any scope-review filename. The Description and Dependencies tabs (BA-owned) carry any provenance the reader needs.

**Rule 5 — Existing schema fields the feature does not write are named in one line, not tabled.** If the feature writes four fields on an existing data object, the §4 Stored data changes "Fields written" table contains those four — and only those four. Fields not written are named on a single "Never touched: `<field-a>`, `<field-b>`, `<field-c>`" line. That is the whole allowance.

**Rule 6 — Response codes and messages are discriminated explicitly.** If an endpoint returns three distinct `409` messages, the Refusals table has three rows. Never collapse a code's variants into one row. Similarly for `400` variants.

**Rule 7 — No client-narrative, no provenance callouts, no author commentary.** Forbidden: *"the client chose transparency knowingly"*, *"this document being complete is not consent"*, *"a module HR uses daily"*, `⚠ PROVENANCE — PLANNED, NOT BUILD-READY` blockquotes, *"acceptance criteria are authored as bullets without ids"*, *"SIMULATED response round"* preambles. The Description and Dependencies tabs carry any client-facing note.

**Rule 8 — No aspirational text.** No *"consider"*, *"might"*, *"could"*, *"we should think about"*. Either the decision is made and stated, or the phase is marked `[HELD · waiting on OQ-<id>]`.

**Rule 9 — No secrets.** Env var **names** only if referenced at all — never values or credentials, even if the repo scan surfaced them.

**Rule 10 — Size budget — HARD per-section, planned upfront, measured in CHARACTERS not bytes, DENSE NOT VERBOSE (v2.3.12 — v2.3.13 tightened budgets + required-coverage discipline).**

**The two orthogonal disciplines — length AND density.**

- **Length discipline** — each section has a HARD upper-bound character count. Compose within the bound on FIRST write; never a trim-after pass (that flattens section proportions and reads as uneven).
- **Density discipline** — inside the bound, every sentence carries a DISTINCT best-practice concern from the required-coverage checklist for its section. No two sentences say the same thing at different volume. No paragraph where a one-line entry with a bold prefix would work. Prose is the WORST format — prefer table row / bulleted line with bold role / signature-style declaration over paragraph text.

**Measure characters, not bytes.** MC's `implementationDetails` field caps at 60 000 CHARACTERS. Every size gate below is a **character count** (Python `len(s)`, JS `[...s].length` counting code points — never `Buffer.byteLength(s)`). Em-dashes and multi-byte glyphs count as ONE character each. A byte-count check produces false-positive overflows on em-dash-dense docs; the 66 291-char frontend doc that forced a rewrite pass was a byte-vs-char confusion combined with too-permissive per-section budgets.

**`implementation` mode — per-section budget (v2.3.13 — tightened; density mandatory):**

| Section | Target | Max | Density mandate |
|---|---|---|---|
| §1 Build sequence | 1 400 | 2 200 | Intro para 3 lines max + step table (rows 1 line each, no cell wrapping) + mermaid step-graph. No commentary between step and mermaid. |
| §2 Impacted components | 1 000 | 1 800 | ONE row per dimension. Each row is ONE sentence naming the concrete impact + the file/module. `N/A — <specific reason>` per Rule 11.12; bare N/A halts. No sub-bullets under matrix rows. |
| §3 Operations exposed and consumed | 4 500 | 9 000 | Per operation: inputs table + payload JSON + order-of-checks table + refusals table + one-line invariants. NO narrative paragraphs describing what tables already say. Consumer §3 uses the SAME tables byte-for-byte (Rule 11.6); it does not paraphrase. If §3 grows past max, sub-task owns too many operations — split. |
| §4 Stored data changes | 900 | 1 800 | Fields-written table + one-line "Never touched" + one-line index declaration + one-line declaration hazards. Migration block per Rule 11.10a only when store has live rows. `None.` closes §4 at ~10 chars for sub-tasks without persistence. |
| §5 User-facing surfaces | 3 500 | 6 000 | Where-it-lives 3 lines + hierarchy tree + operation-wiring table + per-surface heading × (props table / state table / effects one line / rendered-states one line / control table / on-success one line / on-refusal one line / refusal-placement table) + service-layer one paragraph max 6 lines. NO paragraphs describing what tables already list. `None.` closes §5 for backend/job-only sub-tasks. |
| §6 Touch points | 700 | 1 200 | Reuse + New + Cross-sub-task table only. One row per Reuse/New; multi-file modules consolidate into ONE row with comma-separated paths. |
| §7 Risks and rollback | 700 | 1 400 | Risks table max 5 rows + Out of scope max 3 bullets + two-tier rollback per Rule 11.14 (cheapest lever one line + full one bullet list). NO Assumptions heading. Mitigations reference AC/BR/TS ID + tier, never a specific test file. |
| §8 Shared contract | 700 | 1 200 | Fixed shape from Rule 11.3; every sub-task in a split inherits VERBATIM. No expansion. |
| **Total (soft target)** | **~13 400** | **~24 400** | Leaves ~35 KB headroom under 60 000-char refuse line for Rule 11.10 feature-shape adapter blocks and per-repo dimensions. |

**Warn: 55 000 chars. HALT: 60 000 chars (Rule 0a #1).** Per-section maximums in the table above are GUIDES for the compose, not halts. Over-max on a single section triggers a WARN with the suggestion to apply the section's drop rule; it does not halt the compose. Only total-file > 60 000 chars halts (that's MC's actual cap). Reverted from the earlier v2.3.13 tight 40k warn line because that produced compose-halt-and-rewrite loops that hurt more than they helped.

**Rule 10a — Required-coverage checklist per section (v2.3.13). Each concern is covered in ONE dense line or table row, never a paragraph. Missing coverage → halt (a concern skipped is a review debt); over-length coverage → halt (a paragraph where a line would do is verbose).**

Every implementation.md must cover EVERY concern in the checklist for the sections that apply to its capabilities. Concerns not applicable to the sub-task (e.g. accessibility for a queue worker) are named as `N/A — <reason>` on their own line — not omitted silently.

**§1 Build sequence — required coverage:**
- Ordered steps with WHERE (Files column) and WHAT (Step column) and WHY it satisfies (Satisfies column: parent AC/BR/TS IDs by reference — §7 is canonical)
- Mermaid step-graph showing the dependency edges
- Any `[HELD · waiting on OQ-<id>]` phase called out inline

**§2 Impacted components — required coverage (each ONE line):**
Surfaces · Operations · Stored data · Authz · Integrations · Background jobs · Notifications · Observability · Existing tests · Docs · Flags · Analytics (per-repo dimensions added by shape: Screens / Accessibility / Migration / Message contract when applicable).

**§3 Operations exposed and consumed — required coverage PER OPERATION (all as tables/payloads, no prose):**
- Method + path + unit ID heading
- Auth boundary (which middleware/guard is mounted; ONE line)
- Inputs table (name / location / type / required / constraint — one row per input)
- Success payload example + specific response code
- Order-of-checks table (each check + its failure code — one row per check, walks EVERY input state per Rule 11.13 §1)
- Refusals table (one row per DISTINCT message per Rule 6 — never collapse variants)
- Invariants line (idempotency / partial-write / side-effect / ordering — ONE sentence per invariant, max 4 sentences)

**§4 Stored data changes — required coverage:**
- Store name + kind (table / collection / KV / cache / file store) + new-or-modified
- Fields-written table (field / type / source of value — one row per field written)
- "Never touched" line (comma-separated field list)
- Index declaration line (which query it serves)
- Declaration-hazard line (repo-specific gotcha, e.g. attribute-naming pitfall — ONE line)
- Migration block per Rule 11.10a IF store has live rows (else omit)

**§5 User-facing surfaces — required coverage PER SURFACE (each concern ONE line or ONE table row, never a paragraph):**
- Where it lives (route path or CLI command + host file + section-in-page vs full page)
- Component hierarchy (ASCII tree if > 2 nested components; single-component skips this)
- Operation-wiring table (surface / trigger / calls — one row per trigger)
- **Props table** (prop / type / produced by — one row per prop)
- **State table** (state / type / purpose — one row per state field)
- **Effects line** (lifecycle triggers + refetch semantics — ONE line)
- **Rendered states line** (loading / empty / populated / refusal-variants — ONE line naming each state's UI)
- **Controls table** (control / behaviour — one row per control including validation + enablement + on-submit)
- **On success** (ONE line: what surface + what surrounding context does)
- **On refusal** (ONE line: inline / toast / banner + placement rule)
- **Refusal-placement table** (code / placement / additional action — one row per code)
- **Accessibility line** (focus trap / restore / aria-live / keyboard nav — ONE line; `N/A — <reason>` if surface is non-interactive)
- **Local-check vs server-check line** (which validations run locally, which are server-only, WHY the local check doesn't defeat server reachability per Rule 11.9 §3 — ONE line)
- **Session-expiry handling line** (once at service layer, not per call — ONE line)
- **Service/adapter layer paragraph** (max 6 lines: names the wrapper for each call, unwrap responsibility, success-vs-refusal branch condition per Rule 11.13 §4, global 401 handling, copy-from-sibling hazard if any)

**§6 Touch points — required coverage:**
- Reuse rows (one per module — role + path)
- New rows (one per module — role + path)
- Cross-sub-task rows (symmetric pair per Rule 11.8 — Delivers / Consumes)
- Cross-sub-task E2E ownership rows for cross-layer coverage (`E2E for AC-M/BR-K owned by sub-task N (<repo>) — <test file path>`)
- Reviewer note (one line — Reuse rows should be re-verified against context graph)

**§7 Risks and rollback — required coverage (v2.3.15 — Assumptions section removed; v2.3.16 — mitigations reference AC/BR/TS + tier, not test files):**
- Risks table (max 5 rows — R-N / Risk / Severity / Mitigation-cites-AC-BR-TS-ID + applicable tier from `qa/quality-gates.md`)
- Out of scope for this sub-task (max 3 bullets — each names a specific implementation the sub-task does NOT deliver, one line: `No edit operation — no PUT/PATCH route registered; UI shows no edit affordance`. Never restate parent's out-of-scope; never a rationale wrapper.)
- Rollback — cheapest lever (ONE line naming the §1 step it undoes)
- Rollback — full (bullet list per Rule 11.14 — every §1 step artefact either reverted or explicitly justified as harmless)

Boring decisions (no pagination / no rate limit / no permission model / no optimistic updates / no polling) do NOT appear in §7. They live IN CONTEXT at their code-implementation site per Rule 11.13 §5 — §3 Invariants or Authz clauses, §5 Effects or on-success clauses, §5 operation-wiring row. §7 has NO Assumptions heading.

**§8 Shared contract — required coverage:**
- Fixed table shape from Rule 11.3 (auth artefact / one-record shape / list shape / success-vs-refusal condition / code+message location / global 401 / identifiers / time+locale / pagination convention).
- Every row wire-level per Rule 11.3a — no framework field paths.

**Rule 10b — Density + anti-rationale enforcement in the pre-write scan (v2.3.13, expanded v2.3.14).** Alongside Rule 11.5's mechanical markdown check, the pre-write scan runs these heuristics:

- **Paragraph-where-line-should-be.** Any prose paragraph inside §5 (per-surface) that is > 3 lines and doesn't sit under an explicit heading that permits paragraph content ("Service/adapter layer paragraph") → halt naming the section and the offending paragraph. The reader gets a table row or a bold-prefix bullet; not a paragraph.
- **Paragraph inside §2, §4, §6.** These sections carry TABLES only, plus one-liners between tables when structurally needed. Any paragraph over 2 lines in these sections → halt.
- **Restated table content.** After every table, the paragraph following is scanned for phrases that just re-describe what the table already listed ("the table above shows the fields written…"). Any restatement paragraph → halt with the phrase quoted.
- **Adjacent-sentence redundancy.** Two consecutive sentences whose token overlap > 60% → halt naming both. This catches "the panel shows loading. The loading state is a spinner. The spinner appears during the first fetch. During the first fetch the panel shows loading." — a real anti-pattern in 66k drafts.
- **Sentence length ceiling.** Any single sentence > 40 words → halt asking for a rewrite as ≤ 40-word sentences. Compound sentences hide multiple concerns; splitting reveals them.
- **Rationale-sentence starters (v2.3.14).** Any sentence starting with `This ensures`, `This means`, `This handles`, `The reason for this is`, `This is because`, `So that`, `In order to`, `This prevents`, `This guarantees`, `This maintains`, `This preserves`, `This allows`, `This makes it possible` → halt with the sentence quoted. These sentences explain WHY code exists rather than describing WHAT to build — per Rule 3, WHY lives in another tab. If a sentence starting with `This ensures…` says something the plan actually needs, the FACT it references is what stays (as a directive), not the rationale wrapper.
- **AC/BR mention outside §1 Satisfies column and §7 mitigation cells (v2.3.14, updated v2.3.16).** Any `AC-\d+`, `BR-\d+`, `TS-\d+`, `NFR-\d+` reference OUTSIDE `§1 Satisfies column` or `§7 mitigation Mitigation cell` → halt. Canonical mention sites in the plan are exactly two: §1 Satisfies column (per Rule 11.11, plan-time canonical coverage) and §7 mitigation cells (each cites the AC/BR/TS ID + applicable tier). Any §5 prose or §7 risk-description prose that mentions `BR-3` inline → halt. Direct AC/BR/TS mention in narrative prose is rationale leakage.
- **"Handled per §X" / "See §X" narrative connectors (v2.3.14).** Any prose sentence whose primary purpose is to point the reader at another section (e.g. `"…handled per §3."` `"…as described in §7."`) → halt. Cross-references belong in table Cross-ref columns, not narrative prose. If a reader NEEDS the cross-ref inline, the table cell for that row carries it — the surrounding prose does not narrate the pointer.
- **`**Assumptions.**` or `## Assumptions` heading anywhere (v2.3.15).** Halts naming the location. Boring decisions live IN CONTEXT at their code-implementation site per Rule 11.13 §5 — not as a collected "assumptions" list. Common misplacements the scan catches: `**Assumptions.** <bullets>` at §7 tail; `## Assumptions` inside any section; `Assumptions:` label at feature root.
- **`## 7. Coverage` heading anywhere (v2.3.16).** Halts naming the location. Coverage is not a plan-time table — plan-time intent lives in §1 Satisfies column, build-time evidence in `dev/acceptance-map.md`. Any `## 7. Coverage`, `## Coverage`, or `**Coverage.**` heading in an implementation.md → halt.
- **`Deferred to E2E` or `Deferred` status text anywhere (v2.3.16).** Halts naming the line. E2E is a covered TIER (declared in `qa/quality-gates.md`, owned by a specific sub-task's §1), never a deferral status.

**Interaction with Rule 11.4 (plan not code):** §5 service-layer paragraph max 6 lines includes prose only; code idioms remain forbidden per Rule 11.4. If 6 lines of prose can't cover the service layer's contract, the sub-task is describing more than one service layer.

**Interaction with Rule 11.13 (content quality):** budgets exist so the reader can scan; substantive-and-dense wins over both terse-and-empty and verbose-and-repeating. If a row would need padding with generic language to hit target, it's fine BELOW target — targets are ceilings, not floors. Required-coverage checklist is a floor on COVERAGE (every concern named), never a floor on WORD COUNT.

**`rollup` mode:** target 2 000–5 000 chars (short by design — detail lives per sub-task). Warn at 20 000 chars. If a rollup exceeds 20 000, detail belonging on sub-tasks is being duplicated — check for that before continuing.

**`description` mode (v2.3.4):** unchanged. Total target ~1 400 chars, max ~2 000 chars, absolute refuse-line 3 000 chars. See §"Per-section character budget" in the description mode spec above.

**Rule 11 — No invention.** Every endpoint contract, every DB field, every UI surface traces to the context graph or the feature files. When silent, mark the affected step `[HELD · waiting on OQ-<id>]` and name the gap. Do not guess.

**Rule 11.3 — `§8 Shared contract` — feature-wide invariants inherited verbatim (v2.3.9 format fix; renamed and moved to end in v2.3.11).** The frame is §1 through §9 — 9 sections total, plan-only. `§8 Shared contract` sits AT THE END so the plan opens with buildable work (§1 Build sequence) and closes with the reference contract the reader looks up on demand. **Every sub-task in a split feature INHERITS the same `§9` VERBATIM** — composed once at the parent level, copied byte-for-byte into every sub-task's implementation.md. This is what makes "same probably means the same" become "same by construction."

`§8 Shared contract` contents (fixed shape; all mandatory when the feature is split; parent-alone gets whatever subset applies). Every row describes the WIRE / CONTRACT / CONVENTION at the interface — never a framework field path or code extraction (see Rule 11.3a below):

- **How the caller is identified.** The credential the wire carries (bearer token, cookie, signed header, mTLS cert, session cookie, service-account key), where the caller reads it from (session store, keychain, env var, secret manager), and what identity the receiver EXPOSES to its own code — described as the abstract identity (the identity of the calling user / calling service), not the exact server-side accessor.

  **v2.3.24 — this row is FILLED VERBATIM from the endpoint units' `## Auth` structured fields, NEVER paraphrased or invented.** Procedure:
  1. For every endpoint referenced in this sub-task's §3 Operations (whether owned or consumed), read the endpoint unit file's `## Auth` section from the TL code-context tree.
  2. If ANY endpoint's `## Auth` is free-prose (like `"Requires a valid JWT"`) instead of the structured fields defined in `tl-code-map/references/code-context-templates.md` (Token type / Verified by / Client obtains via / Header format / Server extracts / Failure responses / Server prerequisites) → **HALT** the compose with `blocker: endpoint-auth-not-structured` naming which endpoint unit needs re-mapping. The compose does NOT invent an auth pattern from thin air.
  3. If every referenced endpoint has structured `## Auth`, VERIFY they all use the SAME `Token type` + `Client obtains via` (a sub-task can't sensibly consume two different auth mechanisms in one shared contract). If they differ → HALT with `blocker: auth-pattern-inconsistent` naming which endpoints diverge.
  4. Compose §8's "How the caller is identified" row by copying VERBATIM from the endpoint unit's `## Auth`:
     - The `Token type` string
     - The `Client obtains via` code snippet (exact — this is what the frontend must call)
     - The `Header format` string
     - The `Server extracts from token` list
  5. Also compose §8's "Global session-expiry behaviour" row from the endpoint unit's `## Auth` `Failure responses` list — pick the branch that covers expiry/invalid-token.
  6. Also compose §8's server-prerequisite awareness — if the endpoint's `## Auth` `Server prerequisites` lists env vars like `FIREBASE_SERVICE_ACCOUNT`, those flow into `§2 Impacted components` "Integrations" row as external config the deploy must set.

  **The frontend implementation.md §5 service layer then inherits the exact `Client obtains via` code snippet from §8 verbatim.** No generic Bearer flow. No `localStorage.getItem('jwtToken')` unless the endpoint's `## Auth` `Client obtains via` explicitly says so.
- **Shape of one record.** How a single record travels on the wire — bare object vs wrapped, id encoding, whether nulls are omitted or explicit.
- **Shape of a list (or collection).** How a collection travels on the wire — array-under-key vs bare array, empty representation, envelope key name, whether pagination fields ride here.
- **How a caller knows an operation failed.** The abstract distinction between success and refusal at the wire — success shape ≠ refusal shape / discriminated union tag / status field / etc. Named as the CONDITION the caller checks, not the code path in a specific framework's helper.
- **Where the code and message are read from a refusal.** The abstract path — "status is at the top level of the refusal object; the human-readable message is nested one below" — the specific field names, not the framework accessor.
- **Global session-expiry behaviour.** What every operation does on expired credentials — one canonical answer applied everywhere at the interface layer.
- **Common identifiers.** Id format used across the feature — opaque string / UUID / ULID / integer / composite — length and case rules if relevant.
- **Time and locale.** Wire time format (UTC ISO-8601 / epoch millis / etc.), timezone assumptions, locale for user-visible text.
- **Pagination convention (feature-wide).** If ANY list operation in this feature paginates, name the convention (cursor with named field / offset+limit / page+size). Even if THIS operation doesn't paginate, record the feature-wide "no pagination in v1 — accepted assumption" here.

When compose runs, `§9` is composed once from `shared-context/system-landscape.md` + parent BA files + resolved plan-blockers. The exact bytes of that `§9` are then copied into every sub-task's implementation.md. If a sub-task's `§9` disagrees byte-for-byte with the canonical `§9` → Rule 11.9 §10 halts.

**Rule 11.3a — `§9` states the WIRE contract, not the framework extraction (v2.3.11).** The line between "belongs in `§9` of the pushed plan" and "belongs in the local TL context unit only" is:

- **In `§9` (portable, stack-agnostic):** what the WIRE carries and what the CALLER conceptually checks. `Authorization: Bearer <token>`. `{ "items": [...] }`. `status` at top level of refusal; `message` one below. Caller knows it failed when the request helper returns rather than throws. Ids are opaque 24-hex strings.
- **NOT in `§9` — kept in the local TL unit files only:** framework-specific accessor paths (`req.user.id`, `result.response !== undefined`, `result.response.data.message`, `req.headers.authorization`), specific helper library names, code-level property paths that only make sense inside one stack's runtime. Those are extraction details the developer looks up in the TL unit file (endpoint file / page file) at build time — they're not part of the cross-repo/cross-stack contract the reader needs at plan time.

The test: **could a Go backend developer, a Node backend developer, and a Swift mobile developer each build against this same `§9` and produce interoperable code?** If yes, the wording is right. If one of them would misread it because it names a JS/Node-specific field path, rewrite the line to describe the wire and the condition, not the extraction.

Compose halts if `§9` contains: any regex hit on `req.`, `res.`, `result.response`, `ctx.`, `.headers[`, or any bracketed property path that looks like a runtime accessor. On halt, the compose reports which line + the framework-scent phrase + the abstract rewrite it should be.

**Rule 11.4 — implementation.md is a PLAN, not a code file (v2.3.7).** Every claim in this document describes something a developer will build; **the actual code goes into the repo at `/dev:build` time, via `dev-stack-adaptive-implementation`, not into this file.**

- **Allowed in implementation.md:**
  - **File paths** — "Create `src/models/Comment.js`" — WHERE the code lives
  - **Named exports / handlers / components** — "`comment.js` exports three handlers: `createComment`, `listComments`, `deleteComment`" — the SHAPE of the public surface
  - **API wire-format examples** — JSON request bodies and response bodies. These are CONTRACT specs (part of the plan), not code.
  - **Signatures and props** — "CommentsPanel props: `taskId: string`. State: `comments`, `loading`, `error`" — WHAT the interface is
  - **Integration points** — "Add one import + one JSX section entry to `src/pages/TaskDetail.jsx` — mount CommentsPanel between the description section and the activity log, pass `taskId` prop"
  - **Invariants and hazards** — "Use `required: true`, NOT the near-miss `require:` which is silently ignored" — WHAT to avoid
  - **Data shape tables** — request body fields, response fields, refusal codes
  - **Order-of-operations tables** — "Step 1: validate session; Step 2: validate body; …"

- **NOT allowed in implementation.md:**
  - Actual code snippets showing implementation. NO `import { X } from Y`, NO function definitions, NO JSX blocks with actual attributes, NO SQL statements, NO shell script bodies. The code is what dev-stack-adaptive-implementation writes at `/dev:build` time based on this plan.
  - Framework-specific idioms in code form (e.g. actual JSX, `mongoose.Schema({...})` blocks). Describe the shape in prose or tables; don't write the code.
  - Example: describe the service layer's shape as **"`src/service/commentApi.js` exports three named calls: `create(taskId, body)` → POST to EP-CMT-01; `list(taskId)` → GET to EP-CMT-02; `remove(commentId)` → DELETE to EP-CMT-03. Each call wraps the shared request helper (`commonReq.js`), passing method + path + body + a headers object containing `Authorization: Bearer <session token from local session store>`. Response normalisation: rejections carry `{status, message}` one level below the successful response shape — service layer reads at that level, callers read the normalised shape only."** — NOT `import { commonReq } from './commonReq'; export const commentApi = { create: (taskId, body) => commonReq('POST', ...) }`.

Same discipline in both directions: backend §4 didn't paste `new mongoose.Schema({body: {type: String, required: true}})` — it said "declare with `required: true` (not `require:`)". Frontend §5 shouldn't paste the JSX either.

**Rule 11.5 — Markdown rendering discipline for MC's react-markdown + remark-gfm stack (v2.3.5, expanded v2.3.17 with auto-fix + mermaid + blank-line halts).**

**Confirmed MC toolchain:** `react-markdown v9` + `remark-gfm v4` + `mermaid v11.6` + `rehype-highlight` + `rehype-raw` + `rehype-sanitize`. See Rule 0d for the full rendering contract that MUST be in the compose LLM's system prompt.

**Under Rule 0, these mechanical scans run in the lint pass. Auto-fixable ones apply the fix inline; unfixable halts stop the compose.**

| Check | Detection | Auto-fix | Fallback |
|---|---|---|---|
| Pipe-table rows crammed on one line | Regex: two or more `| \d+ |` or `| — |` cells on the same physical line separated only by ` | ` | Split at cell boundary, insert `\n`, ensure header separator row is present. Re-parse; if now a valid GFM table, continue | HALT (Rule 0a #5) with byte range |
| Missing header separator (`|---|---|---|`) between header and body rows | Regex: line starting with `|` followed by another line starting with `|` where the second line's cells are not `---` | Insert `|---|---|…|` between header and first body row (column count = pipe count minus one) | HALT with byte range |
| Unclosed code fence | Count of ` ``` ` in file is odd | none — HALT (Rule 0a #6) | — |
| Mermaid fence missing `mermaid` language tag | Detect ` ``` ` on its own line followed by `flowchart` / `graph` / `sequenceDiagram` / `stateDiagram` / `classDiagram` on the next line | Insert `mermaid` after the opening fence: ` ```mermaid ` | HALT (Rule 0a #9) with byte range |
| Missing blank line before/after table, code fence, mermaid block, heading | Scan for `[^\n]\n\|` (non-blank followed by table), `[^\n]\n\`\`\`` (non-blank followed by code fence), `[^\n]\n##` (non-blank followed by heading) | Insert `\n` before the block; scan the closing side, insert `\n` after | HALT (Rule 0a #10) with byte range |
| Solo-pipe noise line — `\|` (or whitespace+pipes) on its own line preceding a table separator | Regex `^\s*\|+\s*$` matches | Delete the line unconditionally (v2.3.26, Transform 0) | never — always auto-fixable |
| Table column-count mismatch — header row has N pipe-cells, separator row has M pipe-cells, N ≠ M | Count pipes in header vs `\|(:?-+:?\|)+` separator | none — the LLM's intent is ambiguous | HALT (Rule 0a #11) with byte range; re-compose |
| Heading levels beyond `##` at section boundary | Regex: `^#[^#]` (level 1) at start of a section, or `^####` (level 4+) at section boundary | none | WARN (not halt) |
| Bullets mix `*` and `-` | Line-scan; if both markers appear in the same bullet-list block | none | WARN |
| Table cell contains a literal `\n` or `<br/>` | Regex on cell contents | WARN — remark-gfm renders `<br/>` inline but multi-line cells are hostile; prefer restructuring | WARN |

**The "pipe run-on" auto-fix regex** (the specific one that catches the screenshot bug):

Given a physical line matching `^(\|[^\n\|]+)+\|\s*\|\s+\d+\s+\|`, split at the boundary `| \d+ |` (start of a numbered row) into separate physical rows. If the split produces rows with consistent pipe counts + a header row + data rows, insert `|---|---|---|` (matching the pipe count) between header and first data row. Emit each row on its own physical line separated by `\n`.

Example:

INPUT (broken, from screenshot):
```
| # | Step | Files | | 0 | Prettier-format… | Modified: context/… | | 1 | | 2 | Add validators | New: models/holiday.js |
```

AUTO-FIXED (renderable):
```

| # | Step | Files |
|---|---|---|
| 0 | Prettier-format… | Modified: context/… |
| 1 |  |  |
| 2 | Add validators | New: models/holiday.js |

```

If the auto-fix cannot align pipe counts (a row's cell count doesn't match the header), HALT with the exact byte range and the mis-aligned row.

The scan runs, in order:

1. **Pipe-table one-row-per-line check.** Walk every line that begins with `|`. Track the pipe-count per row. If two adjacent lines both begin with `|` AND share the same pipe-count AND appear on the same physical line separated by a space-pipe run (`| … | | …`), that's a single-line pipe-run-on → halt naming the line. Also: the header separator row (`|---|---|…|`) MUST appear on its own physical line between header and body — any table where the separator is inline with header or a body row → halt. WRONG: `| Step | Units | | 1 | … | | 2 | … |`. RIGHT: each row on its own physical line, separator row alone between header and body.
2. **Mermaid MUST be a fenced code block.** Any table that names steps in numbered order (`1. X → 2. Y → 3. Z`) without a corresponding `\`\`\`mermaid` fenced block for the flowchart → halt. A numbered list is NOT a diagram — the diagram must render as one. RIGHT: `\`\`\`mermaid\nflowchart LR\n    S1[…] --> S2[…]\n\`\`\`` on its own three physical lines, opening fence on its own line, closing fence on its own line.
3. **Heading level check.** Every `## ` heading in `implementation` mode must be a level-2 heading of a numbered section (§1–§9). No `#` (level 1 — that's the MC tab title). No level 3+ *at section boundary* (level 3+ inside a section subsection is fine).
4. **Code fences must be balanced.** For every opening ` ``` ` fence there must be a matching closing ` ``` ` fence on its own line. Odd count → halt naming the line of the last unclosed fence.
5. **Bullet consistency.** Every bullet list uses `-` prefix (never `*`). Mixed → halt naming the offending block.
6. **Blank-line-before-and-after every table, code fence, heading.** Missing blank lines cause the markdown parser to concatenate blocks. Scan for `[^\n]\n\|` (non-blank followed by table start), `[^\n]\n##` (non-blank followed by heading), `[^\n]\n\`\`\`` (non-blank followed by code fence). Any hit → halt.

**On any halt:** write nothing to disk. Report the byte range + rule number + concrete fix (e.g. "line 47: pipe-table rows 3 and 4 crammed on the same physical line — insert a newline between them"). This is the last line of defense; catching it here means the developer never sees an implementation.md rendered as an unreadable wall of text.

**Rule 11.6 — Consumer sub-task's §3 INCLUDES consumed contracts in full (v2.3.5, generalised in v2.3.11).** A sub-task with `capabilities: [consumes-contract, ...]` doesn't OWN the operations it calls — but the developer needs the FULL request/response/refusal shape of every operation it consumes to build correctly. §3 Operations exposed and consumed for a consumer sub-task MUST include:

- One `### <Method + Path>` heading per consumed endpoint (e.g. `### POST /api/holidays — Add a holiday (owned by sub-task 1 backend, consumed here)`)
- Request body table (fields, types, required, constraints) — copied verbatim from the owning sub-task's endpoint unit
- Response body JSON example — copied verbatim
- Refusals table — one row per distinct message (409 DATE_ALREADY_HOLIDAY, 400 NAME_TOO_LONG, etc.) — copied verbatim
- One-line pointer to the owning unit: `Owned by: EP-HCAL-01 (Inhouse-server/context/code-context/backend/domains/holiday/endpoints/add-holiday.md)`

The v2.3.4 output that only said "None owned. This sub-task consumes the three operations delivered by sub-task 1" was WRONG shape for §3 — it leaves the frontend developer with no contract in view. The prose about "three details of those contracts are load-bearing" belonged in §6 Touch points (as caveats on the consumed contracts), not as a substitute for §3's contract tables.

**Rule 11.7 — Every sub-task's §3–§6 must reach the same structural completeness bar.** A sub-task without persistence (its `capabilities` don't include `owns-state`/`reads-state`) legitimately has `§4 Stored data changes` as `None.` — but its §3 Operations, §5 User-facing surfaces, §6 Touch points must each be as concrete as its siblings' are for the sections that DO apply to it. If a consumer sub-task's §3 is 3 sentences of prose while its owner sibling's §3 is 500 lines of contract tables, that's a completeness gap — the consumer section pulls the consumed contracts up per Rule 11.6.

**Rule 11.11 — Plan-time coverage lives in `§1 Satisfies` column + `qa/quality-gates.md` tier pool; build-time evidence lives in `dev/acceptance-map.md` — NO `§7 Coverage` table in the plan (v2.3.16 replacement).**

Earlier drafts had a `§7 Coverage` table restating every parent AC/BR/TS with test file references at plan time. That table:
- Duplicated the AC/BR/TS ID list already in parent BA files (`acceptance-criteria.md`, `business-rules.md`, `test-scenarios.md`).
- Duplicated the evidence artifact `dev/acceptance-map.md` already built at `/dev:build` Stage 8.
- Grew to 30+ rows for a feature with 15 ACs × 5 BRs × 15 TS, adding noise without adding value.
- Introduced "Deferred to E2E" as a coverage status, which is a QA-audit vocabulary that has no place in feature-plan discipline — the plan states what WILL BE COVERED, not what will be deferred.

**Three separate artifacts own the three separate concerns:**

| Artifact | Owns | When |
|---|---|---|
| `implementation.md §1 Build sequence` Satisfies column | Plan INTENT — which AC/BR/TS IDs each build step delivers | Plan time |
| `qa/quality-gates.md` tier pool | STACK CONTRACT — which test tiers are mandatory for this sub-task's layer | QA setup (once per repo) — falls back to stack-detected pool if user skipped QA setup at plan time (see `/dev:plan` Stage 1 QA-check) |
| `dev/acceptance-map.md` | Build EVIDENCE — actual test file::test name + Pass/Fail per AC/BR/TS | `/dev:build` Stage 8 |

**No "Deferred" concept in the plan — every parent AC/BR/TS in this sub-task's scope is COVERED.** For a new feature at plan/build time, coverage is 100% across every applicable tier for the sub-task's layer. What varies is WHICH tiers apply — that comes from the stack (via `qa/quality-gates.md` if present, or via stack detection when skipped). Cross-layer coverage (E2E) is a legitimate covered TIER, owned by whichever sub-task authors the E2E test file (declared in §1 Build sequence of that sub-task + cross-referenced in §6 Touch points of the others).

**Plan-time coverage invariant enforced by Rule 11.9 §1:**
- Every parent AC/BR/TS ID in this sub-task's scope MUST appear in the Satisfies column of at least one §1 build step, OR appear as a `Not applicable — <layer-specific reason>` note on the build step where it would otherwise apply, OR appear as a Cross-sub-task row in §6 Touch points pointing at the sibling sub-task whose §1 covers it.
- Missing ID → halt naming the ID.
- The plan does NOT list test file paths or test names — those are build-time artifacts in `dev/acceptance-map.md`.

**Tier-strategy declaration:** `qa/quality-gates.md` declares which tiers are mandatory for each capability class (backend service, frontend app, mobile, worker, etc.). When `qa/quality-gates.md` is missing at plan time (user chose to skip QA setup — see `/dev:plan` Stage 1 QA-check with skip prompt), the plan uses stack-detected fallback tiers based on `shared-context/technology-stack.md` or repo package-manifest scan. Either way, the plan itself does not enumerate the tier list — the developer/agent reads it from the source-of-truth artifact at build time.

**Cross-sub-task coordination without a §7 table:**
- Every sub-task's §1 covers ITS layer's AC/BR/TS satisfactions
- Cross-layer E2E owned by ONE sub-task (typically the last-landing frontend sub-task, or a dedicated e2e/ folder declared in `qa/quality-gates.md`)
- §6 Touch points Cross-sub-task rows in other sub-tasks reference the E2E owner: `E2E for AC-M / BR-K owned by sub-task N (<repo>) — tests/e2e/<flow>.spec.js`

**What §7 Risks and rollback mitigations reference now (v2.3.16):** ID + tier, never a specific test file. Example: `Covered by AC-1 + BR-3 at Unit + Integration tiers (per qa/quality-gates.md backend pool)`. The actual test file and test name live in `dev/acceptance-map.md` at build time.

**Rule 11.12 — Every `§2` row is substantive; bare `N/A` is a compose halt (v2.3.9 format fix).** "N/A" without a 1-line reason is unfalsifiable — the reader can't tell "N/A because carefully considered and doesn't apply" from "N/A because forgot to think about it". Every row now requires one of these shapes:

- **`N/A — <specific reason this dimension does not apply>`** — 1-line justification. Reasons must be specific: "N/A — no data objects in this repo", not bare "N/A". "N/A — no queue system exists in this repo" not "N/A — no jobs". "N/A — no monitoring framework to extend" not "N/A — none".
- **`<real impact statement>`** — a described impact, per Rule 11.10's shape adapters (Migration Plan block for altered collections; Message Contract block for queues; etc.)
- **Either always beats a bare N/A.** Compose halts on any row where the impact cell is exactly `N/A` (no dash, no reason).

Two rows that both look like "N/A" but say very different things:

```
| Feature flags | N/A |                          ← BARE — halt
| Feature flags | N/A — ships dark; endpoints unreachable until the routes registered in §1 step 6 |   ← SUBSTANTIVE — OK
```

The second is 1 line more but conveys the actual design decision.

**Rule 11.9 — Pre-write SELF-CONSISTENCY validation (v2.3.8, extended v2.3.9).** Before writing any implementation.md to disk, `tl-feature-compose` runs an explicit consistency check against a defined list of contradictions. Any hit halts the compose with a per-issue diff. This catches "the plan disagrees with itself" bugs — the class of defect an outside reviewer sees within minutes.

Consistency checks the compose runs (in order):

1. **AC/BR/TS coverage — every ID in scope is satisfied somewhere (v2.3.16 simplified — no §7 table anymore).** Every parent AC/BR/TS ID in this sub-task's scope must appear in exactly ONE of: (a) `§1 Satisfies` column of a build step in this sub-task (Covered here), OR (b) `§6 Touch points` Cross-sub-task row pointing at the sibling sub-task whose §1 covers it (Carried by sibling), OR (c) a `Not applicable — <layer-specific reason>` note on the build step where it would otherwise apply. Missing ID → halt naming the ID. Two claims → halt naming both. **No "Deferred to E2E" status** — E2E is a covered TIER (declared in `qa/quality-gates.md` and owned by whichever sub-task authors the E2E test file), never a deferral.

2. **Refusal exhaustiveness.** For every endpoint in `§3`:
   - Every code in the refusals table must correspond to at least one failure clause in the execution-order table (step X `→ Failure: 400 …`).
   - Every failure clause must have a corresponding refusal-table row.
   - For every conditional update / concurrent-write endpoint, the compose must enumerate every "matched null" branch (not-found / not-author / stale / etc.) and disambiguate each with a refusal code. A branch that can happen but isn't handled → halt naming the branch.
   - Backend refusal codes must all be handled in the frontend consumer's `§3` UI-placement column. Every code — no silent 401, no silent 404. If the frontend intentionally sends a 401 through a middleware handler and shows no UI, that's stated explicitly, not implied.

3. **Local-check-doesn't-defeat-server-reachability.** If the plan justifies leaving off a control-shape attribute ("no `maxLength` attribute so the server's 400 wording is reachable"), no other clause in the same sub-task's `§5` can add a local check that blocks the request before the server sees it. Contradiction of the reachability rationale → halt with both clauses printed side by side. Same for control-char rejection, length caps, format checks.

4. **Every field the request accepts has a validation clause.** Cross-check `§3` request-body table against the execution-order table. Any field that appears in the body table but not in the execution-order's validation steps → halt (or the plan must state "no validation needed because <reason>" as its own execution-order step).

5. **Every list endpoint has an explicit pagination decision.** Cross-check `§3` for GET-style list endpoints. Missing pagination clause (either "paginated with cursor/limit params" OR "not paginated in v1 because <reason>, accepted assumption") → halt.

6. **Referenced-but-not-defined check (§B in the reviewer's feedback).** Every identifier mentioned in `§6` (component props, state fields, service functions, toast systems, session-store fields, existing utilities) MUST be sourced somewhere in the same file: either defined as a prop/state row in a table above OR cited as a Reuse entry in `§7` naming its file path OR named in an existing sub-task's `§7` (for cross-sub-task deps). `currentUserId` referenced as a prop but never sourced → halt. `useToast()` or "the toast system" referenced but not named as a Reuse in `§7` → halt.

7. **Response envelope ownership.** For every endpoint returning a wrapped shape (`{comments: [...]}`), the plan must state which layer unwraps to the raw shape the callers use. Frontend `§5` component state saying `comments: Comment[]` combined with backend `§3` response saying `{ comments: [...] }` must be paired with an explicit statement in `§5` service layer of who unwraps. Missing → halt naming the mismatch.

8. **Success-vs-refusal branching stated.** If the plan uses "return the rejection object rather than throw" (or any equivalent no-throw pattern), the plan must state HOW callers distinguish success from refusal (e.g. "callers check `result.ok`" OR "callers check `result.response !== undefined`"). Every one of the three (or N) service-layer calls must branch — the branch is not optional. Missing → halt.

9. **Test file paths NOT in the plan (v2.3.16 simplified).** The plan does NOT list test file paths or test names — those are build-time artifacts in `dev/acceptance-map.md`. If any `tests/` or `spec.` or `test.` file path appears in the plan outside §1 Build sequence's Files column for the tests step, → halt naming the leak. §1's Files column MAY name a test glob (e.g. `New: tests/<domain>*.spec.{js,jsx}`); specific test file::test names live in acceptance-map.md.

10. **Cross-doc auth mechanism identity.** Backend `§3` phrasing describing the auth artefact (e.g. "session credential with email claim", "req.user.id"), and frontend `§5` service-layer phrasing describing the same artefact (e.g. "Authorization: Bearer <session token from local session store>") MUST cite the same UPSTREAM source — a `shared-context/system-landscape.md § Auth boundary` section OR a specific DEC. If they name different tokens/shapes and there's no explicit "these are the same X, per DEC-Y" bridge, → halt.

**On any halt:** the compose HALTS this sub-task (or the split-batch as a whole per Rule 11.8's fan-in). Report each finding as a diff — quote both clauses that disagree, name the contradiction category, cite the rule. `/dev:plan` Stage 4 surfaces this as `stage_4_self_consistency_failed`. The developer's fix goes upstream — either fix the analysis scratchpad section that produced the contradiction OR fix the TL context unit that's ambiguous OR resolve an open question that was left silent.

**Rule 11.13 — Content quality — exhaustiveness, consumers, named-dependencies, branch spelled out, boring decisions recorded (v2.3.9).** Format rules catch contradiction; content rules catch omission. The compose applies these principles to every draft before running the self-consistency checks:

1. **Every table exhaustive over its own input space.** An execution-order table isn't done when it lists what happens on the happy path — it's done when it walks EVERY path parameter and EVERY body field and states what happens when each is malformed AND when each is missing AND when each is in every distinct state (fresh / already-modified / soft-deleted / stale). Ordered ≠ complete. Before signing off a `§3` endpoint, the compose walks each input across all its states and confirms each has an execution-order line. Missing state → halt naming which input, which state.

2. **Every refusal code has a consumer.** Every code in a backend's refusal table must be handled somewhere in the frontend's `§3` UI-placement column (or explicitly stated as "not reachable from the user's flow" with a reason). The counter-rule is symmetric: if the frontend can't reach a code, the backend shouldn't be returning it — remove from backend or explain why it's reachable through another path. Rule 11.9 §2 catches "backend refusal missing frontend handling"; Rule 11.13 also catches "frontend describes handling for a refusal code the backend never returns" (dead handler).

3. **Name every dependency you lean on.** The reader test is: could a developer who has NEVER opened this repo satisfy this line? If not, name the file / module / hook / component / utility. `Modal.jsx` and `formatTimestamp.js` are named — good. "the toast system" appearing four times unnamed → halt with the phrase and Rule 11.9 §6 firing. `currentUserId` as a required prop with no source → halt.

4. **Say HOW the caller branches, not just what they read.** When a contract is unusual (returns rejection object rather than throwing; success vs refusal aren't the same shape; error status lives one level down), naming the field to read AFTER you know it's a refusal is only half the answer. The other half — how the caller distinguishes success from refusal in the first place — must be stated as a specific condition (e.g. "callers check `result.ok`" OR "callers check whether `result.response` is defined"). Rule 11.9 §8 catches this.

5. **Boring decisions surface IN CONTEXT — no "Assumptions" heading in the plan (v2.3.15 sharpened).** No pagination on a list operation, no rate limit, no permission model, no edit operation — each reads as an OVERSIGHT unless recorded — BUT the recording lives AT THE SECTION WHERE THE CODE IMPLEMENTS IT, as ONE line inside an existing table or one-liner. No dedicated "Assumptions" heading. The plan is a build script, not a policy doc; a heading that collects "assumptions we accept" makes the reader parse policy prose instead of build directives.

   **Where each boring decision LIVES:**
   - **No pagination** — VISIBLE in §3 response payload example (no `next`/`page`/`cursor` fields) + optionally one clause in §3 per-operation Invariants line (`Not paginated — response returns full result set`). No separate note needed if the payload example carries the shape.
   - **No rate limiting** — one clause in §3 per-operation Invariants line (`No rate limiting; uncapped`).
   - **No permission model beyond authentication** — one clause in §3 per-operation Authz line (`Any authenticated caller; no role check, no owner check`).
   - **No optimistic updates** — one clause in §5 per-surface on-success behaviour line (`Refetch before mutating local state`).
   - **No live refresh / polling / subscription** — one clause in §5 per-surface Effects line (`No polling; refetch only on <trigger> and explicit refetch()`).
   - **No edit operation** — if the reader might expect one, one clause in §5's operation-wiring table row OR §8 Out of scope bullet. Not both.

   **The one-question test still applies:** *"Would the developer type something different into a file if this line changed?"* If yes → keep as an in-context directive. If it's just parent-scope context or a "we'll revisit" note → cut (parent's Dependencies tab).

   **Wrong shape (compose halts):**
   - A dedicated `**Assumptions.**` heading in §8 (or anywhere).
   - `No <absence> — accepted assumption; <business rationale>; revisit if that changes.` (Bullet-list assumptions are the anti-pattern this rule closes.)

   **Silent absences check** — the pre-write scan still verifies that expected boring-decisions are recorded SOMEWHERE (§3 Invariants, §3 Authz, §5 on-success, §5 Effects, §5 operation-wiring, §8 Out of scope). If a reader would EXPECT to see pagination addressed and no section carries it → halt naming the missing directive site. But the halt asks for the clause to appear AT the code-implementation site, never to add an Assumptions heading.

6. **Cross-check the same nouns across sub-tasks (literal diff).** For every noun that appears in both sub-tasks — envelope field name (`comments` / `data` / `items`), auth artefact name (`session token` / `Bearer <credential>`), identifier field name (`id` / `_id` / `commentId`), timestamp field name (`created_at` / `createdAt`), refusal shape (`{status, message}` / `{code, error}`), pagination structure (`{next, items}` / `{page, size, total}`) — the two docs must use IDENTICAL nouns. If backend calls it `_id` and frontend calls it `id`, that's a bug waiting to happen. Rule 11.8 catches this at the reference-kind level; Rule 11.13 adds field-name-level identity.

7. **The adversarial read pass (v2.3.9 — the final gate before writing).** After Rules 11.9 (consistency), 11.10 (feature-shape adapters), 11.11 (§1 Satisfies canonical coverage per v2.3.16), 11.12 (substantive rows), and 11.13 (content quality) all pass, the compose runs ONE MORE pass reading the plan as **an adversary who wants to build something technically compliant and broken**. Specifically: the compose re-scans looking for constructions where a plan clause and a stated rationale contradict each other RHETORICALLY, not structurally — e.g. "no `maxLength` attribute so server 400 is reachable" while the compose has also written a local check that blocks Submit when body length exceeds server max. Structurally the consistency check catches this via Rule 11.9 §3. But the adversarial pass catches the SUBTLER variant: local check with a slightly different bound (e.g. blocks at 1900 chars while server refuses at 2000, or blocks control chars while server refusal renders "Comment contains characters that can't be saved"). Rhetorical inconsistencies where the plan LOOKS compliant but produces broken behaviour.

   The adversarial pass is not a rule; it's a mindset. The compose prompt for this pass reads: **"Read the draft as a hostile developer who wants to write code that passes every named test AND still ships a broken product. Where would that hostile developer succeed? Every place they succeed is a rule the plan needs to state explicitly or a sentence the plan needs to rephrase."** Findings surface as candidates for Rule 11.9 additions; on live compose, they're halts with a per-finding diff.

**Rule 11.14 — Two-tier rollback in `§8` (v2.3.11).** Every sub-task's `§7 Risks and rollback` closes with TWO explicit rollback levers, not one:

- **Rollback — cheapest lever:** the one action that removes user-visible reach with the smallest edit. Usually undoing the mount / route registration / wiring step — the last step in `§1 Build sequence` that made the new work reachable. State it as a one-line command or edit. Nothing else is touched; the built code stays in the repo, unreachable.
- **Rollback — full:** the full revert — the complete list of files/paths/artefacts to delete or revert, plus any store-level rollback (drop the new table/collection, undo the migration). State it as a bullet list; every artefact listed in `§1` step-by-step should either be reverted here or explicitly justified as "left in place, harmless."

Rationale: a single "rollback plan" hides the distinction between "one minute, no user impact" and "full unwind, coordinate with ops." Two levers make it obvious to on-call which to reach for. Compose halts if `§8` has only one lever or the cheapest lever is missing the "which step from `§1` this undoes" reference.

**Rule 11.15 — `capabilities:` frontmatter — machine-readable roles the sub-task plays (v2.3.11).** Every sub-task's `implementation.md` frontmatter carries `capabilities: [<role>, <role>...]` — a list drawn from a controlled vocabulary. Rule 11.8's cross-sub-task interconnection check uses this to verify structural pairings without keyword-scanning prose.

Controlled vocabulary (stack-agnostic):

- **`exposes-contract`** — this sub-task owns an operation contract (an endpoint, an RPC method, a queue message shape, a job trigger) that other sub-tasks consume.
- **`consumes-contract`** — this sub-task calls an operation owned by a sibling sub-task.
- **`owns-state`** — this sub-task creates or writes persisted state (table, collection, KV entry, file store, cache region).
- **`reads-state`** — this sub-task reads state owned elsewhere (either a sibling's `owns-state` or pre-existing state), but does not write.
- **`renders-surface`** — this sub-task creates or modifies a user-facing surface (web page, mobile screen, CLI command, terminal UI, service dashboard).
- **`bridges-integration`** — this sub-task adds or modifies an external integration point (third-party API, webhook, message broker connection).
- **`schedules-work`** — this sub-task adds or modifies background jobs, cron, queue producers, scheduled triggers.
- **`observes`** — this sub-task adds monitoring, tracing, metrics, or structured logging surfaces beyond the existing convention.

Multiple capabilities per sub-task are normal. Backend sub-task typically: `[exposes-contract, owns-state]`. Frontend/mobile sub-task typically: `[consumes-contract, renders-surface]`. Job/worker sub-task: `[schedules-work, consumes-contract]` or `[schedules-work, owns-state]`.

**Cross-sub-task check Rule 11.8 uses this for:**
- Every `consumes-contract` sub-task's `§3` MUST reference an operation owned by an `exposes-contract` sibling. Compose halts if a consumer cites an operation no sibling exposes.
- Every `owns-state` sub-task's `§4` MUST list new/modified persisted state. Compose halts if `capabilities` claims `owns-state` but `§4` is `None.`.
- Every `renders-surface` sub-task's `§5` MUST list at least one surface. Compose halts if `capabilities` claims `renders-surface` but `§5` is `None.`.
- Every `exposes-contract` sub-task's `§3` MUST have at least one owned operation. Compose halts otherwise.

Rationale: keyword-scanning prose to determine role is brittle. A frontmatter field the compose can read directly is not. It also gives the reader (and reviewers) a one-glance summary of what each sub-task's job is in the split.

**Rule 11.10 — Feature-shape adapters — the frame is the FRAME, not the CONTENT (v2.3.8, updated v2.3.10).** The 9-section (§1–§9) structure is a chassis. Certain feature shapes REQUIRE additional sub-section content beyond the frame. If the analysis scratchpad or TL units indicate one of these shapes, the compose MUST include the additional sub-sections. Missing → halt with `feature_shape_gap_<name>`.

Detected shapes + mandatory sub-sections:

**a. Migration on an existing collection/table with live rows** (detected via `dev/<repo>-analysis.md § impact_matrix.database` mentioning "modified" or "altered" — not just "new"):

- `§4` must include a "**Migration plan**" sub-section with:
  - Ordered forward migration steps (add column with default → backfill in batches → tighten constraint → remove default) — each step with its own execution characteristics
  - Backfill strategy — batch size, throttling, resumability, expected duration for a repo-scale row count
  - Dual-read window — during migration, which reads see old vs new; when the switchover happens
  - Rollback that ISN'T "drop the collection" — a real down migration that undoes the change without destroying data
  - Consistency window — what queries might see stale/mixed data during migration
- N/A is not acceptable here. If the sub-task says "modified an existing collection" and this block is missing → halt.

**b. Queue / event / async contract** (detected via `dev/<repo>-analysis.md § impact_matrix.jobs` or `.notifications` non-N/A):

- `§3` must include a "**Message contract**" per message-type block:
  - Delivery semantics — at-least-once / exactly-once / at-most-once — chosen explicitly, not implied
  - Idempotency key strategy — what makes a re-delivery a no-op
  - Retry policy — max attempts, backoff, dead-letter queue behavior
  - Ordering guarantees — total order per key, no order, FIFO with partition-key
  - Payload schema and versioning strategy (adding fields, deprecating fields)

**c. Real authz model** (detected via `dev/<repo>-analysis.md § impact_matrix.authz` mentioning roles OR per-object permissions):

- `§3` must include an "**Authz decision**" block per endpoint:
  - Who can invoke — role names OR "any authenticated user" OR "resource owner only"
  - What data the caller can see/modify — full row / filtered projection / owned rows only
  - How the check is enforced — route middleware / handler check / DB query filter / row-level security
  - Failure code when unauthorized — 403 vs 404 (leak vs hide)

**d. Performance targets declared in parent NFRs** (detected via parent's `nfrs.md` mentioning latency or throughput targets):

- `§4` must include an "**Expected query plans**" block per read-heavy query — the intended index usage, projected rows scanned, projected time.
- `§7` must include a "**Load characteristics**" block — expected requests-per-second, expected data volume, when load-tests fire.

**e. Feature spans > 2 sub-tasks** (detected via parent's rollup Sub-tasks table count > 2):

- `§6` Touch points must switch from table to a **dependency graph** (mermaid `flowchart LR` showing per-sub-task edges), because a table can't cleanly represent an N-way dependency graph. Each edge annotated with the resource it carries (endpoint, entity, event).

**f. Cross-cutting concern touched (logging, error-tracking, tracing, metrics)** (detected via `§2` Monitoring dimension non-N/A):

- `§2` Monitoring row must not be a 1-line "log the error" — must state the observation contract (event name / correlation id / retention / where it lands / who alerts on it).

**The general principle behind these adapters:** an "N/A" row in `§2` is a CLAIM (this dimension does not apply) that must be defended by the same rigor as a non-N/A row. Silent N/A → the plan is unmoored to the reader. Every N/A row in `§2` must include a 1-line justification for why the dimension doesn't apply to THIS sub-task specifically ("N/A — no data objects in this repo", NOT bare "N/A"). Compose halts if any `§2` cell is bare N/A.

**Rule 11.8 — Cross-sub-task interconnection is VERIFIED before write (v2.3.6).**

**The problem this closes.** A split feature is built by different developers on different branches. The backend developer builds the endpoint contract in their branch; the frontend developer, working in parallel on THEIR branch, consumes that contract from THEIR sub-task's implementation.md. When both PRs merge back, the code must interoperate — the frontend must call the exact contract the backend delivered, with the exact refusal codes the backend returns, against the exact entity the backend writes. If the two sub-tasks' implementation.md files drifted on any of these — the endpoint path, the request field names, the response shape, the refusal codes, the entity identifier — the merged feature is broken.

**The plan-time verification.** Every shared reference across sub-tasks — endpoint / page / entity / business rule / acceptance criterion / test scenario — MUST be verified as identical across all sub-tasks that reference it, BEFORE any implementation.md is written to disk.

**What "identical" means for each reference kind:**

| Reference kind | The owning sub-task writes | Every consuming sub-task writes | Identical means |
|---|---|---|---|
| Endpoint | Full contract in §3 — heading with Method + Path + unit ID; request table; response example; refusals table | Same heading (Method + Path + unit ID) in §3 marked "consumed here"; same request table; same response example; same refusals table | Byte-for-byte copy of the owning §3 contract fields |
| Page | Full page shape in §5 — heading with unit ID; layout; interactions | Cross-sub-task row in §6 citing the page's unit ID | Same unit ID cited |
| Entity | Full field table in §4 — unit ID + object name | Cross-sub-task row in §6 citing the entity's unit ID + object name for reads/writes | Same unit ID + object name |
| Business rule / AC / test scenario | Cited in owning sub-task's §1 Satisfies column with the parent's ID | Cited in consumer's §1 with the identical ID | Identical ID string |
| Cross-sub-task Touch point | §6 row: "Delivers <ids> for sub-task N (<repo>)" | §6 row: "Consumes <same ids> from sub-task N (<repo>)" | Symmetric — one row on each side, referencing the same IDs |

**The verification runs at compose time, before any file is written:**

1. **Fan-in of the parallel compose batch.** For a split feature (compose runs on N sub-tasks in parallel), each sub-task's compose worker holds its output IN MEMORY. No file is written until every sub-task's compose completes.
2. **Cross-reference index build.** Once all workers have their in-memory drafts, one coordinator step builds a cross-reference index across all N drafts: every unit ID mentioned, in which sub-task, in which section, with what surrounding contract text.
3. **Consistency check per reference.**
   - For every unit ID appearing in more than one sub-task, verify identical shape per the table above.
   - Every cross-sub-task Touch point row must have a mirror on the counterpart sub-task.
   - Every consumer must cite an owner that actually declares full ownership (not just another cross-sub-task consumer).
4. **On any mismatch found:** the compose HALTS the whole split. Write nothing to disk. Report the mismatch:
   ```
   ✗ Cross-sub-task interconnection mismatch:
     Sub-task <M> (<repo>) §3 declares <unit-id> with <shape A>
     Sub-task <N> (<repo>) §3 consumes <unit-id> with <shape B>
     These disagree on: <field-by-field diff>
     
     Fix at the TL context unit level (single source of truth for the contract);
     re-run /dev:plan --resume.
   ```
   The developer edits the TL context unit (which both sub-tasks read as their source of truth), then re-runs compose — both sides regenerate consistently from the shared unit.
5. **On clean interconnection:** all N sub-task files are written to disk atomically. The parent's rollup Sub-tasks table is then derived from the verified cross-references — `Depends on` / `Blocks` columns come directly from the checked Touch point mirrors, not paraphrased.

**Why the check runs at compose, not at build.** Once sub-task files are on disk and pushed to MC, developers may start building. Discovering a mismatch AFTER build has begun means torn-off work. Catching it at compose means the developer sees the mismatch before ANY code is written — cheapest possible feedback loop.

**Why the fix goes to the TL context unit, not to the sub-task files.** Each sub-task's implementation.md is DERIVED from the TL context units it references (endpoint files, page files, entity files). If two sub-tasks disagree on a contract, one of them is reading a different version of the truth — or the unit itself is ambiguous. Editing the unit forces both sub-tasks to re-derive from the same source; editing one sub-task's file to match the other leaves the source-of-truth drift in place and re-emerges on the next re-compose.

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

### 7. **Mechanical fix pass (Rule 0c.i) — MUST run before Write** (v2.3.21 — CRITICAL, do not skip)

BEFORE calling `Write`, run the deterministic transformations from **Rule 0c.i** on the compose LLM's draft output string:

1. `split_table_rows(text)` — split pipe-run-on lines at row boundaries; insert `\n` between rows
2. `insert_header_separator(text)` — insert `|---|---|…|` between header and body if missing
3. `ensure_blank_line_surrounds(text, ["|", "```", "```mermaid", "##"])` — insert `\n\n` around every table, code fence, mermaid block, heading if missing
4. `tag_bare_mermaid_fences(text)` — insert `mermaid` after ` ``` ` if followed by `flowchart|graph|sequenceDiagram|…`
5. `strip_retired_headings(text)` — remove `## 7. Coverage`, `**Assumptions.**`, `Deferred to E2E`, `# FEAT-`, etc.

After transformations, **RE-SCAN** the transformed string for HALT-only conditions (payload > 60 000 chars, unclosed code fence, framework field paths in §8, mis-aligned column counts after auto-fix). Any HALT → report + do NOT `Write`.

**This step is mandatory. The compose LLM's output is not treated as reliable for mechanical format** — see Rule 0c.i for the exact reference implementation the tl-feature-compose skill invokes.

### 8. Write the file + update inputs_hash + read-back verify
Write to the mode-appropriate output path with the mode-appropriate frontmatter (see the two frontmatter shapes at the top of the Operating contract section). `inputs_hash` is set to the sha256 computed in step 2 — for `description` and per-sub-task `implementation`, hash the sub-task's owned unit files, not the whole feature's owned units. Use CRLF-safe I/O — write with `\n` line endings; the push stage handles CRLF normalisation.

**IMMEDIATELY AFTER `Write`:** call `Read` on the just-written file, compute SHA-256 of the read-back content vs the transformed string sent to `Write`. Match → proceed. Mismatch → HALT with `blocker: write-tool-mangled-output`. This catches the rare case where line-ending normalization or filesystem encoding mangled the content.

**Mode → output path recap:**
- `implementation` on parent-alone → `features/<slug>/implementation.md` (frontmatter: `doc_type: implementation`, `compose_mode: implementation`)
- `implementation` on a sub-task → `features/<slug>/subtask/<repo>/implementation.md` (frontmatter: `doc_type: implementation`, `compose_mode: implementation`)
- `description` on a sub-task → `features/<slug>/subtask/<repo>/description.md` (frontmatter: `doc_type: description`, `compose_mode: description`)
- `rollup` on parent → `features/<slug>/tl-plan.md` (frontmatter: `doc_type: tl-plan`, `compose_mode: rollup`)

**Never write both `tl-plan.md` and sub-task files from the same call** — one call, one mode, one output. Callers that need both (`/dev:plan` Stage 2 in split branch) make multiple calls.

Preserve any manual developer edits marked with `<!-- KEEP -->` HTML comment sentinels — read the existing file first, extract fenced regions between `<!-- KEEP -->` and `<!-- /KEEP -->`, and reinsert them at the same section anchor on write. If a KEEP region has no matching anchor in the newly composed body, keep it at the section tail and warn the user.

### 9. Log material decisions
If composing forced a real design choice (e.g. picking one of two plausible target file paths, choosing which of two reused endpoints a page consumes), append a `DEC-###` row to `shared-context/decision-log.md`. Composition choices that are pure arrangement (order of sections, choice of table vs list) don't need a decision — only technical choices that later reviewers might contest.

### 10. Report per feature
Return: features composed vs skipped-unchanged (with reason each), the size per feature, open items surfaced (grouped by feature), and any features where the repo-scan preflight left file paths as `TBD`. Link to each `tl-plan.md`. If any feature refused to compose (missing units, size overflow, unresolved TBD in a critical field), name it and the reason — never silently swallow.

## Completion criteria

Depends on the mode.

**`implementation` mode** — a feature (or sub-task) is composed when: the output file exists at the mode-appropriate path with the correct frontmatter (including `capabilities:` per Rule 11.15); contains exactly eight sections in order (§1 Build sequence · §2 Impacted components · §3 Operations exposed and consumed · §4 Stored data changes · §5 User-facing surfaces · §6 Touch points · §7 Risks and rollback · §8 Shared contract); no `§ Coverage` section (removed in v2.3.16 — plan-time intent lives in §1 Satisfies column + qa/quality-gates.md tier pool; build-time evidence lives in dev/acceptance-map.md); no `§ Business flow` and no `§ How to verify locally` (dropped in v2.3.10 — business context lives on the Description tab, verify runbook lives in status.md); every operation owned has its order-of-checks and refusals tables with one row per distinct response `message`; the §4 "Fields written" table lists only the fields written with a one-line "Never touched" boundary; every user-facing surface is named by role with its operation wiring; every REUSE from the context graph is captured in Touch points (not a separate Prerequisites section); §8 Shared contract passes the wire-only test (Rule 11.3a — no framework field paths); the file is ≤ 60 000 CHARACTERS (Rule 10 — `len(text)`, not byte length; multi-byte glyphs like em-dashes count as one character each); each section stayed under its Rule 10 per-section max on the FIRST write (no compose-then-trim rewrite pass); every concern in Rule 10a's required-coverage checklist for the sections that apply is present as ONE dense line or ONE table row (no missing concerns, no paragraph-where-a-line-would-do); Rule 10b density scan passed (no adjacent-sentence redundancy, no restated-table paragraphs, no sentence > 40 words); and none of the Rules 1–15 above are violated.

**`description` mode** — a sub-task Description is composed when: `subtask/<repo>/description.md` exists with the correct frontmatter; the body is one or two paragraphs of continuous prose (no headings, no lists, no tables, no code fences); business vocabulary used throughout; distinct refusals named as distinct business situations (not response codes); length between 500–1500 characters (warn at 3 KB); none of the Rules 1–11 above are violated.

**`rollup` mode** — a parent's rollup Implementation is composed when: `features/<slug>/tl-plan.md` exists with `compose_mode: rollup` in frontmatter; contains exactly the three sections (Build sequence · Sub-tasks · Touch points); the Build sequence names each sub-task by role and has a mermaid step-graph of sub-task nodes; the Sub-tasks table has one row per sub-task with `#`/`Repo`/`MC Task`/`Depends on`/`Blocks`/`State` columns; no Operations / Stored data changes / User-facing surfaces sections present (those live per sub-task); target ≤ 5 KB; none of the Rules 1–15 above are violated.

**Pre-write scan (v2.3.11).** Before writing, verify the document does NOT contain any of these patterns:
- **Version numbers next to a technology name**: `React 18`, `Node 20`, `Python 3.11`, `MongoDB 6.0`. Version is deployment detail, not plan detail — halt.
- **Feature-id headings**: `# FEAT-` or the feature id in any H1/H2 heading. Feature identity lives in frontmatter — halt.
- **Business goal / user flow / acceptance criteria / NFR / test scenario / dependency prose** duplicating other tabs — halt.
- **Framework field paths in §8 Shared contract**: any `req.`, `res.`, `result.response`, `ctx.`, `.headers[`, or runtime-accessor-shaped bracket path inside `## 9. Shared contract` — halt per Rule 11.3a.
- **Aspirational prose**: `consider`, `might`, `could`, `we should think about`, `probably` outside of a `[HELD · waiting on OQ-…]` marker — halt per Rule 8.
- **Client-narrative preambles**: `⚠ PROVENANCE`, `SIMULATED response round`, `the client chose transparency knowingly` — halt per Rule 7.

File paths (`src/…`, `app/…`, etc.) and framework names (`React`, `Jest`, `Mongoose`, etc.) are ALLOWED in §1/§4/§5/§6 per Rules 1 and 2. Framework-idiomatic code snippets (`new mongoose.Schema({...})` blocks) are NOT allowed — describe the constraint in prose. §9 remains framework-clean by Rule 11.3a.

Any hit means the composition is wrong. Rewrite before writing to disk.

## Principles

- **Compose, don't author.** The design lives in the graph. You arrange it for one feature.
- **Inline what a developer needs; cite what they don't.** Endpoint contracts of endpoints the feature owns are inlined. Endpoint contracts of endpoints the feature *reuses* are cited by id and their repo path.
- **Never invent.** Where the source is silent, surface the gap. `TBD` cells and §8 rows are the honest way; a plausible guess is the wrong way.
- **Plan-only, no business restatement.** implementation.md is a build spec — business context (goal, user story, scope, personas, journeys) lives on the Description tab. No `## Business Goal`, no `§ Business flow`. The plan opens with `§1 Build sequence` and closes with `§8 Shared contract` (reference material at the tail, buildable work at the head).
- **Never leak secrets.** Env var names, never values. Off-limits files during repo scan.
- **Stay under the cap.** MC rejects >60 KB. If the composed doc would exceed the cap, ask the user to split the feature — don't truncate.
- **Preserve developer edits.** `<!-- KEEP -->` blocks survive re-composition.
- **Idempotent by inputs_hash.** A re-run against unchanged inputs is a no-op.
