## Stage: `scope` (implemented — uses scope-mcp)

### 2. Walk local files — via Bash ONLY, never `Read`

**Hard rule: do NOT use the `Read` tool to open any of the scope files.** Reading an 81KB scope.md into Claude's context defeats the entire direct-to-GCS design and will slow the push to a crawl. The point of the three-phase flow is that file bytes stay out of Claude — this step is where that discipline starts.

Use ONE `Bash` tool call to walk, size, and hash every file in a single shot. Emit one `path|size_kb|content_hash` line per file so the plugin can parse it into the manifest.

Script skeleton:

```bash
#!/usr/bin/env bash
set -e
PROJECT_ROOT="<absolute project_root from step 0>"
cd "$PROJECT_ROOT"

# Every scope-stage file the plugin will consider.
CANDIDATES=(
  ba-output/scope.md
  ba-output/data-register.md
  ba-output/workflow-register.md
  ba-output/business-rule-register.md
  ba-output/use-case-register.md
  ba-output/integration-register.md
  ba-output/example-register.md
  ba-output/assumption-register.md
  ba-output/requirement-register.md
  ba-output/clarification-log.md
  shared-context/project-profile.md
  shared-context/glossary.md
  shared-context/stakeholder-map.md
  shared-context/system-landscape.md
  shared-context/decision-log.md
  context/features/feature-index.md
)

for f in "${CANDIDATES[@]}"; do
  [[ -f "$f" ]] || continue
  size_bytes=$(wc -c < "$f")
  size_kb=$(( (size_bytes + 1023) / 1024 ))
  hash=$(sha256sum "$f" | cut -d' ' -f1)
  echo "$f|$size_kb|$hash"
done
```

Parse the output into a list of `{ path, size_kb, content_hash }` entries. If `<filename>` was supplied, filter to just that entry.

Skip:
- Per-feature folders under `context/features/<slug>/` — they become MC Tasks via `/jetrix:push tasks`, not scope docs.
- `artifacts/`, `intake-runs/` — local-only (Tier 3).

Missing paths are already skipped by the `[[ -f "$f" ]]` guard — no error if `context/features/feature-index.md` doesn't exist yet.

**Do not `Read` any of these files anywhere in this command. The bytes exist only on disk; the plugin only ever holds their metadata (path, size_kb, content_hash).**

### 3. Tag mapping + version handling (sync-state.json — via Bash again)

**Tag scheme — two levels only:**

- **`["scope"]`** → the primary scope document. Applied to `ba-output/scope.md` ONLY. This is the tag Mission Control's Documents UI filters by to surface the user-facing scope doc.
- **`["scope-context"]`** → every other scope-stage file. Registers, shared-context, feature-index. Uploaded so agents and `/jetrix:pull scope` can retrieve them, but **not surfaced in the Documents UI** — they're background context material, not primary deliverables.

Per-file mapping:

| Local path | Tags to send |
|---|---|
| `ba-output/scope.md` | `["scope"]` |
| `ba-output/data-register.md` | `["scope-context"]` |
| `ba-output/workflow-register.md` | `["scope-context"]` |
| `ba-output/business-rule-register.md` | `["scope-context"]` |
| `ba-output/use-case-register.md` | `["scope-context"]` |
| `ba-output/integration-register.md` | `["scope-context"]` |
| `ba-output/example-register.md` | `["scope-context"]` |
| `ba-output/assumption-register.md` | `["scope-context"]` |
| `ba-output/requirement-register.md` | `["scope-context"]` |
| `ba-output/clarification-log.md` | `["scope-context"]` |
| `shared-context/project-profile.md` | `["scope-context"]` |
| `shared-context/glossary.md` | `["scope-context"]` |
| `shared-context/stakeholder-map.md` | `["scope-context"]` |
| `shared-context/system-landscape.md` | `["scope-context"]` |
| `shared-context/decision-log.md` | `["scope-context"]` |
| `context/features/feature-index.md` | `["scope-context"]` |

scope-mcp does **not** auto-add any identity tag — the plugin owns the tag semantics. Every future stage (task-mcp, deliverable-mcp) mirrors this two-level pattern with its own primary/support pair (`tasks`/`tasks-support`, etc.).

