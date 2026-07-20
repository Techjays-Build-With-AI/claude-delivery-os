# TL Agent — Technical Design Authoring & Specification Review

The **Technical Lead Agent** does two jobs a seasoned TL does. It **authors** the technical design context a team builds from — mapping each BA feature to its pages, endpoints, and database entities and wiring them into a linked graph (`/tl:plan`) — and it **reviews** a technical specification for an applied AI system before a team commits engineering time and budget, handing back a **scored, actionable review** (`/tl:review`, `/tl:resolve`).

| | |
|---|---|
| **Namespace** | `/tl:` |
| **Commands** | `/tl:plan <feature-or-features>` · `/tl:review <doc> [out=<prefix>]` · `/tl:resolve <responses-file>` · `/tl:scaffold [spec] [repo=<path>]` · `/tl:map [repo=<path>]` · `/tl:maturity [repo=<path>] [strict-baseline]` |
| **Input** | Feature planning: the BA feature breakdown under `context/features/`. Spec review: a tech spec / architecture / system-design / HLD / SRS document (`.md`, `.docx`, or `.pdf`). Scaffold: the confirmed architecture (spec / `context/project/`) + the context graph |
| **Output** | Feature planning: the linked `context/frontend|backend|database` graph + three indexes. Spec review: `tl-output/spec-review-<timestamp>.{html, md, json}`. Scaffold: the initial application repository (skeleton + tooling + green base) and `context/project/{technology-stack, architecture, coding-standards}.md` |
| **Skills** | `tl-feature-planning` · `tl-spec-review` · `tl-project-scaffold` · `tl-codebase-map` · `tl-maturity-audit` |

---

## Feature planning (`/tl:plan`)

Point it at one feature folder or the whole `context/features/` set. For each feature it maps the pages/APIs/data-entities the BA declared into real, linked unit files: **pages** (`context/frontend/pages/`), **endpoints** (`context/backend/domains/`), and **entities** (`context/database/entities/`). It **reuses** a unit and adds a back-link where its match key already exists (page route, endpoint `METHOD + path`, entity object name), and creates it — minting the next `PAGE-`/`EP-`/`ENT-<AREA>-NN` — where it doesn't, so shared units live once with many links rather than duplicated per feature.

The result is a **bidirectional graph**: a page links to the endpoints it consumes, an endpoint to its callers and the entities it touches, an entity back to its consuming endpoints and to the BA `DATA-###` it realises. Database entities cite the BA data-register (not a parallel ID space), material design decisions are logged as `DEC-###`, genuine unknowns become open questions rather than invented contracts, and a **link-integrity check** flags any dangling reference, uncalled endpoint, or orphan entity. Backend-only features (jobs, events, webhooks, integrations) enter at endpoints, skipping the page layer.

---

## Project scaffold (`/tl:scaffold`)

Feature planning and code both need a codebase to live in. On a **greenfield** project there isn't one yet — and the dev agent refuses to scaffold with a guessed stack, because the stack is an architecture decision. `/tl:scaffold` is where that decision gets made and executed, under the TL's architecture hat.

Point it at the tech spec / architecture (or let it read `context/project/` + `shared-context/`). It extracts every stack choice the architecture **confirms**, and for every required choice it leaves **open** — application type, repo layout, frontend framework, backend language/framework, database, package manager, test framework — it **asks you with a recommended option and a one-line rationale** grounded in the project profile and the shape of the context graph. It never silently guesses a critical stack decision.

Then it scaffolds: the idiomatic skeleton (preferring official generators like `create-vite`, `spring init`, `poetry new`), package-manager manifests, lint/format/type/test/build tooling, one trivial passing test, a README and `.gitignore`, and it writes `context/project/{technology-stack.md, architecture.md, coding-standards.md}`. Every stack decision — spec-confirmed or you-answered — is logged as a `DEC-###`. Before handing off it runs `install → lint → type-check → test → build` and confirms the **base build is green** — the exact readiness item the dev agent checks. It scaffolds the *foundation*, not features; the dev agent's `feature-delivery-loop` builds those into it.

Once it's done, the workspace is build-ready: `/dev:build <feature>` (and the dev agent's `/dev:bootstrap` greenfield check) will pass.

---

## Maturity audit (`/tl:maturity`)

Feature planning, scaffold, and spec review all act *before or around* the build. `/tl:maturity` acts on the **built system**: a read-only, evidence-backed score of how production-ready a project actually is, and where the engineering risk lies. It's the third of three audits in Delivery OS, each with a different subject — `/tl:review` scores a design **document**, `/qa:audit` scores the **test harness**, and `/tl:maturity` scores the **running system's reality**, consuming the other two.

