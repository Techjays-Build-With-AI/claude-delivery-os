---
name: feature-delivery-loop
description: Autonomously deliver one approved feature through a controlled, state-driven loop — implement, validate, fix, track, and prepare for review — rather than a one-shot code dump. Use whenever the user asks to "build/implement a feature", "run the delivery loop", "develop FEAT-…", "take this feature to a PR", or hand an approved, TL-planned feature to development. Point it at one feature (a FEAT-<AREA>-NN id or a context/features/<slug>/ folder) or let it pick the next feature at READY_FOR_DEV. It reads the BA feature breakdown and the TL technical context graph, validates feature readiness, analyses concrete code-level impact, writes a technical implementation plan, works in an isolated branch/worktree, implements scoped changes with tests, runs validation and maps results to acceptance criteria, repairs actionable failures within retry limits, moves the feature through an explicit state model, updates delivery status and the feature tracker, and prepares a pull-request handoff. It escalates business, architecture, schema, security, dependency, and scope blockers instead of guessing, and never merges, deploys, modifies secrets, or expands scope without human approval. It orchestrates the dev-validation, dev-code-review, and dev-pr-handoff skills. Re-run it to continue a feature, respond to review feedback, or pick up after an escalation is resolved.
---

# Feature Delivery Loop (approved feature → validated, review-ready implementation)

You are turning an **approved, planned feature** into working, validated code and a clean review handoff. The BA answered *what capability and why* (`context/features/`); the TL answered *which pages, endpoints, and entities* (`context/frontend|backend|database`). You answer *the working implementation, proven against the acceptance criteria*. This is an **execution and verification loop**, not a single code-generation call: you implement, you prove, you fix, you track, and you either reach a review-ready state or you escalate — you never declare a feature done because code exists.

The defining behaviour of this skill is the **state-driven loop with hard guardrails**. Every feature moves through explicit states; every meaningful change is validated; every acceptance criterion is backed by evidence; repairs are bounded; and ambiguity, risk, and scope decisions are escalated rather than guessed. You are the **build authority** for the feature's scope, but "build authority" is not "licence to decide the business" — where the context is silent on something that changes behaviour (a business rule, an auth model, a schema risk, an integration contract), you raise a blocker, not a guess.

## Operating contract

Read the **`delivery-os-conventions`** contract first if it isn't in context — the workspace layout, the frontmatter standard, the stable-ID rules, the source-citation form, and the controlled vocabulary. Your **inputs** are published upstream work you consume and never regenerate:

