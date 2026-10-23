---
description: Seed the minimum Delivery-OS working tree inside `.jetrix/` — `cache/` and `shared-context/decision-log.md`. Nothing else is created up front; every other folder is created by the command that first writes into it, so the tree doubles as an honest progress indicator. Entire `.jetrix/` is gitignored. Idempotent — never clobbers existing files. USUALLY RUNS AUTOMATICALLY as the final step of `/jetrix:init`; invoke directly to repair a workspace or to finish one bound with `--skip-scaffold`. Requires `.jetrix/` to already exist (via `/jetrix:init`).
argument-hint: ""
---

# /delivery-os:init

Seed the Delivery-OS working tree at `<workspace>/.jetrix/`. The whole folder is gitignored (via `/jetrix:init`). Sync to the bound tracker via `/jetrix:push`; hydrate via `/jetrix:pull`.

> **Usually you don't run this directly.** `/jetrix:init` runs this logic inline as its final step. Reach for it when you want to:
> - Repair a workspace where `cache/` or `decision-log.md` was deleted by accident.
> - Finish a workspace bound with `/jetrix:init --skip-scaffold`.

Read the `delivery-os-conventions` skill first if it's not already in context.

## The rule: create nothing you cannot fill

**A folder is created by the command that writes into it, not in advance.** Seeding an empty tree costs real money in three ways, and we measured all three on a live workspace after a full plan → build → commit:

- **16 of 27 directories held nothing but a `.gitkeep`.** A `.gitkeep` exists to make git track an empty directory — and `/jetrix:init` puts the entire `.jetrix/` in `.gitignore`. Git never saw one of them. They were doing a job that is impossible by construction.
- **Only 3 of 30 seeded files carried data.** The other 27 were empty tables and blank frontmatter.
- **An empty template is a second copy of a schema that can drift from the contract.** It already had: `system-landscape.md` shipped as a `System · Purpose · Owner · Integration Touchpoints` table while `blocker-fold.md` writes an **Actors** section the template never defined.

A seeded file that lies about existing is worse than no file. `qa/quality-gates.md` was seeded as a 9-line stub, which forced a rule into `/dev:build` Stage 4 — *"a file with no `harness_status` key is the scaffold placeholder, the same thing as missing."* We seeded a lie, then wrote a rule to detect it.

**Seeding is not the same as existing.** Not creating an empty `glossary.md` here is not a claim that glossaries don't matter — it is the instruction that `/ba:scope` creates it **with content**, from real sources.

## 1. Precheck — `.jetrix/` must exist

`<cwd>/.jetrix/` must already exist (`/jetrix:init` writes it with `project.json` + `cache/`). Missing → stop with `Run /jetrix:init first — this command seeds the tree INSIDE .jetrix/, it does not create .jetrix/ itself.`

## 2. Create the tree

Under `<cwd>/.jetrix/`, create — idempotent, never overwriting:

```
.jetrix/
├── project.json                  (written by /jetrix:init)
├── connection-map.md             (if the tracker had one, or /jetrix:init §9a asked for it)
├── cache/
│   ├── repolocation.json         local repo paths
│   └── sync-state.json           drift hashes — `{}` when new
└── shared-context/
    └── decision-log.md           append-only DEC-###
```

**Three directories, four files, every one of them carrying data.** `decision-log.md` is seeded from `${CLAUDE_PLUGIN_ROOT}/templates/shared-context/decision-log.md`; the two cache files are written by `/jetrix:init`.

`decision-log.md` is the single exception to the rule above, and it earns it: it is referenced in **38 files**, more than anything else in the system, it is append-only, and **its first writer varies** — `/ba:scope` or `/dev:plan`, whichever the user reaches first. No single command can be made responsible for creating it.

Stamp `generated_at: <today>` on the seeded file if its frontmatter has that field. **Skip anything that already exists.**

## 3. Who creates everything else

Not a to-do list — a map of ownership. Each row is created, with content, the first time its command runs.

| Path | Created by | Holds |
|---|---|---|
| `requirements/<slug>/` | `/ba:scope` | one requirement: scope, sources, ledger, artifacts, registers, reviews, features |
| `shared-context/glossary.md` | `/ba:scope` | terms, project-wide |
| `shared-context/stakeholder-map.md` | `/ba:scope` | people — who can answer a `ledger.md` row |
| `shared-context/system-landscape.md` | `/ba:scope` | systems and their touchpoints |
| `shared-context/data.md` · `integrations.md` | `/ba:scope` | `DATA-###` · `INT-###` — the system's, not one requirement's |
| `shared-context/coding-standards.md` § `<repo>` | `/tl:code-map` | what `/dev:build` Stage 0 gates on |
| `code-map-registry.md` | `/tl:code-map` | one row per mapped repo — at the `.jetrix/` root |
| `qa/` | `/qa:audit` | audits, then the gates `/qa:setup` promotes to Active |
| `doc/` | `/doc:*` | decks, walkthroughs, workflows, boards |
| `tasks/` | `/jetrix:pull task` | work that is not a requirement — a bug, a one-off ticket |
| `requirements/<slug>/features/<slug>/units/<repo>/` | `/dev:plan` | one folder per repo — the build state, always, even at N=1 |

**There is no `tl/` folder.** `/tl:code-map` is the only TL command a user types, and its registry belongs at the `.jetrix/` root with the rest of the wiring — `project.json`, `connection-map.md`, `cache/`. A folder named after a role only invites people to look for the others.

**`baseline-profile.md` is not a workspace file.** It is QA's org-wide tooling floor, `scope: org-default`, identical everywhere — so seeding it meant every workspace overriding the default with a copy of the default. It lives in the plugin; a workspace copy appears only on a genuine override.

**The tree becomes a progress indicator.** `requirements/` existing means discovery has started. `qa/` existing means the harness was audited. An empty scaffold tells you nothing, because it looks the same on day one and day thirty.

## 4. Report

Print only what this run created.

```
✓ Workspace ready.

  .jetrix/cache/                  repolocation · sync-state
  .jetrix/shared-context/         decision-log.md

  Everything else is created by the command that writes it.

Next:
  /ba:scope add "<where your material lives>"    start a requirement
  /tl:code-map                                   map repos already on disk
```

**This command does not know what the workspace is for**, so it names both entry points and stops. `/jetrix:init` has looked at the project — and at the bound tracker, whether that is Jetrix, Jira, ClickUp or another — so it is the one that can name a single next step.

Re-runs fill in only what is missing. They never clobber.
