---
description: Create a "magic board" — a self-contained, Miro-style infinite-canvas HTML board with a guided next/next fly-through tour, great for showing a workflow or your understanding of a system to a client or team. Pass a topic and any source material; the doc agent drafts the spine from the BA scope when a workspace exists, designs the cards, wires the tour, and writes a timestamped board-<topic>-<timestamp>.html to doc-output/.
argument-hint: "topic=\"<what the board is about>\" [kind=workflow|journey|system|concept|strategy|roadmap] [\"<extra source material / custom rules>\"]"
---

# /doc:magic-board

You are the entry point for creating a **magic board** — a spatial, pannable/zoomable HTML canvas with a guided fly-through tour (click next / next / next, each stop framed full-screen), like a Miro board you can present from. Parse the arguments and **delegate the build to the `doc-agent` subagent**, which runs in its own context.

## 1. Parse arguments

`$ARGUMENTS` may contain, in any order:
- **`topic="<…>"`** — what the board is about (e.g. "Acme invoice-processing workflow", "our understanding of the claims system"). If omitted, infer from the workspace/scope or ask.
- **`kind=<…>`** — the board's arc: `workflow` (default for Delivery OS — steps of a process / "our understanding"), `journey` (user journey), `system` (architecture deep-dive), `concept` (explainer), `strategy` (decisions), or `roadmap` (phases). If omitted, infer or ask the one shaping question.
- **`out=<prefix>`** — optional output-prefix override (default `doc-output/board-<topic>`). A timestamp is always appended.
- **Free-text** — any extra source material, emphasis, or custom rules (which systems to feature, what to leave out, brand/accent overrides, "keep it to 8 cards", etc.). Passed through verbatim.

If a Delivery OS workspace exists, tell the agent to draft the board's spine and cards from `ba-output/scope.md`, `ba-output/workflow-register.md`, and `shared-context/`.

## 2. Delegate

Invoke the **doc-agent** subagent. Pass it this instruction:

> Create a **magic board** using the `doc-magic-board` skill. Topic: `<topic>`; kind: `<kind or "infer">`. Custom rules / source (verbatim, or "none"): `<free text>`.
>
> Build **one self-contained, offline-portable HTML file**: inline `assets/board-engine.js` (the pan/zoom/tour engine — keep it intact), inline all CSS and SVG, no external fetches. When a Delivery OS workspace exists, draft the spine and cards from `ba-output/scope.md`, `ba-output/workflow-register.md`, and `shared-context/` (real names and the client's real numbers; never fabricate — mark unknowns `[[NEEDS: …]]`). Follow the skill's method: find the narrative spine, cluster into 3–6 left-to-right parts, design each card to its content (diagrams, two-column step cards, a wow card near the center, a closer), place cards by inline `left/top/width` with no overlaps, and wire `window.tour` in narrative order. Apply the voice rules (no em-dashes, no contrastive negation, address the client by name). Read a run timestamp and write `doc-output/board-<topic>-<timestamp>.html` (create `doc-output/` if absent). Then do a QA pass (overview fits all clusters, every tour stop frames cleanly, no overlaps) and return a short summary, any `[[NEEDS: …]]` placeholders, and the file link.

## 3. Surface the result

When the agent returns, present its **summary**: what the board covers, its parts and tour length, which content came from the BA scope vs. supplied, and any placeholders still needing the user's input. Link to the generated `board-<topic>-<timestamp>.html` and tell the user to open it in a browser and use the on-screen next/prev (or arrow keys) to walk the tour, drag to pan, scroll to zoom, and press `O` for the overview. Keep it tight.
