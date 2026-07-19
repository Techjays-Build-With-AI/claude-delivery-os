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
>
> **Decision logic is a business decision, not implementation — do not hand it to the TL.** *How the business wants a decision made* — which factors it considers, how they are weighted or ordered, what wins when they conflict, and what the output must look like — is squarely **in scope for this review**, even though it describes a "how." What belongs to the TL is only *how that logic is realised in code* — the algorithm, data structures, model, or query. Refined litmus: **"Would the client have an opinion on this, and would a wrong answer produce the wrong business result?"** → yours. **"Is it purely an engineering realisation of an already-agreed rule?"** → the TL's. Waving a decision-logic gap through as "implementation" is the single most expensive miss this review can make: a scope that says "the engine optimises the schedule" without stating the rule is not leaving implementation open — it is leaving the *business decision* unmade.

---

## A — The bounding layer (check this FIRST, for every feature)

Knowing *what a feature does* is not the same as knowing *its boundary*. The most common — and most expensive — failure in a scope is a feature whose **function is clear but whose boundary is undefined**: "classify the invoice", "process the request", "match the record" — with no statement of *which* things, defined *how*, and what falls *outside*. Your first job on every feature is to force it from a functionality statement into a **bounded, defined, categorized** one. Do this before you score the nine dimensions; it's what most of the deductions will come from.

For every feature, demand these things (items 1–4 for every feature; item 5 additionally for any decision/optimization feature):

1. **Categories / buckets — enumerated and closed.** Does the feature name the set of things it operates on, and is that set *closed*? "Classifies invoices" → *which* invoice types — the 4–5 named buckets? "Handles requests" → which request types? An open-ended "classifies documents" with no enumerated set is **unbounded**. The set must be finite and listed, with a stated policy for "anything not in the list".

2. **Definitions / identifying criteria — how we decide.** Is each category or key entity *defined* in business terms — the data points, markers, or signals used to identify it and to place it in one bucket vs another? How do we decide a document *is* an invoice (vs a PO, a quote, a receipt)? Which fields/markers make it invoice-type-A rather than type-B? A category name with no identifying criteria is a **label, not a boundary** — the team can't build a classifier from "invoices".

3. **Covered vs explicitly excluded — per bucket.** For each bucket, what's covered; and — critically — what falls *outside* the defined set and is therefore **out of scope**, stated in words ("documents that aren't one of the 5 invoice types are not processed; non-invoice emails are ignored"). The exclusion must be written, not implied — this is the line that prevents scope creep and disputes.

