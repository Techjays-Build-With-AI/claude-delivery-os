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
3. Response has `pulled: 0 | 1` and a `features[0]` record (or none if the ref didn't match). If `pulled: 0`, report "no match for `<ref>`" and stop — do not run the materializer with an empty bundle.
4. **Materialize the feature folder** — do NOT iterate the fields with `Write` calls. Dump the response JSON to disk (one Bash heredoc) then invoke `materialize-features.py` (one Bash → Python). Same script and same on-disk contract as `pull scope` §6 — one feature or fifty, identical mechanism.

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

5. **sync-state is updated inside the script** — no separate Bash pass. Merge-safe: only this feature's `tasks/<feature_id>` entry is touched, every other stage's key is preserved.

Report:
```
✓ Pulled TASK-42 (FEAT-CLSF-01, "Document Classification & Extraction")
  → features/document-classification-extraction/
    feature.md, workflow.md, acceptance-criteria.md,
    business-rules.md, nfrs.md, test-scenarios.md,
    dependencies.md, open-questions.md, status.md
    tl-plan.md         (only if TL has pushed implementation for this feature)
```

Use this stage for **single-task dev flow** — `/dev:build TASK-42` can auto-run it if the feature folder isn't already on disk.

---

