# /jetrix:init — the connection map: build one if there is none, then pull it

**Jetrix only.** On every other tracker §13 already wrote this file from the user's own answers —
do not run this and do not overwrite it.

Two paths. When the portal has built a map, pull it (§10a → §10c). When it has not, **offer to
build one from here** (§10a.i) rather than sending the teammate to the portal — this command
already creates apps, and `project-mcp` carries the whole connection flow.

## 10. The connection map — build it if missing, then pull

**Jetrix only.** No other tracker has a Connections tab, so skip this whole step there — `/jetrix:init` §13 already wrote `connection-map.md` from the user's own answers, and there is nothing to pull.

The connection-map is the LLM-synthesised architecture doc for the Solution, authored via the portal's Connections tab. Its canonical local path is **`<workspace_root>/.jetrix/connection-map.md`** — at the `.jetrix/` root, NOT under `<slug>/context/`. Rationale: `.jetrix/` root is stable across future plugin folder-reorgs; the connection-map is one file per Solution, not per feature/page/entity, so it belongs alongside `project.json`.

### 10a. Gate on the metadata we already have

**Do NOT call `scope_pull_connection_map` blindly.** The Solution bundle `/jetrix:init` §10 already fetched carries `solution.connection_map_ref` — a `null` value means the portal has never built a map, so there is nothing to fetch. Skipping the MCP call in that case saves a full round-trip on the common "not built yet" path.

Check:

```
if bundle.solution.connection_map_ref is null (or missing):
    → §10a.i below, then continue to §15
```

### 10a.i. No map yet — offer to build one, don't send the user to the portal

**`/jetrix:init` creates apps** (`project_create_project`, §11), so writing to the Solution is
nothing new here, and `project-mcp` exposes the whole connection flow — `get`, `replace`, `build`.
Printing "open the portal" while holding those three tools leaves the teammate to do by hand what
this command could have done in the same breath. The portal is required for **repo linking**,
which needs an OAuth popup with no MCP path; connections are not in that category.

**When the Solution has 2+ apps**, offer it:

```
No connection map for this Solution yet. You have 2 apps.
Describe how they talk and I'll build it now? [y/n]

  testing-frontend → testing_backend   protocol? [REST]   purpose?
```

- **`y`** → run [`../connections.md`](../connections.md) — the same file `/jetrix:project-setup`
  §3b.i runs — then continue from §10c to pull the document it built.
- **`n`**, or fewer than 2 apps → print the portal fallback, built per
  [`../portal-links.md`](../portal-links.md) — the **Solution Explorer** route with the encoded blob, never
  the Mission Control route with the raw id — then skip to §15:

  ```
  · No connection-map yet.
      <portal-base>/solutions/explorer/solution/<encoded>
      → Connections tab → wire the apps → Save → Build map
  ```

**This is the only branch that may print a portal address.** Reaching for it without having asked is the
failure this section exists to prevent: the teammate is told to go and do by hand what the command was
holding three MCP tools to do.

**Offer it on a refresh too, not only on a first bind.** A Solution bound before anyone thought
about wiring is exactly the one that still has no map.

**This is worth a question, where most things are not.** The wiring cannot be recovered later:
`/tl:code-map` reads each repo in isolation, so a frontend call with no declared backend
counterpart comes out unresolved, and re-mapping is the only fix. Asking costs one prompt;
not asking costs a re-map.

Only if `connection_map_ref` is set (has `gcs_path` + `updated_at`) do you proceed with §10c onwards. Apply the same pattern to any future doc: if the metadata says it doesn't exist, don't call the fetch. Never make an "empty" pull call just to discover it's empty.

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

If this tool errors with "No connection-map found" (race between §10a and §10c — someone deleted the ref, or a permissions issue) → soft-fail with the same message §10a.i prints on `n`. Do NOT retry.

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
