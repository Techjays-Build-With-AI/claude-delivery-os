---
description: Publish local delivery-os work up to Jetrix via the stage-specific MCP. Argument selects which stage to sync — `scope` (BA outputs → scope-mcp), `context` (TL graph → context-mcp), `feature` (BA feature folders → task-mcp), `task` (any .md file or folder of .md files → task-mcp, with optional --list / --sprint targeting), `implementation` (TL plan → Task's implementation tab), `deliverable` (client HTMLs → deliverable-mcp). Uploads use the direct-to-GCS pattern (server brokers signed URLs, local bash + curl streams bytes from disk straight to GCS), so pushes never route file bytes through Claude's context — a 100-file push is as fast as a 1-file push.
argument-hint: "<stage> [<path>] [--list=<name|id>] [--sprint=<id>]"
---

# /jetrix:push

Publish local delivery-os work to Jetrix. The first argument names the **stage** — this decides which local paths get scanned and which MCP handles the sync:

| Stage | MCP | What it pushes |
|---|---|---|
| `scope` | `scope-mcp` | BA outputs — `ba-output/*.md`, `shared-context/*.md`, `context/features/feature-index.md` |
| `context` | `context-mcp` | TL knowledge graph — 3 knowledge indexes (env-scoped) |
| `feature` | `task-mcp` | Per-feature MC Tasks — creates ONE Task per `context/features/<slug>/` folder |
| `task` | `task-mcp` | Ad-hoc tasks — ONE MC Task per `.md` file. Accepts a file, a folder, or omit for `tasks/**/*.md`. Optional `--list=<name\|id>` or `--sprint=<id>` chooses the target. |
| `implementation` | `task-mcp` | TL plan → each Task's Implementation tab (`implementationDetails`), status → `READY_FOR_DEV` |
| `deliverable` | `deliverable-mcp` | Client HTMLs — `doc-output/*.html` |

Every stage uses a **three-phase direct-to-GCS pattern** on its MCP (`*_prepare_push` → local `curl` PUTs → `*_finalize_push`) so the plugin does at most 2 MCP calls + 1 Bash call per push, regardless of file count. **File bytes never enter Claude's context**; they go straight from local disk to GCS via signed URLs (same pattern the UI's KnowledgeHubService uses).

This document covers all four stages. **Scope (the BA sync) is the currently-implemented one.** The others land as their MCPs come online.

---

## 0. Preflight — resolve the delivery-os workspace

**This command operates on the delivery-os container folder that `/jetrix:init` bound to a Jetrix Solution — NOT on your current directory.** Resolve the workspace FIRST:

1. Walk up from `$PWD` looking for **`.jetrix/project.json`** (up to 3 parent levels). If missing everywhere → stop and tell the user to run `/jetrix:init <projectId | slug>` first.
2. Read `solutionId` + `solutionSlug` from it. Note the folder that CONTAINS `.jetrix/` as **`workspace_root`** — the entire `.jetrix/` is gitignored; it's the local working copy.
3. The delivery-os container is the nested folder `<workspace_root>/.jetrix/<solutionSlug>/` (e.g. if `solutionSlug: "larkiq"` then `.jetrix/larkiq/`). Note this as **`project_root`** — every content file walk below is relative to it.
4. Verify the container exists. If missing → tell the user to run `/delivery-os:init`.

> **Directory contract (referenced throughout this doc):**
> ```
> <workspace_root>/
> └── .jetrix/                         ← ENTIRELY gitignored
>     ├── project.json
>     ├── cache/sync-state.json        ← sync-state ALWAYS lives here
>     └── <solutionSlug>/              ← project_root
>         ├── ba-output/
>         ├── shared-context/
>         ├── context/
>         └── ...
> ```
> Every `sync-state.json` reference below resolves to `<workspace_root>/.jetrix/cache/sync-state.json` — NEVER inside `<project_root>/`.

## 1. Parse the stage argument

```
/jetrix:push <stage> [<filename>]
```

- `<stage>` (required): `scope` | `context` | `feature` | `task` | `implementation` | `deliverable`. If missing or unknown, print the table above and stop.
- `<filename>` (optional, scope only): push a single file at that relative path instead of the whole stage.
- `<path>` (optional, task only): `.md` file or folder; see the `task` stage below.
- `--list=<name|id>` / `--sprint=<id>` (task only): target selector — see the `task` stage below.

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

scope-mcp does **not** auto-add any identity tag — the plugin owns the tag semantics. Every future stage (context-mcp, task-mcp, deliverable-mcp) mirrors this two-level pattern with its own primary/support pair (`context`/`context-support`, `tasks`/`tasks-support`, etc.).

