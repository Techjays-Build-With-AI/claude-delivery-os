---
description: Build and continuously update the living project scope from client material. Point it at folders/Google Drive with `add "..."` (it references originals, classifies, and summarizes them), and it maps everything out, writes the module-centric scope document in the Techjays template, and raises every open question and assumption as a clean "questions for the client" deliverable. Feed back a client-answers doc or new meeting notes and it folds them in, closes the answered questions, and updates the living scope. With no args it re-processes registered sources incrementally.
argument-hint: "[add \"transcripts in <path/link>, requirements in <path/link>, answers in <path>, ...\"] [mode=auto|incremental|full-refresh|dry-run|index-only|classify-only]"
---

# /ba:scope

You are the entry point for building and maintaining the project's **living scope document**. Parse the arguments and **delegate the actual work to the `ba-agent` subagent**, which runs in its own context and does the file-heavy processing.

The mental model: **one living scope document** that is created from the first batch of client material and then **kept up to date** as new meeting notes, documents, examples, or client answers arrive. Every run also surfaces the open questions and assumptions the team needs to take to the client, and folds their answers back in when they return.

## 1. Parse arguments

`$ARGUMENTS` may contain, in any order:
- An optional **`add "<free text>"`** payload — a conversational declaration of where sources live, e.g. `add "meeting transcripts in D:\acme\meetings, requirements at <drive-link>, invoice archive in D:\acme\invoices for reference only"`. Sources can be **local folders/files or Google Drive links**. When present, the agent ingests these (classify → summarize → register in `sources.md`, referencing originals) **before** processing.
  - The same `add` mechanism is how you feed material **back in**: point it at the questions document the client returned, a client-answers document, or a fresh set of discovery/meeting notes, and the agent folds them into the living scope (see "answer round-trip" below).
- An optional **`mode=…`** token (default `auto` if none given).

If `sources.md` doesn't exist yet, tell the user to run `/delivery-os:init <name>` first (or, if they clearly want to proceed, have the agent scaffold the minimal workspace). Then continue.

Mode table:

| Mode | Meaning |
|---|---|
| `auto` | Default. Classify sources, deep-analyze primary artifacts, safely index/skip large or reference artifacts, and update the scope. |
| `incremental` | Process only **new or changed** sources (compare against the hashes in the `sources.md` registry). The normal mode for an ongoing project. |
| `full-refresh` | Rebuild scope from all eligible artifacts; back up previous `ba/` first. |
| `dry-run` | Report what *would* be ingested/processed and changed. **Write nothing.** |
| `index-only` | Register + classify sources in `sources.md` only; no summaries, no extraction. |
| `classify-only` | Classify sources and produce user guidance; no summaries, no analysis. |

If the token is unrecognized, tell the user the valid modes and stop.

## 2. Read what already exists — only if it does

**First, make `shared-context/` current.** These six files are project-level and every requirement writes into
them, so scoping against a stale or absent copy is how the previous requirement's terms get dropped. Where the
workspace is bound to Jetrix and `shared-context/` is missing or older than the bucket, run
`/jetrix:pull scope` for it before extracting. Not on Jetrix, or nothing pushed yet → carry on; this adds a
source, it is never a prerequisite.

It also arms the version lock: the push sends `expected_version` from sync-state, and sync-state only knows a
version for a file that was pulled. Writing a file you never pulled means the push carries nothing to compare,
so it overwrites the server copy instead of being told to merge.

**The gate, first.** Read `.jetrix/code-map-registry.md`:

| What you find | What happens |
|---|---|
| **Mapped repos** | read the graph (below), then scope as a change to a working system |
| **No registry** | greenfield. **Skip the rest of this step** and scope exactly as before |
| **Repos linked, none mapped** | skip it too, and say so: *"2 repos linked but not mapped — run `/tl:code-map` for a scope that accounts for what exists"* |

**Nothing about the existing flow changes when there is no code context.** This step adds a source when one is
available; it never becomes a prerequisite. A greenfield run reads the client material and nothing else, which
is what it did before. **Never guess at existing behaviour from a repo name** — absence of a graph is absence
of knowledge, not permission to assume.

---

With mapped repos, pass the agent the **`tl-read-code-context`** skill along with the registry. It is
index-first: root index → layer index → the one unit file, never a grep across source, so reading the graph
costs a handful of files rather than a repository. It also **refuses to fabricate** — where the graph does not
cover an area it says so and points at `/tl:code-map`, which is what makes it safe here.

**Read `.jetrix/connection-map.md` too, where it exists.** The two artefacts answer different questions and
the scope needs both (`delivery-os-conventions`):

| Question | Where |
|---|---|
| What does *this repo* contain — which pages, endpoints, entities? | `<repo>/context/code-context/` |
| **Which apps exist, how do they talk, where is auth, what is already integrated?** | `.jetrix/connection-map.md` |

