# Feature Delivery Loop Skill — Requirement Specification

## 1. Overview

### Skill Name

`feature-delivery-loop`

### Skill Type

Development Agent orchestration skill.

### Purpose

The Feature Delivery Loop skill enables a development agent to autonomously take an approved feature from the project context, implement it, validate it against acceptance criteria, fix identified issues, update delivery status, and prepare the work for human review.

The skill is designed to operate as an execution and verification loop rather than as a one-time code-generation task.

It should coordinate multiple development activities including context reading, planning, implementation, testing, review, documentation updates, and tracker updates.

---

## 2. Problem Statement

Development agents can generate code, but without a structured loop they may:

* Implement only part of a feature.
* Miss related pages, APIs, workflows, or edge cases.
* Ignore acceptance criteria.
* Stop after code generation without validating the result.
* Make repeated changes without tracking what was attempted.
* Fail to escalate when a business or architectural decision is required.
* Leave feature documentation and delivery trackers outdated.

The Feature Delivery Loop skill solves this by creating a controlled, state-driven execution process for each feature.

---

## 3. Objectives

The skill must:

1. Pick an approved feature from the project context.
2. Read and understand the feature-specific business, technical, and workflow context.
3. Identify impacted pages, APIs, services, database entities, integrations, tests, and documentation.
4. Create or update an implementation plan before coding.
5. Implement the feature in an isolated branch or worktree.
6. Run required validation checks.
7. Compare implementation results against feature acceptance criteria.
8. Fix actionable issues through controlled retry loops.
9. Update feature-level documentation and project tracking status.
10. Prepare a clean handoff for human code review and approval.
11. Escalate when the agent reaches a business, architecture, security, dependency, or scope blocker.

---

## 4. Non-Objectives

The skill should not:

* Independently approve unclear business requirements.
* Change product scope without approval.
* Deploy directly to production unless a separate deployment skill explicitly authorizes it.
* Bypass required human approvals.
* Modify unrelated features merely because they appear technically connected.
* Continue retries indefinitely.
* Make destructive database, infrastructure, security, or compliance changes without escalation.
* Treat passing unit tests alone as confirmation that the feature is complete.

---

## 5. Expected Context Structure

The skill should work with the project context folder created by the BA agent.

```text
context/
  project/
    project-overview.md
    architecture.md
    coding-standards.md
    technology-stack.md
    integration-map.md
    glossary.md

  features/
    FEAT-001-supplier-onboarding/
      feature.md
      implementation-plan.md
      acceptance-criteria.md
      impacted-components.md
      workflow.md
      test-cases.md
      decisions.md
      risks-and-dependencies.md
      delivery-status.md
      implementation-log.md

  tracker/
    feature-tracker.md
    dependency-tracker.md
    decision-log.md
    release-plan.md
```

The skill should support situations where some files are missing. It must identify missing context and either generate a draft or escalate based on the importance of the missing information.

---

## 6. Inputs

The skill should accept the following inputs.

### Required Inputs

| Input                                    | Description                                    |
| ---------------------------------------- | ---------------------------------------------- |
| Feature ID or feature folder             | Identifies the feature to implement.           |
| Project repository path                  | Repository where implementation will occur.    |
| Context folder path                      | Location of project and feature documentation. |
| Current branch or worktree configuration | Defines where code changes should be made.     |

### Optional Inputs

| Input                    | Description                                                                        |
| ------------------------ | ---------------------------------------------------------------------------------- |
| Execution mode           | `plan-only`, `implement`, `validate-only`, `fix-review-comments`, or `prepare-pr`. |
| Retry limit              | Maximum number of focused repair attempts. Default: 3.                             |
| Test scope               | Unit-only, integration, end-to-end, or full validation suite.                      |
| Human review requirement | Whether human approval is required before PR creation.                             |
| Environment information  | Local, development, staging, or sandbox details.                                   |
| Existing PR reference    | Used when continuing work on an existing pull request.                             |
| Reviewer feedback        | Used when responding to code review comments.                                      |

---

## 7. Feature Prerequisites

Before development begins, the feature should ideally contain:

* Feature objective.
* Business problem.
* User personas or user roles.
* Scope and out-of-scope items.
* Functional requirements.
* Workflow or user journey.
* Acceptance criteria.
* Impacted pages, APIs, services, and integrations.
* Data model or data requirements.
* Edge cases.
* Dependencies.
* Risks.
* Open questions.
* Test scenarios.

If critical prerequisites are missing, the skill must not proceed blindly.

Examples of critical missing information:

* No acceptance criteria.
* Conflicting workflow definitions.
* Unknown source of truth for data.
* Missing API contract.
* Missing authentication or permission rules.
* Unresolved database schema requirement.
* Dependency on an unavailable external system.

---

## 8. High-Level Execution Flow

