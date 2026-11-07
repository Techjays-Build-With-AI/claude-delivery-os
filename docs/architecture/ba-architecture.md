---
title: Business Analysis — Architecture
audience: Business analysts, delivery leads, client stakeholders
status: current
---

# Business Analysis — Architecture

The BA stage converts unstructured client material into a scored, defensible scope and an
implementation-ready feature breakdown. It carries the highest leverage in the system: an error
here is multiplied by every downstream stage.

---

## 1. Architecture

### 1.1 Components

| Component | Responsibility |
|---|---|
| `/ba:scope` | Register sources, classify, extract, build and maintain the living scope |
| `/ba:review` | Interrogate the scope feature by feature; score it; raise questions |
| `/ba:resolve` | Adjudicate client answers; fold them back; recompute; write the next round |
| `/ba:features` | Gate on readiness, then decompose into self-contained feature folders |
| `ba-classification` | How sources are ingested, weighted and normalized |
| `ba-extraction` | What is mined from each artifact and where it is recorded |
| `ba-scope-review` | The dimensions, the scoring formula, the question screens |
| `ba-feature-breakdown` | How a scope becomes feature folders |

### 1.2 Data model

```
  sources.md ─── SRC-###  ──┐
                            │
  artifacts/<category>/*.summary.md
                            │
                            ▼
                      ┌──────────┐
                      │ scope.md │   THE single source
                      └─────┬────┘
                            │ projected into (never hand-edited)
        ┌───────────┬───────┴───────┬──────────────┬──────────────┐
        ▼           ▼               ▼              ▼              ▼
 requirements.md  use-cases.md  workflows.md  business-rules.md  examples.md

  ledger.md ─── CLR-### (questions) · CON-### (contradictions) · ASM-### (assumptions)

  reviews/review-<ts>.html  ──►  review-<ts>-responses.md  ──►  next round
```

**The registers are projections.** They exist because six different consumers need structured
access to facts that live inside a narrative document. Editing a register instead of the scope
creates two sources of truth — the exact failure the architecture prevents.

---

## 2. Process

### 2.1 Classification — deciding how deeply to read

Sources arrive as an intent statement, not a file list: *"transcripts in this folder,
requirements at this link, the invoice archive for reference only."*

Each source passes six steps:

```
  locate → detect → classify → categorize → register → normalize
```

**Locate** resolves the path or link. **Detect** samples type, count, size cheaply. **Classify**
assigns a usage mode. **Categorize** names an emergent category. **Register** writes the
`sources.md` row. **Normalize** produces a summary appropriate to the mode.

Six usage modes govern how much effort a source earns:

| Usage mode | Treatment |
|---|---|
| Deep Analysis | Full per-document summary with BA-relevant signals and key quotes |
| Sample and Summarize | Structure described from a recorded sample; no global rules inferred |
| Reference Only | Index entry and high-level description; never read in depth |
| Index Only | Folder-level listing — names, types, counts, sizes |
| Future Agent Input | Registered for a later role; not analyzed now |
| Needs User Guidance | Not summarized; the row carries the reason and a recommended mode |

**Why modes exist.** A 4,000-file invoice archive and a one-hour discovery transcript are not
equally informative. Reading both exhaustively wastes the budget that should go to the
transcript; inferring business rules from a sampled archive invents requirements. The mode is an
explicit, recorded decision about evidentiary weight, and an explicit user instruction always
overrides inference.

**Originals are referenced in place — never copied or moved.** The workspace holds summaries and
pointers, not a second copy of the client's material.

### 2.2 Source authority

Answers do not carry equal weight, and the weight travels with every fact derived from them.

```
  client-signed  >  client-authored  >  client-relayed  >  internal  >  as-built
```

This ladder lets the review state *"the scope is complete, but rests on answers relayed through
us rather than confirmed by the client"* — materially different from *"the scope is complete."*

### 2.3 Extraction — twenty categories

Every eligible artifact is mined against a fixed taxonomy, and **each category is reported even
when empty**, because "no integrations were mentioned" is itself a finding.

| | | | |
|---|---|---|---|
| Business objectives | Stakeholders and actors | Current workflows | Future expectations |
| Functional requirements | Business rules | Data entities | Integrations |
| Reports and dashboards | Notifications and alerts | Permissions and roles | Pain points |
| Manual effort | Exceptions and edge cases | Compliance and security | Examples and scenarios |
| Terminology | Assumptions | Clarifications needed | Contradictions |

The last three are the system's memory of its own uncertainty and feed the ledger directly as
`ASM-###`, `CLR-###` and `CON-###`.

