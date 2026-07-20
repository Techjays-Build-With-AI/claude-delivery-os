# Context file templates

The exact schema for each unit file (page, endpoint, entity) and for the three layer indexes. Build every file from these so the `context/frontend|backend|database` graph stays uniform, bidirectionally linked, and machine-parseable. Fill sections from the feature breakdown and the BA registers; where a section has no supported content write the labelled placeholder (`None`, `TBD`, or `Open question — see below`) — **never delete a heading, never invent an integration or a rule the source can't ground**.

Slugs are **lowercase kebab-case**. IDs are stable and append-only: `PAGE-<AREA>-NN`, `EP-<AREA>-NN`, `ENT-<AREA>-NN`, `NN` sequential within that area and layer. Links between units are **relative paths** so the graph resolves on disk. Confidence per designed fact uses the shared vocabulary: `Confirmed · Likely · Assumed · Conflicting · Needs Clarification`.

---

## _overview.md (one per layer)

`context/frontend/_overview.md`, `context/backend/_overview.md`, `context/database/_overview.md` — a short orientation doc at the head of each layer folder so a reader (or a coding agent) landing in the layer sees its stack and conventions **once**, and every unit file below stays lean instead of repeating them. Written by `tl-codebase-map` from the detected stack (reverse) or by `tl-feature-planning` from the confirmed architecture (forward); it holds no per-unit facts and never duplicates a unit.

```md
---
doc_type: layer-overview
schema_version: 1.1
produced_by: tl
layer: frontend        # frontend | backend | database
generated_at: YYYY-MM-DD
---

# Frontend Overview

## Stack
React 18 + TypeScript, Vite. Routing: React Router v6. Data: React Query over an axios client (`src/api/`).

## Conventions
Pages under `src/pages/<area>/`; one route → one page component. Shared UI in `src/components/` (not mapped as pages).

## Entry Points
Router config: `src/router.tsx`. API base + interceptors: `src/api/client.ts`.

## Notes
<!-- backend: framework, routing style, auth model, ORM. database: engine, migration tool, schema location. -->
Anything a unit file would otherwise have to restate — recorded here instead.
```

---

## page-index.md

`context/frontend/page-index.md` — the map of all pages. One row per page. On re-runs update in place; keep retired pages visible with a status.

```md
---
doc_type: page-index
schema_version: 1.1
produced_by: tl
status: Emerging
generated_at: YYYY-MM-DD
---

# Page Index

| Page ID | Page | Area | Used by Features | Consumes Endpoints | Folder |
|---|---|---|---|---|---|
| PAGE-SUP-01 | Supplier List | Supplier | FEAT-SUP-001 | EP-SUP-01 | ./pages/supplier/supplier-list.md |
| PAGE-SUP-02 | Create Supplier | Supplier | FEAT-SUP-001 | EP-SUP-02, EP-SUP-05 | ./pages/supplier/create-supplier.md |
| PAGE-SUP-03 | Supplier Details | Supplier | FEAT-SUP-001, FEAT-SUP-002 | EP-SUP-03, EP-SUP-04 | ./pages/supplier/supplier-details.md |
```

**Status** (controlled): `Proposed · Designed · In Development · Released · Blocked` (+ retirement `Merged into … · Deferred · Removed`).

---

## endpoint-index.md

`context/backend/endpoint-index.md` — the map of all endpoints.

```md
---
doc_type: endpoint-index
schema_version: 1.1
produced_by: tl
status: Emerging
generated_at: YYYY-MM-DD
---

# Endpoint Index

| Endpoint ID | Method + Path | Domain | Called by | Reads/Writes Entities | Used by Features | File |
|---|---|---|---|---|---|---|
| EP-SUP-01 | GET /suppliers | Supplier | PAGE-SUP-01 | ENT-SUP-01 | FEAT-SUP-001 | ./domains/supplier/endpoints/list-suppliers.md |
| EP-SUP-02 | POST /suppliers | Supplier | PAGE-SUP-02 | ENT-SUP-01, ENT-SUP-02 | FEAT-SUP-001 | ./domains/supplier/endpoints/create-supplier.md |
| EP-SUP-06 | (Schedule) supplier-doc-expiry-sweep | Supplier | Trigger: Schedule (daily) | ENT-SUP-03 | FEAT-SUP-001 | ./domains/supplier/endpoints/doc-expiry-sweep.md |
```

**Called by** is a page ID, or `Trigger: Schedule/Event/Webhook/Service` for non-UI endpoints.

---

## entity-index.md

`context/database/entity-index.md` — the map of all data entities.