```text
Feature selected
→ Validate feature readiness
→ Read feature and project context
→ Identify impacted components
→ Create or update implementation plan
→ Create isolated worktree or branch
→ Implement feature
→ Run tests and static validation
→ Validate acceptance criteria
→ Run reviewer checks
→ Fix actionable issues
→ Repeat validation loop within retry limits
→ Update documentation and tracker
→ Prepare pull request
→ Hand off for human review
```

---

## 9. Feature State Model

The skill must manage feature progress through explicit states.

```text
BACKLOG
→ READY_FOR_DEV
→ IN_PLANNING
→ BLOCKED
→ IN_DEVELOPMENT
→ TESTING
→ REVIEW_FIXES
→ READY_FOR_PR
→ HUMAN_REVIEW
→ APPROVED
→ MERGED
→ RELEASED
```

### State Definitions

| State          | Meaning                                                                       |
| -------------- | ----------------------------------------------------------------------------- |
| BACKLOG        | Feature exists but is not ready for implementation.                           |
| READY_FOR_DEV  | Feature has sufficient context and is approved for development.               |
| IN_PLANNING    | Agent is reviewing context and preparing implementation steps.                |
| BLOCKED        | Development cannot continue without a decision, dependency, or clarification. |
| IN_DEVELOPMENT | Agent is actively making code changes.                                        |
| TESTING        | Automated and manual validation checks are being executed.                    |
| REVIEW_FIXES   | Agent is resolving validation failures or review feedback.                    |
| READY_FOR_PR   | Implementation and validation are complete.                                   |
| HUMAN_REVIEW   | Pull request is waiting for human review or approval.                         |
| APPROVED       | Human reviewer has approved the implementation.                               |
| MERGED         | Code has been merged into the target branch.                                  |
| RELEASED       | Feature has been deployed and release validation is complete.                 |

---

## 10. Core Functional Requirements

### 10.1 Feature Selection

The skill must:

* Accept a specific feature ID when provided.
* Otherwise identify the next feature marked `READY_FOR_DEV`.
* Avoid selecting blocked, incomplete, or already active features unless explicitly instructed.
* Prevent multiple agents from simultaneously working on the same feature unless parallel work is explicitly enabled.

### 10.2 Context Reading

The skill must read:

* `feature.md`
* `acceptance-criteria.md`
* `workflow.md`
* `impacted-components.md`
* `risks-and-dependencies.md`
* `project-overview.md`
* `architecture.md`
* `coding-standards.md`
* Relevant existing code, tests, APIs, schemas, and documentation.

The skill must summarize its understanding before implementation in `implementation-plan.md`.

### 10.3 Readiness Validation

Before implementation, the skill must validate:

* Feature is marked approved or ready for development.
* Acceptance criteria exist.
* Dependencies are either available or explicitly mocked.
* Major open questions are resolved.
* Repository is in a usable state.
* Required environment variables, credentials, and tools are available.
* Feature ownership is not already locked by another agent.

If readiness fails, the skill must update the feature status to `BLOCKED` and document the reason.

### 10.4 Impact Analysis

The skill must identify likely impacts across:

* Front-end pages and components.
* Backend APIs and services.
* Database schema and migrations.
* Authentication and authorization.
* Third-party integrations.
* Background jobs and queues.
* Notifications.
* Monitoring and observability.
* Existing tests.
* Documentation.
* Feature flags.
* Analytics and event tracking.

The impact analysis must be stored in `impacted-components.md` or appended to it.

### 10.5 Implementation Planning

The skill must create or update `implementation-plan.md` with:

* Ordered implementation steps.
* Affected files or modules.
* Required API changes.
* Required schema changes.
* Test strategy.
* Rollback considerations.
* Risks and assumptions.
* Validation criteria.
* Estimated complexity level.
* Dependencies on other features or teams.

The plan must be actionable enough for another developer or agent to continue work from the same point.

### 10.6 Isolated Development Environment

The skill should work in an isolated branch or worktree.

Suggested branch format:

```text
feature/FEAT-001-supplier-onboarding
```

The skill must not make implementation changes directly on protected branches such as `main`, `master`, or `production`.

### 10.7 Implementation

The skill must:

* Follow repository coding standards.
* Reuse existing patterns and abstractions where appropriate.
* Avoid unnecessary refactoring.
* Keep changes within the approved feature scope.
* Add or update tests with code changes.
* Maintain backward compatibility unless the feature explicitly requires a breaking change.
* Document important technical decisions in `decisions.md`.

### 10.8 Validation

The skill must run relevant validation checks, including where applicable:

* Linting.
* Formatting checks.
* Type checking.
* Unit tests.
* Integration tests.
* API contract tests.
* End-to-end tests.
* Build validation.
* Security scans.
* Dependency checks.
* Database migration validation.
* Accessibility checks.
* Performance checks.
* Feature-specific acceptance tests.

