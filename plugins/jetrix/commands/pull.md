---
description: Refresh the local working copy from Jetrix (the source of truth) into .jetrix/cache/. Incremental by default — compares each section's hash against Jetrix and re-downloads ONLY what changed, so pulling often is cheap and staleness is never a worry. With no scope args it does a FULL pull (project identity + apps + all available content); scope args narrow it. Also refreshes the committed .jetrix/project.json wiring (project + apps + env→branch mapping). Read-only against Jetrix; never writes back (that is /jetrix:push). Requires the repo to be bound first via /jetrix:init.
argument-hint: "[--project] [--apps] [--scope] [--features] [--context] [--glossary] [--force]"
---

# /jetrix:pull

You are **refreshing the local working copy from Jetrix**. Jetrix is the source of truth; `.jetrix/cache/` is a disposable local mirror the agents read so they can do a whole piece of work locally without a round-trip per read. A pull brings the cache (and the committed wiring in `project.json`) up to date with Jetrix. It **never writes to Jetrix** — pushing local changes up is `/jetrix:push`. Read the `jetrix-sync` skill first if it is not already in context.

## 1. Preconditions

- The repo must be **bound**: `.jetrix/project.json` must exist with a resolved `jetrix.project_id`. If it is missing, stop and tell the user to run `/jetrix:init <slug>` first.
- The **Jetrix MCP** must be connected. If it is not, stop — a pull cannot fabricate Jetrix data. (Do **not** fetch via curl/scripts; only the Jetrix MCP is the read path. Bind the exact MCP tool names in the `jetrix-sync` skill once the Jetrix MCP is confirmed.)

## 2. Parse scope

`$ARGUMENTS` selects which sections to refresh. **No args = full pull** of everything available for the project:

| Flag | Refreshes |
|------|-----------|
| *(none)* | Everything available: `project`, `apps`, `glossary`, `scope`, `registers`, `features`, `context`. |
| `--project` | Project identity/overview + `environments` only (the top of `project.json`). |
| `--apps` | The apps list — repos, types, and each app's env→branch mapping — into `project.json`. |
| `--glossary` / `--scope` / `--features` / `--context` | Just that content section of the cache. |
| `--force` | Ignore cached hashes and re-download the selected sections unconditionally. |

Combine flags freely (e.g. `--project --apps` after the user created apps in Jetrix). Unknown flag → list the valid ones and stop.

## 3. Incremental fetch (the core rule)

For each selected section, do a **hash check before download**:

1. Read the section's `hash` + `fetched_at` from `.jetrix/cache/cache.manifest.json`.
2. Ask Jetrix (via the Jetrix MCP) for that section's **current hash/version** for this `project_id`.
3. If the hashes match and `--force` was not given, **skip** the section (log "unchanged"). Otherwise fetch it and overwrite the local copy.
4. Update the section's `hash` + `fetched_at` in the manifest.

A pull where nothing changed is a **no-op** beyond the hash checks. This is deliberate: because refresh is cheap, callers pull freely (at session start, and always before a push) rather than reasoning about staleness.

## 4. Write the wiring — `.jetrix/project.json` (committed)

For `--project` / `--apps` (and the full pull), refresh the committed descriptor from Jetrix:
- **project**: `jetrix.*` (slug, id, workspace_ref, overview) and the project-level `environments`.
- **apps**: rebuild `apps[]` from Jetrix — each app's `slug`, `id`, `type`, `repo`, and `env_branches` (every project environment → that app's branch name). This is how apps created in the Jetrix UI land locally.

**Merge, never clobber:** preserve `bound_at` and any hand-added `local_root` values; refresh Jetrix-sourced fields; stamp `last_pulled`. Never write secrets — names/refs/branches only.

## 5. Write the content — `.jetrix/cache/` (gitignored)

For the content sections, mirror the Jetrix records into the cache tree as the agents expect to read them:

```text
.jetrix/cache/
├── cache.manifest.json
└── context/
    ├── glossary.md
    ├── scope/            # scope + registers, rendered from the Jetrix records
    ├── features/         # feature-index + one folder per feature
    ├── frontend/  backend/  database/   # the technical context graph
```

Record every pulled record's `local_id → jetrix_id` in the manifest `id_map` (so a later push upserts, not duplicates). Content here is a **read cache** — agents read it, but Jetrix stays authoritative; never treat a cache edit as published until it is pushed.

## 6. Report

Print: the resolved project; which sections were **refreshed vs unchanged vs skipped**; the app count now in `project.json` (and each app's env→branch mapping if `--apps`/full); and the new `last_pulled` stamp. If apps were expected but Jetrix returned none, say so and point the user to create them in Jetrix, then re-run `/jetrix:pull --apps`.

Keep it **idempotent and read-only**: a re-run with no changes upstream must touch nothing but the hash-check timestamps, and must never write to Jetrix.
