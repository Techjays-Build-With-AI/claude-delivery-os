# Dev Agent — Feature Delivery Loop

The **Developer Agent** takes an approved, TL-planned feature and **builds it** — through a controlled, state-driven loop rather than a one-shot code dump. It reads the BA feature context and the TL technical graph, validates readiness, plans, implements in an isolated branch, validates against the acceptance criteria, repairs actionable failures within retry limits, tracks state, and prepares a clean pull-request handoff for a human. It escalates ambiguity, risk, and scope decisions instead of guessing, and it never merges or deploys.

| | |
|---|---|
| **Namespace** | `/dev:` |
| **Commands** | `/dev:build <feature>` · `/dev:validate <feature>` · `/dev:fix-review <feature> feedback=<...>` · `/dev:pr <feature>` |
| **Input** | The BA feature breakdown (`context/features/<slug>/`), the TL context graph (`context/frontend|backend|database`), and the product repository |
| **Output** | Working code on `feature/FEAT-<AREA>-NN-<slug>`, the `dev/` context files per feature, `dev-output/feature-tracker.md`, and a `dev/pr-summary.md` review handoff |
| **Skills** | `feature-delivery-loop` · `dev-validation` · `dev-code-review` · `dev-pr-handoff` |

---

## The loop

`/dev:build` runs the full sequence for one feature:

```text
Select feature (or next READY_FOR_DEV) → acquire lock
→ Read BA + TL context, summarise → Validate readiness (gate)
→ Analyse code-level impact → Write the technical plan
→ Create isolated branch/worktree → Implement (scoped, with tests)
→ Validate suite → Map results to acceptance criteria
→ Repair actionable failures (bounded) → Self-review + security pass
→ Update delivery status + feature tracker → Prepare PR handoff
→ Hand off for HUMAN_REVIEW   (never merges or deploys)
```

Each feature moves through an explicit **state model** — `BACKLOG → READY_FOR_DEV → IN_PLANNING → BLOCKED → IN_DEVELOPMENT → TESTING → REVIEW_FIXES → READY_FOR_PR → HUMAN_REVIEW → APPROVED → MERGED → RELEASED`. The fine-grained state lives in each feature's `dev/delivery-status.md`; it is mirrored into the BA `status.md`/`feature-index.md` using the shared vocabulary, and rolled up into `dev-output/feature-tracker.md`.

| State | Meaning | Owner |
|---|---|---|
| `READY_FOR_DEV` | Sufficient context, approved for development | TL / human |
| `IN_PLANNING` | Reading context, preparing the technical plan | dev |
| `BLOCKED` | Cannot continue without a decision, dependency, or clarification | dev |
| `IN_DEVELOPMENT` | Actively making code changes | dev |
| `TESTING` | Running the validation suite | dev |
| `REVIEW_FIXES` | Resolving validation failures or review feedback | dev |
| `READY_FOR_PR` | Implementation and validation complete; handoff prepared | dev |
| `HUMAN_REVIEW` | PR waiting for human review/approval | dev → human |
| `APPROVED` · `MERGED` · `RELEASED` | Human- or deploy-owned; the dev agent only records them | human |

The agent owns transitions up to `HUMAN_REVIEW` and stops there — it never advances a feature to `APPROVED`, `MERGED`, or `RELEASED` itself. `BLOCKED` is reachable from any working state and returns to the state it left once the blocker is resolved. The full state → BA-vocabulary mapping is in [`feature-delivery-loop/references/loop-control.md`](skills/feature-delivery-loop/references/loop-control.md).

### Planning gate — it plans the feature for you

The very first thing `/dev:build` does is make sure the feature is **planned** — split by the TL into pages, endpoints, and database entities — because that graph is what it builds against. It detects this by reading the feature's `feature.md` and checking every declared page/API/data-entity actually **resolves** to a real TL unit file **and** is **linked** to this `FEAT-id` in the TL indexes (so a partial or stale plan is caught, not just an empty one).

If the feature isn't planned (or is only partially planned), the agent **auto-plans it** — it delegates to the `tl-agent` and runs `tl-feature-planning` on that one feature (the same work `/tl:plan` does), re-verifies the graph, and then continues the loop, noting in the summary what was planned (units created/reused, `DEC-###` decisions, any open questions the TL raised). So pointing `/dev:build` at a feature folder "just works" whether or not you ran `/tl:plan` first.