> **sync-state contract (applies to every stage below — read carefully).** `sync-state.json` is the **single shared file** for ALL stages — scope, feature, implementation. Every write is a MERGE, never a REPLACE. The correct pattern in every stage's write-back step is:
>
> 1. **Read** `<workspace_root>/.jetrix/cache/sync-state.json` (treat missing/empty as `{}`).
> 2. **Merge** your new/updated keys into that object (do NOT drop any existing keys).
> 3. **Write** the merged object back to the same path.
>
> Never write a file that only contains keys you just produced. Every stage's keys coexist in the same file — scope keys look like `ba-output/scope.md`, feature keys look like `tasks/FEAT-...`, context keys look like `context/frontend/page-index.md`, etc. If you overwrite this file with only your stage's keys, other stages' entries are lost — the next push of those stages will look like a fresh upload and create duplicate FileMeta rows in Jetrix.

`sync-state.json` is a tiny JSON file (metadata only, never bytes) — safe to read with the `Read` tool since its size is bounded by the number of scope files. Read `<workspace_root>/.jetrix/cache/sync-state.json` (create empty `{}` if missing). Each entry looks like:

```json
{
  "ba-output/scope.md": {
    "documentId": "doc_abc123",
    "version": 3,
    "contentHash": "sha256:...",
    "lastPushed": "2026-07-22T..."
  }
}
```

For each collected file:
- If `sync-state[path].contentHash === current contentHash` → **skip** (unchanged).
- Otherwise mark as **needs push**. If an entry exists, carry:
  - `documentId` → send as `document_id` on the payload (scope-mcp forwards it to notify-upload for the version chain).
  - `version` → send as `expected_version` on the payload. scope-mcp compares to the server's current version; on mismatch (someone else pushed newer), the doc is rejected with `conflict: 'version_mismatch'` so we can prompt the user to `/jetrix:pull scope` before overwriting. Sending both keys is the "safe update" path.

### 4. Phase 1 — prepare (single MCP call)

For every file that needs push, invoke ONCE:

```
mcp__scope-mcp__scope_prepare_push(
  solution_id=<from project.json>,
  docs=[
    { path: "ba-output/scope.md",         mime_type: "text/markdown" },
    { path: "ba-output/data-register.md", mime_type: "text/markdown" },
    ...
  ]
)
```

Response:
```
{
  "solution_id": "...",
  "prepared": N,
  "docs": [
    { "path": "ba-output/scope.md", "signed_upload_url": "https://...", "gcs_path": "gs://.../project-context/<sol>/scope/<ts>-ba-output__scope.md", "mime_type": "text/markdown", "ok": true },
    ...
  ]
}
```

**Path contract:** `path` you send in and receive back is always the *relative local path inside the delivery-os container* (e.g. `ba-output/scope.md`). scope-mcp stores it verbatim on `FileMeta.originalName`, and pull replays it back so a puller can reconstruct the exact folder tree via `mkdir -p $(dirname path)`. The `gcs_path` is a flattened storage detail (`project-context/<sol>/scope/<ts>-<flattened>`); only the upload script in step 5 needs it.

Skip any doc whose `ok:false` from this response and record the error to report later.

### 5. Phase 2 — upload bytes directly to GCS (single Bash call)

Generate ONE shell script that curl-PUTs every prepared file from local disk to its signed URL. **This is what removes bytes from Claude's context** — the bytes go from disk to `storage.googleapis.com` directly, not through the model.

Script skeleton (write to a temp file to keep the Bash tool call clean — never inline dozens of curl commands in a single command string):

