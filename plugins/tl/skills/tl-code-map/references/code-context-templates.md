# Code-context file templates

The exact schema for every file `/tl:code-map` writes into a repository's **`code-context/`** tree: the root index and README, the three layer indexes (semantic-first), the per-unit files (page, endpoint, database object), the coverage manifest, and the workspace registry that ties several repos together. Build every file from these so the tree stays uniform, bidirectionally linked, machine-parseable, and — critically — **readable index-first**.

These templates are a **superset** of `tl-feature-planning`'s `references/context-file-templates.md`. Same IDs, same match keys, same link discipline, same controlled vocabulary. The additions are: a repo-root output location, kind-grouped database folders, a one-line `Summary` on every unit, semantic **Domain Map** sections on every index, and the endpoint's `Validation` / `Business Logic` / `Data Access` sections. A file written from these templates is still a valid unit for forward planning to reuse.

Slugs are **lowercase kebab-case**. IDs are stable and append-only: `PAGE-<AREA>-NN`, `EP-<AREA>-NN`, `ENT-<AREA>-NN`. Links inside one repo are **relative paths**; links across repos go through the registry (see §8). Confidence uses the shared vocabulary: `Confirmed · Likely · Assumed · Conflicting · Needs Clarification`.

---

## 0. Where the tree lives, and why

The tree lives at **`<repo>/context/code-context/`** — a `context/` folder at the root of the mapped repository, with `code-context/` inside it — and is **committed with the code**. It is not inside `.jetrix/` (that folder is gitignored, so a tree written there would be local-only and lost on a fresh clone) and not at workspace level — even when `/tl:code-map` is run from a parent workspace over several repos, each repo's context is written into that repo. The context then travels with the code: it is reviewable in a pull request, it diffs when the code changes, and any agent or human who clones the repo gets it.

```text
<repo>/context/code-context/        # a context/ folder at the repo root, code-context/ inside it
├── README.md                       # what this is + the index-first read protocol (for humans and agents)
├── code-context-index.md           # ROOT index — layers present, domain list, where to start
├── map-coverage.md                 # the coverage manifest (enumerated vs mapped vs skipped)
├── backend/
│   ├── _overview.md                # stack, conventions, entry points for this layer
│   ├── backend-index.md            # SEMANTIC index: Domain Map + unit table
│   └── domains/<domain>/
│       ├── <domain>-index.md       # OPTIONAL — only when the layer index outgrows one pass (§3.d)
│       └── endpoints/<slug>.md     # EP-<AREA>-NN, one file per operation
├── frontend/
│   ├── _overview.md
│   ├── frontend-index.md
│   └── pages/<area>/<slug>.md      # PAGE-<AREA>-NN, one file per routed surface
└── database/
    ├── _overview.md
    ├── database-index.md
    ├── tables/<slug>.md            # ENT-<AREA>-NN, Kind: Table
    ├── views/<slug>.md             # Kind: View
    ├── collections/<slug>.md       # Kind: Collection      (NoSQL — document stores)
    ├── procedures/<slug>.md        # Kind: Stored Procedure
    ├── functions/<slug>.md         # Kind: Function
    └── triggers/<slug>.md          # Kind: Trigger
```

Only create the layer folders and the kind folders that the repo actually has. A relational repo has no `collections/`; a document-store repo has no `procedures/`. An empty folder is noise — omit it, and say so in the layer `_overview.md`.

**Never write into `code-context/`:** secrets, connection strings, credentials, tokens, customer data, or copied production rows. It is a checked-in, shareable description of *structure and intent* — column names and types yes, sample values no.

---

## 1. The index-first read protocol (the point of the whole tree)

Everything below is shaped by one rule: **an agent should be able to answer "which files do I need?" without opening a single unit file.** The indexes are a semantic routing layer; the unit files are the payload. State this protocol in the repo's `code-context/README.md` verbatim so every consumer follows it:

1. Read `code-context/code-context-index.md` — one page. It says which layers exist and lists every domain with a one-line meaning.
2. Read the relevant **layer index**'s `## Domain Map` — a paragraph per domain describing *what kinds of things live there*. Pick the domain(s).
3. Scan that domain's rows in the layer index's `## Units` table — each row carries a one-line `Summary`. Pick the specific unit(s).
4. **Only now** open the unit file(s), plus the layer `_overview.md` if you need stack conventions.

That is at most three cheap reads before a targeted one, instead of a directory walk. Two rules keep it true:

- **Index budget.** A layer index must stay readable in a single pass. If its `## Units` table passes ~150 rows or the file passes ~500 lines, split: leave the `## Domain Map` and a domain-level roll-up in the layer index, and move the per-unit rows into per-domain `<domain>-index.md` files (§3.d). Never let the layer index become a directory listing.
- **Summaries are copied, not rewritten.** Every unit file carries a `## Summary` — one sentence. The index row's `Summary` cell is **that exact sentence**. It is written once, on the unit, and mirrored into the index, so the two can never disagree. If you find yourself composing a different summary for the index, fix the unit instead.

---

## 2. Root files and layer overviews

### 2.a `code-context/README.md`

```md
---
doc_type: code-context-readme
schema_version: 1.3
produced_by: tl
status: Emerging
generated_at: YYYY-MM-DD
---

# Code Context

A machine-first, as-built description of this repository: every page, every endpoint,
and every database object, grouped by business domain, with the links between them.
Generated by `/tl:code-map` (Techjays Delivery OS) from the code in this repo — **derived,
never invented**. It is committed with the code so it travels with the repo and diffs
in review.

## How to read this (index first — please follow this order)

1. `code-context-index.md` — layers and domains, one line each.
2. The layer index (`backend/backend-index.md`, `frontend/frontend-index.md`,
   `database/database-index.md`) → its **Domain Map** section. Pick a domain.
3. The **Units** table in that index → pick the specific unit by its one-line summary.
4. Open only that unit file.

Do not walk the folders to find something. The indexes exist so you don't have to.

## What is here
| Layer | Units | Index |
|---|---|---|
| Backend | 84 endpoints across 5 domains | ./backend/backend-index.md |
| Frontend | — lives in `acme-web` | see the workspace registry |
| Database | 63 objects (34 tables, 5 views, 14 procedures, 4 functions, 6 triggers) | ./database/database-index.md |

## Trust and staleness
Every unit cites the source file it was read from and carries a confidence.
`Confirmed` = read directly from the code. `Assumed` = inferred; verify before relying on it.
Mapped from commit `a1b2c3d` on YYYY-MM-DD. Re-run `/tl:code-map` after significant changes;
`map-coverage.md` records anything that could not be mapped confidently.

## Boundaries
This describes what the code **does**, not what the product **should** do. Business
requirements live in the Delivery OS workspace (`ba/`), not here.
```

### 2.b `code-context/code-context-index.md` — the root hop

