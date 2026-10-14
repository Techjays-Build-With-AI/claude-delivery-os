---
name: ba-extraction
description: What the BA Agent extracts from eligible artifacts and how it records the results. Read before extracting BA intelligence during /ba:scope. Lists the 20 extraction categories, the living scope document structure, and the schema of every supporting register and shared-context/ file.
---

# BA intelligence extraction

**Read the track you were given before anything else.** It arrives as a name, never a letter: `client-requirement` or `task-ba-plan`.

**`client-requirement`** behaves as this file describes throughout. **`task-ba-plan`** is internal work with no client, and changes four things:

- **Questions for the requirement's owner go to `ba/open-questions.md`**, not `client-questions.md` — there is no client, and the file name is the only thing telling a reader who is expected to answer.
- **Current state comes from the code**, read per the area the requirement touches, not from a question to the user.
- **Omit a §3.x dimension that does not apply**, rather than writing it with "None".
- **No client examples exist**, so `examples.md` is usually empty and example-validation is not a finding against the scope.

No track given is `client-requirement`. If the work plainly has no client, say so rather than silently producing a client packet nobody will send.

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

## Before you extract

Three passes, in this order, before any category is pulled. Each is short; skipping them is what produces a scope that reads fluently and is wrong.

### 1 · Inventory the sources, and say what you did with each one

List every eligible source in `artifacts/` with its `SRC-###`, and after extraction state, per source, whether it contributed to the scope and where. **Report the ones that contributed nothing.** A source that produced no `SRC-###` citation anywhere is either irrelevant — fine, say so in one line — or it was not read, which is the failure this pass exists to catch. The run summary carries the list.

This reports; it does not fail the run. A source with nothing to give is a normal outcome, and a run that halts on it would be worse than one that names it.

### 2 · Build the glossary before the requirements

Pull category #17 (terminology) first, across every source, and settle each term **before** writing requirements against it. The client's word for a thing is usually a domain object with rules attached — "shift", "cycle", "settlement", "approval" — and two sources rarely mean the same thing by it. Where they do not agree, that is a `CON`, not a wording preference: a requirement written over an unsettled term is a requirement that will be built twice.

Use the client's term throughout, including in module and use-case names. Where a term stays ambiguous, raise it through the **question gate** and keep using it verbatim in the meantime — never substitute a synonym of your own, because a renamed thing cannot be matched back to what they said.

### 3 · Write the understanding brief, and put it where they will read it

Before the module breakdown, write a short brief — roughly half a page — of what you understand the work to be: the business problem in the client's own framing, who it is for, what changes when it ships, and the three or four facts everything else rests on. It goes at the top of `ba/scope.md`, under the cover block, ahead of §1.

This is the cheapest correction point in the whole engagement. A reader who disagrees with the brief disagrees in two minutes; the same disagreement found at §3.7 costs a rewrite. State what you are **unsure** of in the brief too, in plain words — not as ids. If the brief cannot be written because the sources do not say what the work is for, that is the finding, and it outranks every detailed question below it.


## Living scope document (`ba/scope.md`)

**The scope document is the frozen baseline deliverable and MUST conform to the Techjays D&D Scope Document Template** (`docs/D&D Documentation/02 - Scope Document Template.docx`). It is **module-centric**, not a flat list. The full markdown template ships at `delivery-os-core/templates/ba/scope.md` — always start from it and keep every heading.

Structure — **do not reorder**. Drop a heading only where this list says it is droppable (§0, §4b, and the §3.x sub-headings a module does not use); every other heading stays, empty or not, because the client signs against this shape:

