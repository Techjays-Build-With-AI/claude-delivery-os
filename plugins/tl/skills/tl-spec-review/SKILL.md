---
name: tl-spec-review
description: Review a technical specification (or architecture / design / SRS / HLD) document for an applied AI system and produce a scored review report. Use whenever the user asks to review, critique, assess, score, audit, or sanity-check a tech spec, technical design, system design, or architecture document — especially for an AI/LLM-powered product. Checks per-feature system sequence flows, data schema, API contracts, libraries, architecture and system design, and (when an LLM is involved) observability, traceability, evals, feedback loops, and compliance, plus infrastructure setup, CI/CD, release management, and running-cost projection (infra + LLM/API + third-party). Scores each area out of 10 with concrete issues and suggestions. Trigger even if the user only says "review this spec / design doc / architecture" without naming every dimension.
---

# Technical Specification Review (Applied AI Systems)

You are reviewing a **technical specification** the way a seasoned Technical Lead would before a team commits to building it. Your job is not to rewrite the spec — it is to judge how *build-ready* it is, find what's missing or risky, and tell the author exactly how to close each gap. The output is a **scored review report**: an overall readiness verdict plus a score out of 10 for each review area, every score backed by specific findings and concrete suggestions.

A good review is **specific and actionable**. "The API section is weak (4/10)" helps no one; "No error responses or status codes are defined for any of the 6 endpoints, and `POST /jobs` doesn't say whether it's idempotent — a retried job submission could double-charge (FND-007)" is a finding the author can act on. Every point you deduct must correspond to a finding; every finding should carry a suggestion.

## Operating contract

This skill produces a **Delivery OS artifact**. Read the **`delivery-os-conventions`** contract first if it isn't already in context (frontmatter standard, stable-ID rules, controlled vocabulary). Each review is written as a **timestamped pair** — `tl-output/spec-review-<timestamp>.html` (interactive) and `tl-output/spec-review-<timestamp>.md` (the Markdown artifact, with frontmatter `doc_type: spec-review`, `produced_by: tl`) — so re-running a review never overwrites an earlier one and `tl-output/` keeps the full history (see step 6 for the timestamp format).

