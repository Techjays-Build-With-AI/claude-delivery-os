# Audit report — data schema, Markdown format, and HTML rendering

The audit produces **one structured data object**, rendered into two files that can't drift: the interactive `.html` and the Markdown artifact `.md`. Build the object first, then render. The object itself travels inside the HTML at `<script id="audit-data">`, which is how `/qa:plan` reads the round back — there is no `.json` sidecar to keep in sync.

## Audit data object (injected into the HTML)

```json
{
  // The ABSOLUTE folder this report belongs to. The page sends it with every
  // save, so any serve-review instance writes to the right place and the port
  // stops mattering. Without it the save falls back to the server’s own folder.
  "saveDir": "<absolute path to requirements/<slug>/reviews>",
  "auditId": "2026-07-05-143210",
  "schema_version": "1.1",
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
      "whyItMatters": "The dev delivery loop's agentExecuting step has nothing to run — no feature can be validated.",
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

## Markdown artifact (`<repo>-audit-<timestamp>.md`)

Frontmatter then body:

```yaml
---
doc_type: test-audit
schema_version: 1.1
produced_by: qa
audit_id: 2026-07-05-143210
round: 1
status: Reviewed
generated_at: 2026-07-05
---
```

Body sections, in order: **Summary** (readiness score, verdict, one-paragraph headline), **Detected stack**, **Scorecard** (table: area · score/10 · note), **Findings** (one block per `QAF-###`: severity, what's missing, why it matters, recommendation, recommended option, effort, proposed decision), and **Next action** (review → approve → export approvals → `/qa:plan`).

## Interactive HTML (`<repo>-audit-<timestamp>.html`)

Build the audit object, write it to a **scratch** file, then render by injecting it into `assets/report.html` at the `__AUDIT_DATA__` placeholder with the bundled script — `node assets/inject.js assets/report.html <scratch>/audit-data.json __AUDIT_DATA__ qa/reviews/<repo>-audit-<timestamp>.html`. **The scratch JSON is not an output** — it is injection input and is not kept. An audit leaves exactly two files: the `.html` a human reads and the `.md` that is the durable artifact. The data survives inside the HTML at `<script id="audit-data">`, which is where `/qa:plan` reads it. Never hand-assemble the HTML: the report carries non-ASCII glyphs (`§`, `—`, `→`) that a Windows code page double-encodes into mojibake (`§`→`Â§`, `—`→`â€"`) even with `<meta charset="utf-8">`. `inject.js` reads/writes UTF-8 deterministically, validates the JSON, and aborts on mojibake; if Node is unavailable, do the replacement manually but save as **UTF-8 without a BOM** and verify `§`/`—`, not `Â§`/`â€"`.

The report lets the human, per finding, set **Adopt / Skip / Defer** and add a note, then **Export approvals** — which downloads `<repo>-audit-<timestamp>-approvals.md` in the format `/qa:plan` reads.

## Approvals file (`<repo>-audit-<timestamp>-approvals.md`) — the join back to `/qa:plan`

```yaml
---
doc_type: test-audit-approvals
schema_version: 1.1
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

`source_audit` + `repo` are the join key back to `<repo>-audit-<auditId>.html`, whose `<script id="audit-data">` block holds the full finding detail; `/qa:plan` reads it from there and plans only the `Adopt` rows.
