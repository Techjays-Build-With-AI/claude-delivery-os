---
description: Compose the Implementation-tab content (`tl-plan.md`) for one or more features, from the TL context graph. Populates only the Implementation tab in Jetrix via `/jetrix:push implementation` — Description, Business Rules, Acceptance Criteria, NFRs, Test Scenarios, and Dependencies come from BA push. The composed document names components by role (never by file path or framework name), lists API endpoints with normative execution order and distinct-message refusals tables, names only the DB fields the feature writes, describes UI surfaces by role with their API wiring, and closes with a Reuse / New Touch-points table. Pass one feature id/folder, an `initiative=<name>` filter, or no argument to compose every feature.
argument-hint: "<feature-folder | feature-slug> [initiative=<name>] [--force]"
---

# /tl:compose

You are the entry point for TL feature composition. Parse the arguments and **delegate the composition to the `tl-agent` subagent**, which runs `tl-feature-compose` in its own context and does the per-feature synthesis.

**`/tl:compose` presupposes `/tl:plan` has run** — it reads the graph, it does not build it. If a target feature has no owned units in the three indexes, tell the user to run `/tl:plan` first and stop.

## 1. Parse arguments

`$ARGUMENTS` may contain:
- A **feature target** — a path to one feature folder (`context/features/<slug>/`), a feature slug, a `FEAT-<AREA>-NN` id, or the whole set (`context/features/` / `feature-index.md`). Default: `context/features/` (compose all features).
- An optional **`initiative=<name>`** — restrict composition to features whose `feature.md` frontmatter `initiative` matches (same filter `/tl:plan` uses).
- An optional **`--force`** — recompose every targeted feature even if its `tl-plan.md` is already up-to-date. Default: skip a feature whose graph inputs haven't changed since the last compose (checked via content-hash).

If no target and intent is ambiguous, ask which feature(s) to compose and stop. If there's no `context/features/`, tell the user to run `/ba:features` and `/tl:plan` first.

## 2. Delegate

Invoke the **tl-agent** subagent with the target. Pass it this instruction:

> Compose the Implementation-tab content for `<target>` using the `tl-feature-compose` skill. The output goes to `context/features/<slug>/tl-plan.md` and populates **only** the Implementation tab of the MC Task — Description, Business Rules, Acceptance Criteria, NFRs, Test Scenarios, and Dependencies come from BA push and must never appear in what you write.
>
> **If an `initiative=<name>` was given, compose only the features whose `feature.md` frontmatter `initiative` matches** — skip all others and report which features the filter selected.
>
> For each targeted feature: read `feature.md`, `workflow.md`, `acceptance-criteria.md`, `dependencies.md`, `open-questions.md`, and any per-feature NFR / test-scenario / business-rule content. Resolve the feature's owned unit files from the three indexes (frontend pages, backend endpoints, database entities) using the feature-cell matching rule the implementation push uses (word-boundary match on comma-separated cells; 2-hop endpoint → entity chain). Read every owned page, endpoint, and entity file — the graph's file paths and framework detail are your INPUT for accuracy, not your output.
>
> Compose the file per `references/implementation-plan-template.md` with exactly these five subsections in this order:
>
> 1. **Build sequence** — one paragraph, one mermaid step-graph, a step table with independently verifiable "Done when" per step. Steps depending on undecided open questions are marked `[HELD · waiting on OQ-<id>]`.
> 2. **API endpoints** — one heading per endpoint the feature creates or modifies. Each carries a path-parameter table (if any), request-body table + JSON example, a **normative Execution-order table** (step-by-step with failure code per step), a success JSON with the exact response code, and a Refusals table with **one row per distinct `message`** (three `409` variants → three rows, never collapsed). Close with a paragraph on invariants (idempotency, partial-write behaviour, side effects).
> 3. **Database modifications** — a one-line description of the affected data object by role. A "Fields written by this feature" table listing ONLY the fields this feature writes. A one-line "Never touched: `<field-a>`, `<field-b>`, `<field-c>`" boundary. A paragraph on state semantics the write depends on.
> 4. **Frontend UI** — an API-wiring table (Surface | Trigger | Calls), one heading per user-facing surface described by role, a control table on the interactive form, a Refusal-placement table (which server `message` renders where, per code), a one-paragraph API service description.
> 5. **Touch points** — Reuse / New table naming existing and new components **by role**. Include the internal review caveat.
>
> **Absolute rules — a violation invalidates the composition:**
>
> - **No file paths**, anywhere. Not in Touch points, not in headings, not in prose, not in code fences. Every component is named by its role — *"the leave controller"*, *"the decision dialog"*, *"the API service layer"*, *"the leave list"*, *"the row action"*. Repo paths in the graph are TL design detail — the dev-agent maps role names back to files via the local graph at build time.
> - **No framework, library, or version names**, anywhere. No `React`, `Vite`, `Express`, `Mongoose`, `mongoose.Schema`, `TipTap`, `Redux`, `Playwright`, `Jest`, `Prisma`, `SQLAlchemy`, `React 18`, `Node 20`. Describe the data object by role and fields written; do not include a schema code fence in any framework's syntax.
> - **No duplication of other tabs.** No Business Goal, no user-flow narrative, no mermaid workflow diagram (Description owns it), no AC list, no NFR list, no Business Rule list, no Test Scenarios, no Dependencies. If a fact belongs in another tab, do not restate it here.
> - **No feature identity in visible content.** Feature id, initiative, slug, and provenance live in the frontmatter and MC task metadata — never in headings or prose. No `# FEAT-…` H1. No "Provenance:" line. No reference to `feature.md`, `workflow.md`, `acceptance-criteria.md`, `ba-output/*`, `context/*`, or any scope-review filename.
> - **Existing schema fields the feature does not write** are named on one boundary line — not tabled.
> - **Response codes and messages are discriminated explicitly** — one row per distinct `message`.
> - **No client-narrative, no provenance callouts, no author commentary.** No *"the client chose transparency knowingly"*, no `⚠ PROVENANCE — PLANNED, NOT BUILD-READY` blocks, no *"acceptance criteria are authored as bullets without ids"*, no *"SIMULATED response round"* preambles.
> - **No aspirational text** (*consider*, *might*, *could*). A phase is either buildable or `[HELD · waiting on OQ-<id>]`.
> - **No secrets.** Env var names only if referenced; never values.
> - **Size budget** — target 10–15 KB, warn at 55 KB, refuse above 60 KB (MC's `implementationDetails` cap). Do not truncate; surface the overflow and ask the user to split the feature.
> - **No invention.** Every fact traces to the context graph or the feature files. When silent, mark the step `[HELD · waiting on OQ-<id>]` and name the gap.
>
> Write the file to `context/features/<slug>/tl-plan.md` with the frontmatter (`doc_type: tl-plan`, `schema_version`, `produced_by: tl`, `feature_id`, `composed_at`, `inputs_hash`). On re-runs, update in place, preserve `<!-- KEEP -->` blocks, and log any material design choice as a `DEC-###`.
>
> Return: features composed vs skipped-unchanged (with reason each), size per feature, any features where the graph is incomplete (missing owned units), and any steps marked `[HELD]`.

## 3. Surface the result

Present the composition summary: features composed vs skipped-unchanged, `[HELD]` steps surfaced per feature (with the OQ id blocking each), size per feature (min/max/median), and any features refused due to incomplete graph. Link to each `tl-plan.md`. Remind the user that `/jetrix:push implementation` sends each `tl-plan.md` verbatim to its MC Task's Implementation tab.
