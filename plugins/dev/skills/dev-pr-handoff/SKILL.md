---
name: dev-pr-handoff
description: Compose the review-ready `dev/pr-summary.md` for `/dev:commit` Stage 9, or the structured `dev/escalation-<n>.md` for any stage that hits bounds-exceeded / immovable-blocker. Content composition ONLY — no state transitions, no MC calls, no tracker updates. The invoking orchestrator (`/dev:commit`, `/dev:build`, `/dev:plan`) owns state. Use when a stage needs the polished reviewer-facing PR body written, or when a blocker requires structured human escalation. Never merges, deploys, approves, or promotes state.
---

# Dev PR Handoff (content composition only)

You compose the two review-ready documents the delivery loop produces: a **clean PR summary** for `/dev:commit` Stage 9, or a **structured escalation** when any stage hits bounds-exceeded / immovable-blocker. **Composition only.** State transitions, MC status updates, and `features/tracker.md` writes are owned by the invoking orchestrator, NOT by this skill.

The v2.2 slim-down: this skill was previously a state-transitioning agent; it no longer is. Orchestrators now handle their own state. This skill focuses on producing well-structured reviewer-facing content.

## Operating contract

Read **`delivery-os-conventions`** and **`references/pr-and-escalation.md`** if not in context. Inputs from the task's `dev/` folder:

- For a PR summary: `dev/build-run.md`, `dev/commit-run.md`, `dev/acceptance-map.md`, `dev/implementation-log.md`, `dev/security-findings-commit.md`, `dev/code-review-findings.md`, `dev/context-merge-log.md`, `dev/decisions.md`, plus parent BA files (`feature.md`, `business-rules.md`, `nfrs.md`).
- For an escalation: `dev/build-run.md` OR `dev/commit-run.md` (the failing run log), the finding chain, `dev/delivery-status.md`, plus optional `dev/plan-blockers.md` if plan-time is the halt.

## PR summary composition

1. **Verify the gate is passable.** Check `dev/commit-run.md`:
   - Stage 3 (security): zero Critical + zero High
   - Stage 4 (code review): zero Blocker + zero Major
   - Stage 5 (acceptance): all rows `✅` or valid `⏸ deferred-to-e2e`
   - Stage 7 (semantic merge): zero unresolved conflicts

   If any gate fails, this skill REFUSES to write the PR summary — return the failing gate + a suggestion to route back to the appropriate stage. NEVER paper over a failing gate with hopeful prose.

2. **Compose `dev/pr-summary.md`.** Follow the exact structure in `references/pr-and-escalation.md#pr-summary`. The output is reviewer-facing:
   - Purpose (2 lines from parent's `feature.md`)
   - Scope of changes (files, endpoints, entities)
   - Technical approach (3-4 sentences, framework-agnostic where possible)
   - Test coverage summary (numbers only)
   - Acceptance criteria table
   - Business rules enforcement table
   - Security review outcome (commit-time thresholds)
   - Code review outcome (severity breakdown)
   - Follow-up suggestions (Minor findings, non-blocking)
   - Semantic context merge summary
   - Deferred-to-E2E items
   - Reviewer instructions (focus areas + non-concerns)

3. **Return** the composed file path + the headline (Purpose, Scope, Acceptance summary, Reviewer focus) as terminal output for the orchestrator to route.

## Escalation composition

1. **Compose `dev/escalation-<n>.md`** (n = next sequential integer already determined by the caller). Follow the exact structure in `references/pr-and-escalation.md#escalation`:
   - Feature identity + current state
   - What was attempted (chain of finding + fix + broad-rerun outcomes)
   - Precise blocker (finding text + failure scenario)
   - Impact (which ACs / BRs / NFRs it stalls)
   - Decision needed (framed as concrete options)
   - Recommended option (with rationale)
   - Work that can safely continue in parallel (if any)

2. **Return** the composed file path + the blocker + recommended option as terminal output. The invoking stage (Stage 6 fix loop, Stage 7 conflict, etc.) handles the state transition (LOCAL → BLOCKED, MC status → blocked when appropriate) itself.

## Boundaries

- **NEVER** call `task-mcp` or any MC status transition
- **NEVER** modify `dev/delivery-status.md` or `features/tracker.md`
- **NEVER** flip local state (that's the orchestrator's job)
- **NEVER** merge, push, deploy, or approve
- **NEVER** create the branch, execute tests, or run security scans (upstream stages do this)
- **NEVER** inflate a summary to get a feature through a failing gate
- **NEVER** downgrade a real blocker into an assumption to avoid escalating

The skill is content composition only. If asked to do more, refuse and route back to the orchestrator.

## Return value

- **PR summary path:** `dev/pr-summary.md` written; return the file path + a 4-line headline
- **Escalation path:** `dev/escalation-<n>.md` written; return the file path + blocker + recommendation

The orchestrator ingests the return value and handles routing / state.
