---
description: Build and continuously update the living project scope from client material. Point it at folders/Google Drive with `add "..."` (it references originals, classifies, and summarizes them), and it maps everything out, writes the module-centric scope document in the Techjays template, and raises every open question and assumption as a clean "questions for the client" deliverable. Feed back a client-answers doc or new meeting notes and it folds them in, closes the answered questions, and updates the living scope. With no args it re-processes registered sources incrementally.
argument-hint: "[add \"transcripts in <path/link>, requirements in <path/link>, answers in <path>, ...\"] [mode=auto|incremental|full-refresh|dry-run|index-only|classify-only]"
---

# /ba:scope

You are the entry point for building and maintaining the project's **living scope document**. Parse the arguments and **delegate the actual work to the `ba-agent` subagent**, which runs in its own context and does the file-heavy processing.

The mental model: **one living scope document** that is created from the first batch of client material and then **kept up to date** as new meeting notes, documents, examples, or client answers arrive. Every run also surfaces the open questions and assumptions the team needs to take to the client, and folds their answers back in when they return.

## 1. Parse arguments

`$ARGUMENTS` may contain, in any order:
- An optional **`add "<free text>"`** payload — a conversational declaration of where sources live, e.g. `add "meeting transcripts in D:\acme\meetings, requirements at <drive-link>, invoice archive in D:\acme\invoices for reference only"`. Sources can be **local folders/files or Google Drive links**. When present, the agent ingests these (classify → summarize → register in `intake.index.md`, referencing originals) **before** processing.
  - The same `add` mechanism is how you feed material **back in**: point it at a filled-in `client-questions.md`, a client-answers document, or a fresh set of discovery/meeting notes, and the agent folds them into the living scope (see "answer round-trip" below).
- An optional **`mode=…`** token (default `auto` if none given).

If `intake.index.md` doesn't exist yet, tell the user to run `/delivery-os:init <name>` first (or, if they clearly want to proceed, have the agent scaffold the minimal workspace). Then continue.

Mode table:

| Mode | Meaning |
|---|---|
| `auto` | Default. Classify sources, deep-analyze primary artifacts, safely index/skip large or reference artifacts, and update the scope. |
| `incremental` | Process only **new or changed** sources (compare against the hashes in the `intake.index.md` registry). The normal mode for an ongoing project. |
| `full-refresh` | Rebuild scope from all eligible artifacts; back up previous `ba/` first. |
| `dry-run` | Report what *would* be ingested/processed and changed. **Write nothing.** |
| `index-only` | Register + classify sources in `intake.index.md` only; no summaries, no extraction. |
| `classify-only` | Classify sources and produce user guidance; no summaries, no analysis. |

If the token is unrecognized, tell the user the valid modes and stop.

### 1a. Which track is this? (ask once, before any extraction)

Read the input first — the `add` payload, the ticket, the file — **then propose a track with a reason.** Do not ask the user to classify work nobody has looked at yet, and do not ask anything about sources until the track is settled: what to ingest depends on the answer.

**Read the signal, do not guess it.** The material present tells you most of it:

| What is there | Reads as |
|---|---|
| Transcripts, meeting notes, client emails, an RFP | **track A** — client material means a client is the answerer |
| A requirement doc or ticket, and repos on disk, no client material | **track B or C** — nobody external to question |
| A one-line ask, one repo, an existing surface | **track C** |

**Never author source material.** Where a source is thin or missing, that is a question for the user or the client — never an offer to write one. Do not generate a transcript, a meeting note, an email or a brief, not as a sample, a mock or an illustration. A fabricated discovery call that "answers some of the brief's open points" closes real `CLR`s with invented answers, mints `DEC`s citing a conversation nobody had, and drops those questions from the client packet — so the gap stops being visible. One requirement document is a perfectly good scope input on its own; its open points are what `client-questions.md` exists to carry.

| Track | For | Code context | Produces |
|---|---|---|---|
| **A · Client requirement** | work a client signs off and someone estimates | no | scope · registers · client packet · HTML — the full pass, unchanged |
| **B · Task needing a BA plan** | a module-sized internal piece: too big for one flat plan, no client to question | **yes — see §1b** | scope document + feature split |
| **C · Simple task** | one repo, understood well enough to build | resolved at plan time | nothing — hands to `/dev:plan` |

```
This reads as a module-sized internal change: 1 repo named, no client material,
roughly 4 surfaces. I would take track B (task needing a BA plan).

  A  client requirement    B  task needing a BA plan    C  simple task
```

**Track C hands off and stops.** Print the reason and the command — `/dev:plan <ref or "description">`, which takes a ticket, a plain `.md`, or a description. Do not build a scope for it.

**Two rules disqualify track C**, both checkable rather than judgement:

- the work's surfaces span **more than one repo**
- it needs **more than ~3 features**

