---
doc_type: spec-review
schema_version: 1.0
produced_by: tl
status: Reviewed
generated_at: 2026-06-25
reviewed_document: "D:/Projects/Tools/claude-delivery-os/examples/tl-review-test/support-copilot-spec.md"
document_version: "0.3 (2026-06-20)"
---

# Technical Specification Review — SupportCopilot

> **Note:** No Delivery OS workspace was found near the reviewed document (no `tl-output/` and no `intake.index.md`). Per the skill's operating contract, this report is written next to the document being reviewed rather than to `tl-output/spec-review.md`.

| | |
|---|---|
| **Document reviewed** | `D:/Projects/Tools/claude-delivery-os/examples/tl-review-test/support-copilot-spec.md` (v0.3, 2026-06-20) |
| **Reviewed by** | TL Agent (Techjays Delivery OS) |
| **Review date** | 2026-06-25 |
| **AI / LLM system?** | Yes — RAG over pgvector + GPT-4o for drafting/summarizing/tone, text-embedding-3-small for embeddings |
| **Multiple systems?** | Yes — React web app (embedded in Zendesk), FastAPI backend, retrieval service, Postgres/pgvector, OpenAI API, Zendesk API |

## Executive summary

**Overall score: 2.0/10 — Not ready — major rework**

SupportCopilot is a RAG-assisted reply-drafting copilot for support agents, and the spec reads as an early concept sketch rather than a build-ready technical specification. It names the right pieces (Zendesk embed, FastAPI, pgvector retrieval, GPT-4o) but stops at naming them: there are no error/timeout/retry semantics, no API or data schemas, and — most consequential for an LLM product — no observability, no evals, no feedback loop, and no cost model whatsoever. The single most important thing to fix is the **complete absence of an AI-compliance and data-handling story**: customer ticket data (which contains PII) flows to OpenAI with no review of provider data-use terms, no redaction, and no injection defense even though the model ingests untrusted customer text (FND-001). Four areas are effectively absent (Observability, Evals, Feedback, Cost), which is exactly the cluster that hurts most in production for this class of system.

**Gating findings** (the ones that must close before/early in build):
- `FND-001` (Blocker) — Customer PII is sent to OpenAI with no data-use-terms review, no redaction, and no zero-retention/enterprise-endpoint decision → Review OpenAI's data-use/retention terms, choose a zero-retention or enterprise tier, and define a PII-redaction step before the model call.
- `FND-002` (Blocker) — Retrieved articles + raw customer tickets are concatenated into a prompt with no prompt-injection or abuse defense, while the input is attacker-controllable customer text → Add input sandboxing/delimiting, instruction-hierarchy defenses, and output review before send; treat retrieved + ticket content as untrusted.
- `FND-003` (Blocker) — No evaluation strategy of any kind: no golden set, no metric for "good enough," no regression gate → a prompt or model change can silently degrade every agent's drafts → Define accuracy/groundedness/task-success metrics, build a labelled eval set, and gate releases on it.
- `FND-004` (Blocker) — No cost model at all for a token-heavy RAG product (top-5 context + GPT-4o per draft, plus summarize/tone) → cost is unbounded and unbudgeted → Add token-math cost projection grounded in stated volume (DAU, drafts/day, avg tokens) with input/output prices split and scaling/sensitivity.
- `FND-005` (Major) — No observability of model calls (no prompt/completion/token/cost/latency capture, no trace correlation) → a bad draft can't be reconstructed or debugged → Add structured per-call logging and end-to-end trace correlation with a PII-in-traces policy.

**Notable strengths:** The high-level component split (web/backend/retrieval) is sensible and the core RAG happy path is described clearly enough to picture; the technology choices (FastAPI, pgvector, OpenAI) are reasonable defaults for this problem.

## Scorecard

