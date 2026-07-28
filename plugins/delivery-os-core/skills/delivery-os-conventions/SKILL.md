---
name: delivery-os-conventions
description: The Techjays Delivery OS shared document contract. Read this before producing or consuming any Delivery OS document (scope, registers, shared-context, run summaries). Defines the project workspace layout, the document frontmatter standard, stable ID conventions, and the shared vocabulary (artifact statuses, confidence values, usage modes) that every agent — ba, doc, tl, qa — must speak so their outputs stay interoperable.
---

# Delivery OS — Shared Document Contract

This is the single source of truth that makes Delivery OS documents **shareable across agents and across weeks**. The BA Agent produces documents today; the Doc, TL, and QA agents consume them later. They only interoperate if every agent honors this contract.

> **Contract version: 1.2.** Bump `schema_version` in document frontmatter and update this file together when the contract changes.
>
> **1.1 (use-case model).** Made **use cases** first-class: added the `<MODULE>-UC-NN` id and `use-case-register.md`; the scope §3.x now carries a **§3.x.3 Master Flow** and a **§3.x.4 Use Cases** layer (renumbered through §3.x.11); added the **Mermaid diagram convention** (§8) where Mermaid is the living source and the Doc Agent's branded SVG swimlane is its projection. The change is **additive** — a `schema_version: 1.1` document remains readable; new documents are written at `1.1`.
>
> **1.2 (eval layer).** Added the applied-AI **eval** layer: the `EVAL-<AREA>-NN` id (§3), the `context/evals/` sub-tree (§1), and the *applied-AI / LLM feature* classification (§5) that gates it. The TL's `tl-feature-planning` **designs** eval units for AI-bearing features, the dev `feature-delivery-loop` **runs and inspects** them, and QA's harness hosts them — see the core **`eval-engineering`** skill. Additive — deterministic features are unaffected.

---

## 1. Workspace layout

Every Delivery OS project lives under a **single named container folder** (so the user can see exactly what Delivery OS owns, and delete one folder for a clean slate). Agents read and write **only** at these paths.

```text
<project-name>/                  # the one container — everything Delivery OS owns lives here
├── README.md                    # what init created + how to use it (the workspace manifest)
├── intake.index.md              # LIVING source registry — maintained by /ba:scope (human-editable)
├── artifacts/                   # generated normalized summaries — categories created on demand
│   ├── <category>/              # emergent (e.g. meeting-transcripts/, requirements/) — NOT pre-made
│   │   └── <name>.summary.md    # markdown summary of one source doc (traces to the original)
│   └── ...
├── shared-context/              # cross-agent context (BA writes, everyone reads)
│   ├── project-profile.md
│   ├── glossary.md
│   ├── stakeholder-map.md
│   ├── system-landscape.md
│   └── decision-log.md
├── ba-output/                   # Business Analyst Agent outputs
│   ├── scope.md                 # the living scope document (primary handoff)
│   ├── client-questions.md      # clean, handover-ready open questions for the client
│   ├── requirement-register.md
│   ├── workflow-register.md
│   ├── use-case-register.md
│   ├── business-rule-register.md
│   ├── example-register.md
│   ├── data-register.md
│   ├── integration-register.md
│   ├── assumption-register.md
│   ├── clarification-log.md
│   ├── contradiction-log.md
│   ├── indexing-assistance-needed.md
│   ├── change-log.md
│   └── intake-runs/
│       └── run-001.md ...
├── context/                     # shared implementation context (the whole build team reads)
│   ├── features/                # BA feature breakdown (ba-feature-breakdown)
│   │   ├── feature-index.md
│   │   └── <feature-slug>/ …
│   ├── frontend/                # TL feature planning (tl-feature-planning)
│   │   ├── page-index.md
│   │   └── pages/<area>/<page-slug>.md          # PAGE-<AREA>-NN
│   ├── backend/
│   │   ├── endpoint-index.md
│   │   └── domains/<domain>/endpoints/<slug>.md # EP-<AREA>-NN
│   ├── database/
│   │   ├── entity-index.md
│   │   └── entities/<entity-slug>.md            # ENT-<AREA>-NN → DATA-###
│   └── evals/                # TL eval design for applied-AI features — dev runs these
│       ├── eval-index.md
│       └── <feature-slug>/<eval-slug>.md        # EVAL-<AREA>-NN → verifies an AC, exercises EP-/ENT-
├── doc-output/                  # Doc Agent outputs (Phase 2) — created on demand
├── tl-output/                   # TL Agent outputs (Phase 3) — created on demand
└── final/                       # approved, client-facing deliverables
```