```md
---
doc_type: entity-index
schema_version: 1.1
produced_by: tl
status: Emerging
generated_at: YYYY-MM-DD
---

# Entity Index

| Entity ID | Entity | Kind | Source DATA-### | Used by Endpoints | File |
|---|---|---|---|---|---|
| ENT-SUP-01 | suppliers | Table | DATA-004 | EP-SUP-01, EP-SUP-02, EP-SUP-03 | ./entities/suppliers.md |
| ENT-SUP-02 | supplier_contacts | Table | DATA-005 | EP-SUP-02, EP-SUP-03 | ./entities/supplier-contacts.md |
| ENT-SUP-03 | supplier_documents | Table | DATA-006 | EP-SUP-04, EP-SUP-06 | ./entities/supplier-documents.md |
```

**Kind**: `Table · Collection · View · Stored Procedure · Function · Trigger`. **Source DATA-###** links to the BA data-register; `—` if the entity is a pure technical object with no business-register counterpart (note why on the file) — reverse-mapped functions and triggers usually have no `DATA-###` and that's expected.

---

## 1. page.md

One user-facing surface — what it is, who uses it, what it does, and the endpoints it consumes. Never copies an endpoint's contract; links to it.

```md
---
doc_type: page
schema_version: 1.1
produced_by: tl
page_id: PAGE-SUP-03
status: Designed
generated_at: YYYY-MM-DD
---

# Page: Supplier Details

## Page ID
PAGE-SUP-03

## Status
Proposed | Designed | In Development | Released | Blocked

## Route
/suppliers/:supplierId

## Surface
Web | Mobile | Both        <!-- the kind of UX surface -->

## Purpose
Show a single supplier's profile, contacts, documents, and approval status; the hub from which a user edits the supplier, uploads documents, and submits it for review.

## User Personas
- Operations Coordinator — views and edits supplier data, uploads documents
- Supplier Manager — submits for review
- Compliance Reviewer — reviews documents (read-mostly)

## Key Interactions / Workflows
- View supplier profile and status
- Edit profile fields (Operations Coordinator)
- Upload / replace compliance documents
- Submit supplier for review (guarded by completeness)
- View approval history

## Page States
- Loading / empty (supplier not found)
- Draft supplier (incomplete — submit disabled)
- Pending review (read-mostly)
- Approved / Rejected (with reason)

## Consumes Endpoints
<!-- this file is context/frontend/pages/<area>/<slug>.md → three levels up to context/ -->
- GET supplier — ../../../backend/domains/supplier/endpoints/get-supplier.md (EP-SUP-03)
- Update supplier — ../../../backend/domains/supplier/endpoints/update-supplier.md (EP-SUP-04)
- Upload document — ../../../backend/domains/supplier/endpoints/upload-supplier-document.md (EP-SUP-05)

## Used by Features
- FEAT-SUP-001 Supplier Onboarding
- FEAT-SUP-002 Supplier Approval Workflow

## Permissions
- Edit fields: users with `supplier.edit`
- Submit for review: users with `supplier.submit`
- Approve/reject actions are on the Approval Queue page, not here

## Open Questions
- OQ-SUP-10 | Can a supplier be edited after approval? | Product Owner | Impacts page states | Open

## Source References
- Feature: FEAT-SUP-001 (feature.md → Related Pages), FEAT-SUP-002
- Workflow: WF-012 Supplier Onboarding
- Business rules: BR-004 (submit requires completeness)
```

---

## 2. endpoint.md

One backend operation — its contract, the pages/triggers that call it, and the entities it touches. Never copies an entity's columns; links to it.

