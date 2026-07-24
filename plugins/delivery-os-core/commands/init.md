---
description: Scaffold the Delivery-OS output workspace as a named container inside the current directory. Folder name comes from `.jetrix/project.json` (Solution slug) if `/jetrix:init` has run; otherwise pass a `<name>` argument. Creates `./<name>/` with `ba-output/`, `artifacts/`, `context/`, `shared-context/` (with seeded templates), `tl-output/`, `qa-output/`, `dev-output/`, `doc-output/`. Sibling of `.jetrix/` at workspace root — matches the delivery-os get-started model ("single container folder per project"). Does NOT touch Jetrix.
argument-hint: "[<name>]"
---

# /delivery-os:init

Scaffold the Delivery-OS project workspace as a named container at `<workspace>/<name>/`. Sits **sibling** to `.jetrix/` at workspace root:

```
<workspace>/
├── .jetrix/                    ← (optional, from /jetrix:init)
└── <name>/                     ← this command creates this
    ├── ba-output/
    ├── artifacts/
    ├── context/
    ├── shared-context/
    ├── tl-output/
    ├── qa-output/
    ├── dev-output/
    └── doc-output/
```

Read the `delivery-os-conventions` skill first if it's not already in context.

## 1. Resolve the container name

The name for the new folder comes from one of these, in order:

1. **`.jetrix/project.json` exists** (workspace already bound via `/jetrix:init`) → use `solutionSlug` from that file. **No argument needed.** This is the standard path.
2. **`$ARGUMENTS` provided** → use it as the name (kebab-case recommended). Standalone / no-Jetrix mode.
3. **Neither** → ask the teammate for a name. Do NOT scaffold into cwd itself (that pollutes the parent).

## 2. Resolve target path

`<target>` = `<cwd>/<name>/`.

**Rerun handling:**

- If `<target>/` exists AND contains a `ba-output/` folder or seeded `shared-context/*.md` → treat as an existing Delivery-OS container. Fill in only missing pieces; never clobber existing files.
- If `<target>/` exists but has NO Delivery-OS markers → report *"Folder `<name>` already exists but doesn't look like a Delivery-OS workspace. Continue anyway? [y/n]"*.

## 3. Create the folder tree

Under `<target>/`, create (all idempotent — never overwrite existing files):

```
<target>/
├── ba-output/                          (empty; .gitkeep)
├── artifacts/                          (empty; .gitkeep)
├── context/
│   ├── features/                       (empty; .gitkeep)
│   ├── frontend/pages/                 (empty; .gitkeep)
│   ├── backend/domains/                (empty; .gitkeep)
│   ├── database/entities/              (empty; .gitkeep)
│   └── project/                        (empty; .gitkeep)
├── shared-context/
│   ├── project-profile.md              (seeded)
│   ├── glossary.md                     (seeded)
│   ├── stakeholder-map.md              (seeded)
│   ├── system-landscape.md             (seeded)
│   └── decision-log.md                 (seeded)
├── tl-output/                          (empty; .gitkeep)
├── qa-output/                          (empty; .gitkeep)
├── dev-output/                         (empty; .gitkeep)
└── doc-output/                         (empty; .gitkeep)
```

Seed `shared-context/` templates from `${CLAUDE_PLUGIN_ROOT}/templates/shared-context/`. Stamp `generated_at: <today>` and `status: Draft` on each. Skip files that already exist.

## 4. Report

Print the tree that now exists. Note that original source files are never moved or copied — Delivery-OS only indexes and summarizes them. Give the next step:

```
✓ Delivery-OS workspace scaffolded.

Container:  ./<name>/
Sibling of: .jetrix/  (Jetrix wiring, if bound)

Layout:
  <name>/ba-output/, artifacts/, context/, shared-context/ (5 seeded templates),
        tl-output/, qa-output/, dev-output/, doc-output/

Next:
  cd <name>
  BA:  /ba:scope  →  /ba:features
  TL:  /tl:map (brownfield)  or  /tl:scaffold (greenfield)
  QA:  /qa:audit
  Dev: /dev:build FEAT-<n>
  Doc: /doc:proposal / /doc:magic-board / /doc:walkthrough / /doc:workflow
```

Keep it idempotent — re-runs never clobber existing work; they only fill in missing pieces.
