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

## Where to start — use cases, not modules

**Start from `ba/registers/use-cases.md`. One candidate feature per `<MODULE>-UC-##`.** Then group upward. The module is a grouping label, not the unit.

**The direction matters more than it looks.** Starting from modules and splitting down means each route has to argue its way out of the module it sits in, and the default outcome is one feature per module — which is the scope restated, not a breakdown. Starting from routes and grouping up means a *merge* has to justify itself, and the default outcome is the granularity the scope already established.

The work of deciding what is materially different is **already done**. `ba-extraction`'s branch rule split a requirement into separate use cases precisely when the route differs in a material way — different steps, different actors, different business rules, different systems, or a different business outcome. A routing variant that differed only by a data value never became a use case at all; it is a business rule on one route. So the use-case layer is the scope's own answer to "what is a distinct piece of work", and re-deciding it here produces a second, coarser answer that contradicts the first.

### The grouping test — same surfaces group, different surfaces split

A feature is a unit of **build, test and release**, and that unit is defined by the surfaces it touches:

> Two routes belong in **one** feature when they touch the **same pages, the same endpoints and the same entities**, and differ only in business rules. They are **separate** features when either needs a surface the other does not.

Checkable rather than a judgement call, and it reads from what the scope already carries — §3.x.8 data fields, §3.x.9 integrations, each use case's own workflow, and on an internal-track scope the `related_pages` / `related_apis` / `related_entities` resolved from the code.

Worked through:

```text
§3.2 Invoice Processing
    INVP-UC-01  credit memo          different validation, different posting
    INVP-UC-02  net settlement       different validation, different posting
    INVP-UC-03  full-month invoice   different validation, different posting
  → three features. Each needs endpoints the others do not.

§3.4 Timesheet Entry
    TIME-UC-01  entry by supervisor      same screen, same endpoint, same entity
    TIME-UC-02  entry by site manager    same screen, same endpoint, same entity
  → one feature. The difference is a permission rule, not a surface.
```

### A capability several routes reuse is its own feature

Where three routes all run the same approval step, that step is **one** feature the others cite — not a thing copied into three folders. This is Rule 3 (link, do not duplicate) applied at the boundary rather than inside the folder, and it is what stops route-first decomposition producing three near-identical features.

### Module-level rules are inherited verbatim by every feature split from that module

Splitting a module into several features splits the **routes**. It does not split the rules that govern all of them. Scope §3.x.7 is explicitly *module-level, cross-cutting* — a rule there applies to every route in the module, and a route-specific rule was already written inside its own use case instead.

So when a module produces more than one feature:

> Compose the module's §3.x.7 rules **once**, then copy them **byte-for-byte** into the `business-rules.md` of **every** feature split from that module, each keeping its global `BR-###`.

Mark them as inherited, and keep the feature's own route-specific rules in a separate group below. A developer must be able to see at a glance which rules came with the module and which belong to this route.

**Why verbatim rather than a reference.** A developer pulls **one ticket**. If a rule that governs their work lives only on a sibling ticket or in the scope document, they will build without it — and the rule will not fail loudly, it will just be missing. Copying is the cost of each ticket being self-contained, and the global `BR-###` is what keeps the copies honest: a later scope change updates every feature carrying that id, together.

This is the same mechanism `tl-feature-compose` already uses for sub-tasks (Rule 11.3, `§8 Shared contract`), where it is described as what turns *"same probably means the same"* into *"same by construction"*. Sibling features need it for exactly the same reason.

**The three failures it prevents**, all of which happen silently:

- the rules land in one feature and the other two ship without them
- they are copied with edits, so the same rule says two things
- they are left in the scope and in no feature, so nothing builds against them

**Siblings are findable.** Every feature split from one module carries the same `mapped_scope` in its frontmatter (e.g. `"§3.2 Invoice Processing"`). That is how a reader — or a later re-run — finds the set that must stay consistent. Do not invent a separate grouping field for it.

### Coverage is mechanical, and that is the point

- **Every `UC` lands in exactly one feature**, and each feature cites the `UC` ids it covers.
- A `UC` in **no** feature is work that will not get built — the breakdown is incomplete, not merely coarse.
- A `UC` in **two** features is a boundary drawn wrong — either they are one feature, or the shared part is the reusable capability above.

Both are checks rather than opinions, which is what makes this verifiable instead of a matter of taste.

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

Both guards still bind when starting from routes. A single route with no standalone business value groups with its siblings rather than shipping as a feature of its own — Guard 2 does not stop applying because the candidate came from a `UC`. And a route broad enough to fail Guard 1 splits further, use case or not.

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
Related Page:   ../../frontend/pages/supplier/supplier-details.md
Related API:    ../../backend/domains/supplier/endpoints/create-supplier.md
Related Entity: ../../database/entities/suppliers.md
```

**Rule 4 — Mark uncertainty explicitly.** Use the labels **Confirmed · Assumption · Open Question · Dependency · Risk · Out of Scope · Future Phase**. Never turn an assumption into a confirmed requirement.

**Rule 5 — Support incremental refinement.** The first breakdown needn't be perfect. Re-run when scope changes, new stakeholder input arrives, technical design adds constraints, UX changes, QA finds edge cases, or a feature is split / merged / deferred / removed. When updating, preserve history where possible and clearly identify what changed.

---

## Traceability & the no-drop rule

Every feature's `feature.md` carries **Source References** back to the scope section and/or the register IDs (`<MODULE>-FR-NN`, `WF-###`, `BR-###`, `DATA-###`, `INT-###`, `EX-###`) and, where relevant, the `[SRC-### › original]` citation. Traceability runs **scope → feature**. Before finishing, check the reverse: walk the scope's §2 module table and §3.x requirements and confirm **each maps to at least one feature**. A scope item with no feature is either a missed feature or an explicit out-of-scope/future-phase note — never a silent drop.

---

## Completion checklist

- [ ] Every `<MODULE>-UC-##` in `ba/registers/use-cases.md` appears in **exactly one** feature, and each feature cites the `UC` ids it covers.
- [ ] Any two routes merged into one feature can point at the shared pages, endpoints and entities that justified the merge.
- [ ] Where one module produced several features, every one of them carries the module's §3.x.7 rules verbatim, with the same `BR-###` ids and marked as inherited.
- [ ] A capability reused by several routes is one feature the others cite, not duplicated across folders.

The feature breakdown is complete when:

- [ ] Every major scope item maps to one or more features.
- [ ] Every feature has a dedicated folder with all ten files.
- [ ] Every feature includes business purpose, user context, workflow, acceptance criteria, dependencies, assumptions, and open questions.
- [ ] Features are indexed in `feature-index.md`.
- [ ] Features have a preliminary implementation sequence.
- [ ] Cross-feature dependencies are documented in both features and the index.
- [ ] Unresolved scope questions are visible and assigned where possible (owner or `Unassigned`).
- [ ] No source requirement is silently dropped.
- [ ] Every feature is understandable by a coding agent without full rediscovery of the project.
