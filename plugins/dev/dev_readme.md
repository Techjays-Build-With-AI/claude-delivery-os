# Dev Agent — Feature Delivery Loop (v2.2)

The **Developer Agent** takes an approved, TL-planned feature and **builds + ships** it — through a controlled three-command flow rather than a one-shot code dump. It reads the BA feature context and the TL technical graph, plans just-in-time (with user-driven plan-blocker resolution), builds in an isolated branch with dynamic stack-adaptive skills, validates against the acceptance criteria, runs a two-gate security model (build → commit), semantically merges the code-context against baseline, and raises a clean PR. It escalates ambiguity, risk, and scope decisions instead of guessing, and it never merges or deploys.

| | |
|---|---|
| **Namespace** | `/dev:` |
| **Commands** | `/dev:bootstrap [spec]` · **`/dev:plan <task>`** · **`/dev:resolve --plan <task>`** · **`/dev:build <task>`** · **`/dev:commit <task>`** · `/dev:fix-review <task> feedback=<...>` |
| **Input** | BA feature breakdown (`features/<slug>/`), TL context graph (`<repo>/context/code-context/{frontend,backend,database}`), product repository, and (for `/dev:build`) plan artifacts `/dev:plan` produced with `plan-blockers.md` all `RESOLVED` |
| **Output** | Working code on `feature/FEAT-<AREA>-NN-<slug>[-<repo>]`, `dev/` context files per task, each feature’s own `status.md`, `units/<repo>/pr-summary.md § ## How to verify` (developer verification guide), and a merged / mergeable PR with `units/<repo>/pr-summary.md` as body |
| **Skills** | `feature-delivery-loop` · `dev-stack-adaptive-implementation` · `dev-stack-adaptive-code-review` · `qa-greenfield-harness` · `dev-pr-handoff` (slimmed to content-only). `dev-validation` retired (folded into `/dev:build` Stages 7–9). |

---

## The v2.2 three-command flow

