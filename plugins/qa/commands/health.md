---
description: Re-check an existing test harness against its own quality gates to catch drift — a disabled check, a dropped coverage floor, a broken e2e config, a gate that flipped to failing. Read-only re-verification; reports deltas and recommends fixes, never silently repairs by weakening a gate.
argument-hint: "<repo=<path> | (blank = current workspace)>"
---

# /qa:health

You re-verify that the repo still meets the quality gates it claims — a fast drift check over the live harness. Delegate to the **`qa-agent`** subagent, which runs `qa-quality-gates` (health mode).

## 1. Parse arguments

`$ARGUMENTS` may contain an optional **`repo=`** path (default: the current workspace / project repo). If there's no `qa-output/quality-gates.md`, tell the user there's no harness to health-check yet — run `/qa:audit` → `/qa:plan` → `/qa:setup` first — and stop.

## 2. Delegate

Invoke the **qa-agent** subagent. Pass it this instruction:

> Run `/qa:health` using the `qa-quality-gates` skill (health mode) — schema in `references/quality-gate-contract.md`. Read `qa-output/quality-gates.md`, then re-run each **Required** gate's command against the current repo. Report drift: any gate now `Failing`, any `Not-configured` that regressed, any threshold no longer met (including coverage below `coverage_floor`). Update each gate's `Status` and the `harness_status` from the real results (set `Broken` if a Required gate is red). Do **not** repair by weakening a gate — surface the delta and recommend the fix; a threshold change is a human `DEC-###`. Return the gate status table, the drift deltas, and recommended actions.
>
> Repository: `<repo or current workspace>`

## 3. Surface the result

Present the **gate status** (required vs optional, with current status and thresholds) and the **drift deltas** since the gates were set, with recommended actions. Link to `qa-output/quality-gates.md`. If a Required gate is red, lead with it — that's a dev readiness blocker until fixed.
