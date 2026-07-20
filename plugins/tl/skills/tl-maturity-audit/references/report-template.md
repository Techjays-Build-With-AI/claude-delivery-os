# Maturity report — data schema, Markdown format, and HTML rendering

The audit produces **one structured data object**, rendered into three files that can't drift: the interactive `.html`, the Markdown artifact `.md`, and the `.json` sidecar. Build the object first, then render.

## Maturity data object (the JSON sidecar)

```json
{
  "maturityId": "2026-07-19-152210",
  "schema_version": "1.0",
  "produced_by": "tl",
  "round": 1,
  "priorAudit": null,
  "repo": "<repo path or name>",
  "generatedAt": "2026-07-19",
  "profile": { "type": "public-api", "hasUI": false, "hasDatastore": true },
  "stack": { "languages": ["C#"], "frameworks": [".NET 8", "ASP.NET Core"], "packageManager": "nuget" },
  "baseline": {
    "status": "Unmet",
    "unmet": ["BL-05", "BL-08", "BL-09"],
    "source": "org-default"
  },
  "auditConfidence": 0.62,
  "evidenceSplit": { "evidenced": 13, "attested": 6, "notMeasured": 4 },
  "overallScore": 5.8,
  "tier": "Significant gaps",
  "domains": [
    {
      "id": "D1", "name": "Code Quality & Maintainability", "score": 6.5, "applicable": true,
      "subAreas": [
        { "id": "D1.1", "name": "Lint cleanliness & enforcement", "score": 5, "applicable": true,
          "evidence": "evidenced", "rung": "present", "note": "analyzers present, not enforced in CI" }
      ]
    }
  ],
  "findings": [
    {
      "id": "MAT-001",
      "domain": "D2",
      "subArea": "D2.3 Coverage enforcement",
      "severity": "Blocker",
      "evidence": "evidenced",
      "whatsWrong": "Tests run in CI but coverage is neither collected nor threshold-gated.",
      "whyItMatters": "A feature can drop coverage to zero and still merge — the loop's sign-off is unproven.",
      "evidenceRef": "no coverlet in *.csproj; CI workflow has no coverage step",
      "recommendation": "Add coverlet + fail the build below coverage_floor (70).",
      "routesTo": "qa",
      "effort": "S"
    }
  ],
  "attestations": [
    { "subArea": "D3.4 Observability", "claim": "Logs to Datadog, alerts on error rate", "by": "unanswered", "status": "open" }
  ],
  "notMeasured": [
    { "subArea": "D2.2 Coverage level", "needs": ".NET SDK + restore + coverlet", "owner": "user" }
  ]
}
```

Rules:
- **`MAT-###`** IDs are stable and append-only across re-audits (carry forward by ID; a re-audit is a new `round` with `priorAudit` set).
- `overallScore` = average of `applicable: true` **domains**; each domain score = average of its applicable sub-areas. `notMeasured` sub-areas are **excluded** from averages (they lower `auditConfidence`, not the score).
- Any `Blocker` finding caps `tier` downward regardless of the average.
- `auditConfidence` = evidenced ÷ (evidenced + attested + notMeasured) over applicable sub-areas. Report it **separately** from `overallScore`.
- Every finding carries an `evidence` class (`evidenced`/`attested`) and, when evidenced, an `evidenceRef` (tool + file/line or report artifact). `routesTo` is `qa` when the fix is baseline/harness work QA owns, else null.

## Markdown artifact (`maturity-<timestamp>.md`)

Frontmatter then body:

```yaml
---
doc_type: maturity-audit
schema_version: 1.0
produced_by: tl
maturity_id: 2026-07-19-152210
round: 1
status: Reviewed
generated_at: 2026-07-19
---
```

Body sections, in order: **Summary** (overall score, tier, Audit Confidence, one-paragraph headline), **Preflight & baseline** (detected stack, baseline status + unmet items, what wasn't measured and why), **Domain scorecard** (table: domain · score/10 · confidence note), **Sub-area detail** (per domain, each sub-area with score, evidence class, rung), **Findings** (one block per `MAT-###`: severity, evidence class, what's wrong, why it matters, evidence ref, recommendation, routes-to), **Attestations** (the human-answered claims and their status), and **Next action**.

## Interactive HTML (`maturity-<timestamp>.html`)

Write the `.json` sidecar first, then render by injecting it into `assets/report.html` at the `__MATURITY_DATA__` placeholder with the bundled script:

```text
node assets/inject.js assets/report.html maturity-<timestamp>.json __MATURITY_DATA__ maturity-<timestamp>.html
```

Never hand-assemble the HTML: the report carries non-ASCII glyphs (`§`, `—`, `→`) that a Windows code page double-encodes into mojibake even with `<meta charset="utf-8">`. `inject.js` reads/writes UTF-8 deterministically, validates the JSON, and aborts on mojibake. If Node is unavailable, do the replacement manually but save as **UTF-8 without a BOM** and verify `§`/`—`, not `Â§`/`â€"`.

The report renders the score + tier + **Audit Confidence** in the hero, a domain scorecard with score bars, a findings register with a live severity filter and `evidenced`/`attested` + `present`/`enforced`/`passing` badges, expandable evidence per finding, and the preflight/baseline banner. Read-only — it's a report, not a decision surface (no approvals export); items that route to QA say so and point at `/qa:audit`.

## Output location

Inside a workspace: `tl-output/maturity-<timestamp>.{html,md,json}` (create `tl-output/` on first run). No workspace: beside the repo, with a note that no workspace was found. The timestamp (`YYYY-MM-DD-HHMMSS`, from the system clock) means a re-audit never overwrites a prior one.
