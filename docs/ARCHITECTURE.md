---
title: Techjays Delivery OS — Architecture Overview
audience: Delivery leads, business analysts, technical leads, engineers, QA, client stakeholders
status: current
---

# Techjays Delivery OS — Architecture Overview

Delivery OS turns client discovery material into shipped, verified software through one
continuous, auditable chain. This document covers the purpose of each part, how the parts
connect, and the workflow that runs through them.

Detailed architecture per area:

| Area | Document |
|---|---|
| Business analysis | [architecture/ba-architecture.md](architecture/ba-architecture.md) |
| Development | [architecture/dev-architecture.md](architecture/dev-architecture.md) |
| Code map | [architecture/code-map-architecture.md](architecture/code-map-architecture.md) |
| Project scaffold | [architecture/scaffold-architecture.md](architecture/scaffold-architecture.md) |
| Quality assurance | [architecture/qa-architecture.md](architecture/qa-architecture.md) |

---

## 1. Why the system exists

Software delivery fails at the seams — between what the client said and what was scoped,
between what was scoped and what was planned, between what was planned and what was built.
Each handoff is a point where meaning is re-interpreted, and every re-interpretation is a
chance to drift.

Delivery OS removes the seams by making every artifact a **typed, identified, traceable
object** that the next stage consumes mechanically rather than by interpretation.

Three principles hold it together.

**Nothing is invented.** Where the source material is silent, the system raises an identified
open question. It never fills a gap with a plausible guess. A missing fact becomes a `CLR-###`
the client can answer, not a sentence in a document nobody can trace back.

**Every judgment is derived, not felt.** Scores come from a published formula over a coverage
map. Verdicts come from bands over those scores. A number that cannot be recomputed from its
inputs is treated as a defect, not as an opinion.

**State lives in files, not in conversation.** Each stage writes its output to a known path
with known frontmatter. A later stage — or a different person, or a different agent, weeks
later — reads that path and continues. No stage depends on remembering a chat.

---

## 2. The parts and what each is for

| Part | Purpose | Entry commands |
|---|---|---|
| **Core** | The shared document contract, vocabulary, templates and workspace scaffolder every other part speaks | `/delivery-os:init`, `/delivery-os:setup` |
| **BA** | Turn raw client material into a scored, defensible scope and an implementation-ready feature breakdown | `/ba:scope`, `/ba:review`, `/ba:resolve`, `/ba:features` |
| **TL** | Own technical design: reverse-map existing code, scaffold new repositories, score production readiness | `/tl:code-map`, `/tl:scaffold`, `/tl:maturity` |
| **Dev** | Plan, build and ship a feature through gated loops | `/dev:plan`, `/dev:build`, `/dev:commit`, `/dev:review`, `/dev:fix-review`, `/dev:resolve` |
| **QA** | Define what "verified" means and make the repository able to prove it | `/qa:audit`, `/qa:plan`, `/qa:setup`, `/qa:health` |
| **Doc** | Produce client-facing collateral from the same source material | `/doc:proposal`, `/doc:deck`, `/doc:walkthrough`, `/doc:workflow`, `/doc:magic-board` |
| **Jetrix** | Bind the workspace to the delivery platform and keep both in sync | `/jetrix:init`, `/jetrix:pull`, `/jetrix:push`, `/jetrix:project-setup` |

Seven plugins carry **32 commands** and **29 skills**. Commands are the human entry points;
skills carry the method and are reused across plugins. `tl` behaves as a second core — `/dev:plan`
cannot run without it.

---

## 3. How the parts connect