Either one and it is track B at least, whatever it looks like. A simple-looking change across two repos is not simple — it needs the split that only the feature path gives.

### 1b. Track B — start from the code

The reason track B exists is that full BA writes acceptance criteria blind, and the mismatch only surfaces at `/dev:plan`. Track B inverts that: resolve what exists **before** describing what to build.

1. **Repo paths** — read `.jetrix/cache/repolocation.json`. `/jetrix:init` already collects them, so ask for a path only where the workspace is unbound.
2. **Resolve only the area the requirement touches** — not the repo. Check `context/code-context/` exists, then read the units the requirement names and the indexes that lead to them, picking the repo via `.jetrix/connection-map.md` on a multi-repo solution. A requirement about timesheets reads the timesheet units; it does not walk the codebase. No code-context for that area → **ask**, never grep the repo silently; same rule and reason as `/dev:plan` §2a.1.

   **What the code is for here, and what it is not.** It tells you what already exists so you can ask a *better business question* — not so you can start designing. Stay in the BA's seat:

   | Ask this (BA) | Not this (dev — it belongs to `/dev:plan`) |
   |---|---|
   | "Submitting a timesheet twice — should the second be refused, or replace the first?" | "Should the duplicate check sit in the controller or the model?" |
   | "The screen already shows Draft and Submitted. Does this add a state, or reuse Submitted?" | "Which component should own that state?" |
   | "Approval exists for expenses. Should timesheets follow the same rule or a different one?" | "Can we reuse the approval service?" |

   The code answers *what is there*. You are still asking *what should happen* — and a question only counts if a different answer changes the behaviour, not the implementation.
3. **Write the scope against what is there** — what exists, what is new, what changes. A surface the work assumes and the code does not have becomes a question now, not a blocker two commands later.
4. **Split into features, carrying the resolved surfaces with them.** Write what step 2 resolved into each feature's frontmatter — `related_pages`, `related_apis`, `related_entities`. This is the step that makes track B worth taking.

   Without it `/dev:plan` Stage 1a reads no declared units, concludes *not planned*, and auto-runs `/tl:plan` — which **designs from the description** the units track B already **resolved from the code**. Same units, derived twice, and the second pass is the blind one.

   With it, Stage 1a returns *planned* immediately and the units are as-built rather than designed. `/tl:plan` still runs for any genuinely **new** surface in that feature, which is correct — nothing in the code owns it yet.

Then hand each feature to `/dev:plan`. Do not run `/tl:plan` or `/dev:resolve` yourself: `/dev:plan` invokes the TL with no human pause where units are missing, and asks plan blockers in the conversation as they arise.

**Track B writes the registers its own downstream steps read.** `ba-feature-breakdown` walks `requirements`, `workflows`, `business-rules`, `data`, `integrations`, `use-cases`, `assumptions` to build each feature folder, and track B ends in a feature split — so omitting them starves the step this track exists to reach. Write the ones that have content. Skip only a register with nothing to put in it: `examples.md` is usually empty here, because client examples are what track A has and track B does not.

**`/ba:scope` writes questions. It does not ask them.** That separation is the point: this command analyses and records, `/ba:resolve` collects answers and folds them. Raising a question and answering it in the same breath means the record is written after the fact, and there is no moment where the gaps are visible as a set.

So: finish the analysis, write every question down, report the score — and stop. Even a question the person running this could answer in a second goes into the record first.

**Two destinations, decided by who owns the answer:**

| Question is about | Written to | Asked by |
|---|---|---|
| business intent, priority, scope boundary, what the requester meant | **`ba/open-questions.md`** — the deliverable for the requirement's owner | nobody here; it goes to them |
| something the person running the loop can settle — an implementation choice, a technical constraint | the `CLR` ledger, marked `answerable: here` | **`/ba:resolve`**, one at a time |

Both are logged as normal — `CLR` to `ba/logs/clarifications.md`, `SQ-###` to the review `.json` — so the ledger and the round carry-forward are unchanged.

**An unanswered question is not an assumption.** Do not downgrade one into `ASM` to clear the list. An assumption is a position someone took deliberately and can be held to; an unanswered question is a gap with nobody's name on it. Leave it `Open`, let it hold the readiness verdict down, and say who it is waiting on.

**Do not ask what the code already answers.** `§3.x.1 Current → Future State` is a question on track A because nobody has seen the system. On track B the current state **is the code you just resolved** — write it from the units and their files, and ask only about the *future* half. A question whose answer is sitting in a file you have already opened is the thing `checkedIn` exists to prevent.

**Omit a dimension that does not apply; do not probe it.** `§3.x.6 AI / Automation` on a form with no model in it, `§3.x.9 Integrations` on a change that calls nothing — these are client-analysis shaped and produce questions whose answers change nothing. Leave the subsection out, the same way `§2` of an implementation plan omits an unaffected dimension rather than writing `N/A`.