> **sync-state contract (applies to every stage below — read carefully).** `sync-state.json` is the **single shared file** for ALL stages — scope, feature, context, implementation. Every write is a MERGE, never a REPLACE. The correct pattern in every stage's write-back step is:
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

### 5. Phase 2 — upload (one Bash call)

Generate a bash script that curl-PUTs each file to its signed URL (same pattern as scope push — `set +e`, log OK/FAIL per file, `-H "Content-Type: text/markdown"`).

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

## Stage: `feature` (implemented — uses task-mcp)

Creates ONE MC Task per `context/features/<slug>/` folder. Features are grouped into MC Lists by resolved `list_name` — one Task per feature, one MC List per unique `list_name` value, one `feature_upsert_bundle` call per group (task-mcp's `solution_slug` parameter carries the resolved List name for that batch). First push per Task = POST (create); repush = PUT (update by `jetrix_task_object_id` stored in `feature.md` frontmatter).

### 1a. Prereq check — do NOT crash on missing files, tell the user what to pull

Before walking, verify `context/features/` exists and has at least one feature folder with a `feature.md`. Two failure modes to handle explicitly:

- **`context/features/` doesn't exist** — halt with:
  ```
  ✗ /jetrix:push feature requires the BA feature breakdown.
    This workspace has no context/features/ folder.
    Run one of:
      /ba:features                 (generate the breakdown from local scope)
      /jetrix:pull scope           (pull an existing breakdown from Jetrix)
    Then re-run /jetrix:push feature.
  ```
- **Folder exists but a feature is missing required BA files** (e.g. no `feature.md`, or no `acceptance-criteria.md` — the seven tab-critical files) — halt for that feature with:
  ```
  ✗ /jetrix:push feature: feature '<slug>' is missing required BA files.
    Missing:
      context/features/<slug>/business-rules.md
      context/features/<slug>/nfrs.md
    Run one of:
      /jetrix:pull scope           (pull all feature folders from Jetrix)
      /jetrix:pull task <ref>      (pull just this feature)
      /ba:features <slug>          (regenerate locally from scope)
    Then re-run /jetrix:push feature.
  ```
- **Never silently skip** a feature just because a file is missing. Silent skips ship half-tasks; explicit halts let the user fix and retry.

Only after all prereq checks pass do you walk the folders in step 2.

### 2. Walk feature folders — Bash + Read (small files, OK to read)

Feature files are small (each `.md` is a few KB). Reading them is fine — bytes DO enter Claude's context here because we need to parse sections. Use ONE Bash call to list folders + hash for skip-unchanged; then `Read` per file to extract sections.

```bash
#!/usr/bin/env bash
set -e
PROJECT_ROOT="<absolute project_root>"
cd "$PROJECT_ROOT"

for dir in context/features/*/; do
  slug=$(basename "$dir")
  [[ "$slug" == "feature-index.md" ]] && continue
  # concat hash of all 6-7 files in the folder
  hash=$(cat "$dir"*.md 2>/dev/null | sha256sum | cut -d' ' -f1)
  echo "$slug|$hash"
done
```

Parse into `[{slug, content_hash}]`.

### 3. Per feature — read local files + assemble the wire fields

For each folder that needs push (content_hash differs from `sync-state.json[<slug>].contentHash`):

**(a) Read the BA-authored files** (feature folder contents — small, `Read` is fine). The BA templates now produce tab-shape content directly, so **no stripping, regex-cleaning, or reshaping is needed at push time.** The push is a passthrough for five files and a two-line concatenation for the two merge pairs.

| Local file | Read purpose | Special notes |
|---|---|---|
| `feature.md` | Frontmatter (identity + metadata) + body (Description tab: Objective / In Scope / Out of Scope) | Frontmatter carries `title` (human-readable task title), `feature_id`, `initiative`, `slug`, `list_name` (optional — MC List routing), `use_cases`, `mapped_*`, `depends_on_features`, `status`, `priority`, `jetrix_task_id`, `jetrix_task_object_id`. Task title = `frontmatter.title` (falls back to H1 line if a legacy file still carries one, then to `slug` — but new templates author `title:` in frontmatter and never carry an H1). List routing resolved in (b) below. |
| `workflow.md` | Body (Workflow section — user flows + mermaid) | Concatenated into `description` at (b). |
| `business-rules.md` | Body verbatim | Sent as-is. |
| `acceptance-criteria.md` | Body verbatim | Sent as-is. Templates now author it as three grouped tables directly. |
| `nfrs.md` | Body verbatim | Sent as-is. If the file is missing, send `""`. |
| `test-scenarios.md` | Body verbatim | Sent as-is. If the file is missing, send `""`. |
| `dependencies.md` | Body (Depends on + Assumptions) | Concatenated with `open-questions.md` into `assumptions` at (b). |
| `open-questions.md` | Body (Open questions bullet list) | Concatenated with `dependencies.md` into `assumptions` at (b). |
| `implementation-plan.md` | Not read | Local-only. Never pushed. |
| `status.md` | Not read | Local-only. Never pushed. |

**(b) Assemble the wire fields** — five verbatim, two merges. Nothing else.

```
title              = <frontmatter.title of feature.md>
                     ↳ fallback: <H1 of feature.md body> if frontmatter.title absent
                     ↳ fallback: <frontmatter.slug> if neither is present

description        = <feature.md Objective section (from "## Objective" up to but not including "## In Scope")>
                   + "\n\n## Workflow\n\n"
                   + <workflow.md body — minus frontmatter, minus H1>
                   + "\n\n"
                   + <feature.md In Scope + Out of Scope sections (from "## In Scope" to end of body)>
                     ↳ If feature.md has no "## In Scope" heading (legacy or authored without scope):
                       fall back to <feature.md body> + workflow (old order). Warn the author —
                       the reader loses the "scope after workflow" affordance that AC / test-scenarios
                       rely on when they cite "email notifications are out of scope, so a toast is shown".

business_rules     = <business-rules.md body — minus frontmatter, minus H1>

acceptance_criteria = <acceptance-criteria.md body — minus frontmatter, minus H1>

nfrs               = <nfrs.md body — minus frontmatter, minus H1>
                     or "" if the file is missing

test_scenarios     = <test-scenarios.md body — minus frontmatter, minus H1>
                     or "" if the file is missing

assumptions        = <dependencies.md body — minus frontmatter, minus H1>
                   + (open-questions.md body starts with "— none."
                        ? "\n\n**Open questions** " + <open-questions.md body>
                        : "\n\n**Open questions**\n\n" + <open-questions.md body>)
```

**Frontmatter → metadata** (populates task metadata for the dependency-check gate in `/dev:build`):

```
metadata = {
  externalId:          <frontmatter.feature_id>,
  externalInitiative:  <frontmatter.initiative>,
  externalSlug:        <frontmatter.slug>,
  dependsOnFeatureIds: <frontmatter.depends_on_features (list)>,
  useCases:            <frontmatter.use_cases (list)>,
}
```

**Resolve `list_name` per feature** — this determines which MC List the Task lands under. Fallback chain:

```
list_name = <frontmatter.list_name of feature.md>
            ↳ fallback: <frontmatter.mapped_scope with the "§X.Y " prefix stripped>
                        e.g. "§3.2 Supplier Management" → "Supplier Management"
            ↳ fallback: <frontmatter.initiative>            (kebab-case is fine; MC List names are free text)
            ↳ fallback: <solution_slug from project.json>   (last-resort; no feature is orphaned)
```

Compute the pattern strip as: if `mapped_scope` starts with `§`, drop everything up to and including the first whitespace character; trim the remainder. Every feature ends up with a non-empty `list_name`. Two features with the same resolved `list_name` share one MC List; task-mcp's find-or-create against `List.name` handles both cases.

**One targeted transform — file-path strip on every wire field before sending.** Local BA files may contain filesystem navigation aids (`see business-rules.md`, `[code › ...]`, backticked code paths). Those help the BA author cross-check while authoring, but they're meaningless to a Jetrix reader who has no filesystem. After assembling each wire field, apply `strip_file_paths()` (defined below) to `description`, `business_rules`, `acceptance_criteria`, `nfrs`, `test_scenarios`, and `assumptions`. Do NOT apply to `implementation_details` (TL-authored, already clean) or to `metadata` / `title` (structured, no prose).

```
def strip_file_paths(text):
    # File-reference prose  ("… — see foo.md.", "(see foo.md)", "see `foo.md`")
    text = re.sub(r'\s+—\s+see\s+[a-zA-Z0-9_-]+\.md\.?', '', text)
    text = re.sub(r'\s*\(see\s+[a-zA-Z0-9_-]+\.md\)\.?', '', text)
    text = re.sub(r'see\s+`[a-zA-Z0-9_-]+\.md`', '', text)

    # Bracketed code citations  ([code › src/...], [TL ...])
    text = re.sub(r'\[code › [^\]]+\]', '', text)
    text = re.sub(r'\[TL[^\]]*\]', '', text)

    # Backticked code paths — must contain "/" to distinguish from bare filenames
    text = re.sub(
        r'`(src|controllers|models|routes|components|pages|endpoints|entities|api|utils|services|app|lib)/[^`]+`',
        '', text,
    )

    # Backticked bare filenames with code extensions
    text = re.sub(
        r'`[a-zA-Z0-9_-]+\.(md|js|ts|jsx|tsx|py|go|java|rb|rs|kt|swift)`',
        '', text,
    )

    # Cleanup: collapse leftover spaces + orphan punctuation
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r' +([\.,;:])', r'\1', text)
    text = re.sub(r',\s*,', ',', text)
    return text.strip()
