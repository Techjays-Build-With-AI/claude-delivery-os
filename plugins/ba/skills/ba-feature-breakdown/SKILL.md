---
name: ba-feature-breakdown
description: Convert a scope document and its supporting discovery artifacts into a structured, implementation-ready feature breakdown — one folder per feature, each holding the business context, implementation plan, workflow, acceptance criteria, dependencies, open questions, and status a developer, tech lead, QA engineer, or coding agent needs to start building. Use whenever the user asks to "break the scope into features", "create feature folders", "produce a feature breakdown", "make the scope implementation-ready", or hand the scope off to build. Decomposes the scope into independently understandable features sized to plan/build/test/release, identifies the expected pages, APIs, workflows, integrations, background jobs, events, and data entities, distinguishes confirmed requirements from assumptions / open questions / out-of-scope / future-phase, preserves traceability back to the source scope, and maintains a feature-index. It creates the implementation *context* that precedes development — it never writes production code, and it never fabricates behavior, UI, business rules, API contracts, schemas, or integrations the source material doesn't support; missing information becomes an explicit open question, not an invented requirement. Re-run it when scope changes, a feature is split/merged/deferred, or new stakeholder, technical, or QA input arrives.
---

# BA Feature Breakdown (scope → implementation-ready features)

You are turning an approved (or emerging) **scope** into the **implementation context** a build team needs before it writes a line of code. The scope answers *what the business wants*; the feature breakdown answers *what gets built, why, for whom, how the journey works, and what's still unknown* — decomposed into features a developer, tech lead, QA engineer, or coding agent can pick up **one folder at a time** and understand without re-reading the whole scope.

The defining behaviour of this skill is **implementation-readiness without invention**. You break the scope into features, and for each you write down the pages, APIs, workflows, integrations, jobs, events, and data entities it implies — but only as far as the source material supports. Where the scope is silent, you do **not** guess a business rule, an API contract, a schema, or a UI behaviour; you record it as an **open question** with an owner and an impact. A feature breakdown that quietly fills gaps with plausible-sounding requirements is worse than one that leaves them visible, because the invented requirement gets built.

This skill **does not write production code** and does not make technical-design decisions (that's the TL's job). Its single responsibility is to create the structured, traceable context that lets development begin.

## Operating contract

This produces **Delivery OS** context files. Read the **`delivery-os-conventions`** contract first if it isn't already in context — the frontmatter standard, the stable-ID rules, the source-citation form (`[SRC-### › <original location>]`), the controlled vocabulary, and the diagram convention (§8: Mermaid is the living source). The scope you consume is the module-centric **Techjays D&D scope** that `ba-extraction` produces (`ba-output/scope.md`), with its eleven sub-headings per module — including a **§3.x.3 Master Flow** and a **§3.x.4 Use Cases** layer; read `ba-extraction` if the expected scope structure isn't already in context, because your features map back to those modules, their `<MODULE>-<FR|AI|DET|HUM>-NN` requirement IDs, and their `<MODULE>-UC-NN` **use cases** (each a distinct scenario/route with its own flow and worked example). A use case is often the right size for a feature — or a small cluster of use cases becomes one — so carry the `UC-` ids into the feature and let each route's flow become an alternative flow in the feature's `workflow.md`.

**Output location.** The feature breakdown is written to a `context/` tree at the project root (a sibling of `ba-output/`, `shared-context/`, and `artifacts/`), because it is the shared *implementation context* the whole build team reads — not a BA-private register:

```text
context/
  features/
    feature-index.md
    <feature-slug>/
      feature.md
      implementation-plan.md
      workflow.md
      acceptance-criteria.md
      dependencies.md
      open-questions.md
      status.md
```

Feature folder names are **lowercase kebab-case** (`supplier-onboarding`, `outlet-discovery`, `proposal-generation`, `contract-approval`). Each feature gets **all seven files**, every time — an empty section reads "None identified yet", never a missing file. The exact schema for each file, and for `feature-index.md`, is in **`references/feature-file-templates.md`** — build every file from it so the folders stay uniform and machine-parseable. How to *decide* the feature set (sizing, feature kinds, the breakdown rules, and the completion bar) is in **`references/decomposition-guide.md`** — read it before you cut the scope into features.

If there's no Delivery OS workspace (no `ba-output/scope.md`, no `intake.index.md`), don't block: take the scope path the user gives you, create `context/features/` next to it, and note in the run summary that a standard workspace wasn't found. Keep the frontmatter either way; only the location changes.

## Workflow

