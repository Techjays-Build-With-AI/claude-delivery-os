# Jira-Anchored Delivery OS — Adaptation Specification

> **Client:** Unbounce &nbsp;·&nbsp; **Status:** Draft for review (ideation phase) &nbsp;·&nbsp; **Author:** Techjays Delivery &nbsp;·&nbsp; **Date:** 2026-08-04
>
> This document specifies how the Techjays **Delivery OS** (a Claude plugin suite for the SDLC) is adapted for Unbounce by making **Jira** the system of record in place of Jetrix, and by making the **scoping step ticket-type-aware** so that every scope, RCA, and plan produced across the organisation follows one predetermined, uniform format. This is an ideation-phase design; nothing here is implemented yet.

---

## 1. Purpose

Unbounce runs their delivery on Jira. We want to bring the Delivery OS to their organisation so that:

1. **Jira is the single source of truth for execution.** Epics, stories, bugs and requests already live in Jira; the OS reads from Jira and writes its structured outputs *back* to Jira. Product requirements are captured as a **PRD in Notion** — so requirements live where the product team already works, and execution lives in Jira.
2. **Every artifact has one org-wide format.** When anyone scopes a ticket, breaks down a feature, or writes an RCA, the *shape* of what they produce is fixed by a template — and the template is chosen automatically by the **type of the ticket** (Bug, Feature, Client Request). Two people scoping two different bugs produce documents that look identical section-for-section.
3. **The whole SDLC runs on rails.** One Jira ticket travels through scope → breakdown → plan → build → review → QA → docs, and each stage is a plugin that reads the prior stage's structured output and writes its own back to Jira under a stable, predictable naming convention.

This spec covers the architecture, the Jira mapping, the **Notion PRD surface**, the ticket-type template library (with three full formats plus the feature story format), the unified naming conventions, the end-to-end flow, a **worked future-state example**, the additive changes to the shared conventions, and a rollout plan describing how each SDLC lifecycle stage is affected.

---

## 2. What exists today (baseline)

The Delivery OS is six Claude plugins over a shared document contract:

| Plugin | Role in the SDLC |
|--------|------------------|
| `delivery-os-core` | The **document contract** — workspace layout, YAML frontmatter standard, stable ID conventions, controlled vocabularies. Everything else conforms to it. |
| `ba` | Business analysis — `/ba:scope` (living scope), `/ba:features` (feature breakdown), review/resolve. |
| `tl` | Tech lead — codebase map, feature planning, maturity audit, scaffold, spec review. |
| `dev` | Delivery — bootstrap, build (feature-delivery-loop), code review, validation, PR handoff. |
| `qa` | Quality — test setup, test audit, quality gates. |
| `doc` | Client-facing docs — deck, proposal, spec walkthrough, workflow diagrams. |
| `jetrix` | **Source-of-truth binding** — `/jetrix:init`, `/jetrix:pull`, `/jetrix:push` against a "Jetrix MCP". |

Two properties of the baseline make this adaptation cheap and safe:

- **The source binding is isolated.** BA/TL/Dev/QA/Doc do **not** know about Jetrix. They read and write markdown records addressed by stable ID. Only the `jetrix` plugin knows how those records sync to an external store. Swapping in Jira is therefore *a new sync plugin plus a small conventions edit*, not a rewrite of the agents.
- **The canonical form is structured records; documents are projections.** Inside the source of truth, the truth is records (requirement, workflow, feature, page, endpoint, entity…) each with a stable ID. `scope.md` and the branded `.docx` are *rendered* from those records. This is exactly the model Jira wants too: the issue and its fields are the record; our markdown is a projection.

The **gap** we are filling: today the unit of work is a whole *engagement* — `/ba:scope` builds one large module-centric project scope from many client documents, and its "classification" decides *how deeply to read a source*, not *what type of ticket* is being worked. There is no per-ticket scoping and no bug-vs-feature-vs-request format switch. That switch is the core of this adaptation.

---

## 3. Design principles

