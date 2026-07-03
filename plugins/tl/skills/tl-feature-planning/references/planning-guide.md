# Planning guide

How to decide the technical units a feature needs, how to match against what already exists so you reuse instead of duplicate, how to enter for features that have no UI, how to make design calls honestly, and the link-integrity bar for calling a plan complete. Read this before planning a feature; use `context-file-templates.md` for the files themselves.

---

## The three layers

Every feature decomposes into up to three layers of logical units. Each unit is one file; each file is one node in the graph.

| Layer | Unit | What one unit is | Stable ID | Lives in |
|---|---|---|---|---|
| **Frontend** | Page | One user-facing surface — a web page, a mobile screen, any UX view a user actually sees | `PAGE-<AREA>-NN` | `context/frontend/pages/<area>/<slug>.md` |
| **Backend** | Endpoint | One backend operation — a request the system serves (or a job/event handler) | `EP-<AREA>-NN` | `context/backend/domains/<domain>/endpoints/<slug>.md` |
| **Database** | Entity | One data object — a SQL table, a NoSQL collection, a view, or a stored procedure | `ENT-<AREA>-NN` | `context/database/entities/<slug>.md` |

`<AREA>` is a short uppercase abbreviation for the capability area, reused from the feature's ID where possible (Supplier → `SUP`, Sourcing → `SRC`, RFP → `RFP`). `NN` is sequential **within that area and layer** (`PAGE-SUP-01`, `EP-SUP-01`, `ENT-SUP-01` are three different units). IDs are append-only — never renumber, never reuse a retired ID.

Not every feature has all three layers. A pure UI feature may add no new entity; an integration or a scheduled job has endpoints and entities but no page. Plan only the layers the feature actually needs.

---

## What each unit is — and is not

**A page** is a distinct surface a user navigates to or opens, with its own purpose, personas, and workflow role. A list, a detail view, a create/edit form, an approval queue, a dashboard — each is a page. A modal, a tab, a panel, or a single widget is **part of** a page, documented inside it (as a state or section), not a page of its own — unless it's a genuinely reusable surface the whole app leans on. The test: would a user think of it as "a screen"?

**An endpoint** is one logical backend operation with a method, a path, an input, an output, and a job to do (`POST /suppliers`, `GET /suppliers/{id}`, `POST /suppliers/{id}/submit-for-review`). Group by REST resource / domain operation, not by page — one endpoint often serves several pages. A validation helper, a private function, or a single query is **inside** an endpoint, not an endpoint. An endpoint that isn't called by a page must declare its trigger (schedule, event, webhook, another service).

**An entity** is one persisted data object — a table, a collection, a view, or a stored procedure. It owns its columns/fields, keys, and relationships. A single column, an index, or a migration is documented **inside** the entity, not as its own unit. Where the BA data-register already has the entity as a `DATA-###`, this file **realises** that entity (cites the ID, adds the physical design) — it does not invent a new one.

---

## Reuse vs create — the match keys

Before creating any unit, look it up in the layer's index. Reuse wins; duplication is the failure mode this skill exists to prevent.

| Layer | Match on | If it exists | If it doesn't |
|---|---|---|---|
| Page | route / canonical page name | link to it, add this feature to its *Used by features*, extend its sections if the feature adds behaviour | create it, mint next `PAGE-<AREA>-NN` |
| Endpoint | `METHOD + path` (normalised) | link to it, add the calling page/trigger to its *Called by*, reconcile the contract if the feature needs more | create it, mint next `EP-<AREA>-NN` |
| Entity | object name (table/collection/proc) | link to it, add the endpoint to its *Used by endpoints*, add any new columns the endpoint needs | create it, mint next `ENT-<AREA>-NN`, cite `DATA-###` if one exists |

When you reuse, you **add** back-links and extend — you never overwrite existing callers/readers or silently change a contract another feature depends on. If the feature needs a genuinely different behaviour from an existing endpoint, that's a *new* endpoint (or a versioned one), not a mutation of the shared one — decide deliberately and note why.