| # | Area | Score | Status |
|---|------|:-----:|--------|
| 1 | Overview & Problem Framing | 4/10 | Weak |
| 2 | Architecture & System Design | 4/10 | Weak |
| 3 | Feature Flows & System Sequencing | 3/10 | Weak |
| 4 | Data Schema & Modeling | 3/10 | Weak |
| 5 | API Contracts | 2/10 | Stub |
| 6 | Libraries, Frameworks & Tech Stack | 4/10 | Weak |
| 7 | Observability & Traceability | 0/10 | Absent |
| 8 | Evaluation Strategy | 0/10 | Absent |
| 9 | Feedback Loops & Continuous Improvement | 0/10 | Absent |
| 10 | AI Compliance, Safety & Governance | 1/10 | Stub |
| 11 | Infrastructure & Environment Setup | 3/10 | Weak |
| 12 | CI/CD & Release Management | 2/10 | Stub |
| 13 | Cost Projection | 0/10 | Absent |
| | **Overall (avg of applicable)** | **2.0/10** | **Not ready — major rework** |

## Area detail

### 1. Overview & Problem Framing — 4/10
**Assessment.** There is a clear "what and why" — help Acme support agents draft replies faster and more consistently — and the user (support agent) and surrounding product (Zendesk console) are identifiable. But success is stated only as adjectives ("faster", "more consistent") with no measurable target, there are no non-goals, and the key assumptions (volume, languages, ticket types, what "good" looks like) are unsurfaced. It frames the problem but doesn't bound it.
**Findings.** FND-006, FND-007.
**Suggestions.** Add measurable success criteria (e.g. target draft-acceptance rate, median time-to-reply reduction, p95 draft latency). State explicit non-goals (e.g. "not auto-sending without an agent in the loop", "English-only in phase 1"). List the load and content assumptions the rest of the spec depends on.
**Strengths.** The problem and primary user are crisp and uncontested.

