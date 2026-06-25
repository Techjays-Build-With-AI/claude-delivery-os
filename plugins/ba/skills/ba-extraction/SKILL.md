---
name: ba-extraction
description: What the BA Agent extracts from eligible artifacts and how it records the results. Read before extracting BA intelligence during /ba:intake. Lists the 20 extraction categories, the living scope document structure, and the schema of every supporting register and shared-context file.
---

# BA intelligence extraction

Extraction reads the **normalized summaries** under `artifacts/` (produced during ingest — see `ba-classification`), not the raw originals. For each eligible source, extract the categories below, assign a stable ID and confidence value (see `delivery-os-conventions`), and cite the source as `[SRC-### › <original location>]` — traceability runs original → summary → scope item, so the citation always names the untouched original.

## The 20 extraction categories

1. Business objectives
2. Stakeholders and actors
3. Current workflows
4. Future expectations
5. Functional requirements
6. Business rules
7. Data entities
8. Integrations
9. Reports and dashboards
10. Notifications and alerts
11. Permissions and roles
12. Pain points
13. Manual effort
14. Exceptions and edge cases
15. Compliance and security requirements
16. Examples and scenarios
17. Terminology and glossary items
18. Assumptions
19. Clarifications needed
20. Contradictions with existing scope

## Living scope document (`ba-output/scope.md`)

**The scope document is the frozen baseline deliverable and MUST conform to the Techjays D&D Scope Document Template** (`docs/D&D Documentation/02 - Scope Document Template.docx`). It is **module-centric**, not a flat list. The full markdown template ships at `delivery-os-core/templates/ba-output/scope.md` — always start from it and keep every heading.

Structure (do not reorder, do not drop headings):

1. **Cover block** — Project, Client, Version, Date, Status (Draft / In Review / Approved).
2. **§1 Scope Statement** — one or two sentences defining the delivery boundary.
3. **§2 Module Breakdown** — `| Module | One-line purpose | Specified in §3? |`. Decompose the business into modules (typical set: Intake, Processing, Validation, Approval, System Updates, Exception Handling, Reporting, Admin, Integrations).
4. **§3 Module Requirements** — one `### 3.x Module: <Name>` sub-section **per module**, each with all nine sub-headings, even if "None":
   - 3.x.1 Current → Future State (current = actors/triggers/systems/manual steps/pain points; future = AI/deterministic/human split) — cite sources.
   - 3.x.2 In Scope / Out of Scope.
   - 3.x.3 Functional Requirements table → `| ID | Requirement | Resp. | Pri. | Acceptance criteria |`.
   - 3.x.4 AI / Automation Responsibilities (AI does · confidence threshold & fallback · human-in-the-loop).
   - 3.x.5 Business Rules.
   - 3.x.6 Data Fields → `| Field | Type | Req. | Source / validation |`.
   - 3.x.7 Integrations.
   - 3.x.8 Exception Handling → `| Exception | Handling |`.
   - 3.x.9 Acceptance Criteria (tie to the requirement IDs above).
5. **§4 AI vs. Deterministic Responsibility Split** — the engagement-wide dividing line.
6. **§5 User Roles & Permissions** — `| Role | Description | Key permissions |`.
7. **§6 Global Out-of-Scope** — cross-cutting exclusions.
8. **§7 Assumptions & Dependencies** — **reference the RAID Register; do not duplicate.** Assumptions and dependencies are owned there.
9. **§8 Approval & Scope Freeze** — 8.1 Exclusions Acknowledgement · 8.2 Change-Control Note · 8.3 Client Sign-off table. Draft now; completed at scope-freeze (status → Frozen).

### Scope-document conventions (must match the template)

- **Responsibility (`Resp.`)** controlled values: `AI` (AI capability) · `DET` (deterministic logic) · `HUM` (human action).
- **Priority (`Pri.`)** controlled values (MoSCoW): `M` (Must) · `S` (Should) · `C` (Could) · `W` (Won't-this-phase).
- **Requirement IDs** are module-prefixed: `<MODULE>-<FR|AI|DET|HUM>-<NN>` (e.g. `INTK-AI-02`, `VALD-DET-01`). The module prefix is a short uppercase abbreviation; `NN` is sequential within the module. These IDs are the canonical requirement IDs used in `requirement-register.md`.
- **"Ask the client" cues**: every open question in the scope is also logged in `clarification-log.md` (and feeds RAID Open Questions `Q-##`).
- Keep capability-level only — detailed testable specs are deferred to the SRS.

### Assembling the module-centric scope from the registers

The registers are your flat working memory; the scope is the assembled deliverable. To build §3:
- Group `requirement-register` rows and `workflow-register` rows by module → one §3.x block each.
- Pull the module's business rules from `business-rule-register`, data fields from `data-register`, integrations from `integration-register`, exceptions from edge-case extractions.
- Route **assumptions** → RAID Assumptions (`A-##`, fed by `assumption-register.md`); **dependencies** → RAID Dependencies (`D-##`); **open questions / "Ask the client"** → RAID Open Questions (`Q-##`, fed by `clarification-log.md`); **risks/contradictions** → RAID Risks (`R-##`). §7 of the scope only *references* these.

Track scope evolution in `change-log.md` (not inside the deliverable), and bump the cover-block **Version** as maturity advances (Draft → In Review → Approved, mapped from frontmatter `status`: Draft/Emerging/Reviewed/Frozen).

## Supporting registers (`ba-output/`)

Each register is a Markdown file with frontmatter + a table. Suggested columns:

| Register | Key columns |
|---|---|
| `requirement-register.md` | REQ ID, Requirement, Module, Source, Confidence, Status, Open Questions |
| `workflow-register.md` | WF ID, Name, State (current/future), Trigger, Actors, Steps, Systems, Outputs, Exceptions, Source |
| `business-rule-register.md` | BR ID, Rule, Applies To, Source, Confidence, Clarification |
| `example-register.md` | EX ID, Scenario, Maps To (WF/REQ), Source, Why It Matters |
| `data-register.md` | DATA ID, Entity, Fields, Source System, Sensitivity, Used For, Open Questions |
| `integration-register.md` | INT ID, System, Purpose, Direction, Data Exchanged, Dependency, Risk |
| `assumption-register.md` | ASM ID, Assumption, Reason, Risk, Validation Needed |
| `clarification-log.md` | CLR ID, Question, Category, Raised By Run, Status, Answer |
| `contradiction-log.md` | CON ID, Conflicting Statements, Sources, Impact, Resolution Status |
| `change-log.md` | Date, Intake Run, Summary of Changes |
| `indexing-assistance-needed.md` | Item, Why, Recommended Usage Mode, Status |

> Source tracking (what used to be `artifact-map` / `artifact-ledger` / `source-classification`) now lives in the **`intake.index.md` registry** — see `ba-classification`. Don't recreate those files.

## Shared-context files (`shared-context/`)

- `project-profile.md` — core project info
- `glossary.md` — business terms, acronyms, client vocabulary
- `stakeholder-map.md` — names, roles, teams, involvement
- `system-landscape.md` — systems, tools, platforms, integration touchpoints
- `decision-log.md` — confirmed decisions (DEC) and their impact

## Intake run summary (`ba-output/intake-runs/run-###.md`)

Sections: Run Details (date, mode, input index, scope version) · Artifacts Scanned (totals by status) · Sources Processed table · New Information Identified · Scope Updates Made · Registers Updated · Contradictions Found · Clarifications Added · Indexing Assistance Needed · Risk Notes · Next Recommended Actions.
