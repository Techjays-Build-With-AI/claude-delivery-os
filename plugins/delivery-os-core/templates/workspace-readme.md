# [Project Name] — Delivery OS Workspace

This folder is a **Techjays Delivery OS** project workspace. Everything here was created by the Delivery OS plugin. To start completely over, delete this folder.

> **Your original files are never touched.** Delivery OS does not copy, move, or delete your source documents. It only keeps an *index* of where they live and generates *summaries* of them here. The originals stay wherever you put them (local folders, Google Drive, etc.).

## What's in here

| Path | What it is | Who maintains it |
|------|------------|------------------|
| `intake.index.md` | The **source registry** — every source you've added, where it really lives, how it was classified, and its summary + status. | `/ba:intake` (you can edit it too) |
| `artifacts/` | Generated **markdown summaries** of your sources, grouped into categories that are created on demand. | `/ba:intake` |
| `shared-context/` | Project profile, glossary, stakeholders, systems, decisions — shared with future Doc/TL/QA agents. | BA agent |
| `ba-output/` | The **living scope document** and supporting registers (requirements, business rules, etc.). | BA agent |
| `ba-output/intake-runs/` | One summary per intake run. | BA agent |
| `final/` | Approved, client-facing deliverables. | you |

## How to use it

1. **Add your sources in one line** (no need to pre-sort anything):
   ```text
   /ba:intake add "meeting transcripts in <folder or Drive link>, client requirements in <folder or Drive link>, historical invoices in <folder> for reference only"
   ```
   Intake classifies each source, generates a summary under `artifacts/`, and registers it in `intake.index.md`.
2. **Build / refresh the scope:**
   ```text
   /ba:intake
   ```
   Re-run it any time you add more material — it processes only what's new or changed.

## Modes
`/ba:intake` · `/ba:intake add "…"` · `mode=incremental` · `mode=dry-run` · `mode=index-only` · `mode=classify-only`