```
   CLIENT MATERIAL
         │
         ▼
   ┌───────────────┐
   │      BA       │  classify → extract → scope → review → resolve → gate → features
   └───────┬───────┘
           │  features/<slug>/  (acceptance criteria, business rules, NFRs, test scenarios)
           ▼
   ┌───────────────┐       no repo?      ┌──────────────────┐
   │   TL / DEV    │ ──────────────────► │   TL SCAFFOLD    │  stack decisions → green base repo
   │   PLANNING    │                     └────────┬─────────┘
   └───────┬───────┘                              │
           │  repo exists?  ┌──────────────────┐  │
           ├───────────────►│   TL CODE MAP    │  │  reverse-map → as-built context
           │                └────────┬─────────┘  │
           │                         │            │
           ▼                         ▼            ▼
   ┌───────────────────────────────────────────────────┐
   │        CODE CONTEXT GRAPH  (units + indexes)      │
   │   endpoints · pages · entities · bidirectional    │
   └───────────────────────┬───────────────────────────┘
                           │  reused by planning, by BA question screening,
                           │  and by any codebase question
                           ▼
                   ┌───────────────┐
                   │  IMPLEMENTATION PLAN  (§1–§8)  │
                   └───────┬───────────────────────┘
                           ▼
   ┌───────────────┐   governed by   ┌───────────────┐
   │   DEV BUILD   │ ◄────────────── │ QA quality-   │
   │   DEV COMMIT  │ ◄────────────── │ gates.md      │
   └───────┬───────┘                 └───────────────┘
           │
           ▼
     PULL REQUEST  →  merge  →  context graph marked implemented
```

Every arrow is a file on disk, not a conversation. That is what lets a different person, or a
different agent, pick the chain up at any point.

---

## 4. The workflow, end to end

### Phase 1 — Discovery and scope *(BA)*

Client material is registered, classified by how deeply it deserves to be read, and mined
against a fixed taxonomy. The result is a living scope document plus derived registers. Every
uncertainty becomes an identified question, assumption or contradiction rather than a silent
decision.

### Phase 2 — Validation *(BA)*

The scope is interrogated feature by feature across nine business dimensions, scored by formula,
and every gap becomes a question routed to an owner. The client answers inside a generated
report; each answer is adjudicated rather than accepted, folded back into the scope, and the
scores recomputed. The loop repeats until a readiness gate passes.

### Phase 3 — Breakdown *(BA)*

An approved scope becomes one self-contained folder per feature: business context, acceptance
criteria, business rules, NFRs, test scenarios, dependencies, status. No scope item may be
silently dropped.

### Phase 4 — Technical foundation *(TL)*

Two entry points depending on what exists.

- **No repository** → `/tl:scaffold` establishes the stack, the skeleton, the tooling, the
  design system and a green base build.
- **Repository exists** → `/tl:code-map` reverse-maps it into a committed, index-first context
  tree marked as-built.

Either way the output is the same shape: a graph of endpoints, pages and entities that later
planning reuses rather than duplicates.

### Phase 5 — Quality foundation *(QA)*

The repository is audited for testability, the human approves the recommendations, the harness
is built and proven green, and `qa/quality-gates.md` is published — the contract the delivery
loop enforces.

### Phase 6 — Planning *(Dev + TL)*

Each feature is mapped onto the context graph, split per repository where needed, and composed
into an eight-section implementation plan in stack-agnostic vocabulary. Every decision a
developer would otherwise stop and ask about is surfaced as a plan blocker first.

### Phase 7 — Build and ship *(Dev)*

Build implements against the plan, writes tests, and produces a verifiable test map. Commit is
the only executor: it runs the suite, reviews security and code, re-verifies acceptance,
merges the context graph and raises the pull request. Gates block; they do not warn.

---

## 5. Workspace layout

Two levels, deliberately separated.

```
.jetrix/                          gitignored — platform binding and caches
├── project.json                  tracker binding
├── connection-map.md             cross-repo wiring and external integrations
├── code-map-registry.md          one row per mapped repository
├── cache/                        repo paths · drift hashes
│
├── shared-context/               PROJECT LEVEL — outlives every requirement
│   ├── decision-log.md           append-only DEC-###
│   ├── glossary.md               data.md · integrations.md · system-landscape.md
│   └── architecture.md           technology-stack.md · coding-standards.md
│
└── requirements/<slug>/          REQUIREMENT LEVEL — one body of work
    ├── scope.md                  THE source
    ├── sources.md                SRC-### registry
    ├── ledger.md                 CLR · CON · ASM in one table
    ├── artifacts/                normalized source summaries
    ├── registers/                projections of scope.md — never hand-edited
    ├── reviews/                  review rounds, local only
    └── features/<feature-slug>/  BA authors · TL enriches · Dev delivers
        └── units/<repo>/         one folder per repository touched
```