```md
---
doc_type: endpoint
schema_version: 1.1
produced_by: tl
endpoint_id: EP-SUP-02
status: Designed
generated_at: YYYY-MM-DD
---

# Endpoint: Create Supplier

## Endpoint ID
EP-SUP-02

## Status
Proposed | Designed | In Development | Released | Blocked

## Method + Path
POST /suppliers

## Domain
Supplier

## Purpose
Create a new supplier profile in Draft status.

## Trigger
Called by page(s) — see Called by. (For non-UI endpoints: Schedule | Event | Webhook | Service, with the specifics.)

## Request
| Field | Type | Required | Notes | Confidence |
|---|---|---|---|---|
| legalName | string | yes | Unique per tax ID | Confirmed (BR-003) |
| taxId | string | yes | Format validated | Assumed |
| contacts | array<Contact> | no | May be added later | Confirmed |

## Response
- `201 Created` → `{ supplierId, status: "Draft" }`
- `400` validation error (missing required fields)
- `409` duplicate supplier (per BR-003)
- `401 / 403` unauthenticated / lacking `supplier.create`

## Auth
Requires `supplier.create`. | Confidence: Assumed — auth model not yet confirmed (OQ-SUP-11).

## Behaviour / Business Rules
- Creates the supplier in Draft (BR-002).
- Duplicate check on tax ID before insert (BR-003).
- Writes an audit entry.

## Called by
<!-- this file is context/backend/domains/<domain>/endpoints/<slug>.md → four levels up to context/ -->
- PAGE-SUP-02 Create Supplier — ../../../../frontend/pages/supplier/create-supplier.md

## Reads / Writes Entities
- Writes suppliers — ../../../../database/entities/suppliers.md (ENT-SUP-01)
- Writes supplier_contacts — ../../../../database/entities/supplier-contacts.md (ENT-SUP-02)
- Writes audit_log — ../../../../database/entities/audit-log.md (ENT-CORE-01)

## Integrations
- None. (When present, cite INT-###: e.g. CRM sync — INT-002.)

## Open Questions
- OQ-SUP-11 | What is the auth/authorization model for supplier writes? | TL / Security | Impacts every write endpoint | Open

## Source References
- Feature: FEAT-SUP-001 (feature.md → Related APIs)
- Business rules: BR-002, BR-003
- Data: DATA-004 suppliers, DATA-005 supplier_contacts
```

---

## 3. entity.md

One data object — its physical design, and the endpoints that use it. Realises a BA `DATA-###` where one exists.

```md
---
doc_type: entity
schema_version: 1.1
produced_by: tl
entity_id: ENT-SUP-01
status: Designed
generated_at: YYYY-MM-DD
---

# Entity: suppliers

## Entity ID
ENT-SUP-01

## Status
Proposed | Designed | In Development | Released | Blocked

## Kind
Table | Collection | View | Stored Procedure | Function | Trigger

## Source Data Entity
DATA-004 (ba-output/data-register.md) — the business entity this realises. `—` if none; note why.

## Purpose
Stores the core supplier profile and its lifecycle status.

## Columns / Fields
| Name | Type | Constraints | Notes | Confidence |
|---|---|---|---|---|
| id | uuid | PK | | Confirmed |
| legal_name | text | not null | | Confirmed (DATA-004) |
| tax_id | text | unique, not null | duplicate guard (BR-003) | Confirmed |
| status | enum | not null, default 'draft' | draft/pending/approved/rejected | Confirmed (WF-012) |
| created_at | timestamptz | not null, default now() | | Confirmed |
| updated_at | timestamptz | not null | | Confirmed |

## Keys & Indexes
- PK: `id`
- Unique: `tax_id`
- Index: `status` (approval-queue queries)

## Relationships
- 1—N supplier_contacts (ENT-SUP-02)
- 1—N supplier_documents (ENT-SUP-03)
- 1—N supplier_status_history (ENT-SUP-04)

## Used by Endpoints
<!-- this file is context/database/entities/<slug>.md → two levels up to context/ -->
- EP-SUP-01 GET /suppliers — ../../backend/domains/supplier/endpoints/list-suppliers.md
- EP-SUP-02 POST /suppliers — ../../backend/domains/supplier/endpoints/create-supplier.md
- EP-SUP-03 GET /suppliers/{id} — ../../backend/domains/supplier/endpoints/get-supplier.md

## Data Classification / Retention
- Contains PII (contact-linked). Retention: TBD — OQ-SUP-12.

## Open Questions
- OQ-SUP-12 | What is the retention policy for supplier records? | Compliance | Impacts schema + purge job | Open

## Source References
- Feature: FEAT-SUP-001 (feature.md → Related Data Entities)
- Data register: DATA-004
- Workflow: WF-012 (status lifecycle)
```

---

## Notes that apply to all unit files

- **Bidirectional links are mandatory.** A page lists *Consumes Endpoints*; each of those endpoints must list the page under *Called by*. An endpoint lists *Reads/Writes Entities*; each entity must list the endpoint under *Used by Endpoints*. The link-integrity check fails if a forward link has no matching back-link.
- **Link, don't duplicate.** Pages point at endpoint files; endpoints point at entity files. Contracts live once, on the endpoint; columns live once, on the entity.
- **Reuse extends, never overwrites.** When a second feature reuses a unit, add the new *Used by Feature* / *Called by* / *Used by Endpoint* row — don't remove the existing ones.
- **Every unit carries Source References** back to the feature (`FEAT-…`) and the register IDs (`WF-###`, `BR-###`, `DATA-###`, `INT-###`) that motivate it. A unit with no source is a design invention — either ground it or raise it as an open question.
- **Open questions on a unit** use the same `OQ-<AREA>-NN` scheme as the feature breakdown (or reuse a `CLR-###` already logged), and never get silently promoted into a confirmed contract.