It scores four domains, each out of 10 (average of applicable sub-areas; any Blocker caps the tier):

| Domain | What it looks at |
|---|---|
| **Code Quality & Maintainability** | lint cleanliness & enforcement, complexity, duplication, dependency hygiene, docs/ADRs, architectural adherence |
| **Test Quality & Verifiability** | unit/integration/e2e presence, coverage level & enforcement, CI gating — **consumes `qa-output/quality-gates.md`; does not re-score testability** |
| **Infrastructure & Operations** | CI/CD reliability, deployment safety (rollback, zero-downtime, migration safety), observability, scalability, env parity / IaC |
| **Security** | dependency CVEs, SAST, secrets in code/history, authN/authZ posture, secrets management |

**How it stays honest.** It prefers the project's **own enforced tooling** as evidence (the SonarScanner posture): a check wired into pre-commit/CI and passing scores highest — reading that tool's output *and* rewarding the enforcement. It only falls back to an ephemeral scanner where the project has nothing. Every check is tagged **`evidenced`** (a tool produced it) or **`attested`** (a human answered because no tool can see it — observability platform, rollback, autoscale), and it never fabricates a score for something it couldn't measure (`not measured`, never `0`). Alongside the maturity score it reports a **separate Audit Confidence** — the share of applicable checks actually tool-measured — so a high score resting on little measurement can't hide.

**The QA baseline gate.** In preflight it reads the active `baseline-profile.md` and `quality-gates.md`'s `baseline_status` to check whether the mandatory tooling floor (enforced lint, coverage gate, dependency + secret scanning) is in place. If it isn't, it **reminds and routes** to `/qa:audit` → `/qa:setup` and — by default — still scores in **degraded mode** at reduced Audit Confidence; with `strict-baseline` it stops before scoring. It never establishes the baseline itself.

**Read-only, always.** It installs nothing into the repo, changes no code or tests, and routes tooling gaps back to QA rather than fixing them. Output is a timestamped trio in `tl-output/` — `maturity-<timestamp>.{html, md, json}` — the interactive report carries the domain scorecard, the Audit Confidence split, and a `MAT-###` findings register with per-finding evidence and `routes-to-QA` badges. The JSON sidecar is keyed for a future org-wide portfolio rollup.

```text
/tl:maturity                                   # score the current workspace / repo
/tl:maturity repo=D:\acme\orders-service       # point at a repo
/tl:maturity repo=D:\acme\orders-service strict-baseline   # require the QA baseline first
```

---

## What it reviews

The agent first works out the **system profile** — does it use an LLM/AI? does it span multiple systems? — because that decides which areas apply. Then it scores each applicable area **out of 10**, backing every deducted point with a finding and a concrete fix.

| Group | Areas scored |
|-------|--------------|
| **Architecture & Design** | Overview & problem framing · Architecture & system design · Feature flows & system sequencing |
| **Engineering Contracts** | Data schema & modeling · API contracts · Libraries & tech stack |
| **Applied AI / LLM** *(only when an LLM is involved)* | Observability & traceability · Evaluation strategy · Feedback loops · AI compliance, safety & governance |
| **Delivery & Operations** | Infrastructure & environment setup · CI/CD & release management · Cost projection (infra + LLM/API + third-party) |

If the system isn't AI-powered, the Applied-AI areas are marked **N/A** and excluded from the score. If it's a single service, cross-system flow expectations are scoped down rather than penalized.

### Scoring & verdict

Each area gets a 0–10 score (9–10 Excellent … 0 Absent, or N/A). The **overall score** is the average of applicable areas, mapped to a readiness verdict — and **any unresolved Blocker caps the verdict** no matter how high the average:

| Overall | Verdict |
|---------|---------|
| ≥ 8.5, no Blockers | **Ready to build** |
| 6.5–8.4, no Blockers | **Build with caveats** |
| 4.5–6.4, or any Blocker | **Significant gaps — revise before build** |
| < 4.5 | **Not ready — major rework** |

Findings carry a severity — `Blocker` · `Major` · `Minor` · `Nit` — and a stable `FND-###` ID so they're easy to reference and track across re-reviews.

---

## Setup

Installation and workspace setup are the same across all Delivery OS plugins, so they live in one shared guide: **[docs/SETUP.md](../../docs/SETUP.md)**. The short version for `tl`:

