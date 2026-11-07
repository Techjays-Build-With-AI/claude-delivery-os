---
title: Quality Assurance — Architecture
audience: QA engineers, technical leads, engineers
status: current
---

# Quality Assurance — Architecture

QA owns what "verified" means. It does not write feature tests; it makes the repository **capable
of proving** a feature works, and publishes the contract the delivery loop enforces.

---

## 1. Architecture

### 1.1 Position in the chain

```
   repository (scaffolded or existing)
            │
            ▼
   ┌─────────────────┐
   │   /qa:audit     │  read-only · scores · QAF-### findings
   └────────┬────────┘
            │  <repo>-audit-<ts>.html  +  .md  +  .json
            ▼
      HUMAN APPROVES  ──►  <repo>-audit-<ts>-approvals.md
            │
            ▼
   ┌─────────────────┐
   │   /qa:plan      │  approved items → ordered setup plan + gate draft
   └────────┬────────┘
            ▼
   ┌─────────────────┐
   │   /qa:setup     │  implement → verify loop → prove green
   └────────┬────────┘
            │
            ▼
   qa/quality-gates.md    THE CONTRACT
            │
     ┌──────┴───────┬──────────────┐
     ▼              ▼              ▼
  /dev:build    /dev:commit    /qa:health
  readiness     enforcement    drift check
```

### 1.2 The separation that makes it work

| Owns | QA | Dev |
|---|---|---|
| Test **harness** — frameworks, config, CI, fixtures, mocks | ✔ | |
| Test **strategy** — which tiers are required per capability class | ✔ | |
| **Per-feature** tests | | ✔ |
| **Per-feature** validation against acceptance criteria | | ✔ |

QA defines the shape of proof. Dev produces the proof for each feature inside that shape. Mixing
them produces a harness tuned to whatever feature happened to be built first.

---

## 2. Process

### 2.1 Audit — assess, change nothing

Read-only. The repository is scored and every gap recorded as a stable `QAF-###` finding with a
recommendation and a recommended option, rendered as an interactive report plus Markdown and JSON.

**A mandatory baseline pass runs first.** Each unmet baseline item (`BL-##`) becomes a flagged
finding before any scoring begins — these are the floor, not a preference.

### 2.2 Fifteen scored areas

| # | Area | # | Area |
|---|---|---|---|
| 1 | Unit test framework and runner | 9 | Test data, fixtures and factories |
| 2 | Integration testing | 10 | Mocking and test doubles |
| 3 | End-to-end / UI harness | 11 | Contract / API testing |
| 4 | Coverage measurement and thresholds | 12 | Test conventions and documentation |
| 5 | Linting | 13 | Async failure modes — idempotency and retry |
| 6 | Formatting | 14 | Concurrency |
| 7 | Type checking | 15 | State transitions |
| 8 | CI test automation | | |

Optional areas are scored only where the project requires them.

**Applicability, as everywhere in the system.** Only applicable areas count toward the verdict —
scoring a project for a capability it was never going to need produces a number nobody trusts.

Each area is scored out of ten and **every deduction is backed by a finding**. A score without a
`QAF-###` behind it is a defect in the audit, not a judgment about the repository.

### 2.3 Human approval is a gate, not a formality

The audit produces a **decision surface**, not a work order. The human reviews each finding,
accepts or rejects the recommendation, and exports an approvals file. `/qa:plan` plans **only what
was approved** — it does not quietly include the rest.

### 2.4 Plan — ordered setup plus gate draft

The approved findings become an ordered setup plan, and `qa/quality-gates.md` is drafted. Planning
does not build; `/qa:setup` builds.

### 2.5 Setup — implement, then prove

Work happens on an isolated branch through a bounded implement → verify loop:

```
  install and configure frameworks
  wire CI
  add fixtures and factories
  add mocks for external dependencies
  set coverage thresholds
  scaffold the end-to-end harness
  write testing conventions
        │
        ▼
  prove a green smoke run   ◄── bounded retry
        │
        ▼
  finalize qa/quality-gates.md
```

