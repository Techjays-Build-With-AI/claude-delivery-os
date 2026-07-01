# Report Template — review data object + `scope-review.md`

The review is produced once as a structured **data object**, then rendered into three files: the interactive `scope-review-<timestamp>.html` (inject the JSON into `assets/report.html`), the Markdown `scope-review-<timestamp>.md` (structure below), and the `scope-review-<timestamp>.json` sidecar (the data object verbatim). Build the data object first; all renders derive from it so they can't drift.

Use the controlled severities (`Blocker` · `Major` · `Minor` · `Nit`) and a stable `SQ-###` ID (zero-padded, append-only) for every scope question, per `delivery-os-conventions`.

---

## 1. Review data object (the single source)

This is the JSON injected into `assets/report.html` at the `__REVIEW_DATA__` token. Every field the HTML reads is below; keep the key names exact.

```json
{
  "project": "Acme Customer Portal",
  "documentReviewed": "ba-output/scope.md",
  "documentVersion": "0.3 (Emerging)",
  "reviewDate": "2026-06-30 14:30",
  "reviewId": "2026-06-30-143012",
  "round": 1,
  "priorReview": null,
  "knowledgeBase": {
    "examplesChecked": 12,
    "registersChecked": ["example-register.md", "requirement-register.md", "clarification-log.md", "system-landscape.md"],
    "note": "Cross-checked against 12 client examples (EX-001–EX-012) and the requirement register; no contradiction-log present."
  },
  "overallScore": 3.4,
  "verdict": "Significant gaps — clarify before estimate",
  "verdictReason": "Auth method (SQ-004) and CRM partner (SQ-011) are undefined Blockers; the scope averages 3.4.",
  "executiveSummary": "2–4 sentences: what this scope covers, how estimate-ready it is, and the single most important thing to clarify before pricing it.",
  "gatingQuestions": ["SQ-004", "SQ-011"],
  "strengths": ["Clear module breakdown in §2", "Out-of-scope stated explicitly for the Reporting module"],
  "features": [
    {
      "num": 1,
      "code": "AUTH",
      "name": "Login & Authentication",
      "group": "Core Modules",
      "kind": "UI / auth",
      "score": 2,
      "band": "Stub",
      "boundedness": "Unbounded",
      "boundednessNote": "No auth methods enumerated, no in/out boundary, no adjacent-flow (registration/reset) scope — function stated, boundary undefined.",
      "coverage": {
        "current_future": "Absent",
        "in_out_scope": "Absent",
        "functional_reqs": "Partial",
        "ai_automation": "Absent",
        "business_rules": "Absent",
        "data_fields": "Absent",
        "integrations": "Absent",
        "exceptions": "Absent",
        "acceptance": "Absent"
      },
      "exampleCompliance": "Conflict",
      "exampleNote": "EX-004 shows a user signing in with Google, but the scope mentions only email/password — the scope can't satisfy the example.",
      "assessment": "Unbounded: the scope says only 'the system will have a login screen'. The auth methods aren't enumerated, the in/out boundary and adjacent flows (registration, reset) are unstated, and it conflicts with EX-004 — so it's capped at Weak.",
      "questionIds": ["SQ-001", "SQ-002", "SQ-003", "SQ-004"],
      "suggestions": "Enumerate the supported auth methods and mark each In/Out of scope; state whether registration, password reset, and profile are in scope; add the account-access policies (verification, lockout, MFA).",
      "strengths": ""
    }
  ],
  "questions": [
    {
      "id": "SQ-004",
      "severity": "Blocker",
      "feature": "AUTH",
      "dimension": "functional_reqs",
      "question": "Which authentication methods are in scope — email/password, social (Google/Apple/Microsoft), OTP/passwordless, magic link, or enterprise SSO (SAML/OIDC)?",
      "whyItMatters": "The auth method is a business decision that swings the estimate and the integrations list. Unspecified, the price is a guess — and it conflicts with EX-004 (Google sign-in).",
      "suggestedScope": "In §3.1.3 list the supported methods with Resp./Pri.; if email/password, add verification + password policy + lockout; reconcile with EX-004.",
      "status": "Open",
      "authorResponse": null,
      "adjudication": null,
      "followUps": [],
      "resolvedOn": null,
      "decisionId": null
    }
  ],
  "nextActions": ["Pin the auth method (SQ-004) and the CRM partner (SQ-011) — both block the estimate."]
}
```

