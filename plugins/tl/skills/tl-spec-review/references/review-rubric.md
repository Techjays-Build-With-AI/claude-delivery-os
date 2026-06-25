# Review Rubric — per-area checks, red flags, and scoring guidance

This is the detailed knowledge behind the 13 review areas in `SKILL.md`. For each area: what a **strong** spec contains, the **specific things to check**, and the **red flags** that should cost points. Use the scoring bands in `SKILL.md` §4 — these notes tell you *what evidence* moves a score within those bands.

Don't treat any list as a checkbox quota. A spec can score 9/10 without every bullet if the system genuinely doesn't need it; conversely, ticking every box shallowly isn't an 8. Judge whether a competent team could **build the right thing** from what's written.

---

## A — Architecture & Design

### 1. Overview & Problem Framing (`OVR`)
**Strong looks like:** a crisp statement of the problem and who has it; the goals and **measurable** success criteria (latency, accuracy, adoption, cost-per-transaction); explicit scope and non-goals; the key assumptions and constraints; the primary users/personas; and how this fits the wider product.
**Check:** Is there a single clear "what are we building and why"? Are success criteria measurable or just adjectives ("fast", "scalable")? Are non-goals stated (the cheapest way to prevent scope creep)? Are assumptions surfaced rather than buried?
**Red flags:** jumps straight into components with no problem statement; success defined only qualitatively; no non-goals; conflates "what" with "how" so early that requirements and design are tangled.

### 2. Architecture & System Design (`ARC`)
**Strong looks like:** at least one architecture diagram (context/container level), each component with a clear single responsibility, explicit boundaries and who-owns-what, the data-flow between components, justified technology choices (why this datastore, this queue, this pattern), and explicit thinking about scale, availability, and failure modes (what happens when a dependency is down).
**Check:** Does a diagram exist and does the prose match it? Is every box's responsibility clear, or are there god-components? Are synchronous vs asynchronous boundaries identified? Are state, caching, and the source of truth for each entity clear? Is there any non-functional reasoning (throughput targets, SLOs, single points of failure)?
**Red flags:** no diagram, or a diagram that contradicts the text; components defined by technology ("the Redis box") rather than responsibility; no failure-mode or scaling discussion; "we'll use microservices" with no rationale or boundaries; hand-waving at the integration points where most risk lives.

### 3. Feature Flows & System Sequencing (`FLW`)
**Strong looks like:** for each significant feature, an end-to-end flow showing the systems/services touched in order, what data moves at each hop, which calls are synchronous vs async (queues, events, webhooks, callbacks), where state is persisted, and — critically — the **unhappy paths**: timeouts, retries, partial failures, compensating actions, idempotency.
**Check:** Can you trace a user action from entry to completion across every system? For AI features, is the full chain shown (retrieval → prompt assembly → model call → post-processing → response → logging)? Are long-running/async operations modeled (job status, polling, callbacks) rather than assumed instant? What happens when step 3 of 5 fails?
**Red flags:** only the happy path; "the service calls the API" with no sequencing for multi-system interactions; no retry/timeout/error semantics; async operations described as if synchronous; no sequence or flow diagrams when ≥3 systems interact. Scope this to the system: a single deterministic service needs its request lifecycle, not inter-service diagrams.

---

## B — Engineering Contracts

### 4. Data Schema & Modeling (`DAT`)
**Strong looks like:** the core entities and their relationships (an ERD or equivalent), field-level definition with types and constraints, primary/foreign keys and indexing strategy for the main access patterns, a migration/versioning approach, **PII/sensitivity classification**, and data-retention/lifecycle rules. For AI systems: how embeddings/vectors are stored and indexed, and how source documents map to chunks.
**Check:** Are entities and relationships unambiguous? Are types and required/nullable stated, or just field names? Is there an indexing/access-pattern story, or will this table-scan at scale? Is PII flagged and is retention defined? Is there a plan for schema evolution?
**Red flags:** field names with no types or constraints; no keys/indexes; no PII classification on data that clearly contains it; no migration strategy; vector storage hand-waved ("we'll put it in a vector DB") with no dimensions, index type, or metadata schema.

### 5. API Contracts (`API`)
**Strong looks like:** each endpoint (or RPC/event) with method/path, request and response schemas (fields, types, examples), authentication/authorization, **error responses with status codes**, versioning strategy, rate limits, pagination for collections, and idempotency for unsafe operations. For AI features: the model-call contract — input shape, output shape (and how structured output is enforced), streaming behavior, timeout, and token limits. An OpenAPI/AsyncAPI spec is a strong signal.
**Check:** Is every endpoint's contract complete enough to code a client against without asking? Are error cases enumerated, not just the 200? Is auth specified per endpoint? Are idempotency keys defined where retries could double-act (payments, job creation)? Is versioning thought through so changes don't break clients?
**Red flags:** endpoints listed by name only; no error/status-code definitions; no auth model; no idempotency on operations that mutate money or state; "returns JSON" with no schema; webhooks/events with no payload contract or delivery guarantees.

