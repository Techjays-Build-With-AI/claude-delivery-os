## Stage: `scope` (implemented — uses scope-mcp)

### 2. Phase 1 — manifest (single MCP call)

```
mcp__scope-mcp__scope_pull_manifest(
  solution_id=<from project.json>
)
```

Response:
```
{
  "solution_id": "...",
  "ready": N,
  "docs": [
    {
      "path": "ba-output/scope.md",
      "documentId": "doc_abc123",
      "version": 3,
      "tags": ["scope"],
      "size_kb": 81,
      "signed_download_url": "https://storage.googleapis.com/...",
      "ok": true
    },
    { "path": "ba-output/foo.md", "ok": false, "error": "..." },
    ...
  ]
}
```

scope-mcp filters to docs whose `tags` intersect `{"scope", "scope-context"}` (both the UI-visible primary doc AND the background support files) and issues one signed download URL per doc. If `ready == 0`, report "nothing to pull" and stop.

**About `path` in the response:** each doc's `path` is the `FileMeta.originalName` from Mongo — the *relative local path inside the delivery-os container* (e.g. `ba-output/scope.md`, `shared-context/glossary.md`, `context/features/feature-index.md`). It preserves the on-disk nesting from the pusher's workspace, so the puller's local layout ends up byte-identical (same subfolders, same file names). The signed download URL points at the flattened GCS object (`project-context/<sol>/scope/<ts>-<flattened>`), but writers don't need to think about that — always write bytes to `<project_root>/<path>`.

### 3. Phase 2 — skip unchanged, then download the rest (via Bash — never `Read`)

**Hard rule: do NOT use the `Read` tool to open any of the local scope files.** The whole point of this design is that Claude never handles file bytes. Compute the local-file hashes via Bash (`sha256sum`) so the bytes stay on disk.

`sync-state.json` is a tiny metadata file — safe to read with `Read`. Read `<workspace_root>/.jetrix/cache/sync-state.json` (create empty `{}` if missing).

Then hash the on-disk copies via ONE Bash call:

```bash
#!/usr/bin/env bash
set -e
PROJECT_ROOT="<absolute project_root>"
cd "$PROJECT_ROOT"
for f in <paths from manifest>; do
  if [[ -f "$f" ]]; then
    hash=$(sha256sum "$f" | cut -d' ' -f1)
    echo "$f|$hash"
  else
    echo "$f|MISSING"
  fi
done
```

For each manifest doc where `ok:true`:

- If the manifest returns `contentHash` (server-side hash sidecar tag) → compare `local_sha256[:40] == manifest.contentHash`. Match → **skip** (bytes on disk match bytes on server). Mismatch → download regardless of what sync-state says (someone else pushed a newer version).
- If the manifest has NO `contentHash` (older push predates the tag) → fall back to comparing local hash against `sync-state[doc.path].contentHash`. Match → skip. Mismatch → download.
- Otherwise mark as **needs download**.

Preferring manifest.contentHash over sync-state.contentHash is what catches teammate-pushed drift — a fresh clone or a workspace whose sync-state got out of date will still notice a newer server version and pull it.

Generate ONE shell script that curl-GETs every needs-download doc from its `signed_download_url` and writes to `<project_root>/<doc.path>` — where `<doc.path>` is the relative local path from the manifest response. `mkdir -p` on the *directory* portion of that path reconstructs `ba-output/`, `shared-context/`, `context/features/`, etc. from scratch on a fresh clone, so a teammate who just cloned an empty repo ends up with the same folder tree as the pusher had.