One page. No unit rows — it routes to layer indexes and names the domains.

```md
---
doc_type: code-context-index
schema_version: 1.3
produced_by: tl
status: Emerging
repo: acme-api
layers: [backend, database]
mapped_from_commit: a1b2c3d
generated_at: YYYY-MM-DD
---

# Code Context Index — acme-api

## What this repository is
A Node/Express REST API over PostgreSQL serving the Acme customer portal. Owns
accounts, billing, and subscriptions; the customer-facing UI lives in `acme-web`
(see the workspace registry).

## Layers
| Layer | Present | Units | Index |
|---|---|---|---|
| Backend (endpoints, jobs, webhooks) | yes | 84 | ./backend/backend-index.md |
| Frontend (pages) | no — separate repo `acme-web` | — | — |
| Database (tables, views, procedures, functions, triggers) | yes | 63 | ./database/database-index.md |

## Domains
The business domains this repo is organised into. Each maps to a backend domain
folder and a cluster of database objects.

| Domain | Area | One-line meaning | Backend | Database objects |
|---|---|---|---|---|
| Account | ACC | Customer identity, registration, activation, profile and deactivation | 18 endpoints | 9 |
| Billing | BIL | Invoices, payments, credit notes, dunning and tax calculation | 24 endpoints | 17 |
| Subscription | SUB | Plans, subscription lifecycle, upgrades/downgrades, entitlements | 21 endpoints | 14 |
| Notification | NTF | Templated email/SMS dispatch and delivery tracking | 9 endpoints | 6 |
| Core | CORE | Cross-cutting: auth, audit, feature flags, health | 12 endpoints | 17 |

## Coverage and confidence
147 of 150 enumerated units mapped · 3 skipped (see ./map-coverage.md) ·
Confidence: 71% Confirmed, 22% Likely, 7% Assumed.

## Cross-repo
This repo's endpoints are consumed by `acme-web`. Resolve cross-repo links through
the workspace registry: `<workspace>/.jetrix/tl/code-map-registry.md`.
```

### 2.c `<layer>/_overview.md` — one per layer

Written in Pass A, before any unit file, so every unit below can stay lean and inherit the stack
and conventions from one place. It holds **no per-unit facts** and never duplicates a unit. Same
schema as forward planning's `_overview.md` (`doc_type: layer-overview`), at `schema_version: 1.3`
with the reverse-map provenance fields added.

```md
---
doc_type: layer-overview
schema_version: 1.3
produced_by: tl
layer: backend            # frontend | backend | database
origin: reverse-mapped
repo: acme-api
status: Emerging
mapped_from_commit: a1b2c3d
generated_at: YYYY-MM-DD
---

# Backend Overview

## Stack
Node 20 + TypeScript, Express 4. Routing: one router module per domain, mounted in
`src/app.ts`. Data: TypeORM 0.3 over PostgreSQL 15, with raw SQL for bulk paths.
Validation: Zod schemas in `src/schemas/`, applied by `validate()` middleware.

## Conventions
Endpoints under `src/routes/<domain>/<name>.controller.ts`; business logic in
`src/services/`; data access in `src/repositories/`. Auth is JWT via
`requireAuth`/`requirePermission` middleware. Errors are thrown as `AppError` and
mapped to status codes centrally in `src/middleware/error.ts`.

## Entry Points
HTTP: `src/app.ts` (router mounting) · Jobs: `src/jobs/index.ts` (node-cron) ·
Queue consumers: `src/workers/` · Webhooks: `src/routes/webhooks/`.

## Kinds present
<!-- database layer only: which kind folders exist and which are absent, and why. -->
tables, views, procedures, functions, triggers. No collections — PostgreSQL only.

## Notes
Money is computed in stored procedures, not in application code — see the Billing
domain map. Tenant isolation is enforced by a TypeORM subscriber, not per-query.
```

---

## 3. Layer indexes — semantic summary **plus** unit table

Every layer index has the same two-part shape: a `## Domain Map` you read to *decide*, and a `## Units` table you read to *locate*. The Domain Map is the enhancement that makes the index a first-class retrieval surface rather than a table of contents.

A Domain Map entry answers four questions in a few lines: **what this domain is**, **what kinds of operations/objects live in it** (so a reader can tell whether their need is in here without opening anything), **what it depends on**, and **when to look elsewhere**. Write it from the units you actually mapped — it is a synthesis, never a guess.

### 3.a `backend/backend-index.md`

```md
---
doc_type: endpoint-index          # keeps forward-planning consumers working by doc_type
schema_version: 1.3
produced_by: tl
layer: backend
origin: reverse-mapped
repo: acme-api
status: Emerging
mapped_from_commit: a1b2c3d
generated_at: YYYY-MM-DD
---

# Backend Index — acme-api

84 endpoints across 5 domains. Stack and conventions: ./_overview.md

## Domain Map

Read this first. Find your domain here, then jump to its rows in **Units** below.

### Account — `ACC` · 18 endpoints · ./domains/account/
Everything about *who a customer is*. Covers the full identity lifecycle:
registration and email verification, activation and reactivation, login/session
issuance, profile and preference reads and writes, password reset, role and
permission assignment, and soft-deletion/anonymisation. Read-heavy lookups
(`GET /accounts`, `GET /accounts/{id}`) sit alongside the lifecycle transitions,
each of which writes `account_status_history` and an audit row.
**Touches:** `accounts`, `account_profiles`, `account_roles`, `sessions`, `audit_log`.
**Not here:** what a customer *pays for* → Subscription. Invoices → Billing.

### Billing — `BIL` · 24 endpoints · ./domains/billing/
Money in and money owed. Invoice generation (on-demand and via the nightly
`invoice-run` job), payment capture and refunds through the PSP, credit notes,
dunning/retry escalation, tax calculation, and statement export. The heaviest
stored-procedure usage in the repo — invoice totalling and tax are computed in
`sp_calculate_invoice_total` / `fn_tax_rate_for`, not in application code, so read
the procedure files as well as the endpoints.
**Touches:** `invoices`, `invoice_lines`, `payments`, `credit_notes`, `tax_rates`,
`vw_outstanding_balance`, `sp_calculate_invoice_total`.
**Not here:** plan pricing definitions → Subscription.

### Core — `CORE` · 12 endpoints · ./domains/core/
Cross-cutting infrastructure surfaces rather than a business capability: auth
token issue/refresh/revoke, health and readiness probes, feature-flag reads, the
audit query API, and two internal admin endpoints. Nothing here is customer-facing.
**Touches:** `audit_log`, `feature_flags`, `sessions`.

<!-- one block per domain -->

## Units

One row per endpoint. `Summary` is copied verbatim from the unit file's `## Summary`.

