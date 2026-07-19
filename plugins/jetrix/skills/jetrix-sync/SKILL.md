---
name: jetrix-sync
description: The Jetrix binding + sync contract for Techjays Delivery OS. Read this before running or reasoning about /jetrix:init, /jetrix:pull, or /jetrix:push, or before any agent reads/writes the .jetrix/ tree. Defines the working-copy model (Jetrix is the source of truth; local .jetrix/cache is a disposable read-through copy), the two-files/two-lifecycles split (committed project.json identity+wiring vs gitignored cache), the incremental pull + idempotent push mechanics, and how local Delivery OS records map to Jetrix objects. Builds on the delivery-os-conventions document contract (stable IDs, schemas) — that skill defines the records; this one defines how they sync.
---

# Jetrix Sync — Binding & Working-Copy Contract

When a project's delivery context is centralized in **Jetrix**, Jetrix is the **single source of truth** for *all* project context — glossary, scope, the supporting registers, the feature breakdown, and the `context/` graph (pages, endpoints, entities, and their relationships). This skill defines how a local workspace binds to a Jetrix project and stays in sync. It builds on `delivery-os-conventions` (which defines the records themselves — stable IDs, frontmatter, schemas, vocabulary); this skill defines how those records move between local and Jetrix.

> **Contract version: 1.0.** This is owned by the **`jetrix`** plugin. The `delivery-os` core plugin keeps a one-paragraph pointer to it (conventions §1.b).

---

## 1. The working-copy model

The local `.jetrix/` folder is **not** a second source of truth. It is a **working copy**, exactly like a git checkout:

1. The agent **pulls** the slices it needs into a local cache;
2. does a whole piece of work **locally** — no MCP round-trip per read; fast, reviewable, and it keeps working read-only when the MCP is down;
3. and when the user is satisfied, **pushes** the result back to Jetrix.

A push is a **deliberate commit**, not an autosave. Nothing a user does locally is *published* until it is pushed.

```text
<workspace-root>/
└── .jetrix/
    ├── project.json          # COMMITTED — identity + wiring, same for every dev + CI
    └── cache/                # GITIGNORED — disposable working copy of the Jetrix store
        ├── cache.manifest.json
        └── context/          # local mirror: glossary, scope, features, frontend/backend/database
```

---

## 2. Two files, opposite lifecycles — never merge them

### `.jetrix/project.json` (committed) — identity + wiring, never content
Machine-independent so every developer, CI job, and MCP client resolves the *same* project and the *same* environment→branch mapping. It holds:
- **Identity:** Jetrix `project_slug`, `project_id`, `workspace_ref`, one-line `project_overview`.
- **Environments** (project-level): the ordered list — e.g. `dev`, `staging`, `uat`, `prod`.
- **Apps** (`apps[]`): each app is a repo (frontend / backend / mobile / service) with its `slug`, `id`, `type`, `repo` URL, an optional local checkout path (`local_root`), and an **`env_branches`** map — every project environment → *that app's* branch name. This is the mapping CI reconciliation and environment promotion consume.

It holds **no project content** (that's the cache) and **no secrets** (tokens live only in the developer's local Jetrix MCP config). `apps[]` is empty at greenfield bind and is filled by a later `/jetrix:pull --apps` once apps are created in Jetrix. Seed from `${CLAUDE_PLUGIN_ROOT}/templates/project.json`.

### `.jetrix/cache/` (gitignored) — the working copy
A disposable local mirror of the Jetrix store. `cache.manifest.json` stamps `fetched_at` + a per-section **hash** so a pull is **incremental** — it re-downloads only the sections whose Jetrix hash changed, which makes frequent pulls cheap and staleness a non-issue. It also holds an **`id_map`** (`{ local_id, jetrix_id, section, hash }`) so a push upserts by stable id rather than duplicating. The whole cache is safe to delete anytime; a pull rebuilds it. Seed the manifest from `${CLAUDE_PLUGIN_ROOT}/templates/cache.manifest.json`.

---

## 3. The two sync verbs

- **`/jetrix:pull`** — Jetrix → cache, incremental and **read-only** against Jetrix. Full pull (no args) refreshes project + apps + all content; scoped flags (`--project`, `--apps`, `--scope`, `--features`, `--context`, `--glossary`) refresh one section; `--force` ignores the cached hash. Run it at session start, after creating apps in Jetrix (`--apps`), and always before a push.
- **`/jetrix:push`** — cache → Jetrix, the **only** path that mutates the store from local. Idempotent (upsert by stable id via `id_map`), transactional (`propose_write` → diff preview → `commit_write` / `cancel_write`), and safe (pull-before-push; on a both-sides-changed conflict it **stops** rather than clobbering a Jetrix edit).

---

## 4. Authority & canonical form

**Jetrix is authoritative.** The cache is a working copy — an agent reads it freely and edits it while working, but a local edit is **not published** until pushed, and on conflict Jetrix (or a human resolving it) wins.

The canonical form **inside Jetrix is structured records**, each with a stable id and its relationships: requirement, workflow, business-rule, data-entity, integration, example, assumption, clarification, decision (BA); feature (BA breakdown); page, endpoint, entity (TL context graph). `scope.md` and the branded `.docx` are **projections rendered from those records**, not the source — push the underlying records, not the document blob. The stable local ids from `delivery-os-conventions` §3 (`INTK-AI-02`, `WF-001`, `FEAT-SUP-001`, `PAGE-…`, `EP-…`, `ENT-…`) are the external keys that make push idempotent and traceability survive in Jetrix.

---

## 5. Greenfield app creation (why a pull may come in two waves)

At greenfield there are no repos/apps yet. The typical order is:
1. `/jetrix:init <slug>` binds identity and scaffolds an empty cache (no apps).
2. BA produces scope locally and `/jetrix:push`es it — Jetrix now holds the scope records.
3. The feature/technical layer needs to bind pages/endpoints/entities to **apps**. If `project.json` has no apps, the flow prompts the user to create the apps in Jetrix (each with its repo link + environment→branch mapping), each getting its own `app_id`.
4. `/jetrix:pull --apps` brings those apps (repo, type, `env_branches`) into `project.json`.

The *logical* implementation needs (which pages/endpoints/entities a feature requires) are app-agnostic and can be produced before apps exist; only the *app binding* waits on step 4. Design downstream commands so the logical layer completes without apps and only the binding step depends on them.

---

## 6. MCP binding (to complete once the Jetrix MCP is connected)

All reads and writes go through the **Jetrix MCP** only — never curl/scripts. Bind the concrete MCP tool names here once the Jetrix MCP is available, mapping each operation to its tool:
- **read**: resolve project by slug; list environments; list apps; fetch each content section + its hash.
- **write**: `propose_write` → `commit_write` / `cancel_write` (transactional), upsert keyed by the record's stable local id stored as an external key.

Until then, the commands reference "the Jetrix MCP" abstractly; wiring the real tool names in is a required follow-up.