1. **Cover block** — Project, Client, Version, Date, Status (Draft / In Review / Approved).
1b. **§0 What We Understand This To Be** — the understanding brief, written before the module breakdown (see *Before you extract*). It sits under the cover block and ahead of §1.
2. **§1 Scope Statement** — one or two sentences defining the delivery boundary.
3. **§2 Module Breakdown** — `| Module | One-line purpose | Specified in §3? |`. Decompose the business into modules (typical set: Intake, Processing, Validation, Approval, System Updates, Exception Handling, Reporting, Admin, Integrations).
4. **§3 Module Requirements** — one `### 3.x Module: <Name>` sub-section **per module**, carrying the sub-headings that apply to that module. **Omit one that does not** — do not write `3.x.6 AI / Automation — None` on a module with no model in it, or `3.x.9 Integrations — none` on one that calls nothing. An empty heading is not evidence it was considered; it is a line the reader has to skip, and on a module with four real dimensions the other seven bury them. Walk all eleven, write the ones that landed. Where a dimension would normally apply to work of this shape and deliberately does not — a module touching auth that leaves authz alone by decision — keep it and say why, because there its absence would read as an oversight.
   - 3.x.1 Current → Future State (current = actors/triggers/systems/manual steps/pain points; future = AI/deterministic/human split) — cite sources.
   - 3.x.2 In Scope / Out of Scope.
   - 3.x.3 **Module Master Flow** — a one/two-line narrative + a Mermaid `flowchart` of the whole journey and its **branch points**; each branch names the use case (§3.x.4) it leads to, so the master flow and the use cases stay 1:1.
   - 3.x.4 **Use Cases** — one `##### [MOD-UC-##]` block per distinct scenario/route, each with **Actor/Persona · Trigger · Preconditions · When this route applies · Explanation · Workflow · Flow diagram (Mermaid) · Worked example · Business rules · Edge cases & exceptions · Acceptance criteria · Source references**. This is where routing variants (e.g. invoice type = credit memo / net settlement / full-month) each get their own explained, exemplified, diagrammed treatment. Mirror every use case in `ba/registers/use-cases.md`.
   - 3.x.5 Functional Requirements table → `| ID | Requirement | Use Cases | Resp. | Pri. | Acceptance criteria |` (the Use Cases column ties each requirement to the route(s) it serves).
   - 3.x.6 AI / Automation Responsibilities (AI does · confidence threshold & fallback · human-in-the-loop).
   - 3.x.7 Business Rules (module-level / cross-cutting; a rule that governs only one route lives in that use case).
   - 3.x.8 Data Fields → `| Field | Type | Req. | Source / validation |`.
   - 3.x.9 Integrations.
   - 3.x.10 Exception Handling → `| Exception | Handling |` (cross-cutting; route-specific edge cases live inside their use case).
   - 3.x.11 Acceptance Criteria (tie to the use cases and requirement IDs above). **Scope every id to its use case** — `UC-01-AC-1`, not a bare `AC-1` repeated under every route. The dev loop maps each id to a test and re-verifies it at commit; a bare `AC-1` appearing in four use cases cannot be traced to one, so the evidence stops meaning anything. Cite the scoped id everywhere it is referenced, including the Functional Requirements table.
5. **§4 AI vs. Deterministic Responsibility Split** — the engagement-wide dividing line.
5b. **§4b Global Non-Functional Requirements & Constraints** — the cross-cutting statements that belong to no single module and are otherwise dropped on the floor: device and browser reach ("must work on mobile"), language and locale ("Arabic support", date and decimal format), data residency and retention ("data stays in the UAE"), volume and concurrency, availability windows, accessibility, and any regulatory constraint. One row each: the statement as given, its source, and whether it is Confirmed or Assumed. A requirement with nowhere to live is a requirement that disappears — this section is that place. Omit the section only when the sources genuinely carry none.
6. **§5 User Roles & Permissions** — `| Role | Description | Key permissions |`.
7. **§6 Global Out-of-Scope** — cross-cutting exclusions.
8. **§7 Assumptions & Dependencies** — **reference the RAID Register; do not duplicate.** Assumptions and dependencies are owned there.
9. **§8 Approval & Scope Freeze** — 8.1 Exclusions Acknowledgement · 8.2 Change-Control Note · 8.3 Client Sign-off table. Draft now; completed at scope-freeze (status → Frozen).

### Scope-document conventions (must match the template)

