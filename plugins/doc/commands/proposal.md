---
description: Generate a Techjays client proposal as a polished .pptx deck in the Techjays house style (editorial, mostly-white, a tight core deck plus a detailed appendix). Pass the client name; the doc agent auto-drafts content from the BA scope when a Delivery OS workspace exists, co-brands the deck with the client's logo, and writes a timestamped deck-<client>-<timestamp>.pptx to doc-output/. Add free-text custom rules to tailor it.
argument-hint: "client=\"<Client Name>\" [title=\"<engagement title>\"] [logo=<path-to-client-logo>] [\"<extra requirements / custom rules>\"]"
---

# /doc:proposal

You are the entry point for generating a **Techjays client proposal** as a slide deck. Parse the arguments and **delegate the actual work to the `doc-agent` subagent**, which runs in its own context and does the content sourcing and deck build.

## 1. Parse arguments

`$ARGUMENTS` may contain, in any order:
- **`client="<Client Name>"`** — the client's name (required). If omitted, ask for it and stop.
- **`title="<engagement title>"`** — the engagement's value-prop headline for the cover. Optional; the agent can draft one from the scope.
- **`logo=<path>`** — path to the client's logo file for co-branding the cover (this environment can't download logos from the web). Optional; without it the cover uses the Techjays mark alone. A prior client PDF/deck also works — the agent can extract the logo from it.
- **`out=<prefix>`** — optional output prefix override (default `doc-output/deck-<client>`). A run timestamp is always appended.
- **Free-text custom rules** — anything else in quotes or trailing prose is treated as **additional requirements**: extra sections, tone, specific pricing, "use the lean core form", "add a security & compliance appendix slide", "emphasize the migration story", brand-color overrides, etc. Pass these through verbatim; the agent layers them on top of the standard.

If a Delivery OS workspace exists (`ba-output/scope.md` present), tell the agent to auto-draft from it. If not, the agent uses what's provided/attached and marks any missing client numbers as placeholders.

## 2. Delegate

Invoke the **doc-agent** subagent with the parsed inputs. Pass it this instruction:

> Generate a Techjays client proposal deck using the `doc-deck` skill. Client: `<client>`; engagement title: `<title or "draft from scope">`; client logo: `<logo path or "none">`. Custom rules (verbatim, or "none"): `<custom rules>`.
>
> Build a polished **.pptx** in the Techjays house style by copying `scripts/build_deck.js` + the `assets/*.png` into the working dir and editing CONFIG and the `► CONTENT` blocks, following `references/design-system.md` (the governing visual spec) and leaning on the `pptx` skill for pptxgenjs gotchas, validation, and rendering. Structure it as a tight **core deck** (cover → executive summary + KPI row → solution summary → timeline high-level → investment → closing) plus an **appendix** holding all the detail (full module scope, "what the client gets", and a week-by-week Gantt). When a Delivery OS workspace exists, auto-draft the problem statement, solution workflow, and value numbers from `ba-output/scope.md` and `shared-context/` (use the client's real numbers; never fabricate metrics — mark unknowns as `[[NEEDS: …]]` placeholders). Co-brand the cover with the client's logo when supplied (dark/brand-coloured crop, background dropped to transparent). Enforce the non-negotiable voice rules (no em-dashes, no contrastive negation, address the client by name, client's real numbers on the executive-summary and investment slides) and the house-style discipline (mostly-white core slides, dark slides only as separators, no accent stripes/underlines, no detail crammed onto core slides). Layer the custom rules on top of the standard; flag any that would break a non-negotiable rule instead of silently applying it. Build, run `validate.py` (must pass), render to PDF and view every slide for overflow/collisions/off-canvas shapes, fix in the generator and re-render. Read a run timestamp (`YYYY-MM-DD-HHMMSS`) and write `doc-output/deck-<client>-<timestamp>.pptx` (create `doc-output/` if absent). Return a short summary, the list of any placeholders still needing the user's numbers, and the file link.

## 3. Surface the result

When the agent returns, present its **summary**: what was built, which content came from the BA scope vs. supplied, and any placeholders the user still needs to fill (missing client metrics, the official logo asset, final pricing). Link to the generated `deck-<client>-<timestamp>.pptx`. Keep it tight.
