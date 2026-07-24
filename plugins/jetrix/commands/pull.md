---
description: Refresh local delivery-os work from Jetrix via the stage-specific MCP. Argument selects which stage to pull — `scope` (BA outputs ← scope-mcp), `context` (TL graph ← context-mcp), `tasks` (feature tasks ← task-mcp; not implemented yet), `all` (every implemented stage). Downloads use the direct-from-GCS pattern (server issues signed URLs, local bash + curl streams bytes straight to disk), so pull is fast regardless of file count. Idempotent — files whose remote contentHash matches the local hash are left untouched.
argument-hint: "<stage> | all"
---

# /jetrix:pull

Refresh the local delivery-os container from Jetrix. The first argument names the **stage** — this decides which MCP fetches and which local paths get written:

| Stage | MCP | What it pulls |
|---|---|---|
| `scope` | `scope-mcp` + `task-mcp` | BA outputs + every feature folder (combined pull) |
| `context` | `context-mcp` | TL knowledge graph (env-scoped; default `main`) |
| `task <ref>` | `task-mcp` | ONE feature folder — `<ref>` is `TASK-<number>`, `FEAT-<id>`, or a MongoDB `_id` |
| `sprint <ref>` | `task-mcp` | Every feature currently in a sprint — `<ref>` is a sprint number or MongoDB `_id` |
| `list <ref>` | `task-mcp` | Every feature in an MC List — `<ref>` is a list name (e.g. solution slug) or MongoDB `_id` |
| `all` | (all above) | Full workspace: scope + context |

Every stage uses a **two-phase direct-from-GCS pattern** — 1 MCP call for the manifest + 1 Bash call for the downloads. **File bytes never enter Claude's context**; they go from GCS straight to disk via signed download URLs.

This document covers all stages. **Scope is the currently-implemented one.**

---

## 0. Preflight — resolve the delivery-os workspace

**This command operates on the delivery-os container folder that `/jetrix:init` bound to a Jetrix Solution.** Resolve the workspace FIRST:

1. Walk up from `$PWD` looking for **`.jetrix/project.json`** (up to 3 parent levels). If missing → tell the user to run `/jetrix:init` first.
2. Read `solutionId` + `solutionSlug` from it. Note the folder that CONTAINS `.jetrix/` as **`workspace_root`** — that's where `.jetrix/cache/sync-state.json` lives.
3. The delivery-os container is `<workspace_root>/<solutionSlug>/`. Note this as **`project_root`**.
4. If `project_root` is missing, create the empty tree (`ba-output/`, `shared-context/`, `context/features/`) — Pull is the natural onboarding flow for a fresh teammate who just cloned the repo.

> **Directory contract:**
> ```
> <workspace_root>/
> ├── .jetrix/
> │   ├── cache/sync-state.json     ← sync-state ALWAYS lives here
> │   └── project.json
> └── <solutionSlug>/               ← project_root
>     ├── ba-output/
>     ├── shared-context/
>     └── context/                  (NEVER contains a .jetrix/ folder)
> ```
> `.jetrix/` and the solution folder are siblings. Sync-state reads/writes below resolve to `<workspace_root>/.jetrix/cache/sync-state.json` — NEVER inside `<project_root>/`.

## 1. Parse the stage argument

```
/jetrix:pull <stage>
```

- `<stage>` (required): `scope` | `context` | `task <ref>` | `sprint <ref>` | `list <ref>` | `all`. If missing or unknown, print the table above and stop.
- `<ref>` (required for `task`/`sprint`/`list` stages): identifier — accepts human forms (`TASK-42`, `FEAT-CLSF-01`, sprint number, list name) or a MongoDB `_id`. Plugin routes the ref to the right filter param on `feature_pull_bundle`.

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

- If the on-disk hash equals `sync-state[doc.path].contentHash` → **skip** (local already matches the version scope-mcp is offering).
- Otherwise mark as **needs download**.

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
      "title": "User Authentication",
      "description": "## Summary\n...\n\n## Business Objective\n...",   // H2 preserved
      "scope": "## In Scope\n...\n\n## Out of Scope\n...",
      "assumptions": "...", "business_rules": "...",
      "technical_flow": "...", "journeys": "...",
      "acceptance_criteria": "...", "dependencies": "...", "open_questions": "...",
      "implementation_details": "...",   // present only if TL has pushed
      "status": "readyForDev", "priority": "..."
    },
    ...
  ]
}
```

### 6. Compose feature files locally (canonical section order)

For each feature in the response, write these files under `<project_root>/context/features/<slug>/`. Use `mkdir -p` first. Order matters — plan v3 §2.5.

**`feature.md`:**
```
---
feature_id: <feature_id>
initiative: <initiative>
slug: <slug>
jetrix_task_id: <task_number>
jetrix_task_object_id: <task_object_id>
status: <status>
---

# <title>

<description>       ← already has ## Summary, ## Business Objective, ...

<scope>             ← already has ## In Scope, ## Out of Scope

## Assumptions

<assumptions>

## Related Business Rules

<business_rules>
```

**`workflow.md`:**
```
# <title> — Workflow

## Technical Flow

<technical_flow>

## User Journeys

<journeys>
```

**`acceptance-criteria.md`:**
```
# <title> — Acceptance Criteria

<acceptance_criteria>
```

**`dependencies.md`:**
```
# <title> — Dependencies

<dependencies>
```

**`open-questions.md`:**
```
# <title> — Open Questions