```text
/dev:plan <task>       ── verify TL graph exists (auto-runs forward planning if not)
                        ── decide multi-repo → sub-task split
                        ── compose each sub-task's Description + Implementation
                        ── create sub-tasks in MC (batched via task-mcp)
                        ── detect + surface plan blockers (BB-01…) — USER resolves these
                        ── write implementation.md + plan-blockers.md (RESOLVED) for each task

         │  (user verifies each sub-task's plan; resolves blockers with DEC-### decisions)
         ▼

/dev:build <task>      ── 11-stage build loop (runs on a decidable plan; NEVER prompts mid-run)
                        ── auto-bootstrap qa-greenfield-harness (deterministic per-stack matrix)
                        ── dev-stack-adaptive-implementation (dynamic per stack, matches repo idioms)
                        ── stack-adaptive test writing + local execute
                        ── `## Acceptance` table vs parent AC+BR+TS+NFRs
                        ── security review — BUILD-TIME GATE: Critical-only blocking
                        ── code-context designed → implemented flip
                        ── summary + units/<repo>/pr-summary.md § ## How to verify

         │  (developer verifies locally per pr-summary.md § ## How to verify)
         ▼

/dev:commit <task>     ── 10-stage commit loop
                        ── security review — COMMIT-TIME GATE: Critical + High blocking
                        ── dev-stack-adaptive-code-review (7 dimensions × 4 severity tiers)
                        ── `## Acceptance` table re-verification + last-sub-task E2E resolution
                        ── bounded fix loop (routes back through security / review / acceptance)
                        ── tl-semantic-context-merge (unit-level, NOT git text-merge)
                        ── push branch, raise PR with units/<repo>/pr-summary.md as body

         │  (human reviewer reviews PR; on merge, webhook flips MC to done in v2.3)
         ▼

PR merged → DONE (human-owned)
```

Each command is user-invoked separately — the flow never chains automatically. Between `/dev:build` and `/dev:commit`, the developer runs the feature locally using `units/<repo>/pr-summary.md § ## How to verify` to sanity-check.

---

## Commands

| Command | Does | Stops at |
|---|---|---|
| `/dev:bootstrap [spec]` | Greenfield — ensure a usable, green product repo exists (scaffolds via the TL on project-zero) | build-ready workspace |
| **`/dev:plan <task>`** | Just-in-time planning — verify TL graph, decide sub-task split, run per-task analysis (Stage 2 scratchpad), detect plan blockers (Stage 3), compose Description + Implementation and push to MC (Stage 4 — only after blockers resolved) | `readyForDev` (blockers `RESOLVED`) or `blocked` |
| **`/dev:resolve --plan <task>`** | Interactive plan-blocker resolution — walks every OPEN PB-### across the task's `dev/*plan-blockers.md`, presents options + TL recommendation per blocker, asks you to pick / type free text / skip, writes Resolution: fields to disk, then invokes `/dev:plan --resume` to fold + compose + push | `readyForDev` (blockers `RESOLVED`) OR still `blocked` if any blockers were skipped |
| **`/dev:build <task>`** | The 11-stage build loop — branch, harness bootstrap, implement, test, security-build-gate (Critical only), `## Acceptance` table, code-context flip, `pr-summary.md` § `## How to verify`. Refuses on unresolved blockers | status `inProgress` (phase `built`) |
| **`/dev:commit <task>`** | The 10-stage commit loop — security-commit-gate (Critical + High), code review (Blocker + Major), acceptance re-verify, semantic-context-merge, push, PR raise | status `devReview` (phase `pr-open`) |
| `/dev:fix-review <task> feedback=<path\|PR>` | Fold reviewer PR comments back in, re-verify, update `units/<repo>/pr-summary.md`; re-run relevant `/dev:commit` stages | status `devReview` (phase `pr-open`) |

`<task>` accepts any of: MC task number (`Task-N` / `Feature-N` / `Subtask-N`), `FEAT-<AREA>-NN` id, `features/<slug>/` folder, sub-task folder path (`features/<slug>/units/<repo>/`), or a bare slug. All three also accept the multi-target forms (`list=<name>`, `requirement=<slug>`, `--all`). **With no target, each one takes every task its gate admits** — `/dev:plan` every `todo`, `/dev:build` every `readyForDev`, `/dev:commit` every `inProgress` + `built` — fanned out bounded by `--concurrency` (default 5). Name a target to do just that one.

Retired in v2.2: **`/dev:validate`** (folded into `/dev:build` Stages 7-9), **`/dev:pr`** (folded into `/dev:commit`).

---

## MC status mapping (v2.2)

Uses MC's existing enum verbatim — no invented local variants.

| Local state | MC status | Set by |
|---|---|---|
| `readyForDev` | `readyForDev` | `/dev:plan` end |
| `blocked` | `readyForDev` (unchanged) | `/dev:plan` when `plan-blockers.md` OPEN |
| `inProgress` (build done) | `inProgress` | `/dev:build` Stage 11 |
| `devReview` | `devReview` | `/dev:commit` Stage 1 |
| `devReview` | `devReview` (unchanged) | `/dev:commit` Stage 7 halt |
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
| `implementation.md` | `/dev:plan` | Ordered implementation steps, files, API/schema changes, test strategy |
| `units/<repo>/plan-blockers.md` | `/dev:plan` | Plan-time blocker resolution log; `status: OPEN \| RESOLVING \| RESOLVED` |
| `implementation.md §2 Impacted components` | `/dev:plan` | 12-dimension code impact |
| `status.md` | all | Local state, owner lock, branch, next action |
| `units/<repo>/status.md § ## Run history` | `/dev:build` | Per-stage log for build loop |
| `units/<repo>/status.md § ## Run history` | `/dev:build` | Detected stack + inferred patterns + per-step evidence |
| `units/<repo>/status.md § ## Acceptance` | `/dev:build` (built) + `/dev:commit` (re-verified) | Parent AC + BR + TS + NFRs → validation → result |
| `units/<repo>/findings.md § ## Security — build` | `/dev:build` Stage 9 | Build-time findings (Critical-blocking) |
| `units/<repo>/pr-summary.md § ## How to verify` | `/dev:build` Stage 11 | Developer-facing manual verification guide |
| `units/<repo>/status.md § ## Run history` | `/dev:commit` | Per-stage log for commit loop |
| `units/<repo>/findings.md § ## Security — commit` | `/dev:commit` Stage 3 | Commit-time findings (Critical + High blocking) |
| `units/<repo>/findings.md § ## Code review` | `/dev:commit` Stage 4 | 4-tier severity findings |
| `units/<repo>/findings.md § ## Context merge` | `/dev:commit` Stage 7 | Semantic merge outcome per unit + index |
| `dev/context-merge-conflicts.md` | `/dev:commit` Stage 7 (on halt) | Human-resolvable merge conflicts |
| `units/<repo>/pr-summary.md` | `/dev:commit` Stage 9 | Reviewer-facing PR body |
| `dev/decisions.md` | all | `DEC-###` audit trail |
| `units/<repo>/status.md § ## Run history (a BLOCKED entry)` | any (on `BLOCKED`) | Structured escalation for human |

Plus each feature’s own `status.md`.

---

## Guardrails

- **`/dev:build` invariant** — runs on a decidable plan or refuses. Never prompts the user mid-run. Plan blockers MUST resolve at `/dev:plan` time.
- **Retry limits** — 3 focused repair attempts per finding, 2 broad re-runs per stage. Exceed → escalate.
- **Never without human approval** — merge a PR, deploy to production, delete production data, modify secrets, change infra permissions, disable security controls, ignore failing tests, or `--no-verify` on push / signing.
- **Scope discipline** — one repo per sub-task; cross-repo edits require a scope escalation.
- **Escalate, don't guess** — business, architecture, security, dependency, or bounds-exceeded → structured `units/<repo>/status.md § ## Run history (a BLOCKED entry)`.

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

**What if `units/<repo>/plan-blockers.md` has OPEN entries?** `/dev:build` refuses. User resolves via `/dev:plan --resume`, ticks the blocker as RESOLVED with a DEC-###, then re-runs `/dev:build`.

**Why two security gates?** Fast build iteration (Critical only) + strict pre-PR check (Critical + High). Same skill, two thresholds.

**Passing unit tests = done?** No. Completion is a filled acceptance map + zero commit-time Blocker/Major/Critical/High + clean semantic merge.

**Can two people build different tasks at once?** Yes. Each task carries an owner lock in `status.md`.

**Why did it stop and escalate?** One of: plan blocker unresolved, ambiguous rule, schema-risk, security concern, unavailable dependency, or bounds-exceeded fix loop. Escalation frames the decision with options + recommendation.

---

## What this plugin records

Installing `dev` registers three hooks (`hooks/hooks.json`) on every prompt you submit, every tool
call, and every session stop — but **they do nothing until you ask them to**. Each one checks for
`~/.claude/metrics/.collect` first; without it they exit before starting, so a fresh install records
nothing.

`/dev:usage-eval` asks the first time you run it and creates the marker on a yes. That is the only
place consent is requested, because it is the only place the data is used.

**Kept:** your prompt text, truncated to the first 4,000 characters · the tool used · file paths,
shell commands, search patterns and URLs from its input · timestamps and the working directory.

**Not kept:** file contents, code bodies, or anything passed to Edit/Write — those are dropped
deliberately so the log cannot hoard source or secrets.

**Where it goes:** `~/.claude/metrics/` on this machine, and nowhere else. The collector makes no
network calls; nothing is uploaded, and there is no server side to this.

**To stop it:** delete `~/.claude/metrics/.collect`. Collection stops on the next prompt, the hooks
stay installed and harmless, and `/dev:usage-eval` will ask again if you ever want it back. Delete
`~/.claude/metrics/` to remove what has already been gathered.

**Why this is written down.** Prompt text is the person's own words. Keeping it is defensible, and a
team evaluating its own usage has a good reason to. Keeping it without saying so is not, and
"silent hooks" in a plugin description is not the same as telling someone.
