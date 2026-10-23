# Setup guide — plan schema, the stand-up checklist, and green-smoke verification

How `/qa:plan` writes the plan and `/qa:setup` builds and proves the harness. The north star: **the harness must be runnable and green with a single sequence of commands, and every check must be real** (no weakening to pass).

---

## 1. `qa/<repo>-setup.md` — the build record

**One file per repo, two halves.** `/qa:plan` writes `## Plan`; `/qa:setup` appends to `## Run history`. Plan
then execution in one file — the same pattern `units/<repo>/status.md` uses, and for the same reason: a resume
wants one read.

The `<repo>-` prefix is there even on a single-repo workspace, so no consumer needs a special case.

```yaml
---
doc_type: qa-setup
schema_version: 2.0
produced_by: qa
repo: backend                     # the slug; matches cache/repolocation.json and quality-gates.md § backend
source_audit: 2026-10-16-142203   # the audit round this plan was approved from
status: Draft                     # Draft (planned) · Building · Active (green smoke passed) · Blocked
generated_at: 2026-10-16
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

**Only `Adopt` rows appear here.** `Defer` rows are listed under *Deferred / open* so they are not lost, and
`Skip` rows are absent. **A decision the human left open is never filled in** — it goes to *Deferred / open*
and stops `/qa:setup`, because guessing a framework is the one thing this flow must not do.

### `## Run history` — written by `/qa:setup`, append-only

```md
## Run history

### 2026-10-16T15:02:11Z · step 1/11 · test runner
- add:    pytest 8.3 · pytest-cov 5.0        (poetry add --group dev)
- prove:  poetry run pytest -q → exit 0, 0 collected
- QAF-002

### 2026-10-16T15:14:40Z · step 4/11 · type check
- add:    mypy 1.11 + pyproject config
- prove:  poetry run mypy app → exit 1, 34 errors
- attempt 1: narrowed to `app/api` — exit 1, 11 errors
- attempt 2: added `ignore_missing_imports` for 3 untyped deps — exit 0
- QAF-005 · 2 of 3 focused fixes used

### 2026-10-16T15:41:08Z · green smoke
- install → lint → format:check → typecheck → unit → coverage(40%) → build
- result: PASS · 4m12s
- quality-gates.md § backend → harness_status: Active

### 2026-10-16T15:44:00Z · ESCALATED
- step:   9/11 · e2e harness
- why:    the staging API needs a seeded tenant that does not exist
- trade-off: shipping without e2e leaves AC-08 and AC-11 unverifiable at build time
- NOT done: the threshold was not lowered and no test was skipped to go green
- DEC-054
```

**Every step records what it added, the command that proved it, and that command's exit code.** A step with no
proving command is a step that was not verified, and the whole point of this file is being able to tell those
apart afterwards.

**Bounds: 3 focused fixes per failing step, 2 broad smoke re-runs, 0 strategy guesses.** Record each attempt —
the attempts are the evidence that the bound was respected.

