---
description: Scaffold a new Techjays Delivery OS project workspace — creates the standard folder structure, a starter intake.index.md, and empty register/shared-context files from the canonical templates. Run this once at the start of a discovery engagement.
argument-hint: "[project-name]"
---

# Initialize a Delivery OS project workspace

You are scaffolding a new Delivery OS project so the BA Agent (and later Doc/TL/QA agents) have a consistent place to read and write. **Follow the shared contract** — read the `delivery-os-conventions` skill first if you have not in this session.

## Inputs
- `$ARGUMENTS` may contain a target project folder name. If empty, scaffold in the current working directory and confirm the project name with the user.

## Steps

1. **Confirm location.** Determine the project root (the `$ARGUMENTS` folder, or current directory). If the folder already contains a Delivery OS workspace (an existing `intake.index.md` or `ba-output/`), do **not** overwrite — report what already exists and stop unless the user asks to proceed.

2. **Create the folder structure** exactly as defined in the contract:
   ```text
   raw-artifacts/{client-requirements,meeting-transcripts,client-reference-docs,system-screenshots,process-maps,sample-data,emails}
   shared-context/
   ba-output/intake-runs/
   final/
   ```
   Add a `.gitkeep` to each empty `raw-artifacts/*` subfolder so the structure survives in git.

3. **Seed files from templates.** The canonical templates ship with this plugin at `${CLAUDE_PLUGIN_ROOT}/templates/`. For each, read the template and write it into the workspace (only if the destination does not already exist):

   | Template | Destination |
   |---|---|
   | `intake.index.md` | `./intake.index.md` |
   | `shared-context/project-profile.md` | `./shared-context/project-profile.md` |
   | `shared-context/glossary.md` | `./shared-context/glossary.md` |
   | `shared-context/stakeholder-map.md` | `./shared-context/stakeholder-map.md` |
   | `shared-context/system-landscape.md` | `./shared-context/system-landscape.md` |
   | `shared-context/decision-log.md` | `./shared-context/decision-log.md` |

   The `ba-output/` register files are created by the BA Agent on first `/ba:intake`, not here — so the workspace starts clean. (Optionally copy the `ba-output/*` templates too if the user wants placeholder registers up front.)

4. **Stamp frontmatter.** Set `generated_at` to today's date and `status: Draft` on each seeded file per the contract's frontmatter standard.

5. **Report.** Print the created tree and tell the user the next steps:
   - Drop source material into `raw-artifacts/…`
   - Edit `intake.index.md` to declare each artifact source (type, path, usage mode, authority, priority)
   - Run `/ba:intake` to build the living scope document

Keep edits minimal and idempotent — re-running this command must never clobber existing work.
