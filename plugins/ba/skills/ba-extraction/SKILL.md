---
name: ba-extraction
description: What the BA Agent extracts from eligible artifacts and how it records the results. Read before extracting BA intelligence during /ba:scope. Lists the 20 extraction categories, the living scope document structure, and the schema of every supporting register and shared-context file.
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
4. **§3 Module Requirements** — one `### 3.x Module: <Name>` sub-section **per module**, each with all eleven sub-headings, even if "None":
   - 3.x.1 Current → Future State (current = actors/triggers/systems/manual steps/pain points; future = AI/deterministic/human split) — cite sources.
   - 3.x.2 In Scope / Out of Scope.
   - 3.x.3 **Module Master Flow** — a one/two-line narrative + a Mermaid `flowchart` of the whole journey and its **branch points**; each branch names the use case (§3.x.4) it leads to, so the master flow and the use cases stay 1:1.
   - 3.x.4 **Use Cases** — one `##### [MOD-UC-##]` block per distinct scenario/route, each with **Actor/Persona · Trigger · Preconditions · When this route applies · Explanation · Workflow · Flow diagram (Mermaid) · Worked example · Business rules · Edge cases & exceptions · Acceptance criteria · Source references**. This is where routing variants (e.g. invoice type = credit memo / net settlement / full-month) each get their own explained, exemplified, diagrammed treatment. Mirror every use case in `use-case-register.md`.
   - 3.x.5 Functional Requirements table → `| ID | Requirement | Use Cases | Resp. | Pri. | Acceptance criteria |` (the Use Cases column ties each requirement to the route(s) it serves).
   - 3.x.6 AI / Automation Responsibilities (AI does · confidence threshold & fallback · human-in-the-loop).
   - 3.x.7 Business Rules (module-level / cross-cutting; a rule that governs only one route lives in that use case).
   - 3.x.8 Data Fields → `| Field | Type | Req. | Source / validation |`.
   - 3.x.9 Integrations.
   - 3.x.10 Exception Handling → `| Exception | Handling |` (cross-cutting; route-specific edge cases live inside their use case).
   - 3.x.11 Acceptance Criteria (tie to the use cases and requirement IDs above).
5. **§4 AI vs. Deterministic Responsibility Split** — the engagement-wide dividing line.
6. **§5 User Roles & Permissions** — `| Role | Description | Key permissions |`.
7. **§6 Global Out-of-Scope** — cross-cutting exclusions.
8. **§7 Assumptions & Dependencies** — **reference the RAID Register; do not duplicate.** Assumptions and dependencies are owned there.
9. **§8 Approval & Scope Freeze** — 8.1 Exclusions Acknowledgement · 8.2 Change-Control Note · 8.3 Client Sign-off table. Draft now; completed at scope-freeze (status → Frozen).

### Scope-document conventions (must match the template)