It only stops on the planning step in two cases: the **TL plugin isn't installed** (it blocks and asks you to run `/tl:plan`), or **TL planning itself hits a genuine unknown** (a missing integration contract, an undecided auth model) — in which case it carries the TL's blocking open questions up as the escalation rather than building on a half-graph. Prefer to review the technical design before any code is written? Run `/tl:plan <feature>` yourself first; the gate will see it's already planned and go straight to building.

---

## Commands

| Command | Does | Stops at |
|---|---|---|
| `/dev:build <feature>` | The full loop — implement, validate, repair, track, prepare PR | `HUMAN_REVIEW` (or `BLOCKED`) |
| `/dev:validate <feature>` | Runs the validation suite and maps results to acceptance criteria; no code changes | acceptance-map report |
| `/dev:fix-review <feature> feedback=<path\|PR>` | Folds reviewer comments back in, re-validates, refreshes the PR summary | `HUMAN_REVIEW` (or `BLOCKED`) |
| `/dev:pr <feature>` | Verifies completion criteria and writes the PR handoff | `HUMAN_REVIEW` |

`<feature>` is a `FEAT-<AREA>-NN` id, a `context/features/<slug>/` folder, or a slug. `/dev:build` with no target picks the next feature at `READY_FOR_DEV`.

---

## What it writes (per feature)

Alongside the BA's seven files, under a `dev/` subfolder so nothing collides:

| File | What |
|---|---|
| `dev/dev-plan.md` | The technical implementation plan (ordered steps, files, API/schema changes, test strategy, rollback, risks) |
| `dev/impacted-components.md` | Concrete code-level impact across 12 dimensions (frontend, backend, DB/migrations, authz, integrations, jobs, notifications, monitoring, tests, docs, flags, analytics) |
| `dev/acceptance-map.md` | Each acceptance criterion → validation method → result → evidence artifact |
| `dev/implementation-log.md` | Dated log of steps, validation results, failures, repair attempts, next actions |
| `dev/delivery-status.md` | The loop state, owner lock, branch, validation status, blocker, next action |
| `dev/decisions.md` | Technical decisions (also appended as `DEC-###` to `shared-context/decision-log.md`) |
| `dev/pr-summary.md` | The review-ready PR handoff |
| `dev/escalation-<n>.md` | A structured blocker note when the feature goes `BLOCKED` |

Plus the cross-feature `dev-output/feature-tracker.md`.

---

## Guardrails

The loop is bounded and permission-fenced by design:

- **Retry limits** — 3 focused repair attempts per failure, 2 broad validation cycles, 2 auto-generated plans per feature, 0 scope-expansion attempts without human approval. No blind retries.
- **Never without human approval** — merge a PR, deploy to production, delete production data, modify secrets, change infra permissions, disable security controls, or ignore failing tests.
- **Scope discipline** — works only on the selected feature's files; a real cross-feature impact is documented and a scope escalation is raised *before* touching the unrelated module.
- **Escalate, don't guess** — business/scope, technical (schema-risk, unavailable dependency, unclear authz, breaking contract), security/compliance, and stuck-retry situations go to a human with a structured, decision-ready note. Escalating well is a success.

A feature never reaches `READY_FOR_PR` because code was written — only when the mandatory completion criteria all hold, including acceptance criteria validated with evidence.

---

## Setup

Installation and workspace setup are shared across all Delivery OS plugins — see **[docs/SETUP.md](../../docs/SETUP.md)**. The short version for `dev`:

1. **Install** the core, then the dev plugin:
   ```text
   /plugin marketplace add techjays/claude-delivery-os
   /plugin install delivery-os@techjays-delivery-os
   /plugin install dev@techjays-delivery-os
   ```
2. **Run the BA breakdown first; TL planning is automatic.** The dev agent consumes the BA feature breakdown (`/ba:features`), so that must exist. TL planning it will handle for you: `/dev:build` opens with a **planning gate** that checks whether the feature is already split into pages/endpoints/entities and, if not, auto-plans it via `tl-feature-planning` before building (see below). You can still run `/tl:plan` yourself beforehand if you want to review the technical design first.