| Endpoint ID | Method + Path | Domain | Summary | Called by | Reads/Writes | Used by Features | File |
|---|---|---|---|---|---|---|---|
| EP-ACC-01 | GET /accounts | Account | Lists accounts with filtering by status and search on name or email. | PAGE-ACC-01 (acme-web) | accounts (R), account_profiles (R) | (as-built) | ./domains/account/endpoints/list-accounts.md |
| EP-ACC-02 | POST /accounts | Account | Registers a new account in Pending state and sends the verification email. | PAGE-ACC-02 (acme-web) | accounts (W), audit_log (W) | (as-built) | ./domains/account/endpoints/create-account.md |
| EP-ACC-07 | POST /accounts/{id}/activate | Account | Activates a verified account, writing status history and emitting account.activated. | PAGE-ACC-01, PAGE-ACC-03 (acme-web) | accounts (W), account_status_history (W) | FEAT-ACC-004 | ./domains/account/endpoints/activate-account.md |
| EP-BIL-14 | (Schedule) nightly-invoice-run | Billing | Generates invoices for all subscriptions due today via sp_calculate_invoice_total. | Trigger: Schedule (02:00 UTC) | sp_calculate_invoice_total (X), invoices (W) | (as-built) | ./domains/billing/endpoints/nightly-invoice-run.md |
```

**Called by** is a page ID, or `Trigger: Schedule/Event/Webhook/Service` for non-UI entry points. When the caller lives in another repo, suffix the repo key: `PAGE-ACC-01 (acme-web)`.
**Reads/Writes** is a compact roll-up of the unit's Data Access table: `object (R|W|RW|X)`, where `X` = executes (procedure/function). Cap it at the five most significant objects and append `…` — the unit file has the full list.
**Used by Features** is `(as-built)` until a `/tl:plan` run links a feature to the unit — the same column and the same convention forward planning uses, so the two directions share one index.
**Status** (controlled): `Proposed · Designed · In Development · Released · Blocked` (+ retirement `Merged into … · Deferred · Removed`). Reverse-mapped units are `Released` when the code is on the mapped branch.

### 3.b `frontend/frontend-index.md`

Same two-part shape. `doc_type: page-index`.

```md
## Domain Map

### Account — `ACC` · 7 pages · ./pages/account/
The signed-out and self-service identity surfaces: sign-up, email verification
landing, sign-in, forgot/reset password, the account profile page and its
preferences tab, and the admin account list with its detail drawer. All of them
talk to the Account domain in `acme-api`; none of them read the database directly.
**Not here:** the plan-selection step of sign-up → Subscription (`SUB`).

## Units

| Page ID | Page | Route | Area | Summary | Used by Features | Consumes Endpoints | File |
|---|---|---|---|---|---|---|---|
| PAGE-ACC-01 | Account List | /admin/accounts | Account | Admin table of all accounts with status filter, search and bulk activate. | (as-built) | EP-ACC-01, EP-ACC-07 | ./pages/account/account-list.md |
| PAGE-ACC-02 | Sign Up | /signup | Account | Public registration form; collects identity, validates uniqueness, creates a Pending account. | (as-built) | EP-ACC-02 | ./pages/account/sign-up.md |
```

### 3.c `database/database-index.md` — domains **and** object kinds

The database index carries the extra load: it groups objects **semantically by business domain** (which is how a reader thinks) while the files themselves are **grouped on disk by kind** (which is how a database is administered). The index is what reconciles the two, so it needs both views.

```md
---
doc_type: entity-index
schema_version: 1.3
produced_by: tl
layer: database
origin: reverse-mapped
repo: acme-api
status: Emerging
mapped_from_commit: a1b2c3d
generated_at: YYYY-MM-DD
---

# Database Index — acme-api

63 objects: 34 tables · 5 views · 14 stored procedures · 4 functions · 6 triggers ·
0 collections. Engine, migration tool and schema location: ./_overview.md

## Domain Map

Read this first — objects are described here by **business domain**; the files are
stored by **kind** (tables/, views/, procedures/ …). Both are linked below.

### Account — 9 objects
The identity core. `accounts` is the root record every other domain foreign-keys
to; `account_profiles` holds the mutable, PII-bearing detail split out from it,
and `account_roles` the permission grants. Lifecycle is append-only in
`account_status_history` — status transitions are never edited in place, which is
why activation and deactivation both write two rows. `sessions` is short-lived,
purged nightly. One trigger (`trg_account_audit`) mirrors every write on
`accounts` into `audit_log`.
**Tables:** accounts · account_profiles · account_roles · account_status_history · sessions
**Views:** vw_active_accounts · **Procedures:** sp_anonymise_account
**Triggers:** trg_account_audit · trg_account_status_history
**Contains PII:** account_profiles, accounts (email).

### Billing — 17 objects
Where the real business logic of this system lives — much of it *in the database*
rather than the application. `invoices`/`invoice_lines` are the ledger;
`sp_calculate_invoice_total` computes line totals, discounts and tax in one
transaction and is called by both the nightly run and the on-demand endpoint, so
changing it changes both. `fn_tax_rate_for` resolves a jurisdiction to a rate from
`tax_rates` (effective-dated — always filter by date). `vw_outstanding_balance`
is the single source for "what does this account owe" and is read by three
endpoints and the dunning job.
**Tables:** invoices · invoice_lines · payments · payment_attempts · credit_notes ·
credit_note_lines · tax_rates · dunning_events
**Views:** vw_outstanding_balance · vw_invoice_summary
**Procedures:** sp_calculate_invoice_total · sp_apply_payment · sp_issue_credit_note ·
sp_run_dunning_cycle · **Functions:** fn_tax_rate_for · fn_next_invoice_number
**Triggers:** trg_invoice_line_recalc

