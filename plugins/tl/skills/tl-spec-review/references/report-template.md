# Report Template — review data object + `spec-review.md`

The review is produced once as a structured **data object**, then rendered into two files: the interactive `spec-review.html` (inject the JSON into `assets/report.html`) and the Markdown `spec-review.md` (the structure below). Build the data object first; both renders derive from it so they can't drift.

Use the controlled severities (`Blocker` · `Major` · `Minor` · `Nit`) and the `FND-###` ID convention (zero-padded, append-only) from `delivery-os-conventions`. Drop the Applied-AI areas (or mark `score: "N/A"`) when the system has no LLM.

---

## 1. Review data object (the single source)

This is the JSON injected into `assets/report.html` at the `__REVIEW_DATA__` token. Every field the HTML reads is below; keep the key names exact.

```json
{
  "project": "SupportCopilot",
  "documentReviewed": "examples/.../support-copilot-spec.md",
  "documentVersion": "0.3 (2026-06-20)",
  "reviewDate": "2026-06-25 14:30",
  "system": {
    "isAI": true,
    "aiNote": "RAG over help-center + tickets, GPT-4o for generation",
    "multiSystem": true,
    "multiSystemNote": "React/Zendesk embed, FastAPI backend, retrieval service, Postgres/pgvector, OpenAI, Zendesk API"
  },
  "overallScore": 2.0,
  "verdict": "Not ready — major rework",
  "verdictReason": "Four Blockers plus a 2.0 average.",
  "executiveSummary": "2–4 sentences: what the spec is for, how build-ready it is, the single most important thing to fix.",
  "gatingFindings": ["FND-007", "FND-009"],
  "strengths": ["Sensible high-level RAG architecture", "Pragmatic Zendesk-embedded UX"],
  "areas": [
    {
      "num": 1,
      "code": "OVR",
      "name": "Overview & Problem Framing",
      "group": "Architecture & Design",
      "score": 4,
      "band": "Weak",
      "assessment": "What the spec covers/omits here and why it lands at this score.",
      "findingIds": ["FND-001"],
      "suggestions": "Concrete actions to raise the score.",
      "strengths": ""
    }
  ],
  "findings": [
    { "id": "FND-001", "severity": "Blocker", "area": "CMP",
      "finding": "What's wrong/missing and its consequence.", "fix": "How to close it." }
  ],
  "questions": ["Things that may simply be undocumented — ask before assuming."],
  "nextActions": ["Highest-leverage fix first, usually the Blockers."]
}
```

Field rules:
- `reviewDate` is the human-readable run time (date, plus time of day so two same-day runs are distinguishable) — it's shown in the report header/footer and should match the `<timestamp>` in the filename.
- `score` is a **number 0–10**, or the string `"N/A"` for non-applicable areas (the HTML draws no bar and excludes it visually). Don't include N/A areas in the overall average.
- `band` is the band label for the score (`Excellent`/`Good`/`Adequate`/`Weak`/`Stub`/`Absent`/`N/A`).
- `group` drives the section dividers in the scorecard — use the four group names: `Architecture & Design`, `Engineering Contracts`, `Applied AI / LLM Engineering`, `Delivery & Operations`. Keep areas in order so each group's rows are contiguous.
- `gatingFindings` lists the IDs (Blockers + the most important Majors) surfaced at the top; each must exist in `findings`.
- `findingIds` on an area links it to its rows in `findings`; the HTML makes them clickable.
- Keep all 13 areas in the `areas` array (AI ones with `score: "N/A"` when not an AI system) so the scorecard is complete.

## 2. Injecting into the HTML

Read `assets/report.html`, replace the literal token `__REVIEW_DATA__` (it sits between `<script id="review-data" type="application/json">` and `</script>`) with the JSON object above, and write to the timestamped output path `spec-review-<timestamp>.html` (see SKILL.md step 6). Touch nothing else. Validate the JSON — a trailing comma or unescaped quote makes the page render its empty-state notice instead of the report.

---

## 3. Markdown artifact — `spec-review.md`

Assemble the Markdown in this exact structure. Keep it skimmable: a decision-maker should get the verdict and the gating findings from the first screen, with the per-area detail below for the team that has to act on it. Replace every `<…>` placeholder.

---

````markdown
---
doc_type: spec-review
schema_version: 1.0
produced_by: tl
status: Reviewed
generated_at: <YYYY-MM-DD>
reviewed_document: "<original path or link to the spec reviewed>"
document_version: "<version/date of the reviewed doc, or 'unversioned'>"
---

