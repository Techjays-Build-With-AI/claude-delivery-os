# BA Agent — Discovery & Scope Review

The **Business Analyst Agent** has two jobs. During discovery it is the project's **author and memory** — `/ba:intake` processes client artifacts into a living scope document and registers. Once a scope exists, it becomes its **paranoid critic** — `/ba:review` breaks the scope down feature by feature, interrogates every under-specified line, validates it against the client's own examples, and scores how estimate-ready it is, then `/ba:resolve` closes the open questions and folds the answers back into the scope.

This guide focuses on the **scope review** (`/ba:review` · `/ba:resolve`). For discovery intake, see [`commands/intake.md`](commands/intake.md).

| | |
|---|---|
| **Namespace** | `/ba:` |
| **Commands** | `/ba:intake …` · `/ba:review [<scope-doc>] [out=<prefix>]` · `/ba:resolve <responses-file>` |
| **Review input** | A scope document (`.md`, `.docx`, `.pdf`) — defaults to `ba-output/scope.md` — plus the scope knowledge base (registers, examples, shared-context) when a workspace exists |
| **Review output** | `ba-output/scope-reviews/scope-review-<timestamp>.{html, md, json}` — interactive dashboard + Markdown artifact + data sidecar |
| **Skills** | `ba-classification` · `ba-extraction` (intake) · `ba-scope-review` (review) |

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
| 6 | Data fields | Entities/fields with types, required-ness, source/validation |
| 7 | Integrations | External systems, direction, data exchanged, dependency/owner |
| 8 | Exception handling | The unhappy paths — invalid input, failure, timeout, duplicate, conflict |
| 9 | Acceptance criteria | Testable criteria tied to the feature's requirement IDs |

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

| | With a workspace (`init` + `/ba:intake` were run) | Standalone (no workspace) |
|---|---|---|
| **Default input** | `ba-output/scope.md` if you give no path | you must point it at a scope file |
| **Knowledge base** | also reads `example-register.md` + the other registers, `clarification-log.md`, `contradiction-log.md`, `shared-context/` — so it can validate against examples and detect register↔scope drift | reviews only the document you point it at; example-compliance is limited to what's in that file |
| **Report location** | `ba-output/scope-reviews/scope-review-<timestamp>.{html,md,json}` | written **beside the reviewed document**, with a note that no workspace was found |
| **Resolution promotion** | `/ba:resolve` folds answers back into `scope.md`, `decision-log.md`, `assumption-register.md`, `clarification-log.md` | resolution stays in the report; it lists the edits to apply by hand |

So: run the full discovery flow if you want the review grounded in the client's examples and the answers folded back into the scope; skip it for a quick one-off review of any scope file.

---

## Usage

```text
/ba:review [<path-or-link-to-scope>] [out=<output-prefix>]
```

- **`<scope-doc>`** — optional. Defaults to `ba-output/scope.md` inside a workspace. Accepts `.md`, `.docx`, `.pdf`, or a link.
- **`out=<prefix>`** — optional. Overrides where the report is written. A run timestamp is **always** appended, so repeated reviews never overwrite each other.

Each run is timestamped (`scope-review-2026-06-30-143012.html`), so `ba-output/scope-reviews/` accumulates a full review history — re-review after the scope is revised and compare.

---

## Worked example

You've run discovery for an **Acme Customer Portal** and produced a first scope. Before sending it for estimate, you sanity-check it:

```text
/ba:review
```

The agent reads `ba-output/scope.md`, loads the example-register and the other registers, decomposes the scope into features, and writes the report. The headline it returns:

> **Overall score: 3.4/10 — Significant gaps — clarify before estimate.**
> Clean module breakdown, but the Login feature is a one-liner and conflicts with a client example, and the CRM integration names no system. Two Blockers gate the estimate.

The feature scorecard:

| # | Feature | Kind | Score | Status | Examples |
|---|---------|------|:-----:|--------|----------|
| 1 | Login & Authentication | UI / auth | 2/10 | Stub | Conflict |
| 2 | CRM Integration | integration | 3/10 | Weak | No-examples |
| 3 | Reporting Dashboard | data/reporting | 7/10 | Good | Pass |
| | **Overall** | | **3.4/10** | **Significant gaps — clarify before estimate** | |

Open the Login feature and you see why it's a 2 — eight of nine dimensions are **Absent** — and the questions the agent raised from that single "login screen" line:

| ID | Sev. | Feature | Question | Suggested scope addition |
|----|------|---------|----------|--------------------------|
| SQ-004 | Blocker | AUTH | Which auth methods are in scope — email/password, social (Google/Apple/Microsoft), OTP/passwordless, magic link, or enterprise SSO? | In §3.1.3 list the methods with Resp./Pri.; reconcile with EX-004 (Google sign-in) |
| SQ-005 | Major | AUTH | Are registration, password reset, and profile management in scope, or out? | State each explicitly in §3.1.2 In/Out of scope |
| SQ-006 | Major | AUTH | Session length, lockout after N failures, and MFA — required, optional, or none? | Add session + security rules to §3.1.5 |
| SQ-011 | Blocker | CRM | Which CRM, and is it read/write/bidirectional, real-time or batch? | Name the system + API style + direction in §3.2.7 |

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

A review *raises* scope questions; the loop *closes* them — and, uniquely for the BA, **folds each answer back into the scope** so the gap is fixed at the source.

**The flow:**

1. **Respond in the report.** Open `scope-review-<timestamp>.html`, scroll to **Open questions**, and under each one type your answer and pick an intent (`resolve` / `accept-assumption` / `need-info` / `wont-fix`).
2. **Export.** Click **Export responses**. The page downloads `scope-review-<timestamp>-responses.md` — named with the **same timestamp** as the review, which ties the answers back to it. (Browsers can't write to disk, so it lands in Downloads — move it into `ba-output/scope-reviews/`.)
3. **Resolve.** Run `/ba:resolve ba-output/scope-reviews/scope-review-<timestamp>-responses.md`. The agent matches the timestamp to the review's `.json`, then **adjudicates each answer**:
   - **Resolved** — answers the question with specifics a team could estimate against; records the exact scope edit and a `DEC-###` decision.
   - **Accepted-assumption** — the client can't confirm now, so the team proceeds on an explicit, logged assumption (`ASM-###` / RAID A-##), with the residual risk noted.
   - **Needs-verification** — plausible but thin; it asks 1–3 targeted follow-ups and keeps the item open.
   - **Won't-fix / still Open** — declined/deferred or unaddressed, with a note on the residual gap.
4. **Promote & re-score.** Confirmed answers are folded into `scope.md` (the agent gives the exact §3.x edit) and the relevant register; each feature's coverage map is updated; the feature scores and overall verdict are **recomputed** — a resolved Blocker lifts the cap. A fresh timestamped round is written (`round` 2, `priorReview` linking back) with questions carried forward by their `SQ-###` IDs.
5. **Repeat** until no open questions remain.

**Worked example (continuing Acme):** you answer SQ-004 with *"Email/password + Google SSO, corporate domains only, email verified, MFA optional in phase 1; registration and reset in scope, profile is phase 2"* and export. `/ba:resolve` judges this specific and consistent with EX-004 → marks **SQ-004 Resolved**, gives the §3.1.3 edit, logs **DEC-007**, refills the Login coverage map, and — with that Blocker cleared — lifts the verdict from *Significant gaps* toward *Estimate with caveats*. A vaguer *"we'll support standard login"* comes back as **Needs-verification** with pointed follow-ups.

> Why a separate step rather than editing in place? Timestamped rounds keep the **full history** — what was open at review time, what the author said, and how each question was closed.

---

## How it fits Delivery OS

The scope review is the BA reviewing **its own deliverable** before handoff — distinct from the TL agent's `tl-spec-review`, which is a *technical* review of a spec/architecture and consumes `ba-output/scope.md` as input. The review writes only to `ba-output/scope-reviews/` (and, on resolve, the registers/decision-log it promotes into); it never silently edits the living scope — it *recommends* the exact edits, which a subsequent `/ba:intake` or a manual edit applies. All outputs carry standard frontmatter (`doc_type: scope-review`, `produced_by: ba`).

See the shared [`delivery-os-conventions`](../delivery-os-core/skills/delivery-os-conventions/SKILL.md) skill for the full document contract.

---

## FAQ

**Does it need a scope produced by `/ba:intake`?** No — it'll review any scope file you point it at. But inside a workspace it's much stronger, because it can validate against the client's `example-register` and detect drift between the registers and the scope.

**What if there's no example-register?** It still reviews coverage, but says so — a scope with no examples to validate against is itself a noted limitation (you're validating against air).

**Why did one Blocker cap an otherwise-decent score?** By design. One unknown that swings the estimate (an undefined auth method, an unnamed integration partner) makes the whole price a guess, so the verdict is capped regardless of the average. Resolving it via `/ba:resolve` lifts the cap.

**Is it being too picky?** It's tuned to be *paranoid, not pedantic* — every question should be one a build team would otherwise hit. If answering a question wouldn't change the estimate, the architecture, or the deliverable, it's a Nit at most.

**Do I have to use the HTML to respond?** No — the responses file is plain Markdown. *Export responses* just generates it with the right name and headers. You can hand-write or edit `scope-review-<timestamp>-responses.md` and run `/ba:resolve` on it.

**Can I review the same scope twice?** Yes — that's the point of timestamped filenames. Re-review after revising the scope; the old report stays put so you can compare rounds.
