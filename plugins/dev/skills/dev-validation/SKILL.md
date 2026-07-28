---
name: dev-validation
description: Run a feature's validation suite and map the results to its business acceptance criteria as evidence. Use whenever the delivery loop needs to prove a change — "run the tests", "validate the feature", "check acceptance criteria", "is this feature done" — or in validate-only mode. It runs the applicable checks (lint, format, type-check, unit, integration, API-contract, end-to-end, build, database-migration validation, security scan, dependency check, plus feature-specific acceptance tests), records every result in the implementation log, and builds the acceptance map that ties each acceptance criterion to a validation method, a pass/fail result, and an evidence artifact. It treats passing unit tests alone as insufficient — completion is the acceptance map, not a green unit run. It is the test-runner and acceptance-validator half of the dev agent; it does not implement fixes (the delivery loop's repair step does) and it does not merge or deploy.
---

# Dev Validation (run the suite, map results to acceptance criteria)

You prove a feature works. The delivery loop implements; you run the checks and turn raw pass/fail into **evidence against the acceptance criteria**. Your defining rule: a green unit run is not "done" — **done is a filled acceptance map** where every mandatory acceptance criterion has a validation method, a result, and a named evidence artifact.

## Operating contract

Read **`delivery-os-conventions`** and the delivery loop's `references/dev-context-templates.md` (the `acceptance-map.md` and `implementation-log.md` schemas) if not in context. Your inputs are the feature's `acceptance-criteria.md`, the product repo's test/lint/build tooling, and the changes under test. Your outputs are appended to `dev/implementation-log.md` (raw results) and written to `dev/acceptance-map.md` (the evidence table). Run checks in the shell against the real repo; never fabricate a result.

## What you run

**Read the QA quality-gate contract first.** If `qa-output/quality-gates.md` exists (`produced_by: qa`), it is the authority for what "verified" means in this repo: it lists the **Required** gates, the exact command for each, and the thresholds (coverage floor, when e2e/contract tests are mandatory). Run every Required gate's command, plus any Optional gate whose rule the feature triggers (e.g. a `user-journey` acceptance criterion → e2e; a changed `EP-<AREA>-NN` contract → contract test), and enforce the `coverage_floor` on the feature's changes. This is what lets you validate against an agreed bar rather than guessing the tooling. If the contract is **absent** (the qa plugin isn't in use), fall back to detecting the toolchain from the repo and note in the results that no quality-gate contract was found — verification used detected tooling, not an agreed bar.

**Applied-AI features — evals are a check.** If the feature is AI-bearing (`delivery-os-conventions` §5) and the TL designed `EVAL-<AREA>-NN` units under `context/evals/`, treat each eval's verifier as a required check for its AI-driven acceptance criterion: run it (wiring the live-vs-simulated tool calls it declares), record the result, and — because model output is non-deterministic — **inspect the trajectory as well as the verifier verdict** so a reward-hacked pass doesn't count. Use the core **`eval-engineering`** skill and the loop's **`references/eval-runner.md`**. Deterministic features have no evals; the standard suite proves them.

Run the checks in `references/validation-suite.md` that **apply** to the change — mark the rest `N/A` rather than skipping silently. Order them cheap-to-expensive so failures surface fast: lint/format → type-check → unit → integration/API-contract → build → migration validation → security/dependency scan → end-to-end → feature-specific acceptance tests. When the quality-gate contract is present, its commands and Required set take precedence over guessed ones; otherwise detect the toolchain from the repo (package scripts, Makefile, CI config).

## Workflow

1. **Read** `acceptance-criteria.md` and the plan's test strategy so you know what each criterion needs to be proven.
2. **Detect** the repo's tooling and the applicable check set.
3. **Run** each applicable check in cheap-to-expensive order. Capture the command, the result, and the failing output for anything red. Append a dated entry to `dev/implementation-log.md`.
4. **Map** every acceptance criterion to a validation method, a result (`Passed` · `Failed` · `Blocked` · `Waived` · `Not Covered`), and an evidence artifact (test file, run output, screenshot). Write/refresh `dev/acceptance-map.md`. A criterion with no automated or manual coverage is `Not Covered` — flag it, don't hide it.
5. **Report** the summary: suite results, the acceptance-map pass/fail table, and any `Failed`/`Blocked`/`Not Covered` rows that the loop must repair or escalate. Hand failures back to the delivery loop's repair step with enough detail (cause, failing artifact) to act — you don't fix them here.

## Boundaries

You run and record; you don't implement fixes, redesign contracts, waive criteria (only a human waives), merge, or deploy. If validation needs external access you don't have, or a criterion can't be validated because its rule is undefined, that's a `Blocked` row for the loop to escalate — not a pass.

## Return value

Return the suite summary and the acceptance-map table, calling out every non-`Passed` row and whether it is actionable (→ repair) or a blocker (→ escalate).
