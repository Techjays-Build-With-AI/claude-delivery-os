---
description: Scaffold the Delivery-OS working tree at `.jetrix/` root — role folders (ba/ tl/ qa/ dev/ doc/), shared-context/ (seeded), features/ (empty), tasks/ (empty). No <slug>/ wrapper. Entire `.jetrix/` is gitignored. Idempotent — never clobbers existing files. Requires `.jetrix/` to already exist (via `/jetrix:init`).
argument-hint: ""
---

# /delivery-os:init

Scaffold the Delivery-OS working tree at `<workspace>/.jetrix/`. Nested inside `.jetrix/` — the entire folder is gitignored (via `/jetrix:init`). Sync back to Jetrix via `/jetrix:push`; hydrate from Jetrix via `/jetrix:pull`.

**Layout — v2.0 (role-centric, no `<slug>/` wrapper):**

```
<workspace>/
└── .jetrix/                    ← gitignored (whole folder)
    ├── project.json            (from /jetrix:init)
    ├── connection-map.md       (from /jetrix:init if the portal built one)
    ├── cache/                  (from /jetrix:init — repolocation, sync-state)
    │
    ├── shared-context/                 ← cross-role context (seeded)
    ├── ba/                     ← Business Analyst outputs
    ├── features/               ← Feature bundles (BA authors, TL enriches, Dev delivers)
    ├── tl/                     ← Tech Lead outputs (reviews, maturity, code-map registry)
    ├── qa/                     ← QA outputs (gates, audits, health)
    ├── doc/                    ← Documentation deliverables
    └── tasks/                  ← Non-feature MC tasks
```

The per-feature `dev/` sub-tree lives under `features/<slug>/dev/` (owned by the feature). There is **no** top-level `dev/` folder — dev has one workspace-level file, `features/tracker.md`, and everything else is per-feature.

Read the `delivery-os-conventions` skill first if it's not already in context.

## 1. Precheck — .jetrix/ must exist

`<cwd>/.jetrix/` must already exist (`/jetrix:init` writes it with `project.json` + `cache/`). If missing → stop with `Run /jetrix:init first — this command scaffolds the working tree INSIDE .jetrix/, but does not create .jetrix/ itself.`

## 2. Rerun handling

If the workspace has already been scaffolded (`.jetrix/ba/` or `.jetrix/shared-context/decision-log.md` exists) → treat as an existing Delivery-OS workspace. **Fill in only missing pieces; never clobber existing files.** The seeded templates in `shared-context/` are copied only when the destination file is absent.

## 3. Create the folder tree

Under `<cwd>/.jetrix/`, create (all idempotent — never overwrite existing files):

```
.jetrix/
├── README.md                          (seeded — the map, "what lives where")
│
├── shared-context/
│   ├── project-profile.md             (seeded from template)
│   ├── glossary.md                    (seeded)
│   ├── stakeholder-map.md             (seeded)
│   ├── system-landscape.md            (seeded)
│   ├── decision-log.md                (seeded — append-only DEC-###)
│   └── baseline-profile.md            (seeded — optional QA baseline override)
│
├── ba/
│   ├── intake.index.md                (seeded)
│   ├── scope.md                       (empty; .gitkeep)
│   ├── client-questions.md            (empty; .gitkeep)
│   ├── artifacts/                     (empty; .gitkeep — raw intake by category)
│   ├── registers/                     (empty; .gitkeep — 8 canonical registers)
│   ├── logs/                          (empty; .gitkeep — 4 canonical logs)
│   ├── intake-runs/                   (empty; .gitkeep)
│   └── reviews/                       (empty; .gitkeep)
│
├── features/                          (empty; .gitkeep — per-feature bundles land here)
│
├── tl/
│   ├── code-map-registry.md           (empty; .gitkeep — feature ↔ app-repo map)
│   ├── reviews/                       (empty; .gitkeep)
│   └── maturity/                      (empty; .gitkeep)
│
├── qa/
│   ├── quality-gates.md               (empty; .gitkeep — the harness contract)
│   ├── audits/                        (empty; .gitkeep)
│   ├── health/                        (empty; .gitkeep)
│   └── escalations/                   (empty; .gitkeep)
│
├── doc/
│   ├── decks/                         (empty; .gitkeep — pptx)
│   ├── walkthroughs/                  (empty; .gitkeep — html)
│   ├── workflows/                     (empty; .gitkeep — html)
│   └── boards/                        (empty; .gitkeep — html)
│
└── tasks/                             (empty; .gitkeep — non-feature MC tasks)
```

Seed templates from `${CLAUDE_PLUGIN_ROOT}/templates/` (relative to the `delivery-os-core` plugin root):

| Target                                    | Template                                    |
|-------------------------------------------|---------------------------------------------|
| `.jetrix/README.md`                       | `templates/workspace-readme.md`             |
| `.jetrix/shared-context/project-profile.md`       | `templates/shared-context/project-profile.md`       |
| `.jetrix/shared-context/glossary.md`              | `templates/shared-context/glossary.md`              |
| `.jetrix/shared-context/stakeholder-map.md`       | `templates/shared-context/stakeholder-map.md`       |
| `.jetrix/shared-context/system-landscape.md`      | `templates/shared-context/system-landscape.md`      |
| `.jetrix/shared-context/decision-log.md`          | `templates/shared-context/decision-log.md`          |
| `.jetrix/shared-context/baseline-profile.md`      | `templates/baseline-profile.md`             |
| `.jetrix/ba/intake.index.md`              | `templates/intake.index.md`                 |

Stamp `generated_at: <today>` and `status: Draft` on each seeded doc where the frontmatter has those fields. **Skip files that already exist** — never overwrite the teammate's work.

(v2.0 note — `shared-context/` keeps its name; only `-output`-suffixed role folders were renamed, and the workspace `<slug>/` wrapper was dropped.)

## 4. Report

Print the tree that now exists (only new folders/files; skip ones that already existed). Give the next step:

```
✓ Delivery-OS workspace scaffolded (v2.0 layout).

Location:  ./.jetrix/   (gitignored — local working copy)

Layout:
  .jetrix/shared-context/         (5 seeded templates + baseline-profile)
  .jetrix/ba/             (intake.index seeded; registers/ logs/ reviews/ artifacts/ intake-runs/)
  .jetrix/features/       (empty — per-feature bundles created by /ba:features)
  .jetrix/tl/             (reviews/ maturity/ code-map-registry.md)
  .jetrix/qa/             (audits/ health/ escalations/ + quality-gates placeholder)
  .jetrix/doc/            (decks/ walkthroughs/ workflows/ boards/)
  .jetrix/tasks/          (empty — non-feature MC tasks)

Next:
  BA:  /ba:scope  →  /ba:features
  TL:  /tl:code-map (brownfield)  or  /tl:scaffold (greenfield)
  QA:  /qa:audit
  Dev: /dev:build FEAT-<n>
  Doc: /doc:proposal · /doc:magic-board · /doc:walkthrough · /doc:workflow
```

Keep it idempotent — re-runs never clobber existing work; they only fill in missing pieces.
