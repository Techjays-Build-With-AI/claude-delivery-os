---
doc_type: intake-index
schema_version: 1.0
produced_by: ba
status: Draft
generated_at: 2026-06-18
---

# Project Intake Index

> Pre-registered sample workspace (new dynamic-intake model). The sources below are **referenced in place** under `./source-files/` — running `/ba:intake` will summarize them into `artifacts/` and build the scope. Originals are never copied or moved.
>
> To test the conversational flow instead, start a fresh workspace with `/delivery-os:init` and run:
> `/ba:intake add "requirements in ./source-files/client-requirements, transcripts in ./source-files/meeting-transcripts, invoice archive in ./source-files/sample-data for reference only"`

## Project
- Client: Acme Components Ltd
- Project Name: AI Invoice Processing
- Business Domain: Accounts Payable
- Project Stage: Discovery
- Discovery Owner: Test User
- Discovery Start Date: 2026-06-18

## Sources

| SRC | Description | Original Location | Type | Category | Usage Mode | Summary | Hash | Status |
|-----|-------------|-------------------|------|----------|------------|---------|------|--------|
| SRC-001 | Client requirement notes | ./source-files/client-requirements | Local Folder | requirements | Deep Analysis | _pending_ | _pending_ | New |
| SRC-002 | Discovery kickoff transcript | ./source-files/meeting-transcripts | Local Folder | meeting-transcripts | Deep Analysis | _pending_ | _pending_ | New |
| SRC-003 | Historical invoice archive (reference) | ./source-files/sample-data | Local Folder | invoice-archive | Reference Only | _pending_ | _pending_ | New |
| SRC-004 | Client Drive reference folder (no access — tests the access path) | https://drive.google.com/drive/folders/EXAMPLE-NO-ACCESS | Google Drive | drive-reference | Reference Only | _n/a_ | _n/a_ | Access Required |