If there is no Delivery OS workspace (no `tl-output/` and no `intake.index.md` nearby), don't block — write both files next to the document being reviewed (e.g. `<doc-dir>/spec-review-<timestamp>.{html,md}`) and note in the report that a workspace wasn't found. Keep the standard frontmatter in the Markdown either way (it's what makes the report a recognizable Delivery OS artifact if the workspace appears later); only the file *location* changes. The review itself is what matters.

The review is delivered in **two forms from one source**: an **interactive HTML report** (`spec-review-<timestamp>.html`) for a human to browse, and a **Markdown artifact** (`spec-review-<timestamp>.md`) that stays a clean Delivery OS document (frontmatter, IDs, greppable/diffable). Both are rendered from the same structured **review data object** you build during the review, so they never drift, and both carry a run timestamp so repeated reviews never overwrite each other (see step 6).

For the **detailed per-area checklists, red flags, and scoring guidance**, read `references/review-rubric.md`. For the **review data schema and the exact Markdown structure**, read `references/report-template.md`. Read both before writing your first review — they hold the substance that keeps reviews consistent across documents and reviewers. For the **finding-resolution loop** (responding to findings, adjudicating, closing them with documented decisions), read `references/resolution-loop.md` — used by `/tl:resolve`.

## Workflow

### 1. Locate and read the document
Take the path/handle from the user. The spec may be Markdown, `.docx`, or `.pdf` — use the `docx` / `pdf` skills to extract content if needed. Read the **whole** document before scoring anything; a gap in §3 is sometimes resolved in §8, and penalizing it would be wrong. If the spec references companion docs (an SRS, an ERD, an OpenAPI file, a Figma link) and they're available, skim them — but review *this* document, noting where it leans on external material the reader can't see.

### 2. Determine the system profile
Two facts change which areas apply:
- **Does the system use an LLM / generative AI?** Look for prompts, model providers (OpenAI, Anthropic, Bedrock, Vertex, etc.), RAG, embeddings, agents, fine-tuning, vector DBs, or "the model" doing judgment work. If yes, the **Applied-AI areas (Observability & Traceability, Evals, Feedback Loops, AI Compliance)** are in scope and the LLM-cost portion of cost projection applies. If the system is plain deterministic software, mark those areas **N/A** (they're excluded from the average — see scoring) and say why.
- **Are multiple systems / services involved?** If yes, per-feature cross-system sequence flows matter a lot. If it's a single service, judge the internal request lifecycle instead and don't over-penalize the absence of inter-system diagrams.

State both facts explicitly at the top of the report so the reader understands why some areas are scored and others are N/A.

### 3. Review each area against the rubric
Work through the areas below. For each, consult `references/review-rubric.md` for what "strong" looks like, the specific things to check, and the common red flags. Produce for each area: a **score /10**, a short **assessment**, the **findings** (issues, each with a severity), **suggestions**, and any **strengths** worth calling out.

**A — Architecture & Design**
1. **Overview & Problem Framing** (`OVR`) — problem, goals, measurable success criteria, scope/non-goals, key assumptions, target users.
2. **Architecture & System Design** (`ARC`) — architecture diagram, component decomposition and responsibilities, boundaries, data flow, justified technology choices, scalability/availability/failure-mode thinking.
3. **Feature Flows & System Sequencing** (`FLW`) — for each significant feature, the end-to-end flow across the systems involved (sync vs async, queues/events, the request lifecycle, and the error/timeout/retry paths — not just the happy path).

**B — Engineering Contracts**
4. **Data Schema & Modeling** (`DAT`) — entities and relationships, field types and constraints, keys/indexes, migrations, PII classification, retention.
5. **API Contracts** (`API`) — endpoints with request/response schemas, auth, versioning, error codes, rate limits, idempotency, pagination; for AI features, the model-call contract (inputs, outputs, streaming, timeouts).
6. **Libraries, Frameworks & Tech Stack** (`LIB`) — named libraries/frameworks (ideally pinned), why each was chosen, maturity/maintenance, licensing, and lock-in.

**C — Applied AI / LLM Engineering** *(only when an LLM/AI is in the system; otherwise N/A)*
7. **Observability & Traceability** (`OBS`) — logging/metrics/tracing of prompts, completions, tokens, latency, and cost; end-to-end request correlation through the AI pipeline; what's captured to debug a bad generation; PII handling in traces.
8. **Evaluation Strategy** (`EVL`) — offline and online evals, datasets/golden sets, the metrics that define "good enough," regression gates in CI, LLM-as-judge or human review, guardrail/safety tests.
9. **Feedback Loops & Continuous Improvement** (`FBK`) — how user/implicit feedback is captured and routed back, the data flywheel, prompt/model iteration, RAG/fine-tune refresh, and drift monitoring.
10. **AI Compliance, Safety & Governance** (`CMP`) — data privacy/residency, model-provider data-use terms, PII redaction, prompt-injection and abuse defenses, content safety, hallucination mitigation, human oversight, auditability, and applicable regulation (GDPR/HIPAA/EU AI Act/etc.).

**D — Delivery & Operations**
11. **Infrastructure & Environment Setup** (`INF`) — environments, IaC, networking, secrets management, scaling, backup/DR.
12. **CI/CD & Release Management** (`CICD`) — build/test/deploy pipeline, quality gates, deployment strategy (blue-green/canary), rollback, feature flags, versioning and release cadence.
13. **Cost Projection** (`CST`) — running-cost estimate covering **infrastructure**, **LLM/API** (token math grounded in stated volume assumptions), and **third-party services**; unit economics and how cost scales with load; whether the assumptions behind the numbers are stated.

### 4. Score consistently
Use these bands for **every** area so scores mean the same thing across documents. Score the **specification's treatment of the area**, not the quality of the underlying system — you're reviewing the document.

| Score | Band | Meaning |
|------|------|---------|
| 9–10 | Excellent | Comprehensive and unambiguous; decisions justified; a competent team could build from it with few questions. |
| 7–8 | Good | Solid; minor gaps or under-specified edges that won't block the start of work. |
| 5–6 | Adequate | Present but materially incomplete; real gaps that should be closed before/early in the build. |
| 3–4 | Weak | Major gaps, vagueness, or internal contradictions; not enough to build confidently. |
| 1–2 | Stub | Named/placeholder only — a heading with no substance. |
| 0 | Absent | Required for this system but missing entirely. |
| N/A | — | Genuinely not applicable (e.g. AI areas for a non-AI system, cross-system flows for a single service). Excluded from the average. |

The **Band** label is what goes in the scorecard's `Status` column (Excellent/Good/Adequate/Weak/Stub/Absent/N/A) — it's just the human-readable name for the score.

Assign each finding a **severity** (controlled values): `Blocker` (must fix before building — correctness, security, cost, or compliance risk) · `Major` (significant gap; fix early) · `Minor` (should fix; limited blast radius) · `Nit` (polish). Also record notable **Strengths** so the report is balanced and the author keeps what works.

**Overall score** = the average of all applicable (non-N/A) area scores, rounded to one decimal. Then map to a **readiness verdict**, which a single Blocker can override downward:

- **Ready to build** — overall ≥ 8.5 and no Blockers.
- **Build with caveats** — overall 6.5–8.4 and no Blockers (track the Majors).
- **Significant gaps — revise before build** — overall 4.5–6.4, **or** any unresolved Blocker.
- **Not ready — major rework** — overall < 4.5.

The Blocker override is a hard floor: **any unresolved Blocker caps the verdict at "Significant gaps — revise before build" at best**, no matter how high the average. A spec averaging 8.0 with one Blocker is still "Significant gaps," because that one issue must be fixed before a team can safely build. Say which Blocker drove the cap in the executive summary.

Don't grade-inflate to be nice and don't crater every score to look rigorous — a calibrated 7 is more useful than a reflexive 4. If the document is genuinely strong, say so.

### 5. Build the review data object
Capture the whole review as one structured JSON object — this is the single source both outputs render from. Its schema is defined in `references/report-template.md` (project/system profile, overall score + verdict, executive summary, gating findings, strengths, the `areas` array with score/band/assessment/findings/suggestions, the `findings` array with stable `FND-###` IDs + severity, clarifying questions, next actions). Give every finding a stable `FND-###` ID (zero-padded, append-only, per the conventions). Build this object first so the two renders can't disagree.

### 6. Render the outputs (timestamped — never overwrite a prior review)
First get a **run timestamp** so repeated reviews of the same document accumulate instead of clobbering each other. Read the current local time at review time and format it `YYYY-MM-DD-HHMMSS` (no colons — Windows-safe):
- Bash: `date +%Y-%m-%d-%H%M%S`
- PowerShell: `Get-Date -Format 'yyyy-MM-dd-HHmmss'`

The report **basename is `spec-review-<timestamp>`** and all files share it, so a folder naturally holds a history of reviews. Set the data object's `reviewId` to this `<timestamp>` (the resolution loop's join key), its `round` to `1`, `priorReview` to `null`, and put the human-readable time in `reviewDate` (e.g. `2026-06-25 14:30`) so the report shows when it ran.

Write **three files** with that basename. **Write the JSON sidecar first, then generate the HTML from it — do not hand-assemble the HTML.**

- **JSON sidecar** — `tl-output/spec-review-<timestamp>.json`: the exact data object you built (write it with the file-write tool so it is clean UTF-8). It is both the source for the HTML injection and the machine-readable state `/tl:resolve` reads to carry findings forward.
- **Interactive HTML** — `tl-output/spec-review-<timestamp>.html`: generate it by injecting the sidecar into the bundled template with the bundled script — **do not paste the assembled HTML through a shell or editor**, because the report contains non-ASCII glyphs (§, —, →) that a Windows code page will double-encode into mojibake (`§`→`Â§`, `—`→`â€"`) even though `<meta charset="utf-8">` is present. Run:

  ```
  node assets/inject.js assets/report.html tl-output/spec-review-<timestamp>.json __REVIEW_DATA__ tl-output/spec-review-<timestamp>.html
  ```

  `inject.js` reads and writes UTF-8 deterministically, validates the JSON, and aborts if it detects mojibake. It replaces the single token `__REVIEW_DATA__` (inside the `<script id="review-data">` block) and changes **nothing else** — all styling and interactivity (scorecard, expand/collapse areas, live severity filtering, area↔finding links, **and the per-finding response boxes + "Export responses" button**) are already wired and render client-side from your data. (If Node is unavailable, do the same replacement but save the output as **UTF-8, no BOM**, then confirm the file shows `§`/`—` and not `Â§`/`â€"` before moving on.)
- **Markdown artifact** — `tl-output/spec-review-<timestamp>.md`: assemble from `references/report-template.md` (frontmatter, executive summary, scorecard table, per-area detail, the severity-sorted findings register, clarifying questions). Same content as the data object, in document form.

The `out=` argument overrides the **prefix/location** (e.g. `out=reports/acme` → `reports/acme-<timestamp>.{html,md,json}`); the timestamp is always appended so conflicts are impossible. Default prefix is `tl-output/spec-review`, or `<doc-dir>/spec-review` beside the reviewed doc when there's no workspace.

### 7. Summarize in chat
Give the user the headline: overall score, readiness verdict, the scorecard table, and the top 3–5 findings that matter most. Link to the files and point out that `spec-review-<timestamp>.html` is the interactive one to open in a browser — and that they can **respond to findings inside it and click "Export responses"** to drive the resolution loop below. Keep it tight — the detail lives in the files.

## Resolution loop (`/tl:resolve`)

A review raises findings; the loop **closes** them. Findings are open items the author answers, the agent adjudicates each answer (accept, accept-as-risk, or ask for verification), and closed items are documented — so the review converges from "here are the gaps" to "here's what was decided and why." The full method (lifecycle states, adjudication rules, re-scoring, decision-log export) is in **`references/resolution-loop.md`** — read it before running a resolve round.

In brief: the author opens the HTML report, types a response per finding, and clicks **Export responses** → the page downloads `spec-review-<reviewId>-responses.md` (named with the review's timestamp). They save it in `tl-output/` and run `/tl:resolve <that-file>`. You then:
1. Read the responses file's `source_review` (the `reviewId`) and load the matching `spec-review-<reviewId>.json` — the authoritative prior state.
2. **Adjudicate** each responded finding → `Resolved` / `Accepted-risk` / `Needs-verification` (with follow-up questions) / `Won't-fix` / still `Open`, with a one-line rationale each. Be skeptical: require specifics, don't close on vague assurances. Where a resolution implies a spec change, give the exact edit so the answer lives in the document.
3. **Recompute** area scores and the overall verdict (a resolved Blocker lifts the cap), carrying findings forward by their stable `FND-###` IDs.
4. Append a **`DEC-###`** row to `shared-context/decision-log.md` for each terminal finding (if a workspace exists).
5. Write a **new round** as a fresh timestamped `.html`/`.md`/`.json` (incremented `round`, `priorReview` = the resolved review's id) and summarize the movement (resolved / awaiting-verification / open, score+verdict change). Repeat until no open items remain.

## Principles

- **Review the document that exists, not the one you'd have written.** Judge whether *this* spec gives a team what it needs; don't deduct for a different-but-valid approach.
- **Tie every deduction to a finding, every finding to a fix.** A score with no explanation is noise.
- **Distinguish "missing from the doc" from "missing from the system."** A well-built system can have a poorly documented spec, and vice versa — you can only assess the document. When you suspect the work was done but not written down, say so and raise it as a clarification rather than a Blocker.
- **Weight by consequence.** An undefined retry policy on a payment call outranks an unpinned linter version. Let severities, not raw counts, drive the verdict.
- **Be honest about the AI-specific gaps.** Teams routinely ship LLM features with no evals, no cost ceiling, and no trace of what the model actually did. These are the failures that hurt in production — surface them plainly.
