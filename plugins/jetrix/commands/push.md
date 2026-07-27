---
description: Publish local delivery-os work up to Jetrix via the stage-specific MCP. Argument selects which stage to sync — `scope` (BA outputs → scope-mcp), `context` (TL graph → context-mcp), `tasks` (feature tasks → task-mcp), `deliverable` (client HTMLs → deliverable-mcp). Uploads use the direct-to-GCS pattern (server brokers signed URLs, local bash + curl streams bytes from disk straight to GCS), so pushes never route file bytes through Claude's context — a 100-file push is as fast as a 1-file push.
argument-hint: "<stage> [<filename>]"
---

# /jetrix:push

Publish local delivery-os work to Jetrix. The first argument names the **stage** — this decides which local paths get scanned and which MCP handles the sync:

| Stage | MCP | What it pushes |
|---|---|---|
| `scope` | `scope-mcp` | BA outputs — `ba-output/*.md`, `shared-context/*.md`, `context/features/feature-index.md` |
| `context` | `context-mcp` | TL knowledge graph — 3 knowledge indexes (env-scoped) |
| `feature` | `task-mcp` | Per-feature MC Tasks — creates ONE Task per `context/features/<slug>/` folder |
| `implementation` | `task-mcp` | TL plan → each Task's Implementation tab (`implementationDetails`), status → `READY_FOR_DEV` |
| `deliverable` | `deliverable-mcp` | Client HTMLs — `doc-output/*.html` |

Every stage uses a **three-phase direct-to-GCS pattern** on its MCP (`*_prepare_push` → local `curl` PUTs → `*_finalize_push`) so the plugin does at most 2 MCP calls + 1 Bash call per push, regardless of file count. **File bytes never enter Claude's context**; they go straight from local disk to GCS via signed URLs (same pattern the UI's KnowledgeHubService uses).

This document covers all four stages. **Scope (the BA sync) is the currently-implemented one.** The others land as their MCPs come online.

---

## 0. Preflight — resolve the delivery-os workspace

**This command operates on the delivery-os container folder that `/jetrix:init` bound to a Jetrix Solution — NOT on your current directory.** Resolve the workspace FIRST:

1. Walk up from `$PWD` looking for **`.jetrix/project.json`** (up to 3 parent levels). If missing everywhere → stop and tell the user to run `/jetrix:init <projectId | slug>` first.
2. Read `solutionId` + `solutionSlug` from it. Note the folder that CONTAINS `.jetrix/` as **`workspace_root`** — that's the top of the delivery-os workspace, and it's where `.jetrix/cache/sync-state.json` lives.
3. The delivery-os container is the sibling folder `<workspace_root>/<solutionSlug>/` (e.g. if `solutionSlug: "larkiq"` then `larkiq/` next to `.jetrix/`). Note this as **`project_root`** — every content file walk below is relative to it.
4. Verify the container exists. If missing → tell the user to run `/delivery-os:init`.

> **Directory contract (referenced throughout this doc):**
> ```
> <workspace_root>/
> ├── .jetrix/
> │   ├── cache/sync-state.json     ← sync-state ALWAYS lives here
> │   └── project.json
> └── <solutionSlug>/               ← project_root
>     ├── ba-output/
>     ├── shared-context/
>     ├── context/
>     └── ... (NEVER contains a .jetrix/ folder)
> ```
> **`.jetrix/` and the solution folder are siblings.** Never create `.jetrix/` inside the solution folder. Every `sync-state.json` reference below resolves to `<workspace_root>/.jetrix/cache/sync-state.json` — NEVER inside `<project_root>/`.

## 1. Parse the stage argument

```
/jetrix:push <stage> [<filename>]
```

- `<stage>` (required): `scope` | `context` | `feature` | `implementation` | `deliverable`. If missing or unknown, print the table above and stop.
- `<filename>` (optional): scope only — push a single file at that relative path instead of the whole stage.

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
      expected_version: <sync-state.version, if any> // enables optimistic locking
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

Pushes the 3 architecture indexes env-scoped:
- `context/frontend/page-index.md`
- `context/backend/endpoint-index.md`
- `context/database/entity-index.md`

**Env is driven by envConfig** — every project has a list of envs (e.g. `["dev", "staging", "prod"]` or `["dev", "live"]`). Pass `--env=<name>` to select any of them. If omitted, defaults to the **first env in the chain** (the working / in-flight env — usually `dev`). The **last env in the chain** is the baseline / shared truth (`main`, `prod`, `live` — whatever the team named it) and is what `/jetrix:pull context` returns by default.

To resolve the env list, call `project-mcp.project_get_env_configs(project_id)` — the response's `environment` fields form the chain. The plugin can validate `--env=<name>` against that list.

