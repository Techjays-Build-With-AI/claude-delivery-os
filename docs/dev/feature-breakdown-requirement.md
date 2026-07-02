# BA Agent Skill: Feature Breakdown

## Skill Name

`ba-agent:feature-breakdown`

## Objective

Convert a scope document and supporting discovery artifacts into a structured, implementation-ready feature breakdown.

The output must help a human developer, tech lead, QA engineer, or coding agent understand:

* What needs to be built
* Why it needs to be built
* Which users are involved
* What business problem it solves
* How the user journey should work
* Which pages, APIs, workflows, integrations, and data entities are expected
* What assumptions, dependencies, risks, and open questions remain
* How the feature should be validated before it is considered complete

The skill does not write production code. Its responsibility is to create the implementation context required before development begins.

---

## When to Use

Run this skill after one or more of the following are available:

* Scope document
* PRD
* Discovery notes
* Stakeholder interview notes
* Workflow diagrams
* Existing product documentation
* Screenshots or wireframes
* API documentation
* Existing repository context
* Reference files from the client
* Business process documents
* Acceptance criteria

The skill may also be run again when the scope changes.

---

## Inputs

The command may receive one or more of the following:

```text
- Scope document path
- Reference artifact folder
- Requirement markdown files
- Workflow documents
- Existing context folder
- Existing product or codebase documentation
- Clarification notes
- Change request documents
```

Example command:

```bash
ba-agent:feature-breakdown \
  --scope ./docs/scope.md \
  --references ./reference-artifacts \
  --context ./context
```

Example natural-language instruction:

```text
Review the scope document, workflow notes, and client reference files.
Break the scope into implementation-ready features.
Create or update the feature folders inside /context/features.
Mark missing information as open questions instead of inventing requirements.
```

---

## Required Behavior

The BA Agent must:

1. Review all supplied documents before creating features.
2. Identify the major business capabilities in scope.
3. Break each capability into independently understandable features.
4. Avoid creating features that are too broad to estimate, build, test, or release.
5. Avoid creating features that are too small to have meaningful business value unless they are clearly reusable technical capabilities.
6. Identify dependencies between features.
7. Identify expected pages, APIs, workflows, integrations, background jobs, events, and data entities.
8. Clearly distinguish between:

   * Confirmed requirements
   * Assumptions
   * Open questions
   * Out-of-scope items
   * Future-phase items
9. Preserve traceability back to the source scope or requirement document.
10. Update the feature index after creating or modifying features.
11. Never fabricate product behavior, UI behavior, business rules, API contracts, data schemas, or integrations that are not supported by the source material.

---

## Feature Definition Standard

A feature is a meaningful business capability that can be planned, implemented, tested, and tracked.

A feature should usually represent one of the following:

* A user-facing business capability
* A workflow stage
* A reusable domain capability
* A meaningful integration capability
* An operational or administrative capability
* A major reporting, approval, compliance, or automation function

Examples:

```text
Good feature examples:
- Supplier Onboarding
- Supplier Approval Workflow
- Outlet Discovery and Recommendation
- RFP Creation and Distribution
- Proposal Generation
- Contract Approval Workflow
- User and Role Management
- Notification Center
- Audit History
- CRM Synchronization
```

Avoid treating these as standalone business features unless necessary:

```text
Usually too small:
- Create Supplier API
- Edit Button
- Supplier Status Dropdown
- Database Migration
- Email Template
```

These should normally be documented as part of a feature.

---

## Output Folder Structure

The skill must create the following structure:

```text
/context
  /features
    feature-index.md

    /supplier-onboarding
      feature.md
      implementation-plan.md
      workflow.md
      acceptance-criteria.md
      dependencies.md
      open-questions.md
      status.md

    /supplier-approval
      feature.md
      implementation-plan.md
      workflow.md
      acceptance-criteria.md
      dependencies.md
      open-questions.md
      status.md
```

Feature folder names must use lowercase kebab-case.

Example:

```text
supplier-onboarding
outlet-discovery
proposal-generation
contract-approval
```

---

# Required Files Per Feature

## 1. feature.md

This is the primary business and product context document.

