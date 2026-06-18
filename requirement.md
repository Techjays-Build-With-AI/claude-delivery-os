# Techjays Delivery OS — Requirements Specification

## 1. Overview

**Techjays Delivery OS** is an internal Claude Code plugin intended to standardize and automate key delivery workflows across Techjays.

The plugin will initially focus on the **Business Analyst Agent**, which will process client discovery artifacts, maintain a living project scope document, and create structured outputs that can later be reused by documentation and technical review agents.

Over time, the plugin will expand to include:

* **BA Agent** — Discovery intake, scope creation, requirement extraction, clarification management.
* **Doc Agent** — Proposal, walkthrough, SRS, SoW, and executive document generation.
* **TL Agent** — Architecture review, code review, security review, observability review, compliance review, and project maturity scoring.

---

## 2. Plugin Name

```text
Techjays Delivery OS
```

## 3. Purpose

The purpose of Techjays Delivery OS is to create a reusable AI-powered operating system for project discovery, scope management, documentation, technical validation, and delivery maturity.

The plugin should help Techjays teams move from raw client inputs to structured delivery outputs with consistency, traceability, and reduced manual effort.

---

## 4. Initial Scope

The first release will focus only on the **Business Analyst Agent**.

### Initial Command

```text
/ba:intake
```

### Future Commands

```text
/doc:proposal
/doc:walkthrough
/doc:srs
/doc:sow
/doc:executive-summary

/tl:architecture-review
/tl:code-review
/tl:security-review
/tl:observability-review
/tl:compliance-review
/tl:maturity-score

/delivery:risk-review
/delivery:sprint-readiness
/delivery:release-readiness
```

---

# 5. Business Analyst Agent

## 5.1 Purpose

The Business Analyst Agent is responsible for processing client discovery artifacts and maintaining a living project scope document during the discovery phase.

The discovery phase may span multiple weeks. During this period, new artifacts such as meeting notes, transcripts, reference documents, sample files, screenshots, spreadsheets, and client requirement documents may be added continuously.

The BA Agent should process newly added or changed artifacts, identify what is new, update the living scope document, and maintain supporting registers such as requirements, workflows, business rules, examples, assumptions, clarifications, and contradictions.

---

## 5.2 Core Behavior

The BA Agent should behave as the project discovery memory.

It should:

1. Read the project intake index.
2. Scan referenced local folders and Google Drive links.
3. Classify artifacts before analysis.
4. Identify new, changed, unchanged, inaccessible, and reference-only artifacts.
5. Avoid fully analyzing large reference folders unless explicitly instructed.
6. Extract relevant BA intelligence from eligible artifacts.
7. Update the living scope document.
8. Maintain artifact traceability.
9. Maintain requirement and workflow registers.
10. Create clarification questions.
11. Log contradictions.
12. Produce an intake run summary.
13. Prepare structured outputs for future Doc Agent and TL Agent usage.

---

# 6. Artifact Intake Model

## 6.1 Artifact Sources

Artifacts may come from:

* Local folders
* Local files
* Google Drive folders
* Google Drive files
* Meeting transcripts
* Client requirement documents
* Functional specification documents
* Reference documents
* Screenshots
* Sample data files
* Historical records
* Reports
* Existing process documents
* Code repositories, for future TL Agent usage

---

## 6.2 Intake Index File

Each project should contain an intake index file.

Recommended file name:

```text
intake.index.md
```

The index file should define:

* Project details
* Artifact sources
* Source type
* Source location
* Usage mode
* Authority level
* Priority
* Access requirements
* Processing rules
* Output location

---

## 6.3 Sample Intake Index

