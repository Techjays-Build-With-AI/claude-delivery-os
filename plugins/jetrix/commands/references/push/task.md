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
- `--list` and `--sprint` are **mutually exclusive**. If neither, fall through to the interactive prompt in §1a.

Detect oid vs name via the regex `^[0-9a-fA-F]{24}$`.

### 1a. Interactive target prompt (when neither `--list` nor `--sprint` is provided)

Don't silently drop tasks into a List named after `solutionSlug`. Ask the user which container to use — Lists first, then Sprints, then a "create new" option.

1. Call `mcp__task-mcp__list_all_lists(solution_id)` to fetch existing Lists (includes empty ones).
2. Call `mcp__task-mcp__list_all_sprints(solution_id)` to fetch existing Sprints.
3. Present a numbered menu:

```
Ready to push N task(s). Which container?

  Lists:
    [1] V2 Backlog         (32 tasks · existing)
    [2] Bugs               (5 tasks · existing)
    [3] <solutionSlug>     (default — will be created if missing)

  Sprints:
    [4] Sprint 12          (Active · 18 tasks)
    [5] Sprint 13          (Planned · 0 tasks)

  Other:
    [6] Create a new List  → prompt for name
    [7] Cancel

Choice:
```

4. Map the user's choice to a push target:
   - Existing List → set `list_name = <selected name>` (or `list_id = <_id>` for safety on ambiguous names)
   - Existing Sprint → set `sprint_id = <_id>`
   - Solution-slug default → set `list_name = <solutionSlug>` (find-or-create)
   - Create new → ask for name, then set `list_name = <user input>` (creates on first push)
   - Cancel → exit cleanly with `Cancelled — no tasks pushed.`
5. Also present the resolved choice back for confirmation before batching:
   ```
   Pushing 3 tasks into List "V2 Backlog" (_id: 6a61d4...). Proceed? (Y/n)
   ```
6. On `n`, restart the prompt. On `Y`, continue to §2.

### 1b. Permission-aware halt

If any downstream MCP call returns `{ok: false, error: "permission_denied", required_permission: "<name>"}`, halt cleanly:

```
✗ Push failed — your role is missing permission '<name>'.
  Ask your Techjays admin to grant it, then re-run /jetrix:push task.
```

Do not retry. Do not fall back to a different target. Do not swallow the error — surface it clearly with the exact permission name so the user knows what to ask for.

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

### 3. Walk + parse + assemble every task — ONE Bash+Python call

**Do NOT `Read` each task file individually.** Invoke the plugin's script once — it walks the target set, extracts frontmatter + body, applies the `title` fallback chain, skips unchanged files against sync-state, and emits ONE JSON blob ready for `task_upsert_bundle`.

```bash
ASSEMBLED="<workspace_root>/.jetrix/cache/.push-tasks.json"
mkdir -p "$(dirname "$ASSEMBLED")"

python "$CLAUDE_PLUGIN_ROOT/scripts/assemble-tasks.py" \
  --project-root "<absolute project_root>" \
  --sync-state   "<workspace_root>/.jetrix/cache/sync-state.json" \
  --output       "$ASSEMBLED" \
  --target       "<TARGET>"      # default: tasks   (or explicit file / directory)
```

`<TARGET>` mirrors the arg parse in §1 — omitted uses `tasks/`, otherwise a single `.md` file or a directory.

Claude reads the ONE JSON blob:

```json
{
  "tasks":              [<payload>, ...],
  "skipped_unchanged":  ["tasks/foo.md", ...],
  "halts":              [{"path": "tasks/bar.md", "reason": "missing feature_id in frontmatter"}]
}
```

- **Halts** → report each and skip that file. Do not silently push; the halt reason is authoritative (missing `feature_id` = "identity anchor" per §2's contract).
- **Skipped unchanged** → include in the final report only.
- **Tasks** → payloads shaped exactly for `task_upsert_bundle`. Each carries an internal `_local_content_hash` + `_local_rel_path` — leave them in place; `apply-task-responses.py` reads them for sync-state.

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

### 6. Apply response — write-back frontmatter + sync-state (ONE Bash+Python call)

Dump the `task_upsert_bundle` response to disk and invoke the plugin's apply script — patches each task file's frontmatter (for `created`/`recreated` rows) and updates sync-state, merge-safe.

```bash
RESPONSES="<workspace_root>/.jetrix/cache/.push-tasks-responses.json"
mkdir -p "$(dirname "$RESPONSES")"

cat > "$RESPONSES" <<'JETRIX_RESP_EOF'
[
  {"_local_rel_path":"tasks/login-bug.md","slug":"login-bug","feature_id":"TASK-LOGIN-BUG","task_object_id":"6a61...","task_number":42,"version":1,"action":"created","ok":true,"_local_content_hash":"<sha256 from assemble step>"},
  ...one row per task...
]
JETRIX_RESP_EOF

python "$CLAUDE_PLUGIN_ROOT/scripts/apply-task-responses.py" \
  --responses    "$RESPONSES" \
  --project-root "<absolute project_root>" \
  --sync-state   "<workspace_root>/.jetrix/cache/sync-state.json"

rm -f "$RESPONSES"
```

The script:
- Patches each `<rel-path>` .md's frontmatter — sets `jetrix_task_id` + `jetrix_task_object_id` for rows whose `action` is `created` or `recreated` (regex upsert, no Read).
- Writes per-task entries under `tasks/<rel-path>` in sync-state (file-path-keyed, not feature-id-keyed — keeps task-stage entries distinct from feature-stage entries under the same `tasks/` namespace).
- Prints per-task status to stdout.

### 8. Report

```
✓ Pushed 3 tasks to List 'sprint-q3-hotfixes' (Solution: LarkIQ).

  tasks/login-bug.md              → TASK-42 (created)
  tasks/session-timeout.md        → TASK-43 (updated, v2)
  tasks/other.md                  → skipped (unchanged)

Uploaded:  2    Skipped:  1    Failed:  0
```

Failed pushes list each with its error (missing feature_id, version conflict, id mismatch, etc.).

