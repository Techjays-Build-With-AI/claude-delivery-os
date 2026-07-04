---
name: dev-pr-handoff
description: Prepare a feature's pull-request handoff for human review, or write a structured blocker escalation when the loop is stuck. Use when the delivery loop reaches READY_FOR_PR ("prepare the PR", "write the PR summary", "hand this off for review"), or when a feature must stop and ask a human ("escalate this", "we're blocked"). For a handoff it verifies the completion criteria are met, then writes a review-ready summary — feature purpose, scope of changes, technical approach, affected pages/APIs/services, tests run, acceptance-criteria status, risks and rollout considerations, open follow-ups, and reviewer instructions — and moves the feature to HUMAN_REVIEW without merging or deploying. For an escalation it writes a structured note — what was attempted, the precise blocker, its impact on acceptance criteria, the decision needed with options and a recommendation, and the work that can safely continue — and sets the feature BLOCKED. It is the pr-preparer and blocker-escalator half of the dev agent; it never merges, deploys, or approves.
---

# Dev PR Handoff (review-ready PR summary / structured escalation)

You produce the two things a feature hands to a human: a **clean PR summary** when it's done, or a **structured escalation** when it's stuck. Both exist so a human can act quickly and correctly — approve a well-described change, or make a decision from a well-framed blocker. You never merge, deploy, or approve; you prepare the handoff.

## Operating contract

Read **`delivery-os-conventions`** and the delivery loop's `references/dev-context-templates.md` (`pr-summary.md`, `escalation-<n>.md` schemas) and `references/loop-control.md` (completion criteria, state model, permission boundaries) if not in context. Inputs are the feature's `dev/` context — `dev-plan.md`, `impacted-components.md`, `acceptance-map.md`, `implementation-log.md`, `decisions.md`, `delivery-status.md`. Field-level guidance for both outputs is in **`references/pr-and-escalation.md`**.

## PR handoff

1. **Gate on completion.** Before writing a PR summary, confirm every **mandatory** completion criterion in `loop-control.md` holds — scope implemented, required acceptance criteria `Passed`/`Waived`, tests + build + static checks green, docs updated, no unresolved critical/high defect, no unresolved blocker, tracker current. If any fails, **stop** — the feature isn't ready; return it to the loop or escalate. Do not paper over a gap with a hopeful summary.
2. **Write `dev/pr-summary.md`** from the template: feature purpose, scope of changes, technical approach, affected pages/APIs/services (cite the TL `PAGE-/EP-/ENT-` units), tests run, acceptance-criteria status (the `acceptance-map` table), risks/rollout considerations, known limitations and open follow-ups, and explicit reviewer instructions (what to focus on, how to run it). Name the branch.
3. **Advance the state** to `READY_FOR_PR` → `HUMAN_REVIEW`, mirror the mapped value into `status.md`/`feature-index.md`, and update `dev-output/feature-tracker.md` with the PR reference and next action ("await human review").
4. **Hand off** — return the summary and the link; the human reviews and merges. You stop here.

## Escalation

1. **Write `dev/escalation-<n>.md`** from the template: the feature and current state, what was attempted, the precise blocker, its impact (which acceptance criteria it stalls), the decision needed framed as concrete options, a recommended option with rationale, and the work that can safely continue in parallel.
2. **Set state `BLOCKED`**, mirror it to `status.md`/`feature-index.md`, and record the blocker + escalation link in `dev/delivery-status.md` and `dev-output/feature-tracker.md`.
3. **Hand off** — return the escalation so the human can decide. When the decision comes back, the delivery loop folds it in (logs the `DEC-###`), clears the blocker, and resumes.

## Boundaries

You never merge, deploy, approve your own work, or advance past `HUMAN_REVIEW` — those are human-owned states. You don't inflate a summary to get a feature through the gate, and you don't downgrade a real blocker into an assumption to avoid escalating. A good escalation is specific and decision-ready; a good PR summary lets a reviewer approve without spelunking the diff.

## Return value

For a handoff: the PR summary headline (purpose, scope, acceptance status, risks, reviewer focus) and the link to `dev/pr-summary.md`. For an escalation: the blocker, the decision needed with your recommendation, the parallel work that can continue, and the link to the escalation note.
