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
3. **Materialize every feature folder** — do NOT iterate `features[]` with `Write` calls (for a 15-feature sprint that's ~105 tool round-trips). Dump the response JSON to disk (one Bash heredoc), then invoke `materialize-features.py` (one Bash → Python). Same script as `pull scope` §6 — the sprint case is just fewer features going in.

    ```bash
    BUNDLE="<workspace_root>/.jetrix/cache/.pull-features.json"
    mkdir -p "$(dirname "$BUNDLE")"

    cat > "$BUNDLE" <<'JETRIX_BUNDLE_EOF'
    <paste the entire feature_pull_bundle JSON response here, verbatim>
    JETRIX_BUNDLE_EOF

    python "$CLAUDE_PLUGIN_ROOT/scripts/materialize-features.py" \
      --bundle       "$BUNDLE" \
      --project-root "<absolute project_root>" \
      --sync-state   "<workspace_root>/.jetrix/cache/sync-state.json"

    rm -f "$BUNDLE"
    ```

4. **sync-state merges inside the script** — per-feature `tasks/<feature_id>` entries updated with fresh `contentHash` + `lastPulled`. Other stages' keys preserved.

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

