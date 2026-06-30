# Scope Review Rubric — coverage dimensions, the paranoid playbook, and scoring guidance

This is the detailed knowledge behind the feature-by-feature review in `SKILL.md`. It has three parts: (A) what **"Covered"** looks like for each of the nine D&D coverage dimensions and the red flags that should cost points; (B) the **paranoid questioning playbook** — worked examples that show how to turn a one-line feature into the questions an estimator actually needs; (C) **scoring, severity, and example-compliance calibration**.

Don't treat any list as a checkbox quota. A feature can score 9/10 without every dimension if it genuinely doesn't need it (a static "About" page needs no integrations or business rules); conversely, ticking every dimension shallowly isn't an 8. Judge whether a team could **estimate and build the right thing** from what's written, and whether it's consistent with the examples the client shared.

---

## A — The nine coverage dimensions

For each feature, mark every dimension **Covered** / **Partial** / **Absent**. These map 1:1 to the Techjays D&D scope §3.x.1–3.x.9 sub-headings, so you're grading whether the scope actually filled them in.

### 1. Current → Future state (`current_future`)
**Covered:** today's process is described — the actors, the trigger, the systems touched, the manual steps, and the pain points — and the future state names the split between what AI does, what deterministic logic does, and what a human still does.
**Red flags:** future state only ("the system will…") with no baseline, so nobody can size the *change*; "automate the process" with no statement of which steps actually become automated vs stay manual.

### 2. In scope / Out of scope (`in_out_scope`)
**Covered:** the boundary is explicit — what this feature includes **and** a deliberate list of what it does not. Out-of-scope is stated, not implied.
**Red flags:** no out-of-scope line at all (the default failure); "etc." or "and so on" doing the work of a boundary; scope that quietly assumes adjacent functionality ("login" silently assuming registration, profile, password reset) without saying so.

### 3. Functional requirements (`functional_reqs`)
**Covered:** the capabilities are enumerated, each with a responsibility (`AI`/`DET`/`HUM`) and a MoSCoW priority (`M`/`S`/`C`/`W`), at capability level (not testable-spec level — that's the SRS).
**Red flags:** one prose sentence standing in for a requirement list; no responsibility or priority, so everything reads as an undifferentiated "must"; requirements that are actually solutions ("use a dropdown") rather than capabilities.

### 4. AI / Automation responsibilities (`ai_automation`)
**Covered:** what the AI is responsible for, the **confidence threshold and fallback** when it's unsure, and the **human-in-the-loop** point. (Mark `Covered` as N/A-style "not needed" only when the feature genuinely has no AI/automation — say so; don't penalise a static page for lacking an AI section.)
**Red flags:** "AI will handle X" with no accuracy bar, no fallback, and no human review for a consequential decision; automation claimed with no statement of what happens on low confidence.

### 5. Business rules (`business_rules`)
**Covered:** the rules, thresholds, validations, and decision logic the feature enforces, each traceable to a source.
**Red flags:** a feature that obviously encodes rules (eligibility, pricing, routing, approval limits) with none stated; rules implied inside an example but never lifted into the scope.

### 6. Data fields (`data_fields`)
**Covered:** the entities/fields the feature reads or writes, with types, required-ness, and source/validation.
**Red flags:** a data-entry or data-display feature with no fields listed; "captures user details" with no field list; PII handled with no sensitivity note.

### 7. Integrations (`integrations`)
**Covered:** the external systems involved, the direction of data flow, what's exchanged, and the dependency/owner. "None" is a valid, explicit answer.
**Red flags:** an integration implied ("syncs with the CRM", "sends to the payment provider") with no named system, direction, or contract; a third-party dependency with no owner or fallback.

### 8. Exception handling (`exceptions`)
**Covered:** the unhappy paths — what happens on invalid input, failure, timeout, partial completion, duplicate, or conflict — and who is notified.
**Red flags:** only the happy path; "handle errors gracefully" with no specifics; no statement of what the user/system does when the AI or an integration fails.

### 9. Acceptance criteria (`acceptance`)
**Covered:** testable criteria tied to the feature's requirement IDs — the definition of done a QA agent could later turn into tests.
**Red flags:** "it should work"; criteria that restate the requirement instead of making it verifiable; no link back to requirement IDs.