Legacy `--baseline` is still accepted as an alias for "push to the last env in the chain."

### 2. Collect the 3 index files — Bash only

Plan v3 §2.7 is explicit: **exactly three files go to GCS** — the three
layer indexes. Per-unit files (individual page / endpoint / entity `.md`s
under `context/{frontend,backend,database}/**/`) are NOT pushed here;
their content reaches Jetrix by being concatenated into
`task.implementationDetails` via `/jetrix:push implementation` (§2.9),
so the dev agent gets one self-contained buildable spec per feature Task.

```bash
#!/usr/bin/env bash
set -e
PROJECT_ROOT="<absolute project_root>"
cd "$PROJECT_ROOT"

# Exactly three files. No walk, no recursion.
CANDIDATES=(
  "context/frontend/page-index.md"
  "context/backend/endpoint-index.md"
  "context/database/entity-index.md"
)

for f in "${CANDIDATES[@]}"; do
  [[ -f "$f" ]] || continue
  size_bytes=$(wc -c < "$f")
  size_kb=$(( (size_bytes + 1023) / 1024 ))
  hash=$(sha256sum "$f" | cut -d' ' -f1)
  echo "$f|$size_kb|$hash"
done
```

Parse output into `[{path, size_kb, content_hash}]`. Missing indexes
skip silently (an early workspace may only have one or two).

Do NOT `Read` any of these files. Do NOT enumerate per-unit files under
`context/frontend/pages/`, `context/backend/domains/`, or
`context/database/entities/` — those belong in `/jetrix:push
implementation`, not here. Pushing them from this command creates
scattered FileMeta rows in Jetrix that duplicate what the Task's
Implementation tab already contains.

### 3. Resolve env + skip unchanged

- Resolve env from args:
  - If `--env=<name>` present → use it verbatim after validating against the project's envConfig list.
  - Else if `--baseline` present → `env = <last env in envConfig chain>` (the shared truth — `main` / `prod` / `live`).
  - Else if the workspace has NO `context/features/*/implementation-plan.md` files → **auto-baseline**: `env = <last env in envConfig chain>`. Rationale: with no `/tl:plan` output yet, the indexes describe as-shipped code (produced by `/tl:map`), so they belong in the shared baseline env, not the working env. Print a one-line note: *"No feature plans found — pushing to baseline `<env>`. Pass `--env=<name>` to override."*
  - Else → `env = <first env in envConfig chain>` (the working env, usually `dev`).
- Read `<workspace_root>/.jetrix/cache/sync-state.json`. Look at `context/<path>[<env>]` — skip files whose `contentHash` matches.

### 4. Phase 1 — prepare (one MCP call)

```
mcp__context-mcp__context_prepare_push(
  solution_id=<from project.json>,
  docs=[
    { path: "context/frontend/page-index.md",   mime_type: "text/markdown" },
    { path: "context/backend/endpoint-index.md", mime_type: "text/markdown" },
    { path: "context/database/entity-index.md",  mime_type: "text/markdown" }
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
    ...
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

Creates ONE MC Task per `context/features/<slug>/` folder. All FEATURE tasks for a Solution land under a single MC List named after `solutionSlug`. First push = POST (create); repush = PUT (update by `jetrix_task_object_id` stored in `feature.md` frontmatter).

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

### 3. Per feature — read + parse (canonical section order)

For each folder that needs push (content_hash differs from `sync-state.json[<slug>].contentHash`):

**Read `feature.md`**, extract:
- **Frontmatter** (YAML between `---` fences): `feature_id`, `initiative`, `priority`, `status`, `jetrix_task_id`, `jetrix_task_object_id`, `slug`
- **`# <title>`** (H1 line) — title
- **Body split on `\n## `** — section content per header

Compose Task fields (H2 headers PRESERVED in multi-section fields):

```
title             = "<H1 content>"
description       = "## Summary\n<content>\n\n## Business Objective\n<content>\n\n## Users\n<content>\n\n## User Value\n<content>"
scope             = "## In Scope\n<content>\n\n## Out of Scope\n<content>"
assumptions       = "<Assumptions section content, H2 stripped>"
business_rules    = "<Related Business Rules section content, H2 stripped>"
```

**Read `workflow.md`** — split on `## `:
```
technical_flow    = "<Technical Flow section content>"
journeys          = "<User Journeys section content>"
```

**Read `acceptance-criteria.md`, `dependencies.md`, `open-questions.md`, `status.md`** — full body (minus H1 title line) into the respective field. `status.md` parse `# Status: X` + `Progress: N%`.

### 4. Single MCP call — `feature_upsert_bundle`