Field rules:
- `reviewDate` is the human-readable run time (date + time so two same-day runs are distinguishable); it shows in the header/footer and should match the `<timestamp>` in the filename.
- `reviewId` is the filename `<timestamp>` (`YYYY-MM-DD-HHMMSS`) — the join key the resolution loop uses to match a responses file back to its review. The HTML "Export responses" button reads it to name the download. `round` starts at 1; `/ba:resolve` increments it. `priorReview` is the `reviewId` of the report this round resolves (null for round 1).
- The per-question **resolution fields** (`status`, `authorResponse`, `adjudication`, `followUps`, `resolvedOn`, `decisionId`) start at `Open`/null in round 1 and are filled by `/ba:resolve`. `status` uses the controlled values in `resolution-loop.md`; `followUps` is a list of verification questions when `status` is `Needs-verification`.
- `score` is a **number 0–10** (the HTML draws a bar and a band). Keep all features in the `features` array so the scorecard is complete.
- `band` is the band label (`Excellent`/`Good`/`Adequate`/`Weak`/`Stub`/`Absent`).
- `boundedness` is one of `"Bounded"` / `"Partially-bounded"` / `"Unbounded"`; `boundednessNote` (one line) says what's undefined. **These cap the score** — `Unbounded` ≤ 4, `Partially-bounded` ≤ 6 (see `review-rubric.md` §A). The HTML shows a boundedness badge on the feature.
- `coverage` has exactly the nine keys above, each valued `"Covered"` / `"Partial"` / `"Absent"` (the HTML renders the matrix and colours each cell). Use `"Covered"` with an assessment note when a dimension is genuinely not-needed for that feature.
- `exampleCompliance` is one of `"Pass"` / `"Partial"` / `"Conflict"` / `"No-examples"`; `exampleNote` explains it (cite the EX id for Partial/Conflict).
- `group` drives the section dividers in the scorecard — use your own module-group names (e.g. `Core Modules`, `Supporting Modules`, `Cross-cutting`). Keep features in order so each group's rows are contiguous.
- `kind` (optional) is the feature kind (UI/auth, integration, data/reporting, AI/automation, admin, workflow) — shown as a tag.
- `gatingQuestions` lists the IDs (Blockers + the most important Majors) surfaced at the top; each must exist in `questions`.
- `questionIds` on a feature links it to its rows in `questions`; the HTML makes them clickable.
- `dimension` on a question is one of the nine coverage keys (or omit) — used to tag which sub-heading the gap sits in.

## 2. Injecting into the HTML

Read `assets/report.html`, replace the literal token `__REVIEW_DATA__` (between `<script id="review-data" type="application/json">` and `</script>`) with the JSON object above, and write to the timestamped path `scope-review-<timestamp>.html` (SKILL.md step 7). Touch nothing else. Validate the JSON — a trailing comma or unescaped quote makes the page render its empty-state notice instead of the report.

**Also write the same JSON object to `scope-review-<timestamp>.json`** alongside. This sidecar is the machine-readable state `/ba:resolve` reads (matched by `reviewId`) to carry questions forward without re-parsing HTML or prose.

---

## 3. Markdown artifact — `scope-review.md`

Assemble the Markdown in this exact structure. Keep it skimmable: a decision-maker should get the verdict and the gating questions from the first screen, with per-feature detail below for the BA who has to close the gaps. Replace every `<…>` placeholder.

---

````markdown
---
doc_type: scope-review
schema_version: 1.0
produced_by: ba
status: Reviewed
generated_at: <YYYY-MM-DD>
reviewed_document: "<original path or link to the scope reviewed>"
document_version: "<version/status of the reviewed scope, or 'unversioned'>"
review_id: "<timestamp>"
round: 1
---

# Scope Review — <Project / System Name>

| | |
|---|---|
| **Document reviewed** | `<path or link>` (<version/status>) |
| **Reviewed by** | BA Agent (Techjays Delivery OS) |
| **Review date** | <YYYY-MM-DD HH:MM> (this report: `scope-review-<timestamp>.md`) |
| **Knowledge base** | <N examples checked (EX-001–EX-0NN); registers consulted: …> |

## Executive summary