```md
# Feature: Supplier Onboarding

## Feature ID
FEAT-SUP-001

## Status
Proposed | Ready for Planning | In Development | In QA | UAT | Released | Blocked

## Summary
Allow internal users to create and manage supplier profiles before the supplier can participate in sourcing workflows.

## Business Objective
Reduce manual supplier onboarding through email, spreadsheets, and disconnected internal tools.

## Business Problem Solved
The current process requires operations teams to manually gather supplier information, validate documents, track approval status, and coordinate with compliance teams.

## Users
- Operations Coordinator
- Supplier Manager
- Compliance Reviewer
- Finance Reviewer
- System Administrator

## User Value
- Faster supplier setup
- Reduced manual follow-up
- Clear approval visibility
- Better compliance tracking
- Consistent supplier information

## In Scope
- Create supplier profile
- Add supplier contacts
- Upload compliance documents
- Validate mandatory fields
- Submit supplier for review
- Track onboarding status
- View approval history

## Out of Scope
- Supplier contract generation
- Supplier payment setup
- Supplier performance scoring

## Related Business Workflows
- Supplier Onboarding
- Supplier Approval
- Supplier Compliance Review

## Related Pages
- Supplier List Page
- Create Supplier Page
- Supplier Details Page
- Supplier Approval Queue

## Related APIs / Services
- POST /suppliers
- GET /suppliers/{supplierId}
- PUT /suppliers/{supplierId}
- POST /suppliers/{supplierId}/submit-for-review
- POST /suppliers/{supplierId}/documents

## Related Data Entities
- suppliers
- supplier_contacts
- supplier_documents
- supplier_status_history
- audit_log

## Related Integrations
- Document storage provider
- CRM
- Notification service

## Dependencies
- User and Role Management
- Document Upload Capability
- Notification Service

## Assumptions
- Supplier onboarding will be performed by internal users.
- Mandatory compliance documents will be configurable.
- Supplier records must support draft status before submission.

## Open Questions
- Who can approve suppliers?
- What are the mandatory document types?
- Is finance approval required for every supplier?
- Are suppliers allowed to update their own profile?

## Source References
- Scope Document: Section 3.2 Supplier Management
- Discovery Notes: Supplier Intake Workshop, June 2026
```

---

## 2. implementation-plan.md

This file explains how the feature should be broken into buildable work areas.

It must not contain low-level code instructions unless those are already confirmed by the technical design.

```md
# Implementation Plan: Supplier Onboarding

## Implementation Goal
Enable internal teams to create, validate, review, and submit supplier profiles for approval.

## Proposed Build Areas

### 1. Supplier Profile Management
Users can create, edit, save, and view supplier profiles.

Expected pages:
- Supplier List Page
- Create Supplier Page
- Supplier Details Page

Expected backend capabilities:
- Create supplier
- Retrieve supplier
- Update supplier
- Search suppliers

Expected data entities:
- suppliers
- supplier_contacts

### 2. Supplier Document Management
Users can upload and manage compliance documents.

Expected pages:
- Supplier Details Page
- Document Upload Modal

Expected backend capabilities:
- Upload supplier document
- Retrieve supplier documents
- Validate document metadata
- Delete or replace document

Expected data entities:
- supplier_documents

Expected integrations:
- File storage service

### 3. Supplier Review Submission
Users can submit a supplier for review once all required fields are complete.

Expected backend capabilities:
- Validate onboarding completeness
- Change supplier status
- Record status history
- Notify reviewers

Expected data entities:
- suppliers
- supplier_status_history
- audit_log

### 4. Approval Queue
Approvers can review pending suppliers and approve or reject them.

Expected pages:
- Supplier Approval Queue
- Supplier Details Page

Expected backend capabilities:
- Retrieve suppliers pending review
- Approve supplier
- Reject supplier
- Record approval decision

## Suggested Delivery Sequence
1. Supplier data model and basic profile management
2. Supplier list and detail pages
3. Document upload and validation
4. Submit-for-review workflow
5. Approval queue and decision workflow
6. Notifications and audit history
7. QA, UAT, and edge-case validation

## Technical Considerations
- Supplier status transitions must be controlled through backend validation.
- Approval actions must be auditable.
- File uploads must be linked to the correct supplier record.
- Role-based access must be enforced for approval actions.
- Supplier records should support draft saving.

## Potential Risks
- Mandatory document rules are not yet confirmed.
- Approval workflow may differ by supplier type or geography.
- Existing supplier data may require migration or cleanup.

## Implementation Readiness
Partially Ready

## Blocking Items
- Approval matrix confirmation
- Mandatory document list
- Document storage integration confirmation
```

