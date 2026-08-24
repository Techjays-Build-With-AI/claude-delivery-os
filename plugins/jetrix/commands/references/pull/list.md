## Stage: `list <ref>` (implemented — uses task-mcp)

Materializes every task in an MC List — both FEATURE tasks (BA feature folders) and non-FEATURE tasks (bugs, chores, ad-hoc work). `<ref>` accepts:

- A **list name** (e.g. `"Reported Issues"`, `"Supplier Management"` — use the exact List name shown in MC)
- A **MongoDB `_id`** (24-char hex)

Plugin recipe — TWO calls in parallel, one per task type:

1. **Parse `<ref>`** — 24-char hex → `list_id`; anything else → `list_name`.
2. **Fetch FEATURE tasks** — for BA-style folders:
   ```
   mcp__task-mcp__feature_pull_bundle(
     solution_id = <from project.json>,
     list_name   = "larkiq"     # OR list_id="..."
   )
   ```
   → materializes `features/<slug>/*.md` (the 8-file folder layout).
3. **Fetch non-FEATURE tasks** — for single-file tasks:
   ```
   mcp__task-mcp__task_pull_bundle(
     solution_id = <from project.json>,
     list_name   = "Reported Issues"
     # task_type omitted → returns ALL types; MC returns each type in one shot
   )
   ```

4. **Materialize both sides via the plugin scripts** — do NOT iterate features or tasks with per-file `Write` calls. Dump each MCP response to disk (Bash heredocs) then invoke the appropriate script once. Skip whichever script has no rows to write:

    ```bash
    # --- Feature side (materialize-features.py) — skip if features[] was empty ---
    FBUNDLE="<workspace_root>/.jetrix/cache/.pull-features.json"
    mkdir -p "$(dirname "$FBUNDLE")"
    cat > "$FBUNDLE" <<'JETRIX_BUNDLE_EOF'
    <paste feature_pull_bundle JSON, verbatim>
    JETRIX_BUNDLE_EOF
    python "$CLAUDE_PLUGIN_ROOT/scripts/materialize-features.py" \
      --bundle       "$FBUNDLE" \
      --project-root "<absolute project_root>" \
      --sync-state   "<workspace_root>/.jetrix/cache/sync-state.json"
    rm -f "$FBUNDLE"

    # --- Task side (materialize-tasks.py) — skip if tasks[] was empty ---
    TBUNDLE="<workspace_root>/.jetrix/cache/.pull-tasks.json"
    cat > "$TBUNDLE" <<'JETRIX_TASKS_EOF'
    <paste task_pull_bundle JSON, verbatim>
    JETRIX_TASKS_EOF
    python "$CLAUDE_PLUGIN_ROOT/scripts/materialize-tasks.py" \
      --bundle       "$TBUNDLE" \
      --project-root "<absolute project_root>" \
      --sync-state   "<workspace_root>/.jetrix/cache/sync-state.json"
    rm -f "$TBUNDLE"
    ```

    Both scripts do their own skip-unchanged (compare freshly-composed content vs on-disk); no separate hash step needed. Sync-state merges from both scripts land in the same file — merge-safe, no key collisions (features live under `tasks/<feature_id>`, tasks under `tasks/<slug>.md`).

### Non-feature task file layout (one file per task)

Write to `tasks/<slug or task-N>.md`. All tab content lands in one file:

```md
---
task_number: 230
task_object_id: 6a7c376e6a993512f7ffba90
task_type: task              # or "bug", "chore" — whatever MC returned
title: Reported issue — login redirect loop
status: inProgress
priority: high
list_id: 6a61d4b8c9e2a1d3f4e5b6c7
list_name: Reported Issues
sprint_id:                    # empty if not in a sprint
sprint_number:
metadata:                     # verbatim task.metadata as YAML
  externalId: TASK-LOGIN-BUG
  externalInitiative: q3-hotfixes
last_pulled: 2026-08-13T...
---

# {title}

## Description
{description verbatim — the Description tab}

## Business Rules
{businessRules — omit section entirely if the field is empty}

## Acceptance Criteria
{acceptanceCriteria — omit if empty}

## NFRs
{nfrs — omit if empty}

## Test Scenarios
{testScenarios — omit if empty}

## Assumptions / Dependencies
{assumptions — omit if empty}

## Implementation
{implementationDetails — omit if empty}
```

Skip sections whose fields are empty so the file doesn't fill up with blank headings. `task_type` is preserved in frontmatter so a subsequent push can round-trip through `/jetrix:push task` without losing the type.

### Why two calls (feature + task)?

`feature_pull_bundle` filters to `taskType="feature"` server-side — non-features never appear in its result. `task_pull_bundle` doesn't filter by type (or filters to a specific non-feature type) — that's where bugs / chores / ad-hoc tasks come from. Running both against the same List gives you complete coverage without either tool having to change.

A Solution's FEATURE tasks may be spread across **multiple MC Lists** (one per resolved `list_name` at push time — see `push.md` Stage: feature). `pull list <name>` fetches only the tasks in that one List. To materialize every feature under the Solution regardless of List, use `pull scope`.

---

Keep it **idempotent** — a re-pull of unchanged docs must be a no-op (only `lastPulled` timestamps get bumped). Never overwrite a locally-modified file whose contentHash differs from the last pull unless the remote hash also differs (that's covered because we compare local-vs-remote-record before deciding to download).