<open_questions>
```

**`status.md`:**
```
# Status: <STATUS_UPPER>
Progress: <progress>%
```

**`tl-plan.md`** — write ONLY if `implementation_details` is non-empty (means TL has already run `/jetrix:push implementation`).

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

## Stage: `context` (implemented — uses context-mcp)

**Env is driven by envConfig.** Pass `--env=<name>` to select any env from the chain (e.g. `dev` / `staging` / `prod` / `live` — whatever the team named them). Default: the **last env in the envConfig chain** — the shared baseline all teammates plan against.

Env resolution:
- Resolve envConfig via `project-mcp.project_get_env_configs(project_id)` first (unless `--env=` supplied — in which case just validate it).
- If `--env=<name>` present → use it.
- Else → default to the last env in the chain (typically named `main` / `prod` / `live`).

### 2. Phase 1 — manifest (one MCP call)

```
mcp__context-mcp__context_pull_manifest(
  solution_id=<from project.json>,
  env="<resolved env name>"
)
```

Response: `{solution_id, env, ready, docs: [{path, signed_download_url, documentId, version, tags, size_kb, ok}, ...]}`.

Filter: only rows tagged `["context", "env:<resolved env>"]`.

### 3. Skip-unchanged + download (Bash only, no `Read`)

Same pattern as pull scope: sha256sum every local candidate → compare against `sync-state.json[<path>][main].contentHash` → skip matching, download the rest via curl GET to `<project_root>/<path>`.

`mkdir -p context/frontend context/backend context/database` before writes.

### 4. Update sync-state

Write per-file fresh contentHash under the `main` sub-key. Report `Updated: N | Unchanged: M`.

## Stage: `all`

Runs every implemented stage in order. Currently just `scope` + `context`; extends automatically as stages come online.

---

## Stage: `task <ref>` (implemented — uses task-mcp)

Materializes ONE feature folder locally. `<ref>` accepts any of:

- `TASK-42` — task number (routed to `task_number=42`)
- `FEAT-CLSF-01` — BA feature id (routed to `feature_id="FEAT-CLSF-01"`)
- `6a61...` (24-char hex) — MongoDB `_id` (routed to `task_object_id`)

Plugin recipe:

1. **Parse `<ref>`** — regex-detect the identifier type:
   - Starts with `TASK-` → strip prefix, `task_number` (int)
   - Starts with `FEAT-` → `feature_id` (string)
   - 24 lowercase-hex chars → `task_object_id`
   - Anything else → error, print help.
2. **Single MCP call** with only the matched filter:
   ```
   mcp__task-mcp__feature_pull_bundle(
     solution_id = <from project.json>,
     task_number = 42    # OR feature_id="FEAT-CLSF-01" OR task_object_id="..."
   )
   ```
3. Response has `pulled: 0 | 1` and a `features[0]` record (or none if the ref didn't match).
4. **Reconstruct the local feature folder** at `<project_root>/context/features/<slug>/` from the record's fields — same shape as the combined `scope` pull.
5. **Update sync-state** (merge, not replace) — set `tasks/<FEAT-...>` entry with new `contentHash` + `lastPulled`.

Report:
```
✓ Pulled TASK-42 (FEAT-CLSF-01, "Document Classification & Extraction")
  → context/features/document-classification-extraction/
    feature.md, workflow.md, acceptance-criteria.md,
    dependencies.md, open-questions.md, implementation-plan.md, status.md
```

Use this stage for **single-task dev flow** — `/dev:build TASK-42` can auto-run it if the feature folder isn't already on disk.

---

## Stage: `sprint <ref>` (implemented — uses task-mcp)

Materializes every feature folder currently in a sprint. `<ref>` accepts:

- A **sprint number** (integer like `3`) — routed to `sprint_number=3`; task-mcp resolves it to `sprintId` server-side via the solution's sprint list
- A **MongoDB `_id`** (24-char hex) — routed to `sprint_id`

Plugin recipe:

1. **Parse `<ref>`** — integer or 24-char hex.
2. **Single MCP call**:
   ```
   mcp__task-mcp__feature_pull_bundle(
     solution_id = <from project.json>,
     sprint_number = 3        # OR sprint_id="..."
   )
   ```
3. Iterate `features[]` in the response → reconstruct each `context/features/<slug>/` folder.
4. Merge into sync-state per feature.

Report:
```
✓ Pulled Sprint 3 (5 features)
  ✓ TASK-42 document-classification-extraction
  ✓ TASK-43 matching-deduplication
  ✓ TASK-44 human-in-the-loop-review
  ✓ TASK-45 portal-access-security
  ✓ TASK-46 validation-hubspot-sync
```

Use this stage for **sprint kickoff** — team members pull just this week's work rather than the whole solution.

---

## Stage: `list <ref>` (implemented — uses task-mcp)

Materializes every feature folder in an MC List. `<ref>` accepts:

- A **list name** (e.g. `larkiq` — task-mcp uses the solution slug as list name by default)
- A **MongoDB `_id`** (24-char hex)

Plugin recipe:

1. **Parse `<ref>`** — 24-char hex → `list_id`; anything else → `list_name`.
2. **Single MCP call**:
   ```
   mcp__task-mcp__feature_pull_bundle(
     solution_id = <from project.json>,
     list_name = "larkiq"     # OR list_id="..."
   )
   ```
3. Same materialization + sync-state merge as `sprint` stage.

Since task-mcp always creates FEATURE tasks in a list named after the solution slug, `list <solution_slug>` is functionally equivalent to `pull scope` minus the BA docs — useful when you already have scope pulled and just want fresh feature content.

---

Keep it **idempotent** — a re-pull of unchanged docs must be a no-op (only `lastPulled` timestamps get bumped). Never overwrite a locally-modified file whose contentHash differs from the last pull unless the remote hash also differs (that's covered because we compare local-vs-remote-record before deciding to download).
