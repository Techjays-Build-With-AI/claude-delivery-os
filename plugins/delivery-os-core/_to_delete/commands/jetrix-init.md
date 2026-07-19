---
description: Bind this local workspace to an existing Jetrix project so Delivery OS agents and MCP clients resolve the same project every time. Writes a committed identity + wiring descriptor at .jetrix/project.json and scaffolds a gitignored .jetrix/cache/ working copy. Does NOT fetch content here — the cache is filled by /delivery-os:jetrix-pull. At greenfield there are usually no apps yet; apps are created in Jetrix later and pulled in. Idempotent — re-run to refresh the descriptor. Does NOT scaffold a local Delivery OS workspace (that is /delivery-os:init) and never invents Jetrix data.
argument-hint: "<project-slug> [--repo <path>]"
---

# /delivery-os:jetrix-init

You are **connecting this local workspace to an existing Jetrix project**. Jetrix is the **source of truth** for all delivery context; this command records *which* project this workspace maps to and scaffolds a local working copy that `/delivery-os:jetrix-pull` fills. Read the `delivery-os-conventions` skill (§1.b *Jetrix binding*) first if it is not already in context.

**This is not `/delivery-os:init`.** `init` scaffolds a local-only Delivery OS workspace. `jetrix-init` binds this workspace to a Jetrix project so work syncs to the shared store. They are different verbs; do not scaffold the `shared-context/`/`ba-output/` tree here.

**Apps are not required here.** An *app* is a repo (frontend, backend, mobile, a service). At greenfield there are usually none yet — they are created in Jetrix later (repo link + env→branch mapping) and land in `project.json` via `/delivery-os:jetrix-pull --apps`. Do not ask the user to pick an app at bind time.

## 1. Parse arguments

`$ARGUMENTS`:
- **`<project-slug>`** (required) — the Jetrix project slug the user already created. If missing, ask for it; do not guess.
- **`--repo <path>`** (optional) — workspace root to bind; defaults to the current directory.

## 2. Preconditions

Confirm the **Jetrix MCP** is connected. If it is not, stop and tell the user to connect Jetrix (this command cannot fabricate project data). Do not fetch via curl/scripts — only the Jetrix MCP.

## 3. Resolve the project from Jetrix (source of truth)

Via the Jetrix MCP, look up the project by `<project-slug>` and read:
- project id, canonical name, one-line overview, and workspace ref (URL or id);
- the project's **environments** — names/refs only (e.g. dev/staging/uat/prod);
- the project's **apps** if any already exist — slug, id, type, repo, env→branch mapping. At greenfield expect none.

If the slug resolves to nothing, stop and report it (offer the closest matches if the MCP supports search). Never invent ids.

## 4. Write the committed descriptor — `.jetrix/project.json`

Seed from the bundled template at `${CLAUDE_PLUGIN_ROOT}/templates/jetrix/project.json`, filling real values from step 3. This file is **committed** (machine-independent identity + wiring, identical for every dev + CI). It holds project identity, `environments`, and `apps[]` (repos + each app's env→branch mapping) — **wiring only, never content and never secrets**. Leave `apps[]` empty if Jetrix has none yet; a later `/delivery-os:jetrix-pull --apps` fills it once apps are created.

**Idempotency (this is required):**
- If `.jetrix/project.json` already exists, **merge, don't clobber**: refresh `jetrix.*`, `environments`, and `apps[]` from Jetrix, but preserve any hand-added fields (e.g. an app's `local_root`).
- Stamp `bound_at` only on first creation; refresh `last_pulled` whenever Jetrix data is read.
- **Never** write tokens, passwords, or connection secrets here — names/refs/branches only.

## 5. Gitignore the cache

Ensure the repo's `.gitignore` ignores the cache (create `.gitignore` if absent, append idempotently — don't duplicate the line):

```gitignore
# Delivery OS — Jetrix local context cache (disposable, per-machine)
.jetrix/cache/
```

`.jetrix/project.json` stays tracked; `.jetrix/cache/` never is.

## 6. Scaffold the cache folder — do NOT fetch content here

Create the empty `.jetrix/cache/` structure only. **Do not pull content during bind** — keep binding fast and independent of the full project being fetchable. The cache is filled by `/delivery-os:jetrix-pull`, which is incremental (it refreshes only what changed in Jetrix).

```text
.jetrix/
├── project.json                 # committed identity + wiring (step 4)
└── cache/                        # gitignored, disposable working copy — created empty here
    ├── cache.manifest.json       # from templates/jetrix/cache.manifest.json (all sections empty, hashes null)
    └── context/
        ├── glossary.md  .gitkeep
        ├── scope/       .gitkeep
        ├── features/    .gitkeep
        ├── frontend/    .gitkeep
        ├── backend/     .gitkeep
        └── database/    .gitkeep
```

- Write `cache.manifest.json` from the template with every section `fetched_at: null`, `hash: null` — it's a stub the first `jetrix-pull` fills in.
- Create each `context/` subfolder with a `.gitkeep` so the layout exists for the pull. Don't call the Jetrix MCP for content in this step.

## 7. Report

Print:
- the resolved Jetrix **project** (slug, name, overview);
- the **environments** discovered, and the **app count** (usually 0 at greenfield);
- the exact `.jetrix/` tree written (cache scaffolded empty), and the `.gitignore` line ensured;
- whether this was a first bind or a refresh of an existing one.

Next step: the workspace is now bound but the cache is **empty**. Run `/delivery-os:jetrix-pull` to fill it from Jetrix (and again after you create apps in Jetrix, to pull their repo + env→branch wiring into `project.json`). Re-run `/delivery-os:jetrix-init <slug>` anytime to refresh the descriptor. Keep it **idempotent** — a re-run must refresh Jetrix-sourced fields without ever clobbering hand-edits.
