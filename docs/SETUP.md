# Delivery OS — Setup (shared)

This is the **common setup guide** for every Techjays Delivery OS plugin (`ba`, `tl`, and the rest). Individual plugin READMEs link here instead of repeating these steps, so there's one place to keep current. It covers two things every plugin shares: **installing the plugin** and **initializing a project workspace** with `/delivery-os:init`.

> **The one thing to understand first:** installing a plugin does **not** touch your project. It only makes the commands available. Your project folders are created later, by an explicit command, and only when you ask. For the fuller end-to-end walkthrough (with a first BA run), see [ONBOARDING.md](../ONBOARDING.md).

---

## Prerequisites

- **Claude Code** (CLI, desktop, or IDE extension) — Delivery OS ships as a Claude Code plugin marketplace.
- Access to the `techjays/claude-delivery-os` repository (or the git host it's published to).

---

## Step 1 — Add the marketplace and install the core

Every plugin depends on the shared **core** (`delivery-os`), which carries the document contract, shared vocabulary, the `/delivery-os:init` scaffolder, and the canonical templates. **Install it first**, once per machine:

```text
/plugin marketplace add techjays/claude-delivery-os
/plugin install delivery-os@techjays-delivery-os
```

(Replace `techjays/claude-delivery-os` with the actual git host/repo if it differs.)

This downloads the plugins into Claude Code's **own cache** (`~/.claude/plugins/…`) — *not* your project folder. It registers the commands so they appear when you type `/`, and nothing else: no files are created in your project, nothing is analyzed.

## Step 2 — Install the plugin(s) you need

Add whichever domain agents you want. Each is an independent install on top of the core:

```text
/plugin install ba@techjays-delivery-os      # Business Analyst — /ba:scope
/plugin install tl@techjays-delivery-os      # Technical Lead    — /tl:review
```

> **Team rollout:** instead of each person installing by hand, commit the marketplace + `enabledPlugins` block into a project's `.claude/settings.json` so teammates are prompted to enable them automatically. See the [README](../README.md#roll-out-to-a-team-recommended) for the exact JSON.

---

## Step 3 — Initialize a project workspace (`/delivery-os:init`)

Most Delivery OS work lives in a **single named container folder** so you can see exactly what Delivery OS owns (and delete one folder for a clean slate). That folder is created **only** when you run `init` inside the directory where you want it:

```text
/delivery-os:init my-client-project
```

This scaffolds:

```text
my-client-project/
├── README.md            ← what's in here + how to use it (the workspace manifest)
├── intake.index.md      ← living source registry (BA intake keeps it current; you can edit it)
├── artifacts/           ← empty — generated summaries land here, in categories created on demand
├── shared-context/      ← seeded starter files (project-profile, glossary, stakeholder-map,
│                          system-landscape, decision-log) that every agent reads
├── ba-output/           ← BA deliverables; register files appear on the first /ba:scope
│   └── intake-runs/
└── final/               ← approved, client-facing deliverables
```

Key properties:
- **Idempotent** — re-running `init` never overwrites existing work; if the folder already holds a workspace it stops and reports rather than clobbering.
- **Reference-only** — your original source files are never moved or copied into the workspace; Delivery OS only *indexes and summarizes* them. They stay where they are.
- **No rigid taxonomy to pre-sort into** — you keep files wherever they live and tell the agents where they are.
- **Per-agent output folders are created on demand.** `init` seeds `shared-context/` and `ba-output/`; other agents create their own output folder the first time they run (e.g. the TL agent creates `tl-output/` on its first review).

If a command needs a workspace and none exists, it will tell you to run `/delivery-os:init` first.

### Do I always need to run `init`?

It depends on the plugin:

| Plugin | Needs a workspace? |
|--------|--------------------|
| `ba` (`/ba:scope`) | **Yes** — intake reads/writes `intake.index.md` and the `ba-output/` deliverables. Run `init` first. |
| `tl` (`/tl:review`) | **Optional** — it can review any document standalone. With a workspace it writes to `tl-output/` and uses `ba-output/scope.md` + `shared-context/` as context; without one it writes the report beside the reviewed document. |

Check the individual plugin's README for which mode applies.

---

## Where everything lives — the mental model

```
PLUGIN CACHE (read-only)        YOUR ORIGINALS (untouched)      THE WORKSPACE (created by init + agents)
~/.claude/plugins/…             D:\acme\…              ─ref─►    my-client-project/
  commands / agents / skills    (never copied/moved)              intake.index.md · artifacts/ · shared-context/
                                                                  ba-output/ · tl-output/ · final/
```

- **Plugin files** = the program. Installed once, never edited by you.
- **Your originals** = stay exactly where they are. Delivery OS only *reads* them.
- **Workspace files** = the index + summaries + outputs — a knowledge layer *over* your files, not a copy. Because every agent writes only to these standard paths, outputs from one agent are reliably consumed by the next.

---

## Next steps

- **Business Analyst:** point intake at your material — `/ba:scope add "transcripts in <folder/link>, requirements in <folder/link>"`. See [ONBOARDING.md](../ONBOARDING.md) for the full first-run walkthrough.
- **Technical Lead:** review a spec — `/tl:review docs/tech-spec.md`. See [plugins/tl/tl_readme.md](../plugins/tl/tl_readme.md).
