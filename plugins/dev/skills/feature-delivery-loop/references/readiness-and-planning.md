# Readiness, impact analysis, and implementation planning

How to gate a feature before coding, how to work out what the change touches, and how to write a plan another agent could continue from. Read this before step 3 of the loop.

---

## 0. Planning gate (ensure the feature is planned)

Run this **before** readiness validation. The dev agent builds against the TL technical context graph (pages, endpoints, entities); if that graph isn't there, there is nothing concrete to implement. So the first thing the build skill does is confirm the feature is **planned**, and — if it isn't — get it planned automatically rather than inventing endpoints and schemas or blocking.

### Detection — "is this feature already planned?" (verify units resolve **and** are linked)

A feature counts as **planned** only when all of the following hold. Presence of the `context/frontend|backend|database` folders is *not* sufficient — verify the actual units:

1. Read the feature's `feature.md` and collect what it declares: **Related Pages**, **Related APIs / Services**, **Related Data Entities**. (Backend-only features declare no pages — skip the page layer for them.)
2. Load the three TL indexes — `context/frontend/page-index.md`, `context/backend/endpoint-index.md`, `context/database/entity-index.md`. If any required index is absent → **not planned**.
3. For every declared unit, confirm two things:
   - **Resolves** — the unit exists as a real file referenced by the index (the index row's file path resolves), not just a name in `feature.md`.
   - **Linked** — this feature's `FEAT-<AREA>-NN` appears in the index/unit as a consumer/owner of that unit (the TL wires `features that use it` into each row). A unit that exists but isn't linked to this feature is a graph gap.
4. **Verdict:**
   - **Planned** — every declared page/endpoint/entity resolves and is linked to this `FEAT-id`. Proceed to readiness.
   - **Partially planned** — some declared units are missing from the graph, unresolved, or unlinked. Treat as *needs planning* (re-run planning to fill the gaps; the TL skill updates in place and won't duplicate existing units).
   - **Not planned** — indexes absent, or none of the feature's units are in the graph.

### Auto-plan when not (or partially) planned

When the verdict is *not planned* or *partially planned*, **plan it first, then continue the loop** (no human pause — that's the configured behaviour):

1. **Delegate to the TL.** Invoke the **`tl-agent`** subagent scoped to this **one** feature folder, with the standard `tl-feature-planning` instruction (the same work `/tl:plan <feature>` does): map the feature's declared pages/APIs/data-entities to real, linked unit files under `context/frontend|backend|database`, reusing existing units and minting new `PAGE-/EP-/ENT-<AREA>-NN` where needed, wiring links both ways, logging `DEC-###` design decisions, updating the three indexes, and running the link-integrity check.
   - If subagent delegation isn't available in the run, run the **`tl-feature-planning` skill** directly on the feature instead — same outcome, same skill.
2. **Re-verify.** After planning returns, run the detection above again. It must now come back **planned**.
3. **Carry the result forward.** Note in the run summary that the feature was auto-planned (units created/reused, `DEC-###` logged, any open questions the TL raised), so the human sees the design that was generated even though the loop didn't pause.
4. **Then** run readiness validation and continue the build.

### Fallbacks and limits

- **TL unavailable** — if the `tl-agent`/`tl-feature-planning` skill isn't installed or can't run, don't invent the graph. Set state `BLOCKED`, write `dev/escalation-<n>.md` explaining the feature isn't planned and TL planning isn't available, and tell the user to run `/tl:plan <feature>` first.
- **TL planning can't complete** — `tl-feature-planning` itself escalates when the design is genuinely undecided (a missing integration contract, an unknown auth model). If it returns with blocking open questions rather than a complete graph, the feature stays `BLOCKED` on *those* questions — carry the TL's escalation up; don't build on a half-graph.
- **Re-verify still fails** — if detection doesn't come back *planned* after one planning pass, escalate rather than looping planning indefinitely (this respects the "2 plans per feature" ceiling — auto-plan counts as one).

The planning gate is the one place the dev agent triggers TL work; it still **consumes** the graph and never edits TL units by hand. Everything downstream (impact, plan, implement) reads the graph the gate guaranteed.

---

## 1. Readiness validation (the gate)

Before any implementation, confirm each item. A failure on a **critical** item (marked ✕-critical) means set state `BLOCKED`, write an escalation note, and stop — do not implement around it.

| Check | Source | Critical? |
|---|---|---|
| Feature is approved / at READY_FOR_DEV | `status.md`, `feature-index.md` | ✕-critical |
| Acceptance criteria exist and are non-empty | `acceptance-criteria.md` | ✕-critical |
| No blocking open question is still `Open` | `open-questions.md` (Impact = "Blocks…") | ✕-critical |
| TL technical context exists for the feature's units | `context/frontend|backend|database` + indexes | ✕-critical → satisfied by the **planning gate (§0)**: auto-planned if missing; only escalates if TL is unavailable or planning can't complete |
| Dependencies are available or explicitly mockable | `dependencies.md`, integration-register | ✕-critical |
| A usable product repository exists; base build is green | product repo (`git status`, build) | ✕-critical → **project-zero** routes to bootstrap (§1a), not a plain block |
| A usable test harness exists; quality gates are defined | `qa-output/quality-gates.md` (`harness_status: Active`) | ✕-critical → **no harness** routes to QA (§1b), not a plain block |
| Required env vars, credentials, tools are available | repo config / environment | ✕-critical |
| Feature ownership is not locked by another agent | `dev/delivery-status.md` owner | ✕-critical |
| Major workflow is unambiguous | `workflow.md` | non-critical → note assumption |
| Coding standards are known | `coding-standards.md` / repo conventions | non-critical → infer + note |

Non-critical gaps: record a marked **assumption** in `dev/dev-plan.md` and proceed. Critical gaps: escalate. Examples of critical missing information that must not be guessed past — no acceptance criteria, conflicting workflow definitions, unknown source of truth for data, missing API contract, missing authn/permission rules, an unresolved schema requirement, or a dependency on an unavailable external system.

Passing readiness gate → set state `IN_DEVELOPMENT` (after planning) and continue.

### 1a. Repository gate — brownfield vs project-zero

The "usable product repository" check has two failure modes, and they are handled differently:

- **Brownfield, but broken** — a repo exists yet its base build/lint/test is already red *before* your changes. This is a genuine escalation (you don't silently fix a pre-existing broken build). Set `BLOCKED` and escalate.
- **Project-zero** — there is **no** product repository at all (no app skeleton, no package-manager files, no build/test tooling), because the workspace is design-only. This is **not** a per-feature bug — it blocks every feature — and the fix is to stand up the initial codebase, which is an architecture decision, not something to guess.

For project-zero, **route to bootstrap rather than plain-blocking**:

1. If a **confirmed architecture** exists (`context/project/architecture.md` / `technology-stack.md`, or a spec the user pointed at) and no stack decision is missing, the loop may **auto-bootstrap** — delegate to the TL `tl-project-scaffold` skill (the same work `/tl:scaffold` / `/dev:bootstrap` does) to stand up the repo and its green base, then re-check and continue.
2. If required stack decisions are **missing** (framework, DB, hosting, …), scaffolding must ask the user — so **hand off to `/dev:bootstrap`** (which runs the TL scaffold's recommend-and-ask flow) instead of trying to answer architecture questions inside the feature loop. Report that the workspace is project-zero and needs a one-time bootstrap.
3. If the **TL scaffold skill isn't available**, escalate: `BLOCKED`, tell the user to run `/tl:scaffold` (or install the tl plugin). Never scaffold with a guessed stack.

The dev agent never chooses the stack itself — bootstrap executes a confirmed one and asks (with a recommendation) for the rest. Once the repo exists with a green base, the repository readiness check passes and the loop proceeds.

### 1b. Test-harness gate — can the loop actually verify?

A repo can build green yet have **no way to prove features** — no test runner, no coverage enforcement, no e2e harness. The dev loop's `TESTING` step then runs whatever tooling happens to exist and calls it "verified," which is exactly the visibility gap QA closes. So before implementing, confirm a usable test harness exists and the loop knows the bar:

1. **Read `qa-output/quality-gates.md`.** If it exists with `harness_status: Active`, the harness is proven and the file tells `dev-validation` which checks are **Required**, their commands, and the thresholds (coverage floor, when e2e/contract tests are mandatory). Proceed — and carry the required gates into the acceptance-map step.
2. **No contract, or `harness_status` is `Draft`/`Broken`** — there is no proven way to verify. This is not a per-feature bug (it blocks every feature) and the fix — which frameworks, what coverage floor — is a strategy decision, not something to guess. **Route to QA rather than plain-blocking:** tell the user to run `/qa:audit` → `/qa:plan` → `/qa:setup` (the QA plugin), analogous to how project-zero routes to `/dev:bootstrap`. If the **qa plugin isn't installed**, degrade gracefully: fall back to detecting the repo's own tooling for this run (as today) and note in the summary that no QA quality-gate contract was found, so verification used detected tooling rather than an agreed bar — recommend installing `qa` and running `/qa:setup`.
3. **A `Broken` harness** (a Required gate is red before your changes) is a genuine escalation, like a broken base build — `BLOCKED`, tell the user to run `/qa:health` and fix the harness first; don't build features onto a broken test setup.

The dev agent never designs the test strategy itself — QA owns that. When the contract is present, the loop simply verifies against it; when it's absent, it routes to QA or degrades to detected tooling, but never invents a quality bar and calls it agreed.

---

## 2. Impact analysis

Identify what the feature actually touches, at the file/module level where you can name it, and write it to `dev/impacted-components.md`. Walk every dimension — mark `N/A` where a dimension doesn't apply rather than dropping it:

- **Frontend** — pages and components (map to the TL `PAGE-<AREA>-NN` units).
- **Backend** — APIs and services (map to `EP-<AREA>-NN`).
- **Database** — schema, tables/collections, and **migrations** (map to `ENT-<AREA>-NN` → `DATA-###`).
- **Authn / authz** — new roles, permissions, or checks.
- **Third-party integrations** — external APIs/services (cite `INT-###`).
- **Background jobs / queues** — scheduled or async work.
- **Notifications** — email, push, in-app.
- **Monitoring / observability** — logs, metrics, traces, alerts.
- **Existing tests** — which suites cover or must extend to cover the change.
- **Documentation** — what needs updating.
- **Feature flags** — gating for rollout.
- **Analytics / event tracking** — events to emit.

Ground each entry in a real file/route/entity where possible; the TL graph and the codebase are your evidence. A schema or migration impact that risks data loss, or an integration whose contract you can't find, is an escalation — flag it here and raise it.

---

## 3. Implementation planning

Write or refresh `dev/dev-plan.md` (schema in `dev-context-templates.md`). It must be actionable enough for another developer or agent to pick up mid-stream. Include:

- **Ordered implementation steps** — the sequence you'll build in (usually: data model/migration → backend endpoints → frontend pages → wiring → notifications/jobs → tests → edge cases), each tied to the TL units and acceptance criteria it satisfies.
- **Affected files or modules** — concrete paths from the impact analysis.
- **Required API changes** — new/changed endpoints, request/response shapes (reuse the TL `EP-` contracts; don't reinvent them).
- **Required schema changes** — new columns/tables/indexes and the migration approach, with rollback.
- **Test strategy** — which acceptance criteria are covered by unit vs integration vs e2e, and what evidence each produces.
- **Rollback considerations** — how to reverse the change safely (migration down, flag off).
- **Risks and assumptions** — including every non-critical readiness assumption you carried forward.
- **Validation criteria** — the exact checks that will constitute "done" for this feature.
- **Estimated complexity** — Low / Medium / High, with the driver.
- **Dependencies on other features or teams** — cross-feature ordering, shared units, external teams.

Respect the **2 plans per feature** limit. Reuse the TL contracts and schemas as given — planning is sequencing and grounding the build, not redesigning what the TL already decided. Where the plan reveals a genuinely undecided design point that changes behaviour, raise it as an open question / escalation rather than baking a guess into the plan.
