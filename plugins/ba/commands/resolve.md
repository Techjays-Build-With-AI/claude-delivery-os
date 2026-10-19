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

> Run a scope-review resolution round using the `ba-scope-review` skill — follow `references/resolution-loop.md`. Read the responses file at `<path>`, take its `source_review` reviewId, and load the matching `scope-review-<reviewId>.json` (the prior review state) from the same folder. For each question that received an answer, **adjudicate** it: set status to `Resolved`, `Accepted-assumption`, `Needs-verification` (with 1–3 specific follow-up questions), `Won't-fix`, or leave it `Open` — with a one-line rationale each. Be skeptical: require specifics, don't close on vague assurances. For every terminal question, give the **exact scope edit** (which §3.x sub-heading, what text) and, when a workspace exists, promote it: confirmed facts → `shared-context/decision-log.md` (`DEC-###`) and the scope; accepted assumptions → `ba/registers/assumptions.md` (`ASM-###`, RAID A-##); still-open must-close items → `ba/logs/clarifications.md` (`CLR-###`, RAID Q-##). Carry all questions forward by their stable `SQ-###` IDs, update each feature's coverage map, and recompute the feature scores and the scope-readiness verdict (a resolved Blocker lifts the cap; note residual risk for accepted assumptions). Then write a **new review round** — fresh timestamped `.html` / `.md` / `.json`, with `round` incremented and `priorReview` set to the resolved reviewId — and return a summary of the movement.
>
> Responses file: `<path>`

## 3. Surface the result

When the agent returns, present the **round summary**: how many questions were Resolved / Accepted-as-assumption / Needs-verification (list the follow-ups the author still needs to answer) / still Open, the score and verdict movement (e.g. "3.4 → 6.2, Significant gaps → Estimate with caveats"), which scope edits were applied, and any `DEC`/`ASM`/`CLR` rows logged.

A round writes a **new timestamped report**. Link and serve it exactly as `/ba:review` §3 does — local only, never published. The round number belongs in the summary so nobody opens the wrong file.

**Reuse a server that is already up.** If one is serving `ba/reviews` from an earlier command in this session, the new round is already reachable — print its URL rather than starting a second one on another port, which only splits the user's attention across two tabs.

Close every round with this block. **The routing rule is `/ba:review` §3's, applied to the new counts** — a resolve round that still leaves a Blocker open routes to resolve again, not forward:

```
Round 2 — scope readiness 3.4 → 6.2   Significant gaps → Estimate with caveats
  Resolved <n> · Assumption <n> · Needs-verification <n> · Open <n>
  Logged: DEC-004, DEC-005, ASM-002, CLR-009

Report   http://127.0.0.1:<port>/scope-review-<ts>.html
         ba/reviews/scope-review-<ts>.html

Next:
  <one block, chosen by /ba:review §3's table against the NEW counts>
```

Three endings, and they are not interchangeable:

- **Follow-ups outstanding** (`Needs-verification`) → answer them in the new report, export, `/ba:resolve` again. Name the follow-ups; "some items need verification" tells the author nothing to act on.
- **No Blocker left** → `/ba:features`.
- **New material arrived instead of answers** → `/ba:scope add "…"`, then re-review. Resolve adjudicates answers to existing questions; it cannot absorb a new document.
