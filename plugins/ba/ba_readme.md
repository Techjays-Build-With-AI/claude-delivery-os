# BA Agent — Discovery & Scope Review

The **Business Analyst Agent** has two jobs, and **`/ba:scope` does both in one command.** It is the project's **author and memory** — processing client artifacts into a living scope document and registers — and then its **paranoid critic**, breaking that scope down feature by feature, interrogating every under-specified line, validating it against the client's own examples, and scoring how estimate-ready it is. You get the scope, the questions, a score and a verdict from one run. `/ba:resolve` then answers the questions in conversation and folds the answers back into the scope.

**Review is not a step you run.** It happens inside every `/ba:scope`, because there is no useful state where you have built a scope and not reviewed it — you would have no score, no verdict and no questions. `/ba:review` still exists for a deliberate re-score without a scope pass, or to grade a scope document this pipeline never wrote.

So the whole loop is three commands:

```text
/ba:scope add "..."     build (and review) the scope
/ba:resolve             answer the open questions, in conversation
/ba:features            break the approved scope into features
```

## Building the living scope — `/ba:scope`

`/ba:scope` is the living-scope engine. You point it at client material — folders or Google Drive — and it references the originals in place, maps everything out into markdown summaries, and writes the module-centric **scope document** in the Techjays template (`ba/scope.md`). It's built to be run again and again: as new meeting notes, documents, examples, or client answers arrive, it updates the same living document rather than starting over.

```text
# build the scope from the first batch of material
/ba:scope add "transcripts in D:\acme\meetings, requirements at <drive-link>, invoice archive in D:\acme\invoices for reference only"

# later — fold in new notes or a client-answers doc, incrementally
/ba:scope add "answers in D:\acme\client-answers.md"
/ba:scope mode=incremental
```

Two things happen on every run:

- **It raises every open item.** All ambiguities, open questions, and assumptions become clarifications / assumptions, and it (re)generates **`ba/client-questions.md`** — a clean, handover-ready list grouped by module and prioritized (*Must close before estimate → Future phase*), with a blank space for each answer. Hand it to the client as-is.
- **It folds client answers back in (the answer round-trip).** Point it at a filled-in `client-questions.md`, a client-answers document, or fresh meeting notes, and it matches each answer to its open question by `CLR` id, closes it, applies the resulting edit to the scope, logs the decision or assumption, and drops the question off `client-questions.md`.

So the loop is: **`/ba:scope` to build → `/ba:resolve` to answer what you can → hand `client-questions.md` to the client for the rest → `/ba:scope add "answers…"` to fold their responses in → repeat.** One living scope document that keeps getting sharper. Modes: `auto` (default) · `incremental` · `full-refresh` · `dry-run` · `index-only` · `classify-only`.

Every run closes with the score, so you never have to go looking for it:

```text
Scope readiness: 8.7 / 10 — Significant gaps, clarify before estimate
Blockers: 1   Major: 5   Minor: 3
Thin on: Acceptance Criteria (3 modules) · Exception Handling (2)
```

| | |
|---|---|
| **Namespace** | `/ba:` |
| **Commands** | `/ba:scope …` (builds **and** reviews) · `/ba:resolve` (no argument needed — it asks) · `/ba:features` · `/ba:review [<scope-doc>]` for a deliberate re-score |
| **Review input** | A scope document (`.md`, `.docx`, `.pdf`) — defaults to `ba/scope.md` — plus the scope knowledge base (registers, examples, shared-context/) when a workspace exists |
| **Review output** | `ba/reviews/scope-review-<timestamp>.{html, md, json}` — interactive dashboard + Markdown artifact + data sidecar |
| **Skills** | `ba-classification` · `ba-extraction` (scope build) · `ba-scope-review` (review) |

---

### It asks what kind of work this is — once, up front

Not every requirement needs a full BA pass, so the first thing `/ba:scope` does is read your input and propose one of three paths, with its reason. You confirm or override:

```text
This is a written client requirement from Novacore Solutions, with an
external client who answers the questions. I would take the first.

  1 · Client requirement       full scope, registers, client packet, review
  2 · Task needs a BA plan     internal, code-first; questions go to open-questions.md
  3 · Straight to /dev:plan    one repo, understood well enough to build
```

