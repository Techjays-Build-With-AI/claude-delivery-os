# QA Agent — Test Infrastructure & Quality Gates

The **Quality Assurance Agent** makes a repository *properly testable* and defines, in a machine-readable contract, exactly what "verified" means for it — so the developer agent's delivery loop validates features against a real, agreed bar instead of whatever tooling happens to exist. It audits the current setup, recommends what's missing, gets the human to approve, stands up the test infrastructure, proves it green, and publishes the quality-gate contract the dev loop reads. It escalates strategy decisions instead of guessing, and it never fakes a green run.

| | |
|---|---|
| **Namespace** | `/qa:` |
| **Commands** | `/qa:audit [repo]` · `/qa:plan <approvals>` · `/qa:setup [plan]` · `/qa:health [repo]` |
| **Input** | The product repository and its tooling; where present, `context/features/`, `ba-output/scope.md`, and `context/project/` |
| **Output** | `qa-output/` — the audit report trio, `test-setup-plan.md`, the test harness itself, and **`quality-gates.md`** (the contract dev consumes) |
| **Skills** | `qa-test-audit` · `qa-test-setup` · `qa-quality-gates` |

---

## The one boundary that defines it

Delivery OS already has a dev agent that writes and runs tests **for the feature it builds**. QA does **not** compete with it:

- **QA owns the harness and the strategy** — frameworks, config, CI wiring, coverage measurement and thresholds, the e2e harness (Playwright config + page-object/fixtures skeleton), test-data factories, mocking, conventions, and the **quality-gate contract**.
- **Dev owns the per-feature tests** — it writes each feature's unit/integration/e2e tests *inside* QA's harness, and `dev-validation` runs them per feature.
- **QA does not run per-feature validation** — `/qa:setup` runs a one-time **smoke** run to prove the harness works; ongoing per-feature suites are the dev loop's job.

QA builds the kitchen; dev cooks each dish.

---

## The flow

```text
/qa:audit    → read-only assessment → scored gap report (HTML + MD + JSON)
   ↓  human reviews, sets Adopt/Skip/Defer per finding, exports approvals
/qa:plan     → approved recommendations → test-setup-plan.md + draft quality-gates.md
   ↓  human reviews the plan
/qa:setup    → build the harness in an isolated branch → prove a green smoke run
   ↓            → finalize quality-gates.md (harness_status: Active)
/qa:health   → re-check the live harness against its gates → report drift
```

Every gap is a stable `QAF-###` finding; every gate is a `QG-###` in the contract. The audit report is a **decision surface** — QA acts only on what the human approves.

---

## Commands

| Command | Does | Stops at |
|---|---|---|
| `/qa:audit [repo=<path>]` | Read-only test-readiness assessment; scores 12 areas, records `QAF-###` gaps with recommendations, renders the interactive report | scored report + approvals surface |
| `/qa:plan <approvals>` | Turns the approved recommendations into `test-setup-plan.md` and drafts the quality gates | reviewable plan |
| `/qa:setup [plan=<path>]` | Builds the harness in an isolated branch, proves a green smoke run, finalizes `quality-gates.md` | human review (never merges) |
| `/qa:health [repo=<path>]` | Re-runs the required gates to catch drift; reports deltas | drift report |

---

## What it writes

Under `qa-output/` (created on first run):

| File | What |
|---|---|
| `test-audit-<ts>.{html,md,json}` | The scored gap report — interactive report, Markdown artifact, and the JSON sidecar `/qa:plan` reads |
| `test-audit-<ts>-approvals.md` | The human's Adopt/Skip/Defer decisions, exported from the report |
| `test-setup-plan.md` | The ordered setup plan (only the approved recommendations) |
| `quality-gates.md` | **The machine-readable contract** — required/optional checks, commands, thresholds, harness status |
| `setup-log.md` · `decisions.md` · `escalation-<n>.md` | The setup run log, `DEC-###` decisions, and structured blocker notes |

---

## How it plugs into the dev loop

`qa-output/quality-gates.md` is the join between QA and Dev:

- **Dev readiness gate** (`feature-delivery-loop`) reads it to confirm a usable harness exists before building. If it's missing or `harness_status` isn't `Active`, the gate routes to QA (`/qa:audit` → `/qa:setup`) — the same way project-zero routes to `/dev:bootstrap`.
- **`dev-validation`** reads it to know which checks are **Required**, the exact command for each, and the bar (coverage floor, when e2e/contract tests are mandatory) — then maps results into the feature's `acceptance-map.md`.

So the dev loop stops guessing the repo's tooling and verifies against a real, QA-owned standard.

---

## Guardrails

- **Never green-by-weakening** — QA may not disable, `.skip`, delete, or loosen a check or threshold to pass; that's an escalation with the trade-off named.
- **Never touch product logic** — QA works on test infrastructure and config only, never a feature's business code.
- **Never write per-feature tests** or run a feature's suite to judge the feature — that's the dev agent.
- **Escalate, don't guess** — framework choice, coverage floor, what's e2e-worthy, testing an unavailable dependency, or an untestable architecture go to the human (that's the audit's approve-with-a-recommendation step). Retry limits mirror the dev loop: 3 focused fixes per failing step, 2 broad smoke re-runs, 0 strategy guesses.
- **Never merges or deploys** — `/qa:setup` hands the setup branch off for human review.

---

## Setup

Install the core, then `qa` (works best alongside `dev`):

```text
/plugin marketplace add techjays/claude-delivery-os
/plugin install delivery-os@techjays-delivery-os
/plugin install qa@techjays-delivery-os
/plugin install dev@techjays-delivery-os   # the consumer of the quality-gate contract
```

Typical first run on an existing repo: `/qa:audit` → review the report, approve recommendations, export → `/qa:plan <approvals>` → `/qa:setup`. After that, `/dev:build` validates features against the gates QA set, and `/qa:health` keeps them honest over time.

---

## How it fits Delivery OS

QA is a **consumer** of the BA/TL context and the **producer** of the test harness and the quality-gate contract. It reads `ba-output/scope.md`, `context/features/`, the TL `context/frontend|backend|database` graph, and `context/project/` to match the harness to the real stack and to what must be testable; it writes `produced_by: qa` files under `qa-output/` and appends `DEC-###` decisions to the shared `decision-log.md`. See the shared [`delivery-os-conventions`](../delivery-os-core/skills/delivery-os-conventions/SKILL.md) contract.
