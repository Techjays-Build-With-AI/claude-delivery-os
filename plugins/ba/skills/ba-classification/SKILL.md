---
name: ba-classification
description: How the BA Agent ingests, classifies, and normalizes artifact sources during /ba:scope. Read before scanning sources. Covers turning a conversational "add" declaration into registered sources, the six usage modes, the reference-only handling rule (never copy/move originals), the large-folder safeguards, and how each mode produces a normalized summary.
---

# BA source ingest, classification & safety

## Ingesting declared sources (the `add` payload)

`/ba:scope add "<free text>"` gives you sources by **intent**, e.g. *"transcripts in D:\acme\meetings, requirements at &lt;drive-link&gt;, invoice archive in D:\acme\invoices for reference only."* For each source you parse out:

1. **Locate** — resolve the path or Drive link. For Drive, check connector access; if absent, mark `Access Required` and add to `sources.md` (Status: Needs User Guidance) (never fabricate access).
2. **Detect** — type (folder/file/Drive/repo), rough file count + size + file types (cheaply: listing + sampling, not full reads).
3. **Classify** — assign one usage mode (below). Honor an explicit user hint ("for reference only") over inference.
4. **Categorize** — choose a short emergent category name (e.g. `meeting-transcripts`, `requirements`, `invoice-archive`). Categories are **created on demand** under `artifacts/<category>/`; there is no fixed taxonomy.
5. **Register** — add/update a row in `sources.md` (SRC id, description, original location, type, category, usage mode, summary path, hash, status). **Reference only — never copy, move, or delete the user's originals.**
6. **Normalize** — generate a markdown summary per the mode (see "Normalized summaries" below).

Re-declaring an existing source updates its row in place (dedup by original location + hash); it never creates a duplicate.

## Reference-only rule (non-negotiable)

Originals stay where the user put them. The workspace holds only the **registry** (`sources.md`) and **generated summaries** (`artifacts/`). Never write into, move, or delete a source location. The only files intake creates are the index rows and the `.summary.md` files.

Classify **every** source into exactly one usage mode before analyzing anything. When in doubt, choose the more conservative (less work, less risk) mode and raise an assistance note.

## Usage modes

### Deep Analysis
Primary discovery artifacts: requirement docs, BRDs, FRDs, SRS, meeting notes, discovery transcripts, process documents, client clarification responses.
- Read fully. Extract requirements, workflows, business rules, actors, examples, assumptions, gaps, clarifications. Update scope + registers.

### Reference Only
Supporting material not to be fully analyzed at intake: historical invoices, old reports, screenshots, sample files, large archives, client data dumps, transaction history.
- Do not deeply analyze. Create an index entry with a high-level description. Use later only when a requirement needs validation or an example.

### Sample and Summarize
A large source that is useful but too big for full analysis (e.g. 2 GB of historical invoices where only the structure matters).
- Analyze representative samples only. Summarize observed structure. **Do not infer global business rules** unless primary artifacts confirm them. Log sample count and selection assumptions.

### Index Only
Large, unknown, or not-immediately-relevant sources.
- Record file names, folder structure, file types, counts, and sizes where possible. Do not open every file. Do not extract requirements from this source.

### Future Agent Input
Useful to a later agent but not to BA intake now: code repositories, architecture docs, deployment files, observability dashboards, security scan outputs.
- Register the source and capture why it exists. Do not analyze during BA intake unless explicitly instructed. Note the intended future agent (e.g. TL).

### Needs User Guidance
You cannot safely determine how to handle it.
- Do not deeply analyze. Set `Status: Needs User Guidance` on its `sources.md` row, recommend a usage mode, and continue with other safe artifacts.

## Large-folder safety safeguards

Apply these thresholds before processing any folder:

```text
More than 100 files       → Ask or Index Only
More than 500 MB          → Ask or Index Only
More than 1 GB            → Index Only by default
Unknown file types        → Ask user
Sensitive-looking data    → Ask user before sampling
```

## What each input format is, and how to read it

**`Unknown file types → Ask user` is for a type that is genuinely unknown, not for one nobody listed.**
Everything below is readable today. Asking the user to confirm a PDF is a PDF spends their patience
and teaches them the tool cannot handle their material.

