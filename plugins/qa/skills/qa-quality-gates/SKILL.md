---
name: qa-quality-gates
description: Author and maintain qa/quality-gates.md — the machine-readable quality-gate contract that declares what "verified" means for a repository, so the dev delivery loop can check readiness and validate features against a real, agreed bar. Use when finalizing a test setup, defining or changing quality gates, or re-checking harness health ("what are our quality gates", "update the coverage floor", "is the harness still green", /qa:health). It lists each required and optional check, the exact command that runs it, and its threshold (coverage floor, which acceptance criteria demand e2e), plus the harness status. The dev readiness gate reads it to know a harness exists; dev-validation reads it to know which suites are required and to what bar. It is the single source of truth for the repo's testing bar — it does not run per-feature validation and does not write feature tests.
---

# QA Quality Gates (the contract the dev loop verifies against)

You own the one file that turns "we have some tests" into "here is exactly what verified means here": `qa/quality-gates.md`. It is written for machines and humans both — the dev readiness gate reads it to confirm a harness exists, and `dev-validation` reads it to know which checks are required, the command for each, and the bar each must clear. Keep it accurate and it makes the whole delivery loop's verification concrete; let it drift and the loop verifies against a lie.

## Operating contract

Read **`delivery-os-conventions`** if it isn't in context. Your input is the proven harness (the commands and thresholds `qa-test-setup` verified green) and the repo's tooling. Your output is `qa/quality-gates.md` (`doc_type: quality-gates`, `produced_by: qa`), created if absent. Follow the exact schema in **`references/quality-gate-contract.md`** so consumers can parse it. If there's no workspace, write it beside the repo and note it.

## What you do

1. **Author / update the contract.** From the proven harness, record each gate: its `QG-###` id, the check (unit, integration, e2e, coverage, lint, format, type, build, contract, security, …), whether it is **Required** or **Optional**, the **exact command** that runs it, its **threshold** (e.g. coverage ≥ 70%, e2e for any acceptance criterion tagged user-journey), and its current **status** (`Passing`/`Failing`/`Not-configured`). Include the canonical green-smoke sequence and the harness status (`Active` once proven, else `Draft`).
2. **State the bar precisely.** "Required" gates are the ones `dev-validation` must run and pass for a feature to advance; "Optional" gates apply where the feature or project calls for them. Name the coverage floor and any rule for when e2e/contract tests are mandatory, so the dev agent isn't guessing what "done" means.
3. **Keep it honest and current.** Never record a gate as `Passing` you haven't proven, and never quietly lower a threshold to make the repo look compliant — a threshold change is a `DEC-###` decision with a rationale. When a check is added or changed, update the contract and bump its `generated_at`.
4. **Health re-check (`/qa:health`).** Re-run the required gates' commands against the current repo and report drift: a gate that flipped to `Failing`, a `Not-configured` that regressed, a threshold no longer met. Surface deltas and recommend fixes; don't silently "repair" by weakening a gate.

   **Three red states, not one.** Collapsing them loses the one thing the reader needs — whether the code is wrong, the test is unreliable, or the check never ran:

   | What happened | `harness_status` | Stamp must say |
   |---|---|---|
   | Required gate ran and failed **consistently** | `Broken` | the failing gate and its output |
   | Required gate failed **intermittently** — a different test each run, or passing in isolation | `Broken` | `flaky`, with **both** run results. A passing retry never erases the failure |
   | Gate **could not run** — service down, env var absent, tool not installed | **`Blocked`** | which prerequisite was missing |

   `Blocked` is not `Broken`: nothing was measured, so nothing failed. Never record `Active` for a gate that did not run.

   **Carry a build's `harness_config_remedy` through.** When the failing gate has one recorded in `dev/implementation-log.md` (Stage 8), reproduce it in the health report instead of restating the symptom — the reader needs the named file and change, not a second description of the red gate.

   **State the working tree.** If it is dirty, say so and scope the results to the tree measured, never to committed state.

## Boundaries

You define and verify the *bar*, you don't do the per-feature work: you don't write feature tests, you don't run a feature's full suite to judge that feature (that's `dev-validation`), and you don't merge or deploy. A threshold or gate change that makes the repo easier to pass is a human decision logged as `DEC-###`, never a silent edit. If a required gate can't be met, escalate with the trade-off — don't drop the gate to go green.

## Return value

Return the gate list (required vs optional, with thresholds and status), the harness status, and — for `/qa:health` — the drift deltas and recommended actions, with a link to `qa/quality-gates.md`.
