# Test Coverage Runbook

Every command, in order. **The QA sequence is the same in every situation** — `/qa:audit` → `/qa:plan` → `/qa:setup`, once per repo. What changes afterwards is only which dev command you run.

---

## Run the QA sequence once — in every situation

`/qa:audit` → `/qa:plan` → `/qa:setup`. New repo, existing repo, or a repo you have been working on for months and are only now pointing the plugin at — **the same three commands, in the same order.** They stand up the harness and publish `qa/quality-gates.md`. You do not repeat them per task.

| Your situation | QA sequence | Then |
|---|---|---|
| **Existing repo**, want coverage for code already written | `/qa:audit` → `/qa:plan` → `/qa:setup` | `/dev:build --tests-only` |
| **New repo** (scaffolded, no features yet) | `/qa:audit` → `/qa:plan` → `/qa:setup` | `/dev:plan` → `/dev:build` |
| **Repo mid-flight**, adopting the plugin now | `/qa:audit` → `/qa:plan` → `/qa:setup` | `/dev:plan` → `/dev:build` |

**`/dev:build` writes tests as part of the build.** For normal feature work there is no separate testing command — Stages 5–6 write the code and its tests together. `--tests-only` is only for *backfilling* coverage onto code that was written outside the loop.

**Don't want the QA part for a given task?** `--skip-qa` is the documented opt-out — it skips the harness gate and writes no tests, for a change whose risk does not justify a test framework (a CSS value, a copy fix, a config default). It buys you out of *testing*, never out of *review*: `/dev:commit` still runs its full security and code review. `--skip-qa` and `--tests-only` are opposites and cannot be combined.

### The one distinction that does matter

Not *which commands* you run — what the **coverage floor** is set to:

| Repo state | Floor |
|---|---|
| No source code yet | the intended target |
| **Any source code at all — even with zero tests** | the **measured baseline**, then ratcheted up |

> **The trap.** A repo with source and no tests looks like a fresh start and is not. Applying a greenfield floor to thousands of untested lines makes the first build fail on code your change never touched. **Absent tests never make a repo "new".**

---

## Step 0 — Have something to audit

### `/tl:scaffold` — new only

The audit reads manifests, scripts, CI config and test directories. An empty folder gives it nothing to work with.

| New | Existing |
|---|---|
| Produces skeleton, package manifests, lint/format/type/build tooling, one trivial passing test, a green base build. **Required** before the audit is meaningful. | Skip — the repo already has all of this. |

---

## Steps 1–3 — Stand up the harness

Identical commands in every situation. What changes is the **coverage floor**, and that difference is the whole reason an existing repo needs this done deliberately.

### Step 1 — `/qa:audit`

Scores how testable the repo is. Reads tooling, **never your source code** — which is exactly why it cannot write your tests.

| New | Existing |
|---|---|
| Finds runner, lint, format, type-check present from the scaffold | Same 14 areas, against real tooling and real debt |
| Flags CI gating, fixtures, mocking, conventions as missing | **Reports measured current coverage** — the number that sets your floor in step 2 |
| Coverage reads `not instrumented`, or near-100% of one file — meaningless either way | Areas 13 & 14 (async, concurrency) score only where a consumer, job, webhook or transaction boundary exists |

- **Reads:** manifests · scripts · CI config · test dirs · `shared-context/technology-stack.md`
- **Writes:** `qa/audits/test-audit-<ts>.{html,md,json}`
- **Changes:** nothing in the repo — read-only

```
Test readiness: 3.4 / 10 — Major gaps
Stack: Python 3.12 · FastAPI · poetry · pytest
Blockers: 1   Major: 6   Current coverage: 4.1%

Report → qa/audits/test-audit-20260930-1412.html

Next:
  1. Open the report, set Adopt / Skip / Defer, Export approvals
  2. /qa:plan qa/audits/test-audit-20260930-1412-approvals.md
```

### Step 2 — `/qa:plan <approvals.md>`

Turns your Adopt/Skip/Defer decisions into an ordered build sheet. Pure transform — reads no repo files, installs nothing.

