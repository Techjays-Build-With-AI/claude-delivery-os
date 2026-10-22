# Report Template — review data object + `scope-review.md`

The review is produced once as a structured **data object**, then rendered into two files: the interactive `scope-review-<timestamp>.html` (injected with `assets/inject.js` — see §2) and the Markdown `scope-review-<timestamp>.md` (structure below). Build the data object first; both renders derive from it so they can't drift.

**There is no `.json` sidecar.** The object travels inside the HTML at `<script id="review-data" type="application/json">`, which is where `/ba:resolve` reads the prior round. Write the object to a scratch file for injection and do not keep it — a second copy on disk is a second thing to keep in sync, and nothing reads it.

Use the controlled severities (`Blocker` · `Major` · `Minor` · `Nit`) and the ledger row's `CLR-###` ID (zero-padded, append-only) for every scope question, per `delivery-os-conventions`.

---

## 1. Review data object (the single source)

This is the JSON injected into `assets/report.html` at the `__REVIEW_DATA__` token. Every field the HTML reads is below; keep the key names exact.

```json
{
  // The ABSOLUTE folder this report belongs to. The page sends it with every
  // save, so any serve-review instance writes to the right place and the port
  // stops mattering. Without it the save falls back to the server’s own folder.
  "saveDir": "<absolute path to requirements/<slug>/reviews>",
  "project": "Acme Customer Portal",
  "documentReviewed": "requirements/<slug>/scope.md",
  "documentVersion": "0.3 (Emerging)",
  "reviewDate": "2026-06-30 14:30",
  "reviewId": "2026-06-30-143012",
  "round": 1,
  "priorReview": null,
  "knowledgeBase": {
    "examplesChecked": 12,
    "registersChecked": ["requirements/<slug>/registers/examples.md", "requirements/<slug>/registers/requirements.md", "requirements/<slug>/ledger.md", "system-landscape.md"],
    "note": "Cross-checked against 12 client examples (EX-001–EX-012) and the requirement register; no contradiction-log present."
  },
  "overallScore": 3.4,
  "verdict": "Significant gaps — clarify before estimate",
  "verdictReason": "Auth method (CLR-004) and CRM partner (CLR-011) are undefined Blockers; the scope averages 3.4.",
  "executiveSummary": "2–4 sentences: what this scope covers, how estimate-ready it is, and the single most important thing to clarify before pricing it.",
  "gatingQuestions": ["CLR-004", "CLR-011"],
  "strengths": ["Clear module breakdown in §2", "Out-of-scope stated explicitly for the Reporting module"],
  "features": [
    {
      "num": 1,
      "code": "AUTH",
      "name": "Login & Authentication",
      "group": "Core Modules",
      "kind": "UI / auth",
      "coverageScore": 0.6,
      "cap": 4,
      "score": 1,
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
      "assessment": "Unbounded: the scope says only 'the system will have a login screen'. The auth methods aren't enumerated, the in/out boundary and adjacent flows (registration, reset) are unstated, and it conflicts with EX-004. Eight of nine dimensions are Absent, so coverage alone puts it at 0.6/10 — below the Unbounded cap of 4, which therefore isn't the binding constraint here.",
      "changes": [],
      "questionIds": ["CLR-001", "CLR-002", "CLR-003", "CLR-004"],
      "suggestions": "Enumerate the supported auth methods and mark each In/Out of scope; state whether registration, password reset, and profile are in scope; add the account-access policies (verification, lockout, MFA).",
      "strengths": ""
    }
  ],
  "questions": [
    {
      "id": "CLR-004",
      "severity": "Blocker",
      "feature": "AUTH",
      "dimension": "functional_reqs",
      "question": "Which authentication methods are in scope — email/password, social (Google/Apple/Microsoft), OTP/passwordless, magic link, or enterprise SSO (SAML/OIDC)?",
      "whyItMatters": "The auth method is a business decision that swings the estimate and the integrations list. Unspecified, the price is a guess — and it conflicts with EX-004 (Google sign-in).",
      "consequence": "estimate",
      "checkedIn": ["§3.1.1–3.1.9", "§6 Global out-of-scope", "requirements/<slug>/ledger.md", "requirements/<slug>/registers/examples.md"],
      "suggestedScope": "In §3.1.3 list the supported methods with Resp./Pri.; if email/password, add verification + password policy + lockout; reconcile with EX-004.",
      "status": "Open",
      "answeredBy": null,
      "authorResponse": null,
      "adjudication": null,
      "followUps": [],
      "resolvedOn": null,
      "decisionId": null
    }
  ],
  "handoffs": [
    {
      "id": "TL-001",
      "feature": "AUTH",
      "question": "Concurrent assign on the same normalised tag — must uniqueness be enforced at the point of write rather than by a prior read?",
      "whyNotScope": "The business rule (one open record per tag) is stated in §3.1.7; how it is guaranteed under concurrency is an engineering choice."
    }
  ],
  // The SAME ledger rows as `questions`, written for the client: `question` in
  // their language, `whyItMatters` saying what it changes for them. Same
  // `CLR-###`, because it is the same question -- answering it once answers it
  // everywhere. There is no CQ id and no linkedTo: nothing to link.
  "clientQuestions": [
    {
      "id": "CLR-004",
      "question": "Do staff sign in with a company email address, or their own?",
      "whyItMatters": "Decides whether we can use your existing Microsoft sign-in or have to build a separate login.",
      "area": "AUTH",
      "status": "Open",
      "owner": "Priya (Acme)",
      "askedOn": "2026-10-18"
    }
  ],
  // CLOSED rows only (Answered / Closed / Superseded) -- the audit trail.
  // Including open ones repeated the Client questions tab verbatim on any
  // round where nothing had closed yet, which is every first review.
  "clarifications": [
    {
      "id": "CLR-007",
      "question": "Is MFA mandatory for admin accounts?",
      "owner": "Acme IT",
      "status": "Open",
      "raid": "Q-04",
      "raisedOn": "2026-10-12",
      "dueBy": "2026-10-25",
      "resolution": null
    }
  ],
  "sinceLastRound": {
    "resolved":     [{ "id": "CLR-004", "feature": "AUTH", "note": "Azure SSO, corporate email only" }],
    "assumption":   [{ "id": "CLR-011", "feature": "SYNC", "note": "Weekly Monday 06:00 \u2014 ASM-003, revisit before build" }],
    "insufficient": [{ "id": "CLR-007", "feature": "TIME", "note": "\u201cstandard rules\u201d \u2014 asked which rules; carried to round 3" }],
    "declined":     [{ "id": "CLR-019", "feature": "RPT",  "note": "out of scope for phase 1, per the client" }],
    "stillOpen":    [{ "id": "CLR-021", "feature": "ALLOC", "note": "no answer given" }]
  },
  "assumptions": [
    {
      "id": "ASM-003",
      "statement": "Payroll pulls weekly on Monday 06:00",
      "whyItMatters": "The pull schedule sets the cut-off every other timesheet rule is written against.",
      "owner": "Novacore",
      "status": "Open",
      "raid": "A-02",
      "basis": "\u00a73.5 \u2014 no source states a schedule",
      "residualRisk": "If the real schedule is daily, the lock-out window in \u00a73.5.2 is wrong."
    }
  ],
  "contradictions": [
    {
      "id": "CON-001",
      "topic": "Offline editing",
      "statementA": "Technicians work fully offline for a whole shift.",
      "sourceA": "Discovery call, 12 Oct",
      "statementB": "Every job update is validated server-side before it saves.",
      "sourceB": "Requirements doc \u00a74.2",
      "severity": "Blocker",
      "status": "Open",
      "resolution": null
    }
  ],
  "nextActions": ["Pin the auth method (CLR-004) and the CRM partner (CLR-011) — both block the estimate."]
}
```

Field rules:
- `reviewDate` is the human-readable run time (date + time so two same-day runs are distinguishable); it shows in the header/footer and should match the `<timestamp>` in the filename.
- `reviewId` is the filename `<timestamp>` (`YYYY-MM-DD-HHMMSS`) — the join key the resolution loop uses to match a responses file back to its review. The HTML "Export responses" button reads it to name the download. `round` starts at 1; `/ba:resolve` increments it. `priorReview` is the `reviewId` of the report this round resolves (null for round 1).
- `answeredBy` records **who** answered — `"client"` / `"internal"` / `"assumed"`, null while `Open`. Required on every terminal status. Only `client` may be written into the scope as a client decision; `internal` and `assumed` on estimate-driving questions cap the verdict (see `SKILL.md` step 7 and `resolution-loop.md` §4).
- The per-question **resolution fields** (`status`, `authorResponse`, `adjudication`, `followUps`, `resolvedOn`, `decisionId`) start at `Open`/null in round 1 and are filled by `/ba:resolve`. `status` uses the controlled values in `resolution-loop.md`; `followUps` is a list of verification questions when `status` is `Needs-verification`.
- `score` is a **number 0–10** (the HTML draws a bar and a band). It is **derived, never chosen** — by the formula in `SKILL.md` step 7 (note a `Bounded` feature has no cap, so its score is simply `round(coverageScore)`). Keep all features in the `features` array so the scorecard is complete.
- `coverageScore` is the pre-cap arithmetic from the coverage map — `(Covered 1 / Partial 0.5 / Absent 0, summed over the nine) / 9 * 10`, to one decimal. It is what makes the score auditable; emit it on every feature.
- `cap` is the boundedness ceiling — `4` when `Unbounded`, `6` when `Partially-bounded`, `null` when `Bounded`. Record it **even when it isn't binding** (i.e. when `coverageScore` is already below it), so a reader can see the cap was considered rather than forgotten.
- These three must agree. If `score` doesn't match the step-7 formula, the map and the number disagree and the report is wrong — fix the coverage call, never the number.
- `band` is the band label (`Excellent`/`Good`/`Adequate`/`Weak`/`Stub`/`Absent`), set **from the computed `score`** using the table in `SKILL.md` step 7 — never assigned independently.
- `changes` explains a score that moved between rounds. Empty `[]` on round 1 and on any feature whose score didn't change; otherwise one entry per dimension that moved:
  `{ "dimension": "business_rules", "from": "Covered", "to": "Partial", "cause": "CLR-009", "raised": "CLR-014" }`
  `priorScore` sits next to it — the feature's score in the previous round, so the panel can show `8 → 6` and colour a fall differently from a rise. Omit both on round 1.
  `dimension` is one of the nine coverage keys. `cause` is the `CLR-###` / `DEC-###` / `ASM-###` that moved it — an entry with no cause is an error, like a `score` that doesn't match its map. `raised` is **required when `to` is worse than `from`** (the `CLR-###` capturing what became unclear) and omitted otherwise; see `resolution-loop.md` §6. A score that changed with an empty `changes` array means the map moved without explanation and the round is wrong.
