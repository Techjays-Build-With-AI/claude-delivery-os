## Stage: `context` (implemented — uses context-mcp)

**Model:** Jetrix stores every architectural context file — indexes + unit files + `_overview.md` — for both envs (`main` baseline, `dev` working state). The graph is not code; it's the map the agents consult, so it belongs in the context engine, not in git.

- **Default push** (no selector) — walks **everything** under `context/frontend/`, `context/backend/`, `context/database/` (indexes + unit files + `_overview.md`). Content-hash skip-unchanged applies, so a re-push of a workspace where nothing changed is a no-op.
- **Patch push** (with `--unit=<ids>` or `--path=<glob>`) — narrows the walk to the specified units. Use when you only want to publish a specific slice (e.g. one page and its endpoint) without touching the rest.
- **Never pushed here** — `context/features/**`. Those are BA scope-stage folders that become MC Tasks via the `feature` stage.

The 3 indexes:
- `context/frontend/page-index.md`
- `context/backend/endpoint-index.md`
- `context/database/entity-index.md`

**Env is driven by envConfig** — every project has a list of envs (e.g. `["dev", "staging", "prod"]` or `["dev", "live"]`). Pass `--env=<name>` to select any of them. If omitted, defaults to the **first env in the chain** (the working / in-flight env — usually `dev`). The **last env in the chain** is the baseline / shared truth (`main`, `prod`, `live` — whatever the team named it) and is what `/jetrix:pull context` returns by default.

To resolve the env list, call `project-mcp.project_get_env_configs(project_id)` — the response's `environment` fields form the chain. The plugin can validate `--env=<name>` against that list.

Legacy `--baseline` is still accepted as an alias for "push to the last env in the chain."

### 2. Parse selectors + build the file list — Bash only

**Arguments accepted:**
- `--unit=<comma-separated-ids>` — narrow to these specific units. Plugin reads the local indexes, maps each id to its `Folder` cell (`./pages/supplier/supplier-list.md`), resolves to a repo-relative path, and uses those paths **plus** the 3 indexes. Unknown IDs → warn per-id and skip; don't halt the batch.
- `--path=<glob>` — narrow by glob. Repo-relative glob under `context/frontend|backend|database/**`. Multiple `--path=` flags may be passed. Examples: `--path=context/frontend/pages/supplier/*.md`, `--path=context/backend/endpoints/**/*.md`.
- No selectors → **default: walk everything** under `context/frontend/`, `context/backend/`, `context/database/`.

**File list:**
- Default: `find context/frontend context/backend context/database -type f -name '*.md'`.
- With selectors: resolve to the narrow list (indexes + specified units/paths).
- **Always exclude** paths under `context/features/**` — those are BA scope-stage content pushed via the feature stage.
- De-duplicate.

```bash
#!/usr/bin/env bash
set -e
PROJECT_ROOT="<absolute project_root>"
cd "$PROJECT_ROOT"

# Default: walk all .md under the three layer dirs.
# Selectors narrow this list (plugin injects a filtered set before this loop).
mapfile -t CANDIDATES < <(
  find context/frontend context/backend context/database \
    -type f -name '*.md' 2>/dev/null | sort
)

for f in "${CANDIDATES[@]}"; do
  [[ -f "$f" ]] || continue
  # Guard: never push under context/features/** here — belongs to feature stage.
  [[ "$f" == context/features/* ]] && continue
  size_bytes=$(wc -c < "$f")
  size_kb=$(( (size_bytes + 1023) / 1024 ))
  hash=$(sha256sum "$f" | cut -d' ' -f1)
  echo "$f|$size_kb|$hash"
done
```

Parse output into `[{path, size_kb, content_hash}]`. Missing dirs skip silently — an early workspace may only have one layer.

**Do NOT `Read` these files.** Bash-only walk keeps bytes out of the plugin's context; content flows GCS → curl in step 5.

**Skip-unchanged is what makes bulk push cheap.** Step 3 below compares content hash against `sync-state.json` and filters unchanged files out before Phase 1 signs URLs. First push uploads everything; subsequent pushes upload only what changed.

### 3. Resolve env + skip unchanged

context-mcp uses a **fixed two-word vocabulary** — `main` (shared baseline) and `dev` (in-flight working state) — NOT the envConfig branch names. This is deliberate: `page-index.md` etc. describe architecture and change slowly, so a two-bucket model is enough and it stays legible regardless of how many deploy envs a project has. Any other value (like `prod` derived from envConfig) writes docs to a tag that pull can't find, so the docs look "lost" even though they're on disk.

