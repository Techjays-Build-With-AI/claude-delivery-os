# Scope Review Rubric — coverage dimensions, the paranoid playbook, and scoring guidance

This is the detailed knowledge behind the feature-by-feature review in `SKILL.md`. It has four parts: (A) the **bounding layer** — the mandatory grounding (categories, definitions, exclusions, mandatory/optional) that every feature must have before anything else; (B) what **"Covered"** looks like for each of the nine D&D coverage dimensions and the red flags that should cost points; (C) the **paranoid questioning playbook** — worked examples that show how to turn a one-line feature into the questions an estimator actually needs; (D) **scoring, severity, boundedness, and example-compliance calibration**.

Don't treat any list as a checkbox quota. A feature can score 9/10 without every dimension if it genuinely doesn't need it (a static "About" page needs no integrations or business rules); conversely, ticking every dimension shallowly isn't an 8. Judge whether a team could **estimate and build the right thing** from what's written, and whether it's consistent with the examples the client shared.

> ### This is a BUSINESS scope review — stay on the business side of the line
> You review **what the business wants**, not **how it will be built**. The scope document is *supposed* to leave implementation open, so its absence is correct — never raise it as a gap or let it lower a score. If a question is really about how it's built, it's the **TL's `tl-spec-review`**, not yours.
>
> **Do NOT review or raise (hand to the TL):** system design & architecture · database/schema design · field data types, lengths, constraints, keys, indexes · API/endpoint contracts, protocols (REST/SOAP/GraphQL) · authentication mechanisms, token/session strategy, password hashing/encryption · technical error handling, timeouts, retries, idempotency · infrastructure, hosting, scaling, CI/CD · library/framework/tech-stack choices · performance/throughput engineering.
>
> **DO review (the business questions):** what the feature is for and who uses it · what's in and out of scope · the business capabilities and rules · which auth *method/policy* the client wants (not how it's secured) · what *information* the feature deals with (not its schema) · which external *systems* it touches and what business data flows (not the contract) · the business exceptions and edge cases · what the client considers "done" · whether it satisfies the client's examples.
>
> Litmus test: **"Is this a decision the client/business makes, or a decision the engineers make?"** If it's the engineers', leave it to the TL.

---

## A — The bounding layer (check this FIRST, for every feature)

Knowing *what a feature does* is not the same as knowing *its boundary*. The most common — and most expensive — failure in a scope is a feature whose **function is clear but whose boundary is undefined**: "classify the invoice", "process the request", "match the record" — with no statement of *which* things, defined *how*, and what falls *outside*. Your first job on every feature is to force it from a functionality statement into a **bounded, defined, categorized** one. Do this before you score the nine dimensions; it's what most of the deductions will come from.

For every feature, demand these four things:

1. **Categories / buckets — enumerated and closed.** Does the feature name the set of things it operates on, and is that set *closed*? "Classifies invoices" → *which* invoice types — the 4–5 named buckets? "Handles requests" → which request types? An open-ended "classifies documents" with no enumerated set is **unbounded**. The set must be finite and listed, with a stated policy for "anything not in the list".

2. **Definitions / identifying criteria — how we decide.** Is each category or key entity *defined* in business terms — the data points, markers, or signals used to identify it and to place it in one bucket vs another? How do we decide a document *is* an invoice (vs a PO, a quote, a receipt)? Which fields/markers make it invoice-type-A rather than type-B? A category name with no identifying criteria is a **label, not a boundary** — the team can't build a classifier from "invoices".

3. **Covered vs explicitly excluded — per bucket.** For each bucket, what's covered; and — critically — what falls *outside* the defined set and is therefore **out of scope**, stated in words ("documents that aren't one of the 5 invoice types are not processed; non-invoice emails are ignored"). The exclusion must be written, not implied — this is the line that prevents scope creep and disputes.