- `boundedness` is one of `"Bounded"` / `"Partially-bounded"` / `"Unbounded"`; `boundednessNote` (one line) says what's undefined. **These cap the score** — `Unbounded` ≤ 4, `Partially-bounded` ≤ 6 (see `review-rubric.md` §A). The HTML shows a boundedness badge on the feature. For a **branching** feature, the note must state whether every materially-different route is expanded into its own §3.x.4 use case (with a flow and worked example) — an un-expanded fork is a boundedness failure, not just a missing dimension, and the flattening is raised as a question tagged `in_out_scope` or `business_rules` (see `review-rubric.md` §A item 6).
- `coverage` has exactly the nine keys above, each valued `"Covered"` / `"Partial"` / `"Absent"` (the HTML renders the matrix and colours each cell). Use `"Covered"` with an assessment note when a dimension is genuinely not-needed for that feature. **Route/use-case expansion is scored through `boundedness`** (plus the `business_rules`/`in_out_scope`/`exceptions` cells it pulls down), not as a tenth coverage key — so the existing nine-column matrix is unchanged.
- `exampleCompliance` is one of `"Pass"` / `"Partial"` / `"Conflict"` / `"No-examples"`; `exampleNote` explains it (cite the EX id for Partial/Conflict).
- `group` drives the section dividers in the scorecard — use your own module-group names (e.g. `Core Modules`, `Supporting Modules`, `Cross-cutting`). Keep features in order so each group's rows are contiguous.
- `kind` (optional) is the feature kind (UI/auth, integration, data/reporting, AI/automation, admin, workflow) — shown as a tag.
- `handoffs` carries the technical follow-ups the review deliberately did **not** score — the things that belong to `tl-spec-review`. `id` is `TL-###` (zero-padded, append-only), `feature` links it to a feature `code`, `question` is what the TL must settle, `whyNotScope` says which business decision is already made and which engineering choice remains. Empty `[]` when there are none. These are not gaps and never affect a score; the array exists so refusing to score something doesn't mean losing it.
- **`clientQuestions`, `clarifications`, `contradictions` are the three register tabs.** They are not re-derived here — they are the review's copy of the review report’s **Client questions** tab, `requirements/<slug>/ledger.md` (kind: question) and `requirements/<slug>/ledger.md` (kind: contradiction), folded in at review time so the report is one surface instead of four files. Each is `[]` when its source file is absent or empty, which the HTML renders as an honest empty state. **Never invent a row to fill a tab.**
  - `clientQuestions` is the **asking** list — the same ledger rows as `questions`, phrased for the client with `whyItMatters` saying what it changes for *them*. **Same `CLR-###`**, so there is nothing to link and nothing to keep in step. Answers are typed into the **Open questions** tab, never here: the BA fills this report, the client never opens it.
  - `clarifications` mirrors the `CLR-###` log, including `raid` (the RAID `Q-##`), `owner` and `dueBy`. `status` uses the same controlled values as `questions`. A `CLR` with no owner is a question nobody is going to answer — record the gap rather than leaving the field out.
  - `contradictions` holds the `CON-###` conflicts. Both sides are **required and must be quoted or closely paraphrased with their source** (`sourceA` / `sourceB` — a call date, a document section, an `EX-###`), because a contradiction a reader cannot verify is an accusation. `resolution` is null until a human decides; the HTML says so in as many words, since an undecided contradiction silently carried into a build is the single most expensive thing this review can miss.