# Technical Specification Review — <Project / System Name>

| | |
|---|---|
| **Document reviewed** | `<path or link>` (<version/date>) |
| **Reviewed by** | TL Agent (Techjays Delivery OS) |
| **Review date** | <YYYY-MM-DD HH:MM> (this report: `spec-review-<timestamp>.md`) |
| **AI / LLM system?** | <Yes — uses ‹models/pattern›  /  No — deterministic> |
| **Multiple systems?** | <Yes — ‹list›  /  No — single service> |

## Executive summary

**Overall score: <X.X>/10 — <Readiness verdict>**

<2–4 sentences: what this spec is for, how build-ready it is, and the single most important thing to fix. State the verdict reason — e.g. "two Blockers (FND-003 payment idempotency, FND-009 PII to third-party model) cap this below build-ready despite strong architecture.">

**Gating findings** (the ones that must close before/early in build):
- `FND-001` (<Blocker/Major>) — <one line> → <one-line fix>
- `FND-002` (<Blocker/Major>) — <one line> → <one-line fix>

**Notable strengths:** <1–2 things the spec does well and should keep>.

## Scorecard

| # | Area | Score | Status |
|---|------|:-----:|--------|
| 1 | Overview & Problem Framing | <n>/10 | <Excellent/Good/Adequate/Weak/Stub/Absent> |
| 2 | Architecture & System Design | <n>/10 | <…> |
| 3 | Feature Flows & System Sequencing | <n>/10 | <…> |
| 4 | Data Schema & Modeling | <n>/10 | <…> |
| 5 | API Contracts | <n>/10 | <…> |
| 6 | Libraries, Frameworks & Tech Stack | <n>/10 | <…> |
| 7 | Observability & Traceability | <n>/10 \| N/A | <…> |
| 8 | Evaluation Strategy | <n>/10 \| N/A | <…> |
| 9 | Feedback Loops & Continuous Improvement | <n>/10 \| N/A | <…> |
| 10 | AI Compliance, Safety & Governance | <n>/10 \| N/A | <…> |
| 11 | Infrastructure & Environment Setup | <n>/10 | <…> |
| 12 | CI/CD & Release Management | <n>/10 | <…> |
| 13 | Cost Projection | <n>/10 | <…> |
| | **Overall (avg of applicable)** | **<X.X>/10** | **<Verdict>** |

## Area detail

> Repeat this block for each area. Keep assessments to a few sentences; push the specifics into findings.

### <n>. <Area name> — <score>/10
**Assessment.** <What the spec does and doesn't cover here, and why it lands at this score.>
**Findings.** <FND-0XX, FND-0XX — or "None; covered well.">
**Suggestions.** <Concrete, specific actions to raise the score. Reference what to add, not just that something's missing.>
**Strengths.** <Optional — what's done well here.>

## Findings register

> Sorted by severity (Blockers first). Every deducted point traces to a finding here; every finding has a suggested fix. `Area` is the area code (OVR/ARC/FLW/DAT/API/LIB/OBS/EVL/FBK/CMP/INF/CICD/CST).

| ID | Sev. | Area | Finding | Suggested fix |
|----|------|------|---------|---------------|
| FND-001 | Blocker | <CODE> | <what's wrong/missing and its consequence> | <how to close it> |
| FND-002 | Major | <CODE> | <…> | <…> |
| FND-003 | Minor | <CODE> | <…> | <…> |
| FND-004 | Nit | <CODE> | <…> | <…> |

## Clarifying questions for the author

> Things that look missing but may simply be undocumented or live in a companion doc — ask before assuming. Resolving these may move scores.

1. <question>
2. <question>

## Recommended next actions

1. <highest-leverage fix, usually the Blockers>
2. <…>
3. <…>
````

---

## Notes on filling it in

- **Executive summary is for the decider; area detail is for the builder.** Don't make the reader scroll past 13 sections to learn whether the spec is ready.
- **The findings register is the spine.** If a score is 5/10 but no findings explain the missing 5 points, the review isn't done. Conversely, don't list a finding you didn't let affect a score.
- **Keep suggestions concrete.** "Add error handling" is weak. "Define 4xx/5xx responses and an idempotency key for `POST /jobs` so a retried submission doesn't create duplicate jobs" is actionable.
- **When you mark N/A, say why in the area detail** (one line) so the reader trusts it was a decision, not an omission.