### 0. Establish the initiative (work-batch grouping)
Take the **`initiative`** for this run from the user (`/ba:features initiative=<name>`) — a lowercase-kebab slug like `payments-v2` that groups the features this scoping effort produces, so a developer can later plan and build just their batch even when `context/features/` holds many developers' in-flight features. If none is given, auto-generate `intake-<YYYY-MM-DD>` (from the system clock) and tell the user what you chose so they can rename it. Every feature you **create** in this run is stamped with this initiative (`initiative:` frontmatter in `feature.md` and `status.md`, and the `Initiative` column in `feature-index.md`). On a re-run, a feature that already exists **keeps its existing initiative** unless the user explicitly passes a new one — so grouping stays stable across merges and re-runs. See `delivery-os-conventions` §3.

### 1. Read the whole scope, and the knowledge base behind it
Take the scope path from the user (default `ba-output/scope.md` when a workspace exists). The scope may be Markdown, `.docx`, or `.pdf` — use the `docx` / `pdf` skills to extract it if needed. **Read all of it before decomposing** — a capability introduced in §2 is specified in §3.x, bounded in §6 Global Out-of-Scope, and its open items live in the RAID registers. Then load the supporting context so your features are traceable and don't re-open settled questions:
- **`ba-output/requirement-register.md`, `workflow-register.md`, `business-rule-register.md`, `data-register.md`, `integration-register.md`** — the source of the requirement IDs, workflows, rules, entities, and integrations you cite in each feature. Link to these; do not copy them (Rule 3).
- **`ba-output/use-case-register.md`** — the scope's use cases (`<MODULE>-UC-##`), each a distinct route with its own flow and worked example. These are the primary input to a feature's `workflow.md`: the module master flow becomes the feature's overview flow, and each use case becomes an alternative flow. Carry the `UC-` ids into `feature.md` and cite them in acceptance criteria.
- **`ba-output/example-register.md`** — the client's shared examples/scenarios (EX-###); use them to sanity-check that a feature's journey and acceptance criteria can actually satisfy what the client showed you. Reuse the worked example already attached to a use case where one exists.
- **`ba-output/assumption-register.md`, `clarification-log.md`, `contradiction-log.md`** — assumptions already logged (ASM-###), questions already open (CLR-###), and known conflicts (CON-###). Reuse these IDs rather than minting new open questions for things already tracked.
- **`shared-context/`** — glossary, stakeholder-map, system-landscape, decision-log — for actor names, systems, and confirmed decisions (DEC-###).

Record which sources you consulted; it goes in the run summary so the reader knows the breakdown's evidentiary base.

### 2. Identify the business capabilities in scope
Work out the major business capabilities the scope delivers. Prefer the scope's own **§2 Module Breakdown / §3.x modules** as your starting unit — a module often *is* a feature or a small cluster of them. Where the scope is flatter, group requirements into coherent capabilities yourself and say you did. The goal at this step is a candidate list of capabilities, not yet the final feature set.

### 3. Decompose into features — sized to plan, build, test, and release
Turn the capabilities into **features** using `references/decomposition-guide.md`. A feature is a *meaningful business capability that can be planned, implemented, tested, and tracked* — a user-facing capability, a workflow stage, a reusable domain capability, a meaningful integration, an operational/admin capability, or a major reporting/approval/compliance/automation function. Apply the two sizing guards: not so **broad** that it can't be estimated, built, tested, or released as a unit; not so **small** that it has no business value on its own (a button, a single endpoint, a dropdown, a migration, an email template) — those are documented *inside* a feature, not as features. Classify each feature's **kind** (UI, workflow, integration, data/reporting, admin, AI/automation, cross-cutting), because the kind drives which context matters most (an integration feature lives on its data flows and failure modes; a UI feature on its pages, states, and roles).

### 4. Build each feature folder
For every feature, create the folder (`context/features/<feature-slug>/`) and write all seven files from `references/feature-file-templates.md`:
- **`feature.md`** — the primary business & product context: a stable **Feature ID** (`FEAT-<AREA>-NN`), its **initiative**, status, summary, business objective and problem solved, users, user value, in/out of scope, related workflows, pages, APIs/services, data entities, integrations, dependencies, assumptions, open questions, and **source references** back to the scope §/register IDs.
- **`implementation-plan.md`** — how the feature breaks into buildable *work areas* (not code): the proposed build areas with their expected pages, backend capabilities, data entities and integrations; a suggested delivery sequence; technical considerations; risks; an implementation-readiness verdict; and blocking items. No low-level code instructions unless the technical design already confirms them.
- **`workflow.md`** — the end-to-end business journey: an **overview flow** (a Mermaid `flowchart`, seeded from the module master flow §3.x.3) showing the trigger, happy path, and branch points; then the primary flow and the **alternative flows**, where each scope **use case** (§3.x.4) the feature covers contributes one alternative flow with its own Mermaid diagram and worked example; the business rules that govern it; and related features. Cite the `UC-`, `WF-`, and `BR-` ids inline.
- **`acceptance-criteria.md`** — testable, capability-level outcomes grouped by area; what "done" means for the business, tied to the requirements.
- **`dependencies.md`** — upstream, downstream, data, and integration dependencies, plus dependency risks.
- **`open-questions.md`** — the unresolved decisions as a table (`ID | Question | Owner | Impact | Status`), reusing `CLR-###` IDs where the question is already logged, minting `OQ-<AREA>-NN` for new ones. **Never** turn one of these into a confirmed requirement elsewhere.
- **`status.md`** — the operational tracker: current status, owners (Feature/Technical/QA, "Unassigned" until known), priority, target release, a development-progress table, current blockers, and last-updated date.

Fill each file from the scope and registers. When a section has no supported content, write "None identified yet" (or the labelled placeholder the template specifies) — don't invent, and don't delete the heading.

### 5. Mark every uncertainty explicitly
Use the controlled labels throughout: **Confirmed · Assumption · Open Question · Dependency · Risk · Out of Scope · Future Phase**. An item is *Confirmed* only when the scope or a register states it; anything you inferred is an **Assumption** (log it, note the risk); anything the scope leaves genuinely undecided is an **Open Question** (owner + impact). This is the line that keeps the breakdown honest: never promote an assumption to a requirement.

### 6. Wire up dependencies and preserve traceability
Identify dependencies **between** features (Supplier Approval depends on Supplier Onboarding; RFP Generation depends on Outlet Discovery) and record them in both features' `dependencies.md` and in the index. Every feature's `feature.md` must carry **Source References** back to the scope section and/or the register IDs it came from — traceability runs scope → feature, and no scope item may be silently dropped. Where you reference a page, API, or data entity that lives in another context file, **link to it, don't duplicate** the contract or schema (Rule 3).

### 7. Create / update the feature index
Write `context/features/feature-index.md` — the one-row-per-feature table (`Feature ID | Feature | Initiative | Status | Priority | Dependencies | Folder`). Fill the `Initiative` column from each feature's stamp. On a **re-run**, update it in place: add new features (with this run's initiative), update changed ones (preserving their existing initiative unless a new one was explicitly passed), and keep retired features visible with a status (e.g. `Merged into …`, `Deferred`) rather than deleting the row — the index is the map of the whole breakdown.

### 8. Support incremental refinement (re-runs)
The first breakdown needn't be perfect. When the scope changes, a stakeholder answers a question, technical design adds a constraint, UX shifts, QA finds an edge case, or a feature is split/merged/deferred/removed — re-run and **update in place**, preserving history where you can and clearly noting what changed (bump the feature's `status.md` "Last Updated", record the change, close the resolved open questions). Never blind-overwrite a feature folder; merge new understanding into it.

