# Quality-gate contract — the schema dev reads

`qa/quality-gates.md` is the single source of truth for what "verified" means in this repo. It must be **parseable and unambiguous** because three consumers depend on it:

- The **dev readiness gate** (`feature-delivery-loop` → `readiness-and-planning.md` §1b) reads it to confirm a usable test harness exists before building a feature.
- **`dev-validation`** reads it to know which checks are **Required**, the exact command for each, and the threshold each must clear — instead of guessing the repo's tooling.
- The **TL maturity audit** (`tl-maturity-audit`) reads `baseline_status` in its preflight to decide whether the mandatory tooling floor is in place before scoring, and consumes the coverage/gate results as its Test-Quality domain evidence instead of re-scoring testability.

Keep the frontmatter and the gate table stable; consumers key off them.

## Frontmatter

```yaml
---
doc_type: quality-gates
schema_version: 1.4
produced_by: qa
harness_status: Active        # Active (proven green) | Stack-Inferred (tiers inferred from stack detection, not confirmed by audit) | Draft (planned, not yet proven) | Broken (a Required gate ran and failed) | Blocked (a Required gate could not run — missing service, env var or tool)
baseline_status: Met          # Met | Unmet — every mandatory BL-## in baseline-profile.md is present AND enforced
baseline_unmet: []            # list of unmet mandatory BL-## ids when baseline_status is Unmet, e.g. [BL-08, BL-09]
coverage_floor: 70            # percent; the enforced minimum, or null if not enforced
source_audit: 2026-07-05-143210
generated_at: 2026-07-05
---
```

## Baseline status — the mandatory floor

`harness_status` says the *test harness* is proven green. `baseline_status` says something broader: every **mandatory** capability in the active `baseline-profile.md` (the org default, or a `shared-context/baseline-profile.md` override) is **present and enforced** — linting/format/type in pre-commit + CI, coverage threshold-gated, CI gating merges, plus dependency and secret scanning (`BL-01`…`BL-10`).

- `/qa:audit` flags every unmet mandatory `BL-##` as a **mandatory gap** (see `qa-test-audit/references/audit-rubric.md`), and `/qa:setup` stands them up. `baseline_status` flips to `Met` only when all mandatory items are enforced.
- A mandatory item can't be silently skipped; skipping one is a `DEC-###` with a rationale, and it stays listed in `baseline_unmet` with a note.
- The TL maturity audit reads `baseline_status`: `Met` → score at full fidelity; `Unmet` → remind + route to `/qa:audit` → `/qa:setup` (or, in strict mode, stop before scoring).

## Green-smoke sequence

The single documented command sequence that proves the harness runs green end to end — the same one `qa-test-setup` verified. List it explicitly so anyone (or the dev loop) can reproduce it:

```text
1. <install cmd>
2. <lint cmd>
3. <format:check cmd>
4. <typecheck cmd>
5. <unit cmd>
6. <coverage cmd + threshold enforcement>
7. <build cmd>
8. <e2e:smoke cmd>   # or N/A — headless service
```

## Gate table

One row per gate. `Required` gates are what `dev-validation` must run and pass for a feature to advance; `Optional` gates apply where the feature/project calls for them.

| Gate | Check | Required? | Command | Threshold / rule | Status |
|---|---|---|---|---|---|
| QG-001 | Lint | Required | `<lint cmd>` | zero errors (baseline: N warnings) | Passing |
| QG-002 | Format | Required | `<format:check cmd>` | no diffs | Passing |
| QG-003 | Type-check | Required | `<typecheck cmd>` | zero errors | Passing |
| QG-004 | Unit | Required | `<unit cmd>` | all pass | Passing |
| QG-005 | Coverage | Required | `<coverage cmd>` | ≥ coverage_floor | Passing |
| QG-006 | Build | Required | `<build cmd>` | succeeds | Passing |
| QG-007 | Integration | Required* | `<integration cmd>` | all pass | Passing |
| QG-008 | E2E | Optional | `<e2e cmd>` | required for user-journey criteria | Passing |
| QG-009 | Contract | Optional | `<contract cmd>` | API/contract surface — required when an `EP-<AREA>-NN` contract changes | Not-configured |
| QG-010 | Security scan | Optional | `<security cmd>` | no high/critical | Not-configured |
| QG-011 | AI evals | Optional | `<eval-runner cmd>` | required for applied-AI features — runs the TL's `EVAL-<AREA>-NN` verifiers | Not-configured |
| QG-012 | Component | Required* | `<component cmd>` | required once a rendered UI surface exists | Not-configured |
| QG-013 | Concurrency | Required* | `<concurrency cmd>` | required once shared mutable state or a transaction boundary exists | Not-configured |
| QG-014 | Idempotency | Required* | `<idempotency cmd>` | required once a consumer, job, webhook or async producer exists — same input applied twice leaves one effect | Not-configured |
| QG-015 | Retry-behaviour | Required* | `<retry cmd>` | required once any retry/backoff path exists — covers exhaustion, not just the happy retry | Not-configured |
| QG-016 | Accessibility | Optional | `<a11y cmd>` | required when an a11y NFR is declared | Not-configured |
| QG-017 | Load | Optional | `<load cmd>` | required when a latency/throughput NFR is declared | Not-configured |
| QG-018 | State-transition | Required* | `<state cmd>` | required once an entity carries a status/lifecycle field — every legal move asserted **and every illegal one rejected** | Not-configured |