| New | Existing |
|---|---|
| Floor = the target you intend to **hold**. The codebase grows into it. | Floor = the **measured baseline** from step 1, then ratcheted. Never a greenfield default. |

- **Reads:** the approvals file → its `source_audit` → the audit JSON
- **Writes:** `qa/test-setup-plan.md` · `qa/quality-gates.md` at `harness_status: Draft`

> **This is where the human decides.** Framework, coverage floor, what is e2e-worthy, and which conditional tiers become Required. Everything before it is assessment; everything after is mechanical. It plans **only Adopt rows** and never invents a choice you left open.

### Step 3 — `/qa:setup`

Builds the harness on an isolated branch and proves it runs green end to end. **Identical in every situation.**

- **Writes:** frameworks · config · CI · fixtures · mocking · e2e skeleton · conventions doc · 5 example tests
- **Proves:** `install → lint → format:check → typecheck → unit → coverage → build → e2e:smoke`
- **Ends:** `harness_status: Active`, commits, pushes, **raises a PR — never merges**

> **Those 5 example tests are instruments, not tests.** One trivial unit, one using a factory, one mocking a dependency, one e2e smoke, one contract example. They prove each layer *runs*. None of them touches your code, and coverage of your features stays at **zero**.

> **Merging the PR is a human call.** The coverage floor starts gating everyone's PRs the moment it lands.

---

## Step 4 — Which dev command

The QA sequence above was identical. This is the only step that differs, and it depends on one thing: **does the code already exist?**

### Feature work — `/dev:plan` → `/dev:build`

The normal path, for new and mid-flight repos alike. **Tests are part of the build** — there is no separate testing command to run afterwards.

- Code **and** tests written together, per build-sequence step
- Coverage climbs alongside the codebase
- Stage 4 finds `Active` → the auto-bootstrap never fires

### Backfill — `/dev:build --tests-only`

For code written outside the loop: an existing repo you want covered, or a feature a developer hand-fixed.

- Tests written **against code already on disk**. No implementation half
- Units ranked by risk: business logic and branches first, getters last
- **Never edits a source file.** A failing test over real behaviour is a *finding*, not licence to change product code
- Never deletes, disables or loosens an existing test

> **Both routes decide what to test the same way.** Each unit's concern class is intersected with the Required tiers in `quality-gates.md`, and a test is written at every tier in the intersection. Only the *source of the units* differs — a build sequence, or the files on disk.

---

## How a test is chosen, and how it is proved

Two mechanisms. The second is what separates "green" from "verified".

### A — The intersection: which tests exist

```
step: "consume FormFilled event, update draft"   Satisfies: AC-3
   └─ concern class ............ Idempotency / retry
        ∩ Required tiers ....... QG-014 Required*, condition holds
             └─ write a test at the Idempotency tier
```

Producing, for example:

```python
def test_duplicate_event_fills_form_once():   # AC-3 · tier: idempotency
    publish(form_filled_event)
    publish(form_filled_event)               # same event, twice
    assert draft.fields == expected          # one effect, not two
```

> **An empty intersection is reported, never silent.** If the concern matches but no tier covers it:
>
> `tier-unavailable: Idempotency/retry needs Idempotency, not declared in quality-gates.md`
>
> — in the log, the Stage 11 summary, and the acceptance-map as `not-verified`. Silence here is what let retries, duplicate events, timeouts and illegal state transitions go untested while every gate read green.

### B — The acceptance-map: whether it counts

Every assertion from the ticket gets a row mapped to a validation method, a result and its evidence.

| Assertion | Method | Result | Evidence |
|---|---|---|---|
| AC-3 duplicate event fills once | test | `pass` | `test_duplicate_event_fills_form_once` |
| AC-4 timeout mid-transcription recovers | — | **`not-verified`** | no reachable tier |
| AC-5 button colour is `#000000` | inspection | `manual` | `theme.ts:42` |

> **Never mark pass without a test.** Anything about runtime behaviour, timing or integration that cannot be settled by reading code is marked `not-verified` and surfaced under a heading you cannot miss. That row is the difference between an agent saying "it works" and evidence that it does.