```

**Never stripped — IDs pass through untouched:** `BR-N`, `AC-N`, `NFR-<label>`, `WF-###`, `DATA-###`, `INT-###`, `SRC-###`, `DEC-###`, `PAGE-<AREA>-NN`, `EP-<AREA>-NN`, `ENT-<AREA>-NN`, `FEAT-<AREA>-NN`. These are the cross-tab reference mechanism inside Jetrix and must survive push.

**No content reshaping otherwise** — no bullet-to-table conversion, no framework rewriting, no heading fixes. BA templates author the tab-shape directly; the strip only removes filesystem noise. If a local file contains something the strip *can't* handle (framework names, provenance callouts, feature-id headings), that's still a **BA template violation** — surface it back to the author, do NOT try to strip silently.

**Section-aware concatenations only** — `description` = `feature.md` Objective + `## Workflow` heading + `workflow.md` body + `feature.md` In-Scope + Out-of-Scope sections (workflow injected between Objective and Scope so AC / test-scenarios can cite the scope points naturally). `assumptions` = `dependencies.md` + `**Open questions**` separator + `open-questions.md` (inline `— none.` form when the questions body starts with it). Everything else is byte-verbatim EXCEPT for the `strip_file_paths()` pass.

### 4. Grouped MCP calls — one `feature_upsert_bundle` per resolved `list_name`

