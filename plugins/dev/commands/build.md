---
description: Build an already-planned task through the full feature-delivery loop — verify the plan exists, mount context, pre-flight, implement in an isolated branch/worktree, validate against acceptance criteria, repair actionable failures within retry limits, update delivery status and the feature tracker, and prepare a pull-request handoff. Accepts any task identifier — MC task number (Task-N / Feature-N / Subtask-N), local feature slug or folder path, sub-task folder path, internal FEAT-<AREA>-NN id, or blank for the next task at PLANNED. Refuses to run if the plan is missing — routes the user to `/dev:plan <task-ref>` first. Never merges or deploys; escalates business, architecture, schema, security, dependency, and scope blockers.
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | features/<slug>/subtask/<repo> | FEAT-<AREA>-NN | (blank = next PLANNED task)> [initiative=<name>] [repo=<path>]"
---

# /dev:build

You are the entry point for building one already-planned task. Parse the arguments and **delegate the build to the `dev-agent` subagent**, which runs the `feature-delivery-loop` skill in its own context and does the context-heavy reading, implementation, validation, and tracking.

**Plan is a hard prerequisite.** If `/dev:plan` hasn't run for this task, `/dev:build` refuses and tells the user which command to run first. `/dev:build` does not plan — its loop starts at branch creation.

## 1. Parse arguments

`$ARGUMENTS` may contain:

- A **task target** — any of:
  - MC task number: `Task-N`, `Feature-N`, `Subtask-N`
  - Local feature slug: `supplier-onboarding`
  - Local feature folder: `features/supplier-onboarding`
  - Sub-task folder: `features/supplier-onboarding/subtask/backend`
  - Internal id: `FEAT-<AREA>-NN`
  - Blank: pick the next task at `PLANNED` from `features/tracker.md`
- An optional **`initiative=<name>`** — scope selection to one work-batch (the `initiative` stamped by `/ba:features`). With a blank target, pick the next `PLANNED` task within that initiative; with an explicit target, confirm it belongs to that initiative before building.
- An optional **`repo=<path>`** — override the resolved repo. Rare; useful when the workspace's repo mapping is stale and you want to build against a local checkout somewhere else. Not passed through to `/dev:plan`.

## 2. Resolve the target and verify the plan exists

Use the same Stage 0 identity-resolution logic `/dev:plan` uses (see `plugins/dev/commands/plan.md` §2). Resolve any accepted input form to a canonical `(feature_id, task_object_id, task_number, task_folder, task_kind)` where `task_kind` is `parent` or `subtask`.

**Determine task kind and its folder:**

- Target is `Subtask-N` OR `features/<slug>/subtask/<repo>/` → `task_kind = subtask`; task folder = `features/<slug>/subtask/<repo>/`.
- Otherwise → `task_kind = parent`; task folder = `features/<slug>/`.

**Verify the plan exists (hard gate).** Check for these files under the task folder:

- Parent-alone: `dev/dev-plan.md`, `dev/impacted-components.md`, `dev/delivery-status.md`.
- Sub-task: `dev/dev-plan.md`, `dev/impacted-components.md`, `dev/delivery-status.md` (inside `subtask/<repo>/dev/`).

If any of the three is missing OR `delivery-status.md`'s `current_state` is not `PLANNED` or a later state (`IN_PROGRESS` / `REVIEW` etc for resume) → halt with:

```
✗ No plan for <target>. Run:
    /dev:plan <target>
  Then re-run:
    /dev:build <target>
```

Do not attempt to plan yourself.

If the target doesn't resolve → tell the user and ask for a valid one. If there's no `features/` at all → tell the user the BA feature breakdown (`/ba:features`) must run first.

## 3. Delegate to the dev-agent

Invoke the **dev-agent** subagent with the resolved target. Pass this instruction:

> Run the feature-delivery loop for `<task_folder>` (`task_kind: <parent|subtask>`) using the `feature-delivery-loop` skill (and its `dev-validation`, `dev-code-review`, `dev-pr-handoff` sub-skills). The task is already planned by `/dev:plan` — `dev/dev-plan.md`, `dev/impacted-components.md`, and `dev/delivery-status.md` exist under the task folder with `current_state: PLANNED` (or later, for resume runs).
>
> Acquire the owner lock in the task's `dev/delivery-status.md`. **If an `initiative=<name>` was given**, confirm the task belongs to that initiative before building (parent's `feature.md` frontmatter `initiative` matches, or the sub-task's parent does); if not, say so and stop rather than building the wrong batch.
>
> Read the parent feature's BA files (`feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md`) — these carry the validation contract regardless of task kind (sub-tasks read the parent's tabs since their own AC/TS tabs are empty by design).
>
> Read the task's Implementation content:
> - `task_kind = parent`: read `features/<slug>/tl-plan.md` (detailed mode).
> - `task_kind = subtask`: read `features/<slug>/subtask/<repo>/description.md` + `implementation.md`; also read `features/<slug>/tl-plan.md` (parent rollup) to see cross-sub-task dependencies in its Sub-tasks table.
>
> Read the dev-plan `/dev:plan` wrote (`dev/dev-plan.md`) and use it as your build script — ordered steps, files to touch, API/schema changes, test strategy. Do not re-plan; if the plan looks stale (unit files moved since it was written), stop and tell the user to run `/dev:plan <target> --resume`.
>
> Run pre-flight (loop step 3 in the skill): MC status check, local drift check, and — for a sub-task — cross-sub-task dependency check against the parent's rollup Sub-tasks table. Halt cleanly if MC status is `blocked`; note drift and continue; escalate if a hard dependency isn't `DONE`.
>
> Resolve the target repo from `.jetrix/cache/repolocation.json`: for a parent-alone task, the workspace's primary product repo; for a sub-task, the repo whose slug matches this sub-task's `subtask_repo` frontmatter. If the resolved repo is `SKIPPED`, escalate.
>
> Create the isolated branch/worktree in the target repo: `feature/FEAT-<AREA>-NN-<slug>` for parent-alone; `feature/FEAT-<AREA>-NN-<slug>-<repo>` for a sub-task. Never on `main` / `master` / `staging` / `production`. Confirm the base build is green before touching anything.
>
> Implement scoped changes following `coding-standards.md`, log `DEC-###` decisions, and add or update tests with the code. Stay inside the sub-task's repo — never touch another repo's files without a scope escalation.
>
> Run `dev-validation` and build `dev/acceptance-map.md` — map each parent AC that THIS task can validate at its layer to a validation method, result, and evidence. Mark E2E ACs `deferred-to-e2e` if they span sub-tasks and can only be closed by the last sub-task to land.
>
> For an **AI-bearing feature**, also materialize, run, and inspect the TL's `EVAL-<AREA>-NN` verifiers under `features/<slug>/evals/` (via the `eval-engineering` skill), feeding pass/fail into the acceptance map and treating a reward-hacked pass as a failure.
>
> Repair actionable failures within 3 focused attempts / 2 broad cycles, logging each in `dev/implementation-log.md`. Run `dev-code-review` (quality + security). Update `dev/delivery-status.md`, the task's `status.md` (parent's or sub-task's), the parent's `feature-index.md` (state mapped per loop-control), and `features/tracker.md`.
>
> When all mandatory completion criteria hold, run `dev-pr-handoff` to write `dev/pr-summary.md` and move to `HUMAN_REVIEW`. **One PR per task, one repo per PR** — sub-tasks each get their own PR in their own repo; cross-repo integration is coordinated by the parent's tracker.
>
> Do NOT merge, deploy, modify secrets, or expand scope without human approval. Escalate business, architecture, schema-risk, security, dependency, cross-sub-task, and stuck-retry situations instead of guessing.
>
> Return the task's new state, what you implemented, the validation + acceptance summary, decisions logged, blockers, and links to `dev/pr-summary.md` (or the escalation) and the tracker.
>
> Target folder: `<task_folder>` · Task kind: `<parent|subtask>` · Repo override: `<repo path or none>`

## 4. Surface the result

When the agent returns, present its **summary**: the task and its new loop state, files/units implemented, the validation summary and the acceptance-criteria pass/fail table (including any `deferred-to-e2e` for sub-tasks), `DEC-###` decisions logged, any blockers/escalations (with the decision needed), and links to `dev/pr-summary.md` (or `dev/escalation-<n>.md`), the parent's `status.md`, and `features/tracker.md`. Keep it tight — the detail lives in the files. If the task is blocked, lead with the decision the human needs to make.
