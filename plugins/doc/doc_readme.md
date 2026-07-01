# Doc Agent — Standardized Client Documents

The **Documentation Agent** exists to unify how the org produces client-facing artifacts — proposals, workflow documents, walkthrough boards — so every document looks and reads like it came from one company, built to the Techjays standard and style system. It ships three capabilities today: the **client proposal**, the **magic board**, and the **workflow document**.

| | |
|---|---|
| **Namespace** | `/doc:` |
| **Commands** | `/doc:proposal client="<Name>" domain=<client.com>` · `/doc:magic-board topic="<…>"` · `/doc:workflow project="<…>"` |
| **Output** | `doc-output/proposal-…html` · `doc-output/board-…html` · `doc-output/[CLIENT]-[TOPIC]-[date].html` — self-contained HTML |
| **Skills** | `doc-proposal` (standard + style guide + template) · `doc-magic-board` (board engine) · `doc-workflow` (swimlane spec + references) |

---

## What `/doc:proposal` does

It generates a **single-file HTML proposal deck** — no external CSS/JS/fonts, opens offline, and exports to a clean PDF — built to `proposal-standard.md` (the governing content flow and voice rules) and `proposal-style-guide.md` (the design system), both bundled in the skill.

- **Branded to the client from their domain.** Give it the client's name and domain; it pulls their logo (`https://logo.clearbit.com/<domain>`, with favicon and text-wordmark fallbacks) onto the title brand pair and closing signoff, and samples their brand color into the deck's accent. For a truly offline file, it base64-embeds the logo.
- **Auto-drafted from the BA scope.** When a Delivery OS workspace exists, it drafts the problem statement, solution workflow, and value numbers from `ba-output/scope.md` and `shared-context/` — using the client's *real* numbers. It never fabricates a metric; unknowns become clearly marked `[[NEEDS: …]]` placeholders listed back to you.
- **The standard's flow.** Title deck → Problem → Solution (workflow) → Value gain → Timeline & budget (with the zero-risk callout) → Partnership → Closing, plus an optional Appendix.
- **PDF as a first-class deliverable.** Every responsive breakpoint is scoped to `@media screen`, the `@page`/print rules invert dark slides to white and preserve accent colors, cards avoid page breaks, and a floating **Print / Save PDF** button is always there. Open in Chrome/Edge → Print → Save as PDF (enable "Background graphics").
- **Custom rules.** Anything extra you pass in quotes is layered on top: "add a security & compliance section", "use the lean 7-section form", "emphasize the migration story", brand-color overrides, specific pricing. A custom rule that would break a non-negotiable voice/brand rule is flagged rather than silently applied.

### Non-negotiable voice rules

No em-dashes; no contrastive negation ("not X but Y"); address the client by name (not "your operating reality"); the Value page carries the client's real numbers; single file with system fonts only. The agent scans its own draft and fixes violations before delivering.

---

## Usage

```text
# minimal — pulls logo + accent from the domain, drafts from the scope if present
/doc:proposal client="Harry Grodsky & Co." domain=grodsky.com

# with an engagement title and custom rules
/doc:proposal client="Acme" domain=acme.com title="AI-Powered Estimating" "lean 7-section form; add a data-security section; pricing fixed at $50k Phase 1"
```

- **`client="…"`** — required. **`domain=…`** — strongly recommended (drives logo + accent).
- **`title="…"`** — optional; drafted from the scope if omitted.
- **Free text** — treated as custom rules, layered on the standard.
- **`out=<prefix>`** — optional output-prefix override; a timestamp is always appended.

Output lands in `doc-output/`. Open the `.html` in a browser and **Print → Save as PDF**.

---

## Magic board — `/doc:magic-board`

A **magic board** is a self-contained, Miro-style **infinite-canvas HTML** file: cards laid out in space, with pan (drag), zoom (scroll toward cursor), and a **guided fly-through tour** that frames each card full-screen as you click next / next / next. It is the best way to *show* a workflow or "our understanding" of a system to a client or team — spatial overview plus a narrated walkthrough in one file.