### 2. Architecture & System Design — 4/10
**Assessment.** The three-part decomposition (React embed, FastAPI backend, retrieval service over Postgres/pgvector) is sound and each component has a recognizable responsibility. However there is no architecture diagram, no discussion of synchronous vs asynchronous boundaries, no failure-mode reasoning (what happens when OpenAI is slow/down, when retrieval returns nothing, when Zendesk's API rate-limits), no scaling or availability targets, and the boundary with Zendesk (auth, embedding model, data sync) is hand-waved. The integration points — exactly where this system's risk lives — are the least specified.
**Findings.** FND-008, FND-009.
**Suggestions.** Add a container-level diagram showing the request path and external dependencies (Zendesk, OpenAI). Document failure modes for each external dependency with intended behavior (degrade, retry, surface error). State throughput/availability expectations and where state lives.
**Strengths.** Clean, justified-enough component separation; retrieval isolated as its own service.

### 3. Feature Flows & System Sequencing — 3/10
**Assessment.** The Draft-reply happy path is narrated (open → click → retrieve top 5 → prompt → GPT-4o → return), which is the strongest part of the doc, but it stops at the happy path. There are no unhappy paths anywhere: no timeout/retry/partial-failure handling for the OpenAI or Zendesk calls, no behavior when retrieval is empty or low-confidence, no sequencing for Summarize or Tone at all, and no statement of sync vs async (these are described as if instantaneous). With ≥3 systems interacting, the absence of any sequence/flow detail beyond one paragraph is a real gap.
**Findings.** FND-010, FND-011.
**Suggestions.** Add an end-to-end sequence for each of the three features showing every hop (web → backend → retrieval → DB → OpenAI → back), marking sync/async, and define the error/timeout/retry path for the OpenAI and Zendesk calls explicitly (including what the agent sees on failure).
**Strengths.** The core retrieval-then-generate chain is described clearly enough to implement the happy path.

### 4. Data Schema & Modeling — 3/10
**Assessment.** The intent is visible — articles and resolved tickets stored with text, an embedding vector, and a source link in Postgres/pgvector, sourced from Zendesk. But there are no field types or constraints, no keys or indexes, no statement of embedding dimensions or the pgvector index type (ivfflat/hnsw) or distance metric, no chunking strategy for long articles/threads, no migration approach, and — critically for this data — no PII classification or retention policy on what is clearly customer content. "We store the text and a vector" is not yet a schema.
**Findings.** FND-012, FND-013.
**Suggestions.** Provide an entity/field table with types, the pgvector index type + dimension + distance metric, the chunking approach and chunk→source mapping, a migration plan, and a PII/retention classification for stored ticket content (including how Zendesk sync handles deletions).
**Strengths.** Choosing pgvector co-located with relational data is a reasonable, low-complexity decision for this scale.

### 5. API Contracts — 2/10
**Assessment.** Three endpoints are named (`POST /draft`, `POST /summarize`, `POST /tone`) and "all endpoints return JSON" — and that is the entire contract. No request or response schemas, no auth model, no error responses or status codes, no versioning, no rate limits, no timeout/streaming behavior for the model calls, and no idempotency. A client engineer could not code against this without asking a question for nearly every field. This is a named placeholder, not a contract.
**Findings.** FND-014, FND-015.
**Suggestions.** For each endpoint, define request/response JSON schemas with examples, the auth mechanism (how the Zendesk-embedded app authenticates to the backend), enumerated error responses with status codes, the model-call contract (timeout, streaming yes/no, token caps), and a versioning strategy. An OpenAPI document would close most of this.
**Strengths.** Endpoint set maps cleanly to the three features.

### 6. Libraries, Frameworks & Tech Stack — 4/10
**Assessment.** Concrete libraries are named for each layer (FastAPI, React, OpenAI SDK, LangChain, pgvector), which is better than "a web framework." But nothing is version-pinned, no choice is justified, and the two consequential decisions are unexamined: **LangChain for orchestration** is introduced with no rationale for a three-prompt app that arguably doesn't need it (and adds lock-in/abstraction cost), and **provider lock-in to OpenAI** (both LLM and embeddings) is not acknowledged. Licensing isn't mentioned.
**Findings.** FND-016, FND-017.
**Suggestions.** Pin versions, justify LangChain vs the raw OpenAI SDK for this surface area (or drop it), and acknowledge OpenAI lock-in for both completion and embeddings with a note on swap cost (changing the embedding model means re-embedding the whole corpus).
**Strengths.** Mainstream, well-supported choices with no exotic dependencies.

### 7. Observability & Traceability — 0/10
**Assessment.** Absent. There is no mention of logging, metrics, tracing, token/cost capture, latency tracking, or request correlation through the retrieval→prompt→model→response pipeline. If an agent reports a bad draft, nothing in this spec lets the team reconstruct what the model saw or produced. For an LLM product this is a required area and it is missing entirely.
**Findings.** FND-005.
**Suggestions.** Specify structured per-call logging (prompt, completion, model+version, tokens in/out, latency, cost), end-to-end trace correlation with a request ID, capture of retrieved chunks and the final assembled prompt for debugging, dashboards/alerts on cost and quality (not just uptime), and a PII-in-traces redaction policy. Name a tool (Langfuse/LangSmith/Phoenix/OTel).
**Strengths.** None — area not addressed.

### 8. Evaluation Strategy — 0/10
**Assessment.** Absent. There is no notion of "good enough," no metrics (faithfulness/groundedness/task success), no golden dataset, no regression gate, no separation of retrieval quality from generation quality, and no safety/guardrail tests. Quality changes would be judged on vibes, and a prompt or model swap could silently degrade every agent's output.
**Findings.** FND-003.
**Suggestions.** Define metrics and a "good enough" bar, build a labelled eval set from real resolved tickets (with provenance), separate retrieval metrics (recall@k) from generation metrics (groundedness/accuracy), wire an eval gate into CI so changes can't merge on regression, and add injection/jailbreak/refusal test cases.
**Strengths.** None — area not addressed.

### 9. Feedback Loops & Continuous Improvement — 0/10
**Assessment.** Absent. The product has an obvious, high-value implicit signal — the agent edits the draft before sending, and accept/reject/edit-distance is a ready-made quality measure — yet there is no capture of it, no path from production data back into eval sets or prompt/retrieval improvement, no prompt/model versioning, and no drift monitoring. This is ship-and-forget.
**Findings.** FND-018.
**Suggestions.** Capture accept/edit/reject and edit-distance per draft, route that signal into the eval set and into retrieval/prompt iteration (the data flywheel), version prompts and model identifiers so a regression traces to a change, and add drift monitoring as ticket mix shifts.
**Strengths.** None — area not addressed.

### 10. AI Compliance, Safety & Governance — 1/10
**Assessment.** Effectively a stub, and the most dangerous gap. Customer ticket data — which routinely contains PII — is sent to OpenAI with no mention of the provider's data-use/training terms, no zero-retention/enterprise-endpoint decision, and no redaction. The system ingests attacker-controllable customer text and concatenates it with retrieved content into a prompt, with no prompt-injection or abuse defense. There is no audit trail, no content-safety check on generated drafts, no human-oversight statement beyond the implicit "agent edits," and no mapping to GDPR/SOC 2 or other applicable regulation. The only thing keeping this above 0 is that an agent-in-the-loop review is implied by the workflow.
**Findings.** FND-001, FND-002, FND-019.
**Suggestions.** Review and document OpenAI data-use/retention terms and select an appropriate tier; add PII redaction before model calls; add prompt-injection defenses (treat ticket + retrieved content as untrusted, delimit, constrain instructions); add content-safety review on outputs; define an audit trail for AI-assisted replies; and map the data flows to GDPR/SOC 2 obligations.
**Strengths.** The agent-edits-before-send workflow provides a baseline human-in-the-loop control (though it is incidental, not a stated safeguard).

### 11. Infrastructure & Environment Setup — 3/10
**Assessment.** A thin sketch: AWS, containerized backend, staging + production, secrets "as environment variables." Environments are at least separated, but there is no IaC (so infra is implicitly click-ops), the secrets approach (env vars) is below the bar for a key as sensitive as the OpenAI key with no rotation or vault, and there is no networking/security-boundary detail, no scaling approach, no backup/DR with RPO/RTO, and no OpenAI quota/rate-limit capacity planning (the AI-era "ran out of capacity" risk).
**Findings.** FND-020, FND-021.
**Suggestions.** Add IaC (Terraform/CDK), move secrets to a managed store (AWS Secrets Manager/Parameter Store) with rotation, define networking boundaries and least-privilege, state a scaling approach and backup/DR with RPO/RTO, and add OpenAI quota/rate-limit planning with a fallback for throttling.
**Strengths.** Staging/production separation is acknowledged from the start.

### 12. CI/CD & Release Management — 2/10
**Assessment.** Barely present: "push to main → auto-deploy via GitHub Actions." That is a deploy trigger, not a release process. There are no quality gates (lint/tests/security scan, and no eval gate for an AI product), no deployment strategy (blue-green/canary) and no rollback plan, no feature flags — meaning a bad prompt or model swap hits 100% of agents at once with no safe rollout — no migration handling, and no versioning/cadence. Auto-deploy-on-main-push without gates is itself a risk.
**Findings.** FND-022, FND-023.
**Suggestions.** Add pipeline gates (lint, unit/integration tests, security scan, eval gate), a canary or gradual rollout with a stated rollback procedure, feature flags for model/prompt changes, safe migration handling in the pipeline, and a versioning/release cadence.
**Strengths.** Deployment is at least automated rather than manual.

### 13. Cost Projection — 0/10
**Assessment.** Absent, and this is a token-heavy RAG product where cost is a first-order design concern. There is no infrastructure cost, no LLM/API token math, no embeddings cost, no Zendesk/third-party cost, no volume assumptions, no scaling/sensitivity, no unit economics, and no cost-control levers — despite every draft pulling top-5 context into a GPT-4o call plus optional summarize/tone calls that multiply token spend. Cost is entirely unbounded as specified.
**Findings.** FND-004.
**Suggestions.** State volume assumptions (agents, drafts/agent/day, avg input/output tokens), compute LLM cost from token math with input vs output prices split per model plus embeddings, add infra and Zendesk costs, show cost at 1×/10×/100× load with a per-draft unit cost, and name levers (caching, context trimming, a smaller model for summarize/tone).
**Strengths.** None — area not addressed.

## Findings register

> Sorted by severity (Blockers first). Every deducted point traces to a finding here; every finding has a suggested fix. `Area` is the area code.

| ID | Sev. | Area | Finding | Suggested fix |
|----|------|------|---------|---------------|
| FND-001 | Blocker | CMP | Customer ticket PII is sent to OpenAI with no review of provider data-use/training terms, no zero-retention/enterprise-endpoint decision, and no redaction — a data-privacy and contractual exposure. | Review OpenAI data-use/retention terms, select a zero-retention/enterprise tier, and add a PII-redaction step before any model call; map flows to GDPR/SOC 2. |
| FND-002 | Blocker | CMP | Untrusted customer ticket text (plus retrieved content) is concatenated into the prompt with no prompt-injection or abuse defense, in a system whose input is attacker-controllable. | Treat ticket + retrieved content as untrusted: delimit/sandbox it, enforce instruction hierarchy, and review outputs before they reach the agent. |
| FND-003 | Blocker | EVL | No evaluation strategy at all — no golden set, no quality metric, no regression gate — so a prompt or model change can silently degrade every agent's drafts. | Define groundedness/accuracy/task-success metrics, build a labelled eval set from resolved tickets, and gate CI on it (retrieval and generation metrics separately). |
| FND-004 | Blocker | CST | No cost model whatsoever for a token-heavy RAG product (top-5 context + GPT-4o per draft, plus summarize/tone); running cost is unbounded and unbudgeted. | Add token-math cost projection grounded in stated volume, input/output prices split, embeddings + infra + Zendesk costs, and 1×/10×/100× scaling with a per-draft unit cost. |
| FND-005 | Major | OBS | No observability of model calls — no prompt/completion/token/cost/latency capture and no trace correlation — so a bad draft can't be reconstructed or debugged. | Add structured per-call logging (prompt, completion, model+version, tokens, latency, cost) and end-to-end trace correlation, with a PII-in-traces redaction policy. |
| FND-006 | Major | OVR | Success is defined only qualitatively ("faster", "more consistent") with no measurable target, so "done/good" is unfalsifiable. | Add measurable success criteria: draft-acceptance rate, time-to-reply reduction, p95 draft latency. |
| FND-007 | Major | OVR | No non-goals or stated assumptions (volume, languages, ticket types), leaving scope unbounded. | State explicit non-goals and the load/content assumptions the design depends on. |
| FND-008 | Major | ARC | No failure-mode or availability reasoning for external dependencies (OpenAI slow/down, empty retrieval, Zendesk rate-limit), where most of the risk lives. | Document intended behavior per dependency failure (degrade/retry/surface) and state availability/throughput expectations. |
| FND-009 | Minor | ARC | No architecture diagram and the Zendesk integration boundary (auth, data sync) is hand-waved. | Add a container-level diagram and specify the Zendesk auth/embedding/data-sync contract. |
| FND-010 | Major | FLW | Only the happy path is described; no timeout/retry/partial-failure handling for OpenAI/Zendesk calls and no behavior on empty/low-confidence retrieval. | Define error/timeout/retry paths and the empty-retrieval fallback, including what the agent sees on failure. |
| FND-011 | Minor | FLW | Summarize and Tone features have no flow/sequencing at all, and sync vs async is unstated for all three. | Add an end-to-end sequence for each feature marking sync/async hops. |
| FND-012 | Major | DAT | No PII classification or retention policy on stored customer ticket content, and no handling of Zendesk-side deletions. | Add PII/retention classification and a deletion-propagation plan for synced ticket data. |
| FND-013 | Minor | DAT | No field types/constraints, keys/indexes, embedding dimension, pgvector index type/metric, chunking strategy, or migration plan. | Provide a typed field table, pgvector index type + dimension + distance metric, chunking + chunk→source mapping, and a migration approach. |
| FND-014 | Major | API | Endpoints have no request/response schemas, no auth model, and no error responses/status codes — uncodeable without asking. | Define request/response JSON schemas with examples, the auth mechanism, and enumerated error responses with status codes (ideally an OpenAPI doc). |
| FND-015 | Minor | API | No model-call contract (timeout, streaming, token caps), no versioning, no rate limits, no idempotency. | Specify timeout/streaming/token caps, a versioning strategy, rate limits, and idempotency where applicable. |
| FND-016 | Minor | LIB | LangChain is adopted for orchestration with no rationale for a three-prompt app, adding abstraction and lock-in cost. | Justify LangChain vs the raw OpenAI SDK for this surface, or drop it. |
| FND-017 | Minor | LIB | OpenAI provider lock-in (LLM + embeddings) is unacknowledged; no versions are pinned. | Acknowledge swap cost (re-embedding the corpus to change embedding model) and pin library versions. |
| FND-018 | Major | FBK | No feedback capture despite an obvious implicit signal (agent edits before send) and no path from production data back into improvement; no prompt/model versioning or drift monitoring. | Capture accept/edit/reject + edit-distance, route it into eval/iteration, version prompts/models, and add drift monitoring. |
| FND-019 | Minor | CMP | No audit trail for AI-assisted replies and no content-safety review on generated drafts. | Define an audit trail and an output content-safety check. |
| FND-020 | Major | INF | Secrets (incl. the OpenAI key) stored as plain environment variables with no managed store or rotation; no IaC. | Move secrets to a managed store with rotation and adopt IaC for reproducible environments. |
| FND-021 | Minor | INF | No scaling approach, no backup/DR with RPO/RTO, and no OpenAI quota/rate-limit capacity planning. | Add scaling, backup/DR (RPO/RTO), and OpenAI quota planning with a throttling fallback. |
| FND-022 | Major | CICD | Auto-deploy on main-push with no quality gates (tests/lint/security/eval) and no rollback plan — a bad change reaches all users unguarded. | Add pipeline gates (incl. an eval gate), a rollback procedure, and gradual rollout. |
| FND-023 | Minor | CICD | No feature flags for model/prompt changes and no versioning/release cadence, so risky AI changes hit 100% at once. | Add feature flags for model/prompt swaps and a versioning/release cadence. |

## Clarifying questions for the author

> Things that look missing but may simply be undocumented or live in a companion doc — ask before assuming. Resolving these may move scores.

1. Is there a companion doc (SRS, ERD, OpenAPI spec, or security/privacy review) that covers the data schema, API contracts, or the OpenAI data-handling terms? If so, this review should reference it.
2. What are the expected volumes (number of agents, drafts/agent/day, average ticket length)? These are needed before any cost or scaling assessment is meaningful.
3. Has the OpenAI data-processing agreement / zero-retention option been evaluated, and is sending customer PII to OpenAI already approved by Acme's privacy/legal function?
4. Is the agent-edit-before-send step a deliberate, enforced safeguard (no auto-send), and is it intended as the primary human-oversight control?
5. Is LangChain a firm decision, or is the orchestration approach still open?

## Recommended next actions

1. Close the four Blockers first: resolve the OpenAI data-handling/PII story (FND-001), add prompt-injection defenses (FND-002), define an eval strategy with a CI gate (FND-003), and produce a token-grounded cost model (FND-004). These gate the build.
2. Build out the Applied-AI operational layer that is currently absent — observability/tracing (FND-005) and feedback capture (FND-018) — since these are what make the system debuggable and improvable in production.
3. Bring the engineering contracts up to build-ready: complete API schemas, auth, and error codes (FND-014/015), and the data schema with PII/retention (FND-012/013); then harden delivery with pipeline gates, rollback, and feature flags (FND-022/023) and managed secrets + IaC (FND-020).
