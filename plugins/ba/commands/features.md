---
description: Break a requirement's scope into an implementation-ready feature breakdown. The BA agent decomposes it into independently understandable features and writes a folder per feature (feature.md, acceptance-criteria.md, business-rules.md, nfrs.md, test-scenarios.md, dependencies.md, status.md) under requirements/<slug>/features/. Then pushes every feature to the bound tracker (Jetrix, Jira, ClickUp — whatever `/jetrix:init` bound) and prints each one's link. It marks assumptions and open questions instead of inventing requirements, preserves traceability to the scope, and updates existing feature folders in place on re-runs — the push is idempotent, so a re-run updates the same tickets.
argument-hint: "[<path-to-scope-doc>] [requirement=<slug>] [out=<output-dir>]"
---

# /ba:features

You are the entry point for building an **implementation-ready feature breakdown** from the scope. Parse the arguments and **delegate the actual work to the `ba-agent` subagent**, which runs in its own context and does the scope-heavy reading, decomposition, and folder authoring.

The mental model: the scope says *what the business wants*; this command turns it into the *implementation context* a build team needs — one folder per feature, each self-contained, with the pages/APIs/workflows/data/integrations it implies, its dependencies, and every remaining unknown captured as an open question rather than a guessed requirement.

## 1. Parse arguments

`$ARGUMENTS` may contain:
- An optional **`requirement=<slug>`** — which requirement to break down. Resolved by `delivery-os-conventions` §1.d: one requirement is used silently, several without a pick are asked for by name, and an unknown slug stops with the real list.
- An optional **scope document reference** — a path to a `.md` / `.docx` / `.pdf` scope, or a link, for a scope that lives outside a workspace. Inside one, the requirement decides the path and this is not needed.
- An optional **`out=<dir>`** — overrides the output location. The default is `requirements/<slug>/features/`, and there is rarely a reason to move it.

**No requirements exist yet** → stop and point at `/ba:scope add "…"`. This command breaks down a scope; it does not create one.

## 2. Delegate

Invoke the **ba-agent** subagent with the scope reference and output directory. Pass it this instruction:

> Run a **feature breakdown** of `requirements/<slug>/scope.md` using the `ba-feature-breakdown` skill. Stamp every feature with `requirement: <slug>` in `feature.md` and `status.md` frontmatter — the folder already says it, and the frontmatter is what survives a push to the tracker and a pull back. Read the whole scope first, then load the supporting context when a workspace exists (`requirements/<slug>/registers/requirements.md`, `requirements/<slug>/registers/workflows.md`, `requirements/<slug>/registers/business-rules.md`, `shared-context/data.md`, `shared-context/integrations.md`, `requirements/<slug>/registers/examples.md`, `requirements/<slug>/ledger.md` (kind: assumption), `requirements/<slug>/ledger.md` (kind: question), `requirements/<slug>/ledger.md` (kind: contradiction), `shared-context/`). Identify the major business capabilities, then decompose them into independently understandable features sized to plan/build/test/release — not so broad they can't be estimated, not so small they carry no business value (a button, one endpoint, a migration go *inside* a feature, not as one). For each feature, create `requirements/<slug>/features/<feature-slug>/` (lowercase kebab-case) and write the seven files from `references/feature-file-templates.md`: `feature.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `status.md`. **The workflow goes inside `feature.md` and open questions inside `dependencies.md`** — the push folds them in anyway, so keeping them apart means composing the same merge twice. There is no `implementation-plan.md`: it was a BA scratchpad one character from `/dev:plan`'s `implementation.md`, which is a different file with a different owner. Identify the expected pages, APIs, workflows, integrations, background jobs, events, and data entities — but only as far as the scope supports; **never fabricate** product/UI behaviour, business rules, API contracts, schemas, or integrations. Mark every uncertainty with the controlled labels (Confirmed / Assumption / Open Question / Dependency / Risk / Out of Scope / Future Phase), reusing `CLR-###` ids for already-logged questions and minting `OQ-<AREA>-NN` for new ones. Wire cross-feature dependencies into both features and the index. Give every feature a stable `FEAT-<AREA>-NN` id and Source References back to the scope §/register ids — no scope item may be silently dropped. **Do not write a the breakdown table in the run summary.** `ls` is the list and status lives in each `status.md`; a cached aggregation only goes stale. The index renders into `scope.html` instead. Return the table in your summary so the run prints it. On a re-run, update folders in place and preserve history, clearly noting what changed. Return a run summary: features created/updated, the breakdown table, cross-feature dependency highlights, open-question count (Blockers first, with owners), and any scope items you couldn't confidently place.
>
> Output directory (verbatim, or default): `<out>`