**The test for raising anything at all:** would a different answer change what gets built or what it is checked against? If not, it is not a question — it is ceremony. Every `CLR` on this track has to pass that, on top of the four screening rules.

**Stop condition, and hold to it.** Research ends when every **applicable** §3.x dimension is either filled or recorded as a question — not when it feels complete. This is the step most likely to grow back into the ceremony this track exists to avoid.

## 2. Delegate

Invoke the **ba-agent** subagent with the project root, the resolved mode, and the `add` payload (if any). Pass it this instruction:

> Run a BA scope build/update in `<project-root>` using mode `<mode>`. If an `add` payload is provided, ingest those sources first: classify, normalize to summaries under `artifacts/`, and register them in `intake.index.md`, **referencing originals — never copy, move, or delete them**. Then process the registered sources: extract from the summaries, and produce/refresh the **module-centric living scope document** (`ba/scope.md`, conforming to the evolved, use-case-first Techjays Scope Document Template), the supporting registers, and the shared-context/ files. For every module that **forks by type/category/condition**, expand each materially-different route into its own **use case** (§3.x.4 — explanation, workflow, Mermaid flow diagram, worked example), draw the module **master flow** (§3.x.3) with branches mapping 1:1 to those use cases, and mirror each in `ba/registers/use-cases.md`.
>
> Two things must always happen:
> 1. **Raise every open item.** Surface all open questions, ambiguities, and assumptions as clarifications (`CLR`) / assumptions (`ASM`) / contradictions (`CON`), and (re)generate the clean, client-facing **`ba/client-questions.md`** deliverable from the open clarifications — grouped and prioritized so the team can take it straight to the client.
> 2. **Fold client answers back in (answer round-trip).** If any ingested source answers open questions (a filled-in `client-questions.md`, a client-answers doc, or meeting notes), match each answer to its open `CLR` id, record the answer and close it, apply the resulting edit to the relevant scope §3.x, log a decision (`DEC`) or assumption (`ASM`) as appropriate, and refresh `client-questions.md` so answered items drop off.
>
> Finish with a run summary. Honor all safety safeguards and never fabricate access to inaccessible sources.
>
> `add` payload (verbatim, or "none"): `<add text>`

## 3. Surface the result

When the agent returns, present its **run summary**: sources added/processed (new/changed/unchanged/inaccessible/reference-indexed), summaries generated, scope updates, **use cases identified/expanded this run** (with their module master flows), **open questions raised** and **questions answered/closed this run**, contradictions, assumptions, anything needing user guidance, and recommended next actions. Link to `ba/scope.md`, `ba/registers/use-cases.md`, the client-facing `ba/client-questions.md`, the run file under `ba/intake-runs/`, and `intake.index.md`.

### Review runs inside this command

The cycle has always been scope → review → resolve, and `/ba:resolve` itself recomputes the scores and writes the next round. There is no useful state where you have built a scope and not reviewed it — you would have no score, no verdict and no questions. So review runs here, every run.

**The score does not need the dashboard.** `overallScore` and `verdict` live in the review `.json`, so close with them in the summary:

```
Scope readiness: 8.7 / 10 — Significant gaps, clarify before estimate
Blockers: 1   Major: 5   Minor: 3
Thin on: Acceptance Criteria (3 modules) · Exception Handling (2)

Next:  /ba:resolve      answer the 4 questions marked answerable here
       send ba/open-questions.md to <the requirement's owner>
```

**Only name commands the user actually runs.** `/tl:plan` and `/dev:resolve` are invoked inside `/dev:plan` — the TL with no human pause, plan blockers in the conversation — so neither belongs in a next-steps list, not even as "don't run this yet". Naming them puts back the extra commands this whole flow exists to remove.

**State the constraint, not the command.** Where blockers must land before building, say which ones and why they matter:

> *CLR-021, CLR-022 and CLR-023 change the data model. Hold off building until they are answered — a plan written now would be written against a shape that is about to change.*

That tells the reader what is actually true. "Do not run `/tl:plan`" tells them about a command that was never theirs to run.

**Say what can start now.** Questions marked answerable here are not waiting on anyone — do not list them behind the ones that are.

**Write the `.md` and `.json` every run.** `/ba:resolve` matches rounds against the `.json`, so it is not optional.

**Generate the HTML only when it has a reader** — when questions are client-bound, because that is the packet you send, or when asked for it. A 62 KB dashboard produced on every incremental run that nobody opens is the cost this change removes.

`/ba:review` remains a command of its own, for a deliberate re-score without a scope pass.

> **Tip — the living-scope loop:** `/ba:scope add "…material…"` to build → hand `client-questions.md` to the client → `/ba:scope add "answers in <path>"` (or new notes) to fold responses in and close questions → repeat. For a scored critique of how estimate-ready the scope is, run `/ba:review`.