Group features by their resolved `list_name` (from step 3(b) above). Emit **one MCP call per group** — the `solution_slug` parameter carries the List name for that batch. All features in the same group land under the same MC List (find-or-create by name). task-mcp requires no change: it already uses `solution_slug` verbatim as the List name for find-or-create.

```
# Example — 10 features resolving to 3 distinct list_names → 3 MCP calls

mcp__task-mcp__feature_upsert_bundle(
  solution_id = <from project.json>,
  solution_slug = "Supplier Management",   // ← resolved list_name for this group
  features = [
    {
      feature_id: "FEAT-AUTH-001",
      slug: "user-auth",
      initiative: "user-portal",
      task_object_id: "<from frontmatter, if present>",  // omit for create

      // The six BA-owned tab fields — passthrough / two-merge output from step 3(b).
      title:               "<frontmatter.title of feature.md, e.g. 'Supplier Onboarding'>",
      description:         "<feature.md Objective + '\n\n## Workflow\n\n' + workflow.md body + '\n\n' + feature.md In-Scope+Out-of-Scope — the reordering puts scope AFTER workflow so AC / test-scenarios can cite it naturally>",
      business_rules:      "<business-rules.md body verbatim>",
      acceptance_criteria: "<acceptance-criteria.md body verbatim>",
      nfrs:                "<nfrs.md body verbatim, or ''>",
      test_scenarios:      "<test-scenarios.md body verbatim, or ''>",
      assumptions:         "<dependencies.md + '\n\n**Open questions**\n\n' + open-questions.md, OR '\n\n**Open questions** ' + '— none. <reason>' when there are no questions — matches v2 shape>",

      // Metadata — populates task.metadata for downstream flows (dev:build dep check, etc.)
      metadata: {
        externalId:          "FEAT-AUTH-001",
        externalInitiative:  "user-portal",
        externalSlug:        "user-auth",
        dependsOnFeatureIds: ["FEAT-USER-001"],
        useCases:            ["AUTH-UC-01", "AUTH-UC-02"],
      },

      status: "todo",
      priority: "..."
    },
    ...
  ]
)

# ... then repeat for the next group:
mcp__task-mcp__feature_upsert_bundle(
  solution_id = <from project.json>,
  solution_slug = "Compliance Review",     // ← next resolved list_name
  features = [ ... features in this group ... ]
)

# ... etc, one call per unique list_name.
```

**Grouping is deterministic** — features iterate in a stable order (`feature_index.md` row order), so groups are formed by first-appearance of each `list_name`. This keeps push logs and MC List creation order predictable across runs.

