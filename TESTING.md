# Testing Techjays Delivery OS locally

You can test the plugin from this repo **without publishing it** anywhere. Work top-down: validate the structure, load it locally, confirm it registered, then run it end to end against the bundled sample project.

## 0. Pre-flight — validate structure

All JSON and frontmatter should be well-formed before loading.

```powershell
# JSON lint (every manifest + marketplace)
Get-ChildItem -Recurse -Filter *.json | Where-Object { $_.FullName -notmatch '\\.git\\' } |
  ForEach-Object { try { Get-Content $_.FullName -Raw | ConvertFrom-Json | Out-Null; "OK  $($_.Name)" } catch { "BAD $($_.Name): $($_.Exception.Message)" } }
```

If your Claude Code build ships a validator, also run it (name varies by version):

```bash
claude plugin validate D:\Projects\Tools\claude-delivery-os
```

## 1. Load the plugin locally

Inside a Claude Code session, add this repo as a marketplace by path, then install:

```text
/plugin marketplace add D:\Projects\Tools\claude-delivery-os
/plugin install delivery-os@techjays-delivery-os
/plugin install ba@techjays-delivery-os
```

(`techjays-delivery-os` is the marketplace `name` from `.claude-plugin/marketplace.json`.)

## 2. Confirm it registered

```text
/plugin        →  Installed tab shows delivery-os + ba; check the Errors tab is empty
/help          →  /delivery-os:init and /ba:scope appear
/agents        →  ba-agent is listed
```

## 3. Functional test — run it against the sample project

A ready-to-run fixture lives at `examples/sample-project/` — a workspace already initialized in the dynamic-intake model, with four sources pre-registered in `intake.index.md` (referencing files under `source-files/`). Open that folder as the working directory, then:

```text
/ba:scope
```

> To test the **conversational ingest** instead, run `/delivery-os:init demo` in an empty folder and then
> `/ba:scope add "requirements in <path>, transcripts in <path>, archive in <path> for reference only"`.
> To test **scaffolding**, run `/delivery-os:init my-test` and confirm it creates ONE container folder (README + intake.index + artifacts/ + shared-context/ + ba-output/ + final/) — nothing dumped in the root, no `raw-artifacts/` taxonomy.

### What a correct run should produce

- `artifacts/<category>/…summary.md` files generated (e.g. `requirements/`, `meeting-transcripts/`) — and **no copies of the originals** anywhere (source-files/ untouched).
- `intake.index.md` rows updated with summary paths, hashes, and `Processed` status.
- `ba-output/scope.md` exists and **conforms to the Techjays Scope Document Template**:
  - Cover block → §1 Scope Statement → §2 Module Breakdown → §3 per-module blocks → §4–§8.
  - Modules decomposed (expect ~ Intake, Extraction/Processing, Validation, Approval, Reporting).
  - §3.x.3 requirement tables use `Resp.` = AI/DET/HUM, `Pri.` = M/S/C/W, and IDs like `INTK-AI-02`.
- `ba-output/requirement-register.md`, `business-rule-register.md`, etc. populated with source citations.
- The **duplicate-payment** pain point and the **£10k vs £15k approval threshold** appear as a **contradiction** (`CON-…`) and/or **clarification** (`CLR-…`) — not silently resolved.
- The **Google Drive** source stays `Access Required` in `indexing-assistance-needed.md` — **not** fabricated.
- The **invoice-archive** source is `Reference Only` — indexed, not deep-analyzed (no per-file summaries).
- `ba-output/intake-runs/run-001.md` summarizes the run; `shared-context/` files created.

### Targeted checks (map to the spec's success criteria)

| Test | How | Pass = |
|------|-----|--------|
| Reference-only | After a run, inspect `source-files/` | unchanged — nothing moved, copied, or deleted |
| Add a source | `/ba:scope add "a note at .\source-files\extra-note.md"` (create that file first) | new SRC row + summary; existing sources untouched |
| Incremental | edit one source, `/ba:scope mode=incremental` | only the changed source re-summarized; scope updated, not rebuilt |
| Dry run | `/ba:scope mode=dry-run` | reports intended changes, writes nothing |
| Classify only | `/ba:scope mode=classify-only` | registry rows classified; no summaries, no analysis |
| Traceability | open `requirement-register.md` | every row cites `[SRC-… › <original location>]` |

## 4. Iterate after edits

After editing a command/agent/skill/template, pick up changes by reloading plugins if your build supports it (`/reload-plugins`), or restart the session and re-run `/ba:scope`. Skills generally refresh within the session; agent/manifest changes may need a reload/restart.

## 5. Clean up between runs

To re-test from scratch, delete the generated outputs in the sample project:

```powershell
$p = "D:\Projects\Tools\claude-delivery-os\examples\sample-project"
Remove-Item -Recurse -Force "$p\ba-output","$p\shared-context","$p\artifacts" -ErrorAction SilentlyContinue
```

(The `intake.index.md` and `source-files/` are the fixture inputs — leave them. You may also want to reset the `Summary`/`Hash`/`Status` columns in `intake.index.md` to `_pending_`/`New`.)
