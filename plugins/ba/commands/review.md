---
description: Review a BA scope document the way a paranoid Business Analyst would before estimate or sign-off. Pass the scope path (defaults to requirements/<slug>/scope.md); the BA agent breaks it down feature by feature, interrogates each for under-specification, validates it against the client's shared examples, scores each feature out of 10, and writes a timestamped interactive scope-review-<timestamp>.html dashboard to `requirements/<slug>/reviews/`.
argument-hint: "[<path-to-scope-doc>] [out=<output-prefix>]"
---

# /ba:review

You are the entry point for a Business Analyst **scope review**. Parse the arguments and **delegate the actual review to the `ba-agent` subagent**, which runs in its own context and does the document-heavy reading, interrogation, and scoring.

## 1. Parse arguments

`$ARGUMENTS` may contain:
- An optional **scope document reference** — a path to a `.md` / `.docx` / `.pdf` scope, or a link. If omitted, default to `requirements/<slug>/scope.md` when a Delivery OS workspace is present.
- An optional **`out=<prefix>`** to override the report location/prefix (default `requirements/<slug>/reviews/scope-review`; beside the document if there's no Delivery OS workspace). A run timestamp is **always** appended, so the files are `<prefix>-<timestamp>.html` and repeated reviews never collide.

If no scope can be located (no path given and no `requirements/<slug>/scope.md`), ask the user which scope to review and stop. If a given path doesn't resolve, say so and ask for a valid one rather than guessing.

## 2. Delegate

Invoke the **ba-agent** subagent with the scope reference and output path. Pass it this instruction:

> Run a **scope review** of the scope document at `<doc-ref>` using the `ba-scope-review` skill — act as a paranoid Business Analyst. Read the whole scope first, then load the scope knowledge base (`requirements/<slug>/registers/examples.md` and the other registers, `requirements/<slug>/ledger.md` (kind: question), `requirements/<slug>/ledger.md` (kind: contradiction), `shared-context/`) when a workspace exists. Decompose the scope into features/modules and, for each, judge coverage across the nine Techjays D&D dimensions (current→future, in/out scope, functional reqs, AI/automation, business rules, data fields, integrations, exceptions, acceptance), interrogate every under-specified point into concrete questions (e.g. "login screen" → which auth method? email vs social vs OTP vs SSO? personal vs corporate email? verification, lockout, MFA, session, roles?), and validate the feature against the client's examples (Pass/Partial/Conflict/No-examples, citing EX ids). Then **screen every question before it counts**: re-search the scope for its answer (record where you looked in `checkedIn`) and name what changes if it stays unanswered (`consequence`) — drop anything the scope already answers, correcting the coverage cell it came from. **Derive** each feature's score from its coverage map rather than judging it — `round(min(coverageScore, cap))`, emitting `coverageScore` and `cap` so it can be audited — give every question a severity (Blocker/Major/Minor/Nit), compute the overall score and scope-readiness verdict (any Blocker caps it), read a run timestamp (`YYYY-MM-DD-HHMMSS`) from the system clock, write the data object to a scratch file (injection input, **not** an output), then generate the interactive `<prefix>-<timestamp>.html` from it with the bundled UTF-8-safe injector (`node assets/inject.js assets/report.html <scratch>/review-data.json __REVIEW_DATA__ <prefix>-<timestamp>.html` — never hand-assemble the HTML, or non-ASCII glyphs like § and — double-encode into mojibake), plus the `<prefix>-<timestamp>.md` artifact (default prefix `requirements/<slug>/reviews/scope-review`) per the report template. Return the executive summary, the feature scorecard, and links to the files.

## 3. Surface the result

When the agent returns, present its **executive summary and feature scorecard**: the overall score, the scope-readiness verdict, the scorecard table, and the top 3–5 gating questions (Blockers/Majors first) with the scope addition each needs. Keep it tight — the per-feature detail lives in the report.

**The review report is local. It is never published.** `scope.html` is the client-facing artifact and goes to Dashboard → Reports; the review is the BA's working surface — it holds unanswered questions, contradictions and a readiness score that is wrong until the round closes. Hosting that is a liability, and nobody but the BA fills it in. Never call `scope_prepare_report_push` here.

**Open it for them — do not print a command and hope.** Start the server yourself, in the background, as the last action of the run:

```bash
node ${CLAUDE_PLUGIN_ROOT}/../delivery-os-core/scripts/serve-review.js .jetrix/requirements/<slug>/reviews
```

**Serve the folder the report is actually in.** BA reviews moved under `requirements/<slug>/reviews/` in v2.0; `ba/reviews` is the v1 path and nothing writes there. Serving the wrong folder leaves the page unable to find its own server, and the reader is told to start one that is already running.

Read the port from its `DELIVERY_OS_SERVE_READY` line — `delivery-os-conventions` §1.e.

Why it must be served rather than double-clicked: Save POSTs the answers back to this server, which writes `scope-review-<ts>-responses.md` into the folder and returns the path it wrote. Opened from `file://` there is no server to ask, so Save degrades to a download and the page says so — correct, but it puts the file in Downloads and hands the user a move step. Starting the server is what keeps that step out of the flow.

If Node is unavailable or the server will not start, say so in one line and print the local file path instead. A review nobody can save from is still worth reading.

Close every run with this block, filled in — every path and command copy-pasteable, never described in prose:

```
Scope readiness: <score> / 10 — <verdict>
Blockers: <n>   Major: <n>   Minor: <n>   Nit: <n>

Report   http://127.0.0.1:<port>/scope-review-<ts>.html    ← open in your browser
         requirements/<slug>/reviews/scope-review-<ts>.html                  ← the file itself

Next:
  1. Answer the questions, click Save — it writes straight to
     requirements/<slug>/reviews/scope-review-<ts>-responses.md
  2. /ba:resolve requirements/<slug>/reviews/scope-review-<ts>-responses.md

  (the review server is running in this session — Save stops working when it stops)
```

The HTML is where the questions get answered — say so as a step, not as a footnote. A reader who is only told the file exists will read it and answer nowhere.

### The next step depends on the score — choose ONE

Print exactly one `Next:` block. **Blockers decide it, not the score**, because a 7/10 hiding one Blocker is not estimate-ready and a 5/10 of Minors is.

| Reading | Next |
|---|---|
| **Any Blocker** | `/ba:resolve` on the responses file. Nothing else — say which Blockers gate it. |
| **No Blocker, Majors open** | Offer both: `/ba:features` now (the Majors become `OQ-###` in the feature folders and travel with the build), or `/ba:resolve` first to close them. **Recommend resolve** where a Major has `consequence: scope` or `integrations` — those change what gets built, not just the estimate. |
| **No Blocker, Minors/Nits only** | `/ba:features`. Say the open items ride along as `OQ-###`. |

Where new material has arrived rather than answers, the step is `/ba:scope add "…"` and then re-review — `/ba:resolve` adjudicates answers to *existing* questions and has nothing to do with new sources.

```
Next:
  No blockers — 3 Major, 6 Minor open.

  /ba:features                                       build the breakdown now
                                                     (the 9 open items ride along as OQ-###)

  or close them first:
  /ba:resolve requirements/<slug>/reviews/scope-review-<ts>-responses.md
```
