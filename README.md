# Techjays Delivery OS

An internal **Claude Code plugin marketplace** that standardizes how Techjays runs delivery — from raw client inputs to structured, reusable delivery documents.

This repository is distributed once across the org. Teams add it as a marketplace and enable the agent plugins they need. Every agent writes to a shared **document contract**, so outputs from one agent are reliably consumed by the next.

## What's in here

| Plugin | Namespace | Status | Provides |
|--------|-----------|--------|----------|
| `delivery-os` (core) | `/delivery-os:` | ✅ MVP | Project scaffolding, the cross-agent document contract, shared vocabulary, canonical templates. **Install first.** |
| `ba` | `/ba:` | ✅ MVP | Business Analyst Agent — discovery intake, classification, living scope, registers. `/ba:intake` |
| `doc` | `/doc:` | 🔜 Phase 2 | Doc Agent — proposal, walkthrough, SRS, SoW, executive summary |
| `tl` | `/tl:` | ✅ MVP | TL Agent — scored technical-spec review for applied AI systems (architecture, system/feature flows, data schema, API contracts, libraries, AI observability/evals/feedback/compliance, infra, CI/CD, cost). `/tl:review` |
| `qa` | `/qa:` | 🔜 Phase 4 | QA Agent |

> **Why separate plugins?** In Claude Code a command's namespace comes from the plugin name. Splitting by domain is what gives the spec's exact commands — `/ba:intake`, `/tl:review`, `/doc:proposal` — while still shipping as one installable bundle.

## Install (individual user)

```text
/plugin marketplace add techjays/claude-delivery-os
/plugin install delivery-os@techjays-delivery-os
/plugin install ba@techjays-delivery-os
/plugin install tl@techjays-delivery-os
```

(Replace `techjays/claude-delivery-os` with the actual git host/repo once published.)

## Roll out to a team (recommended)

Commit `examples/team-settings.json` (below) into a project's `.claude/settings.json`. When teammates trust the repo, Claude Code prompts them to add the marketplace and enable the listed plugins automatically:

```json
{
  "extraKnownMarketplaces": {
    "techjays-delivery-os": {
      "source": { "source": "github", "repo": "techjays/claude-delivery-os" }
    }
  },
  "enabledPlugins": {
    "delivery-os@techjays-delivery-os": true,
    "ba@techjays-delivery-os": true,
    "tl@techjays-delivery-os": true
  }
}
```

For **org-wide enforcement**, an admin can pin approved marketplaces via managed settings (`strictKnownMarketplaces`) so only Delivery OS plugins are installable.

## Quick start (using it)

```text
/delivery-os:init my-client-project     # scaffold ONE container folder (no rigid sub-folders)
/ba:intake add "transcripts in <folder/link>, requirements in <folder/link>, archive in <folder> for reference only"
/ba:intake mode=incremental             # re-run as new material arrives
/tl:review docs/tech-spec.md            # score a technical spec; writes a timestamped report to tl-output/
```

You don't pre-sort files. Tell intake where your originals live; it **references them in place** (never copies/moves), summarizes each into `artifacts/`, registers them in `intake.index.md`, and builds the scope. `/ba:intake` modes: `auto` (default) · `incremental` · `full-refresh` · `dry-run` · `index-only` · `classify-only`.

**Reviewing a technical spec** is independent of intake — point `/tl:review` at any spec / architecture / HLD / SRS doc (`.md`, `.docx`, `.pdf`) and it produces an interactive HTML report plus a Markdown artifact, scoring each area out of 10 with findings and fixes. Each run is timestamped, so re-reviews never overwrite earlier ones. See [plugins/tl/tl_readme.md](plugins/tl/tl_readme.md) for the full guide and a worked example.

> 🧭 **New to the plugin? Read [ONBOARDING.md](ONBOARDING.md)** — it explains the three stages (install → init → intake), what each does to your repo, and walks through a first run. Key point: **installing the plugin does not create anything in your project** — folders appear only when you run `/delivery-os:init`.

## How documents stay shareable

All agents honor `delivery-os-conventions` (in the core plugin), which fixes:
- the **workspace layout** (where inputs live, where each agent writes),
- a **frontmatter standard** on every doc (`schema_version`, `produced_by`, `status`, …),
- **stable IDs** (`REQ-001`, `WF-001`, `BR-001`, …) so cross-references survive across agents and weeks,
- a **controlled vocabulary** (artifact statuses, confidence values, usage modes).

The TL agent (and the Doc agent, a later phase) read `ba-output/scope.md` and `shared-context/` as input context when a workspace exists — no re-analysis. The TL agent also runs standalone on any spec document, with or without a workspace.

## Repository layout

```text
.claude-plugin/marketplace.json      # registers every plugin in this bundle
plugins/
  delivery-os-core/                  # name: "delivery-os" — contract + templates + /delivery-os:init
    templates/                       #   workspace-readme, intake.index registry, scope.md, registers,
    templates/d&d/scope-document/    #   the bundled branded Scope Document .docx (versioned)
  ba/                                # name: "ba" — /ba:intake + ba-agent + skills
  tl/                                # name: "tl" — /tl:review + tl-agent + tl-spec-review skill (HTML report template)
examples/sample-project/             # ready-to-run test workspace (see TESTING.md)
examples/tl-review-test/             # sample spec + generated interactive review report
examples/team-settings.json          # copy into a project's .claude/settings.json
docs/D&D Documentation/              # the Techjays D&D deliverable templates (style authority)
requirement.md                       # source requirements spec
```

## Contributing a new agent (doc / qa)

1. Add `plugins/<domain>/` with a `.claude-plugin/plugin.json` whose `name` is the namespace (e.g. `doc`).
2. Add commands under `commands/`, the worker under `agents/`, heavy detail under `skills/`.
3. Depend on the contract: read `delivery-os-conventions`, read inputs from `ba-output/` and `shared-context/`, write to `<domain>-output/`.
4. Register the plugin in `.claude-plugin/marketplace.json` and bump versions.
