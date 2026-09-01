---
description: Commit a built task through the full 10-stage commit loop — strict security review (Critical + High blocking, vs /dev:build's Critical-only), dynamic code review via dev-stack-adaptive-code-review (Blocker + Major blocking), final acceptance-map re-verification (regression + last-sub-task E2E), bounded fix loop, semantic-context-merge against baseline via tl-semantic-context-merge (unit-level merge, not text-level), push branch, raise PR with dev/pr-summary.md, print terminal summary. State transitions to REVIEW locally + devReview in MC on start; stays there on success (PR-merge webhook flips to DONE / done — future). Sub-task commits work in the sub-task's repo only. Refuses to run without a completed /dev:build.
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | features/<slug>/subtask/<repo> | FEAT-<AREA>-NN | (blank = task that finished /dev:build most recently)> [initiative=<name>] [--resume] [--skip-security] [--force-context-merge=ours] [--force-push]"
---

# /dev:commit

You are the entry point for the 10-stage commit loop. **Orchestrator only** — parses args, resolves identity, verifies `/dev:build` completed, then routes each stage to its reference file under `plugins/dev/commands/references/commit/`. Do NOT paraphrase the stage files' instructions — `Read` them and execute verbatim.

Read the **`delivery-os-conventions`** skill first if it's not in context — the v2.2 loop-control state model + MC status mapping. Then read the task's `dev/build-run.md`.

**The single invariant:** `/dev:commit` runs on a completed `/dev:build` or refuses. Local state must be `IN_PROGRESS` (build-complete state) when this command starts.

---

## 1. Parse arguments

`$ARGUMENTS` may contain:

**Task target** (required, unless blank for "most recently built"):
- MC task number: `Task-N`, `Feature-N`, `Subtask-N`
- Local feature slug: `supplier-onboarding`
- Local feature folder: `features/supplier-onboarding`
- Sub-task folder: `features/supplier-onboarding/subtask/backend`
- Internal id: `FEAT-<AREA>-NN`
- Blank: pick most recent task whose `status.md` has `ready_for_dev_commit: true`

**Flags:**
- `initiative=<name>` — scope selection
- `--resume` — continue from last completed stage per `dev/commit-run.md`
- `--skip-security` — bypass Stage 3 (requires `SECURITY_REVIEW_OVERRIDE` env + audited reason)
- `--force-context-merge=ours` — auto-resolve Stage 7 conflicts to our-side (emergency)
- `--force-push` — allow `git push --force-with-lease` (rare)

## 2. Stage 0 — Identity resolution + branch verification (hard gate)

Same 4-way resolution as `/dev:plan` Stage 0 / `/dev:build` Stage 0 — see `plugins/dev/commands/plan.md` §2a. Determine `task_kind` (parent-alone or sub-task) and canonical `(feature_id, task_object_id, task_number, task_folder)`.

**Verify `/dev:build` completed.** Check `status.md`:
- `current_state: IN_PROGRESS`
- `ready_for_dev_commit: true`
- `branch:` field non-empty

Any missing → halt with "run /dev:build first" message.

**Verify branch is checked out** in the target repo: `git rev-parse --abbrev-ref HEAD` matches the branch recorded in `status.md`. Mismatch → halt with "checkout the feature branch first: `git checkout <branch>`".

**Verify no uncommitted changes** (`git status --porcelain` empty) UNLESS `--resume` and we're in Stage 7 halt state — in which case pending manual edits are allowed on `dev/context-merge-conflicts.md` and touched context files.

## 3. Stage 1 — Acquire lock + flip status

- Write owner into `status.md` (agent id)
- Local: `IN_PROGRESS → REVIEW` (broadcast)
- MC: `inProgress → devReview` via `task-mcp.update_task_status`
- Read parent BA files (`feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`) — validation contract; passed to Stages 4 + 5
- Read `dev/build-run.md` (Stage 10's `context_units_updated:` list, Stage 9's build-time security findings)
- Read `dev/acceptance-map.md` (build-time results, feeds Stage 5)
- Read `dev/implementation-log.md` (detected_stack + inferred_patterns, feeds Stage 4)
- Record start in `dev/commit-run.md`

## 4. Stage 2 — Base branch selection

Resolve base from `.jetrix/project.json`:

- Sub-task with `<repo>` frontmatter → find matching `apps[].name`; use `env_branches.dev` (default: `develop`)
- Parent-alone → primary product repo's `env_branches.dev`

If the branch in `.jetrix/project.json` is `main` / `master` / `staging` / `production` — refuse (branch-protection defaults). Require explicit override.

Run `git fetch <remote>` and check the branch is fresh:

- `git log HEAD..<remote>/<base>` — must be empty (branch is descendant of base). Otherwise halt: "rebase against <base> and re-run".
- Confirm base build is green in target repo (best-effort: read the last CI status via `gh` if available).

Log to `commit-run.md`.

## 5. Route to Stages 3–9

Read each stage's reference file and execute verbatim. Fix loop is inline routing between Stages 3-5 (see Stage 6 file for the loop mechanics).

### Stage 3 — Strict security review

**Read** `plugins/dev/commands/references/commit/stage-3-security.md` and execute verbatim. Invokes Claude Code's `security-review` skill at Critical+High threshold. Any finding routes to Stage 6 fix loop.

### Stage 4 — Dynamic code review

**Read** `plugins/dev/commands/references/commit/stage-4-code-review.md` and execute verbatim. Invokes `dev-stack-adaptive-code-review` skill. Blocker+Major findings route to Stage 6 fix loop.

### Stage 5 — Final acceptance-map verification

**Read** `plugins/dev/commands/references/commit/stage-5-acceptance.md` and execute verbatim. Re-runs every acceptance-map row's test; deferred-to-e2e resolves if this is the last sub-task landing. Regression routes to Stage 6 fix loop.

### Stage 6 — Bounded fix loop

**Read** `plugins/dev/commands/references/commit/stage-6-fix-loop.md`. Not a standalone stage — invoked from Stages 3, 4, or 5 when findings block. After each fix batch, upstream stages re-run in order. Bounds exceeded → escalation + halt.

### Stage 7 — Semantic context merge

**Read** `plugins/dev/commands/references/commit/stage-7-semantic-merge.md` and execute verbatim. Delegates to `tl-semantic-context-merge` skill. Halts cleanly on conflict with `dev/context-merge-conflicts.md` for human resolution.

### Stage 8 — Push the branch

**Read** `plugins/dev/commands/references/commit/stage-8-9-push-pr.md` §Stage 8 and execute verbatim.

### Stage 9 — Raise the PR

**Read** `plugins/dev/commands/references/commit/stage-8-9-push-pr.md` §Stage 9 and execute verbatim. PR body = `dev/pr-summary.md`.

## 6. Stage 10 — Report summary

In-terminal summary:

```
✓ /dev:commit FEAT-SUP-001-1 complete

Task:          Subtask-7 (backend)  ·  Feature-4 Supplier Onboarding
MC parent:     https://mission-control.techjays.com/task/6a94fe0ebc48d4e7d1cab15b
MC sub-task:   https://mission-control.techjays.com/task/6b72a1c48d4e7d1cab2c7
PR:            https://github.com/acme/acme-backend/pull/247

Branch:        feature/FEAT-SUP-001-supplier-onboarding-backend  →  develop
Security:      ✓ 0 Critical, 0 High  (2 Medium warnings surfaced in PR body)
Code review:   ✓ 0 Blocker, 0 Major  (3 Minor follow-ups in PR body)
Acceptance:    ✓ 9/9 verified at commit-time (3 deferred-to-e2e)
Context merge: 3 units merged clean · 4 base units carried forward · 0 conflicts
Push:          ✓ 9 commits pushed to origin
PR:            ✓ opened by /dev:commit

Local state:   REVIEW           (awaiting human review)
MC status:     devReview        (flips to done on PR-merge webhook — future)

Local runbook: features/supplier-onboarding/subtask/backend/dev/local-runbook.md
PR summary:    features/supplier-onboarding/dev/backend-pr-summary.md

Next:
  1. Reviewer reviews PR-247   (link above)
  2. Track task progress on MC (sub-task link above)
  3. On merge, MC status flips to `done` automatically (webhook — v2.3)
```

**Navigation URL sources (v2.3.17 — task-mcp is the URL source of truth):**

- **MC parent** — call `task-mcp.get_task_by_id_or_number(solution_id, feature.md `jetrix_task_object_id`)`; use `.view_url` from the response. task-mcp constructs the URL server-side using its own `mission_control_ui_url` env var.
- **MC sub-task** — same pattern: `get_task_by_id_or_number(solution_id, subtask/<repo>/status.md `jetrix_subtask_object_id`)`; use `.view_url`.
- **PR** — from `dev/<repo>-commit-run.md` stage-9's `pr_url` (written by Stage 9)

Do NOT construct MC URLs locally from `.jetrix/project.json` `mission_control_ui_url` — task-mcp's own env var is the source of truth and the two may drift. task-mcp's returned `view_url` is guaranteed correct.

All three URLs are must-haves in the terminal summary — the whole point of this stage is to give the developer + reviewer clickable jumps to every relevant surface. If any URL cannot be resolved via task-mcp response, print `(not resolvable from MC)` inline, do NOT invent a URL.

No file writes at Stage 10 — pr-summary + commit-run + delivery-status are already written by earlier stages.

## 7. Failure surfaces

- **Any stage BLOCKED** (Stage 6 bounds exceeded) → local `BLOCKED`, MC `blocked`, `dev/escalation-<n>.md`, halt
- **Stage 7 semantic-merge conflict** → local `MERGE_CONFLICT`, MC stays `devReview`, `dev/context-merge-conflicts.md`, halt
- **Stage 8 push rejected** → local `REVIEW` (unchanged), MC stays `devReview`, halt with git error verbatim
- **Stage 9 PR creation failed** → local `REVIEW` (unchanged), MC stays `devReview`, halt with `gh` error verbatim
- **`/dev:commit` on task at `PLANNED` or `IN_PLANNING`** → refuse (§2 hard gate). Route to `/dev:build`

## 8. Guardrails

- Never invent behaviour not in `implementation.md` or resulting from a Stage 6 fix
- Never bypass Stage 3 security review without the `SECURITY_REVIEW_OVERRIDE` env
- Never bypass Stage 7 semantic merge without `--force-context-merge=ours`
- Never `git push --force` without `--force-push`
- Never `--no-verify` on push
- Never mark MC status `done` here — reserved for the PR-merge webhook
- Never modify secrets or `.env` files
- Never rebase automatically — halt and instruct if branch is behind base
- Every material design choice → `DEC-###` in `dev/decisions.md`
- Never move MC status to `blocked` for a Stage 7 conflict — that's `MERGE_CONFLICT` (local only) awaiting human input
