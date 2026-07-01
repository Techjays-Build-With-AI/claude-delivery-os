---
name: ba-classification
description: How the BA Agent ingests, classifies, and normalizes artifact sources during /ba:scope. Read before scanning sources. Covers turning a conversational "add" declaration into registered sources, the six usage modes, the reference-only handling rule (never copy/move originals), the large-folder safeguards, and how each mode produces a normalized summary.
---

# BA source ingest, classification & safety

## Ingesting declared sources (the `add` payload)

`/ba:scope add "<free text>"` gives you sources by **intent**, e.g. *"transcripts in D:\acme\meetings, requirements at &lt;drive-link&gt;, invoice archive in D:\acme\invoices for reference only."* For each source you parse out:

1. **Locate** — resolve the path or Drive link. For Drive, check connector access; if absent, mark `Access Required` and add to `indexing-assistance-needed.md` (never fabricate access).
2. **Detect** — type (folder/file/Drive/repo), rough file count + size + file types (cheaply: listing + sampling, not full reads).
3. **Classify** — assign one usage mode (below). Honor an explicit user hint ("for reference only") over inference.
4. **Categorize** — choose a short emergent category name (e.g. `meeting-transcripts`, `requirements`, `invoice-archive`). Categories are **created on demand** under `artifacts/<category>/`; there is no fixed taxonomy.
5. **Register** — add/update a row in `intake.index.md` (SRC id, description, original location, type, category, usage mode, summary path, hash, status). **Reference only — never copy, move, or delete the user's originals.**
6. **Normalize** — generate a markdown summary per the mode (see "Normalized summaries" below).

Re-declaring an existing source updates its row in place (dedup by original location + hash); it never creates a duplicate.

## Reference-only rule (non-negotiable)

Originals stay where the user put them. The workspace holds only the **registry** (`intake.index.md`) and **generated summaries** (`artifacts/`). Never write into, move, or delete a source location. The only files intake creates are the index rows and the `.summary.md` files.

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
- Do not deeply analyze. Add to `indexing-assistance-needed.md`, recommend a usage mode, and continue with other safe artifacts.

## Large-folder safety safeguards

Apply these thresholds before processing any folder:

```text
More than 100 files       → Ask or Index Only
More than 500 MB          → Ask or Index Only
More than 1 GB            → Index Only by default
Unknown file types        → Ask user
Sensitive-looking data    → Ask user before sampling
```

## Conservative defaults

- A source that looks like a **bulk archive, historical reference, or data dump** → classify `Reference Only` or `Index Only`, **unless** the intake index explicitly marks it `Deep Analysis`.
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
| Needs User Guidance | No summary; logged to `indexing-assistance-needed.md` with a recommended mode. |

Regenerate a summary only when the source is new or its hash changed (incremental runs skip unchanged sources).

## Output of classification

All classification results live in the **`intake.index.md` registry** (this single file replaces the old artifact-map / artifact-ledger / source-classification trio): each row records the usage mode, the one-line reason, detected counts/sizes/types, the summary path, the content hash, and the processing status.
