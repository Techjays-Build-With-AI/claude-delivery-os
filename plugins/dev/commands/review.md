---
description: Review a technical specification (architecture / system design / HLD / SRS) and produce a scored, interactive report you answer inside. One command, two modes — it reads the folder and knows which. No responses file yet → a fresh review round, scoring each area out of 10 with concrete findings. A saved responses file → the resolution round: it adjudicates each answer (resolve / accept-risk / needs-verification / decline), recomputes the score and verdict, and writes the next round. Replaces the old /dev:review + /dev:review pair. Read-only on the spec; writes only into tl-reviews/.
argument-hint: "[<path-or-link-to-spec-doc>] [out=<output-prefix>]"
---

# /dev:review

Review a technical specification the way a Technical Lead would before build starts — scored per area, every deduction backed by a concrete finding, and the open questions answered **inside the report** rather than in a thread nobody can find later.

Delegate the work to the **`tl-agent`** subagent, which runs `tl-spec-review` in its own context.

Read the `delivery-os-conventions` skill first if it isn't in context.

## 1. Decide which round this is — do not ask

**One command, two modes.** Look in `tl-reviews/` for a `spec-review-<ts>-responses.md` newer than its matching `spec-review-<ts>.html`:

| What you find | What this run is |
|---|---|
| No responses file, or none newer than its report | **a fresh review round** — §3 |
| A responses file newer than its report | **a resolution round** — §4 |

**Never ask the user which.** They saved answers in a browser; asking them to also name a mode is making them do the command's job. This is what the old `/dev:review` was, and splitting it across two commands was the only reason the question existed.

A spec reference is **required for the first round** and ignored afterwards — the resolution round takes its document from the review it resolves.

## 2. Parse arguments

- A **document reference** — a path to a `.md` / `.docx` / `.pdf` spec, or a link. Required on a first round; if none is given and there is no responses file to resolve, ask which spec to review and stop.
- An optional **`out=<prefix>`** — overrides the location (default `tl-reviews/spec-review`; beside the document when there is no Delivery OS workspace). A run timestamp is **always** appended, so rounds accumulate and a round never overwrites the one before it.

## 3. Fresh review round

Invoke **tl-agent**:

> Review the technical specification at `<doc-ref>` using the `tl-spec-review` skill. Read the whole document first. Determine whether the system uses an LLM/AI and whether it spans multiple systems, then score each applicable review area out of 10 — Overview, Architecture & System Design, Feature Flows & System Sequencing, Data Schema, API Contracts, Libraries; and (if AI is involved) Observability & Traceability, Evals, Feedback Loops, AI Compliance; plus Infrastructure, CI/CD & Release Management, and Cost Projection. Back every deduction with a finding (severity Blocker/Major/Minor/Nit) and a concrete suggestion, note real strengths, compute the overall score and readiness verdict, read a run timestamp (`YYYY-MM-DD-HHMMSS`) from the system clock, build the review data object, then generate the interactive `spec-review-<timestamp>.html` with the bundled UTF-8-safe injector — `node assets/inject.js assets/report.html <scratch>/spec-review-data.json __REVIEW_DATA__ tl-reviews/spec-review-<timestamp>.html` — never hand-assemble the HTML, or non-ASCII glyphs like § and — double-encode into mojibake. Mark non-applicable areas N/A with a one-line reason. Return the executive summary, the scorecard, and the report path.
>
> Spec: `<doc-ref>` · Output prefix: `<out or tl-reviews/spec-review>`

## 4. Resolution round

Invoke **tl-agent**:

> Run a spec-review resolution round using the `tl-spec-review` skill — follow `references/resolution-loop.md`. Read the responses file at `<path>`, take its `source_review` reviewId, and load that round's data from the matching report's `<script id="review-data">` block. For each finding that received an answer, **adjudicate** it: `Resolved`, `Accepted-risk`, `Needs-verification` (with 1–3 specific follow-ups), `Won't-fix`, or still `Open` — each with a one-line rationale. Be skeptical: require specifics, never close on a vague assurance. Promote terminal items — a confirmed decision → `DEC-###` in `shared-context/decision-log.md`; an accepted risk → recorded with its residual exposure named. Carry every finding forward by its stable id, recompute the area scores and the readiness verdict (a resolved Blocker lifts the cap; an accepted risk does not), and write a **new timestamped round** with `round` incremented and `priorReview` set. Return the movement summary.
>
> Responses file: `<path>`

## 5. Serve it and print both links

`delivery-os-conventions` §1.e. Start the server in the background as the last action and read the port from its `DELIVERY_OS_SERVE_READY` line:

```bash
node ${CLAUDE_PLUGIN_ROOT}/../delivery-os-core/scripts/serve-review.js .jetrix/tl-reviews
```

**Serving is not optional here.** Save POSTs the answers back to this server, which writes the responses file into the folder — which is what makes the next `/dev:review` a resolution round with nothing to type. Opened from `file://` it degrades to a download and the user has to move the file by hand, which is the step people skip.

## 6. Report

```
Spec readiness: <score> / 10 — <verdict>
Blockers: <n>   Major: <n>   Minor: <n>   Nit: <n>

Report   http://127.0.0.1:<port>/spec-review-<ts>.html    ← open in your browser
         tl-reviews/spec-review-<ts>.html                 ← the file itself

Next:
  1. Answer each finding in the report, click Save
  2. /dev:review          folds your answers in and writes the next round
```

On a resolution round, open with the movement — `Round 2 · 6.2 → 8.1 · 9 resolved, 3 accepted as risk, 2 need verification` — then the same two link lines. **Name the follow-ups**; *"some items need verification"* gives the author nothing to act on.

### Where this goes next

Print **one** step, chosen from the result:

| | |
|---|---|
| Blockers open | `/dev:review` again, after answering. Nothing else — say which Blockers gate it. |
| No Blockers left | `/dev:plan` — the spec is ready to build from. Blank plans the whole requirement; do not narrow it to a subset yourself. |

**Never print `tl-feature-planning` (internal)** (`delivery-os-conventions` §1.f). `/dev:plan` builds the technical context graph itself.

## What replaced what

| Was | Now |
|---|---|
| `/dev:review <doc>` | `/dev:review <doc>` |
| `/dev:review <responses>` | `/dev:review` — it sees the saved file and resolves |
| `tl-feature-planning` (internal) | internal; `/dev:plan` auto-runs it |

Three commands became one, and the one no longer asks a question the folder already answers. The skill, the rubric and the resolution loop are unchanged — `tl-spec-review` still does the work.