1. **Additive, not disruptive.** These changes ship as document-contract **v1.3** (the same way the use-case layer shipped as v1.1 and the eval layer as v1.2). A v1.2 document stays readable; new documents are written at v1.3.
2. **Source-agnostic core.** The agents keep speaking "records by stable ID." Jira is confined to one `jira` plugin, mirroring how Jetrix was confined to one.
3. **Type determines format, format is fixed org-wide.** The template a person gets is a pure function of the ticket type. Nobody hand-designs a scope layout; they fill a predetermined one. Uniformity is the deliverable.
4. **Jira round-trips.** Every stage that produces structure writes it back to Jira in a defined way — scope onto the ticket, breakdown as sub-tasks, plan as the implementation plan, and so on. Local markdown is a working copy; Jira is authoritative.
5. **Deterministic naming.** Branch, folder, file, commit and PR names are all derived mechanically from the Jira key + a slug, so the same ticket always resolves to the same names for everyone.

---

## 4. Jira as the system of record

### 4.1 Object mapping (Jira ↔ Delivery OS)

| Jira object | Delivery OS concept | Notes |
|-------------|---------------------|-------|
| Project | Delivery OS project / workspace binding | `project.json` identity + custom-field + transition wiring |
| Epic | Initiative (work batch) | Maps to the existing `initiative` slug that groups features |
| Story / Task | **Feature** ticket → a `scope_profile: feature` scope | The primary unit the scoping agent runs on |
| Bug | **Bug** ticket → a `scope_profile: bug` scope (RCA-centric) | RCA is mandatory |
| Request-type issue (Service/portal/"client request") | **Client Request** → `scope_profile: client-request` scope (triage) | Usually *spawns* child Story/Bug issues |
| Sub-task | A **feature slice** from breakdown | Created by the breakdown step |
| Issue key `PROJ-123` | External key / stable anchor | Makes push idempotent; drives all naming |
| Issue Type | **Ticket type** (canonical) | Mapped through `project.json` (Jira type name → our type) |
| Status / Workflow transition | Delivery OS stage gate | Each stage transitions the issue |
| Custom fields | Acceptance criteria, scope link, plan link, estimate | Named in `project.json` so the OS reads/writes the right fields |
| Attachments / linked docs | Source artifacts for scoping | Referenced, never copied (existing rule) |

### 4.2 The `jira` plugin (working-copy model)

A new `jira` plugin mirrors `jetrix` one-for-one:

```
<workspace-root>/
└── .jira/                          # ENTIRELY gitignored (disposable working copy)
    ├── project.json                # identity + custom-field + transition wiring; regenerated by /jira:init
    ├── cache/                       # local mirror of pulled Jira issues + fields
    │   ├── cache.manifest.json      # per-section hash → incremental pull
    │   ├── sync-state.json          # per-issue version for optimistic-lock on push
    │   └── id_map.json              # { local_id, jira_key, field, hash } → idempotent upsert
    └── <project-slug>/              # the BA/TL/QA/Dev/Doc working copy
        ├── tickets/                 # NEW — one folder per scoped ticket (see §6)
        ├── shared-context/
        └── context/
```

Three verbs, identical semantics to Jetrix:

- **`/jira:init <project>`** — bind identity; pull the Jira project, issue-type map, workflow transitions and custom-field IDs into `project.json`.
- **`/jira:pull`** — Jira → cache, incremental and read-only against Jira. Refreshes issues, fields, attachments. Run at session start and always before a push.
- **`/jira:push`** — cache → Jira, the only path that mutates Jira. Idempotent (upsert by issue key / field via `id_map`), transactional (propose → diff preview → commit/cancel), and safe (pull-before-push; stop on a both-sides-changed conflict rather than clobber a Jira edit). All reads/writes go through the **Jira MCP** — never scripts or curl.

> **Two-way, per the client's model.** Jira holds the epic/story/bug/request information; each downstream stage writes its structured result *back onto Jira*. The next table is the contract for that.

### 4.3 Stage → Jira write-back matrix

This is the heart of "the SDLC runs through Jira." Each stage reads Jira, does local work, and pushes a defined artifact back.

