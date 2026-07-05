---
name: qa-quality-gates
description: Author and maintain qa-output/quality-gates.md — the machine-readable quality-gate contract that declares what "verified" means for a repository, so the dev delivery loop can check readiness and validate features against a real, agreed bar. Use when finalizing a test setup, defining or changing quality gates, or re-checking harness health ("what are our quality gates", "update the coverage floor", "is the harness still green", /qa:health). It lists each required and optional check, the exact command that runs it, and its threshold (coverage floor, which acceptance criteria demand e2e), plus the harness status. The dev readiness gate reads it to know a harness exists; dev-validation reads it to know which suites are required and to what bar. It is the single source of truth for the repo's testing bar — it does not run per-feature validation and does not write feature tests.
---

# QA Quality Gates (the contract the dev loop verifies against)

You own the one file that turns "we have some tests" into "here is exactly what verified means here": `qa-output/quality-gates.md`. It is written for machines and humans both — the dev readiness gate reads it to confirm a harness exists, and `dev-validation` reads it to know which checks are required, the command for each, and the bar each must clear. Keep it accurate and it makes the whole delivery loop's verification concrete; let it drift and the loop verifies against a lie.

## Operating contract

Read **`delivery-os-conventions`** if it isn't in context. Your input is the proven harness (the commands and thresholds `qa-test-setup` verified green) and the repo's tooling. Your output is `qa-output/quality-gates.md` (`doc_type: quality-gates`, `produced_by: qa`), created if absent. Follow the exact schema in **`references/quality-gate-contract.md`** so consumers can parse it. If there's no workspace, write it beside the repo and note it.

## What you do

1. **Author / update the contract.** From the proven harness, record each gate: its `QG-###` id, the check (unit, integration, e2e, coverage, lint, format, type, build, contract, security, …), whether it is **Required** or **Optional**, the **exact command** that runs it, its **threshold** (e.g. coverage ≥ 70%, e2e for any acceptance criterion tagged user-journey), and its current **status** (`Passing`/`Failing`/`Not-configured`). Include the canonical green-smoke sequence and the harness status (`Active` once proven, else `Draft`).
2. **State the bar precisely.** "Required" gates are the ones `dev-validation` must run and pass for a feature to advance; "Optional" gates apply where the feature or project calls for them. Name the coverage floor and any rule for when e2e/contract tests are mandatory, so the dev agent isn't guessing what "done" means.
3. **Keep it honest and current.** Never record a gate as `Passing` you haven't proven, and never quietly lower a threshold to make the repo look compliant — a threshold change is a `DEC-###` decision with a rationale. When a check is added or changed, update the contract and bump its `generated_at`.
4. **Health re-check (`/qa:health`).** Re-run the required gates' commands against the current repo and report drift: a gate that flipped to `Failing`, a `Not-configured` that regressed, a threshold no longer met. Surface deltas and recommend fixes; don't silently "repair" by weakening a gate.

## Boundaries

You define and verify the *bar*, you don't do the per-feature work: you don't write feature tests, you don't run a feature's full suite to judge that feature (that's `dev-validation`), and you don't merge or deploy. A threshold or gate change that makes the repo easier to pass is a human decision logged as `DEC-###`, never a silent edit. If a required gate can't be met, escalate with the trade-off — don't drop the gate to go green.

## Return value

Return the gate list (required vs optional, with thresholds and status), the harness status, and — for `/qa:health` — the drift deltas and recommended actions, with a link to `qa-output/quality-gates.md`.