4. **Completeness rules — mandatory vs optional.** For processing/extraction features, *which* business data points/fields must be handled, and which are **mandatory vs optional**? How many? What happens when a mandatory one is missing (reject, route to a human, flag)? ("Which fields" here means business data points and their required-ness — *not* their technical types or schema, which are the TL's.)

Assign every feature a **boundedness** verdict (`boundedness` in the data object):
- **Bounded** — categories enumerated and closed, each defined by identifying criteria, covered-vs-excluded stated per bucket, mandatory/optional clear.
- **Partially-bounded** — the function and *some* boundaries are clear, but the category set, the identifying logic, or the exclusions are missing or vague.
- **Unbounded** — function stated with no defined categories, no identifying criteria, and no exclusions ("classify invoices" and nothing more).

**Scoring hook — an unbounded feature cannot score above Weak (4/10)**, no matter how clearly its purpose is written, because a team cannot bound the estimate. A `Partially-bounded` feature is capped at Adequate (6). Raise the missing boundary as a **`Blocker`** when it drives the estimate (what/how much gets classified or processed) and a **`Major`** otherwise. The bounding layer expresses itself across three of the nine dimensions below — **In scope / Out of scope** (the exclusions), **Business rules** (the definitions & classification logic), and **Information & data** (the fields and mandatory/optional) — so weak boundedness pulls those three down together.

### Worked example — "Read the email, classify the invoice, process it"
Function is obvious; boundary is absent. This feature is **Unbounded** until the scope answers:
- **Categories (Blocker).** Which invoice types are in scope — name the 4–5 buckets (e.g. standard, credit note, pro-forma, recurring, utility)? What about anything that isn't one of them?
- **Definition (Blocker).** How is a document defined as an "invoice" at all, vs a PO, quote, or receipt? Which data points/markers are used to identify it, and which put it in one bucket vs another?
- **Exclusions / Out of scope (Major).** Non-invoice emails, unsupported invoice types, scanned/handwritten, foreign-language, duplicates — covered, or explicitly excluded? Say it in words.
- **Processing completeness (Major).** Which fields do we extract per invoice type? How many are **mandatory** vs **optional**? What happens when a mandatory field is missing — reject, hold, route to a human?
- **Classification edge cases (Major).** A document that matches two categories, or none — what happens?

That is the depth **every** feature gets: function → categories → definitions/criteria → covered vs excluded → mandatory vs optional.

---

## B — The nine coverage dimensions

For each feature, mark every dimension **Covered** / **Partial** / **Absent**. These map 1:1 to the Techjays D&D scope §3.x.1–3.x.9 sub-headings, so you're grading whether the scope actually filled them in. The **bounding layer above** is what "Covered" *means* for dimensions 2, 5, and 6 — don't mark them Covered just because the topic is mentioned; mark them Covered only when the feature is actually bounded.

### 1. Current → Future state (`current_future`)
**Covered:** today's process is described — the actors, the trigger, the systems touched, the manual steps, and the pain points — and the future state names the split between what AI does, what deterministic logic does, and what a human still does.
**Red flags:** future state only ("the system will…") with no baseline, so nobody can size the *change*; "automate the process" with no statement of which steps actually become automated vs stay manual.

### 2. In scope / Out of scope (`in_out_scope`)  — *carries the bounding layer's exclusions*
**Covered:** the boundary is explicit — what this feature includes **and** a deliberate list of what it does not. For a feature that operates on a *set* of things (documents, requests, invoices, products, customers), that set is **enumerated and closed**, and everything outside it is stated as out of scope ("only these 5 invoice types; anything else is not processed"). A generic "these are the features" with no per-feature exclusions is **not** Covered.
**Red flags:** no out-of-scope line at all (the default failure); "etc." or "and so on" doing the work of a boundary; an open-ended set ("classifies documents") with no enumeration and no "anything else" policy; scope that quietly assumes adjacent functionality ("login" silently assuming registration, profile, password reset) without saying so.

### 3. Functional requirements (`functional_reqs`)
**Covered:** the capabilities are enumerated, each with a responsibility (`AI`/`DET`/`HUM`) and a MoSCoW priority (`M`/`S`/`C`/`W`), at capability level (not testable-spec level — that's the SRS).
**Red flags:** one prose sentence standing in for a requirement list; no responsibility or priority, so everything reads as an undifferentiated "must"; requirements that are actually solutions ("use a dropdown") rather than capabilities.

### 4. AI / Automation responsibilities (`ai_automation`)
**Covered:** what the AI is responsible for, the **confidence threshold and fallback** when it's unsure, and the **human-in-the-loop** point. (Mark `Covered` as N/A-style "not needed" only when the feature genuinely has no AI/automation — say so; don't penalise a static page for lacking an AI section.)
**Red flags:** "AI will handle X" with no accuracy bar, no fallback, and no human review for a consequential decision; automation claimed with no statement of what happens on low confidence.

### 5. Business rules (`business_rules`)  — *carries the bounding layer's definitions & classification logic*
**Covered:** the rules, thresholds, validations, and decision logic the feature enforces, each traceable to a source. **For any feature that classifies, identifies, routes, or matches, this must include the definition** — the business criteria/data points used to decide something is category A and not B ("a document is an *invoice* when it has X and Y; it's a *credit note* rather than a standard invoice when Z"). A rule set that names categories but never says how you tell them apart is **not** Covered — it's a label without logic.
**Red flags:** a feature that obviously encodes rules (eligibility, pricing, routing, classification, approval limits) with none stated; category names with no identifying criteria; rules implied inside an example but never lifted into the scope.

### 6. Information & data (`data_fields`)  — *carries the bounding layer's mandatory/optional fields*
**Business level only.** What *information* the feature captures, uses, or produces — described the way a business person would ("captures the customer's name, email, and order history; produces an approval decision"), plus where that information conceptually comes from and any data the client clearly cares about being present.
**Covered:** the business reader can tell what information the feature deals with; for extraction/processing features, **which business data points are handled and which are mandatory vs optional** (and what happens when a mandatory one is missing); and which data points are used to identify/classify the item.
**Red flags:** a data-entry, extraction, or data-display feature with no mention of *what* it captures/shows; "captures user details" / "extracts the fields" with no list of which fields matter to the business and no mandatory/optional split; clearly-sensitive information (health, payment, ID) handled with no acknowledgement that it's sensitive.
**Out of scope for this review (hand to the TL):** field data types, lengths, nullability, schema, keys/indexes, validation rules, and how/where it's stored. A scope that omits these is correct — do **not** raise them.

### 7. Integrations (`integrations`)
**Business level only.** Which external systems/products the feature touches and what business information flows between them, in which direction, and who owns the dependency.
**Covered:** the named systems, the direction (we read from / write to / both), the business data exchanged, and the dependency owner. "None" is a valid, explicit answer.
**Red flags:** an integration implied ("syncs with the CRM", "sends to the payment provider") with no **named system**, no direction, or no owner; a third-party dependency the client must provide (a sandbox, credentials, an account) that isn't called out.
**Out of scope for this review (hand to the TL):** API style/protocol (REST/SOAP/GraphQL), endpoints, contracts/schemas, auth mechanisms, rate limits, and retry/idempotency. Do **not** raise these.

### 8. Exceptions & edge cases (`exceptions`)
**Business level only.** The *business* unhappy paths and edge cases — what should happen when a business condition fails or is unusual (invalid request, missing approval, duplicate, dispute, an item that doesn't fit the normal flow) and who handles it.
**Covered:** the notable business exceptions are named with the intended handling (auto-reject, route to a human, notify someone), not just the happy path.
**Red flags:** only the happy path; "handle errors gracefully" with no business specifics; a feature with obvious edge cases (partial data, exceptions to a rule, an unhappy customer) that the scope is silent on.
**Out of scope for this review (hand to the TL):** technical errors, timeouts, retries, failure modes of a service or integration. Do **not** raise these.

### 9. Acceptance criteria (`acceptance`)
**Covered:** capability-level criteria that state what "done" means for the business, tied to the feature's requirements — enough that the client and team agree on what success looks like.
**Red flags:** "it should work"; criteria that restate the requirement instead of saying how you'd know it's met; no link back to the feature's requirements.
**Out of scope for this review (hand to the TL/QA):** detailed test cases, test data, and step-by-step test scripts — capability-level is the bar here, not a test plan.

---

## C — The paranoid questioning playbook

This is the core skill: take a thin feature line and generate the questions that change the estimate. The pattern is always the same — **name the decision the scope left implicit, then branch into the sub-decisions each answer forces.** Below are worked examples; reuse the *shape* of the questioning for any feature of the same kind.

### Worked example — "The system will have a login screen" (UI / auth feature)
A single sentence. The estimator cannot price it and the client hasn't actually decided what they want. Interrogate the **business decisions** (not how it's built):

- **Auth method (Blocker).** Email + password? Social login (Google / Apple / Microsoft — which exactly)? OTP / passwordless? Magic link? Enterprise SSO? More than one? *This is a business decision that swings the estimate and the integrations list — almost always a Blocker.*
- **If email/password:** personal addresses, or **corporate-domain-restricted**? Is the email **verified** before access? Is there an account **lockout** policy after repeated failed attempts? *(These are business policies. Password hashing, token strategy, credential storage, brute-force protection are the TL's — don't ask them here.)*
- **If social/SSO:** which providers exactly, and is there a fallback for users without them? *(How provisioning works technically is the TL's.)*
- **MFA:** required, optional, or none — and for all users or only some roles? *(A business policy; the factors/mechanism are the TL's.)*
- **Adjacent scope, often silently assumed (In/Out of scope).** Does "login" include **registration / sign-up**? **Forgot-password / reset**? **Profile management**? **Logout**? If those are out of scope, the scope must say so — this is where scope disputes are born.
- **Roles (Permissions).** Does login branch by role (admin vs user vs …), or one user type?
- **Sensitive data & compliance.** What personal information is captured at sign-in, and is the client subject to a regime (GDPR/etc.) that the scope should acknowledge? *(The business obligation — not the technical controls.)*
- **Acceptance.** What does the client consider "login works"? Successful sign-in, a rejected bad login, a locked account, the reset flow — each needs a business-level criterion.
- **Example check.** If an EX-### shows a user signing in with Google, an email/password-only scope is a **Conflict**, not a detail.

That is one scope line → ~a dozen *business* questions, two or three of them Blockers — without ever touching schema, tokens, or hashing. That is the standard you hold every feature to.

### Worked example — "Integrate with the client's CRM" (integration feature)
*(Business decisions only — the protocol, contracts, auth, and rate limits are the TL's.)*
- **Which system (Blocker)?** Salesforce / Dynamics / HubSpot / a bespoke CRM — *named*. The choice swings the estimate, so an unnamed CRM is a Blocker.
- **Direction & trigger:** do we read from it, write to it, or both? Roughly real-time or periodic, from the business's point of view?
- **What business information flows:** which records/information move (customers, orders, contacts)? Roughly how much/how often, if that affects feasibility?
- **Business exceptions:** what should happen, *for the business*, when a record can't be synced — who notices and what do they do?
- **Ownership (Dependency for RAID):** who owns the CRM side, and must the client provide access or a sandbox? Call it out as a dependency.

### Worked example — "Reporting dashboard" (data/reporting feature)
- **Which reports/metrics exactly**, for **which roles**? Periodic or up-to-date? Drill-down or summary only?
- **Metric definitions:** is each metric's *business* definition agreed (the classic "what counts as an active user")? *(Where the number is computed technically is the TL's.)*
- **Export / distribution:** export to CSV/PDF? Emailed on a schedule? Out of scope if not stated.
- **History:** what time range / how far back does the business need?
- **Acceptance:** what makes a report "right" in the client's eyes?

### Worked example — "AI will categorise incoming requests" (AI/automation feature)
- **Categories:** fixed list or open? Who defines/maintains it?
- **Confidence & fallback (Blocker for AI features):** what accuracy does the business accept, and what happens when the AI is unsure — queue for a human, default category, reject? *(A business policy; the threshold mechanism is the TL's.)*
- **Human-in-the-loop:** does a person review all / sampled / low-confidence items, and can they correct it?
- **Sensitive data:** does the information being categorised include personal/sensitive data the client must be careful with? *(The business/compliance angle — not the model plumbing.)*
- **Volume:** roughly how many items/day, since it affects feasibility and cost?
- **Business edge cases:** an item that fits no category, or fits several — what should happen?

### Questioning heuristics (apply to any feature)
- **For every verb in the feature line, ask "what does the business mean by that, exactly?"** — "manage", "process", "handle", "sync", "notify", "approve" each hide a business decision.
- **For every noun, ask "which, and what information matters?"** — "users", "requests", "documents", "payments" — at the business level, not the schema level.
- **Always probe the boundary** — "what's explicitly *not* in this?" — because the unstated exclusion is the future dispute.
- **Always probe the business unhappy path** — what happens when the normal flow doesn't apply, and who deals with it.
- **Always probe roles & permissions** — "who can do this, and who can't?"
- **Cross-check the examples** — does each EX-### the client shared actually work under this scope?
- **Stop at the business line.** If a question is really about *how it's built* (schema, protocol, framework, infrastructure), it's the TL's — don't raise it as a scope gap.

---

## D — Calibration

### Deriving the feature score from coverage
Let coverage anchor the score, then adjust for consequence, boundedness, and example-compliance:
- **9–10 (Excellent):** **Bounded**; all *applicable* dimensions Covered, none materially Partial, no example conflicts, no open Blockers/Majors. A team estimates tightly.
- **7–8 (Good):** Bounded; applicable dimensions mostly Covered; a few Partial; only Minor/Nit questions; examples Pass or Partial.
- **5–6 (Adequate):** intent clear but **several** dimensions Partial/Absent, or one Major open, or **Partially-bounded**; not safely estimable until those close.
- **3–4 (Weak):** most dimensions Absent, or **Unbounded** (function stated, boundary undefined); a sentence or two of scope; any open Blocker on a feature usually lands here.
- **1–2 (Stub):** a heading / one-liner ("login screen", "classify invoices").
- **0 (Absent):** needed (it appears in an example, a register, or a stakeholder ask) but absent from the scope.

**Boundedness caps (hard):** an **Unbounded** feature scores **≤ 4** and a **Partially-bounded** feature scores **≤ 6**, regardless of how clearly the function is described — a team can't bound the estimate of a feature whose categories, definitions, and exclusions are undefined.

Sanity-check score against questions: a feature with an unresolved **Blocker** rarely scores above 4; **Major** gaps land it around 3–6; only **Minor/Nit** is a 7–8; no real gaps, Bounded, and example-Pass is 9–10. If your score and your questions disagree, reconcile before finalising.

### Severity → RAID Open-Question mapping
Use the controlled severities; they map onto the BA Agent's RAID Open-Question classes so terminal items promote cleanly in `/ba:resolve`:

| Severity | Meaning | RAID Open-Question class |
|----------|---------|--------------------------|
| `Blocker` | Must close before estimate — swings effort/scope/integrations/compliance/cost (e.g. an undefined category set, a missing classification definition, an unnamed integration partner). | *Must close before estimate* |
| `Major` | Close before build; workable only with an explicit, accepted assumption. | *Proceed with assumption* |
| `Minor` | Contained implementation detail; won't move the estimate much. | *Minor implementation detail* |
| `Nit` | Polish, wording, or safely deferred. | *Future phase* |

A question genuinely *too uncertain to scope* (the client can't answer it and it's volatile) is a `Major`/`Blocker` whose suggested resolution is to **exclude it or move it to T&M** — say so in the suggested scope addition.

### Boundedness
- **Bounded** — categories enumerated & closed, each defined by identifying criteria, covered-vs-excluded stated per bucket, mandatory/optional fields clear. Doesn't cap the score.
- **Partially-bounded** — function and some boundaries clear, but the category set, the identifying logic, or the exclusions are missing/vague → caps at 6; raise the gaps (usually Major).
- **Unbounded** — function stated, boundary undefined ("classify invoices" and nothing more) → caps at 4; the missing boundary is a Blocker when it drives what/how-much gets processed.
Set `boundedness` on every feature and let it drive the caps above.

### Example-compliance
- **Pass** — the scope as written satisfies the example end-to-end.
- **Partial** — partially supported; some implied path/field isn't in scope → at least a Minor, often Major.
- **Conflict** — the example contradicts the scope → Major, or Blocker if it invalidates the feature's core (the Google-SSO-vs-email/password case). Always cite the EX id.
- **No-examples** — no example exercises this feature; note it and consider a clarification. Don't fabricate compliance you can't evidence.

### General calibration notes
- **Score the scope, not the system.** A great system idea with a thin scope scores low here — the scope is the artifact people estimate and sign.
- **Severity drives the verdict, not question count.** Five Nits is a healthy 8; one undefined-auth-method Blocker caps an otherwise-good scope.
- **Bound before you praise.** The single most valuable thing this review does is turn "we know what the feature does" into "we know exactly what it covers and excludes." A clearly-written but unbounded feature is *not* a good scope — it's a well-phrased risk. Always ask the four bounding questions (categories, definitions, exclusions, mandatory/optional) before scoring a feature above Weak.
- **Reward stated assumptions and explicit out-of-scope.** A scope that says "we assume corporate-email SSO only; social login is out of scope, phase 2" is *stronger* than one that silently omits it — surfaced uncertainty beats hidden uncertainty.
- **The most valuable questions are the ones the author can't see.** Anyone can note a missing field. The review earns its keep by catching the auth method nobody pinned down, the example the scope can't satisfy, the "sync with CRM" with no named system, the AI step with no fallback.
- **Be paranoid, not pedantic.** Every question you raise should be one a build team would otherwise hit. If answering it wouldn't change the estimate, the architecture, or the deliverable, it's a Nit at most — or not worth raising.