**Project level** holds what outlives any single requirement — glossary, decisions, system
landscape, coding standards. **Requirement level** holds one body of work. A second requirement
reuses the project context instead of restating it.

The **code context** does not live here. It lives inside each mapped repository at
`<repo>/context/code-context/`, so it travels with the code and is reviewed in the same pull
request.

---

## 6. Identifier scheme

Stable identifiers are what make traceability mechanical rather than narrative.

| Prefix | Object | Minted by |
|---|---|---|
| `SRC-###` | Registered source artifact | BA classification |
| `CLR-###` | Clarification — an open question | BA extraction and review |
| `CON-###` | Contradiction between sources | BA extraction and resolution |
| `ASM-###` | Accepted assumption | BA resolution |
| `DEC-###` | Logged decision | Any role |
| `EX-###` | Client-supplied example | BA extraction |
| `FEAT-<AREA>-NN` | Feature | BA breakdown |
| `EP-` · `PAGE-` · `ENT-` | Endpoint · page · entity unit | TL planning and code map |
| `PB-###` | Plan blocker needing a human | Dev planning |
| `QAF-###` | Quality-assurance finding | QA audit |
| `MAT-###` | Maturity finding | TL maturity audit |
| `BL-##` | Mandatory QA baseline item | QA audit |

Identifiers are **append-only**. `CLR-004` in round four is the same question it was in round
one; only its status and resolution thread change. That is what lets a reader follow one
question from the transcript that raised it to the scope sentence that closed it.

The full chain:

```
SRC-###  →  CLR-###  →  scope §3.x  →  FEAT-<AREA>-NN  →  EP-/PAGE-/ENT-  →  commit  →  PR
```

---

## 7. Platform integration

Four MCP servers connect the local workspace to the Jetrix platform.

| Server | Moves | Direction |
|---|---|---|
| `project-mcp` | Solutions, applications, environments, repositories, connection maps | Read + connection writes |
| `scope-mcp` | Scope document, registers, shared context | Push and pull |
| `task-mcp` | Features and tasks, comments, attachments | Push and pull |
| `deliverable-mcp` | Client-facing HTML deliverables | Push |

File bytes never pass through the agent's context. Uploads broker a signed URL and stream from
disk; downloads fetch in parallel directly from storage. A hundred-file push costs the same
context as a one-file push.

---

## 8. Properties that hold across every area

**Idempotence.** Re-running a command updates in place rather than duplicating. Pushes upsert by
stable identifier and skip unchanged content by hash; pulls skip files whose hash already
matches. The default recovery action when something is unclear is simply to run it again.

**Refusal over invention.** Every area has a hard entry gate. `/ba:features` refuses an
unreviewed scope. `/dev:build` refuses an unplanned task. `/dev:commit` refuses unfinished work.
`tl-read-code-context` refuses to answer where the graph is silent. The system would rather stop
than produce something unfounded.

**Human decision points are explicit.** Brand identity, technology stack where the architecture
is silent, coverage floors and test strategy, scope overrides at the readiness gate,
architectural and security findings — each is surfaced as an identified, logged item rather
than resolved by inference.

**Machine-checked consistency.** Prose instructions degrade; checks do not. A lint suite
validates the plugin corpus on every change — cross-file references, document schemas, status
vocabularies, stage contracts, frontmatter, and controlled vocabulary drift. Contracts that
agree by inspection are not assumed to agree; they are tested.

---

## 9. Reading path by role

| If you are | Start with |
|---|---|
| Delivery lead | §2 the parts, §4 the workflow, then BA §5 scoring and §7 the readiness gate |
| Business analyst | [ba-architecture.md](architecture/ba-architecture.md) in full |
| Technical lead | [code-map-architecture.md](architecture/code-map-architecture.md), [scaffold-architecture.md](architecture/scaffold-architecture.md), then dev §3 planning |
| Engineer | [dev-architecture.md](architecture/dev-architecture.md) in full |
| QA engineer | [qa-architecture.md](architecture/qa-architecture.md), then dev §7 test engine |
| Client stakeholder | §1 why it exists, §4 the workflow, then BA §6 and §7 |