- **Status** values: `Passing` · `Failing` · `Not-configured`. Never record `Passing` unproven.
- **`Required*`** = required only if the applicable surface exists (e.g. integration required once there's a DB/service; contract required once an API surface exists). State the condition in the rule column.
- **When e2e/contract is mandatory** — spell out the rule (e.g. "any acceptance criterion tagged `user-journey` requires an e2e; any change to an `EP-<AREA>-NN` contract requires a contract test") so the dev agent knows when an Optional gate becomes obligatory for a given feature.
- **AI evals (applied-AI features).** When a feature is AI-bearing (`delivery-os-conventions` §5), its verification includes the TL-designed `EVAL-<AREA>-NN` evals (core `eval-engineering` skill). QA owns only the **harness** they run on — the eval *design* is the TL's and the *run + inspection* is the dev loop's. Expose an eval-runner command here (QG-011) if the project standardizes one; otherwise the dev loop runs them directly. Non-AI features have no eval gate.

## Tier pool — how dev reads this table

**The gate table IS the tier pool.** `dev-stack-adaptive-implementation` intersects a build step's *concern class* with the Required tiers declared here; a gate's **Check** name is the tier name it declares. `Unit`, `Integration`, `Contract`, `E2E`, `Component`, `Concurrency`, `Idempotency`, `Retry-behaviour`, `State-transition`, `Accessibility` and `Load` are all tier names dev matches on — there is no separate structure to author.

A tier is available to the intersection when its row is `Required`, or `Required*` **and its condition holds for this repo**. A row left `Not-configured` while its condition holds is a gap, not an opt-out:

> If a build step's concern class matches but the intersection comes out **empty**, dev reports `tier-unavailable` rather than writing zero tests. That report names the tier this contract is missing — treat it as a QA finding on the next `/qa:audit`.

This is the mechanism that keeps an untestable concern visible. An async consumer with no `QG-014` row does not quietly get no tests; it gets a named gap.

## Change rules

- Adding, tightening, or **loosening** a gate or threshold is a `DEC-###` decision in `shared-context/decision-log.md` with a rationale — never a silent edit. Lowering `coverage_floor` especially must be justified and human-approved.
- A `Required*` gate whose **condition holds** but whose command is `Not-configured` is a **reportable gap**, never a silent pass. `/qa:audit` raises it as a `QAF-###`; `/qa:health` reports it; dev reports it as `tier-unavailable`. Deciding not to configure one is a `DEC-###` with a rationale, not an omission.
- On any change, bump `generated_at`; if a required gate goes red, set `harness_status: Broken` and surface it (that's a dev readiness blocker until fixed).
- `/qa:health` re-runs the Required gates and updates `Status` + `harness_status` from real results.

## How dev consumes this (informative)

- **Readiness gate:** `harness_status: Active` (and the runner/coverage gates present) → harness exists, proceed. `Draft`/`Broken` or file absent → route to QA (`/qa:audit` → `/qa:setup`), analogous to the project-zero → bootstrap route.
- **dev-validation:** run every `Required` gate's command, plus any `Optional` gate whose rule the feature triggers; map results into the feature's `acceptance-map.md`. The `coverage_floor` is the enforced minimum for the feature's changes. For an AI-bearing feature it also runs the TL's `EVAL-` verifiers (QG-011 or directly) and inspects them for reward hacking.