### 2.4 Review — nine dimensions

| # | Dimension | The question it asks |
|---|---|---|
| 1 | Current → Future state | Is today's process described, and the future split across AI / deterministic / human? |
| 2 | In scope / Out of scope | Is the boundary explicit? Silence here is the most expensive kind |
| 3 | Functional requirements | Are capabilities enumerated with responsibility and priority? |
| 4 | AI / Automation responsibilities | Confidence threshold, fallback, human-in-the-loop — or hand-waving? |
| 5 | Business rules | Are thresholds and decision logic stated? |
| 6 | Information & data | What information is captured and produced, at business level |
| 7 | Integrations | Which systems, what flows, which direction, who owns the dependency |
| 8 | Exceptions & edge cases | Business unhappy paths and who handles them |
| 9 | Acceptance criteria | What "done" means to the business |

**The review is strictly business-level.** Schema, field types, API contracts, auth mechanisms
and infrastructure belong to the technical specification review. A scope is never penalised for
omitting them.

**Applicability.** Each dimension is marked `applicable`, `not-applicable`, or scored. A module
with no integrations and no AI component is scored out of seven, not nine. Scoring it out of
nine charged it points for work it was never going to do, which systematically depressed
well-specified simple features.

### 2.5 Resolution loop

```
  review round N  ──►  client answers in the HTML report  ──►  export responses
                                                                     │
                                            ┌────────────────────────┘
                                            ▼
                                       adjudicate
                                            │
                        ┌───────────────────┼───────────────────┐
                        ▼                   ▼                   ▼
                    Resolved        Accepted-assumption    Needs-verification
                   (terminal)          (terminal)        (follow-ups asked)
                        │                   │                   │
                        └─────────┬─────────┘                   │
                                  ▼                             │
                     fold into scope + registers                │
                                  ▼                             │
                     revalidate impacted questions              │
                                  ▼                             │
                   recompute coverage · score · verdict         │
                                  ▼                             │
                        write round N+1  ◄────────────────────-─┘
```

| Outcome | Meaning | Terminal |
|---|---|---|
| `Resolved` | Substantively answers the question with estimable specifics | Yes |
| `Accepted-assumption` | Not confirmable now; the team proceeds on an explicit, logged assumption | Yes |
| `Needs-verification` | Plausible but thin or unverifiable; 1–3 specific follow-ups asked | No |
| `Won't-fix` | Declined, with rationale | Yes |

---

## 3. Best-practice checks

### 3.1 How a question earns the right to be asked

A question is not simply "something the scope doesn't say." It must survive three screens.

```
  candidate gap
        │
        ├─ already answered elsewhere in the scope?  ── yes ──► DROP (reading error)
        │
        ├─ same fact missing across many features?   ── yes ──► MERGE into ONE
        │                                                        scope-level question
        │
        ├─ does mapped code already answer it?       ── yes ──► DROP
        │
        └─ otherwise ──► RAISE as CLR-###, with consequence and owner
```

**Search before asking.** The scope is not read top to bottom by its author; an obligation opened
in one module is often closed in a global section. Every candidate re-scans the places its answer
would live — the feature's own sub-headings, the global out-of-scope section, the ledger, the
example register — and records them in the question's `checkedIn` field.

**Merge scope-wide gaps.** Twelve features with no non-functional requirements is *one fact about
the scope*, not twelve gaps. The test is whether a single answer closes them all. The merged
question still deducts on every feature it came from — merging changes what the client must
answer, not whether the gap counted.

**Ask nothing the running system answers.** Where repositories are mapped, questions are screened
against the code context first. Asking a client which authentication method they want, for a
product that has had single sign-on for two years, costs more credibility than the answer is
worth.

### 3.2 What makes the resolution loop trustworthy

**A carried question explains itself.** When a question returns in a later round it arrives with
`Previously answered`, `Why it is still open` and `Still needed` — each fed from a recorded field,
so a section is absent only when there is genuinely nothing to report. Without this the author
cannot tell which part of their answer fell short.

**An answer's blast radius is checked.** Promoting an answer edits the scope, and other open
questions were screened against the text it just changed. The impacted set is derived from
`checkedIn`, module, and shared use cases; each is re-screened against the new text and may be
closed, rewritten, or raised as a contradiction. A merged scope-level question moves the
dimension on **every** feature that cited it.

**A terminal question can reopen.** If a round-three answer changes the authentication model, a
question closed in round one against the old model is no longer answered. It reopens with a
rationale naming what invalidated it — never by editing the original closure away.