- Resolve env from args (this is the ONLY place these words come from — do NOT derive from envConfig):
  - If `--env=main` or `--env=dev` present → use it.
  - Else if `--baseline` present → `env = main`.
  - Else if the workspace has NO `context/features/*/implementation-plan.md` files → **auto-baseline**: `env = main`. Rationale: with no `/tl:plan` output yet, the indexes describe as-shipped code (produced by `/tl:map`), so they belong in the shared baseline. Print a one-line note: *"No feature plans found — pushing to baseline `main`. Pass `--env=dev` to override."*
  - Else → `env = dev` (working state).
- Reject any `--env=<other>` value with a clear error naming the two allowed values. The plugin owns the vocabulary contract; passing `prod` / `staging` / `qa` here silently breaks pull.
- Read `<workspace_root>/.jetrix/cache/sync-state.json`. Look at `context/<path>[<env>]` — skip files whose `contentHash` matches.

### 4. Phase 1 — prepare (one MCP call)

Pass the resolved file list from step 2 (indexes + any unit files added via `--unit` / `--path` patches). Skip any file whose `content_hash` matches sync-state for the target env — no need to signed-URL what won't change.

```
mcp__context-mcp__context_prepare_push(
  solution_id=<from project.json>,
  docs=[
    # Always the indexes that exist:
    { path: "context/frontend/page-index.md",   mime_type: "text/markdown" },
    { path: "context/backend/endpoint-index.md", mime_type: "text/markdown" },
    { path: "context/database/entity-index.md",  mime_type: "text/markdown" },
    # Plus any unit files added via --unit / --path (patch mode). Example:
    { path: "context/frontend/pages/supplier/supplier-list.md", mime_type: "text/markdown" },
    { path: "context/backend/endpoints/supplier/create-supplier.md", mime_type: "text/markdown" }
  ],
  env=<main or dev>
)
```

Response: per-doc `{path, signed_upload_url, gcs_path, mime_type, ok}`.

### 5. Phase 2 — upload (one Bash call, parallel)

Generate a bash script that curl-PUTs each file to its signed URL. **Run the uploads in parallel** via `xargs -P 8` — context push may cover 50+ unit files on a busy graph, and sequential PUTs turn that into 25+ seconds of round-trip latency. Parallel uploads cut it to ~3–5 seconds for the same set.

Every upload still logs OK/FAIL per file (same success predicate the sync-state update in step 7 depends on). `set +e` at the top so a single PUT failure doesn't abort the batch — the failed file just gets marked FAIL and excluded from the finalize call.

```bash
#!/usr/bin/env bash
set +e
RESULT_LOG=$(mktemp)

upload_one() {
  local abs_path="$1" signed_url="$2" rel_path="$3"
  local http_code
  http_code=$(curl -sS -o /dev/null -w "%{http_code}" -X PUT \
    -H "Content-Type: text/markdown" \
    --data-binary "@$abs_path" "$signed_url")
  if [[ "$http_code" == "200" ]]; then
    echo "OK  $rel_path" >> "$RESULT_LOG"
  else
    echo "FAIL $rel_path (HTTP $http_code)" >> "$RESULT_LOG"
  fi
}
export -f upload_one
export RESULT_LOG

# One line per doc: abs_path<TAB>signed_url<TAB>rel_path
# (The plugin writes this list from the prepare_push response.)
cat uploads.tsv | xargs -P 8 -d '\n' -I{} bash -c '
  IFS=$'"'"'\t'"'"' read -r abs signed rel <<< "{}"
  upload_one "$abs" "$signed" "$rel"
'

cat "$RESULT_LOG"
rm -f "$RESULT_LOG"
```

Parse the output: lines starting `OK ` are successful uploads (include those docs in the finalize call); `FAIL ` are excluded so no orphan FileMeta rows get created for objects that never made it to GCS.

### 6. Phase 3 — finalize (one MCP call)

```
mcp__context-mcp__context_finalize_push(
  solution_id=<from project.json>,
  docs=[
    { path: "context/frontend/page-index.md", gcs_path: "<from prepare>", size_kb: 12 },
    # ... one row per file uploaded, including any patched unit files
  ],
  env=<main or dev>
)
```

context-mcp auto-tags each doc `["context", "env:<env>"]`. No caller tag work needed.

### 7. Update sync-state per env

**MERGE, do not replace.** Read `<workspace_root>/.jetrix/cache/sync-state.json` first (contains scope/feature/other keys), then set only the `context/<path>` keys you're updating, and write the merged object back.

```json
{
  "context/frontend/page-index.md": {
    "main": { "documentId": "...", "version": 1, "contentHash": "...", "lastPushed": "..." },
    "dev":  { "documentId": "...", "version": 3, "contentHash": "...", "lastPushed": "..." }
  }
}
```

Only touch the sub-key for the env you just pushed. Report `Uploaded: N to <env>`.