| | For | Reads the code? | Produces |
|---|---|---|---|
| **Client requirement** | work a client signs off and someone estimates | no | scope · registers · `client-questions.md` · review |
| **Task needs a BA plan** | a module-sized internal piece: too big for one flat plan, no client to question | **yes** — reads `context/code-context/` for the area the requirement touches | scope document + feature split, questions to `ba/open-questions.md` |
| **Straight to `/dev:plan`** | one repo, understood well enough to build | at plan time | nothing — hands off and stops |

**Two checkable rules disqualify the third option:** surfaces spanning more than one repo, or more than ~3 features. Either one and it needs a BA plan at least, whatever it looks like.

The middle path exists because a module-sized internal change had nowhere to go — too large for one flat `/dev:plan`, too internal for a full client pass. It starts from the code, so the scope is written against what actually exists rather than guessed at and corrected two commands later.

### One requirement at a time

If a scope already exists, `/ba:scope` asks before touching it:

```text
A scope already exists here:
  Shift-based timesheet · v0.4 · Reviewed · 6 modules · last run 2026-10-04

  1 · New material — more transcripts, answers, or changes to the same requirement
  2 · A different requirement — clear the current work and start fresh
```

A workspace holds **one requirement's working state**. Two requirements in one `ba/` tree is not two scopes — it is one scope describing two unrelated things, with modules interleaved and a readiness score computed over the pair. Choosing the second clears `ba/` and `features/` and keeps `shared-context/` (glossary, stakeholders, decisions — project-level truth that outlives any one requirement). The scope and registers already pushed to Jetrix can be pulled back; the run tells you what is local-only before it goes.

---

## What the scope review does

The review's defining behaviour is **productive paranoia**. A scope line like *"the system will have a login screen"* isn't a feature — it's the *name* of one with everything that matters left unsaid. The agent turns that one line into the dozen questions an estimator actually needs (which auth method? email vs social vs SSO? personal vs corporate email? verification, lockout, MFA, session rules, roles, PII/compliance?), so the gaps surface **before** the estimate, not mid-sprint.

For every feature/module in the scope, the agent judges **coverage depth** across the nine Techjays D&D dimensions, marking each **Covered / Partial / Absent**:

| # | Dimension | What "Covered" means |
|---|-----------|----------------------|
| 1 | Current → Future state | Today's actors/triggers/systems/manual steps and the future AI/DET/HUM split are described |
| 2 | In scope / Out of scope | The boundary is explicit — including what's deliberately *out* |
| 3 | Functional requirements | Capabilities enumerated with responsibility (AI/DET/HUM) and MoSCoW priority |
| 4 | AI / Automation responsibilities | What the AI does, its confidence threshold + fallback, and the human-in-the-loop |
| 5 | Business rules | The rules, thresholds, and decision logic the feature enforces |
| 6 | Information & data | What information the feature captures/uses/produces, at a business level (not field types or schema) |
| 7 | Integrations | Which external systems it touches and what business data flows, and who owns the dependency (not API contracts) |
| 8 | Exceptions & edge cases | The business unhappy paths — invalid request, missing approval, duplicate, dispute — and who handles them |
| 9 | Acceptance criteria | Capability-level "done" the client and team agree on (not detailed test cases) |

> **It's a business review, not a technical one.** The scope review judges *what the business wants* and deliberately leaves *how it's built* to the TL's `tl-spec-review`. It will **not** flag — and never penalises the scope for omitting — system design, database/schema, field data types, API contracts/protocols, auth mechanisms, infrastructure, or tech-stack choices. A scope that leaves those open is correct. The litmus test for every question it raises: *is this a decision the client/business makes, or one the engineers make?* Only the former belong here.

### The bounding layer (the heart of the review)

Knowing *what a feature does* is not knowing *its boundary* — and an unbounded feature is where estimates blow up and scope disputes start. So before scoring the nine dimensions, the review **bounds every feature**, demanding four things:

1. **Categories / buckets — enumerated and closed.** *Which* things does it operate on? "Classify the invoice" → which 4–5 invoice types? What about anything not in that list?
2. **Definitions / identifying criteria.** How is each category *defined* — the business data points used to decide a document *is* an invoice (vs a PO or receipt), and what puts it in one bucket vs another? A category name with no criteria is a label, not a boundary.
3. **Covered vs explicitly excluded — per bucket, in words.** e.g. "documents that aren't one of the 5 invoice types are not processed; non-invoice emails are ignored." The exclusion must be written, not implied.
4. **Mandatory vs optional fields.** Which business data points must be processed, which are mandatory vs optional, and what happens when a mandatory one is missing.

