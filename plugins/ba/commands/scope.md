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
| `full-refresh` | Rebuild scope from all eligible artifacts; back up previous `ba-output/` first. |
| `dry-run` | Report what *would* be ingested/processed and changed. **Write nothing.** |
| `index-only` | Register + classify sources in `intake.index.md` only; no summaries, no extraction. |
| `classify-only` | Classify sources and produce user guidance; no summaries, no analysis. |

If the token is unrecognized, tell the user the valid modes and stop.

## 2. Delegate

Invoke the **ba-agent** subagent with the project root, the resolved mode, and the `add` payload (if any). Pass it this instruction:

> Run a BA scope build/update in `<project-root>` using mode `<mode>`. If an `add` payload is provided, ingest those sources first: classify, normalize to summaries under `artifacts/`, and register them in `intake.index.md`, **referencing originals — never copy, move, or delete them**. Then process the registered sources: extract from the summaries, and produce/refresh the **module-centric living scope document** (`ba-output/scope.md`, conforming to the evolved, use-case-first Techjays Scope Document Template), the supporting registers, and the shared-context files. For every module that **forks by type/category/condition**, expand each materially-different route into its own **use case** (§3.x.4 — explanation, workflow, Mermaid flow diagram, worked example), draw the module **master flow** (§3.x.3) with branches mapping 1:1 to those use cases, and mirror each in `use-case-register.md`.
>
> Two things must always happen:
> 1. **Raise every open item.** Surface all open questions, ambiguities, and assumptions as clarifications (`CLR`) / assumptions (`ASM`) / contradictions (`CON`), and (re)generate the clean, client-facing **`ba-output/client-questions.md`** deliverable from the open clarifications — grouped and prioritized so the team can take it straight to the client.
> 2. **Fold client answers back in (answer round-trip).** If any ingested source answers open questions (a filled-in `client-questions.md`, a client-answers doc, or meeting notes), match each answer to its open `CLR` id, record the answer and close it, apply the resulting edit to the relevant scope §3.x, log a decision (`DEC`) or assumption (`ASM`) as appropriate, and refresh `client-questions.md` so answered items drop off.
>
> Finish with a run summary. Honor all safety safeguards and never fabricate access to inaccessible sources.
>
> `add` payload (verbatim, or "none"): `<add text>`

## 3. Surface the result

When the agent returns, present its **run summary**: sources added/processed (new/changed/unchanged/inaccessible/reference-indexed), summaries generated, scope updates, **use cases identified/expanded this run** (with their module master flows), **open questions raised** and **questions answered/closed this run**, contradictions, assumptions, anything needing user guidance, and recommended next actions. Link to `ba-output/scope.md`, `ba-output/use-case-register.md`, the client-facing `ba-output/client-questions.md`, the run file under `ba-output/intake-runs/`, and `intake.index.md`.

> **Tip — the living-scope loop:** `/ba:scope add "…material…"` to build → hand `client-questions.md` to the client → `/ba:scope add "answers in <path>"` (or new notes) to fold responses in and close questions → repeat. For a scored critique of how estimate-ready the scope is, run `/ba:review`.
