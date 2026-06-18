---
name: delivery-os-conventions
description: The Techjays Delivery OS shared document contract. Read this before producing or consuming any Delivery OS document (scope, registers, shared-context, run summaries). Defines the project workspace layout, the document frontmatter standard, stable ID conventions, and the shared vocabulary (artifact statuses, confidence values, usage modes) that every agent — ba, doc, tl, qa — must speak so their outputs stay interoperable.
---

# Delivery OS — Shared Document Contract

This is the single source of truth that makes Delivery OS documents **shareable across agents and across weeks**. The BA Agent produces documents today; the Doc, TL, and QA agents consume them later. They only interoperate if every agent honors this contract.

> **Contract version: 1.0.** Bump `schema_version` in document frontmatter and update this file together when the contract changes.

---

## 1. Workspace layout

Every Delivery OS project is a folder with this structure. Agents read inputs and write outputs **only** at these paths.

```text
project-name/
├── intake.index.md            # human-authored: declares artifact sources (BA input)
├── raw-artifacts/             # human-supplied source material
│   ├── client-requirements/
│   ├── meeting-transcripts/
│   ├── client-reference-docs/
│   ├── system-screenshots/
│   ├── process-maps/
│   ├── sample-data/
│   └── emails/
├── shared-context/            # cross-agent context (BA writes, everyone reads)
│   ├── project-profile.md
│   ├── glossary.md
│   ├── stakeholder-map.md
│   ├── system-landscape.md
│   └── decision-log.md
├── ba-output/                 # Business Analyst Agent outputs
│   ├── scope.md               # the living scope document (primary handoff)
│   ├── artifact-map.md
│   ├── artifact-ledger.md
│   ├── source-classification.md
│   ├── requirement-register.md
│   ├── workflow-register.md
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
├── doc-output/                # Doc Agent outputs (Phase 2) — created on demand
├── tl-output/                 # TL Agent outputs (Phase 3) — created on demand
└── final/                     # approved, client-facing deliverables
```

**Handoff rule:** an agent reads another agent's **published** files (`ba-output/`, `shared-context/`); it never reaches into another agent's working notes. `shared-context/` and `ba-output/scope.md` are the primary handoff surfaces.

---

## 2. Document frontmatter standard

**Every generated Markdown document** starts with YAML frontmatter so any consumer can validate compatibility before reading the body:

```yaml
---
doc_type: scope            # scope | requirement-register | glossary | run-summary | ...
schema_version: 1.0        # the contract version this file conforms to
produced_by: ba            # ba | doc | tl | qa | delivery-os
last_intake_run: run-003   # the run that last touched this file (omit if N/A)
status: Emerging           # see §5 maturity values
generated_at: 2026-06-18   # ISO date of last write
---
```

A consuming agent that finds `schema_version` newer than it understands must **stop and warn** rather than guess.

---

## 3. Stable ID conventions

IDs are the threads that let one agent cite what another produced. They are **append-only** — never renumber, never reuse a retired ID.

| Entity            | Prefix | Example  | Lives in                     |
|-------------------|--------|----------|------------------------------|
| Requirement       | `REQ`  | REQ-001  | requirement-register.md      |
| Workflow          | `WF`   | WF-001   | workflow-register.md         |
| Business rule     | `BR`   | BR-001   | business-rule-register.md    |
| Data entity       | `DATA` | DATA-001 | data-register.md             |
| Integration       | `INT`  | INT-001  | integration-register.md      |
| Example/scenario  | `EX`   | EX-001   | example-register.md          |
| Assumption        | `ASM`  | ASM-001  | assumption-register.md       |
| Clarification     | `CLR`  | CLR-001  | clarification-log.md         |
| Contradiction     | `CON`  | CON-001  | contradiction-log.md         |
| Decision          | `DEC`  | DEC-001  | shared-context/decision-log.md |
| Artifact source   | `SRC`  | SRC-001  | artifact-map.md / ledger     |

IDs are zero-padded to 3 digits. Cross-references are written inline as the bare ID (e.g. "validated by EX-014" or "see WF-002").

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

**Scope maturity** (document-level status):
`Draft` · `Emerging` · `Reviewed` · `Frozen`

---

## 6. Producer / consumer map

| Surface                              | Produced by | Consumed by        |
|--------------------------------------|-------------|--------------------|
| `intake.index.md`                    | human       | ba                 |
| `shared-context/*`                   | ba          | doc, tl, qa        |
| `ba-output/scope.md`                 | ba          | doc, tl, qa        |
| `ba-output/requirement-register.md`  | ba          | doc, tl, qa        |
| `ba-output/integration-register.md`  | ba          | tl                 |
| `ba-output/data-register.md`         | ba          | tl                 |
| `doc-output/*`                       | doc         | human, final       |
| `tl-output/*`                        | tl          | human, delivery    |

When a downstream agent (doc/tl/qa) runs, it should prefer `ba-output/scope.md` as its primary input and **not re-run BA analysis** unless explicitly asked.