Each feature gets a **boundedness** verdict — **Bounded**, **Partially-bounded**, or **Unbounded** — shown as a badge in the report. It's not just a label: an **Unbounded** feature is **capped at 4/10** and a **Partially-bounded** one at **6/10**, no matter how clearly its purpose is written, because a team can't bound the estimate. So "read the email, classify the invoice, process it" — clear function, no defined types/definitions/exclusions — scores as Weak with Blocker questions until the buckets, the classification logic, and the in/out boundary are pinned down. This is what stops the review from staying high-level.

It also runs an **example check** per feature against the client's `example-register` (the scenarios they actually shared): **Pass** (scope satisfies the example), **Partial** (some implied path/field is missing), **Conflict** (the example contradicts the scope — e.g. an example shows Google sign-in but the scope says email/password only, citing the `EX-###` id), or **No-examples**. A scope that can't satisfy a real example the client handed you has a citable gap, not a nicety.

### Scoring & verdict

Each feature gets a **0–10 score** on how completely and unambiguously it's scoped (9–10 Excellent … 1–2 Stub … 0 Absent). The **overall score** is the average of all features, mapped to a scope-readiness verdict — and **any unresolved Blocker caps the verdict** no matter how high the average:

| Overall | Verdict |
|---------|---------|
| ≥ 8.5, no Blockers | **Scope-ready — estimate with confidence** |
| 6.5–8.4, no Blockers | **Estimate with caveats** |
| 4.5–6.4, or any Blocker | **Significant gaps — clarify before estimate** |
| < 4.5 | **Not scope-ready — discovery needed** |

Every gap is logged as a **scope question** with a stable `SQ-###` ID and a severity that maps onto the BA's RAID open-question classes:

| Severity | Meaning | RAID class |
|----------|---------|------------|
| `Blocker` | Must close before estimate — swings effort/architecture/data/integration/security/cost | *Must close before estimate* |
| `Major` | Close before build; workable only with an explicit, accepted assumption | *Proceed with assumption* |
| `Minor` | Contained implementation detail | *Minor implementation detail* |
| `Nit` | Polish or safely deferred | *Future phase* |

---

## Setup

Installation and workspace setup are shared across all Delivery OS plugins — see **[docs/SETUP.md](../../docs/SETUP.md)**. The short version for `ba`:

```text
/plugin marketplace add techjays/claude-delivery-os
/plugin install delivery-os@techjays-delivery-os
/plugin install ba@techjays-delivery-os
```

### Do I need `/delivery-os:init`?

A workspace is **recommended but optional** for `/ba:review`:

| | With a workspace (`init` + `/ba:scope` were run) | Standalone (no workspace) |
|---|---|---|
| **Default input** | `ba/scope.md` if you give no path | you must point it at a scope file |
| **Knowledge base** | also reads `ba/registers/examples.md` + the other registers, `ba/logs/clarifications.md`, `ba/logs/contradictions.md`, `shared-context/` — so it can validate against examples and detect register↔scope drift | reviews only the document you point it at; example-compliance is limited to what's in that file |
| **Report location** | `ba/reviews/scope-review-<timestamp>.{html,md,json}` | written **beside the reviewed document**, with a note that no workspace was found |
| **Resolution promotion** | `/ba:resolve` folds answers back into `scope.md`, `decision-log.md`, `ba/registers/assumptions.md`, `ba/logs/clarifications.md` | resolution stays in the report; it lists the edits to apply by hand |

So: run the full discovery flow if you want the review grounded in the client's examples and the answers folded back into the scope; skip it for a quick one-off review of any scope file.

---

## Usage

```text
/ba:review [<path-or-link-to-scope>] [out=<output-prefix>]
```

- **`<scope-doc>`** — optional. Defaults to `ba/scope.md` inside a workspace. Accepts `.md`, `.docx`, `.pdf`, or a link.
- **`out=<prefix>`** — optional. Overrides where the report is written. A run timestamp is **always** appended, so repeated reviews never overwrite each other.