```text
# a workflow board, drafted from the BA scope when a workspace exists
/doc:magic-board topic="Acme invoice-processing workflow" kind=workflow

# a system deep-dive, with custom emphasis
/doc:magic-board topic="Our understanding of the claims system" kind=system "feature the fraud-check subsystem; keep it to ~10 cards"
```

- **`topic="…"`** — what the board is about. **`kind=…`** — the arc: `workflow` (default), `journey`, `system`, `concept`, `strategy`, or `roadmap`.
- The agent finds the narrative spine, clusters cards into 3–6 left-to-right "parts", designs each card to its content (diagrams, two-column step cards, a wow card, a closer), places them without overlap, and wires the tour. When a workspace exists it drafts from `ba-output/scope.md`, `workflow-register.md`, and `shared-context/`.
- **Presenting:** open the `.html`, use the on-screen next/prev or arrow keys to walk the tour, drag to pan, scroll to zoom, press `O` for the overview.
- The pan/zoom/tour **engine** (`assets/board-engine.js`) is the one fixed piece; everything visual is designed per the skill's house style (warm editorial, five cluster accents, honesty chips), which you can reskin to the client's brand.

## Workflow document — `/doc:workflow`

An **interactive workflow document** that walks a client through the scope of a project as a phased flow: a Techjays-standard single-file HTML page with a dark-navy header, gold accent, fixed left sidebar nav, and — at its center — a **vertical SVG swimlane** (phases as top-to-bottom band rows, actors as left-to-right columns) with **hover-over tooltips** on every step. Each phase has a right-column **value panel** showing the before/after state (current pain → AI solution) and the **efficiency gain** (hours saved), plus **KPI cards** and a **systems retained/retired** grid.

```text
# drafts phases/actors/values from the BA scope + workflow-register when present
/doc:workflow project="Acme Corp — Employee Onboarding"

# with source material / emphasis
/doc:workflow project="Claims Intake" client="Acme" "3 phases; actors: Agent, AI Platform, Adjuster; feature the fraud-check exception path"
```

- **`project="…"`** — required (or inferred from the scope). **`client="…"`** — the header overline; inferred from `shared-context/` when present.
- When a Delivery OS workspace exists, it maps each **scope module / workflow** to a phase, its **actors** to swimlane columns, its **Current→Future state** to the before/after value panel, and its **stated numbers** to the KPIs and hours-saved. It never invents metrics — unknowns become `[[NEEDS: …]]`.
- The exact swimlane spec (vertical orientation, light node fills with coloured borders, horizontal/vertical-only arrows, tooltip data attributes, value-panel coordinates) lives in the skill's `references/`. Output follows the `[CLIENT]-[TOPIC]-[DDMonYYYY].html` naming in `doc-output/`.
- **Viewing:** open the HTML; the sidebar jumps to each phase, and hovering a swimlane node or KPI card reveals its detail.

## How it fits Delivery OS

The Doc agent is a **consumer**: it reads `ba-output/scope.md` and `shared-context/` (produced by `/ba:scope`) and writes to `doc-output/`. So the pipeline is `/ba:scope` (build the scope) → `/ba:review` (harden it) → `/doc:proposal` (turn it into a client-ready deck). It works standalone too — without a workspace it uses what you pass and marks missing client numbers as placeholders.

See the bundled `skills/doc-proposal/references/` for the full standard and style guide, and the shared [`delivery-os-conventions`](../delivery-os-core/skills/delivery-os-conventions/SKILL.md) contract.

---

## FAQ

**Does the logo work in the PDF?** Yes, if you're online when you Save-as-PDF (it loads the logo by domain). For an offline-portable file to archive or email, ask the agent to base64-embed the logo.

**What if Clearbit has no logo for the domain?** It falls back to the site favicon, then to a text wordmark in the client's accent color — replace it with the official asset before sending.

**Can I edit the deck afterward?** Yes — it's a single HTML file. Open it in any editor; the tokens and structure are documented in an HTML comment at the top.

**It left `[[NEEDS: …]]` placeholders.** Those are client numbers or facts the agent wouldn't invent (pricing, real metrics, the official logo). Fill them in before sending; the agent lists every one in its summary.

**Roadmap.** Executive summary, SRS, and SoW documents are next under `/doc:`, on the same standard + style system.