1. **Install** the core, then the TL plugin (see [docs/SETUP.md → Step 1–2](../../docs/SETUP.md#step-1--add-the-marketplace-and-install-the-core)):
   ```text
   /plugin marketplace add techjays/claude-delivery-os
   /plugin install delivery-os@techjays-delivery-os
   /plugin install tl@techjays-delivery-os
   ```
2. **A workspace is optional for `tl`.** Unlike `/ba:scope`, the TL agent can review any document standalone — you don't have to run `/delivery-os:init` first.

### Do I need `/delivery-os:init`?

`/delivery-os:init <project-name>` scaffolds the standard Delivery OS workspace (see [docs/SETUP.md → Step 3](../../docs/SETUP.md#step-3--initialize-a-project-workspace-delivery-osinit)). For the TL agent it's **optional**, and it only changes two things:

| | With a workspace (`init` was run) | Standalone (no workspace) |
|---|---|---|
| **Report location** | `tl-output/spec-review-<timestamp>.{html,md}` (the agent creates `tl-output/` on first run) | written **beside the reviewed document**, with a note that no workspace was found |
| **Input context** | also reads `ba-output/scope.md` and `shared-context/` if present, to ground the review | reviews only the document you point it at |

So: run `/delivery-os:init` if you want the review filed inside a project workspace and cross-referenced with BA discovery; skip it for a quick one-off review of any spec.

---

## Usage

```text
/tl:review <path-or-link-to-spec> [out=<output-prefix>]
```

- **`<doc>`** — required. A path or link to the spec to review.
- **`out=<prefix>`** — optional. Overrides where the report is written. A run timestamp is **always** appended, so repeated reviews never overwrite each other.

Where the report lands:
- Inside a Delivery OS workspace → `tl-output/spec-review-<timestamp>.{html,md}`
- No workspace → written **beside the reviewed document**, with a note that no workspace was found.

Each run is timestamped (`spec-review-2026-06-25-162658.html`), so `tl-output/` accumulates a full review history — re-review after the spec is revised and compare.

---

## Worked example

You've been handed a draft spec for **SupportCopilot** — an AI assistant that drafts customer-support replies (RAG over help-center articles + past tickets, GPT-4o for generation, embedded in Zendesk). You want to know if it's ready to build.

```text
/tl:review docs/support-copilot-spec.md
```

The agent reads the doc, detects an **AI + multi-system** profile (so all 13 areas apply), scores each, and writes the report. The headline it returns:

> **Overall score: 2.0/10 — Not ready — major rework.**
> Sensibly-shaped RAG architecture, but as a build document it's a high-level sketch missing the applied-AI engineering a production LLM feature needs. Four Blockers gate it.

The scorecard:

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
| | **Overall** | **2.0/10** | **Not ready — major rework** |

The four **Blockers** it surfaces are the ones that actually hurt in production — the kind a checklist pass misses:

| ID | Sev. | Area | Finding | Fix |
|----|------|------|---------|-----|
| FND-018 | Blocker | CMP | Customer PII sent to OpenAI with no review of data-use terms or redaction | Confirm zero-retention terms; redact PII pre-call; document legal basis |
| FND-010 | Blocker | API | No request/response schemas, auth, or error codes — endpoints can't be coded against | Define full contracts with examples, auth, status-coded errors |
| FND-013 | Blocker | OBS | No logging of prompts/tokens/cost — a bad draft can't be debugged, cost can't be tracked | Add per-call structured logging with request correlation |
| FND-009 | Blocker | DAT | Ticket data (PII) stored/embedded with no classification or retention policy | Classify PII, define retention, restrict access |

Plus the clarifying questions worth asking before assuming the worst — e.g. *"Is there a companion OpenAPI spec that just isn't referenced here?"* and *"Is the OpenAI account on a zero-retention tier?"* — because those answers move scores.

A populated sample report ships in this repo: [`examples/tl-review-test/`](../../examples/tl-review-test/) — open the `spec-review-*.html` in a browser to see the interactive version.

---

## Reading the interactive HTML report

`spec-review-<timestamp>.html` is fully self-contained — **no internet, no dependencies** — just open it in any browser. It gives you:

- **Sticky header** with the color-coded overall score and verdict badge, always visible as you scroll.
- **Scorecard** with colored score bars, grouped by area group. **Click any row** to jump to and expand that area's detail.
- **Expand/collapse area sections** — weak areas auto-open so problems surface first; "Expand all / Collapse all" buttons.
- **Live severity filter** on the findings register — click `Blocker (4)` / `Major (10)` / … to filter the table instantly.
- **Clickable area↔finding links** — finding chips inside an area jump to and flash-highlight the row in the register.
- **Dark mode** (follows your OS) and a **print-friendly** layout.

The Markdown twin (`spec-review-<timestamp>.md`) is the same content as a clean Delivery OS document — frontmatter, stable IDs, greppable and diff-friendly. A `spec-review-<timestamp>.json` sidecar holds the structured data the resolution loop reads. All three are rendered from one data object, so they never disagree.

---

## Closing findings — the resolution loop (`/tl:resolve`)

A review *raises* findings; the loop *closes* them. Each finding is an open item the author answers, the agent judges whether the answer actually resolves the concern (or pushes back), and closed items are recorded as decisions — so the review converges from "here are the gaps" to "here's what was decided and why," with an audit trail.

**The flow:**

1. **Respond in the report.** Open `spec-review-<timestamp>.html`, scroll to **Open items**, and under each finding type your response and pick an intent (`resolve` / `accept-risk` / `need-info` / `wont-fix`).
2. **Export.** Click **Export responses**. The page downloads `spec-review-<timestamp>-responses.md` — named with the **same timestamp** as the review, which is the key that ties responses back to it. (Browsers can't write to disk, so it lands in your Downloads — move it into `tl-output/`.)
3. **Resolve.** Run `/tl:resolve tl-output/spec-review-<timestamp>-responses.md`. The agent matches the timestamp to the review's `.json`, then **adjudicates each response**:
   - **Resolved** — the answer addresses the concern with verifiable specifics; it records the rationale and, where relevant, the exact spec edit to bake the answer into the document.
   - **Accepted-risk** — you explicitly accept a valid, unfixed concern; the residual risk is noted.
   - **Needs-verification** — plausible but thin; it asks 1–3 targeted follow-up questions and keeps the item open.
   - **Won't-fix / still Open** — declined or unaddressed, with a note on why.
4. **New round.** It writes a fresh timestamped report (`round` 2, `priorReview` linking back) where findings carry forward by their stable `FND-###` IDs with updated **Status** badges, the resolution thread, and a **recomputed score and verdict** — a resolved Blocker lifts the readiness cap. Closed items are also appended as `DEC-###` rows to `shared-context/decision-log.md` (in a workspace), so the decisions persist for the rest of Delivery OS.
5. **Repeat** until no open items remain — answer any follow-ups in the new report and export again.

**Worked example (continuing SupportCopilot):** you respond to FND-018 with *"Azure AI Foundry, West Europe, enterprise DPA, modified abuse monitoring approved (zero retention), legal basis = contract"* and export. `/tl:resolve` judges that this answers the data-use/residency/retention concern with specifics → marks **FND-018 Resolved**, suggests the §10 spec edit, logs **DEC-007**, and — with that Blocker cleared — lifts the verdict from *Not ready* toward *Build with caveats*. A vaguer *"we'll secure it"* would instead come back as **Needs-verification** with pointed questions.

> Why a separate step rather than editing the report in place? The timestamped rounds keep the **full history** — you can see what was open at review time, what the author said, and how each item was closed.

---

## How it fits Delivery OS

The TL agent is a **consumer** in the Delivery OS contract: when a workspace exists it reads `ba-output/scope.md` and `shared-context/` as input context, and writes its review to `tl-output/` with standard frontmatter (`doc_type: spec-review`, `produced_by: tl`). It **reviews** specs — it doesn't author or rewrite them, and it doesn't run BA discovery. Where it suspects work was done but not written down, it raises a clarifying question rather than asserting a Blocker.

See the shared [`delivery-os-conventions`](../delivery-os-core/skills/delivery-os-conventions/SKILL.md) skill for the full document contract.

---

## FAQ

**Does it work on a `.docx` or `.pdf` spec?** Yes — the agent extracts the content first (via the `docx`/`pdf` skills), then reviews it.

**Can I review the same spec twice?** Yes — that's the point of timestamped filenames. Re-review after revising the spec; the old report stays put so you can compare.

**It scored my non-AI service's "Evals" as N/A — is that right?** Yes. When no LLM is involved, the four Applied-AI areas are marked N/A and excluded from the average. The report says why.

**Why did one Blocker drag down an otherwise-good score?** By design. A single must-fix issue (e.g. PII to a third-party model under training terms) means a team can't safely start building, so the verdict is capped regardless of the average. The executive summary names which Blocker drove the cap — and resolving it via `/tl:resolve` lifts the cap.

**Do I have to use the HTML to respond?** No — the responses file is plain Markdown. The HTML's *Export responses* just generates it for you with the right name and finding headers. You can also hand-write or edit `spec-review-<timestamp>-responses.md` and run `/tl:resolve` on it.

**The agent marked my response "Needs-verification" — why?** It judged the answer plausible but missing specifics it can verify (a region, a config state, an approval status, a number). Answer its follow-up questions in the new report and export again; vague assurances are deliberately not enough to close a finding.
