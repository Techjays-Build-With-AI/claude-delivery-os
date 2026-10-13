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

### 1-pre. Is there already a scope here? (ask before the track, or not at all)

**Only when `ba/scope.md` exists.** On a first run there is nothing to ask — go straight to §1a.

Read the existing scope's cover block and §2 module list first, then **name what is there**. "A scope exists" is not something anyone can answer — they need to recognise it:

```
A scope already exists here:

  Shift-based timesheet · v0.4 · Reviewed · 6 modules · last run 2026-10-04
  Intake · Entry · Approval · Payroll Export · Exceptions · Admin

Is this new material for that scope, or a different requirement for this project?

  1 · New material — more transcripts, answers, or changes to the same requirement
  2 · A different requirement — clear the current work and start fresh
```

**1 · New material** is the living-scope loop and the normal case. Nothing is removed. Proceed to §1a.

**2 · A different requirement — clear, then build fresh.**

A workspace holds **one requirement's working state**. Two requirements in one `ba/` tree is not two scopes — it is one scope describing two unrelated things, with modules interleaved, registers mixed and a readiness score computed over the pair. Clearing is what makes a second requirement possible at all; without it every run piles onto the last.

| | |
|---|---|
| **Cleared** | `ba/` entirely — scope, registers, logs, reviews, `artifacts/`, `intake.index.md`, intake runs, the question files · and `features/` |
| **Kept** | `shared-context/` — glossary, stakeholder map, system landscape, decision log. Project-level truth that outlives any one requirement. |
| **Untouched** | `tasks/`, `context/`, `.jetrix/` — dev artifacts, code context and workspace binding are not BA state |

**`intake.index.md` goes with it, and that matters most.** Its source hashes are what `incremental` compares against. Leave it and the new requirement's sources are compared against the old one's — unchanged-looking files are skipped, and the run quietly ingests nothing while reporting success.

**State what is recoverable before clearing, then clear.** `ba/scope.md`, the registers, `clarifications.md`, `shared-context/` and `features/` are pushed to Jetrix, and `.jetrix/sync-state.json` records each one's `version` and `contentHash`. Read it, say what Jetrix holds, and say what is local-only — then do it. This is one line of information, not a confirmation step:

```
Clearing ba/ and features/ for a new requirement.

  In Jetrix (v3, matches local):  scope.md · 8 registers · clarifications · feature-index · 4 features
  Local only, going:              reviews (6 rounds) · artifacts (14) · intake.index · question files
  Kept:                           shared-context/

Cleared. Starting fresh.
```

**Flag only the case that is actually lossy:** `scope.md` or a register with **no `sync-state` entry**, or a `contentHash` that no longer matches. That means Jetrix does not hold what is about to be removed. Say which file and offer to push first — then clear either way if they say go. The user owns this decision; the command's job is to make sure it is not made blind.

### 1a. Which track is this? (ask once, before any extraction)

Read the input first — the `add` payload, the ticket, the file — **then propose a track with a reason.** Do not ask the user to classify work nobody has looked at yet, and do not ask anything about sources until the track is settled: what to ingest depends on the answer.

**Read the signal, do not guess it.** The material present tells you most of it:

| What is there | Reads as |
|---|---|
| Transcripts, meeting notes, client emails, an RFP | **client requirement** — client material means a client is the answerer |
| A requirement doc or ticket, and repos on disk, no client material | **task needing a BA plan**, or straight to `/dev:plan` — nobody external to question |
| A one-line ask, one repo, an existing surface | **straight to `/dev:plan`** |

**Never author source material.** Where a source is thin or missing, that is a question for the user or the client — never an offer to write one. Do not generate a transcript, a meeting note, an email or a brief, not as a sample, a mock or an illustration. A fabricated discovery call that "answers some of the brief's open points" closes real `CLR`s with invented answers, mints `DEC`s citing a conversation nobody had, and drops those questions from the client packet — so the gap stops being visible. One requirement document is a perfectly good scope input on its own; its open points are what `client-questions.md` exists to carry.