The `context/` tree is the shared implementation-context layer, distinct from each agent's private `*-output/`. The BA writes `context/features/`; the TL's `tl-feature-planning` skill writes the `frontend/`, `backend/`, and `database/` sub-trees and links them into a bidirectional graph (page → endpoint → entity, and back), and — for **applied-AI features** — also designs the `evals/` sub-tree of runnable verifiers (see the core `eval-engineering` skill). It is created on demand by the first skill that writes to it — `init` does not pre-make it.

### Output-folder creation rule
`/delivery-os:init` seeds only the BA-phase essentials — `shared-context/` and `ba-output/` — because the Business Analyst runs immediately after init. Every **downstream** agent creates its own output folder the first time it produces something: `tl-output/` on the first `/tl:review`, `doc-output/` on the first Doc run, `qa-output/` later. This is deliberate — it keeps a fresh workspace minimal and avoids empty, speculative folders for agents a given project may never use. An agent must therefore create its output folder if absent, never assume `init` made it.

### 1.b Jetrix binding — `.jetrix/` (owned by the **jetrix** plugin)

A project's delivery context can be centralized in **Jetrix**, in which case Jetrix is the **single source of truth** for all project context (glossary, scope, registers, feature breakdown, and the `context/` graph) and the local `.jetrix/` folder is a disposable **working copy**. Binding a workspace and syncing it are owned by the separate **`jetrix`** plugin — read its **`jetrix-sync`** skill for the full contract: `.jetrix/project.json` (committed identity + app/environment→branch wiring), the gitignored incremental read-through cache, and the pull/push model. Commands: `/jetrix:init` (bind), `/jetrix:pull` (refresh the cache from Jetrix, incremental), `/jetrix:push` (publish local work back as structured records — upsert by stable id, transactional, pull-before-push). The canonical form in Jetrix is **structured records** (the IDs in §3); `scope.md` and the branded `.docx` are projections rendered from them. This is distinct from `/delivery-os:init`, which scaffolds a local-only workspace and never touches `.jetrix/`.

### Source handling — reference, never copy or move
Original source files (local folders/files, Google Drive, etc.) **stay where they are**. The workspace never copies, moves, or deletes a user's originals. Intake only:
1. **records** each source in `intake.index.md` (its real location + classification + status), and
2. **generates** a normalized markdown summary under `artifacts/<category>/` for eligible sources.
So the workspace holds only the **index + generated summaries** — it is a knowledge layer *over* the user's files, not a copy of them.

### `intake.index.md` is the single source registry
It is **agent-maintained** (the user can still hand-edit it) and folds together what were previously separate artifact-map / artifact-ledger / source-classification files: each source's description, original location, detected category, usage mode (the classification + reason), summary path, content hash, and status all live in one registry. Add sources conversationally via `/ba:scope add "..."` — the agent classifies, summarizes, and registers them.

**Handoff rule:** an agent reads another agent's **published** files (`ba-output/`, `shared-context/`, `artifacts/`); it never reaches into another agent's working notes. `shared-context/` and `ba-output/scope.md` are the primary handoff surfaces.

---

## 2. Document frontmatter standard

**Every generated Markdown document** starts with YAML frontmatter so any consumer can validate compatibility before reading the body:

```yaml
---
doc_type: scope            # scope | requirement-register | use-case-register | glossary | run-summary | source-summary | intake-index | ...
schema_version: 1.1        # the contract version this file conforms to
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

A consuming agent that finds `schema_version` newer than it understands must **stop and warn** rather than guess.

---

## 3. Stable ID conventions

IDs are the threads that let one agent cite what another produced. They are **append-only** — never renumber, never reuse a retired ID.

| Entity            | Prefix | Example  | Lives in                     |
|-------------------|--------|----------|------------------------------|
| Requirement       | `<MODULE>-<FR\|AI\|DET\|HUM>` | INTK-AI-02 | requirement-register.md / scope §3 |
| Use case          | `<MODULE>-UC` | INVP-UC-01 | use-case-register.md / scope §3.x.4 |
| Workflow          | `WF`   | WF-001   | workflow-register.md         |
| Business rule     | `BR`   | BR-001   | business-rule-register.md    |
| Data entity       | `DATA` | DATA-001 | data-register.md             |
| Integration       | `INT`  | INT-001  | integration-register.md      |
| Example/scenario  | `EX`   | EX-001   | example-register.md          |
| Assumption        | `ASM`  | ASM-001  | assumption-register.md       |
| Clarification     | `CLR`  | CLR-001  | clarification-log.md         |
| Contradiction     | `CON`  | CON-001  | contradiction-log.md         |
| Decision          | `DEC`  | DEC-001  | shared-context/decision-log.md |
| Artifact source   | `SRC`  | SRC-001  | intake.index.md (registry)   |
| Feature           | `FEAT-<AREA>` | FEAT-SUP-001 | context/features/ (ba)   |
| Page              | `PAGE-<AREA>` | PAGE-SUP-01 | context/frontend/ (tl)    |
| Endpoint          | `EP-<AREA>`   | EP-SUP-02   | context/backend/ (tl)     |
| Entity            | `ENT-<AREA>`  | ENT-SUP-01  | context/database/ (tl) — realises a `DATA-###` |
| Eval              | `EVAL-<AREA>` | EVAL-SUP-01 | context/evals/ (tl) — verifies an AC, exercises EP-/ENT- (applied-AI features) |
| QA finding        | `QAF`  | QAF-001  | qa-output/test-audit-*.md (qa)   |
| Quality gate      | `QG`   | QG-001   | qa-output/quality-gates.md (qa)  |
| Initiative        | *(human slug)* | payments-v2 | feature frontmatter + feature-index (ba) |

