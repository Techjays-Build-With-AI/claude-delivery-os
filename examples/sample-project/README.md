# Sample Project — Acme AI Invoice Processing

A ready-to-run **Delivery OS workspace** for testing the BA agent. It's already initialized in the dynamic-intake model.

```text
sample-project/
├── README.md             ← this file
├── intake.index.md       ← source registry (4 sources pre-registered, referencing ./source-files/)
└── source-files/         ← stands in for the client's ORIGINAL material (referenced, never copied)
    ├── client-requirements/invoice-requirements.md
    ├── meeting-transcripts/2026-06-12-kickoff.md
    └── sample-data/README.txt        (a "reference only" archive stand-in)
```

`artifacts/`, `shared-context/`, and `ba-output/` are intentionally absent — `/ba:scope` creates them.

## Run it
Open this folder as the working directory, then:
```text
/ba:scope
```
The agent summarizes the sources into `artifacts/`, then builds `ba-output/scope.md` (module-centric, conforming to the Techjays Scope Document Template) plus the registers.

The sources are seeded with deliberate traps — a £10k-vs-£15k approval-threshold conflict (should become a contradiction/clarification), an inaccessible Google Drive source (should be flagged `Access Required`, not faked), and a reference-only archive (should be indexed, not deep-analyzed). See [../../TESTING.md](../../TESTING.md) for the full checklist.

## Reset
```powershell
Remove-Item -Recurse -Force .\artifacts,.\shared-context,.\ba-output -ErrorAction SilentlyContinue
```
(`intake.index.md` and `source-files/` are the fixture inputs — leave them.)
