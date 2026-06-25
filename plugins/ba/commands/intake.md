---
description: Run the Business Analyst discovery intake. Add sources in one line with `add "..."` (intake classifies, summarizes, and registers them — referencing originals, never copying), then builds the living scope document and registers. With no args it re-processes the registered sources incrementally.
argument-hint: "[add \"transcripts in <path/link>, requirements in <path/link>, ...\"] [mode=auto|incremental|full-refresh|dry-run|index-only|classify-only]"
---

# /ba:intake

You are the entry point for a Business Analyst intake run. Parse the arguments and **delegate the actual work to the `ba-agent` subagent**, which runs in its own context and does the file-heavy processing.

## 1. Parse arguments

`$ARGUMENTS` may contain, in any order:
- An optional **`add "<free text>"`** payload — a conversational declaration of where sources live, e.g. `add "meeting transcripts in D:\acme\meetings, requirements at <drive-link>, invoice archive in D:\acme\invoices for reference only"`. When present, the agent ingests these (classify → summarize → register in `intake.index.md`, referencing originals) **before** processing.
- An optional **`mode=…`** token (default `auto` if none given).

If `intake.index.md` doesn't exist yet, tell the user to run `/delivery-os:init <name>` first (or, if they clearly want to proceed, have the agent scaffold the minimal workspace). Then continue.

Mode table:

| Mode | Meaning |
|---|---|
| `auto` | Default. Classify sources, deep-analyze primary artifacts, safely index/skip large or reference artifacts. |
| `incremental` | Process only **new or changed** sources (compare against the hashes in the `intake.index.md` registry). |
| `full-refresh` | Rebuild scope from all eligible artifacts; back up previous `ba-output/` first. |
| `dry-run` | Report what *would* be ingested/processed and changed. **Write nothing.** |
| `index-only` | Register + classify sources in `intake.index.md` only; no summaries, no extraction. |
| `classify-only` | Classify sources and produce user guidance; no summaries, no analysis. |

If the token is unrecognized, tell the user the valid modes and stop.

## 2. Delegate

Invoke the **ba-agent** subagent with the project root, the resolved mode, and the `add` payload (if any). Pass it this instruction:

> Run a BA discovery intake in `<project-root>` using mode `<mode>`. If an `add` payload is provided, ingest those sources first: classify, normalize to summaries under `artifacts/`, and register them in `intake.index.md`, **referencing originals — never copy, move, or delete them**. Then process the registered sources: extract from the summaries, and produce/refresh the module-centric scope document (conforming to the Techjays Scope Document Template), the supporting registers, the shared-context files, and an intake run summary. Honor all safety safeguards and never fabricate access to inaccessible sources.
>
> `add` payload (verbatim, or "none"): `<add text>`

## 3. Surface the result

When the agent returns, present its **intake run summary**: sources added/processed (new/changed/unchanged/inaccessible/reference-indexed), summaries generated, scope updates, contradictions, clarifications added, anything needing user guidance, and recommended next actions. Link to the run file under `ba-output/intake-runs/` and to `intake.index.md`.
