# Extraction guide — reading a codebase into the code-context tree

How to find each layer in a real repository, how to derive the business domains that organise the tree, how to read validation and data access out of a handler, how to infer the links between units, how to mark confidence, and how to stay interoperable with `tl-feature-planning` so a later `/tl:plan` reuses what you mapped. Read `references/code-context-templates.md` for the file schemas; this guide is about getting the facts **out of the code** honestly.

The north star: **the unit files you write from code must be indistinguishable in shape from the ones forward planning writes** — same IDs, same match keys, same links — so the two graphs are one graph. The additions are `origin: reverse-mapped`, a code citation, a per-link confidence, and the richer endpoint and database-object sections.

---

## 0. Where the output goes

`<repo>/context/code-context/` — a `context/` folder at the root of the mapped repository, with `code-context/` inside it, committed with the code. Not the workspace, and **not** inside `.jetrix/` — that folder is gitignored, so a tree written there would never reach a teammate's clone. When several repos are mapped from one workspace, each gets its own tree, and `<workspace>/.jetrix/<project-name>/tl/code-map-registry.md` points at all of them. Two consequences for extraction:

- **A repo is mapped as a whole system in its own right.** Its `code-context-index.md` says what the repo is and which layers it has; a backend-only repo says "frontend lives in `<other-repo>`" rather than leaving the layer silently absent.
- **The tree will be read in review.** Write for a human reviewer as well as an agent — and never write a secret, connection string, credential, or customer data row into it.

---

## 1. Interop rule — match keys must line up

`/tl:plan` reuses a unit when its match key already exists. Mint your units on the **same keys** it matches on, or reuse fails and you get duplicates:

| Layer | Match key (must match forward planning) | Read it from |
|---|---|---|
| Page | route path / canonical page name | the router config or the file's route |
| Endpoint | `METHOD + path` (normalised, params as `{id}`) | the route/controller declaration |
| Database object | object name (table / collection / view / procedure / function / trigger) | the DDL, model class, or migration |

Normalise the same way planning does: lowercase, path params as `{param}`, trailing slashes stripped, pluralisation as the code declares it. If in doubt, prefer the string the framework's router actually registers. For database objects, prefer the **physical name in the schema** over the ORM class name (`invoice_lines`, not `InvoiceLine`) — note the class name in the file.

---

## 2. Deriving business domains — the backbone of the tree

Everything is grouped by domain, so get this right before writing anything. Work **down** the ladder and stop at the first rung that gives a clean, stable decomposition:

1. **Explicit module boundaries.** A monorepo's packages, a NestJS/Spring module tree, a Django app list, a bounded-context folder layout. If the codebase already declares its domains, use them verbatim — including their names.
2. **Route prefixes.** `/api/accounts/*`, `/api/billing/*` — the first meaningful path segment after any version prefix. Strong and stable in REST codebases.
3. **Folder and file naming.** `services/billing/`, `controllers/AccountController.ts`, `models/subscription/`. Weaker, but usually consistent within a repo.
4. **Foreign-key / reference clusters.** For the database when nothing above helps: objects that reference each other tightly and are referenced by the same endpoints belong together. `invoices → invoice_lines → payments → credit_notes` is one domain even if the files are scattered.
5. **Ask.** If the repo genuinely resists decomposition (a big-ball-of-mud controller layer, one 200-endpoint router file), don't invent a taxonomy — propose one and flag it as a `DEC-###` with an open question, or ask the user.

Rules that keep the decomposition useful:

- **5–12 domains for a typical application.** Two domains is not a decomposition; thirty is a directory listing. Merge thin domains into a neighbour or into `CORE`.
- **`CORE` is for cross-cutting technical surfaces** — auth, health, audit, feature flags, migrations bookkeeping — not a dumping ground for anything hard to classify. If `CORE` is your biggest domain, the decomposition failed; go back up the ladder.
- **An object serving several domains lives in the domain that *owns* it** (writes it, defines its lifecycle), with back-links from the others. `audit_log` is `CORE`, referenced by everyone.
- **Reuse area tokens across repos.** The frontend repo's Account pages and the backend repo's Account endpoints share `ACC`. Check the registry before minting a token.
- **Domains are stable.** On a re-run, keep existing domain assignments unless the code genuinely moved; renaming a domain churns every ID and link.

Log a `DEC-###` for each non-obvious call — a merge, a split, a token reuse. Those are interpretations, and a reader deserves to see them.

---

## 3. Three passes — discovery, detail, synthesis

