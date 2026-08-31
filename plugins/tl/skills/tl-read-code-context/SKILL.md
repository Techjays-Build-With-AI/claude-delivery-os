---
name: tl-read-code-context
description: Fast, precise lookup skill for answering ANY question about the codebase from the TL context graph — the single source of truth for what exists (endpoints / pages / entities / decisions) and how it connects. Auto-triggers whenever the user asks about the codebase in general terms — "what is EP-...", "how does X work", "which files own Y", "what's the schema for Z", "who calls this endpoint", "trace this feature", "where is X defined", "what does <endpoint id> do", "explain <feature slug>", "show me the graph for <area>". Reads `<repo>/context/code-context/` layer indexes (`backend-index.md` / `frontend-index.md` / `database-index.md`) + per-unit files, walks cross-references via `Called by` / `Data Access` / `Related Units`, and returns a cited answer with unit IDs and file paths so the user can jump to source. Multi-repo aware (reads `.jetrix/cache/repolocation.json` for repo paths). Refuses to fabricate — if the graph doesn't cover the code area, says so and points at `/tl:code-map` for brownfield reverse-map or `/tl:plan` for greenfield planning.
---

# TL Read Code Context (fast graph-backed answers to codebase questions)

You answer any question about the codebase by walking the **TL context graph** — the single source of truth for what exists across every mapped repo. You do NOT read source code directly to answer general questions; the graph is the map. You do NOT guess where the graph is silent; you point the user at the tool that fills the gap.

## When you auto-trigger

Trigger on any of these question shapes, whether the user is talking to `dev-agent`, `tl-agent`, `general-purpose`, or asking directly:

- **Unit-id lookup:** "what is EP-HCAL-01?", "explain PAGE-USR-03", "show me ENT-INV-04"
- **Feature trace:** "how does supplier onboarding work?", "trace FEAT-SUP-001", "walk me through the leave-request flow"
- **Cross-reference walks:** "who calls EP-USR-05?", "which pages consume EP-ORD-14?", "what entities does the invoice controller touch?"
- **Schema / contract lookup:** "what's the schema for the holidays collection?", "what fields does supplier have?", "what does POST /supplier accept?"
- **File-owner lookup:** "which files own the holiday domain?", "where does the auth gate live?", "which model file backs ENT-HCAL-01?"
- **Decision archaeology:** "why did we choose <X>?", "what was DEC-011 about?", "how did we decide on the partial unique index?"
- **Reuse discovery:** "do we have an auth gate we can reuse?", "which endpoint already handles duplicate detection?"
- **Coverage / gap discovery:** "what's not yet mapped in this repo?", "which endpoints don't have entity links?"

Do NOT auto-trigger on:
- Questions about non-code artifacts (BA scope, TL reviews, QA audits) — those live in `ba/` / `tl/reviews/` / `qa/`
- Requests to WRITE code, run tests, or plan new features — those are `/dev:build`, `/qa:setup`, `/dev:plan`
- Questions that clearly ask for the FILE contents of a specific known path — a direct `Read` is faster

## Operating contract

Read the **`delivery-os-conventions`** contract if not in context — you need the code-context tree layout (§1.b) and unit ID conventions (§3).

**Inputs (fast — 1 file each unless expanding):**

1. `.jetrix/cache/repolocation.json` — map from repo slug → absolute local path
2. `.jetrix/tl/code-map-registry.md` — one workspace-level pointer file naming each mapped repo, its context root, its area tokens
3. Per repo: `<repo>/context/code-context/code-context-index.md` — cross-layer summary (top-level entry for jumping to a layer)
4. Per layer: `<repo>/context/code-context/<layer>/<layer>-index.md` — filenames on disk are `backend-index.md` / `frontend-index.md` / `database-index.md` (their frontmatter doc_types are `endpoint-index` / `page-index` / `entity-index` respectively). Each row: `Unit ID | Path | Owner | Origin | Related Features` + a `File` column pointing to the per-unit file.
5. Per unit (endpoint / page / entity): `<repo>/context/code-context/<layer>/domains/<domain>/endpoints/<slug>.md` OR `<layer>/pages/<slug>.md` OR `<layer>/{tables,collections}/<slug>.md`. Body sections: `## Summary`, `## Contract` / `## Fields`, `## Called by`, `## Data Access`, `## Source References`, `## Related Units`.
6. `shared-context/decision-log.md` — for DEC-### lookup

**Outputs:**

- **Cited answer** in-chat. Every claim tagged with `[unit_id · file_path]` so the reader can jump. Include the actual snippet content, not a paraphrase.
- **No file writes.** This skill is read-only.
- **If graph is silent:** name the gap, tell the user which command fills it (`/tl:code-map <repo>` for brownfield reverse-map; `/tl:plan <feature>` for forward-planned units), stop.

## The lookup workflow — 4 phases, ≤5 file reads on the hot path

### Phase 1 — Classify the question (1-2 seconds)

Decide which of the 8 question shapes applies. That determines the entry point:

