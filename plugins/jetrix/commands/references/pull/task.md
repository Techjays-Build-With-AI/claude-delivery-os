## Stage: `task <ref>` (implemented — uses task-mcp)

Materializes ONE feature folder locally. `<ref>` accepts any of:

- `11` or `TASK-42` — task number (routed to `task_number`). A bare integer is the normal form.
- `FEAT-CLSF-01` — BA feature id (routed to `feature_id="FEAT-CLSF-01"`)
- `6a61...` (24-char hex) — MongoDB `_id` (routed to `task_object_id`)

Plugin recipe:

1. **Parse `<ref>`** — regex-detect the identifier type:
   - Bare integer (`^\d+$`) → `task_number` (int) — check this FIRST
   - Starts with `TASK-` (any case) → strip prefix, `task_number` (int)
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

   **`pulled: 0` is not "no such task" — it means "not a FEATURE".** `feature_pull_bundle` filters `taskType="feature"` server-side, so a bug, story, or ad-hoc task never appears in its result however valid the ref is. Fall through to the non-feature path (§7) before reporting anything to the user. Only when §7 also returns nothing is the ref genuinely unmatched — report "no match for `<ref>`" and stop. Never run `materialize-features.py` with an empty bundle.
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

6. **Sub-task materialization** — mirrors `pull scope` §7 so a single-task pull produces the same on-disk shape as a batch pull. Without this step, `/dev:build TASK-42` auto-pull leaves `features/<slug>/subtask/<repo>/` empty on a cold clone of a split feature.

    **Detection.** Read the parent's `jetrix_task_object_id` from `features[0].task_object_id` in the response (same value that materialize-features.py just wrote to `feature.md` frontmatter). If absent — legacy or dry-run parent — skip the sub-task step cleanly.

    **Fetch.** Call `task-mcp.subtask_list(solution_id, parent_task_id=<jetrix_task_object_id>)`. Response shape and field semantics match `pull scope` §7 — same `subtasks[]` array with `subtask_object_id`, `task_number`, `description`, `implementation_details`, `metadata.subtaskRepo`, `metadata.subtaskNumber`, etc.

    **Skip when empty.** `subtasks: []` means parent-alone — do not create empty `subtask/` folders.

    **Materialize via the same script.**

    ```bash
    SUB_BUNDLE="<workspace_root>/.jetrix/cache/.pull-subtasks-<parent-slug>.json"
    mkdir -p "$(dirname "$SUB_BUNDLE")"

    cat > "$SUB_BUNDLE" <<'JETRIX_SUB_EOF'
    {
      "parent_slug":            "<parent-slug>",
      "parent_feature_id":      "<FEAT-<AREA>-NN from parent's feature.md>",
      "parent_task_object_id":  "<parent's jetrix_task_object_id>",
      "parent_task_number":     "<parent's jetrix_task_number, e.g. Feature-4>",
      "subtasks":               <subtask_list.subtasks — verbatim>
    }
    JETRIX_SUB_EOF

    python "$CLAUDE_PLUGIN_ROOT/scripts/materialize-subtasks.py" \
      --bundle       "$SUB_BUNDLE" \
      --project-root "<absolute project_root>" \
      --sync-state   "<workspace_root>/.jetrix/cache/sync-state.json"

    rm -f "$SUB_BUNDLE"
    ```

    Writes `features/<parent_slug>/subtask/<subtaskRepo>/description.md` + `implementation.md` + `status.md` (plus `acceptance-criteria.md` and `test-scenarios.md` when MC has non-empty tab content). Section order in `implementation.md` is preserved verbatim from MC — same string that `/dev:plan` composed via `tl-feature-compose`, byte-identical after the round-trip. Sync-state entries land under `subtasks/<subtask_object_id>`. Detached local sub-task folders (no MC counterpart) trigger warnings, never deletes.

Report:
```
✓ Pulled TASK-42 (FEAT-CLSF-01, "Document Classification & Extraction")
  → features/document-classification-extraction/
    feature.md, workflow.md, acceptance-criteria.md,
    business-rules.md, nfrs.md, test-scenarios.md,
    dependencies.md, open-questions.md, status.md
    tl-plan.md         (only if TL has pushed implementation for this feature)
    subtask/<repo>/*   (only if the parent was split at /dev:plan time)
```

Use this stage for **single-task dev flow** — `/dev:build TASK-42` can auto-run it if the feature folder isn't already on disk.

---

### 7. Non-feature fallback — bugs, stories, ad-hoc tasks

Reached only when §3 returned `pulled: 0`. The ref may still be a real ticket that simply isn't a BA feature.

1. **Re-issue the same ref against the type-agnostic tool.** `task_pull_bundle` applies no type filter unless you pass one, so it covers bug / story / task / epic in one call:

   ```
   mcp__task-mcp__task_pull_bundle(
     solution_id = <from project.json>,
     task_number = 42    # OR task_object_id="..."  (same ref you parsed in §1)
   )
   ```

   `feature_id` is a BA concept — if §1 parsed a `FEAT-` ref and §3 found nothing, the ticket does not exist; report "no match" and stop rather than calling this tool.

2. **Nothing back here either** → report `no match for <ref>` and stop.

3. **Materialize as a flat task file** — `materialize-tasks.py`, not `materialize-features.py`. A non-feature ticket becomes ONE file at `tasks/<slug>.md` carrying only the tabs its type actually has:

   ```bash
   BUNDLE="<workspace_root>/.jetrix/cache/.pull-tasks.json"
   mkdir -p "$(dirname "$BUNDLE")"

   cat > "$BUNDLE" <<'JETRIX_BUNDLE_EOF'
   <paste the entire task_pull_bundle JSON response here, verbatim>
   JETRIX_BUNDLE_EOF

   python "$CLAUDE_PLUGIN_ROOT/scripts/materialize-tasks.py" \
     --bundle       "$BUNDLE" \
     --project-root "<absolute project_root>" \
     --sync-state   "<workspace_root>/.jetrix/cache/sync-state.json"

   rm -f "$BUNDLE"
   ```

   Sync-state lands under `tasks/<slug>.md` — the same key `/jetrix:pull list` writes, so skip-unchanged and `expected_updated_at` work across a pull → push cycle for these tickets too.

4. **Do not synthesise the 8-file BA layout for these.** `features/` means "decomposed from scope"; a bug that never went through `/ba:features` does not belong there. `/dev:plan` reads `tasks/<slug>.md` directly and writes its own outputs to `tasks/<slug>/dev/`.

Report:
```
✓ Pulled TASK-87 (bug, "Login crashes on empty password")
  → tasks/login-crashes-on-empty-password.md
    Bug Description, Steps to Reproduce, Actual Result, Expected Result

  Next: /dev:plan tasks/login-crashes-on-empty-password.md
```

---