| Stage (command) | Reads from Jira | Writes back to Jira |
|-----------------|-----------------|---------------------|
| **Scoping** (`/ba:scope <KEY>`) | Issue fields, description, attachments, issue type | The **type-specific scope** written onto the ticket (Scope custom field / linked doc), `ticket_type` label applied, **Acceptance Criteria** field populated, status → *Scoped* |
| **Feature breakdown** (`/ba:features`) | The scoped Feature/Story | Creates **sub-tasks** in Jira — one per feature slice — linked to the parent, each carrying its feature ID and acceptance criteria |
| **Planning** (`/tl:plan`) | Feature + its sub-tasks | Writes the **implementation plan** into Jira (Plan field / sub-task descriptions), attaches page/endpoint/entity breakdown, sets estimates, status → *Ready for Dev* |
| **Build** (`/dev:build`) | Plan + sub-task | Creates the branch per §6 naming, commits with the smart-commit key, transitions sub-task *In Progress → In Review*, links the PR |
| **Code review** (`/dev` review + `/qa` gates) | The PR + plan | Posts review outcome + **quality-gate result** as a structured comment; transitions on pass/fail |
| **QA** (`/qa:*`) | Acceptance criteria + gates | Records gate status (`QG-###`) and findings (`QAF-###`) back on the issue |
| **Docs** (`/doc:*`) | Approved scope | Attaches the client-facing deliverable (deck/proposal link) to the Epic |
| **Sync** (`/jira:push`) | — | The idempotent upsert path all of the above ride on: records + status transitions committed transactionally |

### 4.4 Notion — the PRD surface

Requirements are captured where the product team already lives: **Notion**. The two surfaces divide cleanly.

| Surface | Holds | Owned by | Synced by |
|---------|-------|----------|-----------|
| **Notion** | The **PRD** (product requirements) — the reviewed, rated, human-facing requirement document | Product / BA | A `notion-sync` capability (pull the base doc in; push the PRD out) |
| **Jira** | Execution — epics, stories, sub-tasks, bugs, implementation plan, status | Delivery | `/jira:push` |

The flow between them: scoping reads inputs (Notion base doc + Jira ticket + local artifacts), produces a validated scope, and **renders the scope into a PRD that is synced to Notion**. The PRD is the requirement-capture artifact — it is reviewed and **rated** (reusing the existing `/ba:review` estimate-readiness scoring), and the rating + updates are written back to Notion. Only once the PRD is approved does the **feature breakdown** run, and *its* outputs (feature stories) land in **Jira**. So requirements are proven in Notion; work is executed in Jira.

Inputs a BA can point the scoping agent at (any combination):
- a **Notion** page/database (a base requirement doc);
- a **Jira** ticket (with its description / attached base document);
- a **local folder** of scope artifacts (transcripts, specs, screenshots) — referenced, never copied.

---

## 5. Ticket type — a first-class dimension

### 5.1 Canonical ticket types

A new controlled vocabulary in the document contract:

```
ticket_type: Bug | Feature | Client-Request
```

Jira's own issue-type names are mapped onto this canonical set in `project.json` (e.g. Jira "Story"/"Task" → `Feature`; "Bug"/"Defect" → `Bug`; a Service/portal request type → `Client-Request`), so the OS is insulated from each board's naming.

### 5.2 Type → template → SDLC path (the scope profile)

Each type maps to a **scope profile**: a predetermined template, a required-section set, and the SDLC path it follows.

| Ticket type | `scope_profile` | Template centrepiece | SDLC path |
|-------------|-----------------|----------------------|-----------|
| **Bug** | `bug` | **RCA** (5-whys) + mandatory regression test | scope(RCA) → fix-plan → build → review → **regression gate** → close |
| **Feature** | `feature` | Use cases + functional requirements + acceptance | scope → **breakdown (sub-tasks)** → plan → build → review → QA gates → (doc if client-facing) |
| **Client Request** | `client-request` | **Triage** + classification + routing decision | scope(triage) → **spawns** child Feature/Bug → those follow their own paths |

The point to demonstrate: **different types take different depths of the same rails.** A bug skips discovery and centres on root cause + a failing-then-passing test; a feature runs the full loop; a client request is triage that routes work into child tickets.

