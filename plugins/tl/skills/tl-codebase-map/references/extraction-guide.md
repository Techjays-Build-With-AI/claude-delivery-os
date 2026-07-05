# Extraction guide — reading a codebase into the context graph

How to find each layer in a real repository, how to infer the links between them, how to mark confidence, and how to stay interoperable with `tl-feature-planning` so a later `/tl:plan` reuses what you mapped. Read `tl-feature-planning`'s `context-file-templates.md` for the file schemas; this guide is about getting the facts **out of the code** honestly.

The north star: **the unit files you write from code must be indistinguishable in shape from the ones forward planning writes** — same IDs, same match keys, same links — so the two graphs are one graph. The only additions are `origin: reverse-mapped`, a code citation, and a per-link confidence.

---

## Interop rule — match keys must line up

`/tl:plan` reuses a unit when its match key already exists. So mint your units on the **same keys** it matches on, or reuse will fail and you'll get duplicates:

| Layer | Match key (must match forward planning) | Read it from |
|---|---|---|
| Page | route path / canonical page name | the router config or the file's route |
| Endpoint | `METHOD + path` (normalised, params as `{id}`) | the route/controller declaration |
| Entity | object name (table / collection / model) | the model class name or table name |

Normalise the same way planning does: lowercase, path params as `{param}`, trailing slashes stripped, pluralization as the code declares it. If in doubt, prefer the string the framework's router actually registers.

---

## Layer 1 — Entities (start here; everything else references them)

Map the data layer first so endpoints can link to real entity files.

- **ORM/ODM models** — one entity per model class (Sequelize/TypeORM/Prisma/Django/SQLAlchemy/ActiveRecord/Mongoose…). Read the columns/fields, types, keys, and declared relations (`hasMany`, FK, `references`).
- **Schema & migrations** — where there's no ORM, read `schema.sql`, migration files, or a Prisma/DBML schema. The latest migration state is the truth; note if migrations conflict.
- **Views / stored procedures** — each is its own entity, marked as such.
- **Citations & confidence:** cite the model/migration file. Columns read from a declared schema are `Confirmed`; a field added dynamically or via mixins is `Assumed`.
- If a BA `data-register.md` exists, link the `DATA-###` the entity realises; brownfield-only projects often have none — that's fine, note it.

## Layer 2 — Endpoints (link them to entities as you go)

- **Route tables / decorators / controllers** — one endpoint per `METHOD + path`. Sources vary by stack: Express/Koa routers, Spring `@GetMapping`, Flask/FastAPI decorators, Rails `routes.rb`, NestJS controllers, Django urls. Capture method, path, and the handler function.
- **Non-HTTP entry points** — scheduled jobs (cron/queue workers), event/message consumers, webhook receivers. Map each as an endpoint with its **trigger** (`Schedule`, `Event`, `Webhook`, `Service`) instead of a caller page — the integrity check requires every endpoint to have a caller *or* a trigger.
- **Endpoint → entity links:** read the handler body. ORM calls / queries against a model give a `Reads/Writes entities` link (Confirmed). A query built from a string variable, or data access buried behind a generic repository, is `Assumed` — link it and flag low confidence.
- **Citations:** cite the route declaration file and the handler file.

## Layer 3 — Pages (link them to endpoints)

- **Routed surfaces** — one page per route in the frontend router (React Router/Next.js `pages` or `app`, Vue Router, Angular routes, server-rendered templates/controllers-with-views). A modal, tab, drawer, or widget is documented *inside* its page, not as its own unit — same rule as forward planning.
- **Page → endpoint links:** trace the page's data calls to the backend — a service/api module, `fetch`/`axios`/`httpClient` calls, generated API clients, React-Query/RTK hooks, or form `action`s. Resolve each call's `METHOD + path` and link to that endpoint (Confirmed when the URL is a static literal; `Assumed` when it's composed at runtime).
- **Citations:** cite the page component/template file and the api/service module.

---

## Confidence — be honest about what the code shows

Use the shared vocabulary (`Confirmed · Likely · Assumed · Conflicting · Needs Clarification`) on every inferred fact and link:

- **Confirmed** — read directly and unambiguously (a static route literal, a declared column, an ORM call naming the model).
- **Likely** — a strong, conventional inference (a service method named `getSuppliers` calling `/suppliers`).
- **Assumed** — inferred to fill a gap (a dynamically built URL, a generic repository, a computed route).
- **Conflicting / Needs Clarification** — the code contradicts itself (two migrations disagree) or is opaque (reflection, code-gen, metaprogramming). Raise an **open question** on the unit; don't pick a story.

A map that is 70% `Confirmed` and honest about the 30% is far more useful than one that looks 100% clean and is quietly wrong.

## Frontmatter marker

Every reverse-mapped unit carries, in addition to the standard template frontmatter:

```yaml
origin: reverse-mapped        # vs authored forward by tl-feature-planning
mapped_from: "src/..."        # the primary source file the unit was read from
map_confidence: Confirmed     # overall confidence for this unit
```

Forward planning ignores `origin`; it just sees a normal unit to reuse and link a feature to. When `/tl:plan` later links a feature, it adds the `FEAT-…` to the unit and index as usual — leave the `origin` marker in place as provenance.

---

## Reconciliation & re-runs

- **Existing graph:** if units already exist (hand-authored, or a prior map), match by key and **extend** — add newly discovered links/columns, don't overwrite. Never duplicate a unit that already exists under a different slug; fix the slug or merge.
- **Re-map after code changes:** update units in place, bump `Last Updated`, add new units, and mark units whose code was deleted with a retirement status (`Removed`) rather than deleting the row.
- **Scope control:** honor a `layers=` filter (frontend/backend/database) and a path/module scope if given, so a large monorepo can be mapped a slice at a time.

## Integrity bar (same as forward planning)

Run `tl-feature-planning`'s link-integrity check before finishing, plus these map-specific findings:
- Code paths you saw but could not confidently map (dynamic routes, reflection, generated handlers) — list them, don't silently drop them.
- Endpoints with no caller and no discoverable trigger — flag (may be dead code or an external caller).
- Entities not referenced by any endpoint — flag as possible orphan/reference data.
- Any link below `Likely` confidence — surfaced so a human (or a later spec review) can verify.