### 9. Summarise in chat
Give the user the headline: how many features you created/updated, the feature-index table, the cross-feature dependency highlights, the count of open questions raised (Blockers first, with owners), and any scope items you couldn't confidently place (raised as questions, not dropped). Link to `feature-index.md` and note that each feature folder is self-contained. Keep it tight — the detail lives in the files.

## Completion criteria

The breakdown is complete when **every major scope item maps to at least one feature**; every feature has its own folder with all seven files; every feature states its business purpose, users, workflow, acceptance criteria, dependencies, assumptions, and open questions; the features are indexed; each has a preliminary delivery sequence; cross-feature dependencies are documented; unresolved scope questions are visible and assigned where possible; **no source requirement is silently dropped**; and each feature is understandable by a coding agent without rediscovering the whole project. (`references/decomposition-guide.md` holds the full checklist.)

## Principles

- **Create context, don't write code.** Your deliverable is the implementation *context* that precedes development — features, journeys, boundaries, dependencies, and the questions still open. Technical design, schemas, and API contracts are the TL's; production code is the developer's.
- **Never fabricate.** No product behaviour, UI behaviour, business rule, API contract, data schema, or integration that the source material doesn't support. When the scope is silent, the honest output is an open question with an owner — not a confident-sounding requirement that will get built.
- **Every feature is independently understandable.** A developer should open one folder and know *what we're building, why, who uses it, what should happen, what depends on it, how we test it, and what's still unclear* — without reading the entire scope.
- **Preserve business value in every feature.** Don't carve out a pure technical component as a standalone feature unless it's a genuinely reusable business capability; otherwise it belongs *inside* a feature.
- **Link, don't duplicate.** Reference the pages, APIs, data entities, workflows, and integrations that live in other context files; don't copy their contracts or schemas into the feature folder.
- **Mark uncertainty explicitly and keep it marked.** Confirmed / Assumption / Open Question / Dependency / Risk / Out of Scope / Future Phase — and never let an assumption quietly become a confirmed requirement across a re-run.
- **Preserve traceability.** Scope → feature, every time; cite the source. No scope item may vanish without a trace.
- **Support refinement.** The breakdown is living. Re-run it as understanding changes, update in place, and make what changed visible.