Validation results must be documented in `implementation-log.md`.

### 10.9 Acceptance Criteria Validation

The skill must explicitly map implementation results to acceptance criteria.

Example format:

| Acceptance Criterion                | Validation Method    | Result | Evidence                       |
| ----------------------------------- | -------------------- | ------ | ------------------------------ |
| Supplier can submit onboarding form | End-to-end test      | Passed | `supplier-onboarding.spec.ts`  |
| Duplicate tax ID is rejected        | API integration test | Passed | `supplier-api.test.ts`         |
| Only admin can approve supplier     | Permission test      | Passed | `approval-permissions.test.ts` |

A feature cannot move to `READY_FOR_PR` until all mandatory acceptance criteria are passed or formally waived by a human.

### 10.10 Repair Loop

When tests or review checks fail, the skill must:

1. Identify the failure cause.
2. Determine whether the issue is actionable.
3. Make a focused correction.
4. Re-run only the relevant validation first.
5. Run the broader validation suite after the focused fix succeeds.
6. Record the attempt and result in `implementation-log.md`.

The skill must avoid repetitive blind retries.

Default maximum focused repair attempts: 3.

### 10.11 Documentation and Tracker Updates

After meaningful progress, the skill must update:

* `delivery-status.md`
* `implementation-log.md`
* `implementation-plan.md`
* `decisions.md`, where applicable
* `feature-tracker.md`

The tracker should include:

* Current state.
* Assigned agent or owner.
* Start date.
* Last updated date.
* Current blocker, if any.
* Validation status.
* PR link or identifier, where available.
* Next action.

### 10.12 Pull Request Preparation

Before creating or preparing a pull request, the skill must ensure:

* All required tests pass.
* Acceptance criteria are validated.
* Documentation is updated.
* No unresolved critical or high-severity issue remains.
* Change summary is generated.
* Known limitations and follow-up work are listed.
* Reviewer instructions are included.

The pull request summary should include:

* Feature purpose.
* Scope of changes.
* Technical approach.
* Affected pages, APIs, and services.
* Tests run.
* Acceptance criteria status.
* Risks or rollout considerations.
* Open follow-up items.

---

## 11. Required Sub-Skills

The Feature Delivery Loop skill should orchestrate the following reusable sub-skills.

```text
dev-agent/
  skills/
    feature-delivery-loop/
    feature-context-reader/
    implementation-planner/
    impact-analyzer/
    code-implementer/
    test-runner/
    acceptance-validator/
    code-reviewer/
    security-reviewer/
    tracker-updater/
    pr-preparer/
    blocker-escalator/
```

### Sub-Skill Responsibilities

| Sub-Skill              | Responsibility                                                                               |
| ---------------------- | -------------------------------------------------------------------------------------------- |
| feature-context-reader | Reads and summarizes feature and project context.                                            |
| implementation-planner | Creates detailed implementation steps.                                                       |
| impact-analyzer        | Identifies impacted pages, APIs, services, schemas, and integrations.                        |
| code-implementer       | Makes scoped code changes.                                                                   |
| test-runner            | Runs relevant validation suites.                                                             |
| acceptance-validator   | Maps test results to business acceptance criteria.                                           |
| code-reviewer          | Reviews code quality, maintainability, regressions, and standards.                           |
| security-reviewer      | Checks authentication, authorization, secrets, input validation, and common vulnerabilities. |
| tracker-updater        | Updates feature state, logs, and central tracker.                                            |
| pr-preparer            | Generates pull request description and review handoff.                                       |
| blocker-escalator      | Creates structured escalation notes when human input is required.                            |

---

## 12. Escalation Rules

The skill must escalate instead of guessing when any of the following conditions occur.

### Business and Scope Escalations

* Acceptance criteria are unclear or contradictory.
* The implementation requires a product decision.
* The feature scope conflicts with another feature.
* New requirements emerge that are not present in the feature documentation.
* A user workflow cannot be determined from existing context.

### Technical Escalations

* Required external API or service is unavailable.
* Required schema change may cause data loss.
* Authentication or authorization rules are unclear.
* A breaking API contract change is required.
* A dependency has incompatible versions.
* Existing architecture cannot support the requested feature without major redesign.
* The repository build is already broken before the agent’s changes.

### Security and Compliance Escalations

* Sensitive data handling is unclear.
* A security vulnerability is identified.
* The feature impacts regulated data, audit logging, retention, consent, or permissions.
* Production credentials or secrets are required.
* The change could expose user data.

### Retry Escalations

* The same test failure remains after three focused repair attempts.
* Fixing one failure repeatedly creates regressions elsewhere.
* The root cause cannot be isolated with available context.
* Validation requires external access unavailable to the agent.

---