| | For | Code context | Produces |
|---|---|---|---|
| **Client requirement** | work a client signs off and someone estimates | no | scope · registers · client packet · review — the full pass |
| **Task needing a BA plan** | a module-sized internal piece: too big for one flat plan, no client to question | **yes — see §1b** | scope document + feature split |
| **Straight to `/dev:plan`** | one repo, understood well enough to build | resolved at plan time | nothing — hands off |

**Ask in these words. Never as "track A / B / C".** The letters are this file's shorthand for the three paths; they mean nothing to the person answering, who should be choosing *what the work is*, not decoding a label. Name each option by what it is, and say what each one produces — that is the information someone needs to pick.

**Offer all three, every time.** Even where one looks obviously right, the other two stay on screen. Dropping an option because it seems inapplicable is the command deciding for the user, and the third path — handing straight to `/dev:plan` — is the one most often wrongly omitted, because by then the run has already assumed a scope is being built.

```
This is a written client requirement from Novacore Solutions, with an external
client who answers the questions. I would take the first.

  1 · Client requirement       full scope, registers, client packet, review
  2 · Task needs a BA plan     internal, code-first; questions go to open-questions.md
  3 · Straight to /dev:plan    one repo, understood well enough to build
```

**Straight to `/dev:plan` hands off and stops.** Print the reason and the command — `/dev:plan <ref or "description">`, which takes a ticket, a plain `.md`, or a description. Do not build a scope for it.

**Two rules disqualify it**, both checkable rather than judgement:

- the work's surfaces span **more than one repo**
- it needs **more than ~3 features**

Either one and it needs a BA plan at least, whatever it looks like. A simple-looking change across two repos is not simple — it needs the split that only the feature path gives.

### 1b. Task needing a BA plan — start from the code

The reason this path exists is that full BA writes acceptance criteria blind, and the mismatch only surfaces at `/dev:plan`. Track B inverts that: resolve what exists **before** describing what to build.

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

**This path writes the registers its own downstream steps read.** `ba-feature-breakdown` walks `requirements`, `workflows`, `business-rules`, `data`, `integrations`, `use-cases`, `assumptions` to build each feature folder, and track B ends in a feature split — so omitting them starves the step this track exists to reach. Write the ones that have content. Skip only a register with nothing to put in it: `examples.md` is usually empty here, because client examples are what track A has and track B does not.

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

Invoke the **ba-agent** subagent with the project root, the resolved mode, the `add` payload (if any), **the track from §1a, and everything the user told you about this requirement in the conversation.**

**The subagent sees only what you pass it.** Nothing said in this chat reaches it, and neither does a track you chose and did not name — so a track B run delegated without its track silently behaves as track A, and the code-first work, the question routing and the omit rules never happen. Both blocks below are required, not optional context:

> **Track:** `client-requirement` | `task-ba-plan` | `direct-dev-plan` — the name, never a letter — and what it changes for this run. For **`task-ba-plan`**: read `context/code-context` for the area the requirement touches before writing; write the registers the feature breakdown reads; raise business questions to `ba/open-questions.md` for the requirement's owner, not `client-questions.md`; omit a §3.x dimension that does not apply; current state comes from the code, not a question.
>
> **What the user said:** everything they told you about this requirement in this conversation that is not already in the sources — corrections, constraints, who the requester is, what they have already decided, what they explicitly ruled out. Quote them. An instruction given in chat and not passed on is lost, and the agent will re-ask what the user already answered.