```markdown
# Project Intake Index

## Project
- Client:
- Project Name:
- Business Domain:
- Project Stage:
- Discovery Owner:
- Discovery Start Date:

## Artifact Sources

### Source 1: Client Requirement Documents
- Type: Local Folder
- Path: ./raw-artifacts/client-requirements
- Content: Requirement specifications and functional documents shared by the client
- Usage Mode: Deep Analysis
- Authority: High
- Priority: High

### Source 2: Meeting Transcripts
- Type: Local Folder
- Path: ./raw-artifacts/meeting-transcripts
- Content: Discovery meeting transcripts and notes
- Usage Mode: Deep Analysis
- Authority: Medium
- Priority: High

### Source 3: Historical Invoice Repository
- Type: Local Folder
- Path: ./raw-artifacts/reference/invoices-2025
- Content: Historical invoice PDFs shared by the client for reference
- Usage Mode: Reference Only
- Authority: Medium
- Priority: Low
- Intake Rule: Do not fully analyze during intake. Create an index only.

### Source 4: Google Drive Reference Folder
- Type: Google Drive
- Link: https://drive.google.com/...
- Content: Client-shared reference documents, screenshots, and sample files
- Usage Mode: Reference Only
- Authority: Medium
- Priority: Medium
- Access Required: Google Drive MCP / Connector
- Fallback: Export locally to ./raw-artifacts/drive-reference

### Source 5: Existing Application Repository
- Type: Code Repository
- Path: ../client-application-repo
- Content: Existing application codebase
- Usage Mode: Future Agent Input
- Future Agent: TL Agent
- Intake Rule: Do not analyze during BA intake unless explicitly requested.
```

---

# 7. Artifact Usage Modes

The BA Agent should classify each artifact source using one of the following usage modes.

## 7.1 Deep Analysis

Used for primary discovery artifacts.

Examples:

* Requirement documents
* BRDs
* FRDs
* SRS documents
* Meeting notes
* Discovery transcripts
* Process documents
* Client clarification responses

Behavior:

* Read fully.
* Extract requirements, workflows, business rules, actors, examples, assumptions, gaps, and clarifications.
* Update the scope document and registers.

---

## 7.2 Reference Only

Used for supporting materials that should not be fully analyzed during intake.

Examples:

* Historical invoices
* Old reports
* Screenshots
* Sample files
* Large document archives
* Client data dumps
* Transaction history

Behavior:

* Do not deeply analyze.
* Create an index entry.
* Capture high-level description.
* Use later only when a requirement needs validation or example reference.

---

## 7.3 Sample and Summarize

Used when a large artifact source is useful but too large for full analysis.

Example:

* 2 GB of historical invoices where only the structure needs to be understood.

Behavior:

* Analyze representative samples only.
* Summarize observed structure.
* Do not infer global business rules unless confirmed by primary artifacts.
* Log sample count and selection assumptions.

---

## 7.4 Index Only

Used when a source is large, unknown, or not immediately relevant.

Behavior:

* Record file names, folder structure, file types, counts, and sizes where possible.
* Do not open every file.
* Do not extract requirements from this source.

---

## 7.5 Future Agent Input

Used for artifacts that are useful for future agents but not immediately relevant to BA intake.

Examples:

* Code repositories
* Architecture documents
* Deployment files
* Observability dashboards
* Security scan outputs

Behavior:

* Register the source.
* Capture why it exists.
* Do not analyze during BA intake unless explicitly instructed.

---

## 7.6 Needs User Guidance

Used when the agent cannot safely determine how an artifact should be handled.

Behavior:

* Do not deeply analyze.
* Add the item to `indexing-assistance-needed.md`.
* Recommend a usage mode.
* Continue processing other safe artifacts.

---

# 8. Large Folder Handling

The BA Agent should not blindly process large folders.

## 8.1 Default Safeguards

If a folder has:

```text
More than 100 files       → Ask or index only
More than 500 MB          → Ask or index only
More than 1 GB            → Index only by default
Unknown file types        → Ask user
Sensitive-looking data    → Ask user before sampling
```

## 8.2 Default Behavior

If a source appears to be a bulk archive, historical reference, or data dump, classify it as:

```text
Reference Only
```

or

```text
Index Only
```

unless the intake index explicitly marks it as:

```text
Deep Analysis
```

---

# 9. Google Drive Handling

## 9.1 Google Drive Access

If a Google Drive link is included in the intake index, the BA Agent should check whether Google Drive MCP or connector access is available.

## 9.2 If Access Is Available

The BA Agent should:

1. List the folder or file contents.
2. Classify artifacts according to usage mode.
3. Process only eligible artifacts.
4. Update the artifact ledger.

## 9.3 If Access Is Not Available

The BA Agent should:

1. Mark the source as `Access Required`.
2. Add it to `indexing-assistance-needed.md`.
3. Ask the user to either:

   * Enable Google Drive MCP / connector access.
   * Export the files locally into `raw-artifacts`.
   * Provide a local synced folder path.
   * Ignore the source for the current intake.

The BA Agent should not pretend to analyze inaccessible Google Drive files.

---

# 10. Project Folder Structure

Each project should follow this structure.

```text
project-name/
├── intake.index.md
├── raw-artifacts/
│   ├── client-requirements/
│   ├── meeting-transcripts/
│   ├── client-reference-docs/
│   ├── system-screenshots/
│   ├── process-maps/
│   ├── sample-data/
│   └── emails/
├── shared-context/
│   ├── project-profile.md
│   ├── glossary.md
│   ├── stakeholder-map.md
│   ├── system-landscape.md
│   └── decision-log.md
├── ba-output/
│   ├── scope.md
│   ├── artifact-map.md
│   ├── artifact-ledger.md
│   ├── source-classification.md
│   ├── requirement-register.md
│   ├── workflow-register.md
│   ├── business-rule-register.md
│   ├── example-register.md
│   ├── data-register.md
│   ├── integration-register.md
│   ├── assumption-register.md
│   ├── clarification-log.md
│   ├── contradiction-log.md
│   ├── indexing-assistance-needed.md
│   ├── change-log.md
│   └── intake-runs/
│       ├── run-001.md
│       ├── run-002.md
│       └── run-003.md
└── final/
```

---

# 11. BA Intake Command

## 11.1 Command Name

```text
/ba:intake
```

## 11.2 Supported Modes

```text
/ba:intake mode=auto
/ba:intake mode=incremental
/ba:intake mode=full-refresh
/ba:intake mode=dry-run
/ba:intake mode=index-only
/ba:intake mode=classify-only
```

## 11.3 Mode Definitions

### auto

Default mode.

The agent should classify sources, deeply analyze primary artifacts, and safely index or skip large/reference artifacts.

### incremental

Processes only new or changed eligible artifacts.

### full-refresh

Rebuilds the scope from all eligible artifacts while preserving previous outputs as backup.

### dry-run

Shows what would be processed and what would change, but does not update files.

### index-only

Scans folders and updates artifact map and artifact ledger only.

### classify-only

Classifies artifact sources and generates user guidance without analyzing content.

---

# 12. BA Intake Processing Flow

The BA Agent should follow this process every time `/ba:intake` runs.

```text
Step 1: Read intake.index.md

Step 2: Discover artifact sources
- Local folders
- Local files
- Google Drive links
- Future references such as code repositories

Step 3: Classify each source
- Deep Analysis
- Reference Only
- Sample and Summarize
- Index Only
- Future Agent Input
- Needs User Guidance

Step 4: Apply safety checks
- File count
- Folder size
- File type
- Source authority
- Relevance to BA scope

Step 5: Compare with artifact-ledger.md
- New
- Changed
- Unchanged
- Missing
- Inaccessible
- Superseded

Step 6: Process eligible sources
- Deep Analysis sources fully
- Sample sources partially
- Reference sources indexed
- Future Agent sources registered only

Step 7: Extract BA intelligence
- Workflows
- Actors
- Requirements
- Business rules
- Examples
- Data needs
- Integrations
- Reports
- Notifications
- Edge cases
- Assumptions
- Clarifications

Step 8: Update living scope document

Step 9: Update supporting registers

Step 10: Produce intake run summary

Step 11: Produce indexing assistance notes where needed
```

