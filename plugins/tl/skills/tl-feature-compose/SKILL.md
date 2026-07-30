---
name: tl-feature-compose
description: Compose a self-contained, buildable per-feature implementation plan (`tl-plan.md`) from the TL context graph and the BA feature breakdown. Use whenever a feature has been planned technically (units exist in `context/frontend|backend|database/`) and needs a single document a developer or coding agent can build from without opening five other files. Point it at one feature folder, a `FEAT-<AREA>-NN` id, an `initiative=<name>` slice, or the whole `context/features/` set; it reads the feature, its owned pages/endpoints/entities, and (when the repo is cloned locally) the target repo's file layout, and writes a 9-section technical spec inlining every endpoint contract, entity column, and page shape. It never restates business rationale (that's in `feature.md`), never invents an endpoint/contract/schema/path the source can't ground, and never composes above Mission Control's 60 KB `implementationDetails` cap.
---

# TL Feature Compose (context graph + feature breakdown → buildable per-feature plan)

You are turning the **linked technical context graph** the TL feature-planning skill produces into a **self-contained per-feature implementation plan** — one document a developer or coding agent can hand straight to Claude and say "build this," without opening the feature folder, the workflow, the acceptance criteria, or any unit file. The graph is a memory for reuse across features; `tl-plan.md` is the buildable output for one feature.

The defining behaviour of this skill is **composition, not authoring**. You do not design new pages, new endpoints, new entities, or new integrations — that is the `tl-feature-planning` skill's job, and if you find genuinely undecided design points you record them as open questions in §9 rather than inventing them. What you *do* is arrange the design that already exists into a document a developer can read top-to-bottom and build from, inlining what needs to be inlined (endpoint contracts, entity columns, page shape) and citing IDs where a follow-through is enough (a reused endpoint the feature does not modify, a `DEC-###` decision the developer does not need to re-derive).

This skill **authors context, not code**. It produces the per-feature buildable spec that precedes implementation; it does not write production code, and it is distinct from `tl-feature-planning` (which authors the graph) and `tl-spec-review` (which scores a finished spec). Compose runs *after* planning; a feature with no owned units in the three indexes cannot be composed.

## Operating contract

Read the **`delivery-os-conventions`** contract first if it isn't already in context — the workspace layout, frontmatter standard, stable-ID rules, source-citation form, and controlled vocabulary. Your inputs are:

- The feature folder — `context/features/<slug>/feature.md`, `implementation-plan.md` (BA's build-areas, optional context), `workflow.md`, `acceptance-criteria.md`, `dependencies.md`, `open-questions.md`.
- The feature's **owned unit files** — pages under `context/frontend/pages/`, endpoints under `context/backend/domains/`, entities under `context/database/entities/` — resolved via the three layer indexes and the feature-cell matching rule (`Used by Features` cell can hold multiple ids, comma-separated; match on word boundary).
- The BA registers the units cite (`data-register.md`, `integration-register.md`, `workflow-register.md`, `business-rule-register.md`) and `shared-context/decision-log.md`.
- The target app repos declared in `.jetrix/cache/repolocation.json` — read the file, and for each repo that exists locally, do a shallow layout scan (top-level + one level down) to establish routing/handler/model conventions. Never read env files, secrets, credentials, or files that look like credentials — treat any file matching `.env*`, `*.pem`, `*.key`, `*credentials*`, `*secret*` as off-limits.

**Output.** For each feature composed, write `context/features/<slug>/tl-plan.md` with the frontmatter:

```yaml
---
doc_type: tl-plan
schema_version: 1.2
produced_by: tl
feature_id: FEAT-<AREA>-NN
composed_at: <ISO date>
inputs_hash: <sha256 of feature.md + owned unit files, for re-run skip>
---
```

The body follows the 9-section structure in **`references/implementation-plan-template.md`** — read the template before composing your first feature.

## Workflow

### 1. Resolve the target feature(s)
Take the target from the user: one feature folder / slug / id, or the whole set. If an `initiative=<name>` filter is present, restrict to features whose `feature.md` `initiative` matches (report which features the filter selected). If the target resolves to nothing, tell the user and stop — do not compose a made-up feature.

### 2. Skip-unchanged check (unless `--force`)
For each targeted feature, compute the `inputs_hash` — sha256 over the concatenation of `feature.md` + each owned unit file's body (frontmatter stripped, CRLF normalised). If a `tl-plan.md` exists with the same `inputs_hash` in its frontmatter, skip it and report `skipped-unchanged`. This is the same idempotence pattern `/jetrix:push` uses via `sync-state.json`.

### 3. Read the feature and its graph slice
For each feature to compose:
- Read `feature.md`, `workflow.md`, `acceptance-criteria.md`, `dependencies.md`, `open-questions.md`. (Optional: read `implementation-plan.md` for BA scoping context — but do NOT copy its text; you are producing a technical document, not concatenating a BA one.)
- Resolve owned units from the three indexes using the awk recipe from `references/index-resolution.md` (same matching rule `/jetrix:push implementation` uses — feature-cell word-boundary match, and the 2-hop endpoint→entity chain via each endpoint row's `Reads/Writes Entities` cell). Reject a feature with **zero owned units** — tell the user to run `/tl:plan` first, do not fabricate units.
- Read every owned page, endpoint, and entity file.

### 4. Repo-scan preflight
Read `.jetrix/cache/repolocation.json`. For each app declared:
- If the local path exists → `ls` the top-level and one level down to discover the routing / handler / model layout. Look for the entry points: `app/`, `src/`, `pages/`, `routes/`, `controllers/`, `domains/`, `models/`, `entities/`, `schemas/`, and their language-specific analogues.
- **Never recurse further, never `Read` a source file, and never touch anything matching the off-limits patterns above.** This is a *shape* check to name plausible target file paths in §2/§3 — not to grep the codebase.
- If the repo is missing locally → mark every file path in §2 and §3 as `TBD — repo not cloned locally, resolve at build time` and surface the missing repo as an open item in §9.

### 5. Compose the Implementation-tab content
Follow `references/implementation-plan-template.md`. The composed `tl-plan.md` populates **only** the Implementation tab of the Jetrix Task via `/jetrix:push implementation`. Description, Business Rules, Acceptance Criteria, NFRs, Test Scenarios, and Dependencies are populated by BA push from other files and never appear in this document.

The output contains exactly five subsections, in this order:

1. **Build sequence** — one paragraph naming the phases and their dependency order, one mermaid step-graph, and a step table (`Step | Build | Done when`). Each step is independently verifiable. A step that depends on an undecided open question is marked `[HELD · waiting on OQ-<id>]` and named as such — never a phase that pretends to be buildable while quietly depending on an unresolved decision.
2. **API endpoints** — one heading per endpoint the feature creates or modifies (`### Create — <role>`, `### Update — <role>`). Each carries: path parameter table (if applicable), request body table + JSON example, **normative execution-order table** (steps 1..N, each with failure code), success JSON with the exact response code, refusals table with **one row per distinct `message`** (three `409` variants → three rows, never collapsed), and a paragraph on invariants (idempotency, partial-write behaviour, side effects).
3. **Database modifications** — one line describing the affected data object by role. "Fields written by this feature" table listing ONLY the fields this feature writes. One "Never touched" line naming existing fields the feature does not write (for reviewer boundary awareness). A paragraph on any state semantics the write relies on.
4. **Frontend UI** — an API-wiring table (`Surface | Trigger | Calls`), one heading per user-facing surface described by role (row action, dialog, list, etc.), a control table on the interactive form, a refusal-placement table (which server `message` renders where, per code), and a one-paragraph API service description.
5. **Touch points** — Reuse / New table naming existing and new components **by role**. Includes the internal review caveat about re-verifying reuse entries.

### 6. Enforce the hard rules
Before writing the file. These are absolute — any violation means the composition is wrong and must be redone.

**Rule 1 — No file paths, anywhere.** Not in Touch points, not in headings, not in prose, not in code fences. Every component is named by its **role** — the leave controller, the decision dialog, the API service layer, the leave list, the row action. `controllers/Leave.js`, `src/components/**/*.jsx`, `models/LeaveRequest.js`, `routes/router.js`, and every other repo path is forbidden. The context graph (which the composer reads as input) has file paths — that is TL design detail; it is not for the reader of this document. The dev-agent, at build time, maps role names back to files via the local context graph, not via this document.

**Rule 2 — No framework, library, or version names, anywhere.** No `React`, `React 18`, `Vite`, `Express`, `Mongoose`, `mongoose.Schema`, `TipTap`, `Redux`, `Playwright`, `Jest`, `axios`, `@uiw/react-md-editor`, `Prisma`, `SQLAlchemy`. Describe the data object by role and by the fields written; do NOT include a schema code fence in any framework's syntax. Version numbers are always forbidden.

**Rule 3 — No duplication of other tabs.** This document contains ONLY the five subsections above. No Business Goal, no user-flow narrative, no mermaid workflow diagram (Description owns that), no AC list, no NFR list, no Business Rule list, no Test Scenarios, no Dependencies / Assumptions / Open Questions. If a fact belongs in another tab, do not restate it here — even briefly.

**Rule 4 — No feature identity in visible content.** Feature id, initiative, slug, and provenance live in the frontmatter and MC task metadata. Never a `# FEAT-…` H1. Never a "Provenance:" line. Never a reference to `feature.md`, `workflow.md`, `acceptance-criteria.md`, `ba-output/*`, `context/*`, or any scope-review filename. The Description and Dependencies tabs (BA-owned) carry any provenance the reader needs.

**Rule 5 — Existing schema fields the feature does not write are named in one line, not tabled.** If the feature writes four fields on an existing data object, the Database modifications table contains those four — and only those four. Fields not written are named on a single "Never touched: `<field-a>`, `<field-b>`, `<field-c>`" line. That is the whole allowance.

**Rule 6 — Response codes and messages are discriminated explicitly.** If an endpoint returns three distinct `409` messages, the Refusals table has three rows. Never collapse a code's variants into one row. Similarly for `400` variants.

**Rule 7 — No client-narrative, no provenance callouts, no author commentary.** Forbidden: *"the client chose transparency knowingly"*, *"this document being complete is not consent"*, *"a module HR uses daily"*, `⚠ PROVENANCE — PLANNED, NOT BUILD-READY` blockquotes, *"acceptance criteria are authored as bullets without ids"*, *"SIMULATED response round"* preambles. The Description and Dependencies tabs carry any client-facing note.

**Rule 8 — No aspirational text.** No *"consider"*, *"might"*, *"could"*, *"we should think about"*. Either the decision is made and stated, or the phase is marked `[HELD · waiting on OQ-<id>]`.

**Rule 9 — No secrets.** Env var **names** only if referenced at all — never values or credentials, even if the repo scan surfaced them.

**Rule 10 — Size budget.** Target 10–15 KB. Warn at 55 KB. **Refuse to write over 60 KB** — MC caps `implementationDetails` at 60 000 characters. If oversized, do NOT truncate; surface the overflow and ask the user to split the feature.

**Rule 11 — No invention.** Every endpoint contract, every DB field, every UI surface traces to the context graph or the feature files. When silent, mark the affected step `[HELD · waiting on OQ-<id>]` and name the gap. Do not guess.

### 7. Write the file + update inputs_hash
Write `context/features/<slug>/tl-plan.md` with the frontmatter above (`inputs_hash` set to the sha256 computed in step 2). Use CRLF-safe I/O — write with `\n` line endings; the push stage handles CRLF normalisation.

Preserve any manual developer edits marked with `<!-- KEEP -->` HTML comment sentinels — read the existing file first, extract fenced regions between `<!-- KEEP -->` and `<!-- /KEEP -->`, and reinsert them at the same section anchor on write. If a KEEP region has no matching anchor in the newly composed body, keep it at the section tail and warn the user.

### 8. Log material decisions
If composing forced a real design choice (e.g. picking one of two plausible target file paths, choosing which of two reused endpoints a page consumes), append a `DEC-###` row to `shared-context/decision-log.md`. Composition choices that are pure arrangement (order of sections, choice of table vs list) don't need a decision — only technical choices that later reviewers might contest.

### 9. Report per feature
Return: features composed vs skipped-unchanged (with reason each), the size per feature, open items surfaced (grouped by feature), and any features where the repo-scan preflight left file paths as `TBD`. Link to each `tl-plan.md`. If any feature refused to compose (missing units, size overflow, unresolved TBD in a critical field), name it and the reason — never silently swallow.

## Completion criteria

A feature is composed when: `tl-plan.md` exists at `context/features/<slug>/tl-plan.md` with the correct frontmatter; the file contains exactly the five subsections (Build sequence · API endpoints · Database modifications · Frontend UI · Touch points); every endpoint the feature owns has its Execution-order and Refusals tables with one row per distinct response `message`; the Database modifications table lists only the fields this feature writes with a one-line "Never touched" boundary; every UI surface is named by role with its API wiring; every reuse in Touch points is named by role; the file is ≤ 60 KB; and none of the Rules 1–11 above are violated.

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
