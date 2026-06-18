---
doc_type: intake-index
schema_version: 1.0
produced_by: human
status: Draft
generated_at: YYYY-MM-DD
---

# Project Intake Index

> Declare every source the BA Agent should consider. For each source set a **Usage Mode** (Deep Analysis / Reference Only / Sample and Summarize / Index Only / Future Agent Input). The agent classifies anything left unmarked conservatively.

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

### Source 3: Historical Reference Archive (example)
- Type: Local Folder
- Path: ./raw-artifacts/sample-data
- Content: Historical files shared by the client for reference
- Usage Mode: Reference Only
- Authority: Medium
- Priority: Low
- Intake Rule: Do not fully analyze during intake. Create an index only.

### Source 4: Google Drive Reference Folder (example)
- Type: Google Drive
- Link: https://drive.google.com/...
- Content: Client-shared reference documents, screenshots, and sample files
- Usage Mode: Reference Only
- Authority: Medium
- Priority: Medium
- Access Required: Google Drive MCP / Connector
- Fallback: Export locally to ./raw-artifacts/client-reference-docs

### Source 5: Existing Application Repository (example)
- Type: Code Repository
- Path: ../client-application-repo
- Content: Existing application codebase
- Usage Mode: Future Agent Input
- Future Agent: TL Agent
- Intake Rule: Do not analyze during BA intake unless explicitly requested.

## Processing Rules
- Respect explicit Usage Mode and Intake Rule per source.
- Apply default safeguards to large folders (see ba-classification).

## Output Location
- BA outputs: ./ba-output/
- Shared context: ./shared-context/
