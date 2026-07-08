# Scope-Question Resolution Loop

A scope review doesn't end when the report is written — each question is an **open item** the author has to answer. This file defines how those items get closed: the question lifecycle, how the author's responses come back, how the agent **adjudicates** each one, how questions close and re-score, and — uniquely for the BA — how a closed answer is **promoted back into the scope and the BA registers** so the gap is fixed at the source. Read this for `/ba:resolve`; read `review-rubric.md` for the original scoring.

The point is **convergence with a paper trail**: open → responded → (verify ⟳) → resolved, with each closure recorded *and folded back into `scope.md` and the registers*, so a later `/ba:review` of the updated scope finds nothing.

---

## 1. Question lifecycle

Every `SQ-###` carries a `status` (controlled values):

| Status | Meaning |
|--------|---------|
| `Open` | Raised, no adequate response yet. (Initial state for every question.) |
| `Responded` | The author has answered; awaiting adjudication. (Transient — moved on in the same run.) |
| `Needs-verification` | Response is plausible but incomplete or unverifiable; the agent asked specific follow-ups. Still open. |
| `Resolved` | The response adequately answers the question. Closed. |
| `Accepted-assumption` | The answer isn't a confirmed fact but an explicit, accepted **assumption** the team will proceed on. Closed, with the assumption logged. |
| `Won't-fix` | The author declines / defers and the agent records why the gap remains. Closed as unaddressed. |

`Resolved`, `Accepted-assumption`, and `Won't-fix` are **terminal**. Keep the original question text unchanged forever — closure is recorded in a *resolution thread* attached to the question, never by editing the question away.

## 2. Round model — stable IDs carry questions forward

- **Round 1** is the initial `/ba:review`: all questions `Open`.
- Each `/ba:resolve` is the **next round**: a new timestamped report whose `priorReview` points back to the report being resolved. Questions carry forward **by their stable `SQ-###` ID** (append-only), so SQ-004 in round 2 is the same item as SQ-004 in round 1 — only its status and resolution thread change.
- The `<timestamp>` (the `reviewId`) is the **join key**: a responses file names the review it came from, and `/ba:resolve` matches it to that review's `.json`. New questions discovered during resolution get fresh IDs continuing the sequence.

## 3. The responses file (input to `/ba:resolve`)

The HTML report's **"Export responses"** button generates this Markdown and downloads it pre-named `scope-review-<reviewId>-responses.md`. The author can also hand-write or edit it. Format:

```markdown
---
doc_type: scope-review-responses
source_review: 2026-06-30-143012        # the reviewId being answered — the join key
scope: ba-output/scope.md
generated_at: 2026-06-30 17:10
---

# Responses to scope-review-2026-06-30-143012

## SQ-004 — [Blocker · AUTH] Which authentication methods are in scope?
**Intent:** resolve            # resolve | accept-assumption | need-info | wont-fix  (a hint, not binding)
**Response:**
Email/password plus Google SSO. Corporate domains only; email is verified; MFA optional in phase 1.
Registration and password reset are in scope; profile management is phase 2.

## SQ-011 — [Blocker · CRM] Which CRM are we integrating with?
**Intent:** need-info
**Response:**
Still confirming with the client — likely Salesforce, awaiting their admin.
```

Parse by the `## SQ-###` headers; read each question's `Intent` and `Response`. A question with a blank or missing response stays `Open` — don't invent a resolution. `Intent` is the author's *requested* outcome; the agent decides the actual status (it is not bound by the hint).

## 4. Adjudication — judge each response, don't rubber-stamp

For every question with a non-empty response, decide its new status. **Be fair but skeptical** — the value of the loop is that the agent actually checks the answer rather than closing on a vague assurance.