**Do NOT send** — these fields are legacy and reserved for MC-specific renders that we no longer duplicate from BA output:

- `scope`, `dependencies`, `open_questions` — their content already lives inside `description` and `assumptions` respectively.
- `technical_flow`, `journeys` — MC's Execution Flow tab can be repopulated later via a targeted structured push if needed; the mermaid diagram in `description` covers the Description-tab render.

**Field-to-tab map:**

| Field | MC Tab | Source |
|---|---|---|
| `description` | Description | `feature.md` Objective + `workflow.md` (Workflow section + mermaid) + `feature.md` In-Scope + Out-of-Scope, joined at push. Order: Objective → Workflow → In Scope → Out of Scope. |
| `business_rules` | Business Rules | `business-rules.md`, verbatim |
| `acceptance_criteria` | Acceptance Criteria | `acceptance-criteria.md`, verbatim |
| `nfrs` | NFRs | `nfrs.md`, verbatim |
| `test_scenarios` | Test Scenarios | `test-scenarios.md`, verbatim |
| `assumptions` | Dependencies (tab labelled Dependencies in UI) | `dependencies.md` (Depends on + Assumptions) + `open-questions.md` (Open questions bullets), joined at push |
| `implementation_details` | Implementation | Not written here — `feature_update_implementation` writes it after `/tl:compose` produces `tl-plan.md`. |
| — | (no tab) | `implementation-plan.md` and `status.md` are local-only, never pushed. |

Response per feature: `{slug, feature_id, task_object_id, task_number, version, action ('created' | 'updated' | 'recreated'), ok}`. `recreated` means the cached `task_object_id` no longer existed in MC (deleted server-side) so a new task was created; the response also carries `previous_task_object_id`.

### 5. Write-back — patch feature.md frontmatter

For each `ok:true` result whose `action` is `'created'` or `'recreated'`: patch `context/features/<slug>/feature.md`'s YAML frontmatter to set `jetrix_task_id: <task_number>` and `jetrix_task_object_id: <task_object_id>`. (`recreated` means the previously-cached task was deleted server-side and a new one was made — overwrite the stale ids exactly like a first-time create.) Use `sed` via Bash — do NOT re-Read the file just to write it back.

### 6. Update `context/features/feature-index.md`

Add/update the `Task ID` column so rows show `TASK-<taskNumber>` next to each feature slug. (This file is scope-stage; push it separately via `/jetrix:push scope` after — sync-state will pick up the change.)

### 7. Update `.jetrix/cache/sync-state.json`

**MERGE, do not replace.** Read the current file (contains scope/context/other keys), set/update only the `tasks/<feature_id>` keys you just pushed, and write the merged object back. Under `tasks/<feature_id>`, record:
```json
{
  "taskNumber": 42,
  "taskObjectId": "<oid>",
  "slug": "user-auth",
  "contentHash": "<sha256 from step 2>",
  "version": <from response>,
  "lastPushed": "<iso>"
}
```

Report per-feature: `created` / `updated` / `recreated` (previous task was gone server-side; a new task was created and the cached ids replaced) / `skipped (unchanged)` / `failed`.

## Stage: `task` (implemented — uses task-mcp)

Ad-hoc task push. Unlike `feature`, which is tied to the BA 6-file folder layout, `task` accepts any `.md` file with the shape below and creates ONE MC Task per file. Target defaults to the solution's List (same as `feature`), or you can point at any List or Sprint.

### 1. Parse the arguments

```
/jetrix:push task [<path>] [--list=<name|id>] [--sprint=<id>]
```

- `<path>` (optional):
  - Omitted → walk `tasks/**/*.md` under `project_root`.
  - `.md` file → push that one file.
  - Directory → walk `<dir>/**/*.md`.
- `--list=<name>` OR `--list=<24-hex-oid>` (optional): target MC List. If name doesn't exist, it's created. If oid, must exist.
- `--sprint=<24-hex-oid>` (optional): target Sprint by _id.
- `--list` and `--sprint` are **mutually exclusive**. If neither, defaults to the solution's List named `solutionSlug`. Note: `push feature` no longer uses a single per-solution List — it groups features into per-scope-module Lists. For ad-hoc `push task`, `solutionSlug` remains the default catch-all List so unbucketed tasks are still discoverable.

Detect oid vs name via the regex `^[0-9a-fA-F]{24}$`.

### 2. File contract

Each task `.md` MUST have YAML frontmatter:

```yaml
---
feature_id: TASK-LOGIN-BUG        # required — natural key. Reused across pushes → idempotent update.
slug: login-bug                    # required — short kebab-case label
title: Fix login redirect loop     # optional — falls back to H1 line of body
status: todo                       # optional — defaults to `todo` on create; passthrough on update
priority: high                     # optional — M/S/C/W or low/medium/high/critical
initiative: q3-hotfixes            # optional — grouping label
jetrix_task_id: 42                 # write-back after first push (task_number)
jetrix_task_object_id: 68f2...     # write-back after first push (MC _id)
---
```

Body → sent as `description` verbatim (frontmatter stripped, H1 title line stripped if present).

Files missing `feature_id` are **rejected** — report `error: "missing feature_id in frontmatter"` and skip. This is the identity anchor; auto-generating from filename creates silent duplicates.

### 3. Walk + hash — Bash only

```bash
#!/usr/bin/env bash
set -e
PROJECT_ROOT="<absolute project_root>"
cd "$PROJECT_ROOT"

# Target set:
#   - explicit .md file: just that one
#   - directory: <dir>/**/*.md
#   - omitted: tasks/**/*.md
TARGET="${1:-tasks}"

if [[ -f "$TARGET" && "$TARGET" == *.md ]]; then
  FILES=("$TARGET")
else
  mapfile -t FILES < <(find "$TARGET" -type f -name "*.md" 2>/dev/null | sort)
fi

for f in "${FILES[@]}"; do
  size_bytes=$(wc -c < "$f")
  size_kb=$(( (size_bytes + 1023) / 1024 ))
  hash=$(sha256sum "$f" | cut -d' ' -f1)
  echo "$f|$size_kb|$hash"
done
```

Parse into `[{path, size_kb, content_hash}]`.

### 4. Parse frontmatter + body — one Read per file

Task files are small (a few KB each). Reading them is fine — bytes DO enter Claude's context here because we need to extract fields.

For each `.md`:
- Split off the YAML block between the first two `---` fences → parse it.
- Body = everything after the closing `---`.
- If body's first non-empty line is `# <heading>`, strip it and use as fallback title.
- Compose the payload item:

```
{
  feature_id:  <frontmatter.feature_id>,   // required
  slug:        <frontmatter.slug>,          // required
  title:       <frontmatter.title || H1 || slug>,
  description: <body after H1 strip>,
  status:      <frontmatter.status>,
  priority:    <frontmatter.priority>,
  initiative:  <frontmatter.initiative>,
  task_object_id: <frontmatter.jetrix_task_object_id, if present>,
  expected_version: <sync-state.version, if present>
}
```

Skip a file when `sync-state[<relative-path>].contentHash === current contentHash` (unchanged).

### 5. Single MCP call — `task_upsert_bundle`

```
mcp__task-mcp__task_upsert_bundle(
  solution_id   = <from project.json>,
  tasks         = [<payloads from step 4>],
  // Exactly one of the following (or none — falls back to solution_slug list):
  list_id       = <if --list=<oid>>,
  list_name     = <if --list=<name>>,
  sprint_id     = <if --sprint=<oid>>,
  solution_slug = <from project.json>    // fallback when no target flag given
)
```

Response per task: `{slug, feature_id, task_object_id, task_number, version, action ('created' | 'updated' | 'recreated'), ok}`.

### 6. Write-back — patch each .md's frontmatter

For every `ok:true` result whose `action` is `created` or `recreated`: `sed`-patch the task's own frontmatter to set `jetrix_task_id: <task_number>` and `jetrix_task_object_id: <task_object_id>`. Do NOT re-Read the file just to write it.

### 7. Update `.jetrix/cache/sync-state.json`

**MERGE, do not replace.** Read the current file first (contains scope/context/feature/other keys). For each pushed task, set the key `tasks/<relative-path>` to:

```json
{
  "taskNumber": <from response>,
  "taskObjectId": "<from response>",
  "featureId": "<feature_id>",
  "slug": "<slug>",
  "contentHash": "<sha256 from step 3>",
  "version": <from response>,
  "lastPushed": "<iso>"
}
```

Note the sync-state key is the file path, not `tasks/<feature_id>` — that keeps task-stage entries distinct from feature-stage entries, so a task file at `tasks/foo.md` and a feature folder at `context/features/foo/` never collide.

### 8. Report

```
✓ Pushed 3 tasks to List 'sprint-q3-hotfixes' (Solution: LarkIQ).

  tasks/login-bug.md              → TASK-42 (created)
  tasks/session-timeout.md        → TASK-43 (updated, v2)
  tasks/other.md                  → skipped (unchanged)

Uploaded:  2    Skipped:  1    Failed:  0
```

