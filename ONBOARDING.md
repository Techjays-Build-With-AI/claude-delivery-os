# Getting Started with Techjays Delivery OS

This guide explains **how the plugin works end to end** — what happens when you install it, where files get created, and how to run your first discovery intake.

> **The one thing to understand first:** installing the plugin does **not** touch your project. It only makes the commands available. Your project folders are created later, by an explicit command, and only when you ask.

---

## The three stages

There are three separate stages. Nothing is written into your repository until **you** run a command.

### Stage 1 — Install (one-time, per machine)

When you install the plugin, Claude Code downloads it into its **own cache** (`~/.claude/plugins/…`) — *not* your project folder.

```text
/plugin marketplace add techjays/claude-delivery-os
/plugin install delivery-os@techjays-delivery-os
/plugin install ba@techjays-delivery-os
```

**What this does:**
- Registers the commands so `/ba:scope` and `/delivery-os:init` appear when you type `/`.
- Registers the `ba-agent` and its skills.

**What this does NOT do:**
- ❌ Does not create any folder in your project.
- ❌ Does not run anything or analyze anything.

Think of it like installing an app — opening the installer doesn't create your documents.

### Stage 2 — Initialize a project workspace (per project)

The standard folder structure is created **only** when you run this inside a project:

```text
/delivery-os:init my-client-project
```

This creates **one named container folder** (so you can see exactly what Delivery OS owns):

```text
my-client-project/
├── README.md                ← what's in here + how to use it
├── intake.index.md          ← source registry (kept up to date by intake; you can edit it)
├── artifacts/               ← empty — summaries land here, in categories created on demand
├── shared-context/          ← seeded with starter files
├── ba-output/               ← stays empty until your first intake
└── final/
```

There is **no `raw-artifacts/` taxonomy to sort into** — you keep your files wherever they already are and just tell intake where they live. It is **idempotent** — re-running it never overwrites existing work.

### Stage 3 — Run the Business Analyst Agent

Tell intake where your material is, in one line — no pre-sorting:

```text
/ba:scope add "meeting transcripts in D:\acme\meetings, client requirements at <drive-link>, invoice archive in D:\acme\invoices for reference only"
```

This **invokes the agent**, which:
1. Parses your declaration into sources and **classifies** each (large/reference folders are not deep-analyzed).
2. **References** each original where it lives — it never copies, moves, or deletes your files.
3. **Summarizes** each eligible source into `artifacts/<category>/…summary.md` and registers it in `intake.index.md`.
4. **Extracts** requirements, workflows, business rules, examples — from the summaries.
5. Writes the living **scope document** and registers into `ba-output/`, and updates `shared-context/`.
6. Produces an **intake run summary** you can review.

Add more material or re-run any time — it processes only what's new or changed:

```text
/ba:scope add "new requirements doc at D:\acme\reqs-v2.docx"
/ba:scope mode=incremental
```

---

## Where files live — the mental model

```
PLUGIN CACHE (read-only)        YOUR ORIGINALS (untouched)      THE WORKSPACE (created by Delivery OS)
~/.claude/plugins/ba/...        D:\acme\meetings\...            my-client-project/
  commands/intake.md  ─run─►    D:\acme\reqs\...      ─ref─►      intake.index.md   ← registry of where originals live
  agents/ba-agent.md            (never copied/moved)             artifacts/…summary.md ← generated summaries
  skills/...                                                     ba-output/scope.md  ← the deliverable
```

- **Plugin files** = the program. Installed once, never edited by you.
- **Your originals** = stay exactly where they are. Delivery OS only *reads* them.
- **Workspace files** = the index + summaries + outputs. This is a knowledge layer *over* your files, not a copy of them.

Because the agent only writes to standard workspace paths, the documents are **shareable**: the future Doc and TL agents read `ba-output/scope.md` and `shared-context/` directly — no re-analysis, no guessing where things are.

---

## Your first run — step by step

1. **Install** the marketplace and the `delivery-os` + `ba` plugins (Stage 1).
2. **Open** the folder where you want the workspace to live.
3. **Scaffold:** `/delivery-os:init my-client-project` (Stage 2) — creates the container.
4. **Point intake at your material** (wherever it already is) and let it organize:
   ```text
   /ba:scope add "transcripts in <folder/link>, requirements in <folder/link>, big archive in <folder> for reference only"
   ```
5. **Review:** read the run summary in `ba-output/intake-runs/run-001.md`, then open `ba-output/scope.md`.
6. **Iterate:** as new material arrives, `/ba:scope add "…"` or `/ba:scope mode=incremental`.

---

## FAQ

**Does installing the plugin change my repo?**
No. Install only registers commands. Folders appear when you run `/delivery-os:init`.

**Do I have to run `init` before `intake`?**
Yes — `intake` needs `intake.index.md` to exist. If it's missing, the command tells you to run `/delivery-os:init` first.

**Can I use this in an existing repo?**
Yes. `init` creates a single named container folder; it won't touch anything else. And your source files are never moved into it — they stay where they are.

**Does it move or copy my source files?**
No. Delivery OS is **reference-only**: it records where your originals live and generates summaries of them, but never copies, moves, or deletes the originals.

**Do I have to pre-sort my files into folders?**
No. That was the old model. Just tell intake where things are with `add "…"` and it organizes summaries into categories for you.

**Where do the templates come from?**
They ship inside the `delivery-os` (core) plugin and seed your workspace during `init`. You can edit your copies freely.

**What modes does intake support?**
`auto` (default) · `incremental` · `full-refresh` · `dry-run` · `index-only` · `classify-only`. See the [README](README.md) for what each does. Use `mode=dry-run` to preview changes without writing anything.

**Will it read my Google Drive automatically?**
Only if a Drive connector/MCP is available. If it isn't, the agent flags the source as `Access Required` and asks you to enable access or export the files locally — it never fabricates analysis of files it can't actually read.
