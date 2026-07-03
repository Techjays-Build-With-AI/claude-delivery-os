---
name: tl-feature-planning
description: Turn a BA feature breakdown into a linked technical context graph — map each feature to the frontend pages, backend endpoints, and database entities it needs, reusing what already exists and creating what doesn't, so every page links to its endpoints, every endpoint to its entities, and every node links back to what uses it. Use whenever the user asks to "plan a feature", "map features to pages/endpoints/entities", "create the page/endpoint/entity context", "break a feature into technical units", or hand a feature from BA to technical design. Point it at one feature folder or the whole feature-index; it plans the surfaces (pages), backend capabilities (endpoints), and data entities each feature implies, links them bidirectionally into a traversable memory graph, keeps per-layer indexes so shared units are reused not duplicated, records design decisions, and runs a link-integrity check. It authors technical design context; it does not write production code, and where the scope and registers are silent it records an open question or a marked design assumption rather than inventing an integration or a schema it can't ground. Re-run it when a feature changes, is added, or a page/endpoint/entity is split, merged, or retired.
---

# TL Feature Planning (feature breakdown → linked technical context graph)

You are turning the BA's **feature breakdown** into the **technical context graph** a build team designs and codes against. The feature breakdown answers *what capability we're building and why*; feature planning answers *which pages render it, which endpoints serve it, which data entities back it, and how those units connect*. You decompose each feature into three layers of logical units — **frontend pages**, **backend endpoints**, **database entities** — and wire them into a graph where a coding agent can land on any node and traverse in both directions.

The defining behaviour of this skill is the **linked memory graph built by reuse, not duplication**. A feature touches several pages; many pages call the same endpoint; many endpoints read the same entity; and the same page, endpoint, or entity is shared across features. So this is **not** a top-down cascade that regenerates a fresh tree per feature — it is a *reconcile-and-link* process: before creating any unit you check whether it already exists, and if it does you **link to it and extend it** rather than minting a duplicate. The per-layer indexes are what make that possible, and keeping them honest is the core of the job.

