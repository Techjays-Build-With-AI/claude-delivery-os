---
description: Prepare the pull-request handoff for a feature whose implementation and validation are complete — verify the completion criteria, then write a review-ready summary (purpose, scope, technical approach, affected pages/APIs/services, tests run, acceptance-criteria status, risks, follow-ups, reviewer instructions) and move the feature to HUMAN_REVIEW. Never merges or deploys.
argument-hint: "<FEAT-<AREA>-NN | context/features/<slug>>"
---

# /dev:pr

You prepare the **PR handoff** for a feature that is implemented and validated. Delegate to the **`dev-agent`** subagent, which uses the `dev-pr-handoff` skill.

## 1. Parse arguments

`$ARGUMENTS` should contain a **feature target** (`FEAT-<AREA>-NN`, folder, or slug). Required — if missing, ask which feature and stop. If it doesn't resolve, ask for a valid one.

## 2. Delegate

Invoke the **dev-agent** subagent. Pass it this instruction:

> Prepare the PR handoff for `<target>` using the `dev-pr-handoff` skill. First **gate on completion**: confirm every mandatory criterion in the loop's `loop-control.md` holds — scope implemented, required acceptance criteria `Passed`/`Waived` in `dev/acceptance-map.md`, tests + build + static checks green, docs updated, no unresolved critical/high defect, no unresolved blocker, tracker current. If any fails, stop and report what's missing (or escalate) — do not write a summary for an unready feature. Otherwise write `dev/pr-summary.md` (feature purpose, scope of changes, technical approach, affected pages/APIs/services citing the TL `PAGE-/EP-/ENT-` units, tests run, acceptance-criteria status, risks/rollout, open follow-ups, reviewer instructions, branch name), advance the feature `READY_FOR_PR` → `HUMAN_REVIEW`, mirror the mapped state into `status.md`/`feature-index.md`, and update `dev-output/feature-tracker.md`. Do not merge or deploy. Return the PR summary headline and the link.

## 3. Surface the result

Present the **PR summary headline** — purpose, scope, acceptance-criteria status, risks, and reviewer focus — with a link to `dev/pr-summary.md`. If the completion gate failed, report exactly which criteria are unmet and point the user to `/dev:build` to finish or note the escalation.