---

## B — The paranoid questioning playbook

This is the core skill: take a thin feature line and generate the questions that change the estimate. The pattern is always the same — **name the decision the scope left implicit, then branch into the sub-decisions each answer forces.** Below are worked examples; reuse the *shape* of the questioning for any feature of the same kind.

### Worked example — "The system will have a login screen" (UI / auth feature)
A single sentence. The estimator cannot price it, the TL cannot design the data model, and the security reviewer has nothing to review. Interrogate:

- **Auth method (Blocker).** Email + password? Social login (Google / Apple / Microsoft / Facebook — which exactly)? OTP / passwordless (SMS or email)? Magic link? Enterprise SSO (SAML / OIDC — which IdP)? More than one? *This one answer swings effort, the data model, the integrations list, and the security review — it is almost always a Blocker.*
- **If email/password:** personal addresses, or **corporate-domain-restricted**? Is the email **verified** before access? Password policy (length, complexity, rotation, breach-check)? Where are credentials stored / which hashing? Account **lockout** after N failed attempts, and unlock path?
- **If social/SSO:** which providers exactly, and is there a fallback for users without them? What profile data is pulled, and is it stored or just used for auth? Just-in-time provisioning, or pre-created accounts? What happens when the IdP is down?
- **MFA:** required, optional, or none? Which factors (TOTP, SMS, email, passkey)? Enforced for all users or by role?
- **Adjacent scope, often silently assumed (In/Out of scope).** Does "login" include **registration / sign-up**? **Forgot-password / reset**? **Profile management**? **Logout**? If those are out of scope, the scope must say so.
- **Session & security.** Session length and idle timeout? Concurrent sessions allowed? "Remember me"? Token strategy? Brute-force / rate-limit protection?
- **Roles (Permissions).** Does login branch by role (admin vs user vs …), or one user type? Where do roles come from?
- **Data & compliance.** What PII is captured at login, under which regime (GDPR/etc.)? Audit log of sign-in attempts?
- **Acceptance.** What defines "login works"? Successful sign-in, failed sign-in, locked account, reset flow — each needs a criterion.
- **Example check.** If an EX-### shows a user signing in with Google, an email/password-only scope is a **Conflict**, not a detail.

That is one scope line → ~a dozen questions, two or three of them Blockers. That is the standard you hold every feature to.

### Worked example — "Integrate with the client's CRM" (integration feature)
- **Which system and version (Blocker)?** Salesforce / Dynamics / HubSpot / a bespoke CRM — named, with API style (REST/SOAP/GraphQL/file)?
- **Direction & trigger:** read, write, or bidirectional? Real-time, batch, or event-driven? Who initiates?
- **Data contract:** which objects/fields, mapped to which local entities? Volume and frequency?
- **Auth & access:** who provides credentials/sandbox? Rate limits?
- **Failure modes (Exception handling):** what happens when the CRM is down, rejects a record, or returns a duplicate? Retry / dead-letter / manual reconciliation?
- **Ownership:** who owns the CRM side, and is a sandbox available for build/test? (Dependency for RAID.)

### Worked example — "Reporting dashboard" (data/reporting feature)
- **Which reports/metrics exactly**, for **which roles**? Real-time or periodic? Drill-down or summary only?
- **Data source & definitions:** where does each number come from, and is each metric's definition agreed (the classic "what counts as an active user")?
- **Export / scheduling:** CSV/PDF export? Scheduled email? Out of scope if not stated.
- **Volume & history:** how much data, what retention/time range?
- **Acceptance:** what makes a report "correct"?

### Worked example — "AI will categorise incoming requests" (AI/automation feature)
- **Categories:** fixed taxonomy or open? Who defines/maintains it?
- **Confidence & fallback (Blocker for AI features):** what accuracy is acceptable, what's the confidence threshold, and what happens **below** it — queue for a human, default category, reject?
- **Human-in-the-loop:** does a person review all / sampled / low-confidence items? Can they correct, and does the correction feed back?
- **Training/grounding data:** what does the model see? Any PII, and is sending it to the provider allowed?
- **Volume & cost:** items/day → drives both feasibility and running cost.
- **Exception handling:** unparseable input, multi-category items, the model/endpoint being down.