**Overall score: <X.X>/10 — <Scope-readiness verdict>**

<2–4 sentences: what this scope covers, how estimate-ready it is, and the single most important thing to clarify. State the verdict reason — e.g. "two Blockers (SQ-004 auth method, SQ-011 CRM partner) cap this below estimate-ready despite a clean module breakdown.">

**Gating questions** (must close before estimate):
- `SQ-004` (<Blocker/Major>) — <one line> → <the scope addition that closes it>
- `SQ-011` (<Blocker/Major>) — <one line> → <…>

**Notable strengths:** <1–2 things the scope does well and should keep>.

## Feature scorecard

| # | Feature | Kind | Score | Status | Boundedness | Examples |
|---|---------|------|:-----:|--------|-------------|----------|
| 1 | Login & Authentication | UI / auth | <n>/10 | <Excellent/Good/Adequate/Weak/Stub/Absent> | <Bounded/Partially-bounded/Unbounded> | <Pass/Partial/Conflict/No-examples> |
| 2 | … | … | <n>/10 | <…> | <…> | <…> |
| | **Overall (avg)** | | **<X.X>/10** | **<Verdict>** | | |

## Feature detail

> Repeat this block per feature. Keep assessments to a few sentences; push specifics into the question register.

### <n>. <Feature name> — <score>/10  ·  boundedness: <Bounded/Partially-bounded/Unbounded>  ·  examples: <Pass/Partial/Conflict/No-examples>
**Bounding.** Categories <enumerated & closed? / open> · Definitions/criteria <stated? how X vs Y is decided> · Exclusions <what's explicitly out> · Mandatory vs optional fields <clear? / missing>. <One line on what's undefined.>
**Coverage.** Current→Future <C/P/A> · In/Out scope <C/P/A> · Functional reqs <C/P/A> · AI/Automation <C/P/A> · Business rules <C/P/A> · Information & data <C/P/A> · Integrations <C/P/A> · Exceptions & edge cases <C/P/A> · Acceptance <C/P/A>
**Assessment.** <What the scope does and doesn't cover for this feature, and why it lands at this score.>
**Example check.** <Pass / or cite the EX id and the conflict/partial gap.>
**Questions.** <SQ-0XX, SQ-0XX — or "None; well scoped.">
**Suggested scope additions.** <Concrete edits — what to add and to which §3.x sub-heading.>
**Strengths.** <Optional.>

## Scope questions & gaps register

> Sorted by severity (Blockers first). Every deducted point traces to a question here; every question carries the scope addition that closes it. `Status` is the lifecycle state (`Open` in round 1; updated by `/ba:resolve`).

| ID | Sev. | Status | Feature | Question | Suggested scope addition |
|----|------|--------|---------|----------|--------------------------|
| SQ-001 | Blocker | <Open/Resolved/Needs-verification/Accepted-assumption/Won't-fix> | <CODE> | <the question> | <the scope edit that answers it> |
| SQ-002 | Major | <…> | <CODE> | <…> | <…> |

**Resolution rounds (round 2+).** For each question that received a response, add a short thread under the register so closure is auditable — the author's response, the agent's adjudication, any follow-ups, and the `DEC-###` / `ASM-###` / `CLR-###` id it promoted to:

```markdown
#### SQ-004 — Resolved (round 2)
- **Author response:** Email/password + Google SSO; corporate domains only; email verified; MFA optional.
- **Adjudication:** Specific and verifiable; reconciles with EX-004. Spec edit applied to §3.1.3. Closed.
- **Promoted to:** DEC-007 (decision-log), scope §3.1.3 updated.
```

## Recommended next actions

1. <highest-leverage clarification, usually the Blockers>
2. <…>
````

---

## Notes on filling it in

- **Executive summary is for the decider; feature detail is for the BA.** Don't make the reader scroll past every feature to learn whether the scope is estimate-ready.
- **The question register is the spine.** If a feature is 3/10 but no questions explain the missing 7 points, the review isn't done. Conversely, don't list a question you didn't let affect a score.
- **Keep suggested additions concrete and located.** "Add more detail" is weak. "In §3.1.3, list auth methods with Resp./Pri. and mark social login Out-of-scope (phase 2)" is actionable.
- **Always show the example check.** Citing EX ids is what separates "I think this is thin" from "this can't do what the client showed us."
