## Stage: `deliverable` (pending — will use deliverable-mcp)

Not yet implemented. Same 3-phase file pattern as scope.

---

Keep it **idempotent** — a re-push of an unchanged file must be a no-op via the sync-state contentHash check. Never write duplicate FileMeta rows.
