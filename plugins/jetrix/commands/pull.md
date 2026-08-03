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
2. Read `solutionId` + `solutionSlug` from it. Note the folder that CONTAINS `.jetrix/` as **`workspace_root`** — the entire `.jetrix/` is gitignored; it's the local working copy.
3. The delivery-os container is nested at `<workspace_root>/.jetrix/<solutionSlug>/`. Note this as **`project_root`**.
4. If `project_root` is missing, create the empty tree (`ba-output/`, `shared-context/`, `context/features/`) — Pull is the natural onboarding flow for a fresh teammate who just cloned the repo and ran `/jetrix:init`.

> **Directory contract:**
> ```
> <workspace_root>/
> └── .jetrix/                         ← ENTIRELY gitignored
>     ├── project.json
>     ├── cache/sync-state.json        ← sync-state ALWAYS lives here
>     └── <solutionSlug>/              ← project_root
>         ├── ba-output/
>         ├── shared-context/
>         └── context/
> ```
> Sync-state reads/writes below resolve to `<workspace_root>/.jetrix/cache/sync-state.json` — NEVER inside `<project_root>/`.

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
    business-rules.md, nfrs.md, test-scenarios.md,
    dependencies.md, open-questions.md, status.md
    tl-plan.md         (only if TL has pushed implementation for this feature)
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

- A **list name** (e.g. `"Supplier Management"` — feature-push resolves the list name from each feature's `list_name` frontmatter, or from `mapped_scope`; use the exact List name shown in MC)
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

A Solution's FEATURE tasks may be spread across **multiple MC Lists** (one per resolved `list_name` at push time — see `push.md` Stage: feature). `pull list <name>` fetches only the tasks in that one List. To materialize every feature under the Solution regardless of List, use `pull scope` (uses `feature_pull_bundle` without a list filter).

---

Keep it **idempotent** — a re-pull of unchanged docs must be a no-op (only `lastPulled` timestamps get bumped). Never overwrite a locally-modified file whose contentHash differs from the last pull unless the remote hash also differs (that's covered because we compare local-vs-remote-record before deciding to download).