**Two run modes.** Pointed at one feature, still read the whole existing graph (step 2 of the workflow) so you reuse units other features created. Pointed at the whole set, plan feature by feature against the *growing* index so later features reuse what earlier ones added. Either way the indexes are the shared memory.

---

## Entry paths — not everything starts at a page

Plan the layers a feature actually has:

- **UI feature** (list/detail/form/queue): page → endpoints → entities. The normal path.
- **Workflow feature**: often a queue/detail page plus state-transition endpoints; entities include a status-history object.
- **Integration feature** (`INT-###`): usually **no page**. Enter at endpoints (inbound webhook, outbound sync call) → entities (mapping/log tables). Cite the `INT-###`; the integration's external contract, if undecided, is an open question, not an invention.
- **Scheduled job / background worker**: no page. Enter at an endpoint/handler with trigger `Schedule`, plus the entities it reads/writes.
- **Event consumer/producer**: no page. Enter at a handler endpoint with trigger `Event`, naming the event.
- **Reporting/analytics feature**: a dashboard/report page → read endpoints → views or aggregate entities.

An endpoint with no page must name its trigger; the link-integrity check flags an untriggered, uncalled endpoint.

---

## Design discipline — author, but don't invent

The TL owns technical design, so this is where contracts and schemas legitimately get created. Keep it honest:

- **Ground it.** Every field, status code, column, and relationship should trace to the feature's workflow, a business rule (`BR-###`), a data entity (`DATA-###`), or an integration (`INT-###`). Cite the source on the unit.
- **Mark confidence.** `Confirmed` where a register states it; `Assumed` / `Likely` where you designed it to fill a gap. Never present an assumption as confirmed.
- **Escalate real unknowns.** When something that changes the design is genuinely undecided — an external API's contract, the auth/authorization model, a retention or PII rule, an idempotency requirement on a money-moving call — record an **open question** on the unit (owner + impact), don't guess.
- **Log decisions.** Append a `DEC-###` row to `shared-context/decision-log.md` for each material design choice (chosen auth scheme, pagination style, soft-delete vs hard-delete, sync vs async on an integration). This is the same decision-log the `tl-resolve` loop writes to, so design and review stay consistent and auditable.

---

## Link-integrity check (run before finishing)

Walk the graph and report each of these as a finding; a plan with dangling links is not complete.

- [ ] Every `feature.md` *Related Page / API / Data Entity* maps to a real unit file (reused or created) — nothing declared was dropped.
- [ ] Every page→endpoint and endpoint→entity forward link resolves to an existing file.
- [ ] Every back-link resolves: each endpoint's *Called by* pages exist; each entity's *Used by endpoints* exist.
- [ ] Every endpoint has at least one caller **or** a declared non-UI trigger (Schedule / Event / Webhook / Service).
- [ ] No orphan entity — every entity is used by ≥ 1 endpoint (or explicitly marked reference/seed data).
- [ ] Every `DATA-###` / `INT-###` / `WF-###` / `BR-###` cited exists in its register.
- [ ] Every unit has a stable ID, frontmatter, Source References, and appears in its layer index.
- [ ] Shared units appear **once** with multiple back-links — no duplicate files for the same page/endpoint/entity.
- [ ] Re-run only: retired units kept in the index with a status; existing back-links preserved, not overwritten.

---

## Completion checklist

The feature plan is complete when:

- [ ] Each target feature's declared pages/endpoints/entities exist as real, linked files.
- [ ] Pages link to their endpoints; endpoints link to callers and entities; entities link back to endpoints and to `DATA-###`.
- [ ] Shared units are reused, not duplicated, and reflected in the three indexes.
- [ ] Material design decisions are logged as `DEC-###`; genuine unknowns are open questions, not inventions.
- [ ] The link-integrity check passes (or every exception is a recorded finding with an owner).
- [ ] The plan is understandable by a coding agent that lands on any single unit file.