### 6. Libraries, Frameworks & Tech Stack (`LIB`)
**Strong looks like:** named, ideally version-pinned libraries and frameworks for each layer; a short rationale for the non-obvious choices; awareness of maturity/maintenance and community; license compatibility (especially for anything redistributed or AGPL/GPL); and a note on lock-in or migration cost for hard-to-reverse choices (e.g. the orchestration framework, the vector DB, the model provider SDK).
**Check:** Are concrete libraries named or is it "a web framework"? Are critical choices justified? Any abandoned/single-maintainer dependencies on the critical path? Licensing reviewed? For AI: is the model-orchestration approach (raw SDK vs LangChain/LlamaIndex/etc.) chosen deliberately, and is provider lock-in acknowledged?
**Red flags:** stack described only by language; no versions anywhere; trendy library chosen with no rationale; license risk ignored; heavy framework adopted for a problem that doesn't need it; no acknowledgment of provider/framework lock-in for the components that are expensive to swap later.

---

## C — Applied AI / LLM Engineering  *(N/A for non-AI systems)*

These are the areas teams most often under-specify, and the ones that cause the most production pain. Hold the bar here.

### 7. Observability & Traceability (`OBS`)
**Strong looks like:** structured logging of each model interaction (prompt, completion, model+version, token counts, latency, cost), end-to-end **trace correlation** so one user request can be followed through retrieval → prompt → model → post-processing, captured intermediate state for debugging a bad generation (retrieved chunks, final prompt, raw output), dashboards/alerts on latency/error/cost/quality, and a deliberate policy on **PII in traces** (what's redacted before logging). Tooling named (LangSmith, Langfuse, Phoenix, OpenTelemetry, Helicone, etc.) is a plus.
**Check:** If a user reports a bad answer, can the team reconstruct exactly what the model saw and produced? Are prompt/response/token/cost captured per call? Is there request correlation across the pipeline? Are there alerts on cost and quality regressions, not just uptime? Is sensitive data handled before it lands in logs?
**Red flags:** "we'll add logging" with no mention of prompts/tokens/cost; no traceability from output back to inputs; no way to debug a specific generation; PII logged verbatim; observability treated as ordinary app logging with no AI-specific signals.

### 8. Evaluation Strategy (`EVL`)
**Strong looks like:** a defined notion of "good enough" with metrics (accuracy/faithfulness/groundedness/task success/safety), an offline **eval set / golden dataset** with provenance, **regression gates in CI** so a prompt or model change can't silently degrade quality, online/production evals (sampling, human review, LLM-as-judge with its own validation), and guardrail/safety test cases (injection, jailbreak, refusal behavior). For RAG: retrieval metrics (recall/precision) separate from generation metrics.
**Check:** How will they know a change made things better or worse — vibes or measurement? Is there a dataset, and where did it come from? Do evals gate releases or just exist? Is LLM-as-judge itself validated against human labels? Are failure modes (hallucination, injection) explicitly tested?
**Red flags:** no evals at all (very common, score it honestly); "we'll test manually"; metrics named but no dataset; evals that don't gate anything; LLM-as-judge trusted blindly; no separation of retrieval vs generation quality in a RAG system.

### 9. Feedback Loops & Continuous Improvement (`FBK`)
**Strong looks like:** explicit/implicit user feedback capture (thumbs, corrections, accept/reject, downstream signals), a path from production data back into eval sets and prompt/model improvement (the data flywheel), a prompt/model iteration and versioning process, a RAG-refresh or fine-tune-retrain cadence where relevant, and **drift/quality monitoring** that catches degradation over time. Human-in-the-loop review where stakes are high.
**Check:** How does the system get better after launch? Is production signal captured and is there a route for it to improve the model/prompts/retrieval? Are prompts and model versions tracked so a regression can be traced to a change? Is there monitoring for input/output drift?
**Red flags:** ship-and-forget with no feedback capture; feedback collected but with no path to improvement; no prompt/version control; no drift monitoring; no plan for the inevitable quality decay as inputs shift.

### 10. AI Compliance, Safety & Governance (`CMP`)
**Strong looks like:** data privacy and residency handled (where data goes, which regions), the model provider's **data-use/training terms** reviewed (is customer data used to train? zero-retention endpoints?), PII redaction before model calls where required, prompt-injection and abuse defenses, content-safety/moderation, hallucination mitigation appropriate to the stakes (citations, grounding, confidence thresholds, human review), audit trails for AI decisions, clear human oversight and accountability, and mapping to applicable regulation (GDPR, HIPAA, SOC 2, the EU AI Act risk tier, sector rules).
**Check:** Does customer data leave the boundary, and is that contractually safe? Is PII sent to the provider, and is that allowed? What stops prompt injection from exfiltrating data or abusing tools? For consequential decisions, is there human oversight and an audit trail? Are the relevant regulations identified and addressed rather than ignored?
**Red flags:** no mention of provider data-use terms; PII sent to third-party models with no review; no injection/abuse defense for a system that takes untrusted input or has tools; no audit trail for automated decisions that affect people; regulation hand-waved; safety treated as a content filter bolted on at the end.

---

## D — Delivery & Operations

### 11. Infrastructure & Environment Setup (`INF`)
**Strong looks like:** defined environments (dev/staging/prod) with parity, infrastructure-as-code (Terraform/Pulumi/CloudFormation/Helm), networking and security boundaries (VPC, ingress, least privilege), **secrets management** (vault/parameter store, key rotation — never secrets in code/env files), scaling approach (horizontal/vertical, autoscaling triggers), and backup/disaster-recovery with stated RPO/RTO.
**Check:** Is infra reproducible (IaC) or click-ops? Are environments separated with prod-like staging? How are secrets and API keys managed? Is there a scaling and a backup/DR story? For AI: GPU/inference infra or managed-API capacity and quota planning.
**Red flags:** no IaC; single environment; secrets in repos or plaintext; no scaling plan; no backup/DR; no quota/rate-limit planning against the model provider (the AI-era "ran out of capacity" outage).

### 12. CI/CD & Release Management (`CICD`)
**Strong looks like:** an automated build→test→deploy pipeline, quality gates (lint, unit/integration tests, security scan, and for AI, eval gates), a deployment strategy (blue-green/canary/rolling) with a **rollback** plan, feature flags for decoupling deploy from release and for gradual rollout, environment promotion, and a versioning/release cadence. Migrations handled safely in the pipeline.
**Check:** Is deployment automated and repeatable? What gates block a bad release? Can they roll back quickly, and is the procedure stated? Are feature flags used for risky changes (model swaps, prompt changes)? Is there a release cadence and changelog discipline?
**Red flags:** manual deploys; no automated tests in the pipeline; no rollback plan; no canary/gradual rollout for a system where a bad model/prompt change hits all users at once; database migrations run by hand; no versioning strategy.

### 13. Cost Projection (`CST`)
**Strong looks like:** a running-cost estimate broken into **infrastructure** (compute/storage/network/managed services), **LLM/API** (token-based math: tokens-per-request × requests-per-period × price, by model, separating input/output token prices, plus embeddings), and **third-party services** (per-seat/per-call SaaS, data providers). The estimate is grounded in **stated volume assumptions** (DAU, requests/user/day, average tokens), shows how cost **scales** with load, ideally gives a per-transaction/per-user **unit economic**, and names cost-control levers (caching, smaller models, prompt compression, batching). A range or sensitivity (low/expected/high) beats a single false-precision number.
**Check:** Are the volume assumptions stated, or is the number conjured? Is LLM cost computed from token math rather than guessed? Are input vs output token prices distinguished (output is usually pricier)? Does the projection show cost at 1×, 10×, 100× load? Is there a per-unit cost so the business can reason about margin? Are obvious cost risks (a retry storm, an unbounded-context RAG call, a chatty agent loop) acknowledged?
**Red flags:** no cost section; a single number with no assumptions; LLM cost ignored or wildly hand-waved; no scaling/sensitivity; third-party SaaS costs omitted; no unit economics; no cost-control levers; ignores that token-heavy patterns (large context, multi-step agents) dominate cost. If the system has no LLM, the LLM portion is N/A but infra + third-party cost still apply.

---

## Calibration notes

- **Let the findings anchor the score.** The two are linked, so use one to sanity-check the other: an area with an unresolved **Blocker** rarely scores above 4; one with **Major** gaps lands around 3–6; only **Minor**/**Nit** findings is a 7–8; no real findings is 9–10. An area that's entirely absent but required is 0; a heading with no substance is 1–2. If your score and your findings disagree (a 7 with a Blocker, or a 3 with only nits), one of them is wrong — reconcile before finalizing.
- **Score the document, not the system.** A brilliant system with a thin spec scores low here; that's correct — the spec is the artifact a team builds from.
- **Severity drives the verdict, not finding count.** Five Nits is a healthy 8; one undefined-idempotency-on-payments Blocker can cap an otherwise-good spec.
- **Reward stated assumptions.** A spec that says "we assume 10k requests/day, revisit at scale" is *stronger* than one that silently omits the number — surfaced uncertainty beats hidden uncertainty.
- **N/A is a real verdict.** Don't invent AI findings for a CRUD app or penalize a single-service system for lacking cross-system diagrams. Mark N/A, say why, and exclude it from the average.
- **The most valuable findings are the ones the author can't see.** Anyone can note a missing diagram. The review earns its keep by catching the retry that double-charges, the PII that flows to a third-party model under training terms, the agent loop with no token ceiling, the eval suite that gates nothing.
