---
description: Run the Business Analyst discovery intake. Scans the artifact sources declared in intake.index.md, classifies them safely, processes eligible discovery artifacts, and updates the living scope document and supporting registers. Supports incremental re-runs as new artifacts arrive.
argument-hint: "[mode=auto|incremental|full-refresh|dry-run|index-only|classify-only]"
---

# /ba:intake

You are the entry point for a Business Analyst intake run. Your job is to parse the requested mode and **delegate the actual work to the `ba-agent` subagent**, which runs in its own context and does the file-heavy processing.

## 1. Parse the mode

Read `$ARGUMENTS` for a `mode=…` token. Default to `auto` if none is given.

| Mode | Meaning |
|---|---|
| `auto` | Default. Classify sources, deep-analyze primary artifacts, safely index/skip large or reference artifacts. |
| `incremental` | Process only **new or changed** eligible artifacts (compare against `ba-output/artifact-ledger.md`). |
| `full-refresh` | Rebuild scope from all eligible artifacts; back up previous `ba-output/` first. |
| `dry-run` | Report what *would* be processed and changed. **Write nothing.** |
| `index-only` | Scan folders; update `artifact-map.md` and `artifact-ledger.md` only. |
| `classify-only` | Classify sources and produce user guidance; do not analyze content. |

If the token is unrecognized, tell the user the valid modes and stop.

## 2. Preconditions

- Confirm `intake.index.md` exists in the current project. If not, tell the user to run `/delivery-os:init` first, then stop.
- Confirm the `delivery-os` (core) plugin's contract is available — the agent must follow `delivery-os-conventions`.

## 3. Delegate

Invoke the **ba-agent** subagent with the resolved mode and the project root. Pass it this instruction:

> Run a BA discovery intake in `<project-root>` using mode `<mode>`. Follow the delivery-os-conventions contract and your intake processing flow. Produce/refresh the scope document, supporting registers, shared-context files, and an intake run summary. Honor all safety safeguards and never fabricate access to inaccessible sources.

## 4. Surface the result

When the agent returns, present its **intake run summary** to the user: artifacts scanned (new/changed/unchanged/inaccessible/indexed), sources processed, scope updates, contradictions, clarifications added, anything needing user guidance, and recommended next actions. Link to the run file under `ba-output/intake-runs/`.