## 13. Required Escalation Output

When blocked, the skill must create a structured escalation note.

```markdown
# Blocker Escalation

## Feature
FEAT-001 — Supplier Onboarding

## Current State
BLOCKED

## What Was Attempted
- Reviewed onboarding workflow.
- Implemented supplier form submission endpoint.
- Attempted integration with tax validation API.

## Blocker
Tax validation API contract is not available in the project context or repository.

## Impact
Supplier duplicate validation cannot be completed.
Acceptance criterion AC-04 cannot be validated.

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

## 14. Completion Criteria

A feature can move to `READY_FOR_PR` only when all applicable conditions are met.

### Mandatory Conditions

* Feature scope is implemented.
* Required acceptance criteria are validated.
* Relevant tests pass.
* Build and static checks pass.
* Required documentation is updated.
* No unresolved critical or high-severity defect remains.
* No unresolved blocker remains.
* Feature tracker reflects the latest status.
* Pull request summary is prepared.

### Optional Conditions

Depending on project requirements:

* Accessibility checks pass.
* Performance checks pass.
* Security review passes.
* End-to-end tests pass.
* Feature flag configuration is documented.
* Release notes are generated.
* Monitoring and alerts are configured.

---

## 15. Loop Control and Guardrails

The skill must include controls to prevent uncontrolled agent behavior.

### Retry Limits

* Maximum focused repair attempts: 3.
* Maximum broad validation cycles: 2.
* Maximum auto-generated implementation plans per feature: 2.
* Maximum scope-expansion attempts: 0 without human approval.

### Permission Boundaries

The skill must not:

* Merge pull requests without approval.
* Deploy to production without approval.
* Delete production data.
* Modify secrets.
* Change infrastructure permissions.
* Disable security controls.
* Ignore failing tests.
* Bypass code review requirements.

### Scope Boundaries

The skill must:

* Work only on files related to the selected feature.
* Document any required cross-feature impact.
* Raise a scope escalation before modifying unrelated modules.
* Avoid opportunistic refactoring unless it is necessary to complete the feature safely.

---

## 16. Logging Requirements

Every execution should create or update an implementation log.

Example:

```markdown
# Implementation Log

## 2026-07-03

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

### Next Action
Investigate validation middleware and API error contract.
```

---

## 17. Success Metrics

The skill should track metrics that indicate whether it is improving delivery quality.

| Metric                     | Description                                                                 |
| -------------------------- | --------------------------------------------------------------------------- |
| Feature completion rate    | Percentage of features reaching `READY_FOR_PR`.                             |
| First-pass validation rate | Percentage of features passing validation without repair loops.             |
| Average repair attempts    | Average number of retries required per feature.                             |
| Escalation rate            | Percentage of features requiring human intervention.                        |
| Escalation quality         | Percentage of escalations resolved without additional clarification.        |
| Regression rate            | Defects introduced after merge.                                             |
| Acceptance coverage        | Percentage of acceptance criteria linked to automated or manual validation. |
| Documentation freshness    | Percentage of completed features with updated context and tracker files.    |
| Cycle time                 | Time from `READY_FOR_DEV` to `READY_FOR_PR`.                                |

---

## 18. Example Invocation

```text
Run feature-delivery-loop for FEAT-001-supplier-onboarding.

Mode: implement
Repository: /workspace/recycling-platform
Context: /workspace/recycling-platform/context
Branch: feature/FEAT-001-supplier-onboarding

Requirements:
- Read all feature and project context before implementation.
- Create or update implementation-plan.md.
- Run unit, integration, and acceptance tests.
- Retry actionable failures up to three times.
- Update delivery-status.md and feature-tracker.md.
- Stop and escalate for unclear business rules, external dependency gaps, schema risks, security concerns, or unresolved test failures.
- Do not merge or deploy.
```

---

## 19. Recommended Skill Prompt Behavior

The skill should follow this operating principle:

```text
Treat the feature context as the source of truth.
Do not begin implementation until the feature is sufficiently ready.
Plan before coding.
Validate every meaningful change.
Use tests and acceptance criteria as evidence of completion.
Fix only actionable issues within defined retry limits.
Persist progress, decisions, and blockers in the context folder.
Escalate ambiguity, risk, or scope decisions instead of guessing.
Never mark a feature complete merely because code was generated.
```

---

## 20. Future Enhancements

Future versions of the skill may support:

* Parallel sub-agent execution for frontend, backend, QA, and review tasks.
* Automated worktree management.
* Pull request creation and GitHub integration.
* CI/CD pipeline integration.
* Automated screenshot validation for UI features.
* Feature-specific AI test generation.
* Performance regression detection.
* Release readiness checks.
* Production monitoring validation after deployment.
* Automated learning from review feedback and recurring defects.
* Cross-feature dependency graph management.