**Its `## External integrations` section settles a whole class of client question.** "It should sync with
payroll" is a different scope item depending on whether payroll is already wired; `None declared` is an
answer, not a gap in our knowledge. Same for `## Apps`: a client who does not know a mobile app exists is
told, rather than the question going to the ledger.

Cite it the same way as the graph — by what it says, never copied in — and raise a `CON` row where the client
material and the map disagree about what is connected to what.

**The code context is not a source, and must never be registered as one.** It does not go in `sources.md`,
it gets no `SRC-###`, and **nothing is written to `artifacts/code-context/`** — that folder should not exist.

| | |
|---|---|
| Where it lives | `<repo>/context/code-context/`, committed with the code |
| How it is found | `.jetrix/code-map-registry.md` — **one pointer, project-wide** |
| How it is read | live, index-first, via `tl-read-code-context` |
| What is kept per requirement | the unit **ids** you cited (`EP-`/`PAGE-`/`ENT-`) inside the scope and the `CON` rows |

**Only the requirement changes between runs; the graph does not.** Summarising it into each requirement
produces one stale copy per requirement per repo, all of them wrong the moment `/tl:code-map` re-runs on a
new commit — and the registry records `mapped_from_commit` precisely so staleness is detectable, which a
loose summary in `artifacts/` defeats.

It also throws away the reason the read protocol exists: three cheap reads against the live graph, not a
paraphrase written weeks ago by a different run.

**`sources.md` is for client material** — transcripts, requirement documents, answer files, anything the
client produced. A derived artifact of our own that carries no content hash is the tell: a row whose hash
column reads *"n/a (derived, committed in repo)"* should never have been a row.

**Cite the graph, do not copy it.** Where the scope leans on current behaviour, name the unit id and the
commit the registry records. A reader who needs the detail opens the unit file, which is current by
construction.

What it changes:

- **A requirement about something that exists is written as a change, not an invention.** "Technicians log
  hours" against a repo with a timesheet module is a modification with a current state, and the scope's
  current→future column is the thing that makes it estimable.
- **Questions the code already answers are never asked.** This is where it pays most: the client is asked
  "which authentication method?" about a repo that has had SSO for two years. Those questions cost
  credibility — and `/ba:review`'s question screen searches the graph for the same reason before any question
  ships.
- **A contradiction between the client and the code is a `CON` row**, not a silent choice. "The brief says
  offline-first; `EP-SYNC-02` validates server-side before save" is a decision someone has to make, and it is
  invisible to a BA reading only the brief.

**Cite the unit, never the file.** `EP-SUP-02`, `PAGE-TIME-01`, `ENT-USR-03` — those ids are stable and
reviewable. A line number is neither.

**As-built is evidence of what is, never of what should be.** A client may change anything their system
currently does; the graph tells you the starting point, not the destination.

## 3. Delegate

Invoke the **ba-agent** subagent with the project root, the resolved mode, and the `add` payload (if any). Pass it this instruction:

> Run a BA scope build/update in `<project-root>` using mode `<mode>`. **Where §2 found mapped repos, read the code context first via the `tl-read-code-context` skill, and read `.jetrix/connection-map.md` where it exists** (which apps exist, how they talk, where auth sits, what is already integrated — its `## External integrations` section answers integration questions outright rather than sending them to the ledger) and treat every affected area as a change to a working system: record its current state, cite the unit ids you relied on (`EP-`/`PAGE-`/`ENT-`), and raise a `CON` row wherever the client material and the code disagree rather than silently preferring either. If an `add` payload is provided, ingest those sources first: classify, normalize to summaries under `artifacts/`, and register them in `sources.md`, **referencing originals — never copy, move, or delete them**. **The code context is not one of them**: never give it an `SRC-###`, never summarise it into `artifacts/`. Read it live through the registry and cite unit ids in the scope instead — §2. Then process the registered sources: extract from the summaries, and produce/refresh the **module-centric living scope document** (`requirements/<slug>/scope.md`, conforming to the evolved, use-case-first Techjays Scope Document Template), the supporting registers, and the shared-context/ files. For every module that **forks by type/category/condition**, expand each materially-different route into its own **use case** (§3.x.4 — explanation, workflow, Mermaid flow diagram, worked example), draw the module **master flow** (§3.x.3) with branches mapping 1:1 to those use cases, and mirror each in `requirements/<slug>/registers/use-cases.md`.
>
> Two things must always happen:
> 1. **Raise every open item.** Surface all open questions, ambiguities, and assumptions as clarifications (`CLR`) / assumptions (`ASM`) / contradictions (`CON`), and (re)generate the clean, client-facing **the review report’s **Client questions** tab** deliverable from the open clarifications — grouped and prioritized so the team can take it straight to the client.
> 2. **Fold client answers back in (answer round-trip).** If any ingested source answers open questions (the returned questions document, a client-answers doc, or meeting notes), match each answer to its open `CLR` id, record the answer and close it, apply the resulting edit to the relevant scope §3.x, log a decision (`DEC`) or assumption (`ASM`) as appropriate, and refresh `client-questions.md` so answered items drop off.
>
> Do **not** hand-write `requirements/<slug>/scope.html` — §3 of this command renders it with the bundled script once you return. Make sure `requirements/<slug>/scope.md` carries its `Requirement` / `Version` / `Status` / `Updated` front matter, because that is what the page header reads. Finish with a run summary. Honor all safety safeguards and never fabricate access to inaccessible sources.
>
> `add` payload (verbatim, or "none"): `<add text>`

