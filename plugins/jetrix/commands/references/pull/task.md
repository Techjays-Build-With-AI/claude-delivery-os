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