- **`sinceLastRound`** is what the round-2+ report opens with, and it replaces the `logs/changes.md` journal nobody opened. Five buckets of **question disposition**, written by `/ba:resolve` as it adjudicates — not derived afterwards from statuses, because a derived bucket cannot record *why* something was declined, and that reason is the entire value of the section. Omit the key on round 1; the page hides the section when `round` is 1 or every bucket is empty.
  - `resolved` · `assumption` — closed. The note says what was decided, not that it was decided.
  - `insufficient` — **answered, and the answer was not enough.** The most important bucket and the easiest to lose: without it, a vague answer looks identical to no answer, and the author is never told their reply did not land. The note must say what was asked back.
  - `declined` — the author chose not to answer. Record the reason they gave, not an inference.
  - `stillOpen` — not answered at all. A note of "no answer given" is correct and honest; do not dress it up.
- `gatingQuestions` lists the IDs (Blockers + the most important Majors) surfaced at the top; each must exist in `questions`.
- `questionIds` on a feature links it to its rows in `questions`; the HTML makes them clickable.
- `dimension` on a question is one of the nine coverage keys (or omit) — used to tag which sub-heading the gap sits in.
- `checkedIn` is a **required** list of the places searched for the answer before the question shipped — the feature's own §3.x sub-headings, the global §6, and whichever registers were consulted (see `SKILL.md` step 6). A question whose answer is found during that search is dropped, not recorded; so an empty list means the search wasn't done.
- `consequence` is **required** and controlled: `"estimate"` · `"scope"` · `"integrations"` · `"compliance"` · `"none"` — what changes if the question stays unanswered. It is the evidence behind `severity`: a `Blocker` or `Major` cannot carry `"none"`, and a `"none"` question is a `Nit` at most. `whyItMatters` stays the prose explanation; `consequence` is the machine-checkable claim underneath it.
- **Backward compatibility** — reviews written before these fields exist will lack `coverageScore`, `cap`, `checkedIn` and `consequence`. Readers (the HTML, `/ba:resolve`) must treat them as absent rather than erroring, and must not back-fill them by guessing: an old review's score was judged, not derived, and inventing a `coverageScore` for it would assert a derivation that never happened.