---

# 13. BA Intelligence Extraction Requirements

For eligible artifacts, the BA Agent should extract:

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

---

# 14. Living Scope Document

The BA Agent should maintain:

```text
ba-output/scope.md
```

## 14.1 Scope Document Structure

```markdown
# Living Scope Document

## 1. Project Context
- Client
- Business unit
- Project objective
- Current discovery status
- Last updated date
- Current scope maturity: Draft / Emerging / Reviewed / Frozen

## 2. Source Material Summary
| Source | Type | Processed Status | Key Contribution |

## 3. Current-State Workflows
For each workflow:
- Workflow name
- Trigger
- Actors
- Current steps
- Systems involved
- Inputs
- Outputs
- Pain points
- Source references

## 4. Pain Points and Operational Gaps
| Pain Point | Impact | Frequency | Source | Confidence |

## 5. Future-State / AI-Reimagined Workflows
For each workflow:
- Future trigger
- System actions
- AI actions
- Human review points
- Exception handling
- Output
- Source references

## 6. Functional Scope
| Module | Capability | Description | Priority | Source | Status |

## 7. Business Rules
| Rule ID | Rule | Applies To | Source | Confidence | Open Questions |

## 8. Data Requirements
| Entity | Data Needed | Source System | Used For | Sensitivity | Open Questions |

## 9. Integrations
| System | Purpose | Direction | Data Exchanged | Dependency | Risk |

## 10. Roles and Permissions
| Role | Capabilities | Restrictions | Approval Rights |

## 11. Reports, Dashboards, and Notifications
| Item | Audience | Trigger / Frequency | Purpose | Source |

## 12. Examples Captured
| Example ID | Scenario | Source | Workflow | Why It Matters |

## 13. Edge Cases and Exceptions
| Scenario | Expected Handling | Source | Clarification Needed |

## 14. Non-Functional Requirements
- Security
- Performance
- Auditability
- Availability
- Compliance
- Logging
- Data retention
- Scalability

## 15. Assumptions
| Assumption | Reason | Risk | Validation Needed |

## 16. Out of Scope
| Item | Reason | Future Phase? |

## 17. Acceptance Criteria
| Capability | Acceptance Criteria | Validation Method |

## 18. Clarification Questions
Grouped by:
- Workflow
- Business rules
- Data
- Integration
- Security
- Reporting
- Timeline
- Commercial

## 19. Change History
| Date | Intake Run | Summary of Changes |
```

---

# 15. Supporting Registers

The BA Agent should maintain the following registers.

## 15.1 Artifact Map

```text
ba-output/artifact-map.md
```

Purpose:

* Summarize artifact sources.
* Show size, file count, type, usage mode, and agent decision.

## 15.2 Artifact Ledger

```text
ba-output/artifact-ledger.md
```

Purpose:

* Track what has already been processed.
* Track file status, version, hash, modified date, and processing status.

## 15.3 Source Classification

```text
ba-output/source-classification.md
```

Purpose:

* Record how each source was classified.
* Explain why each source was analyzed, sampled, indexed, skipped, or deferred.

## 15.4 Requirement Register

```text
ba-output/requirement-register.md
```

Purpose:

* Maintain extracted requirements with source references, confidence, and status.

## 15.5 Workflow Register

```text
ba-output/workflow-register.md
```

Purpose:

* Maintain current-state and future-state workflows.

## 15.6 Business Rule Register

```text
ba-output/business-rule-register.md
```

Purpose:

* Maintain business rules with source, confidence, and clarification status.

## 15.7 Example Register

```text
ba-output/example-register.md
```

Purpose:

* Maintain real examples and scenarios received from the client.

## 15.8 Data Register

```text
ba-output/data-register.md
```

Purpose:

* Maintain data entities, fields, source systems, sensitivity, and usage.

## 15.9 Integration Register

```text
ba-output/integration-register.md
```

