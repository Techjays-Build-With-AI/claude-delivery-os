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

### 3. Phase 2 — skip unchanged + parallel download + apply (one Bash call)

**One Bash tool call**: writes a curl config + a manifest sidecar as heredocs, runs `curl --parallel` (HTTP/2 multiplexed to GCS — same mechanism the browser uses), then invokes the plugin's apply script to atomically move successful downloads into place and update sync-state.

**Skip-unchanged decision is made in Claude, not in Bash.** Before emitting the script, iterate the manifest docs where `ok:true`:

- If `manifest.contentHash` matches `sync-state[doc.path].contentHash` (both are server-authoritative — we recorded manifest.contentHash on the last successful pull) → **skip**. Don't add to the curl config.
- Otherwise → **needs download**. Add to curl config + manifest sidecar.

No local-file hashing needed. `sync-state.json` is a tiny JSON file — safe to `Read` for the comparison. Manifest.contentHash beats sync-state on any drift (someone else pushed a newer version → their hash differs from ours → we download).

If everything skips (all hashes match), the download step is a no-op and this whole section costs one 200-line Bash script that runs in <100ms.

```bash
#!/usr/bin/env bash
set +e
WORKSPACE_ROOT="<absolute workspace_root>"
PROJECT_ROOT="<absolute project_root>"

STAGING=$(mktemp -d)
CFG=$(mktemp)
LOG=$(mktemp)
META=$(mktemp)

# --- Curl config: one url+output pair per needs-download doc ---
# The plugin fills these in from manifest response (skipping docs where
# manifest.contentHash matches sync-state.contentHash).
cat > "$CFG" <<'CURLCFG'
url = "<signed_download_url_1>"
output = "<STAGING_absolute>/ba-output/scope.md"
url = "<signed_download_url_2>"
output = "<STAGING_absolute>/ba-output/data-register.md"
# ...one url+output pair per needs-download doc
CURLCFG

# --- Manifest sidecar: per-path metadata the apply script writes to sync-state ---
cat > "$META" <<'METAEOF'
{
  "ba-output/scope.md":         {"documentId": "doc_abc123", "version": 3, "contentHash": "<40hex>"},
  "ba-output/data-register.md": {"documentId": "doc_def456", "version": 1, "contentHash": "<40hex>"}
}
METAEOF

# --- Parallel HTTP/2-multiplexed download (single curl process, 8 concurrent) ---
# --create-dirs handles nested staging paths (ba-output/, shared-context/, context/, context/features/).
# --write-out logs "<staged_path>|<http_code>" per completed transfer to $LOG.
curl --parallel --parallel-max 8 --create-dirs \
     -sS --show-error \
     --write-out "%{filename_effective}|%{http_code}\n" \
     --config "$CFG" > "$LOG" 2>&1

# --- Apply: atomic move + sync-state update via the plugin's script ---
# On any non-200 the staged file stays in $STAGING (dropped by rm below) so the
# local original — if any — stays untouched. No more "curl -o truncates local
# then rm deletes it" data-loss bug.
python "$CLAUDE_PLUGIN_ROOT/scripts/apply-scope-manifest.py" \
  --staging      "$STAGING" \
  --project-root "$PROJECT_ROOT" \
  --sync-state   "$WORKSPACE_ROOT/.jetrix/cache/sync-state.json" \
  --curl-log     "$LOG" \
  --manifest     "$META"

rm -rf "$STAGING" "$CFG" "$LOG" "$META"
```

Why parallel: 15 files sequential @ ~500ms handshake each ≈ 8s. Parallel with HTTP/2 multiplexing over a single TCP+TLS connection to `storage.googleapis.com` ≈ 0.5–1s. Same mechanism the Documents-tab UI uses.

Why staging + atomic move: solves the earlier data-loss bug — `curl -o "$abs_path"` truncates the local file *before* seeing the HTTP status, so a 404 destroyed 5 files in one pull. Downloading to a staging dir and only `mv`ing on 200 means failed transfers leave the local original untouched.

### 4. Report

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

### 6. Compose feature files locally — invoke the materializer script

**Do NOT iterate features with per-file `Write` calls.** For 20 features that's ~140 `Write` tool round-trips ≈ 5-10 minutes wall-clock. Instead, dump the bundle JSON to disk (one Bash heredoc) then run the plugin's script (one Bash → Python). Two tool calls, constant regardless of feature count.

```bash
BUNDLE="<workspace_root>/.jetrix/cache/.pull-features.json"
mkdir -p "$(dirname "$BUNDLE")"

# --- Save the feature_pull_bundle JSON response to disk ---
cat > "$BUNDLE" <<'JETRIX_BUNDLE_EOF'
<paste the entire feature_pull_bundle JSON response here, verbatim>
JETRIX_BUNDLE_EOF

# --- Materialize every feature + update sync-state ---
python "$CLAUDE_PLUGIN_ROOT/scripts/materialize-features.py" \
  --bundle       "$BUNDLE" \
  --project-root "<absolute project_root>" \
  --sync-state   "<workspace_root>/.jetrix/cache/sync-state.json"

rm -f "$BUNDLE"
```

`'JETRIX_BUNDLE_EOF'` (quoted heredoc) keeps `$`, backticks, and backslashes in the JSON literal — no shell expansion inside the JSON body.

**Contract — what the materializer writes per feature** (mechanism moved to the script; contract preserved). Seven files reconstructed on pull, one per wire field:

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

**When a local-only file already exists** (author's machine), pull **does not touch it** — the materializer only writes the seven files above, so `workflow.md`, `open-questions.md`, `implementation-plan.md`, `status.md` survive untouched. Fresh teammates simply don't have these four files — they can regenerate the rich author view by running `/ba:features` locally against the same scope.

Sync-state is updated inside the materializer script — `.jetrix/cache/sync-state.json` gets one `tasks/<feature_id>` entry per feature with `taskNumber`, `taskObjectId`, `slug`, `contentHash` (sha256 of the concatenated file contents), `lastPulled`. Merge-safe: existing keys for other stages (scope docs, context units) are preserved.

### 7. Report

```
Pulled:  15 scope docs + 14 features
        (10 features created locally, 4 unchanged)
```

## Prompts count

Fixed cost per combined pull, regardless of doc or feature count:
1. `mcp__scope-mcp__scope_pull_manifest` — one signed URL per doc, all Solution-scoped tags (scope + scope-context + connection-map + solution-context)
2. `Bash <parallel curl + apply script>` — HTTP/2-multiplexed download + atomic staging + sync-state update
3. `mcp__task-mcp__feature_pull_bundle` — feature JSON bundle
4. `Bash <write bundle to disk>` — heredoc dump
5. `Bash <materialize-features.py>` — feature folder writes + sync-state update

Five tool calls total. Never scales with file or feature count — a 5-feature/5-doc pull and a 50-feature/50-doc pull both cost five prompts.