---

## 3. workflow.md

This file explains the end-to-end business journey.

```md
# Workflow: Supplier Onboarding

## Trigger
An internal operations user needs to onboard a new supplier.

## Primary Flow

1. User opens the Supplier List Page.
2. User selects Create Supplier.
3. User enters supplier company information.
4. User adds supplier contacts.
5. User uploads mandatory compliance documents.
6. System validates required fields and required documents.
7. User saves the supplier as Draft or submits it for review.
8. System changes supplier status to Pending Review.
9. System notifies the assigned reviewer.
10. Reviewer opens the Supplier Approval Queue.
11. Reviewer approves or rejects the supplier.
12. System records the decision in audit history.
13. If approved, the supplier becomes available for sourcing workflows.

## Alternative Flows

### Save Draft
The user may save incomplete supplier information as Draft and complete it later.

### Missing Mandatory Documents
The system prevents submission and displays missing document requirements.

### Rejection
The reviewer rejects the supplier and provides a rejection reason.

### Rework
The operations user updates the supplier profile and resubmits it for review.

## Business Rules
- Only users with relevant permissions can submit suppliers for review.
- Only authorized approvers can approve or reject suppliers.
- Rejection requires a reason.
- Supplier cannot be used in sourcing until status is Approved.
- Approval history must not be editable.

## Related Features
- Supplier Approval Workflow
- Notification Center
- Audit History
```

---

## 4. acceptance-criteria.md

This file must define testable outcomes.

```md
# Acceptance Criteria: Supplier Onboarding

## Supplier Creation

- A user can create a supplier profile with required company information.
- A supplier profile can be saved as Draft.
- Draft suppliers are not visible in sourcing workflows.
- Duplicate supplier validation is performed based on configured business rules.

## Document Management

- A user can upload mandatory supplier documents.
- Uploaded documents are associated with the correct supplier.
- The system identifies missing mandatory document types.
- Users can replace expired or incorrect documents.

## Submission for Review

- A user can submit a supplier only when required fields and documents are complete.
- Submission changes the supplier status to Pending Review.
- Submission creates a status-history record.
- Relevant reviewers receive a notification.

## Approval

- Authorized reviewers can approve or reject a supplier.
- Rejection requires a reason.
- Approval changes the supplier status to Approved.
- Approved suppliers become available for downstream sourcing workflows.
- Approval and rejection actions are recorded in audit history.

## Permissions

- Users without approval permission cannot approve or reject suppliers.
- Users without edit permission cannot modify supplier details.
```

---

## 5. dependencies.md

This file documents all upstream and downstream dependencies.

```md
# Dependencies: Supplier Onboarding

## Upstream Dependencies
- User authentication
- Role and permission management
- Document storage service
- Notification service

## Downstream Dependencies
- Supplier Approval Workflow
- Outlet Discovery
- RFP Generation
- Contract Generation
- Supplier Reporting

## Data Dependencies
- suppliers
- supplier_contacts
- supplier_documents
- supplier_status_history
- audit_log

## Integration Dependencies
- CRM synchronization
- File storage provider
- Email or notification provider

## Dependency Risks
- CRM may have duplicate supplier records.
- File storage provider may impose upload-size restrictions.
- Approval workflow may require region-specific rules.
```

---

## 6. open-questions.md

This file must capture unresolved decisions without guessing.

```md
# Open Questions: Supplier Onboarding

| ID | Question | Owner | Impact | Status |
|---|---|---|---|---|
| OQ-SUP-001 | What document types are mandatory for onboarding? | Compliance Team | Blocks validation rules | Open |
| OQ-SUP-002 | Can suppliers update their own information through a portal? | Product Owner | Impacts user roles and UI scope | Open |
| OQ-SUP-003 | Does approval require one reviewer or multiple approval stages? | Operations Lead | Impacts workflow design | Open |
| OQ-SUP-004 | What defines a duplicate supplier? | Data Owner | Impacts validation logic | Open |
| OQ-SUP-005 | Should rejected suppliers be allowed to resubmit? | Product Owner | Impacts state transitions | Open |
```