4. **Completeness rules — mandatory vs optional.** For processing/extraction features, *which* business data points/fields must be handled, and which are **mandatory vs optional**? How many? What happens when a mandatory one is missing (reject, route to a human, flag)? ("Which fields" here means business data points and their required-ness — *not* their technical types or schema, which are the TL's.)

5. **Decision logic — inputs → rule → output, with a worked case.** For any feature that *decides, computes, assigns, prioritises, matches, routes, schedules, allocates, or optimises*, naming the factors is **not enough** — the scope must state **how those factors combine into the output**: the rule, ordering, weighting, or tie-break that turns the inputs into a result, at the business level, **plus at least one worked case** tracing a concrete input to its output. "Assigns each job to the best crew considering route, size, and speciality" names the factors but never says what happens when they conflict — that is a **label, not a decision**. A category name with no identifying criteria is a label without a boundary (item 2); a decision with named factors but no stated combination logic is a **label without a procedure** — the team can't build or estimate it. This is the decision-feature analogue of the classification definition in item 2, and it is a **business** decision, not implementation (see the callout above).

   **For derived-data features — dashboards, reports, KPIs, any computed metric — the same demand has three named parts: how, source, and verify.** A metric is a decision (inputs → formula → output), so a "Shows" line is not scope. For **each** metric the scope must give:
   - **How** — the business computation: what is counted, the formula shape (planned − actual; drive ÷ total paid), the time window, and the grouping/rollup. "Variance", "efficiency trend", "submission-readiness rollup", "drive-vs-productive ratio" named with no definition is a **label, not a metric**.
   - **Source (where)** — for each input to the formula, the named system and business data element it comes from (Acumatica budgeted hours per job; platform approved actuals; Acumatica property→supervisor ownership). Naming the metric's *output* is not naming its *inputs*.
   - **Verify (data-availability)** — an explicit verdict on each input's source: **Confirmed** (the system demonstrably holds it as readable business data) / **Assumed-to-confirm** / **Gap**. Any input a metric depends on that is `Assumed`/`Gap` promotes to a **dependency or `Blocker`** — a metric silently resting on data nobody has confirmed exists is the most common way a whole dashboard pillar turns out unbuildable. "Acumatica supplies them" is an assumption, not a verification. Keep this at the **business** level — *does the source hold this data and can we read it?* — not field types, keys, or the API contract, which stay with the TL.

   A metric with a `Shows` line but no how, or with inputs whose availability is only assumed, makes the feature **Partially-bounded at best**; a dashboard of metrics none of which state how or verify their inputs is **Unbounded**.

6. **Route expansion — one use case per materially-different route.** For any feature/module whose behaviour **forks by type, category, or condition**, the scope must expand each route into its own **use case** (scope §3.x.4) — with its own explanation, workflow, **flow diagram**, and **worked example** — and carry a **§3.x.3 master flow** whose branches line up 1:1 with those use cases. This is the routing analogue of the classification definition (item 2) and the decision logic (item 5): naming that "different invoice types take different routes" is a *label*; the bounded form is *each route written up as its own case*. The test for whether a fork deserves its own use case is **material difference** — different steps, actors, business rules, systems, or outcome. A fork that differs only by a **data value** while the steps stay identical (invoice under vs over an approval threshold) correctly stays a business rule or an alternative flow; do **not** demand a separate use case for it, and don't reward use-case sprawl that splits on trivial values.
   - **Named but not expanded** (the routes exist in the client's world and the scope alludes to them but documents one generic path) → **Partially-bounded (≤ 6)**; each un-expanded material route is a **`Major`** (a **`Blocker`** when the route difference drives the estimate — different systems, approvals, or posting).
   - **Not acknowledged** (the scope treats a genuinely branching process as single-path) → **Unbounded (≤ 4)**.
   - **Master flow missing or inconsistent** with the use cases (branches don't match the documented routes) → at least a **`Minor`**, or **`Major`** if it hides a route.

Assign every feature a **boundedness** verdict (`boundedness` in the data object):
- **Bounded** — categories enumerated and closed, each defined by identifying criteria, covered-vs-excluded stated per bucket, mandatory/optional clear, and — for a decision feature — the decision logic stated with a worked case, and — for a derived-data feature — each metric's how, source, and verified data-availability stated.
- **Partially-bounded** — the function and *some* boundaries are clear, but the category set, the identifying logic, the exclusions, or (for a decision feature) the combination logic behind named factors are missing or vague.
- **Unbounded** — function stated with no defined categories, no identifying criteria, and no exclusions ("classify invoices" and nothing more); **or** a decision feature that names its factors but states no combination logic and gives no worked case ("optimise the schedule" and nothing more); **or** a branching feature whose routes are neither expanded into use cases nor even acknowledged ("processes all invoice types" as a single path).

**Scoring hook — an unbounded feature cannot score above Weak (4/10)**, no matter how clearly its purpose is written, because a team cannot bound the estimate. A `Partially-bounded` feature is capped at Adequate (6). Raise the missing boundary as a **`Blocker`** when it drives the estimate (what/how much gets classified or processed, *how the core decision is made*, or *a route that posts/approves differently*) and a **`Major`** otherwise. The bounding layer expresses itself across four of the coverage dimensions below — **In scope / Out of scope** (the exclusions), **Business rules** (the definitions, classification logic, *and decision logic*), **Information & data** (the fields and mandatory/optional), and **Use-case / route expansion** (each materially-distinct route written up as its own §3.x.4 use case with a flow and a worked example) — so weak boundedness pulls those down together. For a decision feature, undefined combination logic behind named factors is itself an Unbounded trigger; for a branching feature, un-expanded material routes are the equivalent, exactly as an undefined category set is for a classifier.

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
**Covered:** the rules, thresholds, validations, and decision logic the feature enforces, each traceable to a source. **For any feature that classifies, identifies, routes, or matches, this must include the definition** — the business criteria/data points used to decide something is category A and not B ("a document is an *invoice* when it has X and Y; it's a *credit note* rather than a standard invoice when Z"). A rule set that names categories but never says how you tell them apart is **not** Covered — it's a label without logic. **For any feature that computes, assigns, prioritises, schedules, allocates, or optimises, this must include the decision logic** — how the named factors combine into the output, the ordering/weighting, and what wins when they conflict, illustrated by at least one worked case ("job goes to the crew already on its route; if that crew is over capacity, the engine interchanges the member with the most spare hours and the matching speciality; ties break on X"). A decision that names its factors but never states how they combine is **not** Covered — it's a label without a procedure.
**Red flags:** a feature that obviously encodes rules (eligibility, pricing, routing, classification, scheduling, assignment, allocation, approval limits) with none stated; category names with no identifying criteria; **named decision factors with no stated combination logic or tie-break, and no worked case**; rules implied inside an example but never lifted into the scope.

### 6. Information & data (`data_fields`)  — *carries the bounding layer's mandatory/optional fields*
**Business level only.** What *information* the feature captures, uses, or produces — described the way a business person would ("captures the customer's name, email, and order history; produces an approval decision"), plus where that information conceptually comes from and any data the client clearly cares about being present.
**Covered:** the business reader can tell what information the feature deals with; for extraction/processing features, **which business data points are handled and which are mandatory vs optional** (and what happens when a mandatory one is missing); and which data points are used to identify/classify the item. **For a derived-data / metric / dashboard / report feature, Covered additionally requires each displayed metric to be traced to (a) its computation — the *how* — and (b) each of its input data points and their named source, with the source's availability verified** (Confirmed / Assumed-to-confirm / Gap). A metric shown with no computation, or whose inputs are only assumed to exist in an upstream system, is **Partial** — and the unverified input is raised as a dependency/Blocker, not passed over.
**Red flags:** a data-entry, extraction, or data-display feature with no mention of *what* it captures/shows; "captures user details" / "extracts the fields" with no list of which fields matter to the business and no mandatory/optional split; **a dashboard/report pillar whose "Shows" line names a metric ("variance", "readiness rollup", "efficiency trend") with no stated computation, or whose source data is assumed available from an external system with no confirmation ("Acumatica supplies them")**; clearly-sensitive information (health, payment, ID) handled with no acknowledgement that it's sensitive.
**Out of scope for this review (hand to the TL):** field data types, lengths, nullability, schema, keys/indexes, validation rules, and how/where it's stored. A scope that omits these is correct — do **not** raise them.

### 7. Integrations (`integrations`)
**Business level only.** Which external systems/products the feature touches and what business information flows between them, in which direction, and who owns the dependency.
**Covered:** the named systems, the direction (we read from / write to / both), the business data exchanged, and the dependency owner. "None" is a valid, explicit answer. **For a feature whose decision depends on the integration's data** (a scheduler reading jobs/crews, a pricing engine reading rates, a dashboard scoped by an external hierarchy), Covered *additionally* requires the scope to state **which specific business data points are read and which decision factor each one feeds** — not just the named system and direction. Inputs named generically ("reads jobs, properties, and crew members from System X") with no input→factor mapping is **Partial at best**: naming the integration boundary is not the same as specifying the inputs the feature runs on, and the feature can't be estimated from a named boundary alone. **And naming a source is not confirming it: whenever a decision or a metric depends on data read from an external system, Covered requires the scope to state that the source actually holds that data as readable business data — verified, or explicitly flagged as an unconfirmed dependency.** "Acumatica supplies the budgeted hours / property ownership / hierarchy" with no confirmation is an assumption; every metric or decision resting on it inherits the risk, so it must be raised (dependency or Blocker), not assumed away. (This is business-level availability — *does the system hold it and can we read it* — not the API contract or field schema, which are the TL's.)
**Red flags:** an integration implied ("syncs with the CRM", "sends to the payment provider") with no **named system**, no direction, or no owner; **a decision feature's inputs named only as a generic list from the source system, with no statement of which field feeds which decision factor**; **a metric or decision that depends on external data the scope only *assumes* is available ("the ERP supplies it") with no availability confirmation and no dependency raised**; a third-party dependency the client must provide (a sandbox, credentials, an account) that isn't called out.
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
A "Shows" line per pillar is not scope. Every metric needs a **how**, a **source**, and a **verify** before the pillar is estimable — drill each one down:
- **Which reports/metrics exactly**, for **which roles**? Periodic or up-to-date? Drill-down or summary only?
- **How — metric definition (Blocker per metric).** Is each metric's *business* computation agreed — what is counted, the formula shape, the window, the grouping? "Variance", "readiness rollup", "drive-vs-productive ratio", "efficiency trend" are labels until defined (variance = approved actual − Acumatica budgeted, per job, as a %? absolute hours? over what period?). *(Where the number is computed technically is the TL's; what the number **means** is the client's.)*
- **Source (where) — per input.** For each input to the formula, which named system and business element does it come from? (Budgeted hours ← Acumatica; approved actuals ← platform; property→supervisor ownership ← Acumatica.) Naming the metric is not naming its inputs.
- **Verify — does the data actually exist (Blocker when unconfirmed).** For each input from an external system, has anyone confirmed the source holds it as readable business data, or is it merely *assumed*? "Acumatica supplies budgeted hours per job / property ownership / the org hierarchy" is an assumption; until confirmed it's a dependency, and any metric that needs it is at risk. This is the single most valuable question on a dashboard: a pillar resting on data nobody confirmed exists is unbuildable, however cleanly it's described.
- **Export / distribution:** export to CSV/PDF? Emailed on a schedule? Out of scope if not stated.
- **History:** what time range / how far back does the business need — and does the source retain that history, or is that itself an availability gap?
- **Acceptance:** what makes a report "right" in the client's eyes — a worked figure they'd sign off, not "the dashboard shows variance"?

The payoff: produce, for the module, a **data-availability check** — each metric's inputs listed against a Confirmed / Assumed / Gap verdict. That table is what the team carries into the integration deep-dive, and every `Assumed`/`Gap` is a raised question, not a silent hope.

### Worked example — "AI will categorise incoming requests" (AI/automation feature)
- **Categories:** fixed list or open? Who defines/maintains it?
- **Confidence & fallback (Blocker for AI features):** what accuracy does the business accept, and what happens when the AI is unsure — queue for a human, default category, reject? *(A business policy; the threshold mechanism is the TL's.)*
- **Human-in-the-loop:** does a person review all / sampled / low-confidence items, and can they correct it?
- **Sensitive data:** does the information being categorised include personal/sensitive data the client must be careful with? *(The business/compliance angle — not the model plumbing.)*
- **Volume:** roughly how many items/day, since it affects feasibility and cost?
- **Business edge cases:** an item that fits no category, or fits several — what should happen?

### Worked example — "The engine will optimise the schedule" (decision / optimization feature)
The verb *optimise* (or *assign*, *prioritise*, *allocate*, *match*, *route*, *schedule*) hides the entire feature. Naming the factors it "considers" is not scope — the decision **rule** is. Interrogate the **business decision logic** (not the algorithm or data structures, which are the TL's):
- **Inputs & their source (Blocker).** Exactly which data points does the decision run on, and where does each come from? "Reads jobs and crews from the ERP" is not enough — *which* fields (job location, job size, required completion date, crew roster, member availability, speciality), and is each one actually available from that system as structured data? An input the decision needs that the source can't supply is a Blocker, not a detail.
- **Combination logic (Blocker).** How do the factors combine into the output? What is the primary driver, what is secondary, and — critically — **what wins when two factors conflict** (nearest crew is over capacity; right speciality is on another route)? Named factors with no stated combination or ordering is a *label, not a decision*.
- **Tie-break & priority.** When two outputs score equally, what decides? When not everything fits, what gets sacrificed first (travel, completion date, crew continuity)?
- **A worked case (Blocker for decision features).** Trace at least one concrete input to its output: "Job J at property P (large, tree-speciality, due Friday) → assigned to Crew C already on P's route; C lacks a tree specialist, so member M is interchanged in as the nearest available specialist." Without one worked path, no one can confirm the rule produces what the client expects.
- **Unresolvable case (business exception).** What happens when the engine can't produce a valid output — no crew fits, capacity is exceeded everywhere? Who is told and what do they do?
- **Human-in-the-loop.** Does a person review/override the output, and is the output a suggestion or auto-applied? *(A business policy; the override mechanism is the TL's.)*
- **Acceptance.** What makes an output "right" in the client's eyes — a worked scenario they'd sign off on, not "the schedule is optimised."
- **Example check.** A decision feature with no worked scenario has nothing to validate against — treat missing examples as a real gap here (see §D), not a note.

That is one scope line → the handful of *business* decisions that make the engine estimable — without ever specifying the optimization algorithm, the solver, or the data model, all of which are the TL's.

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
- **No-examples** — no example exercises this feature; note it and consider a clarification. Don't fabricate compliance you can't evidence. **Exception for decision/optimization features:** because their combination logic can only be validated against a worked case, a decision feature with `No-examples` and no worked case in the scope carries at least a **Major** (not a bare note) — you cannot confirm the rule produces the client's expected result against air.

### General calibration notes
- **Score the scope, not the system.** A great system idea with a thin scope scores low here — the scope is the artifact people estimate and sign.
- **Severity drives the verdict, not question count.** Five Nits is a healthy 8; one undefined-auth-method Blocker caps an otherwise-good scope.
- **Bound before you praise.** The single most valuable thing this review does is turn "we know what the feature does" into "we know exactly what it covers and excludes." A clearly-written but unbounded feature is *not* a good scope — it's a well-phrased risk. Always ask the bounding questions (categories, definitions, exclusions, mandatory/optional — and, for a decision feature, the combination logic and a worked case) before scoring a feature above Weak.
- **Reward stated assumptions and explicit out-of-scope.** A scope that says "we assume corporate-email SSO only; social login is out of scope, phase 2" is *stronger* than one that silently omits it — surfaced uncertainty beats hidden uncertainty.
- **The most valuable questions are the ones the author can't see.** Anyone can note a missing field. The review earns its keep by catching the auth method nobody pinned down, the example the scope can't satisfy, the "sync with CRM" with no named system, the AI step with no fallback.
- **Be paranoid, not pedantic.** Every question you raise should be one a build team would otherwise hit. If answering it wouldn't change the estimate, the architecture, or the deliverable, it's a Nit at most — or not worth raising.