> Run a BA scope build/update in `<project-root>` using mode `<mode>` on track `<track>`. If an `add` payload is provided, ingest those sources first: classify, normalize to summaries under `artifacts/`, and register them in `intake.index.md`, **referencing originals — never copy, move, or delete them**. Then process the registered sources: extract from the summaries, and produce/refresh the **module-centric living scope document** (`ba/scope.md`, conforming to the evolved, use-case-first Techjays Scope Document Template), the supporting registers, and the shared-context/ files. For every module that **forks by type/category/condition**, expand each materially-different route into its own **use case** (§3.x.4 — explanation, workflow, Mermaid flow diagram, worked example), draw the module **master flow** (§3.x.3) with branches mapping 1:1 to those use cases, and mirror each in `ba/registers/use-cases.md`.
>
> Two things must always happen:
> 1. **Raise every open item.** Surface all open questions, ambiguities, and assumptions as clarifications (`CLR`) / assumptions (`ASM`) / contradictions (`CON`), and (re)generate the clean, client-facing **`ba/client-questions.md`** deliverable from the open clarifications — grouped and prioritized so the team can take it straight to the client.
> 2. **Fold client answers back in (answer round-trip).** If any ingested source answers open questions (a filled-in `client-questions.md`, a client-answers doc, or meeting notes), match each answer to its open `CLR` id, record the answer and close it, apply the resulting edit to the relevant scope §3.x, log a decision (`DEC`) or assumption (`ASM`) as appropriate, and refresh `client-questions.md` so answered items drop off.
>
> Finish with a run summary. Honor all safety safeguards and never fabricate access to inaccessible sources.
>
> `add` payload (verbatim, or "none"): `<add text>`

### Then review it — a second agent, same command

When the build agent returns, **invoke `ba-agent` again** for the review. The user typed one command and takes no second step; this is internal.

**A fresh agent, not the same one carrying on.** Two reasons, and both matter more as the requirement gets bigger:

- **Context.** The build agent is holding the ingestion history, every source it read and the scope it just wrote. Asking it to then read that whole scope back and score nine dimensions per feature is what makes the last modules get a thinner review than the first — silently, in a document that looks finished. The reviewer needs the scope and the registers, and nothing else.
- **Independence.** `ba-scope-review`'s premise is *judge, do not author*. An agent grading the scope it wrote in the same breath is grading the gaps it already decided to leave.

> Run a **scope review** of `ba/scope.md` in `<project-root>` using the `ba-scope-review` skill — act as a paranoid Business Analyst. You did not write this document; read it fresh. Load the scope knowledge base (the registers, `ba/logs/clarifications.md`, `shared-context/`), decompose it into features, interrogate each against the nine coverage dimensions, validate against the client's examples, screen every question through the question gate, score each feature and derive the scope-readiness verdict. Write `ba/reviews/scope-review-<timestamp>.md`, `.json` and `.html` — **all three, every run**. Return the executive summary and feature scorecard.
>
> **Track:** `client-requirement` | `task-ba-plan` — on **`task-ba-plan`** there is no client, so questions belong to the requirement's owner and "no examples" is not a finding against the scope.

**If the review fails or is skipped, say so.** A run that reports a scope with no score is a run where this step did not happen — do not print a readiness line you did not compute.

## 3. Surface the result

When the agent returns, present its **run summary**: sources added/processed (new/changed/unchanged/inaccessible/reference-indexed), summaries generated, scope updates, **use cases identified/expanded this run** (with their module master flows), **open questions raised** and **questions answered/closed this run**, contradictions, assumptions, anything needing user guidance, and recommended next actions. Link to `ba/scope.md`, `ba/registers/use-cases.md`, the client-facing `ba/client-questions.md`, the run file under `ba/intake-runs/`, and `intake.index.md`.

**Lead with the understanding brief.** Print §0 *What We Understand This To Be* in the summary itself, not as a link. It is the cheapest correction point in the engagement, and it only works if it is read — a reader who disagrees with it disagrees in two minutes, while the same disagreement found at §3.7 costs a rewrite. Everything else in the summary is downstream of it being right.

**Then the two coverage counts**, in one line each: sources that contributed nothing, and scope lines carrying no source. The second should be zero; if it is not, name the lines, because each one is something nobody said.

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

**Write all three every run — `.md`, `.json` and `.html`.** The dashboard is how a team reads the questions without being handed a markdown file, and on an internal run it is how someone who was not in the resolve conversation catches up. The score does not depend on it — that comes from the `.json` and the summary above — but the questions are easier to read there than anywhere else, so it is not conditional.

`/ba:review` remains a command of its own, for a deliberate re-score without a scope pass.

> **Tip — the living-scope loop:** `/ba:scope add "…material…"` to build → hand `client-questions.md` to the client → `/ba:scope add "answers in <path>"` (or new notes) to fold responses in and close questions → repeat. For a scored critique of how estimate-ready the scope is, run `/ba:review`.