---

## 7. status.md

This file acts as the operational tracker for the feature.

```md
# Feature Status: Supplier Onboarding

## Current Status
Ready for Planning

## Feature Owner
Unassigned

## Technical Owner
Unassigned

## QA Owner
Unassigned

## Priority
High

## Target Release
TBD

## Development Progress

| Area | Status | Owner | Notes |
|---|---|---|---|
| Requirement Review | Complete | BA Agent | Initial feature context created |
| UX / Page Design | Not Started | Unassigned | Awaiting design direction |
| API Design | Not Started | Unassigned | Dependent on approval rules |
| Data Design | Not Started | Unassigned | Need document requirements |
| Development | Not Started | Unassigned | — |
| QA | Not Started | Unassigned | — |
| UAT | Not Started | Unassigned | — |

## Current Blockers
- Mandatory document list is not confirmed.
- Approval workflow is not confirmed.

## Last Updated
YYYY-MM-DD
```

---

# Feature Index

The BA Agent must create and maintain:

```text
/context/features/feature-index.md
```

Example:

```md
# Feature Index

| Feature ID | Feature | Status | Priority | Dependencies | Folder |
|---|---|---|---|---|---|
| FEAT-SUP-001 | Supplier Onboarding | Ready for Planning | High | User Management, Document Storage | ./supplier-onboarding |
| FEAT-SUP-002 | Supplier Approval Workflow | Proposed | High | Supplier Onboarding, Notification Service | ./supplier-approval |
| FEAT-SRC-001 | Outlet Discovery | Proposed | High | Supplier Onboarding, Outlet Data | ./outlet-discovery |
| FEAT-RFP-001 | RFP Generation | Proposed | Medium | Outlet Discovery, Notification Service | ./rfp-generation |
```

---

# Feature Breakdown Rules

## Rule 1: Preserve Business Value

Every feature must explain its business value.

Do not create a feature that only describes a technical component unless that component provides a reusable business capability.

---

## Rule 2: Keep Features Independently Understandable

A developer should be able to open a feature folder and understand the feature without reading the entire scope document.

The feature folder should contain enough context to answer:

```text
What are we building?
Why are we building it?
Who uses it?
What should happen?
What depends on it?
How do we test it?
What is still unclear?
```

---

## Rule 3: Link, Do Not Duplicate

The feature document may reference pages, APIs, data entities, workflows, and integrations.

Do not duplicate detailed API contracts or database schemas inside the feature folder once those context files exist.

Example:

```md
Related Page:
../../frontend/pages/suppliers/supplier-details.md

Related API:
../../backend/domains/suppliers/endpoints/create-supplier.md

Related Data Entity:
../../data/tables/suppliers.md
```

---

## Rule 4: Mark Uncertainty Explicitly

Use these labels:

```text
Confirmed
Assumption
Open Question
Dependency
Risk
Out of Scope
Future Phase
```

Never turn an assumption into a confirmed requirement.

---

## Rule 5: Support Incremental Refinement

The first feature breakdown does not need to be perfect.

The BA Agent must support re-running the skill when:

* Scope changes
* New stakeholder input is received
* Technical design introduces constraints
* UX decisions change
* QA discovers edge cases
* A feature is split, merged, deferred, or removed

When updating a feature, preserve history where possible and clearly identify what changed.

---

# Completion Criteria

The feature breakdown is complete when:

* Every major scope item maps to one or more features.
* Every feature has a dedicated folder.
* Every feature includes business purpose, user context, workflow, acceptance criteria, dependencies, assumptions, and open questions.
* Features are indexed in `feature-index.md`.
* Features have preliminary implementation sequencing.
* Cross-feature dependencies are documented.
* Unresolved scope questions are visible and assigned where possible.
* No source requirement is silently dropped.
* Every feature is understandable by a coding agent without requiring full rediscovery of the project.
