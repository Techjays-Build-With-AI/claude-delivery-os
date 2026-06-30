---
description: Adjudicate author answers to a scope review and close the questions. Point it at the scope-review-<timestamp>-responses.md file exported from the HTML report; the BA agent matches it to the original review, judges each answer (resolve / accept-as-assumption / ask for verification / decline), folds confirmed answers back into the scope and the BA registers, recomputes the scores and verdict, and writes a new review round.
argument-hint: "<path-to-scope-review-<timestamp>-responses.md>"
---

# /ba:resolve

You are running a **resolution round** on a scope review: the author has answered the scope questions, and you adjudicate each answer, close the open items, and fold the answers back into the scope. Delegate the work to the **`ba-agent`** subagent.

## 1. Parse arguments

`$ARGUMENTS` should be the path to a **responses file** — `scope-review-<reviewId>-responses.md`, exported from the interactive HTML report (or hand-written in the same format). This is required.

- If no path is given, ask the user which responses file to resolve and stop.
- If the path doesn't resolve, say so and ask for a valid one.
- The `<reviewId>` (timestamp) embedded in the filename and the file's `source_review` frontmatter is the **join key** back to the original review.

## 2. Delegate

Invoke the **ba-agent** subagent with the responses-file path. Pass it this instruction:

> Run a scope-review resolution round using the `ba-scope-review` skill — follow `references/resolution-loop.md`. Read the responses file at `<path>`, take its `source_review` reviewId, and load the matching `scope-review-<reviewId>.json` (the prior review state) from the same folder. For each question that received an answer, **adjudicate** it: set status to `Resolved`, `Accepted-assumption`, `Needs-verification` (with 1–3 specific follow-up questions), `Won't-fix`, or leave it `Open` — with a one-line rationale each. Be skeptical: require specifics, don't close on vague assurances. For every terminal question, give the **exact scope edit** (which §3.x sub-heading, what text) and, when a workspace exists, promote it: confirmed facts → `shared-context/decision-log.md` (`DEC-###`) and the scope; accepted assumptions → `assumption-register.md` (`ASM-###`, RAID A-##); still-open must-close items → `clarification-log.md` (`CLR-###`, RAID Q-##). Carry all questions forward by their stable `SQ-###` IDs, update each feature's coverage map, and recompute the feature scores and the scope-readiness verdict (a resolved Blocker lifts the cap; note residual risk for accepted assumptions). Then write a **new review round** — fresh timestamped `.html` / `.md` / `.json`, with `round` incremented and `priorReview` set to the resolved reviewId — and return a summary of the movement.
>
> Responses file: `<path>`

## 3. Surface the result

When the agent returns, present the **round summary**: how many questions were Resolved / Accepted-as-assumption / Needs-verification (list the follow-ups the author still needs to answer) / still Open, the score and verdict movement (e.g. "3.4 → 6.2, Significant gaps → Estimate with caveats"), which scope edits were applied, and any `DEC`/`ASM`/`CLR` rows logged. Link to the new round's `.html` (interactive) and `.md`. If items still need verification, tell the user to answer the follow-ups in the new report and export again.