```bash
#!/usr/bin/env bash
set +e
RESULT_LOG=$(mktemp)

download_one() {
  local abs_path="$1" signed_url="$2" rel_path="$3"
  mkdir -p "$(dirname "$abs_path")"
  local http_code
  http_code=$(curl -sS -o "$abs_path" -w "%{http_code}" "$signed_url")
  if [[ "$http_code" == "200" ]]; then
    echo "OK  $rel_path" >> "$RESULT_LOG"
  else
    echo "FAIL $rel_path (HTTP $http_code)" >> "$RESULT_LOG"
    rm -f "$abs_path"  # Don't leave a partial/error-body file behind
  fi
}

download_one "<project_root>/ba-output/scope.md"          "<signed_download_url>" "ba-output/scope.md"
download_one "<project_root>/ba-output/data-register.md"  "<signed_download_url>" "ba-output/data-register.md"
# ...one line per needs-download doc

cat "$RESULT_LOG"
rm -f "$RESULT_LOG"
```

- Bytes flow GCS → curl → local disk. Never through Python/scope-mcp/Claude.
- `mkdir -p` handles first-time creation of `ba-output/`, `shared-context/`, `context/features/`.
- Bad-response bodies get deleted so a subsequent pull retries cleanly instead of thinking the file is fine.

Parse `RESULT_LOG` — lines starting `OK ` are successful writes; `FAIL ` are failures.

### 4. Update sync-state.json

Run ONE more Bash call to hash the newly-written files (same `sha256sum` loop as step 3, over the successfully-downloaded paths this time). For every successfully-written file, update its entry with the FRESH contentHash:

```json
{
  "ba-output/scope.md": {
    "documentId": "<from manifest>",
    "version": <from manifest>,
    "contentHash": "sha256:<hash of bytes just written>",
    "lastPulled": "<current ISO timestamp>"
  }
}
```

For skipped-unchanged docs, just bump `lastPulled`.

Do NOT touch sync-state for docs that failed download — next pull retries.

### 5. Report

```
✓ Pulled 12 scope-stage docs (Solution: LarkIQ).

  ba-output/scope.md                       ← doc_abc123 (v3, updated)
  ba-output/data-register.md               ← doc_def456 (v1, first pull)
  ba-output/workflow-register.md           ← unchanged (local matches remote)
  shared-context/glossary.md               ← doc_ghi789 (v2, updated)
  context/features/feature-index.md        ← doc_jkl012 (v1, first pull)
  ...

Updated:  8    Unchanged:  4    Failed:  0
```

Failed pulls: list each with its error message; sync-state.json NOT updated for those.

### 5. Phase 3 — feature-folder materialization (single MCP call to task-mcp)

`/jetrix:pull scope` is COMBINED — after scope-mcp finishes writing docs, invoke task-mcp to reconstruct `context/features/<slug>/*.md` folders from MC Tasks. This is what makes a fresh clone look byte-identical to the pusher's workspace.

```
mcp__task-mcp__feature_pull_bundle(solution_id = <from project.json>)
```

Response:
```
{
  "solution_id": "...",
  "pulled": N,
  "features": [
    {
      "task_object_id": "...", "task_number": 42,
      "feature_id": "FEAT-AUTH-001", "slug": "user-auth",
      "initiative": "user-portal",
      "list_id": "<24-hex>", "list_name": "Supplier Management",   // MC List the Task lives in
      "title": "User Authentication",
      "description": "<summary + Users + workflow narrative + mermaid, tab-shape>",
      "business_rules": "<BR table, tab-shape>",
      "acceptance_criteria": "<AC content, tab-shape>",
      "nfrs": "<NFR table by area, tab-shape>",
      "test_scenarios": "<Positive / Negative / Edge tables, tab-shape>",
      "assumptions": "<Depends on + Assumptions + Open questions, three sub-sections>",
      "scope": "...", "dependencies": "...", "open_questions": "...",       // retained on the record; not tab-facing
      "technical_flow": "...", "journeys": "...",                            // Execution Flow tab
      "implementation_details": "...",                                       // present only if TL has pushed
      "status": "readyForDev", "priority": "..."
    },
    ...
  ]
}
```

**Fields carrying tab-shape content** — `description`, `business_rules`, `acceptance_criteria`, `nfrs`, `test_scenarios`, `assumptions`. These are already stripped of file paths / framework names / provenance by `/jetrix:push feature`. When pull writes them back to local files, it writes them **verbatim** — no re-transformation, no reshaping. Local files after pull are the tab-shape versions.