```
mcp__task-mcp__feature_upsert_bundle(
  solution_id = <from project.json>,
  solution_slug = <from project.json>,
  features = [
    {
      feature_id: "FEAT-AUTH-001",
      slug: "user-auth",
      initiative: "user-portal",
      task_object_id: "<from frontmatter, if present>",  // omit for create
      title: ..., description: ..., scope: ...,
      assumptions: ..., business_rules: ...,
      technical_flow: ..., journeys: ...,
      acceptance_criteria: ..., dependencies: ..., open_questions: ...,
      status: "todo",
      priority: "..."
    },
    ...
  ]
)
```

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

## Stage: `implementation` (implemented — uses task-mcp)

TL runs this AFTER `/tl:plan` produces per-feature `implementation-plan.md` PLUS the per-unit files under `context/{frontend,backend,database}/`. Each MC Task's `implementationDetails` gets **the feature's plan concatenated with every unit that feature owns** (verbatim, no rephrasing) so the dev-agent (Stage 4) has a self-contained buildable spec in one field. Status flips to `READY_FOR_DEV`. Does NOT touch BA-owned body fields.

### 2. Walk feature folders that have `implementation-plan.md`

```bash
for dir in context/features/*/; do
  [[ -f "$dir/implementation-plan.md" ]] || continue
  slug=$(basename "$dir")
  echo "$slug"
done
```

### 3. Per folder — read frontmatter, plan, and owned units

For each feature slug:

**(a) Read feature.md frontmatter** — get `feature_id` and `jetrix_task_object_id`. Missing task-object-id → skip with "Push feature first before implementation".

