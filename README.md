# Techjays Delivery OS

An internal **Claude Code plugin marketplace** that standardizes how Techjays runs delivery — from raw client inputs to structured, reusable delivery documents.

This repository is distributed once across the org. Teams add it as a marketplace and enable the agent plugins they need. Every agent writes to a shared **document contract**, so outputs from one agent are reliably consumed by the next.

## What's in here

| Plugin | Namespace | Status | Provides |
|--------|-----------|--------|----------|
| `delivery-os` (core) | `/delivery-os:` | ✅ MVP | Project scaffolding, the cross-agent document contract, shared vocabulary, canonical templates. **Install first.** |
| `ba` | `/ba:` | ✅ MVP | Business Analyst Agent — discovery intake, classification, living scope, registers. `/ba:intake` |
| `doc` | `/doc:` | 🔜 Phase 2 | Doc Agent — proposal, walkthrough, SRS, SoW, executive summary |
| `tl` | `/tl:` | 🔜 Phase 3 | TL Agent — architecture/code/security/observability/compliance review, maturity score |
| `qa` | `/qa:` | 🔜 Phase 4 | QA Agent |

> **Why separate plugins?** In Claude Code a command's namespace comes from the plugin name. Splitting by domain is what gives the spec's exact commands — `/ba:intake`, `/doc:proposal`, `/tl:code-review` — while still shipping as one installable bundle.

## Install (individual user)

```text
/plugin marketplace add techjays/claude-delivery-os
/plugin install delivery-os@techjays-delivery-os
/plugin install ba@techjays-delivery-os
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
    "ba@techjays-delivery-os": true
  }
}
```

For **org-wide enforcement**, an admin can pin approved marketplaces via managed settings (`strictKnownMarketplaces`) so only Delivery OS plugins are installable.

## Quick start (using it)

```text
/delivery-os:init my-client-project     # scaffold the workspace
# …drop source files into raw-artifacts/ and fill in intake.index.md…
/ba:intake                              # build the living scope document
/ba:intake mode=incremental             # re-run as new artifacts arrive
```

`/ba:intake` modes: `auto` (default) · `incremental` · `full-refresh` · `dry-run` · `index-only` · `classify-only`.

## How documents stay shareable

All agents honor `delivery-os-conventions` (in the core plugin), which fixes:
- the **workspace layout** (where inputs live, where each agent writes),
- a **frontmatter standard** on every doc (`schema_version`, `produced_by`, `status`, …),
- **stable IDs** (`REQ-001`, `WF-001`, `BR-001`, …) so cross-references survive across agents and weeks,
- a **controlled vocabulary** (artifact statuses, confidence values, usage modes).

The Doc and TL agents (later phases) read `ba-output/scope.md` and `shared-context/` as their primary inputs — no re-analysis.

## Repository layout

```text
.claude-plugin/marketplace.json      # registers every plugin in this bundle
plugins/
  delivery-os-core/                  # name: "delivery-os" — contract + templates + /delivery-os:init
  ba/                                # name: "ba" — /ba:intake + ba-agent + skills
examples/team-settings.json          # copy into a project's .claude/settings.json
requirement.md                       # source requirements spec
```

## Contributing a new agent (doc / tl / qa)

1. Add `plugins/<domain>/` with a `.claude-plugin/plugin.json` whose `name` is the namespace (e.g. `doc`).
2. Add commands under `commands/`, the worker under `agents/`, heavy detail under `skills/`.
3. Depend on the contract: read `delivery-os-conventions`, read inputs from `ba-output/` and `shared-context/`, write to `<domain>-output/`.
4. Register the plugin in `.claude-plugin/marketplace.json` and bump versions.
