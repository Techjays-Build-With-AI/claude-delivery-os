# Dev Agent — Feature Delivery Loop (v2.2)

The **Developer Agent** takes an approved, TL-planned feature and **builds + ships** it — through a controlled three-command flow rather than a one-shot code dump. It reads the BA feature context and the TL technical graph, plans just-in-time (with user-driven plan-blocker resolution), builds in an isolated branch with dynamic stack-adaptive skills, validates against the acceptance criteria, runs a two-gate security model (build → commit), semantically merges the code-context against baseline, and raises a clean PR. It escalates ambiguity, risk, and scope decisions instead of guessing, and it never merges or deploys.

| | |
|---|---|
| **Namespace** | `/dev:` |
| **Commands** | `/dev:bootstrap [spec]` · **`/dev:plan <task>`** · **`/dev:build <task>`** · **`/dev:commit <task>`** · `/dev:fix-review <task> feedback=<...>` |
| **Input** | BA feature breakdown (`features/<slug>/`), TL context graph (`context/frontend\|backend\|database`), product repository, and (for `/dev:build`) plan artifacts `/dev:plan` produced with `plan-blockers.md` all `RESOLVED` |
| **Output** | Working code on `feature/FEAT-<AREA>-NN-<slug>[-<repo>]`, `dev/` context files per task, `features/tracker.md`, `dev/local-runbook.md` (developer verification guide), and a merged / mergeable PR with `dev/pr-summary.md` as body |
| **Skills** | `feature-delivery-loop` · `dev-stack-adaptive-implementation` · `dev-stack-adaptive-code-review` · `qa-greenfield-harness` · `dev-pr-handoff` (slimmed to content-only). `dev-validation` retired (folded into `/dev:build` Stages 7–9). |

---

## The v2.2 three-command flow

```text
/dev:plan <task>       ── verify TL graph exists (auto-runs /tl:plan if not)
                        ── decide multi-repo → sub-task split
                        ── compose each sub-task's Description + Implementation
                        ── create sub-tasks in MC (batched via task-mcp)
                        ── detect + surface plan blockers (BB-01…) — USER resolves these
                        ── write dev-plan.md + plan-blockers.md (RESOLVED) for each task

         │  (user verifies each sub-task's plan; resolves blockers with DEC-### decisions)
         ▼

/dev:build <task>      ── 11-stage build loop (runs on a decidable plan; NEVER prompts mid-run)
                        ── auto-bootstrap qa-greenfield-harness (deterministic per-stack matrix)
                        ── dev-stack-adaptive-implementation (dynamic per stack, matches repo idioms)
                        ── stack-adaptive test writing + local execute
                        ── acceptance-map vs parent AC+BR+TS+NFRs
                        ── security review — BUILD-TIME GATE: Critical-only blocking
                        ── code-context designed → implemented flip
                        ── summary + dev/local-runbook.md

         │  (developer verifies locally per local-runbook.md)
         ▼

/dev:commit <task>     ── 10-stage commit loop
                        ── security review — COMMIT-TIME GATE: Critical + High blocking
                        ── dev-stack-adaptive-code-review (7 dimensions × 4 severity tiers)
                        ── acceptance-map re-verification + last-sub-task E2E resolution
                        ── bounded fix loop (routes back through security / review / acceptance)
                        ── tl-semantic-context-merge (unit-level, NOT git text-merge)
                        ── push branch, raise PR with dev/pr-summary.md as body

         │  (human reviewer reviews PR; on merge, webhook flips MC to done in v2.3)
         ▼

PR merged → DONE (human-owned)
```

Each command is user-invoked separately — the flow never chains automatically. Between `/dev:build` and `/dev:commit`, the developer runs the feature locally using `dev/local-runbook.md` to sanity-check.

---

## Commands