## 3. Push the features to the tracker

**A breakdown that stays on disk is invisible to everyone who isn't running this command.** The moment the folders are written, push them — run `/jetrix:push feature` and keep its per-feature response. No confirmation prompt: the push is idempotent (upsert by `feature_id`, hash-skipped per feature in sync-state), so a re-run after an edit updates the same tickets rather than filing duplicates.

It works on every tracker. `/jetrix:push feature` reads `tracker` from `project.json` and does the right thing — Mission Control Tasks on Jetrix, one issue per feature on Jira or ClickUp. Nothing here branches on the provider.

**Capture the link per feature.** `view_url` on Jetrix, whatever the tracker returned elsewhere; the push writes it back into each `feature.md` frontmatter alongside the issue ref. §4's summary prints every one — a feature with no link is a feature nobody can open.

Two failures worth handling rather than hiding:

- **No workspace bound** (`.jetrix/project.json` missing) — the breakdown still succeeded. Report the folders, say the push was skipped, and print `/jetrix:init` as the step that enables it.
- **Push partially failed** — list which features did not land and why, and print `/jetrix:push feature` to retry just those. Never report a breakdown as pushed when some of it is not.

## 4. Surface the result

When the agent returns, present its **run summary**: the requirement it worked in, how many features were created/updated, the breakdown table (Feature ID · Feature · Status · Priority · Dependencies), the key cross-feature dependencies, and the top open questions (Blockers first, with owners). Note that each feature folder is self-contained. If any scope item couldn't be confidently placed, call it out as a question — never as dropped. Keep it tight — the per-feature detail lives in the folders.

Close every run with this block, filled in. **Every feature gets a line with its link** — a table is only acceptable if it carries a URL column:

```
✓ 12 features · requirement shift-timesheet · pushed to Jetrix

  FEAT-PAY-01  Card checkout          https://app.jetrix.ai/task/Feature-41
  FEAT-PAY-02  Refund flow            https://app.jetrix.ai/task/Feature-42
  …
  Folders → requirements/shift-timesheet/features/

  Open questions: 2 Blocker · 5 Major   (they travel with the features as OQ-###)

Next:
  /qa:audit                    the repo has no test harness yet — start here
                               → /qa:plan → /qa:setup, then come back

  /dev:plan requirement=shift-timesheet    plan the batch for build
```

### Choosing the next step

Read `qa/quality-gates.md` and print **one** of these. Do not print both.

| State | Next |
|---|---|
| No `qa/quality-gates.md`, or `harness_status` is not `Active` | `/qa:audit` — the harness is what makes "verified" mean anything, and standing it up before the first build is far cheaper than after. Name `/dev:plan` as what follows it. |
| `harness_status: Active` | `/dev:plan requirement=<slug>` — say the gates are already active so nobody re-runs QA setup. |

**QA is strongly recommended, not mandatory.** `/dev:plan` runs without it (it records `qa_setup_skipped: true` and infers tier pools), so a user who wants to build now can. Say that only if they ask — leading with it invites skipping the thing that makes the build verifiable.

**Never print `tl-feature-planning` (internal) as a step** — `delivery-os-conventions` §1.f. `/dev:plan` auto-runs it when the graph is missing. The one TL command that *is* a real step is `/tl:code-map`, and `/dev:plan` raises that itself as a `PB-###` blocker when an area has no code-context — because it writes a committed tree into the product repo, which no summary line should trigger by itself.

> **Tip:** re-run `/ba:features` whenever the scope changes, a question gets answered, or a feature is split / merged / deferred — it updates the folders and the index in place, and re-pushes only what changed.
