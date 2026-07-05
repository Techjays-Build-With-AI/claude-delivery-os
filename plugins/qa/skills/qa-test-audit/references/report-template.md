# Audit report — data schema, Markdown format, and HTML rendering

The audit produces **one structured data object**, rendered into three files that can't drift: the interactive `.html`, the Markdown artifact `.md`, and the `.json` sidecar. Build the object first, then render.

## Audit data object (the JSON sidecar)

```json
{
  "auditId": "2026-07-05-143210",
  "schema_version": "1.0",
  "produced_by": "qa",
  "round": 1,
  "priorAudit": null,
  "repo": "<repo path or name>",
  "generatedAt": "2026-07-05",
  "stack": {
    "languages": ["TypeScript"],
    "frameworks": ["Next.js", "Express"],
    "packageManager": "pnpm",
    "existingTestTooling": ["none detected"],
    "baseBuildRuns": false
  },
  "readinessScore": 3.4,
  "verdict": "Major gaps",
  "scorecard": [
    { "area": "Unit test framework & runner", "score": 0, "applicable": true, "note": "No runner configured" },
    { "area": "End-to-end / UI testing harness", "score": 0, "applicable": true, "note": "No e2e tool" }
  ],
  "findings": [
    {
      "id": "QAF-001",
      "area": "Unit test framework & runner",
      "severity": "Blocker",
      "whatsMissing": "No unit test runner is configured; there is no command to run tests.",
      "whyItMatters": "The dev delivery loop's TESTING step has nothing to run — no feature can be validated.",
      "recommendation": "Adopt Vitest (matches the Vite/TS stack), add a `test` script, and a discoverable `*.test.ts` convention.",
      "recommendedOption": "Vitest",
      "effort": "S",
      "proposedDecision": "Adopt",
      "decision": null,
      "note": null
    }
  ]
}
```

Rules:
- **`QAF-###`** IDs are stable and append-only across re-audits (carry findings forward by ID; a re-audit is a new `round` with `priorAudit` set).
- `proposedDecision` is the QA default (`Adopt` for Blocker/Major, `Consider` for Minor/Nit). `decision` and `note` are the **human's** fields — null until they approve in the report.
- `readinessScore` is the average of `applicable: true` scorecard areas. Any `Blocker` finding caps `verdict` at `Not testable` until resolved.

## Markdown artifact (`test-audit-<timestamp>.md`)

Frontmatter then body:

```yaml
---
doc_type: test-audit
schema_version: 1.0
produced_by: qa
audit_id: 2026-07-05-143210
round: 1
status: Reviewed
generated_at: 2026-07-05
---
```

Body sections, in order: **Summary** (readiness score, verdict, one-paragraph headline), **Detected stack**, **Scorecard** (table: area · score/10 · note), **Findings** (one block per `QAF-###`: severity, what's missing, why it matters, recommendation, recommended option, effort, proposed decision), and **Next action** (review → approve → export approvals → `/qa:plan`).

## Interactive HTML (`test-audit-<timestamp>.html`)

Render by injecting the JSON object into `assets/report.html` at the `__AUDIT_DATA__` placeholder. The report lets the human, per finding, set **Adopt / Skip / Defer** and add a note, then **Export approvals** — which downloads `test-audit-<timestamp>-approvals.md` in the format `/qa:plan` reads.

## Approvals file (`test-audit-<timestamp>-approvals.md`) — the join back to `/qa:plan`

```yaml
---
doc_type: test-audit-approvals
schema_version: 1.0
produced_by: qa
source_audit: 2026-07-05-143210
generated_at: 2026-07-05
---
```

Then one row per finding the human acted on:

```text
QAF-001 · Adopt · Vitest · (note: use workspace config)
QAF-005 · Skip · — · (note: no API surface yet)
QAF-007 · Defer · Playwright · (note: revisit after MVP)
```

`source_audit` is the join key back to `test-audit-<auditId>.json`, so `/qa:plan` reloads the full finding detail and plans only the `Adopt` rows.