Each run is timestamped (`scope-review-2026-06-30-143012.html`), so `ba/reviews/` accumulates a full review history. Every `/ba:scope` and every `/ba:resolve` adds a round, so the history builds itself — and from round 2 each report opens with a **Since the last round** section saying what your previous answers became. `/ba:review` on its own re-scores without a scope pass, which is what you want after hand-editing `ba/scope.md` or to grade a scope document this pipeline never wrote.

---

## Worked example

You've run discovery for an **Acme Customer Portal**:

```text
/ba:scope add "transcripts in D:\acme\meetings, requirements at <drive-link>"
```

It confirms the track (client requirement), builds the scope and registers, then reviews what it just wrote — a second agent reading the document fresh, so the critic is not the author. The headline it returns:

> **Overall score: 3.4/10 — Significant gaps — clarify before estimate.**
> Clean module breakdown, but the Login feature is a one-liner and conflicts with a client example, and the CRM integration names no system. Two Blockers gate the estimate.

The feature scorecard:

| # | Feature | Kind | Score | Status | Boundedness | Examples |
|---|---------|------|:-----:|--------|-------------|----------|
| 1 | Login & Authentication | UI / auth | 2/10 | Stub | Unbounded | Conflict |
| 2 | CRM Integration | integration | 3/10 | Weak | Partially-bounded | No-examples |
| 3 | Reporting Dashboard | data/reporting | 7/10 | Good | Bounded | Pass |
| | **Overall** | | **3.4/10** | **Significant gaps — clarify before estimate** | | |

Open the Login feature and you see why it's a 2 — eight of nine dimensions are **Absent** — and the questions the agent raised from that single "login screen" line:

| ID | Sev. | Feature | Question | Suggested scope addition |
|----|------|---------|----------|--------------------------|
| SQ-004 | Blocker | AUTH | Which auth methods are in scope — email/password, social (Google/Apple/Microsoft), OTP/passwordless, magic link, or enterprise SSO? | In §3.1.3 list the methods with Resp./Pri.; reconcile with EX-004 (Google sign-in) |
| SQ-005 | Major | AUTH | Are registration, password reset, and profile management in scope, or out? | State each explicitly in §3.1.2 In/Out of scope |
| SQ-006 | Major | AUTH | What are the account-access policies the business wants — email verification, lockout after repeated failures, MFA (required/optional/none)? | Add the access policies to §3.1.5 (the *what*, not the technical controls) |
| SQ-011 | Blocker | CRM | Which CRM system, and do we read from it, write to it, or both? | Name the system and direction + the business data exchanged in §3.2.7 |

The **example check** is what turns "this feels thin" into a citable gap: `EX-004` shows a user signing in with Google, but the scope mentions only email/password — a **Conflict**, surfaced against the Login feature.

---

## Reading the interactive HTML dashboard

`scope-review-<timestamp>.html` is fully self-contained — **no internet, no dependencies** — just open it in any browser. It gives you:

- **Sticky header** with the color-coded overall score and scope-readiness verdict badge.
- **Feature scorecard** with score bars, grouped by module group, plus an **example-compliance badge** per feature. **Click any row** to jump to that feature's detail.
- **Per-feature coverage matrix** — the nine dimensions rendered as colored Covered/Partial/Absent cells, so you see at a glance where the scope is thin. Weak features auto-open first.
- **Live severity filter** on the scope-questions register — click `Blocker (n)` / `Major (n)` / … to filter instantly.
- **Clickable feature↔question links** — question chips inside a feature jump to and flash-highlight the row in the register.
- **Dark mode** (follows your OS) and a **print-friendly** layout.

The Markdown twin (`scope-review-<timestamp>.md`) is the same content as a clean Delivery OS document — frontmatter, stable IDs, greppable and diff-friendly. The `scope-review-<timestamp>.json` sidecar holds the structured data the resolution loop reads. All three render from one data object, so they never disagree.

---

## Closing questions — the resolution loop (`/ba:resolve`)

A review *raises* scope questions; the loop *closes* them — and, uniquely for the BA, **applies each answer to the scope** so the gap is fixed at the source rather than described in a report.

### Run it with no arguments — it asks

```text
/ba:resolve
```

It reads the open questions from the latest review and asks them **one at a time**, in the conversation. No file to export, no round-trip. Each question arrives with what it is, why it matters, where the answer was already looked for, and realistic options:

