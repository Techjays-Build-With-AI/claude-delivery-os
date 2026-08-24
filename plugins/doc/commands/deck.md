---
description: Turn any content into a polished Techjays-house-style .pptx deck — a proposal, pitch, engagement plan, report, or status update. Point it at a source (a brief, notes, a doc/PDF, a prior deck) or describe the content; the doc agent builds a tight core deck plus a detailed appendix, co-brands with a client logo when supplied, and writes a timestamped deck-<name>-<timestamp>.pptx to doc/.
argument-hint: "title=\"<deck title>\" [client=\"<Client Name>\"] [kind=proposal|report|update] [logo=<path>] [source=<path/url>] [\"<extra requirements / custom rules>\"]"
---

# /doc:deck

You are the entry point for generating a **Techjays house-style deck** for any content — not only proposals. Parse the arguments and **delegate the actual work to the `doc-agent` subagent**, which runs in its own context and does the content sourcing and deck build. (`/doc:proposal` is the proposal-shaped variant of this command; use it when the deck is specifically a client proposal.)

## 1. Parse arguments

`$ARGUMENTS` may contain, in any order:
- **`title="<deck title>"`** — the deck's headline (required, or clearly inferable from the source). If neither is present, ask and stop.
- **`client="<Client Name>"`** — the client or audience, used in the footer lockup and body copy. Optional.
- **`kind=<proposal|report|update>`** — shapes the core/appendix split (default `proposal`). For a **report**: core = findings/recommendations, appendix = methodology + data tables. For an **update**: core = status + decisions, appendix = per-workstream detail.
- **`logo=<path>`** — path to a client/audience logo file for co-branding (this environment can't download logos from the web). Optional.
- **`source=<path or url>`** — the content to turn into a deck (a brief, notes, a doc/PDF, a prior deck, or a URL). The agent reads it and pulls out the headline offer, the key numbers, the sections, and the detail. Optional if the content is described inline or drawn from the BA scope.
- **`out=<prefix>`** — optional output prefix override (default `doc/decks/deck-<title-or-client>`). A run timestamp is always appended.
- **Free-text custom rules** — extra sections, tone, specific numbers, "lean core", brand-color overrides, etc. Passed through verbatim; the agent layers them on top of the house style.

If a Delivery OS workspace exists (`ba/scope.md` present), tell the agent it may auto-draft from it. If not, the agent uses the source/what's provided and marks any missing numbers as placeholders.

## 2. Delegate

Invoke the **doc-agent** subagent with the parsed inputs. Pass it this instruction:

> Generate a Techjays house-style deck using the `doc-deck` skill. Title: `<title>`; client/audience: `<client or "none">`; kind: `<kind>`; client logo: `<logo path or "none">`; source: `<source or "inline / BA scope">`. Custom rules (verbatim, or "none"): `<custom rules>`.
>
> Read the source first and pull out the substance (headline, 2–4 key numbers, sections, and the fine-grained detail). Build a polished **.pptx** by copying `scripts/build_deck.js` + the `assets/*.png` into the working dir and editing CONFIG and the `► CONTENT` blocks, following `references/design-system.md` and leaning on the `pptx` skill for validation and rendering. Structure it as a tight **core deck** (single idea per slide) plus an **appendix** holding all the detail, with the core/appendix split matched to `kind`. Co-brand the cover with the client logo when supplied. When a Delivery OS workspace exists, you may auto-draft from `ba/scope.md` and `shared-context/` — use real numbers, never fabricate, mark unknowns as `[[NEEDS: …]]`. Enforce the non-negotiable voice rules (no em-dashes, no contrastive negation, address the client/audience by name where relevant, real numbers only) and the house-style discipline (mostly-white core slides, dark slides only as separators, no accent stripes/underlines, timelines as an appendix Gantt, no detail crammed onto core slides). Build, run `validate.py` (must pass), render to PDF and view every slide for overflow/collisions/off-canvas shapes, fix in the generator and re-render. Read a run timestamp (`YYYY-MM-DD-HHMMSS`) and write `doc/decks/deck-<name>-<timestamp>.pptx` (create `doc/` if absent). Return a short summary, any `[[NEEDS: …]]` placeholders, and the file link.

## 3. Surface the result

When the agent returns, present its **summary**: what was built, which content came from the source/BA scope vs. supplied, and any placeholders the user still needs to fill. Link to the generated `deck-<name>-<timestamp>.pptx`. Keep it tight.