**Fields carrying record-only content** — `scope`, `dependencies`, `open_questions`. Preserved on the MC record for traceability but not surfaced in any tab; pull writes them back to their local files for anyone reconstructing the feature folder.

### 6. Compose feature files locally (canonical section order)

For each feature in the response, write files under `<project_root>/context/features/<slug>/` (use `mkdir -p` first). Pull is symmetric to push: write each field to its local file verbatim. **No reshaping, no splitting, no restructuring** — the pushed content is already tab-shape.

**Seven files reconstructed on pull** (one per wire field):

| Wire field | Local file | Body written |
|---|---|---|
| `description` | `feature.md` | Frontmatter + H1 (`# <title>`) + `<description>` verbatim. The Description tab's merged Objective + In / Out Scope + Workflow + mermaid all sit inside this one file. |
| `business_rules` | `business-rules.md` | Frontmatter + `<business_rules>` verbatim. Skip file entirely if the field is empty. |
| `acceptance_criteria` | `acceptance-criteria.md` | Frontmatter + `<acceptance_criteria>` verbatim. Skip if empty. |
| `nfrs` | `nfrs.md` | Frontmatter + `<nfrs>` verbatim. Skip if empty. |
| `test_scenarios` | `test-scenarios.md` | Frontmatter + `<test_scenarios>` verbatim. Skip if empty. |
| `assumptions` | `dependencies.md` | Frontmatter + `<assumptions>` verbatim. The Depends on / Assumptions / Open questions merged shape lands here as-is. |
| `implementation_details` | `tl-plan.md` | Frontmatter + `<implementation_details>` verbatim. Skip if empty (means TL hasn't run `/jetrix:push implementation` yet). |

**Frontmatter written on each file:**

```yaml
---
feature_id: <feature_id>              # from wire task.metadata.externalId
initiative: <initiative>              # from wire task.metadata.externalInitiative
slug: <slug>                          # from wire task.metadata.externalSlug
list_name: <list_name>                # from wire task.list_name — omit key if empty; preserves List routing on re-push
jetrix_task_id: <task_number>
jetrix_task_object_id: <task_object_id>
status: <status>                      # from wire task.status
depends_on_features: [...]            # from wire task.metadata.dependsOnFeatureIds
use_cases: [...]                      # from wire task.metadata.useCases
generated_at: <today>
---
```

**`list_name:` write rule.** Only write the key to `feature.md` frontmatter (never to the other six files); other files derive their List placement from the sibling `feature.md`. Omit the key entirely when the wire `list_name` is empty (task-mcp couldn't resolve the List name) so subsequent push falls back to the mapped_scope-derived default — never write `list_name: ""` which would force an empty-named List.

**Files NOT written on pull** — these are local-only in the BA authoring flow, never round-tripped through Jetrix:

- **`workflow.md`** — its content is inside `feature.md`'s Description-tab body. A fresh teammate does not need it as a separate file; the original author's local copy is left untouched if it exists.
- **`open-questions.md`** — its content is inside `dependencies.md`'s Dependencies-tab body (merged). Same reasoning.
- **`implementation-plan.md`** — local BA scratchpad, never pushed. Not recreated.
- **`status.md`** — local operational tracker; task status is on the MC Task itself. Not recreated.

**When a local-only file already exists** (author's machine), pull **does not touch it**. Fresh teammates simply don't have these four files — they can regenerate the rich author view by running `/ba:features` locally against the same scope.

Update `.jetrix/cache/sync-state.json` `tasks/<feature_id>` entries with `taskNumber`, `taskObjectId`, `slug`, `contentHash` (sha256 of the newly-written folder), `lastPulled`.

### 7. Report

```
Pulled:  15 scope docs + 14 features
        (10 features created locally, 4 unchanged)
```

## Prompts count

Three total per combined pull:
1. `mcp__scope-mcp__scope_pull_manifest`
2. `Bash <download script>`
3. `mcp__task-mcp__feature_pull_bundle`