A large application won't fit in one reading. Enumerate everything cheaply first, write unit files one at a time, then build the indexes from what was actually written. **Enumeration order and link-resolution order are decoupled** — list endpoints and pages first because they're declarative and cheap to enumerate wholesale, but *write* database objects first and resolve cross-links last, so a page file is never written pointing at an endpoint file that doesn't exist yet.

### Prefer a declarative registry over reading every file

Wherever the project already declares its surface, read that declaration instead of reconstructing it — it's authoritative, static, and complete:

| Layer | Best source of truth (in order) |
|---|---|
| Endpoint | a checked-in **OpenAPI/Swagger** spec → a route manifest / `routes.rb`-style table → decorators/controllers read individually |
| Page | the **frontend router config** (route table) → the `pages`/`app` directory convention → screens discovered by naming |
| Database | the **schema/migration state** (or a Prisma/DBML/schema.sql dump) → ORM model classes → raw SQL in the code |

A route-dump *command* (`rails routes`, Django `show_urls`, a printed Spring mapping) is more complete still, but running it collides with the read-only boundary — prefer a **checked-in** spec/manifest and fall back to per-file static reading only when there's no declarative source. Reading git metadata (`git rev-parse HEAD`, `git log -1 --format=%H -- <path>`) is permitted: it doesn't modify anything and gives you the `mapped_from_commit` stamp and, on a `refresh=changed` run, the changed-file set.

### The coverage manifest