| Shape | Entry file |
|---|---|
| Unit-id lookup (`EP-`, `PAGE-`, `ENT-`) | Layer index of that unit's layer (backend/frontend/database) |
| Feature trace (`FEAT-`) | `features/<slug>/feature.md` frontmatter → walk related_apis / related_pages / related_entities |
| Cross-reference walk (`who calls X`, `what does X touch`) | The unit file at the source of the walk |
| Schema / contract lookup | The entity file (for schema) or endpoint file (for contract) |
| File-owner lookup | Layer index (has the `File` column) |
| Decision archaeology (`DEC-`, `why did we`) | `shared-context/decision-log.md` |
| Reuse discovery (`do we have`) | All three layer indexes, filter by domain / area token |
| Coverage / gap discovery | `<repo>/context/code-context/map-coverage.md` |

### Phase 2 — Resolve the repo(s) to read (1 file read: `repolocation.json`)

If the question implies a specific repo (via a repo-scoped area token like `EP-USR-*` where `USR` maps to backend), read only that repo's context tree.

If the question is workspace-wide (e.g. "trace this feature"), fan out across every mapped repo whose area tokens are relevant. Read `.jetrix/tl/code-map-registry.md` to know which repos have `HCAL` mapped, then read only those.

### Phase 3 — Walk to the answer (2-4 file reads)

**Unit-id lookup:**
1. Read layer index; find the row → get `File` path
2. Read the unit file → return `## Summary` + relevant contract section

**Feature trace:**
1. Read `features/<slug>/feature.md` frontmatter → get `related_apis / related_pages / related_entities`
2. Read each layer index once → get the file paths
3. Read the primary unit file (usually the entry-point endpoint or landing page) → return its Summary + walk into `## Called by` or `## Data Access` for the next hop

**Cross-reference walk:**
1. Read the source unit file → find `## Called by` / `## Data Access` / `## Related Units`
2. For each linked unit, read its file → return summarized chain with citations

**Schema lookup:**
1. Read `database-index.md` → find the entity row
2. Read the entity file's `## Fields` section

**Decision archaeology:**
1. Read `shared-context/decision-log.md`; grep for the DEC-###
2. If the decision references a unit, read that unit's file too for context

**Reuse discovery:**
1. Read all three layer indexes (single pass, in parallel if possible)
2. Filter rows by area token / domain / verb (e.g. "gate", "auth", "duplicate", "compliance")
3. For each candidate, read the unit's `## Summary` to confirm fit

**Coverage / gap discovery:**
1. Read `<repo>/context/code-context/map-coverage.md`
2. Return the gaps table verbatim with counts

### Phase 4 — Answer with citations, then stop

Return the answer with every claim citing `[unit_id · file:line]`. Include:

- Direct quote or paraphrase of the relevant graph section
- Cross-reference chain if the question implied one (e.g. "called by")
- Owner (from `Owner` column of layer index) — helpful for follow-up who-to-ask questions
- Origin status: `forward-planned` (planned but not built), `reverse-mapped` (brownfield), `implemented` (built + committed)
- **Path to source file** the unit maps to (from unit frontmatter `path:` field or Source References)

Then STOP. Do NOT proactively read production source files, run tests, or expand into "and here's how you might implement it". You're a lookup skill, not an implementation skill.

## Hard rules

**Rule 1 — Graph-first, never source-first.** For general codebase questions, the graph is authoritative. Read production source only when the graph explicitly points at it AND the user's question requires ground-truth verification (e.g. "does the code actually enforce BR-1?"). Even then, cite the graph unit that led you there.

**Rule 2 — No fabrication.** If the graph doesn't cover a unit / feature / decision the user asked about, say so explicitly and route to the command that fills it: `/tl:code-map <repo>` for brownfield, `/tl:plan <feature>` for greenfield, `/ba:features` for missing feature-level context. Never invent an EP-###, PAGE-###, or DEC-###.

**Rule 3 — Fast paths, no agentic search.** ≤5 file reads on the hot path for a single-unit question. If the question spans a feature or requires multi-hop walks, cap at ≤15 reads and report the walk so the user sees what you read. Never invoke `Grep` or `Glob` for a question a two-file walk (index → unit) resolves.

**Rule 4 — Cite everything.** Every answer names the unit ID and file path it came from. Users need to jump to source to verify. `EP-HCAL-01` alone is NOT a citation — it needs the file path.

**Rule 5 — Multi-repo aware, but scope-tight.** Read only the repos the question implies. A backend endpoint question doesn't need to read the frontend repo's context tree. Save the reads.

**Rule 6 — Honor read-only.** This skill NEVER writes files, never edits the graph, never runs code, never commits, never pushes. If a user asks you to fix, refactor, or extend, refuse and route to `/dev:plan` / `/dev:build`.

**Rule 7 — Do not narrate the walk.** In the answer, cite the units you visited but do NOT paste a step-by-step "I read file X, then file Y". Users want the ANSWER; the citations are the audit trail.