### Initiative — grouping features by work batch (multi-developer)

An **initiative** groups the features produced by one scoping effort so a developer can focus on just their batch even when many developers' in-flight features share `context/features/`. It is a **human-named, lowercase-kebab slug** (`payments-v2`, `supplier-portal`), not a numbered ID — chosen by the developer when they run `/ba:features initiative=<name>` (auto-generated as `intake-<YYYY-MM-DD>` if omitted). It is stamped into every feature the run creates/updates (`initiative:` in `feature.md`/`status.md` frontmatter and an `Initiative` column in `feature-index.md`), and it is the filter `/tl:plan initiative=<name>` and `/dev:build initiative=<name>` use to act on only that group. On a re-run, an existing feature **keeps** its initiative unless a new one is passed explicitly — so grouping is stable across merges. A feature with no initiative is treated as ungrouped (`unassigned`).

The `context/` graph IDs (`FEAT-`/`PAGE-`/`EP-`/`ENT-`) carry a short uppercase **area** token and a sequence within that area/layer (`PAGE-SUP-01`, `EP-SUP-02`). A database entity **cites the BA `DATA-###`** it realises rather than inventing a parallel data ID; likewise endpoints cite `INT-###` for integrations. Never mint a `context/` ID that shadows a BA register ID.

IDs are zero-padded to 3 digits (functional-requirement `NN` is 2 digits within its module, per the scope template). Cross-references are written inline as the bare ID (e.g. "validated by EX-014" or "see WF-002").

**Requirement IDs** follow the Techjays Scope Document convention: `<MODULE>-<FR|AI|DET|HUM>-<NN>` where the module prefix is a short uppercase abbreviation (Intake → `INTK`, Validation → `VALD`), the middle token is `FR` or the responsibility code, and `NN` is sequential within that module. The same ID is used in `requirement-register.md` and in `scope.md` §3.x.5 so they trace 1:1.

**Use-case IDs** follow the same module-prefix convention: `<MODULE>-UC-<NN>` (e.g. `INVP-UC-01`), `NN` sequential within the module. A use case is a **distinct scenario or route** through a module — one that differs from its siblings in a *material* way (different steps, actors, business rules, systems, or outcome), not merely in a data value. The canonical use case lives in `scope.md` §3.x.4 (nested under its module) and in `use-case-register.md`; the two trace 1:1. Functional requirements, workflows, examples, and business rules cite the use case(s) they serve by ID, and a use case cites the requirements/workflows/examples/rules that realise it — so a route is traceable in both directions. See `ba-extraction` for the rule that decides when a branch becomes its own use case versus an alternative flow.

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

**Applied-AI / LLM feature** (does a feature need eval-engineering?):
A feature is **AI-bearing** when its behaviour depends on a model's output — generation, classification/extraction, ranking or semantic search, RAG, or agentic tool use — or it declares `ai_component: true` / cites an `INT-###` to an LLM/AI provider. AI-bearing features get an **eval layer** (`context/evals/`, `EVAL-<AREA>-NN`, see the `eval-engineering` skill); every other feature is **deterministic** and is proven by the dev acceptance-map alone. When it's genuinely unclear, record an **open question** rather than assuming — don't skip evals on a feature that turns out to be AI-bearing, or invent them for one that isn't.

---

## 6. Producer / consumer map

