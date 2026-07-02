# Decomposition guide

How to decide the feature set: what a feature *is*, how to size it, how to classify its kind, the rules that keep the breakdown honest, and the bar for calling it complete. Read this before cutting the scope into features; use `feature-file-templates.md` for the files themselves.

---

## What a feature is

A **feature** is a meaningful business capability that can be **planned, implemented, tested, and tracked** as a unit. It usually represents one of:

- a user-facing business capability,
- a workflow stage,
- a reusable domain capability,
- a meaningful integration capability,
- an operational or administrative capability,
- a major reporting, approval, compliance, or automation function.

Good feature-level examples:

```text
Supplier Onboarding
Supplier Approval Workflow
Outlet Discovery and Recommendation
RFP Creation and Distribution
Proposal Generation
Contract Approval Workflow
User and Role Management
Notification Center
Audit History
CRM Synchronization
```

---

## Sizing — the two guards

Apply both before you commit to a feature.

**Guard 1 — not too broad.** If a capability can't be estimated, built, tested, and released as one coherent unit, it's a *capability area*, not a feature — split it. "Supplier Management" that covers onboarding, approval, compliance, payment setup, and performance scoring is four or five features, not one. A feature you can't picture a team finishing in a bounded slice of work is too broad.

**Guard 2 — not too small.** If an item has no standalone business value, it is **part of** a feature, not a feature. These are usually too small to stand alone:

```text
Create Supplier API
Edit Button
Supplier Status Dropdown
Database Migration
Email Template
```

Document them inside the relevant feature's `implementation-plan.md` (as a build area or backend capability). **Exception:** a technical component *is* a feature when it's a genuinely reusable business capability the whole system leans on — e.g. `Notification Center`, `Audit History`, `User and Role Management`, `Document Upload Capability`. The test is Rule 1: does it carry business value on its own?

When in doubt between one big feature and several small ones, prefer the decomposition that lets a team **estimate and release independently** — that's the unit the breakdown exists to produce.

---

## Feature kinds

Classify each feature; the kind tells you which context matters most and where the gaps usually hide.

| Kind | The context that makes or breaks it |
|---|---|
| **UI / screen** | Pages, states, validation, empty/error states, roles & permissions |
| **Workflow / process** | Triggers, actors, stages, state transitions, alternative flows, business rules |
| **Integration** | Systems touched, data flows & direction, ownership, failure modes, sync vs async |
| **Data / reporting** | Entities, sources, what's captured vs derived, aggregation, access |
| **Admin / operational** | Configuration, roles, audit, overrides |
| **AI / automation** | What's automated vs human, confidence/fallback, human-in-the-loop, edge cases |
| **Cross-cutting** | Where it's reused, who depends on it, versioning/compatibility |

A feature can have a primary kind and a secondary one (an approval *workflow* with a *UI* queue) — write down both if it clarifies the context.

---

## Breakdown rules

**Rule 1 — Preserve business value.** Every feature must explain its business value. Don't create a feature that only describes a technical component unless that component is a reusable business capability.

**Rule 2 — Keep features independently understandable.** A developer should open one feature folder and understand it without reading the whole scope. The folder must answer: *What are we building? Why? Who uses it? What should happen? What depends on it? How do we test it? What's still unclear?*

**Rule 3 — Link, do not duplicate.** Reference pages, APIs, data entities, workflows, and integrations that live in other context files; don't copy their contracts or schemas into the feature folder once those files exist. For example:

```md
Related Page:   ../../frontend/pages/suppliers/supplier-details.md
Related API:    ../../backend/domains/suppliers/endpoints/create-supplier.md
Related Entity: ../../data/tables/suppliers.md
```

**Rule 4 — Mark uncertainty explicitly.** Use the labels **Confirmed · Assumption · Open Question · Dependency · Risk · Out of Scope · Future Phase**. Never turn an assumption into a confirmed requirement.

**Rule 5 — Support incremental refinement.** The first breakdown needn't be perfect. Re-run when scope changes, new stakeholder input arrives, technical design adds constraints, UX changes, QA finds edge cases, or a feature is split / merged / deferred / removed. When updating, preserve history where possible and clearly identify what changed.

---

## Traceability & the no-drop rule

Every feature's `feature.md` carries **Source References** back to the scope section and/or the register IDs (`<MODULE>-FR-NN`, `WF-###`, `BR-###`, `DATA-###`, `INT-###`, `EX-###`) and, where relevant, the `[SRC-### › original]` citation. Traceability runs **scope → feature**. Before finishing, check the reverse: walk the scope's §2 module table and §3.x requirements and confirm **each maps to at least one feature**. A scope item with no feature is either a missed feature or an explicit out-of-scope/future-phase note — never a silent drop.

---

## Completion checklist

The feature breakdown is complete when:

- [ ] Every major scope item maps to one or more features.
- [ ] Every feature has a dedicated folder with all seven files.
- [ ] Every feature includes business purpose, user context, workflow, acceptance criteria, dependencies, assumptions, and open questions.
- [ ] Features are indexed in `feature-index.md`.
- [ ] Features have a preliminary implementation sequence.
- [ ] Cross-feature dependencies are documented in both features and the index.
- [ ] Unresolved scope questions are visible and assigned where possible (owner or `Unassigned`).
- [ ] No source requirement is silently dropped.
- [ ] Every feature is understandable by a coding agent without full rediscovery of the project.
