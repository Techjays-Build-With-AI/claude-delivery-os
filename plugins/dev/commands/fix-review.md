---
description: Fold human reviewer feedback back into an open PR — re-enter the delivery loop at the review-fixes step, address actionable comments within the retry limits, re-validate against acceptance criteria, and refresh the PR summary. Escalates comments that need a product/architecture/security decision instead of guessing. Never merges or deploys.
argument-hint: "<FEAT-<AREA>-NN | context/features/<slug>> [feedback=<path-to-review-comments> | pr=<link>]"
---

# /dev:fix-review

You respond to **reviewer feedback** on a feature already at `HUMAN_REVIEW`. Delegate to the **`dev-agent`** subagent.

## 1. Parse arguments

`$ARGUMENTS` should contain a **feature target** (`FEAT-<AREA>-NN`, folder, or slug) and the **reviewer feedback** — a path to a comments file, an inline list, or a PR link. The target is required; if the feedback source is missing, ask where the review comments are and stop.

## 2. Delegate

Invoke the **dev-agent** subagent. Pass it this instruction:

> Run review-fix for `<target>` using the `feature-delivery-loop` skill. Read the reviewer feedback at `<feedback>` and the feature's current `dev/delivery-status.md`, `dev/pr-summary.md`, and `dev/acceptance-map.md`. Treat the reviewer comments as the failure set and re-enter at `REVIEW_FIXES`: for each comment decide if it's actionable, make a focused fix within the 3-attempt limit, re-run the narrow check then `dev-validation`, and log each attempt in `dev/implementation-log.md`. Run `dev-code-review` again over the new diff. Any comment that needs a product, architecture, schema, or security decision → write `dev/escalation-<n>.md` and set `BLOCKED` rather than guessing. Update `dev/decisions.md` (+ `DEC-###`), the trackers, and refresh `dev/pr-summary.md` with what changed and how each comment was addressed. Keep the feature at `HUMAN_REVIEW` (do not merge/deploy). Return which comments were addressed, which were escalated, the re-validation result, and the updated PR summary link.
>
> Feedback: `<feedback path / PR link>`

## 3. Surface the result

Present the per-comment disposition (addressed / escalated / needs-clarification), the re-validation summary, any `DEC-###` logged, and the link to the refreshed `dev/pr-summary.md`. If anything was escalated, lead with the decision the human needs to make.