---

## Step 5 — Keep it honest over time

### `/qa:health`

Re-runs every Required gate's real command and reports drift — coverage dropped, CI broke, a test got disabled, an integration test quietly became mocked.

- **Effect:** updates each gate's status and `harness_status` from real results
- **Teeth:** a red Required gate sets `Broken`, and `/dev:build` then **halts** rather than bootstrapping over it

> **It never repairs by weakening.** A threshold change is a human `DEC-###` with a rationale, not a silent edit.

Use `/qa:health` after writing tests to see the real coverage number. Re-run `/qa:audit` when you want the readiness score again — **health re-runs gates, audit re-scores the 14 areas**.

---

## Side by side

| Step | New repo | Existing repo | Mid-flight repo |
|---|---|---|---|
| **0** scaffold | `/tl:scaffold` first | skip | skip |
| **1** audit | *same command* — finds scaffold tooling | *same command* — finds real debt, **reports measured coverage** | *same command* |
| **2** plan | *same command* — floor = intended target | *same command* — floor = **measured baseline**, then ratchet | *same command* — measured baseline |
| **3** setup | *identical — 14 steps, green-smoke, PR, never merges* | | |
| **4** tests | `/dev:plan` → `/dev:build` | `--tests-only` to backfill, then normal build | `/dev:plan` → `/dev:build` |
| **5** health | *identical — drift check, `Broken` halts the build* | | |
| **ongoing** | *`/dev:plan` → `/dev:build` → `/qa:health` → `/dev:commit` — identical for all three* | | |

Steps 1–3 are the same commands everywhere. Only the **floor** and the **step-4 command** differ.

### The ongoing loop in detail

Once the harness is Active, every task runs the same four commands — whatever state the repo started in:

| | Command | What it does for tests |
|---|---|---|
| 1 | `/dev:plan` | decides the split; no tests yet |
| 2 | `/dev:build` | writes code **and** its tests, runs them, builds the acceptance-map |
| 3 | `/qa:health` | **writes the gate results back to `quality-gates.md`** — no build stage does this, so without it the contract still shows the previous run |
| 4 | `/dev:commit` | re-verifies every acceptance row, then pushes and raises the PR |

**Backfilling tests for a task someone already hand-coded** is the one exception: run `/dev:build --tests-only` in place of step 2. It writes tests against the code on disk, never edits product logic, and never deletes or loosens an existing test. Re-running it is safe — it reads the stamps on files it wrote before, extends only uncovered branches, and leaves hand-written tests alone.

---

## When a step refuses

| State | What happens | Your move |
|---|---|---|
| No `quality-gates.md` | build bootstraps a minimal harness, or **halts** under `--tests-only` | `/qa:audit` → `/qa:plan` → `/qa:setup`, or `--skip-qa` for this task |
| `harness_status: Draft` | **halts** — your chosen framework and floor are preserved, not overwritten | `/qa:setup` to finish |
| `harness_status: Broken` | **halts** | `/qa:health`, fix the red gate |
| Concern with no tier | `tier-unavailable` reported, not skipped | declare the tier via `/qa:audit` → `/qa:setup` |
| Setup can't pass a step | escalation written; **no** threshold weakened | read `qa/escalations/`, decide the trade-off |
| A gate is red because the **runner** is misconfigured, not the code | run ends `PARTIAL_HARNESS` — it **advances**, carrying the remedy and the red gate into the summary and the PR | apply the remedy as a human `DEC-###`, then `/qa:health` |
| A gate is red because of a real **defect** | run ends `PARTIAL_FAILURES` — it does **not** advance, and `/dev:commit` refuses | fix the defect; the loop re-runs the failing rows |

---

## The boundary that explains all of it

**The QA commands never open an application source file.** They read manifests, scripts, CI config and test directories — tooling, not behaviour.

That is why `/qa:setup` cannot write your feature tests, and why `/dev:build` is the only thing that does. QA installs the kitchen; dev cooks.
