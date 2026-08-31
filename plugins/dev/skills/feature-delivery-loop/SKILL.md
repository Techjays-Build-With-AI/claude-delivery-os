---
name: feature-delivery-loop
description: Deliver one already-planned task (a parent feature or a sub-task) through the v2.2 three-command flow — `/dev:build` (11-stage build loop) followed by `/dev:commit` (10-stage commit loop) — rather than a one-shot code dump. Use when the user asks to "build/implement a task", "run the delivery loop", "develop FEAT-…", "take this feature to a PR", or hand an already-planned task to development. Refuses if `/dev:plan` hasn't run for this task OR if `dev/plan-blockers.md` has unresolved entries — those routes to `/dev:plan` / `/dev:plan --resume`. Enforces the two-gate security model (Critical-only at build, Critical+High at commit), the dynamic stack-adaptive skills (implementation + code-review + qa-greenfield-harness), and semantic context merge (unit-level, not text-level) via `tl-semantic-context-merge`. Uses MC's existing status enum (`todo | readyForDev | inProgress | agentExecuting | devReview | blocked | done`) — never invents local MC states. Orchestrates `/dev:build` first then `/dev:commit`; each is user-invoked (never runs both back-to-back on its own).
---

# Feature Delivery Loop (v2.2 — planned task → validated PR handoff)

You are the outer wrapper that turns an **already-planned task** — either a parent feature (parent-alone) or one sub-task of a split feature — into a working, validated, review-ready PR. Planning (readiness gate, impact analysis, dev-plan.md, plan-blocker resolution) is `/dev:plan`'s job. Building (branch, harness, implement, test, security-build-gate, context flip) is `/dev:build`'s job. Committing (security-commit-gate, code review, acceptance re-verify, semantic-context-merge, push, PR) is `/dev:commit`'s job.

This skill is the **loop coordinator** — it doesn't run the stages itself; it ensures the developer invokes `/dev:build` and `/dev:commit` in the right order with the right preconditions.

**Not a one-shot dispatch.** `/dev:build` finishes → developer verifies locally (via `dev/local-runbook.md`) → developer invokes `/dev:commit`. Never chain the two automatically.

## Operating contract

Read the **`delivery-os-conventions`** skill first (v2.2) — the loop-control state model + MC status mapping. Then read the task's `dev/delivery-status.md`.

**Inputs (from upstream — never re-derive):**

- `/dev:plan` outputs (parent-alone or sub-task):
  - `dev/dev-plan.md` — the build script
  - `dev/impacted-components.md` — what's touched
  - `dev/delivery-status.md` — current state, ownership, branch
  - `dev/plan-blockers.md` — plan-time blocker resolution (v2.2). MUST be absent or `status: RESOLVED` before `/dev:build` can start.
- Parent BA files (`feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md`)
- Parent's TL Implementation content (`tl-plan.md`) OR sub-task's Description + Implementation tabs
- TL context graph — per-repo `context/code-context/` (frontend/backend/database)
- `shared-context/decision-log.md`, `ba/` registers
- Project metadata via `mcp__project-mcp__project_get_project` + `.jetrix/project.json` + `.jetrix/cache/repolocation.json`

**Writes coordinated by this loop (via the two commands):**

- `dev/build-run.md` (by `/dev:build`)
- `dev/commit-run.md` (by `/dev:commit`)
- `dev/implementation-log.md`, `dev/acceptance-map.md`, `dev/decisions.md`, `dev/security-findings-build.md`, `dev/security-findings-commit.md`, `dev/code-review-findings.md`, `dev/context-merge-log.md`, `dev/context-merge-conflicts.md`, `dev/local-runbook.md`, `dev/pr-summary.md`, `dev/escalation-<n>.md`
- MC task status via `mcp__task-mcp__update_task_status`
- Context-mcp: `context_pull_manifest` (baseline read) at Stage 7 semantic merge

## The v2.2 three-command flow

### 1. `/dev:plan <target>` — MUST run first

Produces `dev/dev-plan.md` + `dev/impacted-components.md` + `dev/plan-blockers.md` + `dev/delivery-status.md` at `current_state: PLANNED`. Any blocker → `dev/plan-blockers.md` with `status: OPEN | RESOLVING | RESOLVED` — resolution is user-driven at plan time.