- BA feature folder `context/features/<slug>/` — `feature.md`, `implementation-plan.md`, `workflow.md`, `acceptance-criteria.md`, `dependencies.md`, `open-questions.md`, `status.md`.
- TL context graph — the `PAGE-/EP-/ENT-<AREA>-NN` unit files the feature maps to (via the feature's *Related Pages / APIs / Data Entities*), the three layer indexes, and the `DEC-###` decisions in `shared-context/decision-log.md`.
- `shared-context/` (actors, systems, glossary, decisions) and the BA registers in `ba-output/` (data, integration, workflow, business-rule) for the rules your code must honour.
- The **product repository** you implement in — its `coding-standards.md`/`architecture.md` (from `context/project/` or the repo), its test/lint/build tooling, and its git state.

You **write** your dev context alongside the feature, under a `dev/` subfolder so you never collide with the BA's seven files or the TL's graph, plus a cross-feature tracker in `dev-output/`:

```text
context/features/<slug>/
  feature.md  implementation-plan.md  workflow.md  acceptance-criteria.md
  dependencies.md  open-questions.md  status.md            # BA (input, read-only)
  dev/                                                      # you write these (produced_by: dev)
    dev-plan.md              # the technical implementation plan
    impacted-components.md   # concrete code-level impact analysis
    acceptance-map.md        # acceptance criterion → validation method → result → evidence
    implementation-log.md    # per-run step / validation / failure / next-action log
    delivery-status.md       # the fine-grained loop state, owner lock, blockers
    decisions.md             # technical decisions (also appended to shared-context/decision-log.md)
    pr-summary.md            # the PR / review handoff (dev-pr-handoff writes this)
    escalation-<n>.md        # structured blocker notes when BLOCKED
dev-output/
  feature-tracker.md         # cross-feature delivery dashboard (one row per feature)
```

Every file follows the exact schema in **`references/dev-context-templates.md`** — build them from it so the dev layer stays uniform. Keep the frontmatter (`produced_by: dev`) on every file. If there is no Delivery OS workspace, don't block: take the feature and repo paths the user gives you, create the `dev/` and `dev-output/` folders next to them, and note in the run summary that a standard workspace wasn't found.

## The loop

Follow the state model, retry limits, permission/scope guardrails, escalation rules, and the state → BA-vocabulary mapping in **`references/loop-control.md`**. Follow the readiness gate, impact-analysis dimensions, and implementation-planning method in **`references/readiness-and-planning.md`**. Delegate validation to **`dev-validation`**, self-review and the security pass to **`dev-code-review`**, and the PR/escalation handoff to **`dev-pr-handoff`**.

### 1. Select the feature and acquire the lock
Take the target from the user (a `FEAT-<AREA>-NN`, a feature folder, or a slug), or — if none is given — pick the next feature at `READY_FOR_DEV` from `feature-index.md`. Skip blocked, incomplete, or already-active features unless explicitly told otherwise. Write your owner into `dev/delivery-status.md` so another agent won't take the same feature. Set state `IN_PLANNING`.

### 2. Read the context and summarise before coding
Read the feature's seven BA files, the TL units it maps to, `shared-context/`, and the relevant registers. Read the parts of the **existing codebase** those units touch — the real pages, routes, services, schema, and tests — so your plan reflects the code that exists, not an imagined one. Record which sources you consulted. Do not begin implementation until you can state what "done" is in terms of the acceptance criteria.

### 3. Ensure the feature is planned, then validate readiness (gate)
**Planning gate first** (`references/readiness-and-planning.md` §0). The dev loop builds against the TL context graph, so before anything else confirm the feature is **planned** — detect it by verifying every page/endpoint/entity the feature's `feature.md` declares **resolves** to a real unit file **and** is **linked** to this `FEAT-id` in the TL indexes. If it's *not planned* or *partially planned*, auto-plan it: delegate to the **`tl-agent`** subagent (running `tl-feature-planning` on this one feature folder — the same work `/tl:plan` does), or, if subagent delegation isn't available, run the `tl-feature-planning` skill directly; then **re-verify** it comes back planned and carry the result (units created/reused, `DEC-###`, TL open questions) into the run summary. Only escalate here if TL planning is **unavailable** (set `BLOCKED`, tell the user to run `/tl:plan`) or **can't complete** (carry the TL's blocking open questions up). Then continue the loop.

**Then the readiness checklist.** Run the rest of the gate in `references/readiness-and-planning.md`. If it fails on anything critical — no acceptance criteria, unresolved blocking open questions, unavailable/unmocked dependency, an already-broken repo build, missing credentials/tools, or a lock held by another agent — set state `BLOCKED`, write `dev/escalation-<n>.md` (template in `dev-context-templates.md`), update the trackers, and **stop**. Do not implement around a genuine readiness gap.

### 4. Analyse impact
Identify concrete impacts across the dimensions in `references/readiness-and-planning.md` — frontend pages/components, backend APIs/services, DB schema and migrations, authn/authz, third-party integrations, background jobs/queues, notifications, monitoring, existing tests, docs, feature flags, analytics. Name real files/modules where you can. Write `dev/impacted-components.md`.

### 5. Plan the implementation
Write or refresh `dev/dev-plan.md`: ordered implementation steps, affected files/modules, required API changes, required schema changes, test strategy, rollback considerations, risks and assumptions, validation criteria, complexity, and cross-feature/team dependencies. The plan must let another agent continue from the same point. Max **2** auto-generated plans per feature — if the second plan still can't produce an actionable path, escalate.

### 6. Create the isolated environment
Create the branch or worktree `feature/FEAT-<AREA>-NN-<slug>` off the integration branch. **Never** commit implementation changes directly to `main`, `master`, or `production`. Confirm the working tree is clean and the base build is green before you change anything (a pre-existing broken build is an escalation, not your bug to silently fix).

### 7. Implement (state IN_DEVELOPMENT)
Make scoped changes that follow `coding-standards.md`, reuse existing patterns and abstractions, avoid unnecessary refactoring, keep within the approved feature scope, and add or update tests **with** the code. Maintain backward compatibility unless the feature explicitly requires a break (and if it does, that break is a decision to log and likely to escalate). Log material technical decisions to `dev/decisions.md` and append a `DEC-###` row to `shared-context/decision-log.md`. Stay inside the scope boundary in `references/loop-control.md`: touching an unrelated module requires a scope escalation first.

### 8. Validate (state TESTING)
Invoke **`dev-validation`**: run the applicable suite (lint, format, type-check, unit, integration, API-contract, e2e, build, migration validation, security scan, dependency check, plus any feature-specific acceptance tests), record results in `dev/implementation-log.md`, then build `dev/acceptance-map.md` mapping every acceptance criterion to a validation method, result, and evidence file. Passing unit tests alone is **not** completion — the acceptance map is.

### 9. Repair loop (state REVIEW_FIXES on failure)
For each failure: identify the cause, decide whether it is actionable, make a **focused** correction, re-run the narrow check first, then the broader suite once the focused fix passes, and record the attempt and result in `dev/implementation-log.md`. Honour the limits in `references/loop-control.md`: **3** focused repair attempts per failure, **2** broad validation cycles. The same failure surviving three focused repairs, a fix that keeps causing regressions elsewhere, or a root cause you can't isolate with the available context → **escalate**. No blind repeated retries.

### 10. Self-review and security pass
Invoke **`dev-code-review`**: review the diff for quality, maintainability, regressions, and standards, and run the security pass (authn/authz, secrets, input validation, common vulnerabilities). Fix actionable findings (still within retry limits); anything sensitive-data, vulnerability, or permissions related is a security escalation, not a silent fix.

### 11. Update documentation and trackers
After meaningful progress update `dev/delivery-status.md`, `dev/implementation-log.md`, `dev/dev-plan.md`, `dev/decisions.md` (where applicable), the BA `status.md` and `feature-index.md` (state mapped per `references/loop-control.md`), and `dev-output/feature-tracker.md` (state, owner, start/updated dates, current blocker, validation status, PR link, next action).

### 12. Prepare the PR handoff
Only when **every** completion criterion in `references/loop-control.md` is met — feature scope implemented, required acceptance criteria validated, relevant tests + build + static checks pass, docs updated, no unresolved critical/high defect, no unresolved blocker, tracker current — invoke **`dev-pr-handoff`** to write `dev/pr-summary.md` (purpose, scope of changes, technical approach, affected pages/APIs/services, tests run, acceptance-criteria status, risks/rollout, open follow-ups, reviewer instructions). Move the feature `READY_FOR_PR` → `HUMAN_REVIEW`. **Do not merge or deploy** — hand off to the human.

### Re-runs and other modes
- **Continue** a feature: read `dev/delivery-status.md` for the current state and pick up there; update in place, never blind-overwrite a log.
- **Validate only**: run steps 2, 8, 9 and report — no implementation.
- **Fix review feedback**: re-enter at step 9/10 with the reviewer's comments as the failure set, fix actionable ones within the limits, re-validate, and refresh `dev/pr-summary.md`.
- **After an escalation resolves**: fold the human's decision in (log the `DEC-###`), clear the blocker, move off `BLOCKED`, and resume.

### Report in chat
Give the headline: the feature and its new state, what you implemented (files/units), the validation summary and the acceptance-criteria pass/fail table, decisions logged, blockers/escalations raised, and links to `dev/pr-summary.md` (or the escalation note) and `dev-output/feature-tracker.md`. Keep it tight — the detail lives in the files.

## Completion criteria

A feature reaches `READY_FOR_PR` only when: the feature scope is implemented; required acceptance criteria are validated with evidence (or formally waived by a human); relevant tests, build, and static checks pass; required docs are updated; no unresolved critical or high-severity defect remains; no unresolved blocker remains; the feature tracker reflects the latest state; and the PR summary is prepared. Optional gates (accessibility, performance, e2e, security sign-off, feature-flag config, release notes) apply where the project requires them. (Full checklist in `references/loop-control.md`.)

## Principles

- **Context is the source of truth.** Don't begin until the feature is sufficiently ready; a genuine gap is a blocker, not a guess.
- **Plan before coding, validate every change.** Tests and acceptance criteria are the evidence of completion — code existing is not.
- **Bound the repair loop.** Focused fixes, narrow-then-broad re-runs, three attempts, then escalate. Never retry blindly.
- **Stay in scope.** Work only the selected feature's files; document cross-feature impact and raise a scope escalation before touching unrelated modules.
- **Persist everything.** Progress, decisions, and blockers live in the `dev/` context and the tracker so any agent or human can continue.
- **Escalate, don't guess.** Business, architecture, schema, security, dependency, and stuck-retry situations go to a human with a structured note. Escalating well is success.
- **Never overstep the guardrails.** No merge, no deploy, no secret changes, no scope expansion, no disabling of controls, no ignoring failing tests — without explicit human approval.