| Command | Does | Stops at |
|---|---|---|
| `/dev:bootstrap [spec]` | Greenfield — ensure a usable, green product repo exists (scaffolds via the TL on project-zero) | build-ready workspace |
| **`/dev:plan <task>`** | Just-in-time planning — verify TL graph, decide sub-task split, compose Description + Implementation, create MC sub-tasks, write `dev-plan.md`, detect and surface plan blockers for user resolution | `PLANNED` (blockers `RESOLVED`) or `BLOCKED_ON_PLAN` |
| **`/dev:build <task>`** | The 11-stage build loop — branch, harness bootstrap, implement, test, security-build-gate (Critical only), acceptance-map, code-context flip, local-runbook. Refuses on unresolved blockers | local `IN_PROGRESS`, MC `inProgress` |
| **`/dev:commit <task>`** | The 10-stage commit loop — security-commit-gate (Critical + High), code review (Blocker + Major), acceptance re-verify, semantic-context-merge, push, PR raise | local `REVIEW`, MC `devReview` |
| `/dev:fix-review <task> feedback=<path\|PR>` | Fold reviewer PR comments back in, re-verify, update `dev/pr-summary.md`; re-run relevant `/dev:commit` stages | local `REVIEW`, MC `devReview` |

`<task>` accepts any of: MC task number (`Task-N` / `Feature-N` / `Subtask-N`), `FEAT-<AREA>-NN` id, `features/<slug>/` folder, sub-task folder path (`features/<slug>/subtask/<repo>/`), or a bare slug. `/dev:plan` also accepts multi-target forms (`list=<name>`, `initiative=<name>`, `--all`). `/dev:build` with no target picks the next task at `PLANNED`; `/dev:commit` with no target picks the task most recently at `IN_PROGRESS`.

Retired in v2.2: **`/dev:validate`** (folded into `/dev:build` Stages 7-9), **`/dev:pr`** (folded into `/dev:commit`).

---

## MC status mapping (v2.2)

Uses MC's existing enum verbatim — no invented local variants.

| Local state | MC status | Set by |
|---|---|---|
| `PLANNED` | `readyForDev` | `/dev:plan` end |
| `BLOCKED_ON_PLAN` | `readyForDev` (unchanged) | `/dev:plan` when `plan-blockers.md` OPEN |
| `IN_PROGRESS` (build done) | `inProgress` | `/dev:build` Stage 11 |
| `REVIEW` | `devReview` | `/dev:commit` Stage 1 |
| `MERGE_CONFLICT` | `devReview` (unchanged) | `/dev:commit` Stage 7 halt |
| `BLOCKED` | `blocked` | Any stage's escalation |
| `DONE` | `done` | PR-merge webhook (v2.3) |

---

## Two-gate security model

The `security-review` skill runs TWICE with different thresholds:

- **`/dev:build` Stage 9 (build-time)** — Critical-only blocking. High + Medium + Low logged, non-blocking. Rapid-iteration friendly.
- **`/dev:commit` Stage 3 (commit-time)** — Critical + High blocking. Medium warns. Low logged. Strict pre-PR gate.

Build-deferred Highs surface at commit-time; they either got fixed in dev iteration or now block.

---

## Stack-adaptive skills (dynamic, not per-stack playbooks)

- **`dev-stack-adaptive-implementation`** — detects stack + infers repo patterns (naming, imports, DI, error handling, async, testing conventions) then implements + writes tests matching THIS repo's idioms. No per-stack playbook — the repo is the source of truth.
- **`dev-stack-adaptive-code-review`** — 7 review dimensions (correctness / conventions / errors / testability / BR enforcement / naming / reuse) × 4 severity tiers (Blocker / Major / Minor / Nit). Blocker + Major block at commit-time; Minor + Nit surface in PR body.
- **`qa-greenfield-harness`** — auto-bootstraps a deterministic per-stack test harness when `qa/quality-gates.md` is missing / Draft. NEVER prompts the user during `/dev:build`. Prompts only in `/qa:audit` / `/qa:plan`.

---

## Semantic context merge

New in v2.2: **`tl-semantic-context-merge`** runs at `/dev:commit` Stage 7. Merges the feature branch's flipped `origin: implemented` units against the `main` env baseline via context-mcp. Graph-aware, unit-level merge — NOT a git text-level merge:

- Frontmatter fields: LWW by `updated_at` (with transition-order rules for `origin`)
- Layer indexes: row-union by `unit_id`
- `Source References` sections: append-only
- Real conflicts (tied timestamps, incompatible immutable fields, method / table_name changes) → halt with `dev/context-merge-conflicts.md` for human resolution

Solves Dharma's "Semantic Memory Merging" concern from the design meeting.

---

## What it writes (per task)

Under a `dev/` subfolder in the task folder:

| File | Written by | Purpose |
|---|---|---|
| `dev/dev-plan.md` | `/dev:plan` | Ordered implementation steps, files, API/schema changes, test strategy |
| `dev/plan-blockers.md` | `/dev:plan` | Plan-time blocker resolution log; `status: OPEN \| RESOLVING \| RESOLVED` |
| `dev/impacted-components.md` | `/dev:plan` | 12-dimension code impact |
| `dev/delivery-status.md` | all | Local state, owner lock, branch, next action |
| `dev/build-run.md` | `/dev:build` | Per-stage log for build loop |
| `dev/implementation-log.md` | `/dev:build` | Detected stack + inferred patterns + per-step evidence |
| `dev/acceptance-map.md` | `/dev:build` (built) + `/dev:commit` (re-verified) | Parent AC + BR + TS + NFRs → validation → result |
| `dev/security-findings-build.md` | `/dev:build` Stage 9 | Build-time findings (Critical-blocking) |
| `dev/local-runbook.md` | `/dev:build` Stage 11 | Developer-facing manual verification guide |
| `dev/commit-run.md` | `/dev:commit` | Per-stage log for commit loop |
| `dev/security-findings-commit.md` | `/dev:commit` Stage 3 | Commit-time findings (Critical + High blocking) |
| `dev/code-review-findings.md` | `/dev:commit` Stage 4 | 4-tier severity findings |
| `dev/context-merge-log.md` | `/dev:commit` Stage 7 | Semantic merge outcome per unit + index |
| `dev/context-merge-conflicts.md` | `/dev:commit` Stage 7 (on halt) | Human-resolvable merge conflicts |
| `dev/pr-summary.md` | `/dev:commit` Stage 9 | Reviewer-facing PR body |
| `dev/decisions.md` | all | `DEC-###` audit trail |
| `dev/escalation-<n>.md` | any (on `BLOCKED`) | Structured escalation for human |

Plus cross-feature `features/tracker.md`.

---

## Guardrails

- **`/dev:build` invariant** — runs on a decidable plan or refuses. Never prompts the user mid-run. Plan blockers MUST resolve at `/dev:plan` time.
- **Retry limits** — 3 focused repair attempts per finding, 2 broad re-runs per stage. Exceed → escalate.
- **Never without human approval** — merge a PR, deploy to production, delete production data, modify secrets, change infra permissions, disable security controls, ignore failing tests, or `--no-verify` on push / signing.
- **Scope discipline** — one repo per sub-task; cross-repo edits require a scope escalation.
- **Escalate, don't guess** — business, architecture, security, dependency, or bounds-exceeded → structured `dev/escalation-<n>.md`.

A task never reaches PR because code was written — only when the mandatory completion criteria hold (acceptance map green, security gates passed, code review clean, semantic merge clean).

---

## Setup

See **[docs/SETUP.md](../../docs/SETUP.md)**. Short version:

```text
/plugin marketplace add techjays/claude-delivery-os
/plugin install delivery-os@techjays-delivery-os
/plugin install dev@techjays-delivery-os
/plugin install tl@techjays-delivery-os   # needed for /dev:plan auto-planning + greenfield
/plugin install qa@techjays-delivery-os   # optional — enables /qa:audit + /qa:plan interactive gates
```

---

## FAQ

**Does it actually run tests and git?** Yes — creates branch, edits code, runs lint/type/test/build in the shell. Does not merge or deploy.

**What if `/dev:plan` hasn't run?** `/dev:build` refuses with "run /dev:plan first". `/dev:build` never re-plans.

**What if `dev/plan-blockers.md` has OPEN entries?** `/dev:build` refuses. User resolves via `/dev:plan --resume`, ticks the blocker as RESOLVED with a DEC-###, then re-runs `/dev:build`.

**Why two security gates?** Fast build iteration (Critical only) + strict pre-PR check (Critical + High). Same skill, two thresholds.

**Passing unit tests = done?** No. Completion is a filled acceptance map + zero commit-time Blocker/Major/Critical/High + clean semantic merge.

**Can two people build different tasks at once?** Yes. Each task carries an owner lock in `dev/delivery-status.md`.

**Why did it stop and escalate?** One of: plan blocker unresolved, ambiguous rule, schema-risk, security concern, unavailable dependency, or bounds-exceeded fix loop. Escalation frames the decision with options + recommendation.