---

## 6. Unified naming & structure conventions

Everything downstream keys off `<JIRA-KEY>` + a deterministic `<slug>`.

### 6.1 Slug rule
`slug` = the Jira issue **summary**, lowercased, non-alphanumerics collapsed to hyphens, trimmed to ~40 chars, deterministic (same summary → same slug for everyone). Example: `PROJ-123 "Supplier portal onboarding"` → `supplier-portal-onboarding`.

### 6.2 Per-ticket workspace layout
```
.jira/<project>/tickets/<JIRA-KEY>_<slug>/
├── scope.md            # the type-specific scope (Bug RCA / Feature / Client Request)
├── plan.md             # TL implementation plan (features/bugs)
├── context/            # pages / endpoints / entities the ticket touches
└── review/             # code-review + QA gate outputs
```

### 6.3 Branch / commit / PR conventions
Derived mechanically from the ticket type + key + slug (key and slug joined by `_`, per the org convention):

```
Branch    <prefix>/<JIRA-KEY>_<slug>
          feature/PROJ-123_supplier-portal-onboarding
          bugfix/PROJ-145_null-invoice-on-void
          request/PROJ-160_bulk-export-ask     (rare; requests usually spawn children)

Commit    <JIRA-KEY>: <imperative subject>          → PROJ-123: add supplier onboarding endpoint
          (Jira smart-commit auto-links the work to the issue)

PR title  [<JIRA-KEY>] <ticket summary>             → [PROJ-123] Supplier portal — onboarding
```

Branch-prefix map: `Feature → feature`, `Bug → bugfix`, `Client-Request → request`.

---

## 7. The scoping agent (design, under `/ba:scope`)

> Ideation-phase design only — described here, **not implemented**. It lives under the existing `/ba:scope` entry point, extended to accept a Jira key and switch templates by type.

`/ba:scope <JIRA-KEY>` behaviour:

1. **Pull** the issue via `/jira:pull` (fields, description, attachments).
2. **Resolve type** — map the Jira issue type to the canonical `ticket_type` via `project.json`.
3. **Select the template** for that type's `scope_profile`.
4. **Draft the scope** — fill the template from the ticket + attachments, assigning stable IDs, tracing every fact back to the ticket (`[JIRA <KEY>]`) or a source artifact, and raising open questions as clarifications (`CLR-###`).
5. **Write back** — push the scope onto the Jira ticket, populate the Acceptance Criteria field, apply the `ticket_type` label, and transition status → *Scoped*.
6. **Surface** a run summary: what was scoped, open questions to take to the client/PO, and the next stage.

`/ba:scope` with no Jira key keeps its current whole-engagement discovery behaviour — the two modes coexist.

---

## 8. Format templates (org-wide, one per type)

These are the predetermined formats. Frontmatter conforms to the contract, plus the three new keys (`scope_profile`, `ticket_type`, `jira_key`).

### 8.1 Bug — RCA is the centrepiece

```markdown
---
doc_type: scope
scope_profile: bug
ticket_type: Bug
jira_key: PROJ-145
schema_version: 1.3
produced_by: ba
status: Draft
generated_at: 2026-08-04
---

# PROJ-145 — [Bug summary]

**Severity:** [S1 Critical | S2 Major | S3 Minor]  ·  **Priority:** [M/S/C/W]
**Environment:** [prod | staging | …]  ·  **Reported by:** [name/channel]  ·  **Affects:** [module / area]

## 1. Symptom
[Observed behaviour, verbatim from the ticket.]  `[JIRA PROJ-145]`

## 2. Expected vs Actual
- **Expected:** […]
- **Actual:** […]

## 3. Impact & Blast Radius
[Who/what is affected, how many users, data at risk, current workaround if any.]

## 4. Reproduction
1. [step]  2. [step]  → [failure]     **Reliability:** [always | intermittent — %]

## 5. Investigation Log
| When | Finding | Evidence |
|------|---------|----------|
| … | … | [log / commit / trace] |

## 6. Root Cause (5-Whys)  ← mandatory
1. Why did it happen? …
2. Why? …
3. Why? …
4. Why? …
5. Why? …
**Root cause:** [the actual defect + where it lives]  `[file:line / commit]`

## 7. Fix
[What changes and why it resolves the *root cause*, not just the symptom.]

## 8. Regression Test  ← mandatory
[The test that fails before the fix and passes after — ID + location.]  `TEST-###`