### Questioning heuristics (apply to any feature)
- **For every verb in the feature line, ask "how, exactly?"** — "manage", "process", "handle", "sync", "notify", "validate" each hide a decision.
- **For every noun, ask "which, and what's stored?"** — "users", "requests", "documents", "payments".
- **Always probe the boundary** — "what's explicitly *not* in this?" — because the unstated exclusion is the future dispute.
- **Always probe the unhappy path** — the happy path is the cheap 20%; the exceptions are where the estimate lives.
- **Always probe roles & permissions** — "who can do this, and who can't?"
- **Cross-check the examples** — does each EX-### the client shared actually work under this scope?

---

## C — Calibration

### Deriving the feature score from coverage
Let coverage anchor the score, then adjust for consequence and example-compliance:
- **9–10 (Excellent):** all *applicable* dimensions Covered, none materially Partial, no example conflicts, no open Blockers/Majors. A team estimates tightly.
- **7–8 (Good):** applicable dimensions mostly Covered; a few Partial; only Minor/Nit questions; examples Pass or Partial.
- **5–6 (Adequate):** intent clear but **several** dimensions Partial/Absent, or one Major open; the feature is not safely estimable until those close.
- **3–4 (Weak):** most dimensions Absent; a sentence or two of scope; any open Blocker on a feature usually lands here.
- **1–2 (Stub):** a heading / one-liner ("login screen").
- **0 (Absent):** needed (it appears in an example, a register, or a stakeholder ask) but absent from the scope.

Sanity-check score against questions: a feature with an unresolved **Blocker** rarely scores above 4; **Major** gaps land it around 3–6; only **Minor/Nit** is a 7–8; no real gaps and example-Pass is 9–10. If your score and your questions disagree, reconcile before finalising.

### Severity → RAID Open-Question mapping
Use the controlled severities; they map onto the BA Agent's RAID Open-Question classes so terminal items promote cleanly in `/ba:resolve`:

| Severity | Meaning | RAID Open-Question class |
|----------|---------|--------------------------|
| `Blocker` | Must close before estimate — swings effort/architecture/data/integration/security/cost. | *Must close before estimate* |
| `Major` | Close before build; workable only with an explicit, accepted assumption. | *Proceed with assumption* |
| `Minor` | Contained implementation detail; won't move the estimate much. | *Minor implementation detail* |
| `Nit` | Polish, wording, or safely deferred. | *Future phase* |

A question genuinely *too uncertain to scope* (the client can't answer it and it's volatile) is a `Major`/`Blocker` whose suggested resolution is to **exclude it or move it to T&M** — say so in the suggested scope addition.

### Example-compliance
- **Pass** — the scope as written satisfies the example end-to-end.
- **Partial** — partially supported; some implied path/field isn't in scope → at least a Minor, often Major.
- **Conflict** — the example contradicts the scope → Major, or Blocker if it invalidates the feature's core (the Google-SSO-vs-email/password case). Always cite the EX id.
- **No-examples** — no example exercises this feature; note it and consider a clarification. Don't fabricate compliance you can't evidence.

### General calibration notes
- **Score the scope, not the system.** A great system idea with a thin scope scores low here — the scope is the artifact people estimate and sign.
- **Severity drives the verdict, not question count.** Five Nits is a healthy 8; one undefined-auth-method Blocker caps an otherwise-good scope.
- **Reward stated assumptions and explicit out-of-scope.** A scope that says "we assume corporate-email SSO only; social login is out of scope, phase 2" is *stronger* than one that silently omits it — surfaced uncertainty beats hidden uncertainty.
- **The most valuable questions are the ones the author can't see.** Anyone can note a missing field. The review earns its keep by catching the auth method nobody pinned down, the example the scope can't satisfy, the "sync with CRM" with no named system, the AI step with no fallback.
- **Be paranoid, not pedantic.** Every question you raise should be one a build team would otherwise hit. If answering it wouldn't change the estimate, the architecture, or the deliverable, it's a Nit at most — or not worth raising.
