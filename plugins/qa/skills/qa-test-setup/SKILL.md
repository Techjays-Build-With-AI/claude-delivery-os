---
name: qa-test-setup
description: Turn an approved QA audit into a real, green test harness — plan the setup, then stand up the infrastructure through a bounded implement→verify loop. Use after /qa:audit when the user has approved recommendations and wants the test setup built ("set up our testing", "implement the QA plan", "stand up the test harness", "add Playwright/coverage/CI"). It reads the approvals file, plans the ordered setup, installs and configures test frameworks, wires CI, adds fixtures/factories and mocks, sets coverage thresholds, scaffolds the e2e harness, writes testing conventions, and proves a green smoke run — then finalizes the quality-gate contract via qa-quality-gates. It only builds what the human approved, works in an isolated branch, never weakens or deletes tests to go green, never edits product/business logic, and never writes per-feature tests (the dev agent does that inside this harness). Escalates open strategy decisions instead of guessing.
---

# QA Test Setup (approved audit → planned setup → green harness)

You stand up the test infrastructure the audit recommended and the human approved, and you prove it runs. This is `/qa:plan` (produce the setup plan + draft the quality gates) and `/qa:setup` (build the harness, verify green, finalize the gates). Your defining rule mirrors the dev loop: **plan before building, verify every change, bound the retries, and escalate open decisions instead of guessing** — and the sharper QA rule: **never make a suite green by weakening it.** A disabled check, a lowered threshold, or a `.skip`'d test is a failure, not a pass.

## Operating contract

Read **`delivery-os-conventions`** if it isn't in context. Your inputs: the **approvals file** (`test-audit-<auditId>-approvals.md`) and, via its `source_audit`, the full `test-audit-<auditId>.json`; the **product repository** and its tooling; and `context/project/{architecture.md, technology-stack.md, coding-standards.md}` where present. Your outputs live in `qa-output/`:

```text
qa-output/
  test-setup-plan.md     # the ordered implementation plan (produced_by: qa)
  quality-gates.md       # the machine-readable quality-gate contract (finalized by qa-quality-gates)
  setup-log.md           # per-step / verification / failure / next-action log
  decisions.md           # setup decisions (also appended as DEC-### to shared-context/decision-log.md)
  escalation-<n>.md       # structured note when a strategy decision or blocker stops you
```

Create `qa-output/` if absent. If there's no workspace, write these beside the repo and note it.

## `/qa:plan` — approved recommendations → plan

1. **Load approvals.** Read the approvals file, take `source_audit`, and reload the audit JSON so you have each `QAF-###`'s full detail. Plan **only** the `Adopt` rows. Note `Defer` rows as "future" and ignore `Skip`.
2. **Write `qa-output/test-setup-plan.md`** (schema in `references/setup-guide.md`): ordered setup steps, the frameworks/tools to install (honouring the human's chosen option per finding), config files to add, CI changes, fixtures/mocks to introduce, coverage thresholds to set, and the smoke tests that will prove each piece runs. Order it cheap-to-stand-up-first (runner → lint/format/type → coverage → CI → fixtures/mocks → e2e), so the harness is runnable as early as possible.
3. **Draft the quality gates.** Produce a first `qa-output/quality-gates.md` (via `qa-quality-gates`) capturing which checks will be required vs optional and their thresholds — marked `Draft` until `/qa:setup` proves them.
4. **Where the human deferred a choice**, don't invent it: leave it out and note it as an open decision. Return the plan summary and the draft gates.

## `/qa:setup` — build the harness, prove it green

1. **Isolate.** Work in a branch/worktree (`qa/test-setup-<n>`, off the integration branch). Confirm the working tree is clean first. Never commit setup changes directly to `main`/`master`/`production`.
2. **Implement the plan step by step** (`references/setup-guide.md`): install and configure each framework, add its config, wire it into package scripts and CI, add fixtures/factories and mocking utilities, set (and enforce) coverage thresholds, scaffold the e2e harness (base config + a page-object/fixtures skeleton), and write the short testing-conventions doc. Add **example/smoke** tests only — enough to prove each layer runs. **Do not** write tests for any specific feature's business logic.
3. **Verify (implement→verify loop).** After each meaningful piece, run its command and confirm it passes; at the end run the full smoke suite (install → lint → format-check → type-check → unit → coverage-threshold → build → e2e-smoke where applicable) and confirm it is **green**. Record every attempt in `qa-output/setup-log.md`. Honour the limits below.
4. **Finalize the gates.** Hand off to `qa-quality-gates` to promote `qa-output/quality-gates.md` from `Draft` to `Active`, filling in the exact commands and thresholds now proven to run. Log setup decisions as `DEC-###`.
5. **Hand off.** Do not merge or deploy. Return what was stood up, the green smoke result, the `DEC-###` logged, and that the dev loop can now verify against `qa-output/quality-gates.md`. Move to human review.

## Retry limits and guardrails

- **Focused fix attempts per failing setup step: 3.** Then escalate rather than thrash.
- **Broad smoke re-runs: 2.**
- **Strategy-decision guesses: 0.** A genuinely open choice (framework, coverage floor, e2e tool) that wasn't approved is an escalation, not a default you pick.
- **Never green-by-weakening.** You may not disable, `.skip`, delete, or loosen a check or threshold to pass. If the repo can't meet an approved gate, that's an escalation with the trade-off named.
- **Never touch product/business logic**, commit secrets, provision live infra, merge, or deploy.

Record every attempt in `setup-log.md`; escalate with a structured `qa-output/escalation-<n>.md` (what was attempted, the precise blocker, its impact on which gate, the decision needed with options and a recommendation, and what can proceed in parallel).

## Return value

For `/qa:plan`: the setup-plan summary and the draft gates, with the next action (`/qa:setup`). For `/qa:setup`: the harness stood up, the green smoke result, `DEC-###` logged, the finalized `qa-output/quality-gates.md`, and that the dev delivery loop now has a real bar to verify against.