- **→ `Resolved`** when the response *substantively answers the question* with specifics a team could estimate against. "Email/password + Google SSO, corporate domains, email verified, MFA optional" resolves SQ-004; "we'll sort out login" does not. For Blockers (auth, integration partner, volume, compliance), require concrete facts, not intentions.
- **→ `Accepted-assumption`** when the client can't confirm now but the team will **proceed on an explicit assumption**. Record the assumption and its risk plainly (it becomes an `ASM-###` / RAID A-##). Don't infer acceptance from silence — it must be stated.
- **→ `Needs-verification`** when the answer is plausible but thin, unverifiable, or raises a new question. Ask **1–3 targeted follow-ups** that would close it (e.g. *"Salesforce which edition, and is a sandbox available? Who owns the CRM side?"*). The question stays open into the next round.
- **→ `Open` (unchanged)** when the response doesn't address the question — say why.
- **→ `Won't-fix`** only when the author clearly declines or defers out of phase; record the residual gap (and, if it's being pushed to T&M / a later phase, say so).

Write a short **adjudication rationale** for every decision — one or two sentences on *why* this status. This is the audit trail.

## 5. Promote the answer into the scope and registers (the BA-specific step)

A scope review exists to **improve the scope**, so closing a question means putting the answer where it belongs — not just marking it done in the report. For each terminal question, give the **concrete scope edit** and promote it (only when a Delivery OS workspace exists):

- **`Resolved` (confirmed fact)** → state the exact edit to `ba-output/scope.md` (which §3.x sub-heading, what text), and append a `DEC-###` row to `shared-context/decision-log.md`. Set the question's `decisionId`.
- **`Accepted-assumption`** → add an `ASM-###` row to `ba-output/assumption-register.md` (assumption, reason, risk, validation needed) — this is the RAID Assumptions `A-##` feed — and reference it from scope §7. Note the edit to the relevant §3.x.
- **`Needs-verification` / still `Open`** (must-close items) → ensure a `CLR-###` exists in `ba-output/clarification-log.md` (the RAID Open-Questions `Q-##` feed) carrying the follow-ups, so the open question lives in the BA's own tracking, not only in the review.
- **`Won't-fix` / deferred** → record it as out-of-scope/phase-2 in scope §6 or the relevant §3.x.2, and log the decision (`DEC-###`) so the deferral is auditable.

Baking the answer into `scope.md` is what actually closes the gap — a later `/ba:review` of the updated scope should then find nothing. Use the `DEC-###` / `ASM-###` / `CLR-###` id formats from `delivery-os-conventions` (append-only). If there's no workspace, skip the promotions and keep the resolution in the report only (note that the edits still need applying).

## 6. Re-score and recompute the verdict

Closing questions changes the picture, so recompute:
- Raise a **feature score** when its questions resolve (an `AUTH` feature stuck at 2/10 by a Blocker may rise once the auth method is `Resolved` and the coverage map fills in). Re-judge against `review-rubric.md` using the score↔question anchoring — don't just bump arbitrarily; update the feature's `coverage` map to reflect what the answer added.
- Recompute the **overall score** (average of features) and the **scope-readiness verdict**. A resolved Blocker **lifts the verdict cap**. `Accepted-assumption` also lifts the cap *only if* the assumption is explicit and logged — but call out the residual risk in the executive summary. `Needs-verification` and `Open` Blockers keep the cap.
- Track progress in the executive summary: *"Round 2: 1 of 2 Blockers resolved, 1 awaiting verification; overall 3.4 → 6.2, verdict Significant gaps → Estimate with caveats."*

## 7. Output of a resolve round

`/ba:resolve` writes a **new timestamped review round** — `.html` / `.md` / `.json` (render the `.html` the same UTF-8-safe way as a fresh review: write the `.json` sidecar first, then `node assets/inject.js assets/report.html <round>.json __REVIEW_DATA__ <round>.html` — never hand-assemble the HTML) — carrying every question forward with its updated status and resolution thread (response, adjudication, follow-ups, the promoted `DEC`/`ASM`/`CLR` id), the recomputed scores and verdict, and the list of scope edits to apply (or applied). Then summarise in chat: how many resolved / accepted-as-assumption / awaiting-verification (with the open follow-ups) / still open, the score+verdict movement, and which registers were updated. The loop repeats — export responses from the new report, resolve again — until no open items remain.
