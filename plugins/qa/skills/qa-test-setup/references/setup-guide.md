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
11. **Testing conventions doc** — a short `qa/testing-conventions.md` (or the repo's docs): where tests live, naming, what each level covers, and the single commands to run each — so the dev agent writes feature tests into the harness consistently.
12. **Async failure-mode harness** *(repos with a consumer, job, webhook, scheduler or async producer)* — what a test needs to replay one message twice and to drive a retry path to exhaustion: a way to publish/invoke directly, control over the clock or backoff, and inspection of the effect. Wire the commands into `QG-014` (idempotency) and `QG-015` (retry-behaviour). Prove: an example asserts one effect from two identical deliveries, and one asserts the terminal state after the retry budget is spent. `N/A` with a reason for a repo with no async surface.
13. **State-transition harness** *(repos where an entity carries a status/lifecycle field)* — what a test needs to put an entity into an arbitrary state and attempt a move from it: a factory or fixture per state, and a way to assert the rejection (thrown error, refusal code, unchanged row). Enumerate the states from the schema or enum, never from the existing tests. Wire into `QG-018`. Prove: one example asserts a legal transition succeeds and one asserts an illegal transition is rejected. `N/A` with a reason for a repo with no stateful entity.
14. **Concurrency harness** *(repos with shared mutable state or a transaction boundary)* — the ability to run two operations against the same record concurrently and assert the invariant. Needs a real backend roundtrip; a mocked double cannot establish it. Wire into `QG-013`. Prove: an example drives a concurrent write and asserts no lost update. `N/A` with a reason for a stateless service.

Mark any step `N/A` with a reason rather than skipping silently. Only build steps whose `QAF-###` the human approved.

**Steps 12–14 are the ones a happy-path suite never covers.** A repo can pass every other gate and still have no way to express "the same event arriving twice must not fill the form twice", or "a cancelled order must never become approved". Where the surface exists and the step is skipped, the gate stays `Not-configured` and the dev loop reports `tier-unavailable` on every build that touches it — visible, but untested.

## 2a. Setting the coverage floor

| Repo | Floor |
|---|---|
| **Existing code** | the **measured** current coverage from the audit, then ratchet upward as tests land. Never a greenfield default — the first build would fail on untouched legacy lines, for reasons no change can influence |
| **Scaffold / new** | the target you intend to **hold**; the codebase grows into it |

Record which of the two applied, and the number, in the plan's Thresholds section with the human's rationale.

---

## 3. Green-smoke verification

The harness is "stood up" only when a single documented sequence runs green end to end:

```text
install → lint → format:check → typecheck → unit → coverage(threshold) → build → e2e:smoke (if applicable)
```

- Run it in the shell against the real repo; **never fabricate** a result.
- Every command in the sequence goes into `qa/quality-gates.md` as the canonical command for that gate.
- If a step can't pass **without weakening a check**, stop and escalate — name the trade-off; don't lower the bar to go green.
- Smoke tests prove the *harness* runs; they are not feature tests and are not evidence any feature works.

---

## 3a. Publish the branch

Once green: commit the harness on the setup branch, push it, and raise a PR — the same four-step ladder `/dev:commit` uses (`gh pr create` → `git credential fill` → `gh auth login --with-token` → a printed `compare/` URL with title and body pre-filled). Report the PR URL in the summary.

**Never merge.** The coverage floor begins gating every teammate's PRs the moment it lands, and the setup may have escalated rather than finished clean — both are human calls.

## 4. Handoff to the quality gates

Once green, `qa-quality-gates` promotes `qa/quality-gates.md` to `Active` with the proven commands and thresholds. That file is the contract the **dev readiness gate** checks (does a harness exist?) and **dev-validation** reads (which suites are required, to what bar). Keeping it accurate is what makes the dev loop's "verify properly" concrete.
