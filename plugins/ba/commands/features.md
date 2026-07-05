---
description: Break the scope into an implementation-ready feature breakdown. Pass the scope path (defaults to ba-output/scope.md); the BA agent decomposes it into independently understandable features and writes a folder per feature (feature.md, implementation-plan.md, workflow.md, acceptance-criteria.md, dependencies.md, open-questions.md, status.md) plus a feature-index under context/features/. It marks assumptions and open questions instead of inventing requirements, preserves traceability to the scope, and updates existing feature folders in place on re-runs.
argument-hint: "[<path-to-scope-doc>] [initiative=<name>] [out=<output-dir>]"
---

# /ba:features

You are the entry point for building an **implementation-ready feature breakdown** from the scope. Parse the arguments and **delegate the actual work to the `ba-agent` subagent**, which runs in its own context and does the scope-heavy reading, decomposition, and folder authoring.

The mental model: the scope says *what the business wants*; this command turns it into the *implementation context* a build team needs — one folder per feature, each self-contained, with the pages/APIs/workflows/data/integrations it implies, its dependencies, and every remaining unknown captured as an open question rather than a guessed requirement.

## 1. Parse arguments

`$ARGUMENTS` may contain:
- An optional **scope document reference** — a path to a `.md` / `.docx` / `.pdf` scope, or a link. If omitted, default to `ba-output/scope.md` when a Delivery OS workspace is present.
- An optional **`initiative=<name>`** — the human-named work-batch this scoping run belongs to (lowercase-kebab, e.g. `payments-v2`). It groups the features this run produces so a developer can later plan/build just their batch (`/tl:plan initiative=…`, `/dev:build initiative=…`) even when `context/features/` holds many developers' features. If omitted, the agent auto-generates `intake-<YYYY-MM-DD>` and reports it so you can rename.
- An optional **`out=<dir>`** to override the output location (default `context/features/` at the project root; beside the scope document if there's no Delivery OS workspace).

If no scope can be located (no path given and no `ba-output/scope.md`), ask the user which scope to break down and stop. If a given path doesn't resolve, say so and ask for a valid one rather than guessing.

## 2. Delegate

Invoke the **ba-agent** subagent with the scope reference and output directory. Pass it this instruction:

> Run a **feature breakdown** of the scope document at `<doc-ref>` using the `ba-feature-breakdown` skill. Use **initiative** `<initiative or auto intake-YYYY-MM-DD>` as this run's work-batch grouping: stamp every feature you create with it (`initiative:` frontmatter in `feature.md`/`status.md` and the `Initiative` column in `feature-index.md`), and on a re-run keep an existing feature's initiative unless a new one is explicitly given. Read the whole scope first, then load the supporting context when a workspace exists (`requirement-register.md`, `workflow-register.md`, `business-rule-register.md`, `data-register.md`, `integration-register.md`, `example-register.md`, `assumption-register.md`, `clarification-log.md`, `contradiction-log.md`, `shared-context/`). Identify the major business capabilities, then decompose them into independently understandable features sized to plan/build/test/release — not so broad they can't be estimated, not so small they carry no business value (a button, one endpoint, a migration go *inside* a feature, not as one). For each feature, create `context/features/<feature-slug>/` (lowercase kebab-case) and write all seven files from `references/feature-file-templates.md`: `feature.md`, `implementation-plan.md`, `workflow.md`, `acceptance-criteria.md`, `dependencies.md`, `open-questions.md`, `status.md`. Identify the expected pages, APIs, workflows, integrations, background jobs, events, and data entities — but only as far as the scope supports; **never fabricate** product/UI behaviour, business rules, API contracts, schemas, or integrations. Mark every uncertainty with the controlled labels (Confirmed / Assumption / Open Question / Dependency / Risk / Out of Scope / Future Phase), reusing `CLR-###` ids for already-logged questions and minting `OQ-<AREA>-NN` for new ones. Wire cross-feature dependencies into both features and the index. Give every feature a stable `FEAT-<AREA>-NN` id and Source References back to the scope §/register ids — no scope item may be silently dropped. Create/update `context/features/feature-index.md`. On a re-run, update folders in place and preserve history, clearly noting what changed. Return a run summary: features created/updated, the feature-index table, cross-feature dependency highlights, open-question count (Blockers first, with owners), and any scope items you couldn't confidently place.
>
> Output directory (verbatim, or default): `<out>`

## 3. Surface the result

When the agent returns, present its **run summary**: the **initiative** used (so the developer knows the exact group to plan/build next — e.g. `/tl:plan initiative=<name>`), how many features were created/updated, the feature-index table (Feature ID · Feature · Initiative · Status · Priority · Dependencies), the key cross-feature dependencies, and the top open questions (Blockers first, with owners). Link to `context/features/feature-index.md` and note that each feature folder is self-contained. If any scope item couldn't be confidently placed, call it out as a question — never as dropped. Keep it tight — the per-feature detail lives in the folders.

> **Tip:** re-run `/ba:features` whenever the scope changes, a question gets answered, or a feature is split / merged / deferred — it updates the folders and the index in place.
