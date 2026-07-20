---
description: Reverse-map an existing codebase into the technical context graph — read the real repository and derive its frontend pages, backend endpoints, and database entities and their relationships, writing the same context/frontend|backend|database units that /tl:plan produces forward (so a later /tl:plan reuses them, not duplicates). For onboarding a brownfield project into Delivery OS. Read-only on the code; marks every unit as-built with a confidence and a source-file citation; never invents a relationship the code doesn't show.
argument-hint: "<repo=<path> | (blank = current workspace)> [layers=frontend,backend,database] [scope=<subpath>]"
---

# /tl:map

You onboard an **existing codebase** into Delivery OS by deriving its technical context graph from the code. Delegate the work to the **`tl-agent`** subagent, which runs `tl-codebase-map` in its own context.

## 1. Parse arguments

`$ARGUMENTS` may contain:
- An optional **`repo=`** path to the product repository to map (default: the current workspace / project repo).
- An optional **`layers=`** filter (`frontend`, `backend`, `database`, comma-separated) to map only some layers. Default: all three.
- An optional **`scope=`** subpath/module to map a slice of a large monorepo at a time.

If there's no resolvable repository, say so and ask the user to point you at one — there's nothing to map without code.

## 2. Delegate

Invoke the **tl-agent** subagent. Pass it this instruction:

> Reverse-map the repository at `<repo>` into the technical context graph using the `tl-codebase-map` skill — follow `references/extraction-guide.md`, and write the exact unit/index files defined in `tl-feature-planning`'s `references/context-file-templates.md` so the output is interoperable with forward planning. Run it in **two passes**. **Pass A (discovery):** detect the stack (`context/project/technology-stack.md` if present, else infer) and write a per-layer `_overview.md`; load any existing `page-index.md`/`endpoint-index.md`/`entity-index.md` and **reconcile, don't duplicate**; then **enumerate every unit from the declarative sources** — prefer an OpenAPI/Swagger spec or route manifest for endpoints, the router config for pages, the schema/migration state for entities — into a `context/map-coverage.md` manifest, every row `pending`. **Pass B (detail):** burn the manifest down, writing entities first (table/collection/view/procedure/function/trigger), then endpoints (with `METHOD + path`, plus jobs/events/webhooks and their triggers), then pages — flipping each row to `mapped`. Then infer the links (page→endpoint from API-client calls, endpoint→entity from ORM/queries) and wire them **both ways**. Mint IDs (`PAGE-/EP-/ENT-<AREA>-NN`) on the **same match keys** forward planning uses (route, normalised `METHOD+path`, entity object name) so a later `/tl:plan` reuses these units. Mark every unit `origin: reverse-mapped` with a `[code › <file>]` Source Reference and a per-link **confidence** — `Confirmed` where the code shows it directly, `Assumed`/open-question where it's dynamic or opaque; **never invent** a relationship the code doesn't support. Do **not** modify, refactor, or run the repository, and do **not** author BA features or infer product scope from the code. Update the three indexes (`Used by Features = (as-built)` until a feature links in), run the link-integrity check **including the coverage check (no `pending` rows left)**, and report any code you couldn't confidently map. Return units mapped per layer (created vs reconciled), the coverage (enumerated vs mapped vs skipped), the confidence spread, index deltas, and integrity findings.
>
> Repository: `<repo or current workspace>` · Layers: `<layers or all>` · Scope: `<scope or whole repo>`

## 3. Surface the result

Present the **map summary**: pages/endpoints/entities mapped per layer (created vs reconciled), the **coverage** (units enumerated vs mapped vs skipped, from `context/map-coverage.md`), the confidence spread (how much is `Confirmed` vs `Assumed`), the three index deltas, link-integrity findings, and any code that couldn't be confidently mapped (dynamic routes, generated handlers). Link to the three indexes and the coverage manifest. Tell the user the as-built graph is in place, and the next steps for the brownfield increment: run `/qa:audit` on the repo to check testability, and `/tl:plan initiative=<batch>` for the new features — which will **reuse** these units rather than recreate them. Lead with the low-confidence areas if a meaningful share of the graph is `Assumed`.
