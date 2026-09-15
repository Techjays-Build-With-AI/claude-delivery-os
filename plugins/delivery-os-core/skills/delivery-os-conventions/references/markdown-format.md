# Markdown format contract — Mission Control task tabs

Applies to any `.md` whose body is pushed to a Task tab: BA feature folders, `tasks/*.md`, TL implementation plans, sub-task descriptions. Bodies are pushed **verbatim**, so the file is exactly what the user sees.

Scope is the **markdown tabs** (`contentType: 'md'`). The rich-text editor is a separate surface and none of this applies to it.

## The renderer

`MarkdownTaskEditor.tsx` → `@uiw/react-md-editor` → `@uiw/react-markdown-preview` → `react-markdown` v10.

The library composes the chain itself and appends whatever the component passes:

```
remark:  remark-github-blockquote-alert → remark-gfm
rehype:  rehype-raw → slug → autolink-headings → rehype-ignore → rehype-rewrite
         → rehype-highlight → rehype-sanitize → rehype-prism
```

Everything below was verified by rendering through that chain.

## Use these — they render well

| Feature | Write it as |
|---|---|
| **Table** | GFM pipe table with a `\|---\|---\|` separator |
| **Nested list** | `- parent` then 2-space-indented `  - child` |
| **Checklist** | `- [x] done` / `- [ ] todo` → real checkboxes |
| **Strikethrough** | `~~removed~~` |
| **Code** | fence with a language — ` ```sql ` → syntax highlighted |
| **Footnote** | `Text[^1]` + `[^1]: the note` |
| **Link** | bare URLs autolink; `[label](url)` for a caption |

Headings get automatic anchor links, so `###` sections are individually linkable.

## Breaks content

**Table header and separator must have the same cell count.** A mismatch doesn't degrade into a rough table — no table appears at all, just a line of literal pipe characters running across the tab:

```
| A | B | C |     ← 3 columns
|---|---|         ← 2 columns  →  reader sees:  | A | B | C ||---|---|| 1 | 2 |
| 1 | 2 |
```

Escape a literal pipe inside a cell as `\|`, and keep every cell on one physical line.

**Never mix `-` and `*` in one list.** Each change of marker ends the list and starts a new one, so what should be three bullets becomes three separate one-item lists — with vertical gaps between them instead of tight spacing:

```
- a
* b      →  reader sees three detached bullets, not one list
- c
```

**No trailing double-space** — two spaces at the end of a line force a line break mid-paragraph, so text wraps in a place you didn't choose.

## Avoid

- **GitHub alerts (`> [!NOTE]`, `> [!WARNING]`).** The remark plugin is present, but the sanitiser strips `div` classes, so an alert renders as a plain unstyled block with the word "NOTE" on its own line. Use a bold lead-in instead: `**Note** — …`.
- **Raw HTML.** It does render here (`rehype-raw` runs before the sanitiser, so `<br>` and `<b>` survive), but `class` is stripped and the same text loses the markup entirely on other surfaces. `**bold**` works everywhere; `<b>bold</b>` works in one place.

## Reads badly

- **Tab sections are `##`; everything inside them is `###` or deeper.** Never `#` — that's the title. An `##` inside a tab renders at `1.35em` with a full-width rule, competing with the tab itself. Styling only — it still parses.
- **Keep table cells short.** Long prose wraps badly; move it to a list under the table.
- **Each tab must stand alone** — no "as described above"; the reader sees one tab at a time.

## Diagrams

Fence as ` ```mermaid `, one node or edge per line. A flattened one-line diagram fails to parse and falls back to raw source.

## Not a problem — verified, don't spend effort here

- **Blank lines before headings, lists, tables or fences.** All of them may interrupt a paragraph; glued and spaced render identically.
- **Unbackticked identifiers.** `is_removed` renders intact. Backticks are for clarity, not correctness.
- **Asterisks in prose.** `2*3` and `* wildcard` are safe.

## Placement

Map a section to a tab only when its heading clearly matches a known tab name. Anything else stays in `description` — never invent a tab for it.

**An explicit user instruction always wins over a heading match.** If the user says "put the happy path in the description", it goes in the description regardless of the heading.