Failed pushes list each with its error (missing feature_id, version conflict, id mismatch, etc.).

## Stage: `implementation` (implemented — uses task-mcp)

TL runs this AFTER `/tl:compose` writes per-feature `tl-plan.md` files (the buildable 9-section technical spec). Each MC Task's `implementationDetails` gets **that one file's body verbatim** — no concatenation, no unit-file walking, no manifest degradation. `/tl:compose` is responsible for producing a self-contained document sized under Mission Control's 60 KB cap; this stage only ships what compose produced. Status flips to `READY_FOR_DEV`. Does NOT touch BA-owned body fields.

If a feature folder has no `tl-plan.md`, this stage skips it with a clear message pointing the user at the right recovery command. Two cases:

- **This teammate hasn't composed yet locally** → run `/tl:compose <slug>` to generate `tl-plan.md` from the local graph.
- **The feature's `tl-plan.md` was pushed by a different teammate and this workspace hasn't pulled it** → run `/jetrix:pull task <ref>` (or `/jetrix:pull scope`) to fetch the composed plan from Jetrix.

Never compose silently, never guess, never fall back to the old concat-of-units mode.

### 2. Walk feature folders that have `tl-plan.md`

```bash
for dir in context/features/*/; do
  [[ -f "$dir/tl-plan.md" ]] || continue
  slug=$(basename "$dir")
  echo "$slug"
done
```

A feature folder with a `feature.md` but no `tl-plan.md` means either `/tl:compose` hasn't run locally for this feature, or the composed plan lives on Jetrix but hasn't been pulled. Report the skip explicitly with both recovery paths:

```
[skip] context/features/<slug>/ — no tl-plan.md.
       Run one of:
         /tl:compose <slug>        (compose from the local graph)
         /jetrix:pull task <slug>  (pull an existing plan from Jetrix)
```

### 3. Per folder — read frontmatter, read the plan, size-check

For each feature slug:

**(a) Read `feature.md` frontmatter** — get `feature_id` and `jetrix_task_object_id`. Missing task-object-id → skip with "Push feature first before implementation" (this stage never creates tasks).

**(b) Read `tl-plan.md` body verbatim** — this is the payload. Strip only the YAML frontmatter; every other character (including code fences, tables, and cross-references) goes to MC unchanged.

**(c) CRLF-safe frontmatter strip.**

Delivery-OS `.md` files are CRLF on Windows. A frontmatter strip that compares a line to `---` silently fails against `---\r`, leaving `doc_type:` / `schema_version:` / `produced_by:` metadata visible in the pushed payload where a downstream reader interprets it as spec content. Normalise line endings **before** stripping:

```python
s = io.open(path, encoding='utf-8', newline='').read().replace('\r\n', '\n')
if s.startswith('---\n'):
    end = s.find('\n---\n', 3)
    if end != -1:
        s = s[end + 5:]
payload = s.lstrip('\n')   # drop any leading blank lines left by the strip
```

Verify the payload contains zero `\r` and zero leaked frontmatter keys before pushing.

**(d) Enforce the size cap.** Mission Control's Joi validator on `implementationDetails` rejects anything longer than **60 000 characters** — the response is `{ok: false, updated: 0, error: "\"implementationDetails\" length must be less than or equal to 60000 characters long"}` and **nothing is written**.

`/tl:compose` is supposed to keep `tl-plan.md` at ~10–15 KB and refuse to write above 60 KB. This stage is the last line of defence:

- If `len(payload) > 60000` → **skip this feature and fail loud**. Do NOT truncate. Report:
  ```
  [skip] FEAT-XXX-YY — tl-plan.md is <N> chars, cap is 60000.
                     Split the feature via /tl:compose or /ba:features and re-run.
  ```
- If `55000 < len(payload) ≤ 60000` → push, but warn: `[warn] FEAT-XXX-YY — <N> chars, near the 60 KB cap`.

**(e) Compute hash + skip-unchanged.**

Compute sha256 of the final payload (frontmatter-stripped, CRLF-normalised). Compare against `sync-state.json[tasks/<feature_id>].implementation_hash`:

- Match → skip, print `[skip] TASK-<n> <slug> — unchanged (hash=<sha16>)`, do not call the MCP.
- Mismatch (or missing) → push (step 4), then update sync-state on success (step 5).

### 4. Single MCP call — use the dedicated implementation tool

