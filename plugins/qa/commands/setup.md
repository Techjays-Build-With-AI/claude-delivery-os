---
description: Implement the approved test-setup plan — install and configure frameworks, wire CI, add fixtures/mocks and coverage thresholds, scaffold the e2e harness, prove a green smoke run, and finalize qa-output/quality-gates.md (the contract the dev loop verifies against). Works in an isolated branch; never weakens or deletes tests to go green; never writes per-feature tests or edits product logic; never merges or deploys.
argument-hint: "<(blank = use qa-output/test-setup-plan.md) | plan=<path>> [repo=<path>]"
---

# /qa:setup

You stand up the test harness the plan describes and **prove it runs green**, then finalize the quality-gate contract the dev delivery loop reads. Delegate to the **`qa-agent`** subagent, which runs `qa-test-setup` in its own context.

## 1. Parse arguments

`$ARGUMENTS` may contain an optional **`plan=`** path (default: `qa-output/test-setup-plan.md`) and an optional **`repo=`** path (default: the current workspace / project repo). If there's no setup plan, tell the user to run `/qa:audit` → `/qa:plan` first and stop — don't build without an approved plan.

## 2. Delegate

Invoke the **qa-agent** subagent. Pass it this instruction:

> Run `/qa:setup` using the `qa-test-setup` skill (build phase) — follow `references/setup-guide.md`. Read `qa-output/test-setup-plan.md`. Work in an isolated branch (`qa/test-setup-<n>`, off the integration branch — never on main/master/production) with a clean working tree. Implement the plan step by step in stand-up order: install and configure each framework, add its config, wire package scripts and CI, add fixtures/factories and mocking utilities, set and **enforce** the approved coverage threshold, scaffold the e2e harness (base config + page-object/fixtures skeleton), and write the testing-conventions doc. Add **example/smoke** tests only — never per-feature business-logic tests. After each piece run its command and confirm green; then run the full green-smoke sequence (install → lint → format:check → typecheck → unit → coverage(threshold) → build → e2e:smoke where applicable) and confirm it passes. Honour the limits: 3 focused fixes per failing step, 2 broad smoke re-runs, 0 strategy guesses; **never** disable, skip, delete, or loosen a check/threshold to go green — that's an escalation with the trade-off named, written to `qa-output/escalation-<n>.md`. Log each attempt in `qa-output/setup-log.md` and material decisions as `DEC-###`. Finalize `qa-output/quality-gates.md` via `qa-quality-gates` — promote `harness_status` to `Active` with the proven commands and thresholds. Do not merge or deploy. Return what was stood up, the green-smoke result, the `DEC-###` logged, and the finalized gates.
>
> Repository: `<repo or current workspace>` · Plan: `<plan path>`

## 3. Surface the result

Present what was **stood up** (frameworks, CI, coverage floor, e2e harness, conventions), the **green-smoke result**, the `DEC-###` decisions logged, and the finalized `qa-output/quality-gates.md`. Tell the user the dev delivery loop can now verify features against these gates — the readiness gate will see the harness and `dev-validation` will run the Required gates. If setup hit a blocker, lead with the decision needed (the escalation note) instead of a partial success. Note it stops at human review and never merges.