**The green smoke run is the exit condition.** A harness that is configured but has never
successfully run is not a harness.

### 2.6 Health — drift detection

`/qa:health` re-checks an existing harness against its own gates: a disabled check, a lowered
coverage floor, a broken end-to-end runner. Quality gates decay quietly, and a gate nobody has
exercised in three months is not a gate.

---

## 3. The quality-gate contract

`qa/quality-gates.md` is machine-readable and declares **which test tiers are required per
capability class**. It is the single artifact the delivery loop consumes.

| Consumer | Uses it to |
|---|---|
| `/dev:build` stage 4 | Decide whether the harness is adequate to build against |
| `/dev:build` stage 8 | Know which tiers an assertion must be covered at |
| `/dev:commit` stage 5 | Enforce the gate before the work can ship |
| `/qa:health` | Re-verify the repository still meets its own declaration |

### 3.1 When QA setup was skipped

If `qa/quality-gates.md` is absent at plan time, the user is asked whether to audit and set up
gates for the existing codebase, or skip and plan the new feature only.

On **skip**, a marker is written with `harness_status: Stack-Inferred` and the tier pool derived
from stack detection. The build gate then runs in **soft mode** with an explicit warning about
un-audited existing coverage.

**The new feature still gets full coverage at every applicable tier either way.** The skip defers
the audit of existing code — it does not lower the bar for what is being built now.

---

## 4. Best-practice checks

**Never weaken, skip or delete a test to go green.** This is the single rule the whole stage rests
on. A suite that was made to pass proves nothing, and the damage is invisible afterwards.

**Never edit product or business logic.** QA changes the harness. If the code is untestable, that
is a finding for the developer, not a licence to restructure it.

**Never write per-feature tests.** Those belong to the dev loop, inside the harness QA built.
Writing them here produces tests that drift from the features they describe.

**Never merge or deploy.** Setup works on an isolated branch.

**Escalate strategy, do not guess it.** Framework choice, coverage floor, what deserves an
end-to-end test — these are judgment calls with long lifespans. They go to the human.

**Only build what was approved.** The gap between "the audit found it" and "the human wants it
fixed" is the human's to close.

---

## 5. Evidence

| Artifact | Proves |
|---|---|
| `<repo>-audit-<ts>.html` / `.md` / `.json` | The scored state at a point in time, finding by finding |
| `QAF-###` entries | Each gap, its recommendation, and the option recommended |
| `BL-##` mandatory gaps | Which baseline items were unmet |
| `<repo>-audit-<ts>-approvals.md` | What the human accepted — the mandate for setup |
| `<repo>-setup.md` | The ordered plan actually executed |
| Green smoke run | The harness works, not merely exists |
| `qa/quality-gates.md` | The declared contract, machine-readable |
| `/qa:health` re-runs | Whether the repository still meets its own declaration |

The audit is reproducible: scores derive from the rubric over applicable areas, and each deduction
names its finding. A later audit can be diffed against an earlier one to show movement.

---

## 6. How QA and Dev interlock

```
  QA declares            Dev proves                    Enforcement
  ───────────            ──────────                    ───────────
  which tiers      ──►   test-map rows per        ──►  build stage 7
  are required           assertion                     verifies the map

  coverage floor   ──►   Acceptance table rows    ──►  commit stage 5
                         ⏳ pending → ✅ pass            executes and enforces

  CI wiring        ──►   suite runs in CI         ──►  push refuses on
                                                       unaddressed findings
```

QA never sees an individual feature. Dev never decides what "verified" means. The contract file is
the only thing passing between them, which is why it is machine-readable rather than prose.

---

## 7. Boundaries

QA **never** weakens tests, edits product logic, writes feature tests, merges, deploys, or guesses
a strategy decision. It assesses, plans what was approved, builds the harness, proves it green,
and publishes the contract.
