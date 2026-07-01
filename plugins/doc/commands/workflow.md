---
description: Generate an interactive workflow document — a phased SVG swimlane flow of the project's scope with hover-over tooltips, a per-phase before/after value panel (current pain → AI solution + hours saved), KPI cards, and a systems retained/retired grid, all in one self-contained HTML file. The doc agent drafts phases/actors/values from the BA scope when a workspace exists and writes a timestamped file to doc-output/.
argument-hint: "project=\"<Project Name>\" [client=\"<Client>\"] [\"<source material / custom rules>\"]"
---

# /doc:workflow

You are the entry point for generating a **workflow document**: an interactive, phased swimlane walkthrough of a project's scope. Parse the arguments and **delegate the build to the `doc-agent` subagent**, which runs in its own context.

## 1. Parse arguments

`$ARGUMENTS` may contain, in any order:
- **`project="<Project Name>"`** — e.g. "Acme Corp — Employee Onboarding". If omitted, infer from the workspace/scope or ask.
- **`client="<Client>"`** — the client/org name shown in the header overline. Optional; inferred from `shared-context/project-profile.md` when present.
- **`out=<prefix>`** — optional output-prefix override (default follows the skill's `[CLIENT]-[TOPIC]-[DDMonYYYY]` naming in `doc-output/`).
- **Free-text** — any extra source material, emphasis, or custom rules (which phases/actors to feature, the KPI numbers, systems retained/retired, brand/accent overrides). Passed through verbatim.

If a Delivery OS workspace exists, tell the agent to draft from `ba-output/scope.md`, `ba-output/workflow-register.md`, and `shared-context/`.

## 2. Delegate

Invoke the **doc-agent** subagent. Pass it this instruction:

> Create a **workflow document** using the `doc-workflow` skill. Project: `<project>`; client: `<client or "infer">`. Custom rules / source (verbatim, or "none"): `<free text>`.
>
> Read the skill and its reference files (`design-tokens`, `page-structure`, `components`, `svg-swimlane`, `javascript`) in order, then build **one self-contained, offline-portable HTML file**: dark-navy header + gold accent, fixed left sidebar nav, a **vertical** phased SVG swimlane (phases as top-to-bottom band rows, actors as left-to-right columns) with hover tooltips (`data-title`/`data-desc` with `||` separators), a per-phase right-column **value panel** (current pain → AI solution → hours saved) showing before/after and the efficiency gain, KPI metric cards (gold numbers, hover tooltips), and a systems retained/retired grid. When a Delivery OS workspace exists, draft the phases from the scope modules / `workflow-register` (actors → swimlane columns, Current→Future → value panel, stated numbers → KPIs); use real numbers and never fabricate — mark unknowns `[[NEEDS: …]]`. Follow the skill's Quality checklist (vertical swimlane, light node fills with coloured borders, horizontal/vertical-only arrows with `marker-end` on the final segment only, `body{padding-left:180px}`, tooltip divs first in `<body>`, no external dependencies) and the voice rules (no em-dashes, no contrastive negation, address the client by name). Write to `doc-output/[CLIENT]-[TOPIC]-[DDMonYYYY].html` (create `doc-output/` if absent). Then QA in a browser (scroll-spy works, every node tooltip fires, no clipped SVG, arrows land on node edges) and return a short summary, any `[[NEEDS: …]]` placeholders, and the file link.

## 3. Surface the result

When the agent returns, present its **summary**: the phases and actors covered, the headline KPIs and efficiency gain, which content came from the BA scope vs. supplied, and any placeholders still needing the user's numbers. Link to the generated HTML and tell the user to open it in a browser (sidebar nav jumps to phases; hover swimlane nodes and KPI cards for detail). Keep it tight.