If `/dev:plan` hasn't run → this loop refuses and instructs the user to run `/dev:plan <target>` first.

### 2. `/dev:build <target>` — 11 stages

**Precondition:** `dev/dev-plan.md` exists, `delivery-status.md` `current_state: PLANNED`, and any `dev/plan-blockers.md` is either absent or fully `status: RESOLVED`.

Stages (see `plugins/dev/commands/build.md` + refs):

1. Identity + plan verification (hard gate on blockers)
2. Lock + mount context
3. Pre-flight (MC status + drift + cross-sub-task deps)
4. Branch creation FIRST
5. QA harness gate (auto-bootstraps via `qa-greenfield-harness` skill — deterministic, no prompts)
6. Implementation (via `dev-stack-adaptive-implementation` skill — dynamic per stack)
7. Test writing (same skill)
8. Test execution locally
9. Acceptance map validation
10. Security review — **build-time gate, Critical-blocking only**
11. Update code-context units (`designed → implemented`)
12. Summary + `dev/local-runbook.md`

**Ends with:** local state `IN_PROGRESS`, MC status `inProgress`. Never pushes; never raises PR.

### 3. Developer verifies locally

The `dev/local-runbook.md` from `/dev:build` Stage 11 tells the developer how to run the feature manually. This is NOT part of the loop — it's a human step.

### 4. `/dev:commit <target>` — 10 stages

**Precondition:** `delivery-status.md` `current_state: IN_PROGRESS`, `ready_for_dev_commit: true`, branch checked out in target repo.

Stages (see `plugins/dev/commands/commit.md` + refs):

1. Identity + branch verification
2. Lock + flip to `REVIEW` (local) + `devReview` (MC)
3. Base branch selection
4. Security review — **commit-time strict gate, Critical + High blocking** (same skill as build, stricter threshold)
5. Code review — via `dev-stack-adaptive-code-review` skill, Blocker + Major blocking
6. Acceptance-map re-verification + last-sub-task E2E resolution
7. Bounded fix loop (routes back to Stages 3–5 on findings)
8. Semantic context merge — via `tl-semantic-context-merge` skill, unit-level not line-level
9. Push branch
10. Raise PR (body = `dev/pr-summary.md`, composed via slim `dev-pr-handoff` skill)
11. Terminal summary

**Ends with:** local state `REVIEW`, MC status `devReview`. Human reviews PR. On PR merge, webhook (v2.3) flips MC to `done`.

## MC status mapping (v2.2)

Use MC's existing enum verbatim. Never invent local variants.

| Local state | MC status | Set by |
|---|---|---|
| PLANNED | readyForDev | `/dev:plan` end |
| IN_PLANNING | inProgress | `/dev:build` Stage 1 (build-time re-mount) |
| IN_DEVELOPMENT | inProgress | `/dev:build` Stage 5 start |
| TESTING | inProgress | `/dev:build` Stage 7 start |
| IN_PROGRESS (build done) | inProgress | `/dev:build` Stage 11 finish |
| REVIEW | devReview | `/dev:commit` Stage 1 |
| MERGE_CONFLICT | devReview (unchanged) | `/dev:commit` Stage 7 halt |
| BLOCKED | blocked | any stage's escalation |
| BLOCKED_ON_PLAN | readyForDev (unchanged) | `/dev:plan` Stage 6a (plan-blocker OPEN) |
| DONE | done | PR merge webhook (v2.3) |

The webhook that flips MC `done` on PR merge is v2.3 scope. In v2.2 the MC status stays at `devReview` after `/dev:commit` — human reviewer + merge close the loop manually.

## Two-gate security model

Security review runs TWICE with different thresholds:

- **`/dev:build` Stage 9 (build-time)** — Critical-only blocking. High/Medium/Low logged but non-blocking. Rapid dev iteration friendly.
- **`/dev:commit` Stage 3 (commit-time)** — Critical + High blocking. Medium warns. Low logged. Strict pre-PR gate.

Same `security-review` skill invocation with different `severity_threshold`. Build-deferred Highs surface at commit time; they either got fixed in dev iteration or now block.

## New v2.2 skills orchestrated