**Use `feature_update_implementation`, NOT `feature_upsert_bundle`.** This tool's Pydantic schema accepts ONLY `task_object_id`, `implementation_details`, and `status`. It ignores every other field, so it is IMPOSSIBLE to accidentally clobber BA-owned tabs (description / businessRules / acceptanceCriteria / assumptions / nfrs / testScenarios). Do not fall back to `feature_upsert_bundle` for implementation pushes — that tool accepts BA fields and could wipe them if empty strings sneak in.

```
mcp__task-mcp__feature_update_implementation(
  solution_id = <from project.json>,
  features = [
    {
      feature_id: "FEAT-CLSF-01",                   // reporting only
      slug: "document-classification-extraction",   // reporting only
      task_object_id: "<from feature.md>",           // REQUIRED — this tool never creates
      implementation_details: "<tl-plan.md body from step 3b/c>",
      status: "readyForDev"
    }
  ]
)
```

Response per feature: `{slug, feature_id, task_object_id, task_number, version, ok}`.

Missing `task_object_id` returns `{ok: false, error: "…run /jetrix:push feature first"}` — the tool never creates tasks.

**ALWAYS check the per-feature `ok` field — never infer success from the call returning.** A rejected write still returns a normal-looking response envelope with `updated: 0` and `ok: false` on the individual row. Report `ok:false` rows as failures and leave their sync-state untouched so the next push retries them.

> **Known task-mcp defects (as of 2026-07-27) — do not misread these as your own failure:**
> - **Read tools return empty for tasks that demonstrably exist.** `feature_pull_bundle`, `feature_list_bundle` and `get_task_by_id_or_number` all return nothing for a Solution whose tasks are writable by object id; a raw-oid lookup fails upstream with `"Please select a solution to continue"`, suggesting a missing solution-context header on the read path. **Do not use a read tool to verify a push, and do not treat an empty read as evidence the write failed.** Verify from the write response's `ok`/`updated`/`task_number` instead — `task_number` is echoed from the stored record, so its presence proves the task was found.
> - **`version` comes back `null`** on every write, where scope-mcp and context-mcp both return an integer. Does not appear to affect the write; record `null` in sync-state rather than inventing a number.

### 5. Update sync-state — **incrementally, after EACH successful push**

**Do NOT batch sync-state writes to the end of the run.** For every feature whose `feature_update_implementation` returned `ok: true`, immediately:

1. Read `<workspace_root>/.jetrix/cache/sync-state.json` (MERGE, not replace).
2. Set the `implementation_hash` on that ONE feature's `tasks/<feature_id>` entry.
3. Write the merged object back.

Then move on to the next feature. This runs sync-state one write per successful push, not one at the end.

**Why incremental matters.** Implementation pushes relay 10–15 KB per feature through session context (the tool takes the spec as an inline string). On a 10-feature module that's ~150 KB total, and it's not unusual for the run to stop mid-way (session limits, network, an ambiguous input the agent surfaces). If sync-state is batched to the end and the run stops at 5/10:

- Sync-state has ZERO entries → next run re-pushes all 10, even the 5 that landed cleanly.
- 5 wasted network calls and each identical write bumps the Task's `version` field.

With incremental updates: the same interrupted run leaves sync-state with 5 entries. Next run computes fresh hashes, sees 5 matches, skips those, and pushes only the remaining 5. Clean resume.

**Report format.** Print progress per feature as you go, not one summary at the end:

```
[1/10] TASK-11 opening-balance-import      pushed   (12.4 KB, hash=<sha16>)
[2/10] TASK-14 leave-balance-administration skip     (unchanged, hash=<sha16>)
[3/10] TASK-16 leave-request-submission    pushed   (14.1 KB, hash=<sha16>)
[4/10] TASK-19 approvals-workflow          skip     (no tl-plan.md — run /tl:compose)
[5/10] TASK-22 monster-report              skip     (67.3 KB > 60 KB cap — split the feature)
```

Final report is a two-line summary — `updated: N`, `skipped: M`, `failed: K`, plus a list of any skips/failures with their reason.

### 6. Never fall back to the old concat mode

If a feature has no `tl-plan.md`, this stage **must not** silently reconstruct one by concatenating BA's `implementation-plan.md` + owned units. That path produced the "reads like a business user story" content Dharma flagged. The correct recovery is: tell the user to run `/tl:compose <slug>` and stop for that feature.

## Stage: `deliverable` (pending — will use deliverable-mcp)

Not yet implemented. Same 3-phase file pattern as scope.

---

Keep it **idempotent** — a re-push of an unchanged file must be a no-op via the sync-state contentHash check. Never write duplicate FileMeta rows.
