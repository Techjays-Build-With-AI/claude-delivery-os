---
name: feature-delivery-loop
description: Autonomously deliver one already-planned task (a parent feature or a sub-task) through a controlled, state-driven loop — implement, validate, fix, track, and prepare for review — rather than a one-shot code dump. Use whenever the user asks to "build/implement a task", "run the delivery loop", "develop FEAT-…", "take this feature to a PR", or hand an already-planned task to development. Point it at one task (a Task-N / Feature-N / Subtask-N MC id, a FEAT-<AREA>-NN, a features/<slug>/ folder, or a sub-task's subtask/<repo>/ path) or let it pick the next task at PLANNED. It reads the BA feature breakdown, the TL technical context graph, and the /dev:plan-generated dev-plan; works in an isolated branch/worktree in the task's repo; implements scoped changes with tests; runs validation and maps results to acceptance criteria; repairs actionable failures within retry limits; moves the task through an explicit state model; updates delivery status and the feature tracker; and prepares a pull-request handoff. Refuses to run if the plan is missing — routes the user to /dev:plan first. It escalates business, architecture, schema, security, dependency, and scope blockers instead of guessing, and never merges, deploys, modifies secrets, or expands scope without human approval. It orchestrates the dev-validation, dev-code-review, and dev-pr-handoff skills. Re-run it to continue a task, respond to review feedback, or pick up after an escalation is resolved.
---

# Feature Delivery Loop (planned task → validated, review-ready implementation)

You are turning an **already-planned task** — either a parent feature (parent-alone) or one sub-task of a split feature — into working, validated code and a clean review handoff. Planning (readiness gate, impact analysis, dev-plan document) is `/dev:plan`'s job and has already run; you refuse to start if the plan isn't there. This is an **execution and verification loop**, not a single code-generation call: you implement, you prove, you fix, you track, and you either reach a review-ready state or you escalate — you never declare a task done because code exists.

The defining behaviour of this skill is the **state-driven loop with hard guardrails**. Every feature moves through explicit states; every meaningful change is validated; every acceptance criterion is backed by evidence; repairs are bounded; and ambiguity, risk, and scope decisions are escalated rather than guessed. You are the **build authority** for the feature's scope, but "build authority" is not "licence to decide the business" — where the context is silent on something that changes behaviour (a business rule, an auth model, a schema risk, an integration contract), you raise a blocker, not a guess.

## Operating contract

Read the **`delivery-os-conventions`** contract first if it isn't in context — the workspace layout (including §v2.1 sub-task tree), the frontmatter standard, the stable-ID rules, the source-citation form, and the controlled vocabulary. Your **inputs** are published upstream work you consume and never regenerate:

- **PLAN prerequisite — `/dev:plan` must have run for this task.** For a parent-alone target: `features/<slug>/dev/dev-plan.md` + `impacted-components.md` + `delivery-status.md` must exist with `current_state: PLANNED`. For a sub-task target: same three files under `features/<slug>/subtask/<repo>/dev/`. If missing → halt with *"Run `/dev:plan <task-ref>` first"* and stop. Do NOT re-plan yourself; that's `/dev:plan`'s job.
- BA feature folder `features/<slug>/` — `feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md`, `status.md`. These carry the parent feature's validation contract; for a sub-task target you read the PARENT's tabs as the validation source (sub-task's AC + TS tabs are deliberately empty).
- **`features/<slug>/tl-plan.md`** — TL's parent Implementation content composed by `/dev:plan` Stage 2. In rollup mode when the feature was split; in detailed mode when parent-alone. For a sub-task target: also read `features/<slug>/subtask/<repo>/implementation.md` — the sub-task's own detailed 5-section spec. This is the **primary buildable input** for a sub-task run.
- **`features/<slug>/subtask/<repo>/description.md`** — for a sub-task target, the business flow narrative that describes what THIS sub-task delivers. Read to ground the implementation in the right business framing.
- **`features/<slug>/dev/dev-plan.md`** (parent-alone) OR **`features/<slug>/subtask/<repo>/dev/dev-plan.md`** (sub-task) — the ordered implementation steps + files + API/schema changes + test strategy `/dev:plan` wrote. This is your build script.
- TL context graph — the `PAGE-/EP-/ENT-<AREA>-NN` unit files this task's Implementation cites, the three layer indexes, and the `DEC-###` decisions in `shared-context/decision-log.md`. The graph lives **per-repo** at `<repo>/context/code-context/{frontend|backend|database}/` — travels with the code via `git`. **To find the target repo's absolute path**, read `.jetrix/cache/repolocation.json` — for a sub-task, the `subtask_repo` frontmatter tells you which repo key to look up. If it's `SKIPPED`, halt with an escalation.
- `shared-context/` (actors, systems, glossary, decisions) and the BA registers in `ba/` (data, integration, workflow, business-rule) for the rules your code must honour.
- The **product repository** you implement in — its `coding-standards.md`/`architecture.md` (from `shared-context/` or the repo), its test/lint/build tooling, and its git state. For a sub-task, you work in ONLY that sub-task's repo — never touch another repo's files.

You **write and update** the dev context for the target task. Two layouts depending on whether the target is a parent-alone feature or a sub-task:

**Parent-alone target** — writes under `features/<slug>/dev/`:

```text
features/<slug>/
  feature.md ... open-questions.md  status.md                # BA (input, read-only)
  tl-plan.md                                                  # TL (input, from /dev:plan Stage 2 detailed mode)
  dev/                                                        # /dev:plan Stage 3 created these; you update them
    plan-run.md              # /dev:plan's stage log — you read (may append your own resume notes)
    task-decision.md         # /dev:plan's decision log — read-only
    dev-plan.md              # /dev:plan wrote it — read as your build script
    impacted-components.md   # /dev:plan wrote it — read to know what you touch
    delivery-status.md       # you update state IN_PLANNING → IN_DEVELOPMENT → ... → HUMAN_REVIEW
    acceptance-map.md        # NEW — you write acceptance criterion → validation → result → evidence
    implementation-log.md    # NEW — per-run step / validation / failure / next-action log
    decisions.md             # NEW — technical decisions (also appended to shared-context/decision-log.md)
    pr-summary.md            # NEW at PR time — the PR / review handoff (dev-pr-handoff writes)
    escalation-<n>.md        # NEW when BLOCKED — structured blocker notes
```

**Sub-task target** — writes under `features/<slug>/subtask/<repo>/dev/`:

```text
features/<slug>/
  feature.md ... open-questions.md                            # BA (parent's tabs — READ for validation contract)
  tl-plan.md                                                  # parent's rollup — read for cross-sub-task view
  subtask/
    task-decision.md                                          # /dev:plan's split log — read-only
    <repo>/                                                   # e.g. backend/, frontend/, mobile/
      description.md         # sub-task's Description tab — read for framing
      implementation.md      # sub-task's Implementation tab — READ as your buildable spec (5-section detailed)
      status.md              # sub-task status (mirrors delivery-status current_state)
      dev/                                                    # /dev:plan Stage 3 created these; you update them
        dev-plan.md          # sub-task's dev-plan — read as your build script
        impacted-components.md
        delivery-status.md
        acceptance-map.md    # NEW — parent AC scoped to THIS sub-task's evidence
        implementation-log.md
        decisions.md
        pr-summary.md        # NEW at PR time
        escalation-<n>.md    # NEW when BLOCKED
features/tracker.md                                           # cross-feature delivery dashboard
```

**Sub-task scoping rules:**
- You work in ONE repo — the sub-task's `subtask_repo` from frontmatter. Never touch another repo's files.
- You read the PARENT's AC/BR/NFRs/TS for the validation contract. Sub-task's own AC/TS tabs are empty by design.
- Your `acceptance-map.md` covers parent AC that THIS sub-task can validate at its layer. E2E AC that span sub-tasks are marked `deferred-to-e2e` and only closable by the LAST sub-task to land (per its `/dev:plan`'s dev-plan.md).
- Cross-sub-task dependencies (e.g. "this frontend sub-task waits on backend's endpoint") are honoured — check the parent's tl-plan.md rollup Sub-tasks table's `Depends on` column before starting.

Every file follows the exact schema in **`references/dev-context-templates.md`**. Keep the frontmatter (`produced_by: dev`) on every file. Sub-task files also carry `subtask_number` + `subtask_repo` in frontmatter (see `delivery-os-conventions` §v2.1).

## The loop

Follow the state model, retry limits, permission/scope guardrails, escalation rules, and the state → BA-vocabulary mapping in **`references/loop-control.md`**. Delegate validation to **`dev-validation`**, self-review and the security pass to **`dev-code-review`**, and the PR/escalation handoff to **`dev-pr-handoff`**. For an **applied-AI feature**, follow the eval materialize/run/inspect method in **`references/eval-runner.md`** (and the core **`eval-engineering`** skill) to run the `EVAL-<AREA>-NN` verifiers the TL designed under `features/<slug>/evals/`.

**Planning (readiness gate, impact analysis, dev-plan writing) is `/dev:plan`'s job — not this skill's.** The loop starts at branch creation and assumes the plan artifacts exist. `references/readiness-and-planning.md` has been trimmed to §loop-control content only; the planning stages moved to `plugins/dev/commands/references/plan/`.

**Report progress as you go — don't go dark until the end.** Every time the task changes state, emit the one-line progress broadcast defined in `references/loop-control.md` ("Progress broadcasts") *before* you start the work of that state, and drop a short `↳` heartbeat sub-line whenever you enter a distinct phase of a long-running state (implementation, validation, repair). When you set `BLOCKED`, print the inline error/blocked block from that same reference *in addition to* writing the escalation file — never make the human open the markdown to learn what broke.

### 1. Resolve the target and verify the plan exists
Take the target from the user (any of: `Task-N` / `Feature-N` / `Subtask-N` MC number, `FEAT-<AREA>-NN`, `features/<slug>/` folder, `features/<slug>/subtask/<repo>/` sub-task folder, or a bare slug), or — if none is given — pick the next task at `PLANNED` from `features/tracker.md`. Use the same Stage 0 identity-resolution logic `/dev:plan` uses (see `plugins/dev/commands/plan.md` §2) to resolve to a canonical `(feature_id, task_object_id, task_number, task_folder)`.

If the target is a `Subtask-N` OR a `features/<slug>/subtask/<repo>/` folder → the task is a **sub-task** in the `<repo>` repo. Otherwise it's the **parent** feature (parent-alone).

**Verify the plan exists (hard gate):**

- Parent-alone target: `features/<slug>/dev/dev-plan.md` MUST exist AND `delivery-status.md` MUST have `current_state: PLANNED`.
- Sub-task target: same three files under `features/<slug>/subtask/<repo>/dev/`.

Missing → halt with:

```
✗ No plan for <target>. Run /dev:plan <target> first, then re-run /dev:build.
```

Never re-plan yourself. If a Stage 1 or Stage 2 outcome from `/dev:plan` looks stale (unit files moved since the plan was written), tell the user to re-run `/dev:plan <target> --resume` and stop.

### 2. Acquire the lock and mount the plan
Write your owner into the task's `delivery-status.md` so another agent won't take the same task. Set state `IN_PLANNING` **and broadcast the transition** (`PLANNED → IN_PLANNING`). "IN_PLANNING" here means "mounting the plan and confirming pre-flight," not authoring a new plan.

Read:
- The parent's BA files (`feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md`) — the validation contract.
- The target's Implementation content:
  - Parent-alone → `features/<slug>/tl-plan.md` (detailed mode).
  - Sub-task → `features/<slug>/subtask/<repo>/description.md` + `implementation.md`; also `features/<slug>/tl-plan.md` (parent rollup) to see cross-sub-task Sub-tasks table for dependencies.
- The dev-plan `/dev:plan` wrote: `dev/dev-plan.md` (parent) OR `subtask/<repo>/dev/dev-plan.md` (sub-task).
- The `impacted-components.md` for THIS task.
- TL units this task touches — the code-context tree in THIS task's repo only.

Record which sources you consulted in `implementation-log.md`. Do not begin implementation until you can state what "done" is in terms of the acceptance criteria.

### 3. Pre-flight — MC status + drift + cross-sub-task deps
Cheap re-checks in case things flipped between `/dev:plan` and now:

- **MC status** — fetch this task's MC status; if `blocked` on MC → halt cleanly, print the block reason.
- **Local drift** — invoke the shared drift helper for this task's local files. If drift and the user's not around, note in run summary and continue.
- **Cross-sub-task deps** (sub-task target only) — read the parent's `tl-plan.md` Sub-tasks table. For each row in `Depends on`, check that sub-task's `delivery-status.md` `current_state`. If any dependency is not `DONE` and this task's own dev-plan says it's a hard blocker → halt with an escalation naming the blocker sub-task. If it's a soft dependency (e.g. mock the endpoint), note in the log and continue.

### 4. Create the isolated environment (in the task's repo)
Resolve the target repo:
- Parent-alone → the workspace's primary product repo (per `.jetrix/cache/repolocation.json` — a workspace with one app has one primary).
- Sub-task → the repo whose slug matches this sub-task's `subtask_repo` frontmatter.

If the resolved repo is `SKIPPED` in `repolocation.json` → halt with an escalation.

Create the branch or worktree in that repo:
- Parent-alone → `feature/FEAT-<AREA>-NN-<slug>`
- Sub-task → `feature/FEAT-<AREA>-NN-<slug>-<repo>` (e.g. `feature/FEAT-SUP-001-supplier-onboarding-backend`)

**Never** commit changes directly to `main`, `master`, `staging`, or `production`. Confirm the working tree is clean and the base build is green before you change anything (a pre-existing broken build is an escalation, not your bug to silently fix). Write the branch name into `delivery-status.md`.

### 5. Implement (state IN_DEVELOPMENT — → broadcast the transition)
Execute the ordered implementation steps from your dev-plan.md. Make scoped changes that follow `coding-standards.md`, reuse existing patterns and abstractions, avoid unnecessary refactoring, keep within the approved task scope, and add or update tests **with** the code. Maintain backward compatibility unless the task explicitly requires a break (and if it does, that break is a decision to log and likely to escalate). Log material technical decisions to `dev/decisions.md` and append a `DEC-###` row to `shared-context/decision-log.md`. Stay inside the scope boundary in `references/loop-control.md`: touching an unrelated module — including files in OTHER repos when working a sub-task — requires a scope escalation first.

### 6. Validate (state TESTING — → broadcast the transition)
Invoke **`dev-validation`**: run the applicable suite (lint, format, type-check, unit, integration, API-contract, e2e, build, migration validation, security scan, dependency check, plus any task-specific acceptance tests), record results in `dev/implementation-log.md`, then build `dev/acceptance-map.md` mapping each parent AC that THIS task can validate to a validation method, result, and evidence file. **Sub-task:** E2E ACs that span sub-tasks are marked `deferred-to-e2e` here — closable only by the LAST sub-task to land per its own dev-plan. Passing unit tests alone is **not** completion — the acceptance map is.

**Applied-AI features — run and inspect the evals.** If the feature is AI-bearing and the TL designed `EVAL-<AREA>-NN` units under `features/<slug>/evals/`, materialize and run them as first-class verifiers via **`references/eval-runner.md`** (and the core **`eval-engineering`** skill): run each verifier, wiring the live-vs-simulated tool calls the eval declares, and feed its pass/fail into the acceptance map as the evidence for its AI-driven criterion. **Inspect both sides** — the model's *trajectory* and the verifier's *verdict* — before calling an AI criterion passed, so an agent that reward-hacks the verifier (claims an action it didn't take, over-cites, exploits reachable answers) is caught rather than scored green. A failing or reward-hacked eval is a failure the repair loop handles like any other; a genuinely wrong eval goes back to the TL to revise, not around. Deterministic features skip this — the acceptance map alone proves them.

### 7. Repair loop (state REVIEW_FIXES on failure — → broadcast the transition; heartbeat each repair attempt)
For each failure: identify the cause, decide whether it is actionable, make a **focused** correction, re-run the narrow check first, then the broader suite once the focused fix passes, and record the attempt and result in `dev/implementation-log.md`. Honour the limits in `references/loop-control.md`: **3** focused repair attempts per failure, **2** broad validation cycles. The same failure surviving three focused repairs, a fix that keeps causing regressions elsewhere, or a root cause you can't isolate with the available context → **escalate**. No blind repeated retries.

### 8. Self-review and security pass
Invoke **`dev-code-review`**: review the diff for quality, maintainability, regressions, and standards, and run the security pass (authn/authz, secrets, input validation, common vulnerabilities). Fix actionable findings (still within retry limits); anything sensitive-data, vulnerability, or permissions related is a security escalation, not a silent fix.

### 9. Update documentation and trackers
After meaningful progress update `dev/delivery-status.md`, `dev/implementation-log.md`, `dev/decisions.md` (where applicable), the parent's `status.md` (or this sub-task's `status.md`), `feature-index.md` (state mapped per `references/loop-control.md`), and `features/tracker.md` (state, owner, start/updated dates, current blocker, validation status, PR link, next action). **For a sub-task, also refresh the parent's derived status** — if all sub-tasks reach `HUMAN_REVIEW`, parent's status becomes `HUMAN_REVIEW`.

### 10. Prepare the PR handoff
Only when **every** completion criterion in `references/loop-control.md` is met — task scope implemented, required acceptance criteria validated (or `deferred-to-e2e` marked), relevant tests + build + static checks pass, docs updated, no unresolved critical/high defect, no unresolved blocker, tracker current — invoke **`dev-pr-handoff`** to write `dev/pr-summary.md` (purpose, scope of changes, technical approach, affected pages/APIs/services, tests run, acceptance-criteria status, risks/rollout, open follow-ups, reviewer instructions). Move the task `READY_FOR_PR` → `HUMAN_REVIEW` (**broadcast both transitions**). **Do not merge or deploy** — hand off to the human.

**Sub-task PR handoff — one PR per sub-task, one repo per PR.** Each sub-task raises its own PR in its own repo. Cross-repo integration is coordinated by the parent's tracker + the Sub-tasks table's `Depends on` column; do not attempt to combine sub-tasks into one PR spanning repos.

### Re-runs and other modes
- **Continue** a feature: read `dev/delivery-status.md` for the current state and pick up there; update in place, never blind-overwrite a log.
- **Validate only**: run steps 2, 8, 9 and report — no implementation.
- **Fix review feedback**: re-enter at step 9/10 with the reviewer's comments as the failure set, fix actionable ones within the limits, re-validate, and refresh `dev/pr-summary.md`.
- **After an escalation resolves**: fold the human's decision in (log the `DEC-###`), clear the blocker, move off `BLOCKED`, and resume.

### Report in chat
This closing report is the summary *on top of* the live progress broadcasts you've been emitting throughout the run (see "Progress broadcasts" in `references/loop-control.md`) — not a replacement for them. Give the headline: the feature and its new state, what you implemented (files/units), the validation summary and the acceptance-criteria pass/fail table, decisions logged, blockers/escalations raised, and links to `dev/pr-summary.md` (or the escalation note) and `features/tracker.md`. Keep it tight — the detail lives in the files. If the run ended `BLOCKED`, the final message must include the inline error/blocked block, not just a link.

## Completion criteria

A feature reaches `READY_FOR_PR` only when: the feature scope is implemented; required acceptance criteria are validated with evidence (or formally waived by a human); relevant tests, build, and static checks pass; required docs are updated; no unresolved critical or high-severity defect remains; no unresolved blocker remains; the feature tracker reflects the latest state; and the PR summary is prepared. Optional gates (accessibility, performance, e2e, security sign-off, feature-flag config, release notes) apply where the project requires them. (Full checklist in `references/loop-control.md`.)

## Principles

- **Context is the source of truth.** Don't begin until the feature is sufficiently ready; a genuine gap is a blocker, not a guess.
- **Plan before coding, validate every change.** Tests and acceptance criteria are the evidence of completion — code existing is not.
- **Prove AI behaviour with evals.** For an applied-AI feature, run and inspect the TL-designed `EVAL-` verifiers as part of validation, checking the *trajectory*, not just the verifier's verdict — a reward-hacked pass is a failure. Deterministic features need none.
- **Bound the repair loop.** Focused fixes, narrow-then-broad re-runs, three attempts, then escalate. Never retry blindly.
- **Stay in scope.** Work only the selected feature's files; document cross-feature impact and raise a scope escalation before touching unrelated modules.
- **Persist everything.** Progress, decisions, and blockers live in the `dev/` context and the tracker so any agent or human can continue.
- **Stay visible.** Broadcast every state transition in chat as it happens, heartbeat long phases, and surface blockers inline — the human should never have to open a markdown file to find out where the loop is or why it stopped.
- **Escalate, don't guess.** Business, architecture, schema, security, dependency, and stuck-retry situations go to a human with a structured note. Escalating well is success.
- **Never overstep the guardrails.** No merge, no deploy, no secret changes, no scope expansion, no disabling of controls, no ignoring failing tests — without explicit human approval.