```bash
#!/usr/bin/env bash
set +e
RESULT_LOG=$(mktemp)

upload_one() {
  local abs_path="$1" signed_url="$2" mime="$3" rel_path="$4"
  local http_code
  http_code=$(curl -sS -o /dev/null -w "%{http_code}" \
    -X PUT -T "$abs_path" \
    -H "Content-Type: $mime" \
    "$signed_url")
  if [[ "$http_code" == "200" ]]; then
    echo "OK  $rel_path" >> "$RESULT_LOG"
  else
    echo "FAIL $rel_path (HTTP $http_code)" >> "$RESULT_LOG"
  fi
}

# One line per doc that came back ok:true from scope_prepare_push
upload_one "<project_root>/ba-output/scope.md"          "<signed_upload_url>" "text/markdown" "ba-output/scope.md"
upload_one "<project_root>/ba-output/data-register.md"  "<signed_upload_url>" "text/markdown" "ba-output/data-register.md"
# ...one line per file

cat "$RESULT_LOG"
rm -f "$RESULT_LOG"
```

- Use quotes around every path/url (Windows paths contain spaces; signed URLs contain `&` `?` `=`).
- Use `curl -sS -T` (PUT via file). The bytes flow OS → curl → HTTPS → GCS, never through Python/scope-mcp/Claude.
- Uploads can run **sequentially** — GCS is fast; parallelization here is a marginal win and complicates error handling. Only add `&` + `wait` if a specific push routinely exceeds ~30 s.

Parse `RESULT_LOG` output — lines starting `OK ` are successful uploads; `FAIL ` are failures. Only successful uploads move to Phase 3.

### 6. Phase 3 — finalize (single MCP call)

For every doc that succeeded in Phase 2, invoke ONCE:

```
mcp__scope-mcp__scope_finalize_push(
  solution_id=<from project.json>,
  docs=[
    {
      path: "ba-output/scope.md",
      gcs_path: "<from prepare response>",
      size_kb: 81,
      mime_type: "text/markdown",
      tags: ["ba","scope"],
      document_id: "<from sync-state.json, if any>",
      expected_version: <sync-state.version, if any>, // enables optimistic locking
      content_hash: "<sha256 hex from step 2>" // stored as `ch:` tag; echoed on pull for skip-unchanged
    },
    ...
  ]
)
```

Response:
```
{
  "solution_id": "...",
  "finalized": N,
  "docs": [
    { "path": "ba-output/scope.md", "documentId": "doc_abc123", "version": 3, "ok": true },
    ...
  ]
}
```

### 7. Update sync-state.json

**MERGE, do not replace.** Read `<workspace_root>/.jetrix/cache/sync-state.json` first (may contain `tasks/*`, `context/*`, and other stages' entries). For every doc that returned `ok:true` from Phase 3, **set** its per-path key in the object (leave every other key untouched), then write the merged object back:

```json
{
  "ba-output/scope.md": {
    "documentId": "<from finalize response>",
    "version": <from finalize response>,
    "contentHash": "<sha256 computed in step 2>",
    "lastPushed": "<current ISO timestamp>"
  }
}
```

Do NOT update sync-state for docs that failed in either Phase 2 or Phase 3 — next push retries them.

### 8. Report

```
✓ Pushed 12 scope-stage docs (Solution: LarkIQ).

  ba-output/scope.md                       → doc_abc123 (v3, uploaded)
  ba-output/data-register.md               → doc_def456 (v1, first push)
  ba-output/workflow-register.md           → skipped (unchanged)
  shared-context/glossary.md               → doc_ghi789 (v2, uploaded)
  context/features/feature-index.md        → doc_jkl012 (v1, first push)
  ...

Uploaded:  8    Skipped (unchanged):  4    Failed:  0

View in Jetrix UI: <solution-url> → Documents tab → filter tag `scope` (the primary scope.md). Background files (tag `scope-context`) exist for sync/agent use and are hidden from the primary UI view.
```

Failed uploads: list each with its phase (prepare / upload / finalize) and the error message.

## Prompts count

For a typical push (any file count):

| Prompt | Source | Once ever? |
|---|---|---|
| `mcp__scope-mcp__scope_prepare_push` | first invocation | yes — "don't ask again" |
| `Bash <upload script>` | first invocation with a similar script shape | yes — "don't ask again" |
| `mcp__scope-mcp__scope_finalize_push` | first invocation | yes — "don't ask again" |

After the first push, subsequent pushes run **silently** — same three phases, zero prompts.

