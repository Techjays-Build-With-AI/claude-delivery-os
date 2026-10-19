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

## 2. Delegate

Invoke the **ba-agent** subagent with the project root, the resolved mode, and the `add` payload (if any). Pass it this instruction:

> Run a BA scope build/update in `<project-root>` using mode `<mode>`. If an `add` payload is provided, ingest those sources first: classify, normalize to summaries under `artifacts/`, and register them in `intake.index.md`, **referencing originals — never copy, move, or delete them**. Then process the registered sources: extract from the summaries, and produce/refresh the **module-centric living scope document** (`ba/scope.md`, conforming to the evolved, use-case-first Techjays Scope Document Template), the supporting registers, and the shared-context/ files. For every module that **forks by type/category/condition**, expand each materially-different route into its own **use case** (§3.x.4 — explanation, workflow, Mermaid flow diagram, worked example), draw the module **master flow** (§3.x.3) with branches mapping 1:1 to those use cases, and mirror each in `ba/registers/use-cases.md`.
>
> Two things must always happen:
> 1. **Raise every open item.** Surface all open questions, ambiguities, and assumptions as clarifications (`CLR`) / assumptions (`ASM`) / contradictions (`CON`), and (re)generate the clean, client-facing **`ba/client-questions.md`** deliverable from the open clarifications — grouped and prioritized so the team can take it straight to the client.
> 2. **Fold client answers back in (answer round-trip).** If any ingested source answers open questions (a filled-in `client-questions.md`, a client-answers doc, or meeting notes), match each answer to its open `CLR` id, record the answer and close it, apply the resulting edit to the relevant scope §3.x, log a decision (`DEC`) or assumption (`ASM`) as appropriate, and refresh `client-questions.md` so answered items drop off.
>
> Do **not** hand-write `ba/scope.html` — §3 of this command renders it with the bundled script once you return. Make sure `ba/scope.md` carries its `Requirement` / `Version` / `Status` / `Updated` front matter, because that is what the page header reads. Finish with a run summary. Honor all safety safeguards and never fabricate access to inaccessible sources.
>
> `add` payload (verbatim, or "none"): `<add text>`

## 3. Render and publish the scope

Every run that changed `ba/scope.md` ends by rendering `ba/scope.html` and publishing it to the project's **Dashboard → Reports**, so the team and the client read the scope in a browser instead of a markdown file.

**Render — one command, never by hand.**

```bash
node ${CLAUDE_PLUGIN_ROOT}/skills/ba-extraction/assets/render-scope.js .jetrix/ba/scope.md \
  --questions .jetrix/ba/client-questions.md \
  --review    .jetrix/ba/reviews/<newest>.json
```

It converts the markdown at build time, so the page ships as plain HTML with no
client-side renderer and no CDN — it opens from a double-click, a share link and
a printer identically. The header reads the front matter (requirement, version,
`Draft / In Review / Approved`, updated) and `--review` adds the readiness score
when a review has run.

Both optional flags are **passed when the file exists and omitted when it does not** — the script treats a missing one as "no score" / "no questions section" rather than failing, so a first run before any review still renders.

`--questions` is what turns `client-questions.md` from a path into a link: the open questions become a section of the page the client is already being sent, instead of a second file to find. **Mermaid blocks render as labelled source, not as diagrams** — drawing them would mean pulling a library off a CDN, and a scope that only works online is not self-contained.

**Publish — replace, never add.**

```
hash ba/scope.html  →  same as sync-state's reports.scope.content_hash?
   yes → skip the upload entirely; the link is unchanged
   no  → first publish  : scope_prepare_report_push → curl PUT → scope_finalize_report_push
         already live   : scope_finalize_report_push with the stored attachment_id (replace)
```

Record `attachment_id`, `share_url`, `content_hash` and `published_at` under `reports.scope` in `.jetrix/cache/sync-state.json`. **The `attachment_id` is what keeps the link stable** — replace it in place and a client who bookmarked round 1 sees round 4 at the same URL. Upload a new file instead and the Reports tab fills with `scope.html`, `scope (1).html`, `scope (2).html`.

**Publishing is Jetrix-only.** `capabilities.documents` in `project.json` decides it: `scope-mcp` publishes, `none` does not. On any other tracker — or when the report tools aren't registered — print the local path and the serve line and carry on. Never fail the run over it:

```
Report   local only — this tracker has no report host
         ba/scope.html
         npx serve .jetrix/ba   →   http://localhost:3000/scope.html
```

The serve line matters locally: `file://` blocks a page fetching its own siblings, which the hosted copy never hits.

## 4. Surface the result

When the agent returns, present its **run summary**: sources added/processed (new/changed/unchanged/inaccessible/reference-indexed), summaries generated, scope updates, **use cases identified/expanded this run** (with their module master flows), **open questions raised** and **questions answered/closed this run**, contradictions, assumptions, anything needing user guidance. Link to `ba/registers/use-cases.md`, the client-facing `ba/client-questions.md`, the run file under `ba/intake-runs/`, and `intake.index.md`.

**Close with the link and the next step, in this shape** — both copy-pasteable, never described in prose:

```
✓ Scope built — 6 modules · 34 use cases · 8 sources

What we understand this to be
  <§0 of the scope, printed in full — the cheapest correction point in the
   engagement, and it only works if it is read>

Source coverage
  7 of 8 contributed · scope lines with no source: 0

Report
  https://app.jetrix.ai/reports/shared/6b91a4c8
  ba/scope.html
  npx serve .jetrix/ba   →   http://localhost:3000/scope.html

Next:
  /ba:review      score it and raise the questions
```

Print **all three** lines on Jetrix — the URL for whoever is being sent it, the local path and the serve line for whoever is running the command. Off Jetrix, drop the URL and keep the other two.

On a re-run where the scope did not move, the report line reads `unchanged this run` and keeps the same URL.

**Never print a readiness score here.** `/ba:scope` does not compute one — `/ba:review` does. A run that prints a verdict it never calculated is the bug this split exists to prevent.

> **Tip — the living-scope loop:** `/ba:scope add "…material…"` to build → hand the report link or `client-questions.md` to the client → `/ba:scope add "answers in <path>"` (or new notes) to fold responses in and close questions → repeat. The report link stays the same every round, so it can be sent once. For a scored critique of how estimate-ready the scope is, run `/ba:review`.