Discovery writes `code-context/map-coverage.md` — the full enumerated list, each row the scope guard for "what haven't we mapped yet". Schema in `code-context-templates.md` §7. **Status:** `pending` (enumerated, not yet written) · `mapped` (unit file written) · `skipped` (couldn't map confidently — must carry a note **and** a matching integrity finding) · `removed` (code deleted since the last run). The integrity check fails if any row is left `pending`.

---

## 4. Layer 1 — Database objects (start here; everything else references them)

Map the data layer first so endpoints can link to real object files. **One file per object, in the folder for its kind.** The kinds are not interchangeable: a stored procedure that computes money is a different kind of fact from a table that stores it, and flattening them into "entities" loses exactly the thing a reader needs.

### Tables
ORM/ODM model classes (Sequelize, TypeORM, Prisma, Django, SQLAlchemy, ActiveRecord, Mongoose, EF Core) and the migration/schema state. Read columns, types, nullability, defaults, keys, indexes and declared relations (`hasMany`, FK, `references`). **The latest migration state is the truth** — note it if migrations conflict. Columns read from a declared schema are `Confirmed`; a field added dynamically, by a mixin, or by a JSONB blob's implied shape is `Assumed`.

### Collections (document stores)
One file per collection. Reconstruct the **document shape** from the ODM schema where one exists (Mongoose, Beanie, Prisma-Mongo); where the store is schemaless, reconstruct it from the write paths in the code and say so — a shape derived from writes is `Likely` at best. Always state, per relation, whether it is **embedded or referenced**; that is the schema decision a reader most needs. Record declared indexes and, where present, the shard/partition key.

### Views
Read the `CREATE VIEW` DDL. Record what it reads from (link each source object), the derivation of each output column, and whether it is **materialised** (and if so, how it's refreshed). A view that exists to hide a heavy join is a performance fact worth noting — flag it if endpoints read it in a loop.

### Stored procedures and functions
These carry real business logic, so document them like endpoints: **signature** (parameters, direction, return type, determinism), **Business Purpose**, **Business Logic** as ordered steps, **Objects Touched** with mode, **error conditions**, and transaction/locking behaviour. Sources: migration DDL, a `procedures/` or `functions/` folder, a schema dump. If a procedure is invoked but its body isn't in the repo (created out-of-band in the database), write the file from the call sites, mark it `map_confidence: Assumed`, and raise it as a finding — a procedure the repo calls but doesn't define is a genuine risk worth surfacing.

### Triggers
Record the table it fires on, the **timing and events** (`BEFORE/AFTER INSERT/UPDATE/DELETE`, `FOR EACH ROW/STATEMENT`), any `WHEN` condition, what it does, the objects it touches, and the procedure/function it calls. Triggers are the most common source of "why did this row change?" — a trigger that writes audit rows or recalculates totals must be linked from the tables it touches, or a reader will conclude the application does something it doesn't.

### Business Purpose — the section that isn't in the DDL
Every database object file carries one. It answers *why the business has this object*: what it means, what depends on it, what invariant it protects, what it is **not** for. Derive it from how the object is used across endpoints, procedures and triggers — a table read by one endpoint and written by a nightly job is a different animal from one on every request path. This is interpretation, so keep it grounded: if you can't ground a claim in a call site or a constraint, don't make it.

### DATA-### linkage
If the workspace has a BA `ba/registers/data.md`, link the `DATA-###` the object realises. Brownfield-only projects usually have none — that's fine and expected; write `—` and note why. Views, procedures, functions and triggers rarely have a business-register counterpart.

---

## 5. Layer 2 — Endpoints

One endpoint per `METHOD + path`. Sources vary by stack: Express/Koa routers, Spring `@GetMapping`, Flask/FastAPI decorators, Rails `routes.rb`, NestJS controllers, Django urls, ASP.NET attributes, Go chi/gin route registration. Capture method, path, and the handler function, then read the handler through to the data layer.

**Non-HTTP entry points** are endpoints too: scheduled jobs (cron, queue workers), event/message consumers, webhook receivers, GraphQL resolvers, gRPC methods. Map each with its **trigger** (`Schedule`, `Event`, `Webhook`, `Service`) instead of a caller page — the integrity check requires every endpoint to have a caller *or* a trigger. Record the cron expression, queue and message type, or external sender; "runs nightly" is not enough for someone who has to change it.

### Reading the request contract
Path params from the route pattern; query params from the handler's reads and any schema; body from the validation schema (Zod, Joi, Yup, class-validator, Pydantic, JSON Schema, a DTO class, a protobuf message) — a declared schema is the best source and gives `Confirmed` types. Where there is no schema and the handler destructures the body ad hoc, reconstruct the contract from the destructuring and mark it `Likely`. Note auth-context headers separately from business inputs.

### Reading validation — and where it's enforced
This is the section people most often get wrong by collapsing it into the contract. Capture **each rule and the layer that enforces it**, because that is what determines what happens when it's violated and where a change has to be made:

| Enforced at | Look for | Typical failure |
|---|---|---|
| Framework / schema middleware | Zod/Joi/Pydantic/class-validator on the route | 400 with a field list |
| Handler pre-checks | explicit `if (!x) throw` before the main work, existence and state checks | 404 / 409 with a domain code |
| Permission checks | guard decorators, middleware, in-handler permission tests | 401 / 403 |
| Service / domain layer | invariant checks deeper in the call stack | domain exception → mapped status |
| Database constraints | `NOT NULL`, `CHECK`, `UNIQUE`, FK, exclusion constraints | 500 or a caught constraint violation |
| Stored procedure | `RAISE`/`THROW` inside the procedure | error propagated to the caller |

A rule enforced *only* by a database constraint is a genuine finding — it usually surfaces to the user as a 500. Note it. Where you find **no validation at all**, write `None — no validation beyond framework type coercion. | Confirmed`; a missing section reads as "we didn't look", an explicit `None` reads as a finding.

### Reading business logic
Write ordered steps of what actually happens, following the handler into services and repositories. Capture: transaction boundaries (what's atomic, what isn't), the order of writes, idempotency guards, state transitions, what is computed in the application versus **in the database**, and what happens on failure (rollback, compensating write, retry). Stop at the point where further depth stops changing a reader's understanding — this is a map, not a transcription. If the logic is genuinely too intricate to summarise faithfully, say so and cite the file rather than writing a lossy version.

### Reading data access — mechanism matters
The `Data Access` table records every object touched, its kind, **how** it's touched, and read/write/execute. Access mechanisms to distinguish:

| Access | How you spot it | Confidence notes |
|---|---|---|
| **ORM** | repository/model calls (`repo.find`, `Model.objects.filter`, `db.query.users`) | `Confirmed` when the model is named statically |
| **Direct Query** | raw SQL strings, query builders, `db.execute` | `Confirmed` if the table name is a literal; `Assumed` if the SQL is composed from variables |
| **Stored Procedure** | `CALL sp_…`, `EXEC`, `SELECT sp_…()` | `Confirmed` — and link the procedure file |
| **Function** | a function invoked in a query or a column default | often only visible in the DDL — check both |
| **View** | a query against a `vw_`/view name | `Confirmed`; link the view file, and the view file links its sources |
| **Repository** | a generic repository or data-access facade | `Assumed` unless you follow it through to the concrete query — do follow it, once |
| **Cache** | Redis/memcached reads on the same key as a table | note it; a cache read that shadows a table is why "the endpoint doesn't touch the DB" is sometimes wrong |
| **External** | an HTTP/SDK call to another service | not a database object — record under *Side Effects*, and cite an `INT-###` under *Integrations* if it is a registered integration |

Also record objects touched **indirectly**: a trigger that fires on a table this endpoint writes, or a table written by a procedure it calls. Mark these clearly (the trigger row, or the procedure's own Objects Touched) — a reader tracing "what writes `audit_log`" must find the endpoint even though its code never names the table. This is one of the highest-value things this whole skill produces; the naive answer is wrong in every trigger-using codebase.

---

## 6. Layer 3 — Pages

One page per route in the frontend router (React Router, Next.js `pages`/`app`, Vue Router, Angular routes, SvelteKit, server-rendered templates with view controllers). A modal, tab, drawer or widget is documented *inside* its page, not as its own unit — same rule as forward planning.

**Page → endpoint links:** trace the page's data calls — a service/api module, `fetch`/`axios`/`httpClient` calls, a generated API client, React-Query/RTK/SWR hooks, server actions, form `action`s, or a loader function. Resolve each call's `METHOD + path` and link the endpoint. `Confirmed` when the URL is a static literal or a named constant you resolved; `Assumed` when it's composed at runtime. When the endpoint lives in another repo, use the `[repo:<key>] ./path` form and make sure that repo's endpoint file gets the back-link (or record it in the registry's *Pending cross-repo links* table (`code-context-templates.md` §8) if that repo hasn't been mapped yet).

Also capture, briefly: page states (loading/empty/error/permission), client-side validation, and the state/caching library and cache keys — the last is what tells a reader why a page shows stale data after a write.

---

## 7. Synthesising the indexes (Pass C)

The indexes are a **retrieval layer**, not a table of contents. Build them from the units you actually wrote.

**The `## Domain Map` entry** — a few lines per domain, answering four things: what the domain *is*; what **kinds** of operations or objects live in it, enumerated concretely enough that a reader can tell whether their need is inside without opening a file ("registration, email verification, activation, password reset, role assignment, soft-deletion"); what it **touches** (the main objects); and **when to look elsewhere** ("what a customer pays for → Subscription"). Write it after the units exist, by reading their summaries — never by guessing what a domain called "billing" probably contains.

**The `## Units` table** — one row per unit, `Summary` copied **verbatim** from the unit's own `## Summary`. Write the summary once, on the unit; mirror it. If you catch yourself composing a different sentence for the index, fix the unit.

**Writing a good `## Summary`** — one sentence, what it does plus why someone would want it. "Handles invoices" is useless. "Generates and finalises an invoice for one subscription period, computing totals and tax through `sp_calculate_invoice_total`" lets a reader decide without opening the file. For a database object: what it holds and its role — "Root customer identity record with lifecycle status; every domain foreign-keys to it."

**Index budget** — a layer index must be readable in one pass. Past ~150 unit rows or ~500 lines, keep the Domain Map and a roll-up in the layer index and move per-unit rows into per-domain `<domain>-index.md` files. Never let an index become a directory listing.

**The database index carries both views** — semantic grouping by business domain in the Domain Map (how a reader thinks) and unit tables grouped by kind (how the files are stored, and how a DBA thinks). Both are required; they're the file's whole reason for existing.

---

## 8. Using a language server (optional — best for the linking pass)

Static reading and framework heuristics get you the *facts* (a route's `METHOD + path`, a table name); a **Language Server Protocol** server (typescript-language-server, pyright, gopls, jdtls, rust-analyzer…) makes the *links between them* far more reliable. Reach for it when link inference is the bottleneck on a large codebase — not as a replacement for framework-aware extraction.

Where it helps most (moves links from `Assumed` → `Confirmed`):

- **find-references / call-hierarchy** — answers "which pages call this endpoint" and "which handlers reach this model" *semantically*, following the symbol across imports and re-exports instead of by regex. The single biggest confidence lever, and the way to follow a generic repository through to its concrete query.
- **go-to-definition** — resolves an API-client call back to the URL constant it actually uses, and a handler back to the ORM model, across files.
- **workspace-symbols / document-symbols** — a structural index of every component/class/handler for the discovery pass, without hand-parsing.

Where it does **not** help (still needs framework-aware reading):

- The mapping facts live in **framework conventions on top of the AST** — decorator strings, router config objects, migration SQL. LSP tells you `createInvoice` is called in three places; it will not tell you it's `POST /accounts/{id}/invoices`. Resolve method, path, route binding and table name yourself.
- **Nothing in the database.** Procedures, functions, triggers, views and constraints are invisible to a language server — they're SQL in migration files. The DB layer is always read by parsing DDL.
- Dynamic routing, code-gen, metaprogramming and reflection stay `Assumed`/open-question exactly as before — LSP resolves only what the compiler does.

Cost note: standing up a language server per stack and indexing the repo is real infrastructure and a per-language matrix. For a first cut, **tree-sitter/ctags for enumeration + framework heuristics for semantics + ripgrep for call sites** gets ~80% with far less machinery; add LSP specifically when high-confidence cross-file reference resolution at scale is worth the setup.

---

## 9. Confidence — be honest about what the code shows

Use the shared vocabulary (`Confirmed · Likely · Assumed · Conflicting · Needs Clarification`) on every inferred fact and link:

- **Confirmed** — read directly and unambiguously (a static route literal, a declared column, a `CALL sp_x` naming the procedure).
- **Likely** — a strong, conventional inference (a service method named `getInvoices` calling `/invoices`; a document shape reconstructed from consistent write paths).
- **Assumed** — inferred to fill a gap (a dynamically built URL, a generic repository not followed through, a procedure body not in the repo).
- **Conflicting / Needs Clarification** — the code contradicts itself (two migrations disagree; a schema and an ORM model diverge) or is opaque (reflection, code-gen, metaprogramming). Raise an **open question** on the unit; don't pick a story.

A map that is 70% `Confirmed` and honest about the 30% is far more useful than one that looks 100% clean and is quietly wrong.

### Frontmatter marker

Every reverse-mapped unit carries, in addition to the standard template frontmatter:

```yaml
origin: reverse-mapped        # vs authored forward by tl-feature-planning
mapped_from: "src/..."        # the primary source file the unit was read from
mapped_from_commit: a1b2c3d   # the commit the repo was at when mapped (omit if unavailable)
map_confidence: Confirmed     # overall confidence for this unit
```

Forward planning ignores `origin`; it just sees a normal unit to reuse and link a feature to. When `/tl:plan` later links a feature, it adds the `FEAT-…` to the unit and index as usual — leave the markers in place as provenance.

---

## 10. Reconciliation & re-runs

- **Existing tree:** match by key and **extend** — add newly discovered links, columns and callers; don't overwrite. Never duplicate a unit that already exists under a different slug; fix the slug or merge.
- **Preserve interpretation.** `Business Purpose` and Domain Map prose accumulate human edits over time. On a re-run, keep them unless the code contradicts them — regenerate the *derived* sections (columns, contracts, links, data access) and leave the reasoned prose alone, noting a conflict rather than silently rewriting.
- **`refresh=changed`:** diff against the recorded `mapped_from_commit` and re-derive only units whose source files changed, plus anything linking to them. Re-synthesise the affected Domain Map entries and index rows; bump `generated_at` and `mapped_from_commit` on touched files only.
- **Deleted code:** mark the unit `Removed` and set its coverage row to `removed`; don't delete the file. A committed tree with a retirement history is more useful than one that silently loses rows.
- **Scope control:** honour `layers=`, `scope=` and `domains=` so a large monorepo can be mapped a slice at a time. A partial run must still leave a valid tree — write the indexes for the layers it covered and say in the root index which layers are unmapped.

---

## 11. Integrity bar

Run `tl-feature-planning`'s link-integrity check, plus these map-specific ones:

- **Coverage:** every `map-coverage.md` row is `mapped`, `skipped`-with-a-note, or `removed` — no row left `pending`. A `skipped` row must have a matching finding.
- **Index integrity:** every unit file has a `## Summary`; every index row's `Summary` matches its unit's verbatim; every layer index has a `## Domain Map` covering every domain that has units; no index exceeds the budget without being split.
- **Back-links:** every page→endpoint, endpoint→object, view→source, procedure→object and trigger→table link has its reverse. Cross-repo links resolve through the registry, or are listed in the registry's *Pending cross-repo links* table.
- **Triggers and procedures are linked from the tables they touch** — the check that most often catches a shallow map.
- Endpoints with no caller and no discoverable trigger — flag (dead code, or an external caller).
- Objects not referenced by any endpoint or object — flag as possible orphan/reference data.
- Any link below `Likely` confidence — surfaced so a human (or a later spec review) can verify.
- **No secrets, credentials, connection strings or customer data anywhere in the tree** — it is about to be committed.