**An escalation is a history entry, not a separate file**, and it must name the **trade-off**, not just the
blocker. It must also state what was *not* done: never weaken a check, lower a threshold, skip or delete a test
to reach green. That is the one failure mode this record exists to make visible.

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
11. **Testing conventions doc** — a short `qa/quality-gates.md` § `<repo>` → `## Conventions` (or the repo's docs): where tests live, naming, what each level covers, and the single commands to run each — so the dev agent writes feature tests into the harness consistently.
12. **Async failure-mode harness** *(repos with a consumer, job, webhook, scheduler or async producer)* — what a test needs to replay one message twice and to drive a retry path to exhaustion: a way to publish/invoke directly, control over the clock or backoff, and inspection of the effect. Wire the commands into `QG-014` (idempotency) and `QG-015` (retry-behaviour). Prove: an example asserts one effect from two identical deliveries, and one asserts the terminal state after the retry budget is spent. `N/A` with a reason for a repo with no async surface.
13. **State-transition harness** *(repos where an entity carries a status/lifecycle field)* — what a test needs to put an entity into an arbitrary state and attempt a move from it: a factory or fixture per state, and a way to assert the rejection (thrown error, refusal code, unchanged row). Enumerate the states from the schema or enum, never from the existing tests. Wire into `QG-018`. Prove: one example asserts a legal transition succeeds and one asserts an illegal transition is rejected. `N/A` with a reason for a repo with no stateful entity.
14. **Concurrency harness** *(repos with shared mutable state or a transaction boundary)* — the ability to run two operations against the same record concurrently and assert the invariant. Needs a real backend roundtrip; a mocked double cannot establish it. Wire into `QG-013`. Prove: an example drives a concurrent write and asserts no lost update. `N/A` with a reason for a stateless service.

Mark any step `N/A` with a reason rather than skipping silently. Only build steps whose `QAF-###` the human approved.

**Steps 12–14 are the ones a happy-path suite never covers.** A repo can pass every other gate and still have no way to express "the same event arriving twice must not fill the form twice", or "a cancelled order must never become approved". Where the surface exists and the step is skipped, the gate stays `Not-configured` and the dev loop reports `tier-unavailable` on every build that touches it — visible, but untested.

## 2a. Setting the coverage floor

| Repo | Floor |
|---|---|
| **Existing code** | the **measured** current coverage from the audit, rounded **down**, then ratchet upward as tests land. Never a greenfield default — the first build would fail on untouched legacy lines, for reasons no change can influence |
| **Scaffold / new** | the target you intend to **hold**; the codebase grows into it |

**The same rule governs every inherited-finding gate, not just coverage.** Dependency scanning (`BL-08`)
and secret scanning (`BL-09`) run against a repo whose history you did not write. Set them to **gate new
findings, not existing ones**:

| | |
|---|---|
| Right | scan runs in CI · current findings recorded as the baseline · build fails when a **new** one appears |
| Wrong | `npm audit --audit-level=high` failing on 51 vulnerabilities the branch did not introduce |

A gate that is red on arrival is not enforcement. It is a gate every teammate learns to pass with `--force`,
and it is red for reasons no change in that PR can influence — which is the exact failure the coverage floor
produces. **`BL-08` asks that dependency scanning be present and enforced, not that the repo have zero
findings.** A scan that reports, baselines and blocks regressions satisfies it completely.

**Round down, never up, and never to a nicer number.** A repo measuring `4.49%` gets a floor of `4`, not `5`.
Rounding up by half a point sets a bar the code cannot clear until someone writes tests — so the harness goes
red on its very first CI run, on a branch that changed no product code. This has happened: `Coverage for
lines (4.49%) does not meet global threshold (5%)`, straight after setup.

**The floor is a fact about the repo, not a target.** The target is what the ratchet moves toward, and it
belongs in the plan's rationale, not in the gate that blocks every teammate's PR tomorrow morning.

Record which of the two applied, the measured number it came from, and the floor you set, in the plan's
Thresholds section with the human's rationale.

---

## 3. Green-smoke verification

The harness is "stood up" only when a single documented sequence runs green end to end:

```text
install → lint → format:check → typecheck → unit → coverage(threshold) → build → e2e:smoke (if applicable)
```

- Run it in the shell against the real repo; **never fabricate** a result.
- Every command in the sequence goes into `qa/quality-gates.md` as the canonical command for that gate.

**Run the exact command CI runs — same script, same flags, same config.** This is the one invariant that
makes a green smoke mean anything, and it is how a run reports every gate green and then fails CI minutes
later:

```
local:  ✓ coverage            ← ran the suite, never applied a threshold
CI:     ✗ Coverage for lines (4.49%) does not meet global threshold (5%)
```

Both are true of *different commands*. `4.49 < 5` fails anywhere it is actually enforced, so a local pass
proves only that the threshold was not in the command. **A gate whose local command differs from its CI
command is not verified** — it is two unrelated results wearing one name.

So, for every gate:

| | |
|---|---|
| The command | read it **out of the CI workflow you just wrote**, do not compose a near-equivalent |
| Coverage specifically | the run must **fail** below the floor. Prove it: the command exits non-zero when the floor is above current coverage. A coverage command that always exits 0 is a report, not a gate |
| The config | one source. A threshold in CI-only config that the local command never loads is the same divergence by another route |

**Prove the gate bites, not just that it runs.** Step 5 says "the threshold gate works" — that means
observing a non-zero exit, once, deliberately. A gate nobody has ever seen fail is a gate nobody has tested.
- If a step can't pass **without weakening a check**, stop and escalate — name the trade-off; don't lower the bar to go green.
- Smoke tests prove the *harness* runs; they are not feature tests and are not evidence any feature works.

---

## 3a. Check the gate values against reality, then publish

**A red coverage gate here is almost always the floor, not the tests.** The one failure this has actually
produced is a floor set above what the repo measures:

```
ERROR: Coverage for lines (4.49%) does not meet global threshold (5%)
```

Nothing in the repo can clear that until someone writes tests, so it fails on every CI run from the moment
it lands — on a branch that changed no product code.

**Before the smoke run, check every threshold against its measured value.** For coverage that means §2a:
an existing repo is floored at its measured number **rounded down**. 4.49 gives `4`. If the plan carries a
higher figure, the plan is wrong.

**If the coverage gate fails and `floor > measured`, correct the floor, log it, and re-run.** That is not
the forbidden "lowering a threshold to go green":

| | |
|---|---|
| **Weakening a check** | dropping a bar the code **did** clear, so a real failure stops failing. Never do this — escalate instead |
| **Correcting a value** | fixing a bar the code could **never** clear, set from the wrong number. Do it, log a `DEC-###` with the measured figure beside both floors, and say so in `## Run history` |

The distinction is whether the gate was ever satisfiable. Record which one applied — a reader six weeks from
now cannot tell them apart from the diff alone.

**Publish either way.** A harness that never leaves the machine is not a harness: a teammate's clone has no
gates, so `/dev:build` Stage 4 bootstraps a different one and the two diverge silently. So push and raise the
PR even when a step is still red — but **never describe a red run as green**:

| Sequence result | `harness_status` | What the summary and PR body say |
|---|---|---|
| All green | `Active` | the proven commands and thresholds |
| Red, floor corrected, re-run green | `Active` | the correction, with measured-vs-floor and the `DEC-###` |
| Still red after the correction | `Blocked` | the command, its exit code, its output, and that the PR will fail CI until it is fixed |

**`harness_status` and `baseline_status` are different fields with different consequences.** A red
*harness* gate means `/dev:build` cannot run. A red *baseline* item means `/tl:maturity` scores in degraded
mode and keeps reminding you — the dev loop is fine. Never report a baseline failure as a blocked harness:

| What failed | `harness_status` | `baseline_status` |
|---|---|---|
| A smoke-sequence gate (lint, unit, coverage, build) | `Blocked` | unchanged |
| A baseline item only (`BL-08` dependency, `BL-09` secrets) | **`Active`** — the harness works | `Unmet`, with the id in `baseline_unmet` |

**Name the command that fixes them.** A baselined `BL-08` must print `/dev:build --vulnerable` in the
summary — that mode exists for exactly these findings and runs them against the harness you just stood up.
Reporting the advisories and stopping is how the work gets lost: the dev security reviews only see the
feature diff, so a pre-existing framework advisory is in nobody's path.

**Never fix them inside this run.** A framework major is a product change, and this is the moment the repo
has the least coverage it will ever have.

**A `Blocked` harness still gets its PR**, titled so nobody mistakes it for ready. What must not happen is a
red run reported as a green one, or `Active` written over a sequence that did not pass.

Commit the harness on the setup branch — cut from the base the user confirmed at the start of the run, never from whatever was checked out — push it, and raise a PR — the same four-step ladder `/dev:commit` uses (`gh pr create` → `git credential fill` → `gh auth login --with-token` → a printed `compare/` URL with title and body pre-filled). **Use the repo’s own `PULL_REQUEST_TEMPLATE` when it has one** — `stage-8-9-push-pr.md` §9b.0 — and never tick its checkboxes on the author’s behalf; name the items this run has evidence for instead. Report the PR URL in the summary — or, where the ladder reached its step 4, say plainly that the branch is pushed and the PR still has to be opened from the printed compare URL. Never report a compare link as a raised PR.

**Never merge.** The coverage floor begins gating every teammate's PRs the moment it lands, and the setup may have escalated rather than finished clean — both are human calls.

## 4. Handoff to the quality gates

Once green, `qa-quality-gates` promotes `qa/quality-gates.md` to `Active` with the proven commands and thresholds. That file is the contract the **dev readiness gate** checks (does a harness exist?) and **dev-validation** reads (which suites are required, to what bar). Keeping it accurate is what makes the dev loop's "verify properly" concrete.
