---
description: Adjudicate author responses to a spec review and close findings. Point it at the spec-review-<timestamp>-responses.md file exported from the HTML report; the TL agent matches it to the original review, judges each response (resolve / accept-risk / ask for verification / decline), recomputes the score and verdict, logs decisions, and writes a new review round.
argument-hint: "<path-to-spec-review-<timestamp>-responses.md>"
---

# /tl:resolve

You are running a **resolution round** on a technical-spec review: the author has responded to the findings, and you adjudicate each response and close the open items. Delegate the work to the **`tl-agent`** subagent.

## 1. Parse arguments

`$ARGUMENTS` should be the path to a **responses file** — `spec-review-<reviewId>-responses.md`, exported from the interactive HTML report (or hand-written in the same format). This is required.

- If no path is given, ask the user which responses file to resolve and stop.
- If the path doesn't resolve, say so and ask for a valid one.
- The `<reviewId>` (timestamp) embedded in the filename and the file's `source_review` frontmatter is the **join key** back to the original review.

## 2. Delegate

Invoke the **tl-agent** subagent with the responses-file path. Pass it this instruction:

> Run a resolution round using the `tl-spec-review` skill — follow `references/resolution-loop.md`. Read the responses file at `<path>`, take its `source_review` reviewId, and load the matching `spec-review-<reviewId>.json` (the prior review state) from the same folder. For each finding that received a response, **adjudicate** it: set status to `Resolved`, `Accepted-risk`, `Needs-verification` (with 1–3 specific follow-up questions), `Won't-fix`, or leave it `Open` — with a one-line rationale each. Be skeptical: require concrete specifics, don't close on vague assurances; where a resolution implies a spec change, state the exact edit. Carry all findings forward by their stable `FND-###` IDs, recompute area scores and the overall readiness verdict (a resolved Blocker lifts the cap; note residual risk for accepted-risk items). Append a `DEC-###` row to `shared-context/decision-log.md` for each terminal finding if a workspace exists. Then write a **new review round** — fresh timestamped `.html` / `.md` / `.json`, with `round` incremented and `priorReview` set to the resolved reviewId — and return a summary of the movement.
>
> Responses file: `<path>`

## 3. Surface the result

When the agent returns, present the **round summary**: how many findings were Resolved / Accepted-risk / Needs-verification (list the follow-up questions the author still needs to answer) / still Open, the score and verdict movement (e.g. "2.0 → 6.1, Not ready → Significant gaps"), and any `DEC-###` decisions logged. Link to the new round's `.html` (interactive) and `.md`. If items still need verification, tell the user to answer the follow-ups in the new report and export again.
