---
name: ba-extraction
description: What the BA Agent extracts from eligible artifacts and how it records the results. Read before extracting BA intelligence during /ba:intake. Lists the 20 extraction categories, the living scope document structure, and the schema of every supporting register and shared-context file.
---

# BA intelligence extraction

For each eligible (Deep Analysis / sampled) artifact, extract the categories below, assign a stable ID and confidence value (see `delivery-os-conventions`), and cite the source `[SRC-### › path]`.

## The 20 extraction categories

1. Business objectives
2. Stakeholders and actors
3. Current workflows
4. Future expectations
5. Functional requirements
6. Business rules
7. Data entities
8. Integrations
9. Reports and dashboards
10. Notifications and alerts
11. Permissions and roles
12. Pain points
13. Manual effort
14. Exceptions and edge cases
15. Compliance and security requirements
16. Examples and scenarios
17. Terminology and glossary items
18. Assumptions
19. Clarifications needed
20. Contradictions with existing scope

## Living scope document (`ba-output/scope.md`)

Maintain these sections (full template ships at `delivery-os-core/templates/ba-output/scope.md`):

1. Project Context — client, business unit, objective, discovery status, last updated, maturity (Draft/Emerging/Reviewed/Frozen)
2. Source Material Summary — `| Source | Type | Processed Status | Key Contribution |`
3. Current-State Workflows — name, trigger, actors, steps, systems, inputs, outputs, pain points, source refs
4. Pain Points & Operational Gaps — `| Pain Point | Impact | Frequency | Source | Confidence |`
5. Future-State / AI-Reimagined Workflows — trigger, system actions, AI actions, human review points, exception handling, output, source refs
6. Functional Scope — `| Module | Capability | Description | Priority | Source | Status |`
7. Business Rules — `| Rule ID | Rule | Applies To | Source | Confidence | Open Questions |`
8. Data Requirements — `| Entity | Data Needed | Source System | Used For | Sensitivity | Open Questions |`
9. Integrations — `| System | Purpose | Direction | Data Exchanged | Dependency | Risk |`
10. Roles & Permissions — `| Role | Capabilities | Restrictions | Approval Rights |`
11. Reports, Dashboards & Notifications — `| Item | Audience | Trigger/Frequency | Purpose | Source |`
12. Examples Captured — `| Example ID | Scenario | Source | Workflow | Why It Matters |`
13. Edge Cases & Exceptions — `| Scenario | Expected Handling | Source | Clarification Needed |`
14. Non-Functional Requirements — security, performance, auditability, availability, compliance, logging, retention, scalability
15. Assumptions — `| Assumption | Reason | Risk | Validation Needed |`
16. Out of Scope — `| Item | Reason | Future Phase? |`
17. Acceptance Criteria — `| Capability | Acceptance Criteria | Validation Method |`
18. Clarification Questions — grouped by workflow / business rules / data / integration / security / reporting / timeline / commercial
19. Change History — `| Date | Intake Run | Summary of Changes |`

## Supporting registers (`ba-output/`)

Each register is a Markdown file with frontmatter + a table. Suggested columns:

| Register | Key columns |
|---|---|
| `requirement-register.md` | REQ ID, Requirement, Module, Source, Confidence, Status, Open Questions |
| `workflow-register.md` | WF ID, Name, State (current/future), Trigger, Actors, Steps, Systems, Outputs, Exceptions, Source |
| `business-rule-register.md` | BR ID, Rule, Applies To, Source, Confidence, Clarification |
| `example-register.md` | EX ID, Scenario, Maps To (WF/REQ), Source, Why It Matters |
| `data-register.md` | DATA ID, Entity, Fields, Source System, Sensitivity, Used For, Open Questions |
| `integration-register.md` | INT ID, System, Purpose, Direction, Data Exchanged, Dependency, Risk |
| `assumption-register.md` | ASM ID, Assumption, Reason, Risk, Validation Needed |
| `clarification-log.md` | CLR ID, Question, Category, Raised By Run, Status, Answer |
| `contradiction-log.md` | CON ID, Conflicting Statements, Sources, Impact, Resolution Status |
| `artifact-map.md` | SRC ID, Source, Type, File Count, Size, Usage Mode, Agent Decision |
| `artifact-ledger.md` | File, SRC, Status, Version/Hash, Modified Date, Processing Status |
| `source-classification.md` | SRC ID, Usage Mode, Reason, Action Taken |
| `change-log.md` | Date, Intake Run, Summary of Changes |
| `indexing-assistance-needed.md` | Item, Why, Recommended Usage Mode, Status |

## Shared-context files (`shared-context/`)

- `project-profile.md` — core project info
- `glossary.md` — business terms, acronyms, client vocabulary
- `stakeholder-map.md` — names, roles, teams, involvement
- `system-landscape.md` — systems, tools, platforms, integration touchpoints
- `decision-log.md` — confirmed decisions (DEC) and their impact

## Intake run summary (`ba-output/intake-runs/run-###.md`)

Sections: Run Details (date, mode, input index, scope version) · Artifacts Scanned (totals by status) · Sources Processed table · New Information Identified · Scope Updates Made · Registers Updated · Contradictions Found · Clarifications Added · Indexing Assistance Needed · Risk Notes · Next Recommended Actions.
