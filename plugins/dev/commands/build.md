---
description: Run the full feature-delivery loop on an approved feature — validate readiness, analyse impact, plan, implement in an isolated branch/worktree, validate against acceptance criteria, repair actionable failures within retry limits, update delivery status and the feature tracker, and prepare a pull-request handoff. Pass a feature id/folder, or let it pick the next feature at READY_FOR_DEV. Never merges or deploys; escalates business, architecture, schema, security, dependency, and scope blockers.
argument-hint: "<FEAT-<AREA>-NN | context/features/<slug> | (blank = next READY_FOR_DEV)> [initiative=<name>] [repo=<path>] [mode=implement]"
---

# /dev:build

You are the entry point for the feature-delivery loop. Parse the arguments and **delegate the actual build to the `dev-agent` subagent**, which runs in its own context and does the context-heavy reading, implementation, validation, and tracking.

## 1. Parse arguments

`$ARGUMENTS` may contain:
- A **feature target** — a `FEAT-<AREA>-NN` id, a feature folder (`context/features/<slug>/`), or a slug. If omitted, the agent selects the next feature marked `READY_FOR_DEV` from `feature-index.md`.
- An optional **`initiative=<name>`** — scope the run to one work-batch (the `initiative` stamped by `/ba:features`). With a blank target, the agent picks the next `READY_FOR_DEV` feature **within that initiative** (ignoring other developers' batches); with an explicit target it just confirms the target belongs to that initiative. This is how a developer builds only their own scoping batch when `context/features/` holds many developers' features.
- An optional **`repo=`** path to the product repository to implement in (default: the current workspace / project repo).
- An optional **`mode=`** (`implement` default; `plan-only` stops after the dev plan).

If the target doesn't resolve, say so and ask for a valid one rather than guessing. If there's no `context/features/` at all, tell the user the BA feature breakdown (`/ba:features`) must run first, and offer to build against a path they point you to. If the chosen feature isn't yet planned by the TL (no page/endpoint/entity graph), the agent's **planning gate auto-plans it** via `tl-feature-planning` before building — it only escalates when the TL plugin is unavailable or planning can't complete.

## 2. Delegate

Invoke the **dev-agent** subagent with the feature target. Pass it this instruction:

> Run the full feature-delivery loop for `<target>` using the `feature-delivery-loop` skill (and its `dev-validation`, `dev-code-review`, `dev-pr-handoff` sub-skills). Select the feature (or the next `READY_FOR_DEV` one) and acquire its lock in `dev/delivery-status.md`. **If an `initiative=<name>` was given, restrict selection to features whose `feature.md`/index `initiative` matches** — with a blank target pick the next `READY_FOR_DEV` feature within that initiative only, and with an explicit target confirm it belongs to that initiative (if not, say so and stop rather than building the wrong batch). Read the BA feature folder and the TL context units it maps to. **Run the planning gate first** (readiness-and-planning §0): verify every page/endpoint/entity the feature declares resolves to a real TL unit and is linked to this `FEAT-id`; if it isn't planned or is only partially planned, auto-plan it by delegating to the `tl-agent` subagent with the `tl-feature-planning` instruction on this one feature folder (or run that skill directly if delegation isn't available), then re-verify and note the auto-plan (units created/reused, `DEC-###`, TL open questions) in the summary — escalate only if TL planning is unavailable (→ `BLOCKED`, tell the user to run `/tl:plan`) or can't complete (carry the TL's blocking open questions up). Then validate readiness — if a critical gap exists (no acceptance criteria, unresolved blocking open question, unavailable/unmocked dependency, already-broken base build, missing tooling), set `BLOCKED`, write `dev/escalation-<n>.md`, and stop. Otherwise analyse code-level impact (`dev/impacted-components.md`), write the technical plan (`dev/dev-plan.md`), create the branch `feature/FEAT-<AREA>-NN-<slug>` (never on main/master/production), and implement scoped changes with tests, following `coding-standards.md` and logging `DEC-###` decisions. Run `dev-validation` and build `dev/acceptance-map.md`; repair actionable failures within 3 focused attempts / 2 broad cycles, logging each in `dev/implementation-log.md`; run `dev-code-review` (quality + security). Update `dev/delivery-status.md`, the BA `status.md`/`feature-index.md` (state mapped per loop-control), and `dev-output/feature-tracker.md`. When all mandatory completion criteria hold, run `dev-pr-handoff` to write `dev/pr-summary.md` and move to `HUMAN_REVIEW`. Do not merge or deploy. Escalate business, architecture, schema-risk, security, dependency, scope, and stuck-retry situations instead of guessing. Return the feature's new state, what you implemented, the validation + acceptance summary, decisions logged, blockers, and links to `dev/pr-summary.md` (or the escalation) and the tracker.
>
> Repository: `<repo or current workspace>` · Mode: `<mode>`

## 3. Surface the result

When the agent returns, present its **summary**: the feature and its new loop state, files/units implemented, the validation summary and the acceptance-criteria pass/fail table, `DEC-###` decisions logged, any blockers/escalations (with the decision needed), and links to `dev/pr-summary.md` (or `dev/escalation-<n>.md`) and `dev-output/feature-tracker.md`. Keep it tight — the detail lives in the files. If the feature is blocked, lead with the decision the human needs to make.
