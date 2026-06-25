# TL Agent — Technical Specification Review

The **Technical Lead Agent** reviews a technical specification for an applied AI system the way a seasoned TL would before a team commits engineering time and budget to building from it. It reads the whole document, scores it across the dimensions that decide build-readiness, and hands back a **scored, actionable review** — an interactive HTML report plus a Markdown artifact.

| | |
|---|---|
| **Namespace** | `/tl:` |
| **Command** | `/tl:review <doc> [out=<prefix>]` |
| **Input** | A tech spec / architecture / system-design / HLD / SRS document (`.md`, `.docx`, or `.pdf`) |
| **Output** | `tl-output/spec-review-<timestamp>.html` (interactive) + `…​.md` (artifact) |
| **Skill** | `tl-spec-review` |

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
2. **A workspace is optional for `tl`.** Unlike `/ba:intake`, the TL agent can review any document standalone — you don't have to run `/delivery-os:init` first.

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

The Markdown twin (`spec-review-<timestamp>.md`) is the same content as a clean Delivery OS document — frontmatter, stable IDs, greppable and diff-friendly. Both are rendered from one structured data object, so they never disagree.

---

## How it fits Delivery OS

The TL agent is a **consumer** in the Delivery OS contract: when a workspace exists it reads `ba-output/scope.md` and `shared-context/` as input context, and writes its review to `tl-output/` with standard frontmatter (`doc_type: spec-review`, `produced_by: tl`). It **reviews** specs — it doesn't author or rewrite them, and it doesn't run BA discovery. Where it suspects work was done but not written down, it raises a clarifying question rather than asserting a Blocker.

See the shared [`delivery-os-conventions`](../delivery-os-core/skills/delivery-os-conventions/SKILL.md) skill for the full document contract.

---

## FAQ

**Does it work on a `.docx` or `.pdf` spec?** Yes — the agent extracts the content first (via the `docx`/`pdf` skills), then reviews it.

**Can I review the same spec twice?** Yes — that's the point of timestamped filenames. Re-review after revising the spec; the old report stays put so you can compare.

**It scored my non-AI service's "Evals" as N/A — is that right?** Yes. When no LLM is involved, the four Applied-AI areas are marked N/A and excluded from the average. The report says why.

**Why did one Blocker drag down an otherwise-good score?** By design. A single must-fix issue (e.g. PII to a third-party model under training terms) means a team can't safely start building, so the verdict is capped regardless of the average. The executive summary names which Blocker drove the cap.
