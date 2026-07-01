---
description: Scaffold a new Techjays Delivery OS project workspace — creates ONE named container folder with a README manifest, a living intake.index.md source registry, and the shared-context/ba-output/final structure. Does NOT create a rigid raw-artifacts taxonomy; sources are added later via /ba:scope.
argument-hint: "<project-name>"
---

# Initialize a Delivery OS project workspace

You are scaffolding a new Delivery OS project. **Everything goes under one named container folder** so the user can see exactly what Delivery OS created (and delete one folder for a clean slate). Read the `delivery-os-conventions` skill first if it is not already in context.

## Inputs
- `$ARGUMENTS` should be the project/container name (e.g. `acme-invoice-processing`).
- If `$ARGUMENTS` is empty, **ask the user for a name — do NOT scaffold into the current directory** (that pollutes the root). Suggest a kebab-case name from the client/project if you can infer one.

## Steps

1. **Resolve the container.** The workspace root is `./<project-name>/`. If a folder of that name already contains a Delivery OS workspace (a `README.md` with our manifest marker or an existing `intake.index.md`), do **not** overwrite — report what exists and stop unless the user asks to proceed. Creating into a brand-new folder is the normal path.

2. **Create the structure** (and nothing else — no `raw-artifacts/`, no pre-made categories):
   ```text
   <project-name>/
   ├── README.md
   ├── intake.index.md
   ├── artifacts/            (empty; add a .gitkeep — categories are created later by intake)
   ├── shared-context/
   ├── ba-output/
   │   └── intake-runs/      (empty; add a .gitkeep)
   └── final/                (empty; add a .gitkeep)
   ```

3. **Seed files from the bundled templates** at `${CLAUDE_PLUGIN_ROOT}/templates/`. Write each into the container only if it does not already exist, and stamp `generated_at` to today + `status: Draft`:

   | Template | Destination |
   |---|---|
   | `workspace-readme.md` | `<project-name>/README.md` |
   | `intake.index.md` | `<project-name>/intake.index.md` |
   | `shared-context/project-profile.md` | `<project-name>/shared-context/project-profile.md` |
   | `shared-context/glossary.md` | `<project-name>/shared-context/glossary.md` |
   | `shared-context/stakeholder-map.md` | `<project-name>/shared-context/stakeholder-map.md` |
   | `shared-context/system-landscape.md` | `<project-name>/shared-context/system-landscape.md` |
   | `shared-context/decision-log.md` | `<project-name>/shared-context/decision-log.md` |

   The `ba-output/` register files are created by the BA Agent on first intake — the workspace starts clean. **Do not pre-create downstream agent output folders** (`tl-output/`, `doc-output/`, `qa-output/`): by design each downstream agent creates its own output folder the first time it runs, so a fresh workspace has no empty folders for agents that may never be used (see the `delivery-os-conventions` *Output-folder creation rule*). `init` scaffolds only `shared-context/` and `ba-output/`.

4. **Report.** Print the exact tree you created, note that **original source files are never moved or copied** (Delivery OS only indexes and summarizes them), and give the next step:
   > Add your sources in one line, e.g.:
   > `/ba:scope add "meeting transcripts in <folder or Drive link>, client requirements in <folder or Drive link>, historical invoices in <folder> for reference only"`
   > The agent will classify each, generate summaries under `artifacts/`, register them in `intake.index.md`, and build the scope.

Keep it idempotent — re-running must never clobber existing work.
