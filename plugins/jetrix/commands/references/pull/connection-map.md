# /jetrix:pull connection-map — single-file fetch (via scope-mcp)

Pull the Solution's LLM-synthesised `connection-map.md` from GCS into
`<workspace_root>/.jetrix/connection-map.md` — at the `.jetrix/` root, NOT
under `<slug>/context/`. Rationale: the connection-map is one file per
Solution (not per feature/page/entity), so it belongs alongside
`project.json`, and the `.jetrix/` root is stable across future
`<slug>/…` folder-reorgs.

Authored via the portal's Connections tab (**Build map** button); the plugin
never writes it.

Two-phase, direct-from-GCS — bytes stream from GCS to disk via `curl`,
never through the MCP.

---

## 0. Preflight

The caller (`/jetrix:pull`) has already resolved `workspace_root`,
`solutionId`, and `solutionSlug` from `.jetrix/project.json`. Reuse those.
`project_root` is NOT used by this stage — the connection-map lives above
it, at `.jetrix/` root.

## 0a. Migration — if the file is still at the old location, move it

Old plugin versions wrote to `<workspace_root>/.jetrix/context/connection-map.md`.
Move it to the new canonical path if present:

```bash
OLD="<workspace_root>/.jetrix/context/connection-map.md"
NEW="<workspace_root>/.jetrix/connection-map.md"
if [[ -f "$OLD" && ! -f "$NEW" ]]; then
  mv "$OLD" "$NEW"
  echo "Migrated connection-map to new canonical path: $NEW"
fi
```

Idempotent — no-op if the file is already at the new path.

## 1. Phase 1 — one MCP call

```
mcp__scope-mcp__scope_pull_connection_map(
  solution_id="<solutionId from project.json>"
)
```

Response shape:
```json
{
  "document_id": "68f2...",
  "gcs_path": "gs://dev-jetrix-knowledge-docs/project-context/<solutionId>/connection-map.md",
  "original_name": "connection-map.md",
  "size_kb": 3,
  "updated_at": "2026-08-19T10:14:22.000Z",
  "signed_download_url": "https://storage.googleapis.com/...",
  "tags": ["scope-context", "connection-map"]
}
```

**If the tool errors with "No connection-map found"** — soft-fail: print
"No connection-map yet for this Solution — open the portal → Connections
tab → Build map." Do NOT hard-stop the outer `/jetrix:pull` or
`/jetrix:init` — the connection-map is optional until built.

## 2. Ensure the target directory exists

```bash
mkdir -p "<workspace_root>/.jetrix"
```

## 3. Phase 2 — one curl

```bash
curl --fail --silent --show-error \
     --output "<workspace_root>/.jetrix/connection-map.md" \
     "<signed_download_url>"
```

- `--fail` — non-2xx surfaces as an error rather than a corrupted file.
- Overwrites in place — the file is one-per-Solution and every Build map
  replaces it.

## 4. Update sync-state

Append / replace under `connection_map` (top-level key, NOT under a
project-root path) in `<workspace_root>/.jetrix/cache/sync-state.json`:

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

Create the file if missing; merge (don't clobber other stage entries).

## 5. Report

Print one line:

```
✓ connection-map.md → .jetrix/connection-map.md (3 KB, built <time-ago>)
```

or, on soft-fail:

```
· No connection-map yet — portal → Connections tab → Build map.
```