## 4. Render and publish the scope

Every run that changed `requirements/<slug>/scope.md` ends by rendering `requirements/<slug>/scope.html` and publishing it to the project's **Dashboard → Reports**, so the team and the client read the scope in a browser instead of a markdown file.

**Render — one command, never by hand.**

```bash
node ${CLAUDE_PLUGIN_ROOT}/skills/ba-extraction/assets/render-scope.js \
  .jetrix/requirements/<slug>/scope.md \
  --features .jetrix/requirements/<slug>/features \
  --review   .jetrix/requirements/<slug>/reviews/<newest>.json
```

It converts the markdown at build time, so the page ships as plain HTML with no
client-side renderer and no CDN — it opens from a double-click, a share link and
a printer identically. The header reads the front matter (requirement, version,
`Draft / In Review / Approved`, updated) and `--review` adds the readiness score
when a review has run.

`--sources` renders a **Source coverage** block — what contributed, what did not, and what could not be
read. Useful on an internal copy; **not passed on the published render**, because it is QA on our own
extraction and a client has no use for it. The same facts reach the run summary, where they are for us.

`--features` renders the roll-up, read from each `features/<slug>/status.md` at render time. It replaces
`feature-index.md`, which cached the same two facts and went stale the moment one feature moved.

All four flags are **passed when the file exists and omitted when it does not** — the script treats a missing one as "no score" / "no questions section" rather than failing, so a first run before any review still renders.

**Pass no other flags.** `scope.html` is the document the client reads, and three things that belong to us must not appear in it:

| Not in the client render | Where it lives instead |
|---|---|
| **Open questions** (`--ledger`) | `/ba:review`’s report, which has a tab for answering them in place |
| **Source coverage** (`--sources`) | the run summary — it is QA on our own extraction |
| **Internal ids** (`CLR-`, `CON-`, `UC-`, `EP-`, `PAGE-`, `ENT-`, `ASM-`…) | `scope.md` and the registers, untouched. The renderer strips them from the page automatically |

A client handed thirty-four unanswered questions and a trail of `CON-002` references is reading our filing system, not a scope. The flags still exist for an internal copy; the published render does not use them.

**Mermaid blocks render as real flow diagrams**, drawn to inline SVG. No CDN and no library, so the page stays self-contained — a client opens it offline and still sees the flows. Internal ids are dropped from the node labels too, so `ROLE-UC-01: Assign roles` reads as `Assign roles`. A diagram the renderer cannot model falls back to labelled source rather than breaking the page.

**Publish — replace, never add.**

```
hash requirements/<slug>/scope.html  →  same as sync-state's
                                           reports["<slug>"].scope.content_hash?
   yes → skip the upload entirely; the link is unchanged
   no  → first publish  : scope_prepare_report_push → curl PUT → scope_finalize_report_push
                          → scope_share_report          ← without this the link does not work
         already live   : scope_finalize_report_push with the stored attachment_id (replace)
                          — and NOT scope_share_report again
```

**`scope_share_report` is not optional, and it is first-publish only.** Finalize creates the attachment;
it does not share it. Skip the share and Jetrix serves the client *"This report is not available for
sharing yet"* — the report is there, it simply was never shared.

Call it with `public: false`. That returns the link **and a 4-digit passcode**, with access rate-limited on
Jetrix's side — the right default for a scope going to a named client contact rather than anyone who ends up
with the URL.

**Never call it on a re-publish.** Mission Control mints a *new* passcode every time and overwrites the old
one, so a second call silently breaks the code the client already has — on round 2, with no error on either
side. Replace keeps the attachment, and the passcode with it.

Record `attachment_id`, `share_url`, **`passcode`**, `content_hash` and `published_at` under
`reports["<requirement-slug>"].scope`. Storing the passcode is what lets a later round reprint it without
regenerating; it is a 4-digit access code on a document the client is already being sent, held in a
gitignored workspace file, not a credential.

These all live under **`reports["<requirement-slug>"].scope`** in `.jetrix/cache/sync-state.json`.

