## Stage: `context` (implemented — uses context-mcp)

**Model:** Jetrix stores the full architectural context graph (indexes + unit files + `_overview.md`) per env. Pull fetches it back.

- **Default pull** (no selector) — every context doc in the env, filtered to `context/frontend/`, `context/backend/`, `context/database/` (excludes `context/features/**`). Content-hash skip-unchanged, so subsequent pulls are cheap. Fresh teammate onboarding = one pull, everything on disk.
- **Patch pull** (with `--unit=<ids>` or `--path=<glob>`) — narrows to specific units. Useful for agents that already have most of the graph and just want a refresh of specific units.

**Env is a fixed two-word vocabulary — `main` (baseline) or `dev` (working state).** context-mcp does NOT accept envConfig branch names (`prod` / `staging` / `qa` etc.) — pushing under any other value silently strands docs at a tag pull can't find.

Env resolution:
- If `--env=main` or `--env=dev` present → use it.
- Else → default to `main` (the shared baseline).
- Any other value → reject with a clear error listing the two allowed values.

### 2. Parse selectors

**Arguments accepted:**
- `--unit=<comma-separated-ids>` — narrow to these units. Plugin needs the local indexes to resolve id → path. If any index is missing locally, the plugin pulls the 3 indexes first (small, one round trip), then resolves.
- `--path=<glob>` — narrow by glob. Repo-relative glob under `context/frontend|backend|database/**`. Multiple `--path=` flags allowed.
- No selectors → **default: every doc in the env under `context/frontend|backend|database/`**.

### 3. Phase 1 — manifest (one MCP call)

```
mcp__context-mcp__context_pull_manifest(
  solution_id=<from project.json>,
  env="<resolved env name>"
)
```

Response: `{solution_id, env, ready, docs: [{path, signed_download_url, documentId, version, tags, size_kb, ok}, ...]}`.

Filter: only rows tagged `["context", "env:<resolved env>"]`.

### 4. Client-side filter — narrow to requested files

Build the download set from the manifest based on the selectors parsed in step 2:

- **Default (no selector):** every path in the manifest that starts with `context/frontend/`, `context/backend/`, or `context/database/`. Everything else is dropped (including `context/features/**` — those come via `/jetrix:pull scope`).
- **If `--unit=<ids>` is set:** read the (just-pulled or already-local) indexes, look up each id's `Folder` cell, resolve to a repo-relative path, and include those paths **plus** the 3 indexes. Unknown ids → warn per-id, skip.
- **If `--path=<glob>` is set:** filter the manifest by each glob; union the matches. Indexes NOT auto-included in this mode — user's globs are explicit.
- **De-duplicate** the final path set.

**Never include** paths under `context/features/**` — those are BA scope-stage docs, pulled via `/jetrix:pull scope`.

### 5. Skip-unchanged + download (Bash only, no `Read`)

For each path in the filtered download set: `sha256sum` the local copy (if any) → compare against `sync-state.json[<path>][<env>].contentHash` → skip matching, curl GET the rest to `<project_root>/<path>`.

`mkdir -p` the parent directory of each path before writing — patch pulls of `context/backend/endpoints/supplier/create-supplier.md` need `context/backend/endpoints/supplier/` to exist first.

### 6. Update sync-state

Write per-file fresh contentHash under the env sub-key. Report `Updated: N | Unchanged: M | Skipped-unfiltered: K` (K = manifest rows dropped by the client-side filter — useful for the user to see how much they'd have downloaded in bulk mode).