## 2. Injecting into the HTML

**Write the data object to a scratch file**, then build the HTML from it with the bundled script — never hand-assemble the HTML. The report contains non-ASCII glyphs (`§`, `—`, `→`) both in the template chrome and in your review text; pasting the assembled HTML through a shell or editor on Windows double-encodes them into mojibake (`§`→`Â§`, `—`→`â€"`) even though `<meta charset="utf-8">` is present. The script sidesteps this by reading and writing UTF-8 explicitly:

```
node assets/inject.js assets/report.html <scratch>/review-data.json __REVIEW_DATA__ scope-review-<timestamp>.html
```

`inject.js` replaces the literal token `__REVIEW_DATA__` (between `<script id="review-data" type="application/json">` and `</script>`) with the JSON, touches nothing else, validates the JSON (a trailing comma or unescaped quote would make the page render its empty-state notice), and aborts if it detects mojibake. If Node is unavailable, do the replacement manually but save the output as **UTF-8 without a BOM** and verify the file shows `§`/`—`, not `Â§`/`â€"`, before moving on.

The machine-readable state `/ba:resolve` reads (matched by `reviewId`) is the `<script id="review-data">` block inside the HTML — so questions carry forward without re-parsing prose, and without a second copy on disk to keep in sync. The scratch file is injection input and is **not** an output: the data survives inside the HTML at `<script id="review-data">`, which is where the resolution loop reads it back.

