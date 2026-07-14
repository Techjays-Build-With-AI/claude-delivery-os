---
description: Turn a specification or scope document into an interactive HTML spec walkthrough — a top overview state diagram of the phases the system moves through (hover for detail, click to trace transitions), then a drill-down section per feature/module with its own workflow diagram and worked examples, plus a command/object catalog and success criteria. One self-contained HTML file written to doc-output/.
argument-hint: "spec=\"<path or topic>\" [title=\"<Title>\"] [\"<source material / custom rules>\"]"
---

# /doc:walkthrough

You are the entry point for generating a **spec walkthrough**: an interactive,
sidebar-navigated HTML page that presents a specification as a state overview
plus a module-by-module breakdown with examples. Parse the arguments and
**delegate the build to the `doc-agent` subagent**, which runs in its own
context.

## 1. Parse arguments

`$ARGUMENTS` may contain, in any order:

- **`spec="<path or topic>"`** — the source specification: a file path
  (`.md`/`.docx`/`.pdf`/`.txt`), a workspace doc, or a topic to source from the
  BA scope. If omitted, infer from the workspace/attachments or ask.
- **`title="<Title>"`** — the header title. Optional; inferred from the spec's
  own title when present.
- **`out=<prefix>`** — optional output-prefix override (default follows the
  skill's `walkthrough-<topic>-<DDMonYYYY>` naming in `doc-output/`).
- **Free-text** — any extra source material, emphasis, or custom rules (which
  lifecycle is the spine, which sections to feature, brand/accent overrides).
  Passed through verbatim.

If a Delivery OS workspace exists and no explicit spec is given, tell the agent
to source from `ba-output/scope.md` and `shared-context/`.

## 2. Delegate

Invoke the **doc-agent** subagent. Pass it this instruction:

> Create a **spec walkthrough** using the `doc-spec-walkthrough` skill. Spec
> source: `<path / topic>`. Title: `<title or "infer">`. Custom rules / source
> (verbatim, or "none"): `<free text>`.
>
> First read the source spec end to end and model it: the **state machine** (the
> ordered states/phases the system or a unit of work passes through, with every
> transition including branch/failure edges), the **modules/features** (each with
> its ordered steps and any worked example the spec gives), the **command/object
> catalog**, and the **success criteria**. Then read the skill and its reference
> files (`design-tokens`, `page-structure`, `state-diagram`, `module-sections`,
> `javascript`) in order and build **one self-contained, offline-portable HTML
> file** in the Techjays house style (dark-navy header, gold accent, fixed left
> sidebar nav): a top **overview state diagram** (interactive SVG state machine,
> hover a state for detail via `data-title`/`data-desc` split on `||`, click a
> state to highlight its transitions), then **one section per module/feature**
> each with a compact workflow diagram, a numbered step list, and a **worked
> example using the spec's real IDs/values**, followed by a command/object catalog
> and a success-criteria strip. Source everything from the spec; use real names,
> IDs, and numbers; **never fabricate** — mark any missing detail the page wants
> as `[[NEEDS: …]]` and list it back. Follow the skill's Quality checklist
> (real states + all transitions incl. failure edges, light node fills with
> coloured borders, unique SVG marker ids per diagram, `body{padding-left:180px}`,
> tooltip div first in `<body>`, scroll-spy nav, no external dependencies) and the
> voice rules (no em-dashes, no contrastive negation). Write to
> `doc-output/walkthrough-<topic>-<DDMonYYYY>.html` (create `doc-output/` if
> absent), save UTF-8 with no mojibake. Then QA in a browser (scroll-spy tracks
> sections, every state/step tooltip fires, click-to-highlight lights the right
> edges, no clipped SVG) and return a short summary, any `[[NEEDS: …]]`
> placeholders, and the file link.

## 3. Surface the result

When the agent returns, present its **summary**: the states in the overview, the
module sections covered, which examples were drawn from the spec, and any
`[[NEEDS: …]]` placeholders still needing input. Link to the generated HTML and
tell the user to open it in a browser (sidebar jumps to sections; hover states
and steps for detail; click a state to trace its transitions). Keep it tight.