**Rule 8 — Stack-name discipline.** If the graph unit deliberately doesn't name a framework (per `tl-feature-compose` Rule 2), don't inject one in the answer. Describe by role, cite by ID.

**Rule 9 — When the graph disagrees with source (rare):** report the discrepancy. The graph might be stale (needs `/tl:code-map` refresh) or the source might have drifted (needs `/dev:commit` Stage 7 semantic merge). Naming the disagreement is the honest answer; picking a side isn't.

**Rule 10 — Empty-graph gracefulness.** If a repo has no `context/code-context/` tree, tell the user: "This repo isn't mapped yet. Run `/tl:code-map <repo>` to reverse-map the existing code, or `/tl:plan <feature>` to forward-plan new units."

## Return format

For a single-unit question:

```
**EP-HCAL-01 — Add Holiday** (`POST /api/holidays`)

Owner: backend-team
Origin: forward-planned (not yet implemented)
Source planned at: Inhouse-server/controllers/holiday.js
Layer index: Inhouse-server/context/code-context/backend/backend-index.md
Unit file: Inhouse-server/context/code-context/backend/domains/holiday/endpoints/add-holiday.md

Purpose: Adds one holiday for a date in the current calendar year or later,
refusing a date that already holds an active holiday and naming the holiday
that occupies it, attributed to the caller's verified email.

Contract:
  POST /api/holidays
  Body: { date: string (date), name: string (≤100 chars) }
  Success: 201 with { id, date, name, added_by, added_at }
  Refusals: 400 (MISSING_DATE, NAME_REQUIRED, NAME_TOO_LONG, DATE_TOO_EARLY)
            | 409 (DATE_ALREADY_HOLIDAY) | 401 (auth) | 500 (persistence)

Data access: writes to ENT-HCAL-01 (holidays collection)
Called by: PAGE-HCAL-01 (Holiday Calendar) — via HolidayApi.add()
Consumers of the graph: FEAT-HCAL-01

Related decisions:
  DEC-011 — RESTful routes for the Holiday domain
  DEC-013 — BR-1 enforced by a partial unique index (Add uses insert-then-catch)

Source references (Inhouse-server):
  controllers/holiday.js — this file will host the add handler
  validators/holidayValidator.js — this file will host the add-rule normative table
```

For a feature trace:

```
**FEAT-HCAL-01 Holiday Calendar Management** — traced across 2 repos

Backend (Inhouse-server) — 3 endpoints + 1 entity:
  EP-HCAL-01 POST /api/holidays          → add (writes ENT-HCAL-01)
  EP-HCAL-02 GET /api/holidays           → list by year (reads ENT-HCAL-01)
  EP-HCAL-03 DELETE /api/holidays/:id    → remove (writes ENT-HCAL-01)
  ENT-HCAL-01 holidays                   → realises DATA-001

Frontend (Inhouse-client) — 1 page:
  PAGE-HCAL-01 Holiday Calendar (/profile § holidays)
    Consumes: EP-HCAL-01, EP-HCAL-02, EP-HCAL-03

Sub-tasks (per /dev:plan Stage 2):
  1. backend (Inhouse-server) — EP-HCAL-01/02/03 + ENT-HCAL-01
  2. frontend (Inhouse-client) — PAGE-HCAL-01

Sequence: backend first (frontend depends on all 3 endpoints existing)

Related decisions: DEC-011 through DEC-015
Open questions: OQ-HCAL-03 (partial-unique scope), OQ-HCAL-01 (100-char boundary)

Files to open first:
  Inhouse-server/context/code-context/backend/backend-index.md
  Inhouse-server/context/code-context/database/database-index.md
  Inhouse-client/context/code-context/frontend/frontend-index.md
```

## Completion criteria

An answer is complete when:
- The question is answered from the graph (or the gap is named + routed)
- Every claim is cited with unit ID + file path
- No production source file was read beyond what was necessary for grounding
- ≤ 5 reads on the hot path (single-unit) OR ≤ 15 reads (multi-hop feature trace), and the walk is reported

## Skills / agents invoked

- No subagents (read-only; must reason with the full context in-line)
- No MCPs — reads local files only
- `shared-context/decision-log.md` for DEC-### lookups

## Principles

- **The graph is the map.** Source code is the terrain. For most questions, the map is what you need — the terrain is only for ground-truth verification.
- **Cite everything.** A cited claim can be verified; an uncited claim is a fabrication risk.
- **Fast paths.** A question that maps to a two-hop walk should not become a three-hop walk. Don't over-read.
- **Route on gaps.** If the graph is silent, that's a signal — route to the command that fills it. Never guess.
- **Read-only, always.** This skill never writes. If asked to modify, refuse and route.
- **Stack-name discipline.** The graph deliberately doesn't leak framework names. Don't inject them in the answer.
- **Empty graph is not empty answer.** Even when the graph is silent, the routing to `/tl:code-map` OR `/tl:plan` is itself the answer.