| Surface                              | Produced by | Consumed by        |
|--------------------------------------|-------------|--------------------|
| `intake.index.md` (source registry)  | ba (human-editable) | ba           |
| `artifacts/**/*.summary.md`          | ba          | ba (extraction)    |
| `shared-context/*`                   | ba          | doc, tl, qa        |
| `ba-output/scope.md`                 | ba          | doc, tl, qa        |
| `ba-output/requirement-register.md`  | ba          | doc, tl, qa        |
| `ba-output/use-case-register.md`     | ba          | doc, tl, qa        |
| `ba-output/integration-register.md`  | ba          | tl                 |
| `ba-output/data-register.md`         | ba          | tl                 |
| `context/features/*`                 | ba          | tl, doc, qa        |
| `context/frontend/*` `context/backend/*` `context/database/*` | tl (feature-planning forward, or codebase-map reverse for brownfield) | tl (spec-review), doc, qa, coding |
| `context/evals/*` (applied-AI features) | tl (feature-planning designs) | dev (feature-delivery-loop runs + inspects), qa (harness hosts) |
| `doc-output/*`                       | doc         | human, final       |
| `tl-output/*`                        | tl          | human, delivery    |
| `qa-output/quality-gates.md`         | qa          | dev (readiness gate + dev-validation) |
| `qa-output/test-audit-*` `qa-output/test-setup-plan.md` | qa | human, qa          |

When a downstream agent (doc/tl/qa) runs, it should prefer `ba-output/scope.md` as its primary input and **not re-run BA analysis** unless explicitly asked.

---

## 7. Canonical deliverable formats (Techjays D&D pack)

Client-facing deliverables conform to the Techjays **Design & Discovery** templates. These are the authority for structure and style; the markdown an agent maintains is the living source that the Doc Agent renders into the branded `.docx` at freeze time. The **Scope Document** template is bundled with this core plugin at `${CLAUDE_PLUGIN_ROOT}/templates/d&d/scope-document/` (versioned via its `manifest.json` + `CHANGELOG.md`); the rest still live in the repo `docs/D&D Documentation/` and will be bundled as their agents are built.

| Deliverable | D&D template | Maintained as | Owner |
|-------------|--------------|---------------|-------|
| Scope Document | **bundled** → `templates/d&d/scope-document/scope-document-template.docx` | `ba-output/scope.md` (module-centric) | ba |
| RAID Register | `docs/…/04 - RAID Register Template.docx` | assumption-register + clarification-log + contradiction-log (feeds A/D/R/Q rows) | ba |
| Executive Summary | `docs/…/01 - Executive Summary Template.docx` | `doc-output/` | doc (Phase 2) |
| Technical Architecture | `docs/…/03 - Technical Architecture Template.docx` | `tl-output/` | tl (Phase 3) |
| Implementation Plan | `docs/…/05 - Implementation Plan Template.docx` | `doc-output/` | doc (Phase 2) |

**RAID alignment** — the BA registers map onto the RAID Register's four registers:
`assumption-register.md` → Assumptions `A-##` · dependencies → Dependencies `D-##` · `contradiction-log.md` / risk notes → Risks `R-##` · `clarification-log.md` → Open Questions `Q-##` (classified: *Must close before estimate · Proceed with assumption · Minor implementation detail · Too uncertain (exclude/T&M) · Future phase*). Scope §7 only references RAID — it never duplicates these.

---

## 8. Diagram convention (Mermaid is the living source; branded SVG is the projection)

Flows are authored as **Mermaid** fenced code blocks directly in the markdown the BA maintains — a module master flow in `scope.md` §3.x.3, and a per-use-case flow in each §3.x.4 use case (and, downstream, in each feature's `workflow.md`). Mermaid is chosen because it is diffable, reviewable in a pull request, and renders in most markdown viewers, so the diagram evolves with the words around it instead of drifting out of date in a separate file. The **Doc Agent** renders these same flows into the branded **SVG swimlanes** of the Techjays deliverables at doc/freeze time (`doc-workflow`) — so Mermaid is the *source*, SVG is the *client-facing projection* of the same journey, never a second hand-authored diagram to keep in sync.

Authoring rules so the diagrams stay uniform and machine-mappable:

- Use `flowchart TD` (top-down) for a use-case route and `flowchart TD` or `LR` for a module master flow — pick one orientation per module and keep it.
- **Decision/branch points are diamond nodes** (`{...}`), and **every branch edge is labelled with the condition** that selects it (`-->|credit memo| ...`). In a module master flow, each terminal branch names the use case it leads to by ID and name, so the master flow and the nested use cases line up 1:1.
- Terminal/outcome nodes use rounded ends (`([...])`); systems of record or integrations referenced in a step name the `INT-###` they map to in the node text where it helps.
- Keep the master flow to the decision skeleton (trigger → branch points → which use case) and push step-level detail into each use case's own flow — the master answers *which route*, the use-case flow answers *how that route runs*.
- Fence every diagram as ` ```mermaid ` … ` ``` ` and keep the label text short; long prose belongs in the surrounding narrative, not inside a node.