## 9. Prevention / Follow-ups
| Action | Owner | New ticket |
|--------|-------|-----------|
| [guardrail / lint / alert / doc] | … | [PROJ-###] |

## 10. Sign-off
Root cause confirmed · fix verified · regression test green · no new out-of-scope risk.
```

### 8.2 Feature

```markdown
---
doc_type: scope
scope_profile: feature
ticket_type: Feature
jira_key: PROJ-123
schema_version: 1.3
produced_by: ba
status: Draft
generated_at: 2026-08-04
---

# PROJ-123 — [Feature name]

**Epic / Initiative:** [epic key / batch]  ·  **Priority:** [M/S/C/W]  ·  **Area:** [module]

## 1. Problem & Outcome
- **Problem:** [the user/business problem]  `[JIRA PROJ-123]`
- **Outcome at done:** [what must be true to call this shipped]

## 2. In Scope / Out of Scope
- **In:** […]
- **Out:** […]

## 3. Use Cases
##### [AREA-UC-01] — [name]
- **Actor / Trigger / Preconditions:** …
- **Flow:** 1. … 2. … 3. …
- **Worked example:** …  `[EX-###]`

_(repeat per materially-distinct route)_

## 4. Functional Requirements
| ID | Requirement | Use Cases | Resp. | Pri. | Acceptance criteria |
|----|-------------|-----------|-------|------|---------------------|
| PROJ-FR-01 | … | AREA-UC-01 | DET | M | … |
| PROJ-AI-02 | … | AREA-UC-01 | AI  | M | [≥95% on agreed test set → else triage] |

## 5. Data & Integrations
- **Data:** [fields / entities]  `DATA-###`
- **Integrations:** [external systems + direction]  `INT-###`

## 6. Dependencies & Assumptions
[Blocking tickets, assumptions `ASM-###`, decisions `DEC-###`.]

## 7. Open Questions (for client / PO)
| ID | Question | Blocks estimate? |
|----|----------|------------------|
| CLR-01 | … | Y/N |

## 8. Sub-task Plan (feeds Jira breakdown)
| Slice | Feature ID | Rough size |
|-------|-----------|-----------|
| [slice] | FEAT-AREA-001 | [S/M/L] |

## 9. Estimate Readiness
[Ready / Not ready + exactly what is missing.]
```

### 8.3 Client Request — triage & routing

```markdown
---
doc_type: scope
scope_profile: client-request
ticket_type: Client-Request
jira_key: PROJ-160
schema_version: 1.3
produced_by: ba
status: Draft
generated_at: 2026-08-04
---

# PROJ-160 — [Request title]

**Requested by:** [client contact]  ·  **Channel:** [email/call/portal]  ·  **Received:** [date]

## 1. Raw Request
> [verbatim what the client asked for]  `[JIRA PROJ-160]`

## 2. Clarified Intent
[What they actually need, restated in our words for confirmation.]

## 3. Classification Decision
- **This is really a:** [Feature | Bug | Change Request | Support] — [why]
- **Contractual:** [in current scope | change order | T&M]

## 4. Impact & Options
| Option | Approach | Rough effort | Trade-off |
|--------|----------|--------------|-----------|
| A | … | … | … |
| B | … | … | … |

## 5. Recommendation
[Preferred option + reasoning.]

## 6. Questions Back to Client
| ID | Question | Needed before |
|----|----------|---------------|
| CLR-01 | … | commit / estimate |

## 7. Routing / Next Action
- **Spawns:** [PROJ-### Feature] · [PROJ-### Bug]  (created as linked Jira issues)
- **Status →** [Needs client confirmation]
```

### 8.4 Feature story (produced by feature breakdown)

Once a Feature's PRD is approved, `/ba:features` breaks it into **feature stories** in this fixed format — everything a developer needs to implement the slice with no further questions. Each story is written back to Jira as a sub-task/story.

```markdown
---
doc_type: feature-story
scope_profile: feature
ticket_type: Feature
jira_key: PROJ-123
feature_id: FEAT-ONB-001
prd_ref: <notion-prd-url>
schema_version: 1.3
produced_by: ba
status: Draft
generated_at: 2026-08-04
---

# FEAT-ONB-001 — [Feature slice name]

## About / Description
[As a <role>, I want <capability>, so that <outcome>.]  `[PRD FEAT-ONB-001]`

## Business Goal
[Why this slice exists — the value it delivers.]

## Business Rules
- [BR-01] …
- [BR-02] …

## Validation Logic
| Field / action | Rule | On failure |
|----------------|------|-----------|
| … | … | … |

## Acceptance Criteria
- [ ] Given … when … then …
- [ ] Given … when … then …

## Test Cases
| ID | Scenario | Steps | Expected |
|----|----------|-------|----------|
| TC-01 | happy path | … | … |
| TC-02 | edge / negative | … | … |

## Dependencies
[Blocking features / tickets / integrations `INT-###`.]

## Definition of Done
Code merged · tests green · acceptance criteria met · PRD ↔ Jira in sync.
```

On approval, each feature story is created/updated **directly in the Jira ticket** as a sub-task, carrying its `feature_id`, acceptance criteria, and test cases.

---

## 9. Future-state worked example — Unbounce

This is what a day looks like once the OS is rolled out. Names are illustrative.

**The ticket.** `UNB-482 "Self-serve seat management for team accounts"` sits in Jira as a Story under the *Team Accounts* epic, with a short base document in its description and a link to a Notion requirements page.

**Phase 1 — Scoping (BA points the agent at the sources).**
The BA runs `/ba:scope UNB-482` and points it at three inputs: the **Notion** requirements page, the **Jira** ticket `UNB-482` (with its base doc), and a **local folder** `D:\unbounce\seat-mgmt\` holding call transcripts and a competitor screenshot. The agent pulls the Jira issue, reads the Notion base doc, references (never copies) the local artifacts, resolves the ticket type as **Feature**, and drafts a `scope_profile: feature` scope. It raises the **right clarifying questions** the BA must answer before the scope is trusted — e.g. *"Can a team owner remove a seat mid-billing-cycle, and is it prorated?"* (`CLR-01`), *"Do removed members lose access immediately or at cycle end?"* (`CLR-02`) — surfaced as a clean list.

**Phase 2 — Validate → PRD → Notion (with a rating).**
The BA answers the questions; the agent folds the answers in, closes the clarifications, and **renders the validated scope into a PRD**. The PRD is **synced to Notion**, then **reviewed and rated** (via `/ba:review`) — say *"82/100, estimate-ready; two minor assumptions logged."* The rating and any edits are written back to the **Notion** PRD. Requirements are now captured properly, in one place the product team owns, with a quality score attached.

**Phase 3 — Feature breakdown → Jira.**
With the PRD approved, the BA runs `/ba:features`. The **feature-breakdown plugin reads the approved PRD** and decomposes it into **feature stories** (§8.4), each in the full story format — about/description, business goal, business rules, validation logic, acceptance criteria, and test cases — for example:
- `FEAT-SEAT-001 — Invite a member to a team seat`
- `FEAT-SEAT-002 — Remove a member (proration + access revocation)`
- `FEAT-SEAT-003 — Seat-count billing sync`

On finalisation and approval, these are **created directly as sub-tasks under `UNB-482` in Jira**, each carrying its acceptance criteria and test cases — ready for a developer to pick up with nothing left to ask.

**Phase 4 onward — the rest of the SDLC (unchanged rails).**
`/tl:plan` writes the implementation plan into Jira; `/dev:build` opens `feature/UNB-482_seat-management`, commits `UNB-482: …`; code review + QA quality gates post back; `/jira:push` drives the status transitions. The PRD in Notion and the execution record in Jira stay in lock-step throughout.

**The through-line:** *point at your existing sources → get a validated scope with the right questions → a rated PRD in Notion → story-format features in Jira → build on deterministic rails.* Requirements captured where product works; execution tracked where delivery works; both always in sync.

---

## 10. End-to-end SDLC flow (per type)

```
   INPUTS:  Notion base doc  +  Jira ticket (base doc)  +  local artifacts folder
                                        │
                         ┌──────────────┴──── Jira (execution SoT) ────────────────┐
                         │  Epic · Story · Bug · Request · Sub-task · Status         │
                         └───────────────▲───────────────────────┬─────────────────┘
                             /jira:pull   │                        │  /jira:push
                                          ▼                        ▲
                          ┌──────────────────┐  writes scope onto ticket,
                          │  /ba:scope <KEY>  │  sets AC, status → Scoped
                          └────────┬─────────┘  + raises the RIGHT questions to answer
                                   │  scope_profile chosen by ticket_type
        ┌──────────────────────────┼──────────────────────────────┐
        ▼                          ▼                               ▼
  scope_profile: bug        scope_profile: feature        scope_profile: client-request
  RCA + regression          validate answers               triage + classification
        │                          │                               │
  fix-plan (/tl:plan)     render PRD ──▶ Notion (synced)      spawns child
        │                   review + RATING (/ba:review)      Feature/Bug tickets
  build (/dev:build)        │  approved PRD updated in Notion  (each re-enters /ba:scope)
  branch bugfix/KEY_slug    ▼
        │            /ba:features ──▶ story-format sub-tasks in Jira
  review + REGRESSION       │        (about · goal · rules · validation · AC · tests)
        │            /tl:plan ──▶ impl plan in Jira
  /jira:push → Done         │
                     build (/dev:build) branch feature/KEY_slug
                            │
                     code review + QA quality gates ──▶ Jira
                            │
                     /doc:* (if client-facing) ──▶ deck/proposal on Epic
                            │
                     /jira:push → Done
```

Requirements loop lives in **Notion** (scope → rated PRD → approval); execution loop lives in **Jira** (story sub-tasks → plan → build → review → done). Scoping is the bridge that reads all sources and writes both.

Every arrow that leaves a stage is a `/jira:push`: scope onto the ticket, breakdown as sub-tasks, plan as the implementation plan, review/QA as structured comments and gate records, docs as attachments — and status transitions all the way to Done.

---

## 11. Document contract v1.3 — additive changes

Bump `schema_version` to **1.3** and record this in `delivery-os-conventions`:

1. **New frontmatter keys:** `scope_profile` (`bug | feature | client-request`), `ticket_type` (`Bug | Feature | Client-Request`), `jira_key`; and for feature stories `feature_id` + `prd_ref` (the Notion PRD link). Older documents without them remain valid.
2. **New `doc_type`s and vocabulary:** `feature-story` (§8.4) and the `ticket_type` controlled values above.
3. **Notion PRD binding.** The PRD is a first-class artifact on the **Notion** surface; a `notion-sync` capability pulls the base doc in and pushes the rated PRD out. Requirements live in Notion; execution lives in Jira (§4.4).
4. **Pluggable source binding.** §1.b generalised: the source-of-truth binding is a *pluggable* plugin — `jetrix` **or** `jira`. `.jira/` is the working copy with the same gitignored, disposable, pull/push contract as `.jetrix/`. A `jira-sync` skill mirrors `jetrix-sync`.
5. **Per-ticket workspace subtree.** Add `tickets/<JIRA-KEY>_<slug>/` under the project container (§6.2) as the home for ticket-scoped work, alongside the existing engagement-level `ba-output/` etc.
6. **Naming convention section.** The `<prefix>/<JIRA-KEY>_<slug>` branch rule, the `<JIRA-KEY>:` commit rule, and the `[<JIRA-KEY>]` PR rule become part of the contract so Dev enforces them uniformly.
7. **Traceability form.** `[JIRA <KEY>]` and `[PRD <feature_id>]` are accepted source citations, alongside the existing `[SRC-### › path]`.

All seven are additive; deterministic and existing documents are unaffected.

---

## 12. Rollout plan & SDLC lifecycle impact

### 12.1 How each lifecycle stage changes

| Lifecycle stage | Today | After adoption |
|-----------------|-------|----------------|
| **Intake / Request** | Ad-hoc; requests arrive in many forms | Client requests become `Client-Request` tickets; scoped through the triage template; routed into child Feature/Bug tickets |
| **Analysis / Scoping** | Whole-engagement discovery only | Per-ticket, **type-aware** scope from Notion + Jira + local artifacts; the right clarifying questions raised before validation; uniform format org-wide |
| **Requirements capture** | Scattered / inconsistent | Scope rendered into a **PRD synced to Notion**, reviewed and **rated** (`/ba:review`), updated in Notion — one owned, scored requirement source |
| **Breakdown** | Manual sub-task creation | `/ba:features` reads the approved PRD and creates **story-format sub-tasks in Jira** (about, business goal, business rules, validation logic, acceptance criteria, test cases) |
| **Planning** | Plans live in docs/heads | `/tl:plan` writes the **implementation plan into Jira**, with page/endpoint/entity context |
| **Build** | Branch/commit naming varies by dev | Deterministic `feature|bugfix/<KEY>_<slug>` branches; smart-commit links; auto status transitions |
| **Review** | Inconsistent | `dev-code-review` + `qa` quality gates post structured outcomes back to Jira |
| **QA** | Varies | Quality gates (`QG-###`) and findings (`QAF-###`) recorded on the issue; **bugs require a regression test** to close |
| **Docs / Handover** | Separate effort | `/doc:*` attaches client-facing deliverables to the Epic |
| **Reporting** | Manual | Because everything is on the Jira issue in a fixed shape, status and traceability are queryable in Jira directly |

### 12.2 Suggested rollout sequence

1. **Bind one pilot project** — build the `jira` plugin (`init`/`pull`/`push`) + `jira-sync` skill against the Jira MCP, and the `notion-sync` capability for the PRD; wire `project.json` (issue-type map, transitions, custom-field IDs) and the Notion PRD database.
2. **Publish the contract v1.3 edit**, the three type templates, and the feature-story format as the org standard.
3. **Pilot on Bugs first** — smallest, highest-value format (RCA discipline), lowest blast radius. Prove the Jira write-back loop.
4. **Add Feature scoping → PRD → Notion → breakdown** — the scope→PRD→story-in-Jira loop is where the value compounds (the Unbounce example in §9).
5. **Add Client-Request triage + routing.**
6. **Turn on the downstream stages** (plan → build → review → QA → doc) one at a time, each gated on the prior stage's write-back being trusted.
7. **Roll to remaining teams** once the pilot's formats are stable.

### 12.3 Success signals
Every ticket carries its scope in the fixed format; requirements live as a rated PRD in Notion; every feature reaches Jira as story-format sub-tasks with acceptance criteria and test cases; every bug closes with an RCA + a green regression test; branches/PRs are uniformly named and auto-linked; status in Jira reflects the real SDLC stage without manual updates.

---

## 13. Decisions to confirm before implementation

1. **Notion PRD structure** — confirm the Notion database/page structure for PRDs, and the property mapping (rating, status, PRD ↔ Jira link) so `notion-sync` writes to the right place.
2. **Jira write-back targets** — for each stage, confirm *where* on the issue the output lands (custom field vs. description vs. linked page vs. comment). Depends on Unbounce's Jira configuration and available custom fields.
3. **Issue-type mapping** — confirm Unbounce's actual Jira issue-type names so the canonical map (`Story/Task → Feature`, `Bug/Defect → Bug`, request type → `Client-Request`) is correct.
4. **Status workflow** — confirm the transition names (Scoped / Ready for Dev / In Review / Done) so `/jira:push` can drive them.
5. **PRD approval gate** — confirm who approves the rated PRD in Notion before breakdown may run, and the minimum rating (if any) required to proceed.
6. **Whether to keep `jetrix`** alongside `jira`, or replace it for Unbounce.
7. **Extra ticket types** — Change Request, Tech-Debt, Spike are out of the initial three by decision; confirm they stay out for v1.

---

*End of specification (ideation phase).*