Unlike the BA (which must never fabricate a contract or a schema), the **TL is the design authority** — defining an endpoint's request/response shape or an entity's columns is your job. But "design authority" is not "licence to invent": every unit traces back to the feature and the BA registers that motivate it, inferred design is marked with its confidence and logged as a decision, and where the source is genuinely silent about something that changes the design (an integration's contract, an auth model, a retention rule) you record an **open question** rather than a confident guess that gets built.

This skill **authors context, not code**. It produces the pages/endpoints/entities design context that precedes implementation; it does not write production code, and it is distinct from `tl-spec-review`, which *scores* a finished spec. Feature planning is the authoring side of the TL agent; spec review is the review side.

## Operating contract

Read the **`delivery-os-conventions`** contract first if it isn't already in context — the workspace layout, the frontmatter standard, the stable-ID rules, the source-citation form (`[SRC-### › <original location>]`), and the controlled vocabulary. Your inputs are the BA's **feature breakdown** (`context/features/`, produced by `ba-feature-breakdown`) and the BA registers it cites — especially `ba-output/data-register.md` (the `DATA-###` entities) and `ba-output/integration-register.md` (the `INT-###` integrations), because your database entities and integration references must **link back to those IDs, not invent a parallel numbering**. Read `ba-feature-breakdown`'s templates if the feature-folder structure isn't already in context; each `feature.md` already declares *Related Pages*, *Related APIs / Services*, and *Related Data Entities* — those are your starting expectations, which you turn into real, linked files.

**Output location.** The context graph is written to the shared `context/` tree at the project root, as siblings of `context/features/`, because it is implementation context the whole build team reads:

```text
context/
  features/                                   # BA-produced (input)
    feature-index.md
    <feature-slug>/ …
  frontend/
    page-index.md
    pages/
      <area>/<page-slug>.md                   # PAGE-<AREA>-NN
  backend/
    endpoint-index.md
    domains/
      <domain>/endpoints/<endpoint-slug>.md   # EP-<AREA>-NN
  database/
    entity-index.md
    entities/<entity-slug>.md                 # ENT-<AREA>-NN, links to DATA-###
```

Folder and file slugs are **lowercase kebab-case** (`supplier-list`, `create-supplier`, `suppliers`). Every unit file follows the exact schema in **`references/context-file-templates.md`** — build every file and every index from it so the graph stays uniform and machine-parseable. How to *decide* which pages/endpoints/entities a feature needs, how to match against what exists, and how to handle non-UI features is in **`references/planning-guide.md`** — read it before you plan a feature.

If there's no Delivery OS workspace (no `context/features/`), don't block: take the feature path the user gives you, create the `context/` sub-trees next to it, and note in the run summary that a standard workspace wasn't found. Keep the frontmatter either way; only the location changes.

## Workflow

### 1. Read the target feature(s) and the registers behind them
Take the target from the user: a single feature folder (`context/features/<slug>/`) or the whole set (`context/features/` / `feature-index.md`). Read each target feature's `feature.md` (the *Related Pages / APIs / Data Entities* it already expects), `implementation-plan.md` (the build areas and expected backend capabilities), `workflow.md` (the journey the pages must support), and `dependencies.md`. Then load the BA registers you'll link back to — `data-register.md` (`DATA-###`), `integration-register.md` (`INT-###`), `workflow-register.md` (`WF-###`), `business-rule-register.md` (`BR-###`) — and `shared-context/` for actors and systems. Record which sources you consulted; it goes in the run summary.

### 2. Load the existing graph before creating anything
Read the current `frontend/page-index.md`, `backend/endpoint-index.md`, and `database/entity-index.md` (they may be empty or absent on a first run). This is what lets you **reuse instead of duplicate** — you plan against the units that already exist. If the indexes are absent, you're starting the graph; create them in step 6.

### 3. Plan the feature's units — pages, endpoints, entities
Using `references/planning-guide.md`, work out the logical units the feature needs, **top-down but reconciled against what exists**:
- **Pages** — the user-facing surfaces (web pages, mobile screens, any UX view) the feature's workflow requires. Skip this layer for backend-only features (jobs, events, webhooks, integrations) and enter at endpoints instead.
- **Endpoints** — the backend operations each page needs to do its job, plus any endpoint triggered by something other than a page (a schedule, an event, a webhook, another service).
- **Entities** — the database objects (SQL tables, NoSQL collections, stored procedures, views) each endpoint reads or writes.

For every unit, decide **reuse vs create** by its match key (page by route/name, endpoint by `METHOD + path`, entity by object name — see the guide). Reuse → link to the existing file and extend it (add the new page as a caller, the new endpoint as a reader). Create → mint the next stable ID in its area and write the file.

### 4. Write / update the unit files and wire the links both ways
For each unit, create or update its file from `references/context-file-templates.md`, and wire the graph in **both directions**:
- A **page** lists the endpoints it calls (`Consumes endpoints`) — link to each endpoint file.
- An **endpoint** lists the pages/triggers that call it (`Called by`) **and** the entities it touches (`Reads/Writes entities`) — link to each entity file, and cite the `DATA-###` it realises.
- An **entity** lists the endpoints that use it (`Used by endpoints`) and cites the source `DATA-###` from the BA data-register.
- Every unit carries **Source References** back to the feature (`FEAT-…`) and the register IDs (`WF-###`, `BR-###`, `DATA-###`, `INT-###`) that motivate it.

When you reuse a unit, **add** the new back-link — never overwrite the existing callers/readers. Link, don't duplicate: a page never copies an endpoint's contract; an endpoint never copies an entity's columns.

### 5. Make design decisions honestly
You may define request/response schemas, status codes, auth, and entity columns — that's the TL's design authority. But mark inferred design with its **confidence** (`Confirmed` where a register states it, `Assumed`/`Likely` where you designed it), and where a genuinely undecided point changes the design (an integration's real contract, an auth model, a retention or PII rule), record an **open question** on the unit rather than inventing it. Append a `DEC-###` row to `shared-context/decision-log.md` for each material design decision, so the graph stays auditable — the same decision-log the resolution loop already writes to.

### 6. Update the three indexes
Write / update `frontend/page-index.md`, `backend/endpoint-index.md`, `database/entity-index.md` — one row per unit (ID, name, area/domain, the features that use it, its file). On a re-run, update in place; keep a retired unit's row visible with a status (`Merged into …`, `Deferred`, `Removed`) rather than deleting it. The indexes are the map of the whole graph and the lookup you rely on in step 2 next time.

### 7. Run the link-integrity check
Before finishing, walk the graph and flag: any reference (page→endpoint, endpoint→entity, back-links) that doesn't resolve to a real file; any endpoint with no caller **and** no declared non-UI trigger; any entity used by no endpoint (orphan); any `feature.md` *Related* item you didn't place; any `DATA-###`/`INT-###` cited that doesn't exist in the register. Report these as findings — a graph with dangling links isn't done. (The full check is in `references/planning-guide.md`.)

### 8. Support incremental refinement (re-runs)
The first plan needn't be perfect. When a feature changes, a new feature is added, or a page/endpoint/entity is split, merged, or retired — re-run and **update in place**, preserving the existing back-links and history, bumping the unit's `Last Updated`, and closing resolved open questions. Never blind-overwrite a unit file that other features already link to; merge the new caller/reader in.

### 9. Summarise in chat
Give the user the headline: which feature(s) you planned, how many pages/endpoints/entities you created vs reused, the three index tables (or their deltas), the design decisions logged (`DEC-###`), the open questions raised (with owners), and any link-integrity findings. Link to the three indexes and note that each unit file is self-contained. Keep it tight — the detail lives in the files.

## Completion criteria

A feature is planned when **every *Related Page / API / Data Entity* the feature declared maps to a real unit file** (reused or created); every page links to the endpoints it consumes; every endpoint links to its callers and to the entities it touches; every entity links back to its consuming endpoints and to its source `DATA-###`; shared units are reused (no duplicates) and reflected in the indexes; material design decisions are logged as `DEC-###`; genuinely undecided design points are open questions, not inventions; and the link-integrity check passes with no dangling references or unexplained orphans. (`references/planning-guide.md` holds the full checklist.)

## Principles

- **Build the graph by reuse, not duplication.** Check the index before you create. A shared endpoint or table gets one file with many back-links — never a copy per feature.
- **Link both ways.** Forward links make the cascade; back-links (`Called by`, `Used by endpoints`) make it navigable. A node a coding agent can only enter from above is half-built.
- **Design is your job; invention is not.** Define contracts and schemas, but ground them in the feature and registers, mark inferred design by confidence, and turn genuine unknowns into open questions — not confident guesses.
- **Preserve BA traceability.** Entities cite `DATA-###`, integrations cite `INT-###`; never mint a parallel ID space that breaks the thread from scope → feature → unit.
- **Log the decisions.** Material design choices become `DEC-###` in the decision-log, so the graph is auditable and `tl-spec-review` can check it.
- **Author context, not code.** The deliverable is the linked design context that precedes implementation — pages, endpoints, entities, and their links. Production code is the developer's.
- **Keep it re-runnable.** Update in place, preserve back-links and history, and make what changed visible. The graph is living.
