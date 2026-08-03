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
3. Iterate `features[]` in the response → reconstruct each `context/features/<slug>/` folder.
4. Merge into sync-state per feature.

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