- **Responsibility (`Resp.`)** controlled values: `AI` (AI capability) · `DET` (deterministic logic) · `HUM` (human action).
- **Priority (`Pri.`)** controlled values (MoSCoW): `M` (Must) · `S` (Should) · `C` (Could) · `W` (Won't-this-phase).
- **Requirement IDs** are module-prefixed: `<MODULE>-<FR|AI|DET|HUM>-<NN>` (e.g. `INTK-AI-02`, `VALD-DET-01`). The module prefix is a short uppercase abbreviation; `NN` is sequential within the module. These IDs are the canonical requirement IDs used in `ba/registers/requirements.md`.
- **Use-case IDs** are module-prefixed too: `<MODULE>-UC-<NN>` (e.g. `INVP-UC-01`), `NN` sequential within the module. The same id is used in `scope.md` §3.x.4 and in `ba/registers/use-cases.md`.
- **Flow diagrams** are authored as Mermaid `flowchart` fenced blocks — a master flow in §3.x.3 and one per use case in §3.x.4. Mermaid is the living source; the Doc Agent renders the branded SVG swimlane from it (see `delivery-os-conventions` §8). Decision nodes are diamonds `{…}`, every branch edge is labelled with its condition, and master-flow branches name the use case id they lead to.
- **"Ask the client" cues**: every open question in the scope is also logged in `ba/logs/clarifications.md` (and feeds RAID Open Questions `Q-##`).
- Keep capability-level only — detailed testable specs are deferred to the SRS. **This defers detail nobody has given you; it never discards detail the client did.** A number, field list, threshold or rule stated in a source is kept as stated, in their words, however specific — "12 hours a day", "half-hour steps", "the Monday after the week ends". Generalising it to "daily limits apply" loses the only part nobody can reconstruct later. Defer the *unstated*; keep the *stated*.

### Use-case synthesis — turning branches into first-class routes

Use cases are **synthesized**, not extracted raw: you build them from what you already pulled (workflows #3, functional requirements #5, business rules #6, exceptions/edge cases #14, examples/scenarios #16, stakeholders/actors #2). A use case is a **distinct scenario or route** through a module. The whole point of this layer is that a requirement which "takes a different route depending on the type of X" is expanded into **one use case per route**, each with its own explanation, workflow, flow diagram, and worked example — rather than collapsed into a couple of business-rule rows.

**The branch rule — when a branch becomes its own use case:**

Split a branch into a **separate use case** when, depending on an input type/category/condition, the route differs in a *material* way — **different steps, different actors, different business rules, different systems, or a different business outcome.** Keep it as an **alternative flow or a business rule inside one use case** when the branch differs only by a **data value** while the steps stay the same.

- ✅ Separate use cases: an invoice that routes differently for **credit memo** vs **net settlement** vs **full-month invoice** — different validation, different posting, different approvals → `INVP-UC-01/02/03`.
- ❌ Not a use case: "invoice under $10k auto-approves, over $10k needs a manager" — identical steps, one differing threshold → a **business rule** on a single use case.
- ❌ Not a use case: "user can save as draft" mid-flow → an **alternative flow** documented inside the use case's workflow.

For each route you keep, write it up with all the §3.x.4 fields, mint a `MOD-UC-##` id, and register it in `ba/registers/use-cases.md`. Attach a **worked example** to every use case — reuse a client-shared scenario from `ba/registers/examples.md` (EX-###) where one exists; where none does, construct a realistic instance from the source facts and, if the underlying values are unconfirmed, raise a `CLR` rather than inventing business rules. Never fabricate a route the source material doesn't support; a suspected-but-unconfirmed route is an **open question**, not a use case.

### Assembling the module-centric scope from the registers

The registers are your flat working memory; the scope is the assembled deliverable. To build §3:
- Group `requirement-register` rows and `workflow-register` rows by module → one §3.x block each.
- **Identify the module's routes and write them as use cases (§3.x.4)** using the branch rule above; mint `MOD-UC-##` ids and mirror each in `ba/registers/use-cases.md`.
- **Draw the §3.x.3 Master Flow** as a Mermaid `flowchart`: trigger → branch point(s) → one labelled branch per use case → shared outcome. Keep it 1:1 with the use cases you wrote.
- **Give each use case its own Mermaid flow diagram** and its worked example (EX-### where available).
- Pull the module's business rules from `business-rule-register` (module-level into §3.x.7, route-specific into the owning use case), data fields from `data-register`, integrations from `integration-register`, cross-cutting exceptions into §3.x.10 and route-specific edge cases into the owning use case.
- In §3.x.5, fill the **Use Cases** column so every functional requirement points at the route(s) it serves.
- Route **assumptions** → RAID Assumptions (`A-##`, fed by `ba/registers/assumptions.md`); **dependencies** → RAID Dependencies (`D-##`); **open questions / "Ask the client"** → RAID Open Questions (`Q-##`, fed by `ba/logs/clarifications.md`); **risks/contradictions** → RAID Risks (`R-##`). §7 of the scope only *references* these.

Track scope evolution in `ba/logs/changes.md` (not inside the deliverable), and bump the cover-block **Version** as maturity advances (Draft → In Review → Approved, mapped from frontmatter `status`: Draft/Emerging/Reviewed/Frozen).

## Supporting registers (`ba/`)

Each register is a Markdown file with frontmatter + a table. Suggested columns:

| Register | Key columns |
|---|---|
| `ba/registers/requirements.md` | REQ ID, Requirement, Module, Source, Confidence, Status, Open Questions |
| `ba/registers/workflows.md` | WF ID, Name, State (current/future), Trigger, Actors, Steps, Systems, Outputs, Exceptions, Source |
| `ba/registers/use-cases.md` | UC ID, Use Case, Module, Actor, Trigger, Route Condition, Maps To (WF/REQ/EX/BR), Source, Confidence, Status, Open Questions |
| `ba/registers/business-rules.md` | BR ID, Rule, Applies To, Source, Confidence, Clarification |
| `ba/registers/examples.md` | EX ID, Scenario, Maps To (WF/REQ), Source, Why It Matters |
| `ba/registers/data.md` | DATA ID, Entity, Fields, Source System, Sensitivity, Used For, Open Questions |
| `ba/registers/integrations.md` | INT ID, System, Purpose, Direction, Data Exchanged, Dependency, Risk |
| `ba/registers/assumptions.md` | ASM ID, Assumption, Reason, Risk, Validation Needed |
| `ba/logs/clarifications.md` | CLR ID, Question, Category, Raised By Run, Status, Answer |
| `ba/logs/contradictions.md` | CON ID, Conflicting Statements, Sources, Impact, Resolution Status |

## The question gate

**Every question passes this before it is written — `CLR`, `SQ`, `OQ` alike.** One gate, one standard: a question raised by extraction, by the review and by the feature breakdown is the same question to the person answering, and three different bars produce three different lists of the same gaps.

**1 · Search for the answer first, and record where you looked.** Re-scan where the answer would live: the module's own §3.x sub-headings, the global §6 out-of-scope, `ba/registers/assumptions.md`, `ba/logs/clarifications.md`, **`shared-context/decision-log.md`** and the example register. Found → drop the question and correct the coverage it came from. Absent → keep it, with `checkedIn` naming what you searched. *A question the scope already answers is not a gap — it is a reading error, and it costs trust in every other question in the list.*

**2 · Name what changes if it stays unanswered.** `consequence` is exactly one of `estimate` · `scope` · `integrations` · `compliance` · `none`. `none` is a `Nit` at most; a question you cannot assign a consequence to is not a finding — drop it.

**3 · Would a different answer change what gets built, or what it is checked against?** If not, it is ceremony. This applies to every track and every question type, not only to internal work.

**4 · Is this already asked?** Before minting an id, match the question against the open items in `clarifications.md` and the current review's questions **by topic, not by wording**. The same gap found by extraction, by the review and by the breakdown is **one** question. Three ids for one gap is how a list of eighteen becomes a list of forty.

**Merge visibly, not silently.** Keep every occurrence as an **instance** on the surviving question — the use case or module it bites in, and the one-line form it takes there — rather than discarding it. A silent merge costs three things: the answerer cannot see that one answer settles three places and so weighs it as an isolated detail; a merge that was *wrong* can never be caught, because the question it swallowed no longer exists anywhere; and the resolution edits only one of the three sections, leaving the other two stale. Record them:

```
id:        SQ-012
question:  When someone is removed from a project after logging hours against it,
           what happens to those hours and that row — including in weeks already submitted?
instances:
  - TIME-UC-04  removed mid-week, week not yet submitted
  - TIME-UC-07  removed after submission, before approval
  - PAY-UC-02   removed after payroll has pulled the week
```

**Every question carries a `CLR`, and that is the id people see.** The `CLR` is the gap; `SQ` is the review's handle on it and `OQ` is the internal deliverable's view. A question matching an existing gap reuses its `CLR`; one matching nothing mints a new one. Minting a second family for a gap that already has a `CLR` is how one question ends up with three numbers and a reader cannot tell it is one question. See `delivery-os-conventions` → *One gap, one id*.

**The test for one question rather than several:** would a single answer settle all of them? If yes, it is one question with instances. If any instance would still be open after the answer, it is a separate question — do not merge it to shorten the list. Shortening the list is not the goal; one answer per real decision is.

Both `checkedIn` and `consequence` are required on every question that ships. **The gate is not softening** — the bar for a real gap is unchanged. Removing questions that were never gaps is what lets the rest carry full weight.



**A contradiction is not only two sources disagreeing.** It is also **facts you recorded that cannot all be true at once** — and these are the ones that get missed, because each fact is correct on its own and nothing flags the combination.

Before closing a module, read back what you wrote and check the chains actually resolve:

- **Does every identity or lookup chain reach the end?** "Sign-in matches the employee by email" and "the allocation table holds a free-text name with no reference to the employee register" are each true, and together they leave an unanswered step: *which key joins them?* Record `CON-###` and raise a `CLR` — do not leave two half-chains in separate sections and call it documented.
- **Does a rule survive the facts recorded elsewhere?** A rule promising "a rename keeps history" fails if the lookup it depends on matches on name. State the conflict rather than letting both stand.
- **Is a key you depend on actually guaranteed?** A field marked *optional* in one register cannot be the join key another section assumes. That is a contradiction, not a detail.

**The test:** if a developer followed the scope exactly, would they hit a step it does not define? If so it is a `CON` and a `CLR`, however well each individual fact is written.

| `ba/logs/changes.md` | Date, Intake Run, Summary of Changes |
| `indexing-assistance-needed.md` | Item, Why, Recommended Usage Mode, Status |

> Source tracking (what used to be `artifact-map` / `artifact-ledger` / `source-classification`) now lives in the **`intake.index.md` registry** — see `ba-classification`. Don't recreate those files.

**`ba/logs/clarifications.md` is the round-trip ledger.** The `Status` values are `Open` · `Answered` · `Closed` (or `Superseded`), and `Answer` holds the client's response once it arrives. `client-questions.md` (below) is generated *from* the `Open` rows; when an answer is folded in, set `Status`/`Answer` here and the question drops off the client deliverable.

## Before you ship the scope

Two passes over the assembled document, after §3 is written and before the run summary.

### Cross-module pass

Modules are written one at a time, so what falls between them is written by nobody. Walk the assembled scope once with only these questions:

- **Shared data** — does one module write a field another reads, and do both describe it the same way? A field defined in two §3.x.8 tables with different types or validation is a contradiction (`CON`), not a duplicate row.
- **Handoffs** — where one module's outcome triggers another's, does the receiving module's master flow actually show that trigger? A journey that ends in module A and resumes in module C with nothing in between has a gap where B should be.
- **Identity and matching** — where two modules refer to the same real-world thing (a person, an asset, an invoice), is there a stated key that joins them? A free-text name on one side and a code on the other is a defect found at build time unless it is raised here.
- **Roles** — does every actor named in a use case exist in §5, with permission to do what the use case has them doing?
- **Lifecycle** — for each entity, is creation, change and end-of-life owned by some module? Entities routinely get a create flow and no archive, delete or correction path.

Anything this pass finds is a scope item or a question through the **question gate** — never a silent fix in one module's text.

### Traceability pass

Two directions, both cheap, both catch different failures:

- **Forward — every source claim lands somewhere.** For each `SRC-###`, the facts it carried appear in a requirement, a rule, a use case, a register row, §6 out-of-scope, or an open question. A stated fact with no destination has been dropped.
- **Backward — every scope line cites a source.** Each requirement, business rule and acceptance criterion carries a `[SRC-### › …]` citation, or is marked `ASM` with its reasoning, or is an open question. **A line that is none of the three is invention**, and it is the single most expensive thing this skill can produce, because it reads exactly like the lines that are true.

Report both as counts in the run summary: sources with no destination, and scope lines with no source. Zero is the expected answer for the second.

## Client-facing questions deliverable (`ba/client-questions.md`)

A clean, **handover-ready** document generated every run from the **open** clarifications — the thing the team literally takes to the client. It is *not* the raw `ba/logs/clarifications.md`; it's grouped, prioritized, and has space for answers. Frontmatter `doc_type: client-questions`, `produced_by: ba`, plus `generated_at` and a count of open questions.

Structure:
- A one-line intro telling the reader to fill in answers and return the file (or share meeting notes), then run `/ba:scope add "answers in <path>"` to fold them back in.
- **Grouped by module / topic.** Under each group, one entry per open `CLR`:
  - `### CLR-### — <the question>  ·  Priority: <RAID class>` where the RAID class is one of *Must close before estimate · Proceed with assumption · Minor implementation detail · Future phase*.
  - **Why it matters:** one line on the scope/estimate impact.
  - **Answer:** _(blank for the client to fill)_.
- Order groups/questions so the **Must-close-before-estimate** items come first.

**`ba/open-questions.md` uses this same heading format.** Two question files with one shape, so a reader who has seen one can read the other.

Only `Open` clarifications appear. When the answer round-trip closes a `CLR`, it disappears from the next regeneration (optionally list recently-closed ones in a short "Recently answered" section for continuity). Keep it self-contained and jargon-light — a client, not just the delivery team, may read it.

## Owner questions deliverable (`ba/open-questions.md`)

**The internal track's counterpart to `client-questions.md`.** Same job, different answerer: there is no client, but someone gave you the requirement and they own the answers. Generated every run on the `task-ba-plan` track from the open clarifications, and **not written at all on a client-requirement run** — two question files in one workspace is two places to look and one of them will go stale.

**Do not confuse it with `features/<slug>/open-questions.md`**, which is a different file with the same base name: that one is per-feature, carries `OQ-<AREA>-###` ids with their own owner and impact in `open_questions[]` frontmatter, and is pushed to the Mission Control Dependencies tab. This file is workspace-level, carries `CLR` ids, and is read by a person rather than pushed anywhere.

Frontmatter `doc_type: owner-questions`, `produced_by: ba`, plus `generated_at` and a count of open questions.

Structure — deliberately the same shape as `client-questions.md`, so a reader who has seen one can read the other:

- A one-line intro naming **who is expected to answer** and what to do: fill in the answers and return the file, or answer them in `/ba:resolve`, which asks the same questions one at a time.
- **Grouped by module / topic.** Under each group, one entry per open `CLR`:
  - `### CLR-### — <the question>  ·  Priority: <RAID class>` — **the same heading format as `client-questions.md`**, the RAID class one of *Must close before estimate · Proceed with assumption · Minor implementation detail · Future phase*.
  - **Why it matters:** one line on the scope or estimate impact.
  - **Already checked:** where the answer was looked for and not found — the `checkedIn` value. On this track that usually includes code-context units, so the reader can say "it is in that file, you missed it" rather than answering something already settled.
  - **Answer:** _(blank)_.
- **Must-close-before-estimate first.**

**Mark the ones answerable here.** A question the person running the loop can settle themselves is labelled as such, because `/ba:resolve` will ask those directly and they should not be sent away to someone else. The rest name who they wait on.

Only `Open` clarifications appear. When an answer closes a `CLR`, it drops out of the next regeneration.

## Shared-context files (`shared-context/`)

- `project-profile.md` — core project info
- `glossary.md` — business terms, acronyms, client vocabulary
- `stakeholder-map.md` — names, roles, teams, involvement
- `system-landscape.md` — systems, tools, platforms, integration touchpoints
- `decision-log.md` — confirmed decisions (DEC) and their impact

## Intake run summary (`ba/intake-runs/run-###.md`)

Sections: Run Details (date, mode, input index, scope version) · Artifacts Scanned (totals by status) · Sources Processed table (one row per `SRC-###`, each marked **contributed** with where, or **nothing to contribute** with why) · Traceability (sources with no destination · scope lines with no source — expected zero) · Cross-Module Findings · New Information Identified · Scope Updates Made · Registers Updated · Contradictions Found · Clarifications Added · Indexing Assistance Needed · Risk Notes · Next Recommended Actions.