Purpose:

* Maintain systems, integration direction, data exchange, dependency, and risk.

## 15.10 Assumption Register

```text
ba-output/assumption-register.md
```

Purpose:

* Maintain all assumptions with reason, risk, and validation requirement.

## 15.11 Clarification Log

```text
ba-output/clarification-log.md
```

Purpose:

* Maintain open clarification questions grouped by category.

## 15.12 Contradiction Log

```text
ba-output/contradiction-log.md
```

Purpose:

* Maintain conflicting information found across artifacts.

## 15.13 Change Log

```text
ba-output/change-log.md
```

Purpose:

* Track scope and register changes between intake runs.

## 15.14 Indexing Assistance Needed

```text
ba-output/indexing-assistance-needed.md
```

Purpose:

* Identify large, unclear, inaccessible, or ambiguous artifact sources requiring user guidance.

---

# 16. Artifact Status Values

The BA Agent should use the following statuses:

```text
New
Processed
Changed
Unchanged
Missing
Inaccessible
Superseded
Archived
Access Required
Needs User Guidance
```

---

# 17. Confidence Values

The BA Agent should use the following confidence values:

```text
Confirmed
Likely
Assumed
Conflicting
Needs Clarification
```

---

# 18. Intake Run Summary

Every intake run should create a run summary.

Location:

```text
ba-output/intake-runs/run-###.md
```

## 18.1 Run Summary Structure

```markdown
# Intake Run 001

## Run Details
- Date:
- Mode:
- Input Index:
- Scope Version:

## Artifacts Scanned
- Total artifacts:
- New artifacts:
- Changed artifacts:
- Unchanged artifacts:
- Inaccessible artifacts:
- Indexed-only artifacts:
- Reference-only artifacts:

## Sources Processed
| Source | Usage Mode | Action Taken | Notes |

## New Information Identified
- 

## Scope Updates Made
- 

## Registers Updated
- 

## Contradictions Found
- 

## Clarifications Added
- 

## Indexing Assistance Needed
- 

## Risk Notes
- 

## Next Recommended Actions
- 
```

---

# 19. Shared Context Layer

The BA Agent should create and maintain shared project context files for future agents.

Location:

```text
shared-context/
```

## 19.1 Project Profile

```text
shared-context/project-profile.md
```

Purpose:

* Maintain core project information.

## 19.2 Glossary

```text
shared-context/glossary.md
```

Purpose:

* Maintain business terms, acronyms, and client-specific vocabulary.

## 19.3 Stakeholder Map

```text
shared-context/stakeholder-map.md
```

Purpose:

* Maintain stakeholder names, roles, teams, and involvement.

## 19.4 System Landscape

```text
shared-context/system-landscape.md
```

Purpose:

* Maintain known systems, tools, platforms, and integration touchpoints.

## 19.5 Decision Log

```text
shared-context/decision-log.md
```

Purpose:

* Maintain confirmed decisions and their impact.

---

# 20. Future Doc Agent Integration

The Doc Agent will later consume BA Agent outputs.

## 20.1 Future Doc Commands

```text
/doc:proposal
/doc:walkthrough
/doc:srs
/doc:sow
/doc:executive-summary
```

## 20.2 Doc Agent Input Priority

If `ba-output/scope.md` exists, the Doc Agent should use it as the primary source.

If BA outputs do not exist, the Doc Agent may accept direct user input and format it according to the required document style guide.

The Doc Agent should not repeat BA analysis unless explicitly requested.

---

# 21. Future TL Agent Integration

The TL Agent will later consume BA Agent outputs and code repositories.

## 21.1 Future TL Commands

```text
/tl:architecture-review
/tl:code-review
/tl:security-review
/tl:observability-review
/tl:compliance-review
/tl:maturity-score
```

## 21.2 TL Agent Input Sources

The TL Agent should use:

* `ba-output/scope.md`
* `ba-output/integration-register.md`
* `ba-output/data-register.md`
* `shared-context/system-landscape.md`
* Code repository
* Architecture documents
* Deployment documents
* CI/CD configuration
* Observability setup
* Security configuration

## 21.3 TL Agent Purpose

The TL Agent should review whether the codebase, architecture, security, observability, standards, guardrails, and compliance posture align with the actual business scope.

The TL Agent should also generate a monthly project maturity score.

---

# 22. BA Agent Boundaries

## 22.1 BA Agent Owns

The BA Agent owns:

* Discovery artifact intake
* Source classification
* Requirement extraction
* Workflow understanding
* Scope document maintenance
* Business rule extraction
* Example capture
* Assumption tracking
* Clarification tracking
* Contradiction tracking
* Shared project context creation

## 22.2 BA Agent Does Not Own Initially

The BA Agent does not own:

* Final proposal generation
* Polished walkthrough document generation
* SoW generation
* Architecture review
* Code review
* Security vulnerability review
* Observability review
* Compliance scoring
* Project maturity score

These will be handled by future Doc Agent and TL Agent capabilities.

---

# 23. Quality Rules

The BA Agent must follow these rules.

1. Do not fully analyze large artifact folders unless explicitly marked as `Deep Analysis`.
2. Do not pretend to access Google Drive files without MCP or connector access.
3. Every requirement must have a source reference.
4. Every workflow must include trigger, actors, steps, systems, outputs, and exceptions where available.
5. Every business rule must include source and confidence.
6. Every example must map to a workflow or requirement where possible.
7. Every unclear item must become a clarification question.
8. Every conflict must be logged as a contradiction.
9. Do not erase older understanding without recording why.
10. Do not infer global rules from sample files unless supported by primary artifacts.
11. Mark assumptions clearly.
12. Preserve traceability from artifact to scope item.
13. Produce a run summary for every intake.
14. Update shared context for future agents.
15. Continue safe processing even when some artifacts need user guidance.

---

# 24. MVP Requirement

## 24.1 MVP Command

```text
/ba:intake
```

## 24.2 MVP Inputs

```text
intake.index.md
raw-artifacts/
optional Google Drive references
existing ba-output/
```

## 24.3 MVP Outputs

```text
ba-output/scope.md
ba-output/artifact-map.md
ba-output/artifact-ledger.md
ba-output/source-classification.md
ba-output/requirement-register.md
ba-output/workflow-register.md
ba-output/business-rule-register.md
ba-output/example-register.md
ba-output/clarification-log.md
ba-output/change-log.md
ba-output/indexing-assistance-needed.md
shared-context/project-profile.md
shared-context/glossary.md
shared-context/decision-log.md
```

---

# 25. Success Criteria

The MVP is successful if:

1. A user can create a new project folder and add an `intake.index.md`.
2. The BA Agent can scan the artifact sources.
3. The BA Agent can classify artifacts correctly.
4. The BA Agent avoids deep analysis of large reference folders.
5. The BA Agent identifies inaccessible Google Drive sources and asks for MCP/connector access.
6. The BA Agent processes primary discovery documents.
7. The BA Agent creates a living scope document.
8. The BA Agent creates supporting registers.
9. The BA Agent produces an intake run summary.
10. The BA Agent can run again after new artifacts are added and update the scope incrementally.
11. The BA Agent preserves source traceability.
12. The BA Agent creates clarification questions and contradiction logs.
13. The outputs are reusable by future Doc Agent and TL Agent capabilities.

---

# 26. Final Product Vision

Techjays Delivery OS should become the internal AI operating system for how Techjays runs discovery, scope creation, documentation, technical validation, and delivery maturity.

The BA Agent will be the first foundational capability.

The Doc Agent will convert BA outputs into polished client-facing documents.

The TL Agent will validate whether the technical implementation aligns with the business scope and expected delivery standards.

Together, these agents will help Techjays standardize delivery quality, reduce scope gaps, improve proposal quality, and create a reusable AI-first delivery operating model across the organization.