```text
CLR-021  ·  Blocker  ·  Timesheet — allocations

When someone is removed from a project after logging hours against it,
what happens to those hours and that row — including in weeks already
submitted?

Same scenario in 3 places — one answer settles all three:
  · TIME-UC-04   removed mid-week, week not yet submitted
  · TIME-UC-07   removed after submission, before approval
  · PAY-UC-02    removed after payroll has pulled the week

  1 · Hours stay, row locks        2 · Hours move to unallocated
  3 · type your own                 d · defer
  s · these are not the same — split them
```

**Run it as often as you like.** It only ever asks what is still open, so an answered question never comes back and a deferred one always does. Answer what you know, defer the rest, come back later.

### From round 2, it opens with what moved

```text
Round 3 — since you last answered

  Accepted (4)                   in the scope, closed
     · week closes Sunday 23:59 Gulf time         → §3.2, DEC-012
  Assumption (1)                 building on it, the client still to confirm
     · 12-hour cap is per calendar day            → ASM-007
  Answered — not enough yet (1)
     · multi-site split
       You said: "split it evenly"
       Not enough because: evenly by hours, or by the rate at each site?
       Need: which basis, and what happens when the rates differ.
  Still open (1)                 waiting on the client
  New (1)                        raised by your own answers
```

That block is the answer to *"did my last answers actually land?"* — and **"Answered — not enough yet"** is the one that matters: a vague answer is shown as read-but-insufficient with a specific follow-up, rather than quietly sitting in the open list looking like you never answered it.

### What it does with each answer

- **Resolved** — specific enough to estimate against. **Edits `ba/scope.md`** at the owning §3.x, logs a `DEC-###`. Where the question covered several places, it edits **every** one.
- **Accepted-assumption** — the client can't confirm now, so the team proceeds on an explicit assumption (`ASM-###` / RAID A-##), written into the scope marked as assumed, with the residual risk noted.
- **Needs-verification** — plausible but thin; 1–3 targeted follow-ups, asked **in the same sitting** while you still hold the context.
- **Won't-fix / still Open** — declined or deferred, with the remaining gap recorded.

Then it re-scores: coverage maps updated, feature scores and the verdict recomputed — a resolved Blocker lifts the cap — and a fresh timestamped round written with questions carried forward.

### The file path still works

```text
/ba:resolve ba/reviews/scope-review-<timestamp>-responses.md
```

Point it at an exported responses file and it behaves as it always has. **That is still the right flow when the answerer is a client who is not in the room**: hand them `ba/client-questions.md`, or the HTML report where they can answer inline and click *Export responses*.

> Timestamped rounds keep the **full history** — what was open at review time, what was said, and how each question was closed.

---

## How it fits Delivery OS

The scope review is the BA reviewing **its own deliverable** before handoff — distinct from the TL agent's `tl-spec-review`, which is a *technical* review of a spec/architecture and consumes `ba/scope.md` as input. The review writes only to `ba/reviews/` (and, on resolve, the registers/decision-log it promotes into); it never silently edits the living scope — it *recommends* the exact edits, which a subsequent `/ba:scope` or a manual edit applies. All outputs carry standard frontmatter (`doc_type: scope-review`, `produced_by: ba`).

See the shared [`delivery-os-conventions`](../delivery-os-core/skills/delivery-os-conventions/SKILL.md) skill for the full document contract.

---

## FAQ

**Does it need a scope produced by `/ba:scope`?** No — it'll review any scope file you point it at. But inside a workspace it's much stronger, because it can validate against the client's `example-register` and detect drift between the registers and the scope.

**What if there's no example-register?** It still reviews coverage, but says so — a scope with no examples to validate against is itself a noted limitation (you're validating against air).

**Why did one Blocker cap an otherwise-decent score?** By design. One unknown that swings the estimate (an undefined auth method, an unnamed integration partner) makes the whole price a guess, so the verdict is capped regardless of the average. Resolving it via `/ba:resolve` lifts the cap.

**Is it being too picky?** It's tuned to be *paranoid, not pedantic* — every question should be one a build team would otherwise hit. If answering a question wouldn't change the estimate, the architecture, or the deliverable, it's a Nit at most.

**Do I have to use the HTML to respond?** No — the responses file is plain Markdown. *Export responses* just generates it with the right name and headers. You can hand-write or edit `scope-review-<timestamp>-responses.md` and run `/ba:resolve` on it.

**Can I review the same scope twice?** Yes — that's the point of timestamped filenames. Re-review after revising the scope; the old report stays put so you can compare rounds.
