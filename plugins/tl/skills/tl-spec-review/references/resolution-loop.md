# Finding Resolution Loop

A review doesn't end when the report is written — each finding is an **open item** the author has to answer. This file defines how those items get closed: the finding lifecycle, how the author's responses come back, how the agent **adjudicates** each one (accept, push back, or ask for more), how findings close and re-score, and how the closed decisions are documented. Read this for `/tl:resolve`; read `review-rubric.md` for the original scoring.

The whole point is **convergence with a paper trail**: open → responded → (verify ⟳) → resolved, with the rationale recorded so a reader six weeks later knows *why* a Blocker was closed, not just that it was.

---

## 1. Finding lifecycle

Every `FND-###` carries a `status` (controlled values):

| Status | Meaning |
|--------|---------|
| `Open` | Raised, no adequate response yet. (Initial state for every finding.) |
| `Responded` | The author has answered; awaiting adjudication. (Transient — the agent moves it on in the same run.) |
| `Needs-verification` | Response is plausible but incomplete or unverifiable; the agent asked specific follow-ups. Still open. |
| `Resolved` | The response adequately addresses the concern. Closed. |
| `Accepted-risk` | The concern is valid and unfixed, but the author has *explicitly* acknowledged and accepted the risk. Closed, with residual risk noted. |
| `Won't-fix` | The author declines and the agent records why it remains a gap. Closed as unaddressed. |

`Resolved`, `Accepted-risk`, and `Won't-fix` are **terminal**. Keep the original finding text unchanged forever — closure is recorded in a *resolution thread* attached to the finding, never by editing the finding away.

## 2. Round model — stable IDs carry findings forward

- **Round 1** is the initial `/tl:review`: all findings `Open`.
- Each `/tl:resolve` is the **next round**: a new timestamped report whose `priorReview` points back to the report being resolved. Findings carry forward **by their stable `FND-###` ID** (append-only, per `delivery-os-conventions`), so FND-018 in round 2 is the same item as FND-018 in round 1 — only its status and resolution thread change.
- The `<timestamp>` (the `reviewId`) is the **join key**: a responses file names the review it came from, and `/tl:resolve` matches it to that review's `.json` state. New findings discovered during resolution get fresh IDs continuing the sequence.

## 3. The responses file (input to `/tl:resolve`)

The interactive HTML report's **"Export responses"** button generates this Markdown and downloads it pre-named `spec-review-<reviewId>-responses.md`. The author can also hand-write or edit it. Format:

```markdown
---
doc_type: spec-review-responses
source_review: 2026-06-25-162658        # the reviewId being answered — the join key
spec: support-copilot-spec.md
generated_at: 2026-06-25 17:10
---

# Responses to spec-review-2026-06-25-162658

## FND-018 — [Blocker · CMP] Customer PII sent to Azure OpenAI…
**Intent:** resolve            # resolve | accept-risk | need-info | wont-fix  (a hint, not binding)
**Response:**
We use Azure AI Foundry in West Europe under our enterprise DPA; modified abuse monitoring
approved (zero retention). Legal basis for vendor personal data = contract.

## FND-010 — [Blocker · API] No request/response schemas…
**Intent:** need-info
**Response:**
There's an OpenAPI file at api/openapi.yaml — we'll reference it in §5.
```

Parse by the `## FND-###` headers; read each finding's `Intent` and `Response`. A finding with a blank or missing response stays `Open` — don't invent a resolution. `Intent` is the author's *requested* outcome; the agent decides the actual status (it is not bound by the hint).

## 4. Adjudication — judge each response, don't rubber-stamp

For every finding with a non-empty response, decide its new status. **Be fair but skeptical** — the value of the loop is that the agent actually checks the answer rather than closing on a vague assurance.

- **→ `Resolved`** when the response *substantively answers the concern* with verifiable specifics. "We turned on the in-region endpoint and have the signed DPA" resolves; "we'll handle security" does not. For compliance/security/cost findings, require concrete facts (region, config state, approval status, numbers), not intentions.
- **→ `Accepted-risk`** when the author acknowledges the concern is real, won't fix it now, and *explicitly accepts the risk*. Record the residual risk plainly. (Don't infer acceptance from silence — it must be stated.)
- **→ `Needs-verification`** when the answer is plausible but thin, unverifiable, or raises a new question. Ask **1–3 targeted follow-ups** that would close the gap (e.g. *"Is the modified-abuse-monitoring approval granted or still pending? Which Azure region?"*). The finding stays open into the next round.
- **→ `Open` (unchanged)** when the response doesn't address the finding — say why.
- **→ `Won't-fix`** only when the author clearly declines; record the agent's note on the residual gap.

Write a short **adjudication rationale** for every decision — one or two sentences on *why* this status. This is the audit trail.

Where a resolution implies the **spec should change** (it usually does — the answer ought to live in the document, not just the review), give the **concrete spec edit** to make. "Add to §10: 'Azure OpenAI processes data in West Europe under the enterprise DPA; modified abuse monitoring is approved (zero retention); legal basis for vendor personal data is contract.'" Baking the answer into the spec is what actually closes the gap at the source — a later `/tl:review` of the updated spec should then find nothing.

## 5. Re-score and recompute the verdict

Closing findings changes the picture, so recompute:
- Raise an **area score** when its findings resolve (a `DAT` area stuck at 3/10 by a Blocker may rise once that Blocker is `Resolved`). Re-judge against `review-rubric.md` using the finding-anchoring rule — don't just bump arbitrarily.
- Recompute the **overall score** (average of applicable areas) and the **readiness verdict**. A resolved Blocker **lifts the verdict cap**. `Accepted-risk` also lifts the cap *only if* the acceptance is explicit and documented — but call out the residual risk in the executive summary. `Needs-verification` and `Open` Blockers keep the cap.
- Track progress in the executive summary: *"Round 2: 3 of 4 Blockers resolved, 1 awaiting verification; overall 2.0 → 6.1, verdict Not ready → Significant gaps."*

## 6. Document the closure — decision-log (`DEC`) export

When a finding reaches a terminal status (`Resolved` / `Accepted-risk` / `Won't-fix`) **and a Delivery OS workspace exists**, append a row to `shared-context/decision-log.md` so the decision persists for the BA/Doc agents beyond this review snapshot:

| DEC | Decision | Rationale | Source | Date |
|-----|----------|-----------|--------|------|
| DEC-007 | Azure OpenAI used in West Europe under enterprise DPA, zero retention (modified abuse monitoring) | Resolves PII/data-residency concern for invoice processing | FND-018 (spec-review round 2) | 2026-07-02 |

Use the `DEC-###` id format from `delivery-os-conventions` (append-only). Record the finding's `decisionId` back in the review data so the report links the two. If there's no workspace, skip the DEC export and keep the resolution in the report only.

## 7. Output of a resolve round

`/tl:resolve` writes a **new timestamped review round** — `.html` / `.md` / `.json` — carrying every finding forward with its updated status and resolution thread (responses, adjudication, follow-up questions, decisionId), the recomputed scores and verdict, and any new `DEC` rows. Then summarize in chat: how many resolved / accepted-risk / awaiting-verification (with the open questions) / still open, and the score+verdict movement. The loop repeats — export responses from the new report, resolve again — until no open items remain.