| Format | Read it with | Where the detail actually sits |
|---|---|---|
| `.md` `.txt` | directly | body |
| `.html` `.htm` | directly | body, `<table>` rows, `<svg>` / `<figcaption>` text |
| `.pdf` | the `pdf` skill | body, tables, figure captions — not just the first pages |
| `.docx` | the `docx` skill | body, tables, **comments and tracked changes** (often the real decisions) |
| `.xlsx` `.csv` | the `xlsx` skill | every sheet as a table; named ranges; the tabs nobody mentions |
| `.pptx` | the `pptx` skill | slide text **and speaker notes** — notes carry what the slide implies |
| `.svg` | directly | it is text: read labels and the order nodes connect in |
| `.png` `.jpg` screenshots | directly — the harness renders them | UI mockups, whiteboard photos, annotated flows |

**An image is evidence you cannot quote.** Every other source supports a
`[SRC-### › <original location>]` citation pointing at text. A screenshot does not, so record what
you read from it as an **Assumption** with the image cited as its source, never as a Confirmed
requirement. What a mockup shows is what someone drew, not what the business agreed — and a label
misread from a screenshot is indistinguishable from one read correctly.

**Scanned PDFs and photographed documents behave like images**, whatever their extension: no reliable
text layer, so the same assumption rule applies. If the `pdf` skill returns little or no text for a
file with many pages, treat it as scanned and say so rather than reporting a thin extraction as a
thin document.

## HTML is a first-class source, not an unknown type

**`.html` and `.htm` are eligible** — treat them like a document, not like a binary to be sampled.
Teams coming from Claude desktop workflows hand over client-facing HTML as their main artifact, and
falling through to *Unknown file types → Ask user* is what made one read as surface-level while its
real content sat untouched.

Three things carry the detail, and all three are readable:

- **Body prose** — as any document.
- **`<table>` content** — read as a table, row by row. Appendix tables are where the field lists, the
  rules and the worked examples usually live; skipping them loses more than skipping the prose.
- **`<svg>` and `<figcaption>` text** — an embedded flow diagram carries its steps as text nodes.
  Read the labels and the order they connect in; a flowchart is a workflow written sideways.

Ignore `<script>`, `<style>` and navigation chrome. Where the file is a report **generated by this
plugin** (a scope or review HTML), prefer its Markdown twin if one sits beside it — same content,
less noise.

## Record what you did not read

**A source read in part is summarised in part, and the summary says so.** You are the only step that
opens the original — if you do not record what was skipped, nothing downstream can know it was.

Put it on that source's `artifacts/` summary, under its own heading, and carry the count into the
intake run summary:

```
Partially absorbed: client-master-plan.html
  - Appendix B (field matrix, 140 rows) - not extracted
  - Figure 4 (SVG flow, 22 nodes) - labels read, sequence not resolved
```

**Confident output with silent gaps is the failure this prevents.** A reader cannot tell "the source
did not say" from "I did not read that part", and the two need opposite actions — one is a client
question, the other is a re-run. A question raised about something sitting in an unopened appendix
wastes the client's time and costs the review its credibility.

## Conservative defaults

- A source that looks like a **bulk archive, historical reference, or data dump** → classify `Reference Only` or `Index Only`, **unless** `sources.md` explicitly marks it `Deep Analysis`.
- An explicit `Intake Rule` in the index (e.g. "create an index only") always wins over your inference.
- Authority and priority from the index inform extraction confidence and processing order, but never override the safety thresholds above.

## Normalized summaries (what each mode produces)

Every eligible source becomes one or more `artifacts/<category>/<name>.summary.md` files (template: `source-summary.md`), with provenance frontmatter (`source_id`, `summary_of` = original location, `source_hash`, `usage_mode`). Extraction reads these summaries, not the raw originals — so the heavy reads happen once.

| Usage mode | Summary produced |
|------------|------------------|
| Deep Analysis | Full per-document summary capturing BA-relevant signals + key quotes. |
| Sample and Summarize | One summary describing observed structure from sampled items; records sample count + selection. No global rules inferred. |
| Reference Only | A short index entry / high-level description only — **no** per-file deep summary. |
| Index Only | A folder-level index (names, types, counts, sizes). No content summaries. |
| Future Agent Input | A registration note (what it is, which future agent). Not analyzed. |
| Needs User Guidance | No summary; the `sources.md` row carries the status and the reason with a recommended mode. |

Regenerate a summary only when the source is new or its hash changed (incremental runs skip unchanged sources).

## Output of classification

All classification results live in the **`sources.md` registry** (this single file replaces the old artifact-map / artifact-ledger / source-classification trio): each row records the usage mode, the one-line reason, detected counts/sizes/types, the summary path, the content hash, and the processing status.
