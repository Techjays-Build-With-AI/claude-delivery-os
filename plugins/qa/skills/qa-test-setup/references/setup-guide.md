# Setup guide — plan schema, the stand-up checklist, and green-smoke verification

How `/qa:plan` writes the plan and `/qa:setup` builds and proves the harness. The north star: **the harness must be runnable and green with a single sequence of commands, and every check must be real** (no weakening to pass).

---

## 1. `test-setup-plan.md` schema

```yaml
---
doc_type: test-setup-plan
schema_version: 1.1
produced_by: qa
source_audit: 2026-07-05-143210
status: Draft
generated_at: 2026-07-05
---
```

Body:
- **Scope** — the `QAF-###` findings being implemented (the `Adopt` rows), each with the chosen option.
- **Ordered steps** — cheap-to-stand-up-first, each: what it adds, files/config touched, install command, the command that will prove it runs, and the `QAF-###` it satisfies.
- **Tooling to install** — exact packages/versions and the package manager.
- **CI changes** — which workflow/file, which jobs, run order.
- **Thresholds** — coverage floor and any other enforced bars (with the rationale the human approved).
- **Smoke tests** — the example tests that prove each layer runs (harness-level, not feature-level).
- **Deferred / open** — `Defer` rows and any decision the human left open (never silently filled).
- **Rollback** — how to unwind the setup branch cleanly.

---

## 2. Stand-up checklist (build in this order)

1. **Unit runner** — install and configure the test runner; add a `test` script; establish the test-file convention; add one trivial passing example test. Prove: `<test cmd>` runs and is green.
2. **Lint** — configure the linter + rule set; add a `lint` script; fix or baseline existing violations (baseline, don't blanket-disable). Prove: `<lint cmd>` exits clean.
3. **Format** — configure the formatter with a **check** mode; add `format` / `format:check` scripts. Prove: `<format:check cmd>` passes.
4. **Type-check** (typed stacks) — configure the checker; add a `typecheck` script; establish a known baseline. Prove: `<typecheck cmd>` passes.
5. **Coverage** — instrument coverage, emit a machine-readable report, and **enforce** the approved floor so the build fails below it. Prove: coverage runs and the threshold gate works.
6. **CI** — wire the above into CI on push/PR in cheap-to-expensive order, gating merges. Prove: the workflow is valid and the job graph is correct.
7. **Fixtures & test data** — add a sanctioned factory/builder/fixture approach and a between-tests reset, so tests are isolated and deterministic. Prove: an example test uses a factory and passes in isolation and repeated.
8. **Mocking / test doubles** — add utilities to stub external services/APIs/time/randomness deterministically. Prove: an example test mocks a dependency.
9. **E2E harness** (apps with a UI) — install the e2e tool, add a base config that runs headless in CI, and a **page-object/fixtures skeleton**; add one smoke spec (e.g. app loads). Prove: the e2e smoke runs headless and is green. `N/A` for headless services — note why.
10. **Contract/API tests** (services with an API surface) — add a schema/contract-assertion approach mapped to the TL `EP-<AREA>-NN` endpoints; add one example. `N/A` if no API.
11. **Testing conventions doc** — a short `qa-output/testing-conventions.md` (or the repo's docs): where tests live, naming, what each level covers, and the single commands to run each — so the dev agent writes feature tests into the harness consistently.

Mark any step `N/A` with a reason rather than skipping silently. Only build steps whose `QAF-###` the human approved.

---

## 3. Green-smoke verification

The harness is "stood up" only when a single documented sequence runs green end to end:

```text
install → lint → format:check → typecheck → unit → coverage(threshold) → build → e2e:smoke (if applicable)
```

- Run it in the shell against the real repo; **never fabricate** a result.
- Every command in the sequence goes into `qa-output/quality-gates.md` as the canonical command for that gate.
- If a step can't pass **without weakening a check**, stop and escalate — name the trade-off; don't lower the bar to go green.
- Smoke tests prove the *harness* runs; they are not feature tests and are not evidence any feature works.

---

## 4. Handoff to the quality gates

Once green, `qa-quality-gates` promotes `qa-output/quality-gates.md` to `Active` with the proven commands and thresholds. That file is the contract the **dev readiness gate** checks (does a harness exist?) and **dev-validation** reads (which suites are required, to what bar). Keeping it accurate is what makes the dev loop's "verify properly" concrete.
