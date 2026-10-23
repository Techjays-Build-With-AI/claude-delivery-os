# /jetrix:init — pulling the connection map

**Jetrix only, and only when the portal has built one.** On every other tracker §14 already
wrote this file from the user's own answers — do not run this and do not overwrite it.

## 10. Pull the connection-map — ONLY if the portal has built one

**Jetrix only.** No other tracker has a Connections tab, so skip §14 entirely — §13 already wrote `connection-map.md` from the user's own answers, and there is nothing to pull.

The connection-map is the LLM-synthesised architecture doc for the Solution, authored via the portal's Connections tab. Its canonical local path is **`<workspace_root>/.jetrix/connection-map.md`** — at the `.jetrix/` root, NOT under `<slug>/context/`. Rationale: `.jetrix/` root is stable across future plugin folder-reorgs; the connection-map is one file per Solution, not per feature/page/entity, so it belongs alongside `project.json`.

### 10a. Gate on the metadata we already have

**Do NOT call `scope_pull_connection_map` blindly.** The Solution bundle fetched in §14 already carries `solution.connection_map_ref` — a `null` value means the portal has never built a map, so there is nothing to fetch. Skipping the MCP call in that case saves a full round-trip on the common "not built yet" path.

Check:

```
if bundle.solution.connection_map_ref is null (or missing):
    print "· No connection-map yet — open the portal → Connections tab → Build map."
    skip §14 + §14 + §14 entirely
    continue to §15
```

Only if `connection_map_ref` is set (has `gcs_path` + `updated_at`) do you proceed with §14 onwards. Apply the same pattern to any future doc: if the metadata says it doesn't exist, don't call the fetch. Never make an "empty" pull call just to discover it's empty.

### 10b. Migration (already covered by §5)

The v2 layout migration in §5 handles the old connection-map path (`<slug>/context/connection-map.md` → `.jetrix/connection-map.md`). Nothing extra to do here for workspaces that were bound before v2.0. If you skipped §5 (edge case), the fallback `mv` is safe to run inline: `[[ -f "<workspace_root>/.jetrix/<slug>/context/connection-map.md" && ! -f "<workspace_root>/.jetrix/connection-map.md" ]] && mv <old> <new>`.

### 10c. Fetch a fresh signed URL

Now that we know a build exists, ONE MCP call gets us a signed URL:

```
mcp__scope-mcp__scope_pull_connection_map(solution_id=<solutionId>)
```

Response contract:
```json
{
  "document_id": "68f2...",
  "gcs_path": "gs://<bucket>/project-context/<solutionId>/connection-map.md",
  "original_name": "connection-map.md",
  "size_kb": 3,
  "updated_at": "2026-08-19T10:14:22.000Z",
  "signed_download_url": "https://storage.googleapis.com/...",
  "tags": ["connection-map", "solution-context"]
}
```

If this tool errors with "No connection-map found" (race between §14 and §14 — someone deleted the ref, or a permissions issue) → soft-fail with the same message from §14. Do NOT retry.

### 10d. Download + update sync-state

```bash
mkdir -p "<workspace_root>/.jetrix"
curl --fail --silent --show-error \
     --output "<workspace_root>/.jetrix/connection-map.md" \
     "<signed_download_url>"
```

Update `<workspace_root>/.jetrix/cache/sync-state.json` under the top-level `connection_map` key (merge, don't clobber other stages' keys):

```json
{
  "connection_map": {
    "document_id": "68f2...",
    "gcs_path": "gs://.../connection-map.md",
    "size_kb": 3,
    "updated_at": "2026-08-19T10:14:22.000Z",
    "pulled_at": "<ISO-8601 now>",
    "local_path": ".jetrix/connection-map.md"
  }
}
```

**Failure handling** — never block init on connection-map problems:

- curl exits non-zero (network, 4xx, 5xx from GCS) → print `· connection-map download failed (HTTP <code>) — will retry on next /jetrix:pull scope.` Continue to §15. Do NOT update sync-state on a failed download so the next pull naturally retries.
- Any other error → same soft-fail behavior. Init is done either way.
