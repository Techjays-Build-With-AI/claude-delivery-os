# Readiness, impact analysis, and implementation planning — RELOCATED

> **This content moved to `/dev:plan`.** The `feature-delivery-loop` skill no longer plans — it starts at branch creation and consumes the plan `/dev:plan` produced.

## Where the sections went

The five planning stages that used to live here are now `/dev:plan`'s job. If you're looking for the historical section, use the map below:

| Old §  | Old title | New home |
|--------|-----------|----------|
| §0a    | Pre-flight — MC status + local drift | [`plugins/dev/commands/references/plan/development-planning.md`](../../../commands/references/plan/development-planning.md) §3b |
| §0     | Planning gate (TL graph verify + auto-plan) | [`plugins/dev/commands/references/plan/code-context-readiness.md`](../../../commands/references/plan/code-context-readiness.md) §1a + §1b |
| §1     | Readiness validation checklist | [`plugins/dev/commands/references/plan/development-planning.md`](../../../commands/references/plan/development-planning.md) §3c |
| §1a    | Repository gate — brownfield vs project-zero | [`plugins/dev/commands/references/plan/development-planning.md`](../../../commands/references/plan/development-planning.md) §3c.i |
| §1b    | Test-harness gate | [`plugins/dev/commands/references/plan/development-planning.md`](../../../commands/references/plan/development-planning.md) §3c.ii |
| §2     | Impact analysis (12 dimensions) | [`plugins/dev/commands/references/plan/development-planning.md`](../../../commands/references/plan/development-planning.md) §3d |
| §3     | Implementation planning (dev-plan.md) | [`plugins/dev/commands/references/plan/development-planning.md`](../../../commands/references/plan/development-planning.md) §3e |

## What `/dev:build` still does (not in this file)

The `feature-delivery-loop` skill retains a **lightweight verification** at loop steps 1 – 3:

- **Step 1** — resolve the target (`Task-N`, `Feature-N`, `Subtask-N`, slug, folder, `FEAT-<AREA>-NN`) and **verify the plan exists**. Missing → *"Run `/dev:plan <target>` first"* and halt.
- **Step 2** — acquire the lock, read the parent BA files + this task's Implementation content + `/dev:plan`'s `dev-plan.md`.
- **Step 3** — cheap pre-flight (MC status + drift + cross-sub-task deps) in case things flipped between plan and build.

None of those write a plan — they consume it. See `SKILL.md` steps 1 – 3 for the exact instructions.

## Why the split

Before v2.1: `/dev:build` did readiness + impact + plan + implement + validate + review + PR inline. The loop was slow to start, planning went stale on long-running features, and multi-repo features had no clean way to split.

After v2.1: `/dev:plan` owns planning (across features, in parallel, with sub-task decomposition). `/dev:build` owns implementation (one task at a time, in one repo). Each stage runs just-in-time — plan runs when the developer picks up the task, build runs when the developer starts coding. Neither redoes the other's work; both refuse to run if the other's output is missing.

See the plan file — [docs/dev/dev-plan-command.md](../../../../docs/dev/dev-plan-command.md) — for the full architectural rationale and the sub-task file layout.