- **Responsibility (`Resp.`)** controlled values: `AI` (AI capability) · `DET` (deterministic logic) · `HUM` (human action).
- **Priority (`Pri.`)** controlled values (MoSCoW): `M` (Must) · `S` (Should) · `C` (Could) · `W` (Won't-this-phase).
- **Requirement IDs** are module-prefixed: `<MODULE>-<FR|AI|DET|HUM>-<NN>` (e.g. `INTK-AI-02`, `VALD-DET-01`). The module prefix is a short uppercase abbreviation; `NN` is sequential within the module. These IDs are the canonical requirement IDs used in `requirement-register.md`.
- **Use-case IDs** are module-prefixed too: `<MODULE>-UC-<NN>` (e.g. `INVP-UC-01`), `NN` sequential within the module. The same id is used in `scope.md` §3.x.4 and in `use-case-register.md`.
- **Flow diagrams** are authored as Mermaid `flowchart` fenced blocks — a master flow in §3.x.3 and one per use case in §3.x.4. Mermaid is the living source; the Doc Agent renders the branded SVG swimlane from it (see `delivery-os-conventions` §8). Decision nodes are diamonds `{…}`, every branch edge is labelled with its condition, and master-flow branches name the use case id they lead to.
- **"Ask the client" cues**: every open question in the scope is also logged in `clarification-log.md` (and feeds RAID Open Questions `Q-##`).
- Keep capability-level only — detailed testable specs are deferred to the SRS.

### Use-case synthesis — turning branches into first-class routes

Use cases are **synthesized**, not extracted raw: you build them from what you already pulled (workflows #3, functional requirements #5, business rules #6, exceptions/edge cases #14, examples/scenarios #16, stakeholders/actors #2). A use case is a **distinct scenario or route** through a module. The whole point of this layer is that a requirement which "takes a different route depending on the type of X" is expanded into **one use case per route**, each with its own explanation, workflow, flow diagram, and worked example — rather than collapsed into a couple of business-rule rows.

**The branch rule — when a branch becomes its own use case:**

Split a branch into a **separate use case** when, depending on an input type/category/condition, the route differs in a *material* way — **different steps, different actors, different business rules, different systems, or a different business outcome.** Keep it as an **alternative flow or a business rule inside one use case** when the branch differs only by a **data value** while the steps stay the same.

- ✅ Separate use cases: an invoice that routes differently for **credit memo** vs **net settlement** vs **full-month invoice** — different validation, different posting, different approvals → `INVP-UC-01/02/03`.
- ❌ Not a use case: "invoice under $10k auto-approves, over $10k needs a manager" — identical steps, one differing threshold → a **business rule** on a single use case.
- ❌ Not a use case: "user can save as draft" mid-flow → an **alternative flow** documented inside the use case's workflow.

For each route you keep, write it up with all the §3.x.4 fields, mint a `MOD-UC-##` id, and register it in `use-case-register.md`. Attach a **worked example** to every use case — reuse a client-shared scenario from `example-register.md` (EX-###) where one exists; where none does, construct a realistic instance from the source facts and, if the underlying values are unconfirmed, raise a `CLR` rather than inventing business rules. Never fabricate a route the source material doesn't support; a suspected-but-unconfirmed route is an **open question**, not a use case.

### Assembling the module-centric scope from the registers

The registers are your flat working memory; the scope is the assembled deliverable. To build §3:
- Group `requirement-register` rows and `workflow-register` rows by module → one §3.x block each.
- **Identify the module's routes and write them as use cases (§3.x.4)** using the branch rule above; mint `MOD-UC-##` ids and mirror each in `use-case-register.md`.
- **Draw the §3.x.3 Master Flow** as a Mermaid `flowchart`: trigger → branch point(s) → one labelled branch per use case → shared outcome. Keep it 1:1 with the use cases you wrote.
- **Give each use case its own Mermaid flow diagram** and its worked example (EX-### where available).
- Pull the module's business rules from `business-rule-register` (module-level into §3.x.7, route-specific into the owning use case), data fields from `data-register`, integrations from `integration-register`, cross-cutting exceptions into §3.x.10 and route-specific edge cases into the owning use case.
- In §3.x.5, fill the **Use Cases** column so every functional requirement points at the route(s) it serves.
- Route **assumptions** → RAID Assumptions (`A-##`, fed by `assumption-register.md`); **dependencies** → RAID Dependencies (`D-##`); **open questions / "Ask the client"** → RAID Open Questions (`Q-##`, fed by `clarification-log.md`); **risks/contradictions** → RAID Risks (`R-##`). §7 of the scope only *references* these.

Track scope evolution in `change-log.md` (not inside the deliverable), and bump the cover-block **Version** as maturity advances (Draft → In Review → Approved, mapped from frontmatter `status`: Draft/Emerging/Reviewed/Frozen).

## Supporting registers (`ba-output/`)

Each register is a Markdown file with frontmatter + a table. Suggested columns:

| Register | Key columns |
|---|---|
| `requirement-register.md` | REQ ID, Requirement, Module, Source, Confidence, Status, Open Questions |
| `workflow-register.md` | WF ID, Name, State (current/future), Trigger, Actors, Steps, Systems, Outputs, Exceptions, Source |
| `use-case-register.md` | UC ID, Use Case, Module, Actor, Trigger, Route Condition, Maps To (WF/REQ/EX/BR), Source, Confidence, Status, Open Questions |
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

**`clarification-log.md` is the round-trip ledger.** The `Status` values are `Open` · `Answered` · `Closed` (or `Superseded`), and `Answer` holds the client's response once it arrives. `client-questions.md` (below) is generated *from* the `Open` rows; when an answer is folded in, set `Status`/`Answer` here and the question drops off the client deliverable.

## Client-facing questions deliverable (`ba-output/client-questions.md`)

A clean, **handover-ready** document generated every run from the **open** clarifications — the thing the team literally takes to the client. It is *not* the raw `clarification-log.md`; it's grouped, prioritized, and has space for answers. Frontmatter `doc_type: client-questions`, `produced_by: ba`, plus `generated_at` and a count of open questions.

Structure:
- A one-line intro telling the reader to fill in answers and return the file (or share meeting notes), then run `/ba:scope add "answers in <path>"` to fold them back in.
- **Grouped by module / topic.** Under each group, one entry per open `CLR`:
  - `### CLR-### — <the question>  ·  Priority: <RAID class>` where the RAID class is one of *Must close before estimate · Proceed with assumption · Minor implementation detail · Future phase*.
  - **Why it matters:** one line on the scope/estimate impact.
  - **Answer:** _(blank for the client to fill)_.
- Order groups/questions so the **Must-close-before-estimate** items come first.

Only `Open` clarifications appear. When the answer round-trip closes a `CLR`, it disappears from the next regeneration (optionally list recently-closed ones in a short "Recently answered" section for continuity). Keep it self-contained and jargon-light — a client, not just the delivery team, may read it.

## Shared-context files (`shared-context/`)

- `project-profile.md` — core project info
- `glossary.md` — business terms, acronyms, client vocabulary
- `stakeholder-map.md` — names, roles, teams, involvement
- `system-landscape.md` — systems, tools, platforms, integration touchpoints
- `decision-log.md` — confirmed decisions (DEC) and their impact

## Intake run summary (`ba-output/intake-runs/run-###.md`)

Sections: Run Details (date, mode, input index, scope version) · Artifacts Scanned (totals by status) · Sources Processed table · New Information Identified · Scope Updates Made · Registers Updated · Contradictions Found · Clarifications Added · Indexing Assistance Needed · Risk Notes · Next Recommended Actions.
