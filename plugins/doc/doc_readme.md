# Doc Agent — Standardized Client Documents

The **Documentation Agent** exists to unify how the org produces client-facing artifacts — decks, workflow documents, walkthrough boards — so every document looks and reads like it came from one company, built to the Techjays standard and style system. It ships four capabilities today: the **client deck**, the **magic board**, the **workflow document**, and the **spec walkthrough**.

| | |
|---|---|
| **Namespace** | `/doc:` |
| **Commands** | `/doc:proposal client="<Name>"` · `/doc:deck title="<…>"` · `/doc:magic-board topic="<…>"` · `/doc:workflow project="<…>"` |
| **Output** | `doc/decks/deck-…pptx` · `doc/boards/board-…html` · `doc/[CLIENT]-[TOPIC]-[date].html` |
| **Skills** | `doc-deck` (design system + pptxgenjs generator + brand assets) · `doc-magic-board` (board engine) · `doc-workflow` (swimlane spec + references) · `doc-spec-walkthrough` |

---

## What `/doc:proposal` and `/doc:deck` do

They generate a polished **.pptx deck in the Techjays house style** — editorial and confident: mostly-white content pages, oversized bold headlines, uppercase letter-spaced micro-labels (one typeface throughout), generous whitespace, one dominant brand colour plus two restrained supporting accents, a faint corner watermark, a confidential footer on every page, and **dark slides used as section separators**. The structural idea is a tight **core deck** (executive level, ~6 slides) followed by an **appendix** that holds all the detail — an exec can read the core and skip the rest. It's built to `references/design-system.md` (the governing visual spec) via `scripts/build_deck.js` (a working pptxgenjs generator), both bundled in the `doc-deck` skill, and validated/rendered with the `pptx` skill's tooling.

- **`/doc:proposal`** is the proposal-shaped entry point (cover → executive summary → solution → timeline → investment → closing, plus appendix). **`/doc:deck`** is the general entry point for any deck — a proposal, report, or status update — and shapes the core/appendix split to `kind`.
- **Co-branded to the client.** Supply a client logo file and it goes onto the cover lockup beside the Techjays mark. This environment can't download logos from the web, so the agent takes the logo from a file you provide or extracts it from a prior client PDF/deck (crop tight, drop the background to transparent, use a dark/brand-coloured version so it doesn't vanish on white pages).
- **Auto-drafted from the BA scope.** When a Delivery OS workspace exists, it drafts the problem statement, solution workflow, and value numbers from `ba/scope.md` and `shared-context/` — using the client's *real* numbers. It never fabricates a metric; unknowns become clearly marked `[[NEEDS: …]]` placeholders listed back to you.
- **Core / appendix discipline.** Core slides carry a single idea each; the moment one fills with bullets, the detail moves to an appendix slide with a one-line summary left behind. Timelines show as a proper **Gantt** in the appendix.
- **Custom rules.** Anything extra you pass in quotes is layered on top: "add a security & compliance appendix slide", "use the lean core form", "emphasize the migration story", brand-color overrides, specific pricing. A custom rule that would break a non-negotiable voice or house-style rule is flagged rather than silently applied.

### Non-negotiable voice rules

No em-dashes; no contrastive negation ("not X but Y"); address the client by name (not "your operating reality"); the executive-summary and investment slides carry the client's real numbers; short, decisive headlines with colour used for meaning, not decoration. The agent scans its own draft and fixes violations before delivering.

---

## Usage

```text
# minimal — drafts from the scope if present, Techjays-branded cover
/doc:proposal client="Harry Grodsky & Co."

# with an engagement title, a client logo, and custom rules
/doc:proposal client="Acme" title="AI-Powered Estimating" logo=./acme-logo.png "lean core; add a data-security appendix slide; pricing fixed at $225k"

# a non-proposal deck (report / update) from a source
/doc:deck title="Q3 Delivery Review" client="Acme" kind=report source=./q3-notes.md
```

- **`client="…"`** — required for `/doc:proposal`. **`title="…"`** — the cover headline (drafted from the scope if omitted).
- **`logo=…`** — path to a client logo file for co-branding (optional; no web download).
- **`kind=…`** (`/doc:deck`) — `proposal` (default), `report`, or `update`; shapes the core/appendix split.
- **Free text** — treated as custom rules, layered on the house style.
- **`out=<prefix>`** — optional output-prefix override; a timestamp is always appended.

Output lands in `doc/` as a `.pptx`. Open it in PowerPoint or import to Google Slides. The deck uses one typeface (`CFG.font`, **Google Sans** by default); Google Sans is proprietary and not in the Google Slides picker, so for guaranteed-identical rendering set `CFG.font` to **Poppins** or **Arial** (see `design-system.md` §3).

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
- The agent finds the narrative spine, clusters cards into 3–6 left-to-right "parts", designs each card to its content (diagrams, two-column step cards, a wow card, a closer), places them without overlap, and wires the tour. When a workspace exists it drafts from `ba/scope.md`, `ba/registers/workflows.md`, and `shared-context/`.
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
- The exact swimlane spec (vertical orientation, light node fills with coloured borders, horizontal/vertical-only arrows, tooltip data attributes, value-panel coordinates) lives in the skill's `references/`. Output follows the `[CLIENT]-[TOPIC]-[DDMonYYYY].html` naming in `doc/`.
- **Viewing:** open the HTML; the sidebar jumps to each phase, and hovering a swimlane node or KPI card reveals its detail.

## How it fits Delivery OS

The Doc agent is a **consumer**: it reads `ba/scope.md` and `shared-context/` (produced by `/ba:scope`) and writes to `doc/`. So the pipeline is `/ba:scope` (build the scope) → `/ba:review` (harden it) → `/doc:proposal` (turn it into a client-ready deck). It works standalone too — without a workspace it uses what you pass and marks missing client numbers as placeholders.

See the bundled `skills/doc-deck/references/design-system.md` for the full visual spec, the `pptx` skill for build/validation tooling, and the shared [`delivery-os-conventions`](../delivery-os-core/skills/delivery-os-conventions/SKILL.md) contract.

---

## FAQ

**What format is the deck?** A `.pptx`. Open it in PowerPoint or import it into Google Slides. The whole deck uses a single typeface (`CFG.font`, **Google Sans** by default). Google Sans is a proprietary Google font — it renders only where installed and isn't in the Google Slides font picker, so if the deck needs to look identical everywhere, set `CFG.font` to **Poppins** (a close, freely available match) or **Arial** (universal). Confirm the target with whoever's presenting.

**Can I co-brand with the client's logo?** Yes — pass `logo=<path>` to a logo file, or point the agent at a prior client PDF/deck and it extracts the mark. This environment can't download logos from the web, so a file is required. Use a dark/brand-coloured crop so the mark doesn't vanish on white pages.

**Can I edit the deck afterward?** Yes — it's a normal PowerPoint file. You can also re-run the generator: the `► CONTENT` blocks in `build_deck.js` hold all the words and data arrays.

**It left `[[NEEDS: …]]` placeholders.** Those are client numbers or facts the agent wouldn't invent (pricing, real metrics, the official logo). Fill them in before sending; the agent lists every one in its summary.

**Roadmap.** Executive summary, SRS, and SoW documents are next under `/doc:`, on the same standard + style system.