---

## 3. Markdown artifact — `scope-review.md`

Assemble the Markdown in this exact structure. Keep it skimmable: a decision-maker should get the verdict and the gating questions from the first screen, with per-feature detail below for the BA who has to close the gaps. Replace every `<…>` placeholder.

---

```markdown
---
doc_type: scope-review
schema_version: 1.1
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

<2–4 sentences: what this scope covers, how estimate-ready it is, and the single most important thing to clarify. State the verdict reason — e.g. "two Blockers (CLR-004 auth method, CLR-011 CRM partner) cap this below estimate-ready despite a clean module breakdown.">

**Gating questions** (must close before estimate):
- `CLR-004` (<Blocker/Major>) — <one line> → <the scope addition that closes it>
- `CLR-011` (<Blocker/Major>) — <one line> → <…>

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
**Questions.** <CLR-0XX, CLR-0XX — or "None; well scoped.">
**Suggested scope additions.** <Concrete edits — what to add and to which §3.x sub-heading.>
**Strengths.** <Optional.>

## Scope questions & gaps register

> Sorted by severity (Blockers first). Every deducted point traces to a question here; every question carries the scope addition that closes it. `Status` is the lifecycle state (`Open` in round 1; updated by `/ba:resolve`).

| ID | Sev. | Status | Feature | Question | Suggested scope addition |
|----|------|--------|---------|----------|--------------------------|
| CLR-001 | Blocker | <Open/Resolved/Needs-verification/Accepted-assumption/Won't-fix> | <CODE> | <the question> | <the scope edit that answers it> |
| CLR-002 | Major | <…> | <CODE> | <…> | <…> |

**Resolution rounds (round 2+).** For each question that received a response, add a short thread under the register so closure is auditable — the author's response, the agent's adjudication, any follow-ups, and the `DEC-###` / `ASM-###` / `CLR-###` id it promoted to:

```markdown
#### CLR-004 — Resolved (round 2)
- **Author response:** Email/password + Google SSO; corporate domains only; email verified; MFA optional.
- **Adjudication:** Specific and verifiable; reconciles with EX-004. Spec edit applied to §3.1.3. Closed.
- **Promoted to:** DEC-007 (decision-log), scope §3.1.3 updated.
```

## Recommended next actions

1. <highest-leverage clarification, usually the Blockers>
2. <…>
```

---

## Notes on filling it in

- **Executive summary is for the decider; feature detail is for the BA.** Don't make the reader scroll past every feature to learn whether the scope is estimate-ready.
- **The question register is the spine.** If a feature is 3/10 but no questions explain the missing 7 points, the review isn't done. Conversely, don't list a question you didn't let affect a score.
- **Keep suggested additions concrete and located.** "Add more detail" is weak. "In §3.1.3, list auth methods with Resp./Pri. and mark social login Out-of-scope (phase 2)" is actionable.
- **Always show the example check.** Citing EX ids is what separates "I think this is thin" from "this can't do what the client showed us."