**Every moved score carries its cause.** Each changed dimension records `from`, `to` and the
identifier that moved it. A dimension may only move *down* if a new question goes up; a downward
move with no new question is re-judging in disguise and is rejected.

### 3.3 Validation against client examples

Every feature is checked against the examples the client actually supplied (`EX-###`):

| Verdict | Meaning |
|---|---|
| Pass | The scope as written can satisfy the example end to end |
| Partial | Some path or field the example implies is not in scope |
| Conflict | The example contradicts the scope |

A scope that looks complete but cannot satisfy a real example the client handed over is not
complete. Example conflicts are first-class gaps.

---

## 4. Scoring and evidence

### 4.1 The formula

```
  coverageScore = Σ(Covered = 1, Partial = 0.5, Absent = 0 over APPLICABLE dimensions)
                  / applicable_count × 10

  cap           = 4 if Unbounded · 6 if Partially-bounded · none if Bounded

  score         = round(coverageScore)             when Bounded
                = round(min(coverageScore, cap))   when a cap applies
```

`applicable_count` is recorded beside the score so the arithmetic can be checked by hand. The
**boundedness cap** encodes a hard truth: a feature whose edges are undefined cannot be estimated
no matter how richly its middle is described.

### 4.2 Verdict bands

| Band | Condition |
|---|---|
| Scope-ready — estimate with confidence | ≥ 8.5, no Blockers, client-confirmed |
| Estimate with caveats | 6.5 – 8.4, no Blockers |
| Significant gaps — clarify before estimate | 4.5 – 6.4, **or any unresolved Blocker** |
| Not scope-ready — discovery needed | < 4.5 |

Two overrides sit above the arithmetic.

**The Blocker override** caps the verdict regardless of score — any unresolved Blocker means
"Significant gaps" at best.

**The confirmation override** caps the verdict at *Estimate with caveats* when the answers behind
it are `internal`, `assumed` or `client-relayed`. Confidence is a claim about what the client
agreed, not about how much got written.

### 4.3 Evidence produced

| Artifact | What it proves |
|---|---|
| `sources.md` | Which material was read, how deeply, with what authority and content hash |
| `artifacts/**` | The normalized reading of each source |
| `ledger.md` | Every open question, contradiction and accepted assumption with status |
| `reviews/review-<ts>.html` | The scored review with per-feature coverage maps and question threads |
| `review-<ts>-responses.md` | The client's answers, exported from the report |
| Round N+1 | Movement entries: dimension, from, to, cause |

The chain is checkable end to end: a score can be recomputed from its coverage map, a coverage
cell traced to the question that moved it, and that question traced to the source that raised it.

---

## 5. The readiness gate

`/ba:features` refuses to break down a scope that is not ready.

| Condition | Action |
|---|---|
| No review has been run | **Stop** |
| Any open Blocker | **Stop** — named by id, feature and question |
| Any feature Unbounded or Partially-bounded | **Stop** |
| Any feature scoring below 6.5 | Warn, require confirmation |
| Open Majors | Warn, confirm, log each as an accepted assumption |
| Unconfirmed answers on estimate / integrations / compliance | Warn, require caveat acknowledgement |

Blockers and boundedness cannot be overridden. Everything else can, provided the override is
stated and recorded in the ledger.

**Why the gate exists.** The expensive failure is not a scope with known gaps — it is a scope that
reads as complete and is not. A Blocker at least announces itself.

---

## 6. Feature breakdown

Each feature becomes a self-contained folder a developer, tester or coding agent can work from
without opening anything else.

```
  features/<feature-slug>/
  ├── feature.md             business context and the workflow
  ├── acceptance-criteria.md what "done" means
  ├── business-rules.md      the rules that must hold
  ├── nfrs.md                performance, security, availability expectations
  ├── test-scenarios.md      the scenarios QA and dev must satisfy
  ├── dependencies.md        cross-feature waits + open questions
  └── status.md              lifecycle state
```

Every feature carries a stable `FEAT-<AREA>-NN` and source references back to the scope. **No
scope item may be silently dropped** — an item that cannot be confidently placed is reported as a
question, never as an omission.

Re-runs update folders in place and preserve history. The push to the tracker is idempotent —
upsert by feature id — so a re-run after an edit updates the same tickets rather than filing
duplicates.

---

## 7. Boundaries

The BA stage **never** invents product behaviour, UI, business rules, API contracts, schemas or
integrations the source material does not support. It **never** judges implementation detail —
schema, data types, protocols, infrastructure belong to the technical review. It **never** copies
or moves a client's original files. Missing information becomes an explicit open question.
