# Dev context file templates

The exact schema for every file the dev agent writes. Build each from these so the `dev/` layer and the tracker stay uniform, traceable, and machine-parseable. Fill sections from the feature context, the TL graph, and the run; where a section has no supported content write the labelled placeholder (`None identified yet` / `TBD`) — never delete a heading, never invent content.

All dev files carry `produced_by: dev` and live under `context/features/<slug>/dev/`, except `feature-tracker.md`, which lives at `dev-output/feature-tracker.md`. Dates are ISO (`YYYY-MM-DD`), read from the system clock. Decisions logged here are **also** appended as `DEC-###` rows to `shared-context/decision-log.md`.

---

## 1. dev-plan.md

```md
---
doc_type: dev-plan
schema_version: 1.1
produced_by: dev
feature_id: FEAT-SUP-001
generated_at: YYYY-MM-DD
---

# Dev Plan: Supplier Onboarding

## Implementation Goal
One-paragraph statement of what "done" is, in acceptance-criteria terms.

## Ordered Implementation Steps
1. … (each step cites the TL units and the acceptance criteria it satisfies)

## Affected Files / Modules
| Path | Change | Related TL unit |
|---|---|---|
| services/supplier/createSupplier.ts | new | EP-SUP-01 |

## Required API Changes
- … (reuse TL EP-<AREA>-NN contracts; note new/changed shapes)

## Required Schema Changes
- … (tables/columns/indexes, migration approach, rollback)

## Test Strategy
| Acceptance criterion | Test level | Evidence artifact |
|---|---|---|

## Rollback Considerations
- …

## Risks and Assumptions
- … (include every non-critical readiness assumption carried forward)

## Validation Criteria
- … (the exact checks that constitute done)

## Estimated Complexity
Low | Medium | High — driver: …

## Cross-Feature / Team Dependencies
- …
```

---

## 2. impacted-components.md

```md
---
doc_type: dev-impacted-components
schema_version: 1.1
produced_by: dev
feature_id: FEAT-SUP-001
generated_at: YYYY-MM-DD
---

# Impacted Components: Supplier Onboarding

| Dimension | Impact | Files / Units | Notes |
|---|---|---|---|
| Frontend pages/components | … | PAGE-SUP-01 | |
| Backend APIs/services | … | EP-SUP-01 | |
| Database schema/migrations | … | ENT-SUP-01 → DATA-003 | data-loss risk? |
| Authn / authz | … | | |
| Third-party integrations | … | INT-002 | contract available? |
| Background jobs / queues | N/A | | |
| Notifications | … | | |
| Monitoring / observability | … | | |
| Existing tests | … | | |
| Documentation | … | | |
| Feature flags | … | | |
| Analytics / event tracking | … | | |
```

---

## 3. acceptance-map.md

The evidence table — a feature cannot reach READY_FOR_PR until every mandatory row is `Passed` or human-`Waived`.

```md
---
doc_type: dev-acceptance-map
schema_version: 1.1
produced_by: dev
feature_id: FEAT-SUP-001
generated_at: YYYY-MM-DD
---

# Acceptance Criteria Validation: Supplier Onboarding

| Acceptance Criterion | Validation Method | Result | Evidence |
|---|---|---|---|
| Supplier can submit onboarding form | End-to-end test | Passed | supplier-onboarding.spec.ts |
| Duplicate tax ID is rejected | API integration test | Passed | supplier-api.test.ts |
| Only admin can approve supplier | Permission test | Failed | approval-permissions.test.ts |

Result values: `Passed` · `Failed` · `Blocked` · `Waived` (human) · `Not Covered`.
```

---

## 4. implementation-log.md

Append one dated entry per meaningful step or repair attempt — never overwrite history.

```md
---
doc_type: dev-implementation-log
schema_version: 1.1
produced_by: dev
feature_id: FEAT-SUP-001
generated_at: YYYY-MM-DD
---

# Implementation Log: Supplier Onboarding

## YYYY-MM-DD

### Step
Implemented supplier onboarding form and draft supplier creation API.

### Files Changed
- apps/web/src/pages/SupplierOnboarding.tsx
- services/supplier-service/createSupplier.ts
- services/supplier-service/createSupplier.test.ts

### Validation
- Unit tests: Passed
- Type check: Passed
- Lint: Passed
- Integration test: Failed

### Failure
Duplicate tax ID validation does not return the expected API error code.

### Repair Attempt
1 of 3 — adjusted validation middleware error mapping.

### Next Action
Re-run supplier-api.test.ts, then the broad suite.
```