**(b) Read `implementation-plan.md`** body (the feature's high-level plan).

**(c) Resolve owned units from the 3 layer indexes** — this is the enrichment step.

Each index has a DIFFERENT column layout — do NOT treat them uniformly. Confirmed schemas (in this project):

| Index | Feature filter | File column | Entity chain |
|---|---|---|---|
| `context/frontend/page-index.md` | col 6 = `Used by Features` | col 8 = `Folder` | — |
| `context/backend/endpoint-index.md` | col 6 = `Used by Features` | col 7 = `File` | col 5 = `Reads/Writes Entities` (used below) |
| `context/database/entity-index.md` | *none* — features link indirectly | col 7 = `File` | col 6 = `Used by Endpoints` |

Full headers, as emitted by `tl-feature-planning` / `tl-codebase-map` (`awk -F'|'` field numbers in brackets — note the leading empty field, so **awk field = column + 1**):

```
page-index.md    | Page ID[$2] | Page[$3] | Area[$4] | Origin[$5] | Status[$6] | Used by Features[$7] | Consumes Endpoints[$8] | Folder[$9] |
endpoint-index.md| Endpoint ID[$2] | Method + Path[$3] | Domain[$4] | Called by[$5] | Reads/Writes Entities[$6] | Used by Features[$7] | File[$8] |
entity-index.md  | Entity ID[$2] | Entity[$3] | Kind[$4] | Origin[$5] | Source DATA-###[$6] | Used by Endpoints[$7] | File[$8] |
```

`page-index.md` and `entity-index.md` carry two extra columns relative to `endpoint-index.md` (`Origin`/`Status` and `Origin`/`Source DATA-###`). Getting these wrong does **not** error — it silently reads the `Origin` column as the feature filter (never matching a `FEAT-` id, so every page is dropped) and emits the `Used by Endpoints` cell as a file path. Verify the header before trusting the field numbers.

**Reverse-mapped rows.** Units produced by `/tl:map` carry `(as-built)` in their `Used by Features` cell, so a `FEAT-` filter naturally excludes them. That is correct — as-built units are not owned by any planned feature and must not be concatenated into a Task's implementation spec.

Feature ↔ entity is a **2-hop link**: feature → endpoints (via `endpoint-index`) → entities (via each endpoint row's `Reads/Writes Entities` cell). Never grep entity-index directly for a feature id — that will find nothing.

**Feature-cell matching rule.** The `Used by Features` cell can hold MULTIPLE ids, comma-separated (`FEAT-HITL-01, FEAT-SEC-01, FEAT-MTCH-01`). Match a feature anywhere in the cell, not just at the start. Use a word-boundary check like:

```bash
grep -E "\\b$FEAT\\b"
```

**Recipe — run one bash call per feature to emit the unit paths (three groups):**

```bash
FEAT="FEAT-CLSF-01"
cd "$PROJECT_ROOT"

# --- Frontend pages (features = $7, folder = $9) ---
awk -F'|' -v f="$FEAT" '
  $0 ~ /\|---/ { next }               # skip separator row. MUST be a regex literal:
                                      # the string form "\\|---" compiles to the regex |---
                                      # whose empty left branch matches EVERY line, silently
                                      # skipping the entire table and yielding zero units.
  NF < 9 { next }                     # skip non-table lines / narrower side-tables
  $2 !~ /^ *PAGE-/ { next }           # data rows only (skips header + any second table)
  {
    feats = $7; gsub(/^ +| +$/, "", feats)
    if (feats ~ ("(^|[, ])" f "([,]| *$)")) {
      folder = $9; gsub(/^ +| +$/, "", folder)
      sub(/^\.\//, "", folder)
      print "context/frontend/" folder
    }
  }' context/frontend/page-index.md

# --- Backend endpoints (features = $7, file = $8, entity ids = $6) ---
awk -F'|' -v f="$FEAT" '
  $0 ~ /\|---/ { next }
  NF < 8 { next }
  $2 !~ /^ *EP-/ { next }             # data rows only (skips header + blocked-unit side-table)
  {
    feats = $7; gsub(/^ +| +$/, "", feats)
    if (feats == f || feats ~ ("(^|[, ])" f "([,]| *$)")) {
      file = $8; gsub(/^ +| +$/, "", file)
      sub(/^\.\//, "", file)
      print "context/backend/" file
      # emit the entity ids on this row for the 2-hop entity resolution below
      ents = $6; gsub(/^ +| +$/, "", ents)
      n = split(ents, arr, /[,] */)
      for (i = 1; i <= n; i++) if (arr[i] ~ /^ENT-/) print "__ENT__" arr[i]
    }
  }' context/backend/endpoint-index.md

# --- Database entities (2-hop: use the ENT-* ids emitted above) ---
# (Separate step below; ENT ids collected from the endpoint step feed this.)
```

**Handle the 2-hop for entities.** After the awk above prints unit paths and any `__ENT__ENT-CLSF-01` markers, deduplicate the ENT ids, then look each up in `entity-index.md`:

```bash
# entity-index.md: Entity ID = $2, File = $8
awk -F'|' -v ent="$ENT_ID" '
  $0 ~ /\|---/ { next }
  NF < 8 { next }
  $2 !~ /^ *ENT-/ { next }            # data rows only
  {
    id = $2; gsub(/^ +| +$/, "", id)
    if (id == ent) {
      file = $8; gsub(/^ +| +$/, "", file)
      sub(/^\.\//, "", file)
      print "context/database/" file
    }
  }' context/database/entity-index.md
```

Loop over each unique ENT id to emit its path. Deduplicate the final list of entity paths (an entity used by 3 endpoints shows up once, not three times).

Result of step (c): three lists of file paths — `PAGES`, `ENDPOINTS`, `ENTITIES` — each a set of `context/**/*.md` paths owned by the feature. Read each file with the `Read` tool (unit files are small; a couple hundred lines each).

**Precision note for the executor:** Do NOT invent alternative filter logic or "figure out" a different chain. The three awk snippets above are the spec. If an index's column layout has drifted from what's described here, STOP and surface the discrepancy — don't guess.

**(d) Compose the concatenated `implementation_details`**:

```markdown
# Implementation Plan
<implementation-plan.md body verbatim, YAML frontmatter stripped>

---

# Frontend Pages (N)

## PAGE-XXX-YY — <title from unit file H1>
<page unit body verbatim, frontmatter stripped>

## PAGE-XXX-ZZ — <title>
<...>

---

# Backend Endpoints — grouped by Domain

## <Domain name from index row>

### EP-XXX-YY — <title>
<endpoint unit body verbatim, frontmatter stripped>

---

# Database Entities (N)

## ENT-XXX-YY — <title>
<entity unit body verbatim, frontmatter stripped>
```

Preserve unit-file cross-references (relative paths like `../../../../database/entities/*.md` and ID mentions like `EP-INTK-02`) verbatim. Dev-agent resolves them locally at build time — they're the "external contracts" this feature depends on.

**(e) Compute hash + skip decision**:
- Compute sha256 of the FULL concatenated string (not just implementation-plan.md).
- Skip if `sync-state.json[tasks/<feature_id>].implementation_hash === new hash`. This means any change to any owned unit file re-triggers a push.

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
      implementation_details: "<concatenated content from step 3d>",
      status: "readyForDev"
    }
  ]
)
```

Response per feature: `{slug, feature_id, task_object_id, task_number, version, ok}`.

Missing `task_object_id` returns `{ok: false, error: "…run /jetrix:push feature first"}` — the tool never creates tasks.

### 5. Update sync-state

**MERGE, do not replace.** Read the current file first, add/update the `implementation_hash` field on each `tasks/<feature_id>` entry you just pushed, and write the merged object back. Report: `updated: N, skipped: M`.

## Stage: `deliverable` (pending — will use deliverable-mcp)

Not yet implemented. Same 3-phase file pattern as scope.

---

Keep it **idempotent** — a re-push of an unchanged file must be a no-op via the sync-state contentHash check. Never write duplicate FileMeta rows.