---

## Worked example

You've run `/ba:features` and `/tl:plan`, so `FEAT-SUP-001 — Supplier Onboarding` sits at `Ready for Planning` with a full feature folder and a TL context graph (pages `PAGE-SUP-01…03`, endpoints `EP-SUP-01…04`, entities `ENT-SUP-01…03`). You run:

```text
/dev:build FEAT-SUP-001
```

The agent acquires the lock, reads the seven BA files and the TL units, and validates readiness — all critical gates pass except one: the acceptance criterion *"Duplicate tax ID is rejected"* has no defined rule for what counts as a duplicate, and there's no tax-validation API contract in the context or repo. Rather than guess, it implements everything it safely can — the onboarding form, draft supplier creation, the approval workflow — logs its decisions as `DEC-###`, then **stops on the one blocker** and writes `dev/escalation-1.md`:

> **Blocker** — Tax validation API contract is not available in the project context or repository.
> **Impact** — Acceptance criterion "Duplicate tax ID is rejected" cannot be validated.
> **Decision needed** — (1) use the existing internal compliance service, (2) integrate a third-party service, or (3) handle validation by manual review for now.
> **Recommended** — Option 1, if the internal service exists.
> **Can continue in parallel** — front-end form, draft supplier creation, admin approval workflow.

The feature goes `BLOCKED`, mirrored to `In Development → Blocked` in `feature-index.md`, with the row and next action in `dev-output/feature-tracker.md`. The headline it returns leads with the decision you need to make.

You answer *"use the internal compliance service, duplicate = same tax ID in the same country"*. You re-run `/dev:build FEAT-SUP-001`; the agent folds the decision in (`DEC-###`), clears the blocker, wires the duplicate check, and finishes the loop — validation green, every acceptance criterion mapped to evidence in `dev/acceptance-map.md`, a self-review + security pass, and `dev/pr-summary.md` written. The feature lands at `HUMAN_REVIEW` on branch `feature/FEAT-SUP-001-supplier-onboarding`, ready for you to review and merge. It never merges or deploys.

---

## How it fits Delivery OS

The dev agent is a **consumer** in the Delivery OS contract: it reads the BA feature folders, the TL `context/frontend|backend|database` graph, `shared-context/`, and the BA registers, and never re-runs BA discovery or TL planning. It writes `produced_by: dev` files under each feature's `dev/` folder and `dev-output/`, mirrors feature state into the BA `feature-index.md`/`status.md` using the shared vocabulary, and appends its `DEC-###` decisions to the shared `decision-log.md`. See the shared [`delivery-os-conventions`](../delivery-os-core/skills/delivery-os-conventions/SKILL.md) skill for the full document contract.

---

## FAQ

**Does it actually run tests and git?** Yes — the agent creates the branch/worktree, edits code, and runs lint/type/test/build in the shell against the real repo. It does not merge or deploy.

**What if the feature has no TL plan yet?** The planning gate handles it — `/dev:build` auto-plans the feature via `tl-feature-planning` (delegating to the `tl-agent`) before building, then continues. It only blocks on planning if the TL plugin isn't installed (run `/tl:plan` first) or if TL planning itself hits a genuine unknown, which it carries up as the escalation.

**What if the feature has no acceptance criteria?** That's a critical readiness gap the planning gate can't fill. The agent sets the feature `BLOCKED`, writes an escalation note naming what's missing, and stops — it won't build blind.

**Can two people build different features at once?** Yes. Each feature carries an owner lock in `dev/delivery-status.md`; the agent won't take a feature another agent already holds unless told to.

**Why did it stop and escalate instead of finishing?** Because it hit one of the escalation triggers — an ambiguous rule, a schema/data-loss risk, a security concern, an unavailable dependency, or a failure that survived three focused repairs. The escalation note frames the decision with options and a recommendation; once you decide, re-run `/dev:build` to resume.

**Does passing unit tests mean it's done?** No. Completion is a filled acceptance map — every mandatory acceptance criterion backed by a validation method and an evidence artifact — plus the rest of the completion criteria. A green unit run alone is not enough.
