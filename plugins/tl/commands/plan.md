---
description: Plan a feature (or all features) into a linked technical context graph — map each feature to its frontend pages, backend endpoints, and database entities, reusing existing units and creating new ones, and wire them into a bidirectionally linked graph under context/frontend|backend|database. Pass a feature folder or the feature-index; the TL agent authors the page/endpoint/entity files, keeps the three layer indexes, logs design decisions, and runs a link-integrity check.
argument-hint: "<feature-folder | context/features | feature-slug> [initiative=<name>] [layers=frontend,backend,database]"
---

# /tl:plan

You are the entry point for TL feature planning. Parse the arguments and **delegate the actual planning to the `tl-agent` subagent**, which runs in its own context and does the feature-heavy reading, unit design, and linking.

## 1. Parse arguments

`$ARGUMENTS` should contain:
- A **feature target** — a path to one feature folder (`context/features/<slug>/`), a feature slug, or the whole set (`context/features/` or `feature-index.md`). This is required. Default to `context/features/` (plan all features) if the user clearly means "plan everything" but gives no path.
- An optional **`initiative=<name>`** — restrict planning to the features in that work-batch (the `initiative` stamped by `/ba:features`). This is how a developer plans **only their own scoping batch** when `context/features/` holds many developers' features: `/tl:plan initiative=payments-v2` plans just those, ignoring everyone else's. Combine with a target to narrow further, or use it alone against `context/features/` to mean "plan all features in this initiative."
- An optional **`layers=`** filter (`frontend`, `backend`, `database`, comma-separated) to restrict which layers to build. Default: all three, only creating a layer a feature actually needs.

If no target is given and intent is ambiguous, ask which feature(s) to plan and stop. If the path doesn't resolve, say so and ask for a valid one rather than guessing. If there's no `context/features/` at all, tell the user the BA feature breakdown must run first (`/ba:features`), and offer to plan against a path they point you to.

## 2. Delegate

Invoke the **tl-agent** subagent with the feature target. Pass it this instruction:

> Plan the feature(s) at `<target>` into a technical context graph using the `tl-feature-planning` skill. **If an `initiative=<name>` was given, plan only the features whose `feature.md` frontmatter `initiative` matches it** (read the `Initiative` column in `feature-index.md` or each `feature.md` to select the set) — skip all others, and report which features the filter selected. Read each target feature's `feature.md`, `implementation-plan.md`, `workflow.md`, and `dependencies.md`, and the BA registers they cite (`data-register.md` → `DATA-###`, `integration-register.md` → `INT-###`, `workflow-register.md`, `business-rule-register.md`). Load the existing `page-index.md`, `endpoint-index.md`, and `entity-index.md` first so you reuse units instead of duplicating them. For each feature, map its declared pages / APIs / data entities to real unit files under `context/frontend|backend|database` — reusing a unit and adding a back-link where its match key (page route, endpoint METHOD+path, entity object name) already exists, creating and minting the next `PAGE-/EP-/ENT-<AREA>-NN` where it doesn't. Wire links **both ways**: pages → endpoints → entities, and back (`Called by`, `Used by endpoints`). Enter at endpoints (not pages) for backend-only features (jobs, events, webhooks, integrations). You may design request/response schemas and entity columns, but mark inferred design by confidence, raise genuine unknowns as open questions, and append a `DEC-###` row to `shared-context/decision-log.md` for each material decision. Update the three indexes, then run the link-integrity check and report any dangling links, uncalled endpoints, or orphan entities. Return a summary: features planned, units created vs reused per layer, decisions logged, open questions, and integrity findings.

## 3. Surface the result

When the agent returns, present its **summary**: features planned, the created-vs-reused counts per layer, the three index tables (or their deltas), the design decisions logged (`DEC-###`), the open questions raised (with owners), and any link-integrity findings. Link to the three indexes (`page-index.md`, `endpoint-index.md`, `entity-index.md`) and note that each unit file is self-contained. Keep it tight — the detail lives in the files.