---

## 5. delivery-status.md

The fine-grained loop state and owner lock for this feature.

```md
---
doc_type: dev-delivery-status
schema_version: 1.1
produced_by: dev
feature_id: FEAT-SUP-001
generated_at: YYYY-MM-DD
---

# Delivery Status: Supplier Onboarding

## Loop State
IN_DEVELOPMENT

## Owner (lock)
dev-agent @ 2026-07-03T10:00

## Branch / Worktree
feature/FEAT-SUP-001-supplier-onboarding

## Started
YYYY-MM-DD

## Last Updated
YYYY-MM-DD

## Validation Status
Unit: Passed · Integration: Failed · Build: Passed · Security: Not run

## Current Blocker
None | <one-line summary + escalation-<n>.md link>

## PR / Handoff
None | dev/pr-summary.md | <PR link>

## Next Action
Fix duplicate tax ID error contract and re-validate.
```

Loop-state values and their BA/index mapping are in `loop-control.md`. Whenever this file changes state, mirror the mapped value into the feature's `status.md`, `feature-index.md`, and `dev-output/feature-tracker.md`.

---

## 6. decisions.md

```md
---
doc_type: dev-decisions
schema_version: 1.1
produced_by: dev
feature_id: FEAT-SUP-001
generated_at: YYYY-MM-DD
---

# Technical Decisions: Supplier Onboarding

| DEC ID | Decision | Rationale | Confidence | Date |
|---|---|---|---|---|
| DEC-014 | Enforce tax-ID uniqueness at the DB level with a partial unique index | Prevents race duplicates the app check misses | Confirmed | YYYY-MM-DD |

Every row is also appended to `shared-context/decision-log.md`. Confidence uses the shared vocabulary (`Confirmed` · `Likely` · `Assumed` · `Conflicting` · `Needs Clarification`).
```

---

## 7. pr-summary.md

Written by `dev-pr-handoff`. Full field guide in that skill's `references/pr-and-escalation.md`; schema below.

```md
---
doc_type: dev-pr-summary
schema_version: 1.1
produced_by: dev
feature_id: FEAT-SUP-001
generated_at: YYYY-MM-DD
---

# PR: Supplier Onboarding (FEAT-SUP-001)

## Feature Purpose
## Scope of Changes
## Technical Approach
## Affected Pages / APIs / Services
## Tests Run
## Acceptance Criteria Status
(link or inline the acceptance-map table)
## Risks / Rollout Considerations
## Open Follow-up Items
## Reviewer Instructions
## Branch
feature/FEAT-SUP-001-supplier-onboarding
```

---

## 8. escalation-<n>.md

Written whenever the feature goes `BLOCKED`. `<n>` is a per-feature counter.

```md
---
doc_type: dev-escalation
schema_version: 1.1
produced_by: dev
feature_id: FEAT-SUP-001
generated_at: YYYY-MM-DD
---

# Blocker Escalation

## Feature
FEAT-SUP-001 — Supplier Onboarding

## Current State
BLOCKED

## What Was Attempted
- Reviewed onboarding workflow.
- Implemented supplier form submission endpoint.
- Attempted integration with tax validation API.

## Blocker
Tax validation API contract is not available in the project context or repository.

## Impact
Supplier duplicate validation cannot be completed. Acceptance criterion "Duplicate tax ID is rejected" cannot be validated.

## Decision Needed
Confirm whether:
1. Tax validation should use an existing internal service.
2. A third-party service should be integrated.
3. Validation should be temporarily handled through manual review.

## Recommended Option
Use the existing internal compliance validation service if available.

## Work That Can Continue
- Front-end onboarding form.
- Draft supplier record creation.
- Admin approval workflow.
```

---

## 9. feature-tracker.md

`dev-output/feature-tracker.md` — the cross-feature delivery dashboard. One row per feature the dev agent has touched; update in place.

```md
---
doc_type: dev-feature-tracker
schema_version: 1.1
produced_by: dev
status: Emerging
generated_at: YYYY-MM-DD
---

# Feature Delivery Tracker

| Feature ID | Feature | Loop State | Owner | Started | Last Updated | Validation | Blocker | PR | Next Action |
|---|---|---|---|---|---|---|---|---|---|
| FEAT-SUP-001 | Supplier Onboarding | IN_DEVELOPMENT | dev-agent | 2026-07-03 | 2026-07-03 | Integration failing | None | — | Fix tax-ID error contract |
```