### Core / shared — 17 objects
Not owned by one domain: `audit_log` (written by every domain's trigger),
`feature_flags`, `outbox_events` (the transactional outbox the notification worker
drains), and the migration bookkeeping tables. Reference/seed data —
`countries`, `currencies` — has no writing endpoint by design.

<!-- one block per domain — Subscription (14 objects) and Notification (6) omitted here for brevity -->

## Objects by kind

### Tables (34)
| Entity ID | Table | Domain | Summary | Source DATA-### | Used by Endpoints | File |
|---|---|---|---|---|---|---|
| ENT-ACC-01 | accounts | Account | Root customer identity record with lifecycle status; every domain foreign-keys to it. | — | EP-ACC-01, EP-ACC-02, EP-ACC-07 … | ./tables/accounts.md |
| ENT-BIL-01 | invoices | Billing | Invoice header — account, period, totals, status; lines live in invoice_lines. | — | EP-BIL-03, EP-BIL-05, EP-BIL-14 | ./tables/invoices.md |

### Views (5)
| Entity ID | View | Domain | Summary | Reads From | Used by Endpoints | File |
|---|---|---|---|---|---|---|
| ENT-BIL-09 | vw_outstanding_balance | Billing | Per-account outstanding balance: invoices less payments and credit notes. | invoices, payments, credit_notes | EP-BIL-03, EP-BIL-05, EP-BIL-11 | ./views/vw-outstanding-balance.md |

### Stored Procedures (14)
| Entity ID | Procedure | Domain | Summary | Touches | Called by | File |
|---|---|---|---|---|---|---|
| ENT-BIL-11 | sp_calculate_invoice_total | Billing | Computes line totals, discounts and tax for one invoice and writes the header totals. | invoice_lines (RW), invoices (W), fn_tax_rate_for (X) | EP-BIL-03, EP-BIL-14 | ./procedures/sp-calculate-invoice-total.md |

### Functions (4)
| Entity ID | Function | Domain | Summary | Returns | Called by | File |
|---|---|---|---|---|---|---|
| ENT-BIL-13 | fn_tax_rate_for | Billing | Resolves the effective tax rate for a jurisdiction and date from tax_rates. | numeric(5,4) | sp_calculate_invoice_total, EP-BIL-08 | ./functions/fn-tax-rate-for.md |

### Triggers (6)
| Entity ID | Trigger | Domain | Summary | Fires On | Calls | File |
|---|---|---|---|---|---|---|
| ENT-ACC-08 | trg_account_audit | Account | Mirrors every insert/update/delete on accounts into audit_log. | accounts — AFTER INSERT/UPDATE/DELETE | (inline) | ./triggers/trg-account-audit.md |

### Collections (0)
None — this repo uses PostgreSQL only. (In a document store: one row per collection,
with the document shape summarised and embedded-vs-referenced relations noted.)
```

**Kind** (controlled): `Table · Collection · View · Stored Procedure · Function · Trigger`. **Source DATA-###** — carried on the Tables and Collections tables only — links to the BA data-register when the workspace has one; `—` is normal and expected for reverse-mapped objects, and views, procedures, functions and triggers have no business-register counterpart at all, so they omit the column. Add a **Used by Features** column to any of these tables once forward planning links features to the objects (`(as-built)` until then), so the file stays the one index both directions share.

### 3.d Per-domain sub-index (only when the layer index outgrows one pass)

When a layer index would exceed the budget in §1, keep the `## Domain Map` and a roll-up table in the layer index, and move the unit rows down:

```md
---
doc_type: endpoint-index
schema_version: 1.3
produced_by: tl
layer: backend
domain: billing
parent_index: ../../backend-index.md
origin: reverse-mapped
repo: acme-api
status: Emerging
mapped_from_commit: a1b2c3d
generated_at: YYYY-MM-DD
---

# Billing — Endpoint Index

<!-- the same Domain Map block as the parent, verbatim, so this file also stands alone -->
<!-- then the ## Units table filtered to this domain, identical columns -->
```

The layer index's roll-up row then reads: `| Billing | BIL | 24 | ./domains/billing/billing-index.md |`.

---

## 4. endpoint.md

One backend operation: what it is for, what it takes, what it validates, what it does, and **every database object it touches and how**. Never copies an entity's columns — links to it.

```md
---
doc_type: endpoint
schema_version: 1.3
produced_by: tl
endpoint_id: EP-BIL-03
status: Released
implementation_state: Implemented
origin: reverse-mapped
mapped_from: "src/routes/billing/invoice.controller.ts"
mapped_from_commit: a1b2c3d
map_confidence: Confirmed
generated_at: YYYY-MM-DD
---

# Endpoint: Generate Invoice

## Endpoint ID
EP-BIL-03

## Summary
<!-- ONE sentence. Copied verbatim into the index row. What it does + why someone would call it. -->
Generates and finalises an invoice for one subscription period, computing totals and tax through sp_calculate_invoice_total.

## Method + Path
POST /accounts/{accountId}/invoices

## Domain
Billing

## Status
Released

## Purpose
Produces a finalised invoice for a given account and billing period on demand —
the manual counterpart to the nightly `invoice-run` job (EP-BIL-14), used by
support when a customer disputes or requests an early invoice. Idempotent per
(account, period): a second call returns the existing invoice rather than a duplicate.

## Trigger
Called by page(s) — see *Called by*.
<!-- For non-UI endpoints: Schedule | Event | Webhook | Service, with the specifics:
     cron expression, queue + message type, external sender, calling service. -->

## Request
### Path parameters
| Name | Type | Required | Notes | Confidence |
|---|---|---|---|---|
| accountId | uuid | yes | Must reference an active account | Confirmed |

### Query parameters
| Name | Type | Required | Default | Notes | Confidence |
|---|---|---|---|---|---|
| dryRun | boolean | no | false | Computes and returns totals without persisting | Confirmed |

### Body
| Field | Type | Required | Notes | Confidence |
|---|---|---|---|---|
| periodStart | date | yes | ISO-8601; inclusive | Confirmed |
| periodEnd | date | yes | ISO-8601; inclusive; must be ≥ periodStart | Confirmed |
| lineItemOverrides | array<LineOverride> | no | Support-only; requires `billing.override` | Confirmed |
| notes | string | no | Max 500 chars; printed on the invoice | Confirmed |

### Headers / Auth context
`Authorization: Bearer <jwt>` — required. Tenant is resolved from the token, not the path.

## Validation
<!-- Every check that can reject the request BEFORE business logic runs, and WHERE it is
     enforced — that is the part a reader can't get from the contract alone. -->
| Rule | Enforced at | Failure | Confidence |
|---|---|---|---|
| Body matches the `GenerateInvoiceSchema` (types, required fields, max lengths) | Zod middleware — `src/middleware/validate.ts` | 400 `VALIDATION_ERROR` with field list | Confirmed |
| `periodEnd >= periodStart` and period ≤ 366 days | Zod refinement — same schema | 400 `INVALID_PERIOD` | Confirmed |
| Account exists and is not `Deactivated` | Handler, pre-check query | 404 / 409 `ACCOUNT_INACTIVE` | Confirmed |
| No finalised invoice already covers this period | Handler, pre-check query | 200 with the existing invoice (idempotent) | Confirmed |
| `lineItemOverrides` requires the `billing.override` permission | Handler, after auth middleware | 403 `FORBIDDEN_OVERRIDE` | Confirmed |
| `invoices.invoice_number` uniqueness | Database — unique constraint | 500 on collision; retried once via fn_next_invoice_number | Likely |

## Business Logic
<!-- Ordered, what actually happens. This is the section a coding agent reads to change behaviour. -->
1. Resolve the account and its active subscription for the period; reject if none (409 `NO_SUBSCRIPTION`).
2. Open a transaction.
3. Insert the invoice header in `Draft` with a number from `fn_next_invoice_number`.
4. Expand subscription entitlements and any usage rows in the period into `invoice_lines`; apply `lineItemOverrides` where supplied.
5. Call `sp_calculate_invoice_total` — this is where line totals, proration, discounts and tax are computed and written back to the header. **The application does not calculate money.**
6. Transition the invoice to `Issued` and stamp `issued_at`.
7. Write an `audit_log` entry (also written by `trg_invoice_line_recalc` for the lines).
8. Enqueue `invoice.issued` to `outbox_events` for the notification worker.
9. Commit. On any failure the whole transaction rolls back and no invoice number is consumed (numbers come from a sequence — gaps are possible and acceptable).
- With `dryRun=true`, steps 3–8 run inside a transaction that is **rolled back**; the computed totals are returned.

## Reads / Writes Entities
<!-- Forward planning names this section `Reads / Writes Entities`; the heading is kept verbatim so
     a unit written here is still a unit /tl:plan can read and extend. The table below is the
     enhancement: every database object this endpoint touches and HOW it touches it.
     Kind: Table | View | Collection | Stored Procedure | Function | Trigger
     Access: ORM | Direct Query | Stored Procedure | Function | View | Repository | Cache
             (an HTTP/SDK call to another service is NOT a database object — it goes under Side Effects)
     Mode: R (read) | W (write) | RW | X (executes) | — (indirect, e.g. a trigger that fires on a write here) -->
| Object | Kind | Access | Mode | Via | File | Confidence |
|---|---|---|---|---|---|---|
| accounts | Table | ORM (TypeORM) | R | `accountRepo.findOneBy` | ../../../../database/tables/accounts.md (ENT-ACC-01) | Confirmed |
| subscriptions | Table | ORM (TypeORM) | R | `subscriptionRepo.findActive` | ../../../../database/tables/subscriptions.md (ENT-SUB-01) | Confirmed |
| invoices | Table | ORM + Direct Query | RW | insert via repo; status update via raw SQL | ../../../../database/tables/invoices.md (ENT-BIL-01) | Confirmed |
| invoice_lines | Table | Direct Query | W | bulk `INSERT … SELECT` in `invoice.repository.ts:88` | ../../../../database/tables/invoice-lines.md (ENT-BIL-02) | Confirmed |
| sp_calculate_invoice_total | Stored Procedure | Stored Procedure | X | `CALL sp_calculate_invoice_total($1)` | ../../../../database/procedures/sp-calculate-invoice-total.md (ENT-BIL-11) | Confirmed |
| fn_next_invoice_number | Function | Function | X | in the insert's DEFAULT | ../../../../database/functions/fn-next-invoice-number.md (ENT-BIL-14) | Confirmed |
| vw_outstanding_balance | View | View | R | read for the response's `balanceAfter` | ../../../../database/views/vw-outstanding-balance.md (ENT-BIL-09) | Likely |
| audit_log | Table | ORM | W | `auditService.record` | ../../../../database/tables/audit-log.md (ENT-CORE-01) | Confirmed |
| outbox_events | Table | Direct Query | W | same transaction as the invoice | ../../../../database/tables/outbox-events.md (ENT-CORE-04) | Confirmed |
| invoice_lines (via trg_invoice_line_recalc) | Trigger | Trigger | — | fires on the line insert | ../../../../database/triggers/trg-invoice-line-recalc.md (ENT-BIL-15) | Confirmed |

<!-- File paths: this file is code-<repo>/context/code-context/backend/domains/<domain>/endpoints/<slug>.md
     → four levels up reaches code-context/.
     Indirect rows (Mode `—`) matter: a reader tracing "what writes audit_log" must find this
     endpoint even though its own code never names the table. -->

## Response
- `201 Created` → `{ invoiceId, invoiceNumber, status: "Issued", total, currency, balanceAfter }`
- `200 OK` → the existing invoice, when one already covers the period (idempotent replay)
- `200 OK` → computed totals with no `invoiceId`, when `dryRun=true`
- `400` `VALIDATION_ERROR` · `INVALID_PERIOD`
- `403` `FORBIDDEN_OVERRIDE` — lacks `billing.override`
- `404` account not found · `409` `ACCOUNT_INACTIVE` · `NO_SUBSCRIPTION`
- `500` — transaction rolled back; no partial invoice

## Auth
Requires a valid JWT and the `billing.write` permission; `lineItemOverrides` additionally
requires `billing.override`. Tenant isolation is enforced by a row-level `tenant_id`
filter injected in the ORM subscriber (`src/db/tenant.subscriber.ts`). | Confirmed

## Side Effects
- Emits `invoice.issued` to `outbox_events`; the notification worker (EP-NTF-04) sends the customer email.
- `trg_invoice_line_recalc` fires on line insert and recalculates the line extended amount.
- No email, file or cache write happens synchronously in this request.

## Integrations
- None synchronous. The PSP is only involved at payment time (EP-BIL-06).
<!-- When present, cite INT-### from the BA integration-register: e.g. CRM sync — INT-002. -->

## Called by
<!-- Same-repo callers are relative paths — four levels up to code-context/, e.g.
       - PAGE-BIL-02 Billing Admin — ../../../../frontend/pages/billing/billing-admin.md
     This example repo (acme-api) has no frontend layer, so all three callers live in acme-web
     and use the [repo:<key>] form, resolved through the registry (§8). -->
- PAGE-BIL-02 Billing Admin — [repo:acme-web] ./frontend/pages/billing/billing-admin.md (PAGE-BIL-02) | Confirmed
- PAGE-BIL-04 Invoice Detail — [repo:acme-web] ./frontend/pages/billing/invoice-detail.md | Confirmed
- PAGE-BIL-07 Support Console — [repo:acme-web] ./frontend/pages/billing/support-console.md | Likely

## Behaviour / Business Rules
<!-- Forward planning's heading, kept verbatim. `Business Logic` above is the ordered how;
     this is the WHAT-must-hold — rules the CODE enforces, derived from it. Cite a BA BR-### only
     if the workspace has one and it genuinely matches; otherwise state the rule as read and
     leave the citation as `—`. -->
- One finalised invoice per account per period (idempotency guard). | Confirmed | BR-—
- Money is computed in the database, never in the application layer. | Confirmed | BR-—
- Invoice numbers are sequence-derived and may have gaps. | Confirmed | BR-—

## Used by Features
(as-built) — no feature linked yet. A later `/tl:plan` adds `FEAT-…` rows here and in the index.

## Open Questions
- OQ-BIL-03 | `dryRun` rolls back a transaction that has already consumed an invoice number — is the gap intentional or a defect? | TL / Billing owner | Affects number continuity | Open

## Source References
- [code › src/routes/billing/invoice.controller.ts] — route declaration + handler
- [code › src/services/invoice.service.ts] — business logic steps 3–8
- [code › src/repositories/invoice.repository.ts] — direct queries
- [code › db/migrations/0042_sp_calculate_invoice_total.sql] — the procedure
- [code › src/schemas/billing/generate-invoice.schema.ts] — validation
```

**Sections are never deleted.** Where there is genuinely nothing, write the labelled placeholder: `None.` / `TBD` / `Open question — see below`. An absent *Validation* section reads as "we didn't look"; `None — no validation beyond framework type coercion. | Confirmed` reads as a finding.

---

## 5. page.md

One routed surface — what it is, who uses it, and the endpoints it consumes. Every heading forward planning's `page.md` defines is kept **verbatim** so the file stays a unit `/tl:plan` can read and extend; the reverse-map additions are `## Summary`, `## Area`, `## State & Data Handling`, `## Client-side Validation`, and the `origin`/`mapped_from`/`mapped_from_commit`/`map_confidence` frontmatter.

```md
---
doc_type: page
schema_version: 1.3
produced_by: tl
page_id: PAGE-ACC-01
status: Released
implementation_state: Implemented
origin: reverse-mapped
mapped_from: "src/pages/admin/AccountList.tsx"
mapped_from_commit: 7f3e9c1
map_confidence: Confirmed
generated_at: YYYY-MM-DD
---

# Page: Account List

## Page ID
PAGE-ACC-01

## Summary
Admin table of all accounts with status filter, search and bulk activate.

## Status
Released

## Route
/admin/accounts

## Surface
Web

## Area
Account

## Purpose
The administrator's entry point into customer identity: find an account, see its
status at a glance, and act on it (activate, deactivate, open detail).

## User Personas
- Administrator — the only persona with access; guarded by the `admin` route wrapper (`src/routes/guards.tsx`).

## Key Interactions / Workflows
- Filter by status; free-text search on name and email (debounced 300ms)
- Paginated table, 25 per page, server-side
- Row click → Account Detail (PAGE-ACC-03)
- Bulk select → Activate (calls EP-ACC-07 per row)

## Page States
- Loading skeleton · empty ("no accounts match") · error with retry · bulk-action in-flight

## Consumes Endpoints
<!-- Same-repo endpoints are relative paths — this file is
     code-<repo>/context/code-context/frontend/pages/<area>/<slug>.md → three levels up to code-context/, e.g.
       - GET /accounts — ../../../backend/domains/account/endpoints/list-accounts.md (EP-ACC-01)
     This page lives in acme-web and its endpoints live in acme-api, so both use the
     [repo:<key>] form, resolved through the registry (§8). -->
- GET /accounts — [repo:acme-api] ./backend/domains/account/endpoints/list-accounts.md (EP-ACC-01) | Confirmed
- POST /accounts/{id}/activate — [repo:acme-api] ./backend/domains/account/endpoints/activate-account.md (EP-ACC-07) | Confirmed

## Used by Features
(as-built) — no feature linked yet.

## Permissions
- View: `admin` role (route guard)
- Bulk activate: additionally requires `account.activate`; the button is hidden without it.

## State & Data Handling
React Query, key `['accounts', filters]`, 30s stale time; invalidated after bulk activate.

## Client-side Validation
Search input trimmed and capped at 100 chars. No form submission on this page.

## Open Questions
- None.

## Source References
- [code › src/pages/admin/AccountList.tsx]
- [code › src/api/accounts.ts] — the API client calls traced to endpoints
- [code › src/router.tsx] — route registration
```

---

## 6. Database object files (grouped by kind)

One file per object, in the folder for its **Kind**. All kinds share a spine — `## Entity ID`, `## Summary`, `## Kind`, `## Domain`, `## Status`, `## Purpose`, `## Business Purpose`, `## Used by Endpoints`, `## Used by Database Objects`, `## Used by Features`, `## Open Questions`, `## Source References` — and add the sections that kind actually needs. §6.b–6.d below show only the *kind-specific* sections; every one of those files still carries the full spine. The back-link headings are the same three on every kind (a procedure uses `## Used by Endpoints`, not `## Called by`) so an integrity check can find them without knowing the kind. Write only the sections that apply to the kind; do not carry empty `Columns` on a stored procedure.

### 6.a Table / Collection — `database/tables/<slug>.md`, `database/collections/<slug>.md`

```md
---
doc_type: entity
schema_version: 1.3
produced_by: tl
entity_id: ENT-BIL-01
kind: Table
status: Released
implementation_state: Implemented
origin: reverse-mapped
mapped_from: "db/migrations/0031_create_invoices.sql"
mapped_from_commit: a1b2c3d
map_confidence: Confirmed
generated_at: YYYY-MM-DD
---

# Table: invoices

## Entity ID
ENT-BIL-01

## Summary
Invoice header — account, period, totals, status; lines live in invoice_lines.

## Kind
Table

## Domain
Billing

## Status
Released

## Source Data Entity
— (no BA data-register in this workspace; reverse-mapped from migrations.)

## Purpose
Stores one row per issued or draft invoice: which account, which billing period,
the computed totals, the currency, and the lifecycle status.

## Business Purpose
<!-- WHY the business has this object. The half a reader can't get from the DDL. -->
The billing ledger's header record and the customer-facing artefact of a billing
period. Its `status` drives collections: `Issued` starts the payment clock,
`Overdue` feeds the dunning cycle, `Paid` closes it. Because totals are written by
`sp_calculate_invoice_total` rather than the application, this table — not any
service — is the authority on what a customer was charged, and rows are treated as
immutable once `status = 'Issued'` (corrections are credit notes, never edits).

## Columns / Fields
| Name | Type | Constraints | Notes | Confidence |
|---|---|---|---|---|
| id | uuid | PK, default gen_random_uuid() | | Confirmed |
| tenant_id | uuid | not null, FK → tenants.id | row-level isolation filter | Confirmed |
| account_id | uuid | not null, FK → accounts.id | | Confirmed |
| invoice_number | text | unique, not null | from fn_next_invoice_number | Confirmed |
| period_start | date | not null | inclusive | Confirmed |
| period_end | date | not null | inclusive | Confirmed |
| subtotal | numeric(12,2) | not null, default 0 | written by sp_calculate_invoice_total | Confirmed |
| tax_total | numeric(12,2) | not null, default 0 | written by sp_calculate_invoice_total | Confirmed |
| total | numeric(12,2) | not null, default 0 | subtotal + tax_total | Confirmed |
| currency | char(3) | not null | ISO-4217 | Confirmed |
| status | text | not null, check in (draft, issued, paid, overdue, void) | | Confirmed |
| issued_at | timestamptz | null | set on transition to issued | Confirmed |
| created_at | timestamptz | not null, default now() | | Confirmed |

## Keys & Indexes
- PK `id` · Unique `invoice_number` · Unique `(account_id, period_start, period_end) WHERE status <> 'void'` — the idempotency guard behind EP-BIL-03
- Index `(status, period_end)` — dunning sweep · Index `account_id`

## Relationships
- N—1 accounts (ENT-ACC-01) — `account_id`
- 1—N invoice_lines (ENT-BIL-02)
- 1—N payments (ENT-BIL-03) — partial payments allowed
- Read by vw_outstanding_balance (ENT-BIL-09), vw_invoice_summary (ENT-BIL-10)

## Used by Endpoints
<!-- Forward planning's heading, kept verbatim. This file is
     code-<repo>/context/code-context/database/<kind>/<slug>.md → two levels up reaches code-context/. -->
- EP-BIL-03 POST /accounts/{id}/invoices (RW) — ../../backend/domains/billing/endpoints/generate-invoice.md
- EP-BIL-05 GET /accounts/{id}/invoices (R) — ../../backend/domains/billing/endpoints/list-invoices.md
- EP-BIL-14 (Schedule) nightly-invoice-run (W) — ../../backend/domains/billing/endpoints/nightly-invoice-run.md

## Used by Database Objects
<!-- Reverse-map addition: object-to-object back-links, so a reader tracing what writes this
     table finds the procedure and the trigger, not just the endpoints. -->
- sp_calculate_invoice_total (W) — ../procedures/sp-calculate-invoice-total.md
- vw_outstanding_balance (R) — ../views/vw-outstanding-balance.md
- vw_invoice_summary (R) — ../views/vw-invoice-summary.md

## Used by Features
(as-built) — no feature linked yet.

## Data Classification / Retention
No direct PII (linked to it via `account_id`). Financial record — retention is
statutory; no purge job found in the repo. | OQ-BIL-05

## Open Questions
- OQ-BIL-05 | No retention/archival job exists for invoices — intended? | Compliance | Impacts storage growth + statutory retention | Open

## Source References
- [code › db/migrations/0031_create_invoices.sql] — creation
- [code › db/migrations/0047_add_invoice_idempotency_index.sql] — the unique partial index
- [code › src/entities/Invoice.ts] — ORM mapping
```

For a **Collection** (document store): replace *Columns / Fields* with **Document Shape** (a commented JSON skeleton with per-field type, required, and notes), replace *Keys & Indexes* with the declared indexes and the shard key, and state explicitly for each relation whether it is **embedded** or **referenced** — that distinction is the schema decision a reader most needs.

### 6.b View — `database/views/<slug>.md`

Spine plus:

```md
## Definition
<!-- What the view computes, in prose. Include the SQL only if it is short and clarifying. -->
Per-account outstanding balance: sum of issued invoice totals, less applied payments,
less credit notes, grouped by account and currency. Excludes `void` invoices.

## Reads From
- invoices (ENT-BIL-01) — ../tables/invoices.md
- payments (ENT-BIL-03) — ../tables/payments.md
- credit_notes (ENT-BIL-05) — ../tables/credit-notes.md

## Columns
| Name | Type | Derivation | Confidence |
|---|---|---|---|
| account_id | uuid | invoices.account_id | Confirmed |
| currency | char(3) | invoices.currency | Confirmed |
| outstanding | numeric(12,2) | SUM(invoices.total) − SUM(payments.amount) − SUM(credit_notes.total) | Confirmed |

## Materialised
No — plain view, recomputed per query. Note any refresh strategy if materialised.

## Performance Notes
Full scan of invoices per account without the `(status, account_id)` index; flagged
as a read hotspot for EP-BIL-05. | Likely
```

### 6.c Stored Procedure / Function — `database/procedures/<slug>.md`, `database/functions/<slug>.md`

These carry real business logic, so they get the same treatment as an endpoint.

```md
## Signature
`sp_calculate_invoice_total(p_invoice_id uuid) RETURNS void`
<!-- For a function, state the return type and whether it is deterministic/immutable. -->

## Parameters
| Name | Type | Direction | Notes | Confidence |
|---|---|---|---|---|
| p_invoice_id | uuid | IN | Must reference an invoice in `draft` | Confirmed |

## Business Purpose
The single authority on what a customer is charged. Totalling, proration, discount
application and tax all happen here so that the on-demand endpoint and the nightly
batch can never disagree — a deliberate choice to keep money out of application code.

## Business Logic
1. Lock the invoice row (`FOR UPDATE`); raise if not `draft`.
2. Recompute each `invoice_lines.extended_amount` = qty × unit_price × (1 − discount_pct).
3. Prorate any line whose service window is partly outside the invoice period.
4. Resolve the tax rate via `fn_tax_rate_for(account jurisdiction, period_end)` and compute `tax_total`.
5. Write `subtotal`, `tax_total`, `total` back to the invoice header.
6. Raise `INVOICE_TOTAL_NEGATIVE` if `total < 0` (credit notes take the negative path instead).

## Objects Touched
| Object | Kind | Mode | File |
|---|---|---|---|
| invoices | Table | W | ../tables/invoices.md (ENT-BIL-01) |
| invoice_lines | Table | RW | ../tables/invoice-lines.md (ENT-BIL-02) |
| fn_tax_rate_for | Function | X | ../functions/fn-tax-rate-for.md (ENT-BIL-13) |

## Used by Endpoints
- EP-BIL-03 — ../../backend/domains/billing/endpoints/generate-invoice.md
- EP-BIL-14 — ../../backend/domains/billing/endpoints/nightly-invoice-run.md

## Used by Database Objects
- None. (A trigger or another procedure that called this one would be listed here.)

## Error Conditions
`INVOICE_NOT_DRAFT` · `INVOICE_TOTAL_NEGATIVE` · `TAX_RATE_NOT_FOUND` (from fn_tax_rate_for).

## Transaction & Concurrency
Runs inside the caller's transaction; takes a row lock on the invoice. Safe to retry.
```

### 6.d Trigger — `database/triggers/<slug>.md`

```md
## Fires On
`accounts` — AFTER INSERT, UPDATE, DELETE — FOR EACH ROW

## Condition
No WHEN clause — fires on every row change.

## What It Does
Writes one `audit_log` row per change with the actor from
`current_setting('app.user_id')`, the operation, and the old/new row as JSONB.

## Business Purpose
Guarantees an audit trail regardless of which code path wrote the row — including
direct SQL and migrations. This is why the application layer does not audit account
writes itself, and why bulk migrations against `accounts` produce audit volume.

## Objects Touched
| Object | Kind | Mode | File |
|---|---|---|---|
| accounts | Table | R | ../tables/accounts.md (ENT-ACC-01) — reads OLD/NEW row images |
| audit_log | Table | W | ../tables/audit-log.md (ENT-CORE-01) |

## Calls
Inline trigger body. (Where a trigger calls a procedure/function, link it here.)

## Side Effects to Know About
Doubles write volume on bulk account updates; relies on `app.user_id` being set by
the connection pool's session initialiser — writes from a job that skips it record
`actor = system`. | Likely
```

---

## 7. map-coverage.md — the scope guard

`code-context/map-coverage.md`. Discovery writes every enumerated unit here as `pending`; detail flips each to `mapped`. The integrity check fails while any row is `pending`.

```md
---
doc_type: map-coverage
schema_version: 1.3
produced_by: tl
status: Emerging
repo: acme-api
mapped_from_commit: a1b2c3d
generated_at: YYYY-MM-DD
---

# Map Coverage — acme-api

150 enumerated · 147 mapped · 3 skipped · 0 pending

| Layer | Kind | Match key | Source file | Domain | Status | Note |
|---|---|---|---|---|---|---|
| backend | endpoint | POST /accounts/{id}/invoices | src/routes/billing/invoice.controller.ts | BIL | mapped | |
| backend | job | (Schedule) nightly-invoice-run | src/jobs/invoice-run.ts | BIL | mapped | trigger: cron 0 2 * * * |
| database | table | invoices | db/migrations/0031_create_invoices.sql | BIL | mapped | |
| database | procedure | sp_calculate_invoice_total | db/migrations/0042_*.sql | BIL | mapped | |
| database | trigger | trg_account_audit | db/migrations/0018_*.sql | ACC | mapped | |
| backend | endpoint | ANY /internal/admin/* | src/routes/admin/dynamic.ts | CORE | skipped | dynamic dispatch from a registry object — see finding FND-02 |
```

**Status:** `pending` (enumerated, not written) · `mapped` (unit file written) · `skipped` (must carry a note **and** a matching integrity finding) · `removed` (code deleted since the last run — keep the row, don't delete it).

---

## 8. Workspace registry — `<workspace>/.jetrix/tl/code-map-registry.md`

Each repo owns its full `code-context/`. The workspace owns one small file that says which repos exist, where their context is, and what they cover — so `/tl:plan` can find and **reuse** as-built units instead of duplicating them, and so a page in one repo can link to an endpoint in another.

```md
---
doc_type: code-map-registry
schema_version: 1.3
produced_by: tl
status: Emerging
generated_at: YYYY-MM-DD
---

# Code Map Registry

Repositories mapped by `/tl:code-map`. Each repo's context is committed **inside that repo**
at `<repo>/context/code-context/`; this file is the workspace-level pointer. Before creating a
new unit, `/tl:plan` resolves match keys through these indexes.

| Repo key | Path | Layers | Code context root | Mapped at commit | Last mapped | Units |
|---|---|---|---|---|---|---|
| acme-api | D:/work/acme/acme-api | backend, database | ./code-context/ | a1b2c3d | 2026-08-14 | 84 EP · 63 ENT |
| acme-web | D:/work/acme/acme-web | frontend | ./code-context/ | 7f3e9c1 | 2026-08-14 | 41 PAGE |

## Indexes
| Repo key | Root | Backend | Frontend | Database |
|---|---|---|---|---|
| acme-api | code-context/code-context-index.md | code-<repo>/context/code-context/backend/backend-index.md | — | code-<repo>/context/code-context/database/database-index.md |
| acme-web | code-context/code-context-index.md | — | code-<repo>/context/code-context/frontend/frontend-index.md | — |

## Cross-repo links
Within a repo, links are relative paths. Across repos, prefix the repo key and give the
path **relative to that repo's `code-context/`**:

    [repo:acme-api] ./backend/domains/account/endpoints/list-accounts.md (EP-ACC-01)

A consumer resolves `repo:<key>` through the Path column above. A cross-repo link is
still bidirectional — the endpoint in `acme-api` lists the `acme-web` page under
*Called by* with the same `[repo:…]` form.

## Pending cross-repo links
Links discovered in a mapped repo whose other end lives in a repo that has not been mapped yet.
Each is resolved (and removed from this table) when that repo is mapped; until then the integrity
check counts them as known-incomplete rather than as broken links.

| From | To (unresolved) | Kind | Discovered in | Note |
|---|---|---|---|---|
| PAGE-SUB-03 (acme-web) | POST /billing/portal-session | page → endpoint | acme-web | target repo `acme-payments` not mapped |

## Area token allocation
Area tokens are shared across repos so IDs never collide: `ACC` Account · `BIL` Billing ·
`SUB` Subscription · `NTF` Notification · `CORE` cross-cutting. A new repo reuses an
existing token when it serves the same domain; it never mints a second token for one domain.
```

---

## 9. Rules that apply to every file here

- **Forward-planning headings are kept verbatim.** Every `##` heading `tl-feature-planning`'s `context-file-templates.md` defines on a page, endpoint or entity appears here with the same text — `Reads / Writes Entities`, `Behaviour / Business Rules`, `Called by`, `Used by Endpoints`, `Used by Features`, `Integrations`, `Permissions`, `Status`. The reverse-map enhancements are **additive**. The complete list of added sections is: `Summary`, `Domain`, `Validation`, `Business Logic`, `Side Effects`, `Business Purpose`, `Used by Database Objects`, `Area`, `State & Data Handling`, `Client-side Validation`, plus the kind-specific sections in §6.b–6.d (`Definition`, `Reads From`, `Materialised`, `Performance Notes`, `Signature`, `Parameters`, `Objects Touched`, `Error Conditions`, `Transaction & Concurrency`, `Fires On`, `Condition`, `What It Does`, `Calls`, `Side Effects to Know About`). Everything else is a forward heading with a richer table inside it. Never rename a forward heading to a better one — a consumer that greps for it must still find it.
- **Index-first is a contract, not a suggestion.** Every unit has a one-line `## Summary`; every index mirrors it verbatim; every index has a `## Domain Map` written from the units actually mapped. An index without a Domain Map is incomplete.
- **Bidirectional links are mandatory.** Page → *Consumes Endpoints* implies endpoint → *Called by*. Endpoint → *Data Access* implies object → *Used by → Endpoints*. Procedure → *Objects Touched* implies table → *Used by → Database objects*. The integrity check fails on a forward link with no back-link.
- **Link, don't duplicate.** Contracts live once on the endpoint; columns live once on the object; stack conventions live once in `_overview.md`.
- **Every fact carries provenance.** `mapped_from` in frontmatter, `[code › path]` in Source References, and a confidence on anything inferred. A unit with no code citation is an invention — delete it or turn it into an open question.
- **Reverse-mapped frontmatter** (`origin`, `mapped_from`, `mapped_from_commit`, `map_confidence`) is provenance and stays in place forever — including after `/tl:plan` links a feature to the unit.
- **Reconcile, never clobber.** A re-run extends: new links added, changed facts updated with a bumped `generated_at`, deleted code marked `Removed` rather than erased, hand-written prose in `Business Purpose` preserved unless the code contradicts it.
- **Nothing sensitive.** This tree is committed and shared.
