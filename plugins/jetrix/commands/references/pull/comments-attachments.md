## Shared sub-flow: comments + attachments

Materializes `comments.md` and `attachments/` **next to the task they belong
to**. Invoked by the `task`, `list`, and `sprint` stages after their own
materialization step has run. Not a stage of its own — never routed to
directly from `/jetrix:pull`.

**Target directory per task kind** — this is the only thing that varies:

| Task kind | `--target-dir` |
|---|---|
| BA feature | `features/<slug>/` |
| Sub-task | `features/<slug>/subtask/<repo>/` |
| Bug / story / ad-hoc task | `tasks/<slug>/` |

### Preconditions

The caller already knows each task's `task_number` **and** `task_object_id`
(both are written into `feature.md` / `tasks/<slug>.md` frontmatter by the
materializer that just ran). Pass **both** — `task_comments_pull` and
`task_attachments_pull` then skip their id-resolution lookup entirely.

### 1. Fetch — two MCP calls per task

```
mcp__task-mcp__task_comments_pull(
  solution_id    = <from project.json>,
  task_number    = <jetrix_task_id>,
  task_object_id = <jetrix_task_object_id>
)

mcp__task-mcp__task_attachments_pull(
  solution_id    = <from project.json>,
  task_number    = <jetrix_task_id>,
  task_object_id = <jetrix_task_object_id>
)
```

**Both returning empty is the common case** — most tasks have no discussion.
When `comments.count == 0` and `attachments.count == 0`, skip straight to the
next task. Do NOT create the folder, do NOT run the script.

### 2. Materialize — one Bash call per task

```bash
BUNDLE="<workspace_root>/.jetrix/cache/.pull-comments-<task_number>.json"
MANIFEST="<workspace_root>/.jetrix/cache/.attachments-<task_number>.curl"
mkdir -p "$(dirname "$BUNDLE")"

cat > "$BUNDLE" <<'JETRIX_COMMENTS_EOF'
{
  "task_number":    <task_number>,
  "task_object_id": "<task_object_id>",
  "title":          "<task title>",
  "comments":       <task_comments_pull response, verbatim>,
  "attachments":    <task_attachments_pull response, verbatim>
}
JETRIX_COMMENTS_EOF

python "$CLAUDE_PLUGIN_ROOT/scripts/materialize-comments.py" \
  --bundle            "$BUNDLE" \
  --target-dir        "<absolute target dir from the table above>" \
  --sync-state        "<workspace_root>/.jetrix/cache/sync-state.json" \
  --download-manifest "$MANIFEST"

# Attachment bytes — GCS straight to disk, never through Claude's context.
# The manifest only exists when there are files still to fetch.
[ -f "$MANIFEST" ] && curl --parallel --parallel-max 8 -sSfL -K "$MANIFEST"

rm -f "$BUNDLE" "$MANIFEST"
```

The script writes `comments.md` only when the task has comments and
`attachments.md` + `attachments/` only when it has attachments, so a quiet
task leaves no trace on disk. Both files carry `readonly: true` in
frontmatter — that marker is what stops `/jetrix:push` from ever sweeping
them back up to MC.

Already-downloaded files are not re-fetched: a replaced attachment gets a new
`attachmentNumber`, hence a new local filename.

### 3. Report

Fold into the stage's own report — one extra line per task that had anything:

```
  + comments.md (7 comments, 2 unresolved), attachments/ (2 files)
```

### Batching note (`list` / `sprint`)

Steps 1–2 run per task. For a large List, run the fetch for all tasks first,
then one Bash call per task that actually had content. Tasks with nothing are
never touched, so a List of 40 quiet tasks costs 80 cheap reads and zero
writes.