**Also write `report_url` into `scope.md`’s frontmatter**, so the document itself records where it is
published. sync-state is a cache — cleared, rebuilt, and nobody opens it; the scope is the thing people
actually have in front of them, and a round later "where did we send this?" has an answer in the file rather
than in someone’s chat history. **The passcode stays out of it** and lives only in sync-state: the markdown
is the artifact people copy around, and an access code does not belong in something that gets pasted into a
ticket.

On a re-publish the URL is unchanged, so this is a no-op after the first run.

**The key is per requirement, and that is not cosmetic.** A workspace holds many requirements and each publishes
its own `scope.html`. Keyed on a shared `reports.scope`, the second requirement's publish would find the first
one's `attachment_id` and **replace that report in place** — a client who bookmarked the timesheet scope opens it
and is served the payroll one, at the same URL, with nothing to indicate the swap.

**Within a requirement, the `attachment_id` is what keeps the link stable** — replace in place and a client who
bookmarked round 1 sees round 4 at the same URL. Upload a new file instead and the Reports tab fills with
`scope.html`, `scope (1).html`, `scope (2).html`, each with a different link.

**Publishing is Jetrix-only.** `capabilities.documents` in `project.json` decides it: `scope-mcp` publishes, `none` does not. On any other tracker — or when the report tools aren't registered — print the local path and the serve line and carry on. Never fail the run over it:

```
Report   http://127.0.0.1:<port>/scope.html      ← open in your browser
         requirements/<slug>/scope.html        ← the file itself
         (local only — this tracker has no report host)
```

The serve line matters locally: `file://` blocks a page fetching its own siblings, which the hosted copy never hits.

## 5. Surface the result

**The block below is the whole output.** Not a lead-in to it, not a summary before it — the entire thing
the run prints. Counts, questions, contradictions and assumptions all live in files that are one click away
and stay correct; repeating them here produces a wall nobody reads, and buries the one line that needed
somebody.

| Print | Do not print |
|---|---|
| §0 "What we understand this to be", in full | a module table — it is in the report |
| One counts line | per-register breakdowns, use-case lists |
| **Only decisions that block the next step** | all 34 open questions, all 6 contradictions, all 13 assumptions |
| The links | a files list — the report links to them |

**Fifteen lines, excluding §0.** If it runs longer, something in it belongs in a file.

**The one exception is a decision the user must make before `/ba:review` is worth running** — a date that
cannot be right, a source that never arrived, two branches that disagree about something fundamental. One
line each, three at most, under `Needs you`. Everything else is a question for the client and belongs in the
ledger, which is exactly what the next step is for.

**Close in this shape** — every link and command copy-pasteable, never described in prose:

```
✓ Scope built — 9 modules · 28 use cases · 3 sources · 34 questions for the client

What we understand this to be
  <§0 of the scope, printed in full — the cheapest correction point in the
   engagement, and it only works if it is read>

⚠ Needs you
  1. The JetBrains renewal reads January 2026, which is before the call.
     1 Jan 2027 assumed — confirm or fix the transcript.
  2. Karthik's asset spreadsheet never arrived; 210 rows is an assumption.

Report
  http://127.0.0.1:<port>/scope.html                  ← open in your browser
  https://app.jetrix.ai/reports/shared/6b91a4c8       ← send this to the client
                                       passcode 4417  ← and this, separately
  requirements/<slug>/scope.html                      ← the file itself

Next:
  /ba:review      score it and raise the questions
```

Drop `⚠ Needs you` entirely when nothing qualifies. An empty heading reads as a problem that was not
explained.

**Serve it as the last action of the run — `delivery-os-conventions` §1.e.** Start the server in the
background and read the port from its `DELIVERY_OS_SERVE_READY` line; never print the command and leave the user
to run it, and never assume port 4100.

```bash
node ${CLAUDE_PLUGIN_ROOT}/../delivery-os-core/scripts/serve-review.js .jetrix/requirements/<slug>
```

Print **all three lines on Jetrix**: the local URL for whoever wants to look now, the share URL for whoever is
being sent it, and the path for whoever wants to find it again tomorrow. Off Jetrix, drop the share URL and keep
the other two.

On a re-run where the scope did not move, the report line reads `unchanged this run` and keeps the same URL.

**Never print a readiness score here.** `/ba:scope` does not compute one — `/ba:review` does. A run that prints a verdict it never calculated is the bug this split exists to prevent.

> **Tip — the living-scope loop:** `/ba:scope add "…material…"` to build → hand the client the report link, or the **Client questions** tab exported as a document → `/ba:scope add "answers in <path>"` (or new notes) to fold responses in and close questions → repeat. The report link stays the same every round, so it can be sent once. For a scored critique of how estimate-ready the scope is, run `/ba:review`.
