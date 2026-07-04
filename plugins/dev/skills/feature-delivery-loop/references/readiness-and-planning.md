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
| Repository is in a usable state; base build is green | product repo (`git status`, build) | ✕-critical |
| Required env vars, credentials, tools are available | repo config / environment | ✕-critical |
| Feature ownership is not locked by another agent | `dev/delivery-status.md` owner | ✕-critical |
| Major workflow is unambiguous | `workflow.md` | non-critical → note assumption |
| Coding standards are known | `coding-standards.md` / repo conventions | non-critical → infer + note |

Non-critical gaps: record a marked **assumption** in `dev/dev-plan.md` and proceed. Critical gaps: escalate. Examples of critical missing information that must not be guessed past — no acceptance criteria, conflicting workflow definitions, unknown source of truth for data, missing API contract, missing authn/permission rules, an unresolved schema requirement, or a dependency on an unavailable external system.

Passing readiness gate → set state `IN_DEVELOPMENT` (after planning) and continue.

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
