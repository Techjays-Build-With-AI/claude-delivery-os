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