- `dev-stack-adaptive-implementation` — dynamic implementation guide; detects stack + infers repo patterns; writes idiomatic code + behavioral tests. Invoked at `/dev:build` Stages 5+6. Also invoked in fix-mode from both build's repair loop and commit's Stage 6 fix loop.
- `qa-greenfield-harness` — auto-bootstraps a deterministic per-stack test harness when `qa/quality-gates.md` is missing / Draft. Invoked at `/dev:build` Stage 4. NEVER prompts the user.
- `dev-stack-adaptive-code-review` — dynamic diff review; 7 dimensions × 4 severity tiers. Invoked at `/dev:commit` Stage 4.
- `tl-semantic-context-merge` — unit-level merge of code-context vs baseline. Invoked at `/dev:commit` Stage 7.
- `dev-pr-handoff` (slimmed) — composes `pr-summary.md` OR `escalation-<n>.md` content ONLY. No state transitions, no MC calls. Invoked at `/dev:commit` Stage 9 (PR body compose) or at any escalation point (content compose).

Retired: `dev-validation` (folded into `/dev:build` Stages 7-9), `/dev:pr` command (folded into `/dev:commit`), `/dev:validate` command (retired).

## Guardrails (from `references/loop-control.md`)

- Bounded fix loops: 3 focused fix attempts per finding, 2 broad re-runs per stage. Exceed → escalate.
- Escalation format: `dev/escalation-<n>.md` — chain of attempts, precise blocker, decision needed, recommendation, parallel work.
- Never merge, deploy, or approve.
- Never modify secrets or `.env` files.
- Never expand scope (touching unrelated modules or other repos → scope escalation first).
- Every material design choice → `DEC-###` in `dev/decisions.md` + append to `shared-context/decision-log.md`.
- Broadcast every state transition in chat as it happens; don't go dark.

## Sub-task rules (from v2.1, unchanged in v2.2)

- One repo per sub-task (per `subtask_repo` frontmatter).
- Parent's AC/BR/NFR/TS are the validation contract; sub-task's own AC/TS tabs are empty by design.
- E2E ACs spanning sub-tasks marked `deferred-to-e2e` — closed by the LAST sub-task to land (per parent's rollup Sub-tasks table's remaining-not-DONE count).
- Cross-sub-task hard deps → halt with escalation if the dep sub-task is not `done` on MC.
- One PR per sub-task per repo — never combine sub-tasks into a spanning PR.

## Report in chat

For each command run, emit progress broadcasts:

- On state transition: one-line broadcast `<prev> → <next>` before starting the work of that state
- On long-running phases (implement, validate, repair, semantic-merge): `↳` heartbeat sub-line
- On blocker: inline error/blocked block IN ADDITION to writing `dev/escalation-<n>.md` — never make the human open the markdown to see what broke
- On completion: closing headline — file paths, next command, and terminal-visible summary

## Completion criteria (per command)

**`/dev:build` complete** when Stage 11 finishes; local `IN_PROGRESS`, MC `inProgress`. `dev/local-runbook.md` written.

**`/dev:commit` complete** when Stage 10 (summary) finishes; local `REVIEW`, MC `devReview`. PR opened. `dev/pr-summary.md` is the PR body.

**Task delivered** when PR is merged (out of this loop's scope in v2.2 — human reviewer + merge closes it).

## Principles

- **Context is the source of truth.** Don't begin `/dev:build` until `/dev:plan` produced a decidable plan. A missing blocker resolution IS a blocker.
- **Two-gate security.** Fast at build, strict at commit. Same skill, two configs.
- **Stack-adaptive, not stack-hardcoded.** No per-stack playbooks — repo patterns are the source.
- **Semantic merge, not line merge.** Unit-level context merge on commit; git text-merge can't handle the graph.
- **Prove behaviour with evidence.** Acceptance-map rows must cite tests that actually run.
- **Bound the repair loops.** Focused fixes, narrow-then-broad, hard bounds, then escalate.
- **Stay in scope.** No cross-repo edits from a single sub-task; no unrelated refactors.
- **Persist everything.** Every stage writes its run log; any agent or human can resume.
- **Stay visible.** State transitions broadcast in chat; blockers inline; never go dark.
- **Escalate, don't guess.** Business, architecture, security, dependency, or bounds-exceeded → structured escalation. Escalating well is success.
- **Never overstep guardrails.** No merge, deploy, secret changes, scope expansion, disabled controls, or skipped hooks — without explicit human approval.
