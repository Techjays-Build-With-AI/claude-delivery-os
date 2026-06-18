---
name: ba-classification
description: How the BA Agent classifies each artifact source and decides how deeply to process it. Read before scanning artifact sources during /ba:intake. Defines the six usage modes and their behaviors, the large-folder safety safeguards (file count / size / type thresholds), and the conservative defaults for bulk archives and sensitive data.
---

# BA source classification & safety

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

## Output of classification

Record results in `source-classification.md`: for each source, the chosen usage mode and a one-line reason it was analyzed, sampled, indexed, skipped, or deferred. Reflect counts/sizes/types in `artifact-map.md` and per-file status in `artifact-ledger.md`.
