# Techjays Delivery OS

An internal **Claude Code plugin marketplace** that standardizes how Techjays runs delivery — from raw client inputs to structured, reusable delivery documents.

This repository is distributed once across the org. Teams add it as a marketplace and enable the agent plugins they need. Every agent writes to a shared **document contract**, so outputs from one agent are reliably consumed by the next.

## What's in here

| Plugin | Namespace | Status | Provides |
|--------|-----------|--------|----------|
| `delivery-os` (core) | `/delivery-os:` | ✅ MVP | Project scaffolding, the cross-agent document contract, shared vocabulary, canonical templates. **Install first.** |
| `ba` | `/ba:` | ✅ MVP | Business Analyst Agent — discovery intake, classification, living scope, registers; plus a paranoid feature-by-feature **scope review** (coverage scoring + example validation) with a question-resolution loop. `/ba:scope` · `/ba:review` · `/ba:resolve`. See [plugins/ba/ba_readme.md](plugins/ba/ba_readme.md). |
| `doc` | `/doc:` | ✅ MVP (proposal) | Documentation Agent — standardizes client-facing artifacts to the Techjays standard + style system. Shipping now: the client **proposal** (single-file, print-to-PDF HTML deck, branded from the client's domain, auto-drafted from the BA scope) the **magic board** (a Miro-style infinite-canvas walkthrough with a guided fly-through tour), and the **workflow document** (an interactive phased swimlane of the scope with hover tooltips, before/after value panels, and efficiency KPIs). `/doc:proposal` · `/doc:magic-board` · `/doc:workflow`. SRS, SoW, executive summary to follow. |
| `tl` | `/tl:` | ✅ MVP | TL Agent — scored technical-spec review for applied AI systems (architecture, system/feature flows, data schema, API contracts, libraries, AI observability/evals/feedback/compliance, infra, CI/CD, cost), plus a finding-resolution loop; feature planning & scaffold; and a read-only **project maturity audit** scoring a built system across code quality, test quality, infrastructure/ops, and security with per-finding evidence + Audit Confidence. `/tl:review` · `/tl:resolve` · `/tl:plan` · `/tl:scaffold` · `/tl:map` · `/tl:maturity` |
| `qa` | `/qa:` | 🔜 Phase 4 | QA Agent |

> **Why separate plugins?** In Claude Code a command's namespace comes from the plugin name. Splitting by domain is what gives the spec's exact commands — `/ba:scope`, `/tl:review`, `/doc:proposal` — while still shipping as one installable bundle.

## Install (individual user)

Pick **one** way to add the marketplace, then install the plugins. The marketplace name is `techjays-delivery-os` (from `.claude-plugin/marketplace.json`), so all `install` lines reference that name regardless of how you added it.

**Option A — from the published GitHub repo** (tracks the `main` branch):

```text
/plugin marketplace add Techjays-Build-With-AI/claude-delivery-os
```

**Option B — from a feature branch** (test changes before they're merged to `main`):

```text
/plugin marketplace add Techjays-Build-With-AI/claude-delivery-os@feat/your-branch-name
```

**Option C — from a local folder** (test your own working copy, no push needed) — point it at the repo root, which contains `.claude-plugin/marketplace.json`:

```text
/plugin marketplace add D:\Projects\Tools\claude-delivery-os
```

Then install the plugins (same for all options):

```text
/plugin install delivery-os@techjays-delivery-os
/plugin install ba@techjays-delivery-os
/plugin install doc@techjays-delivery-os
/plugin install tl@techjays-delivery-os
```

After editing files (local) or pushing new commits (GitHub), refresh without re-adding:

```text
/plugin marketplace update techjays-delivery-os
```

> **Switching sources** (e.g. from a branch or local folder to published `main`): remove first, then re-add — `/plugin marketplace remove techjays-delivery-os` then the Option-A line above. Verify installed commands anytime with `/help`.

> 📦 **Full step-by-step setup — install + `/delivery-os:init` — lives in [docs/SETUP.md](docs/SETUP.md).** It's the shared guide every plugin README links to, so the steps stay in one place.

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
    "doc@techjays-delivery-os": true,
    "tl@techjays-delivery-os": true
  }
}
```

For **org-wide enforcement**, an admin can pin approved marketplaces via managed settings (`strictKnownMarketplaces`) so only Delivery OS plugins are installable.

## Quick start (using it)

```text
/delivery-os:init my-client-project     # scaffold ONE container folder (no rigid sub-folders)
/ba:scope add "transcripts in <folder/link>, requirements in <folder/link>, archive in <folder> for reference only"
/ba:scope mode=incremental             # re-run as new material arrives
/ba:review                              # paranoid scope review of ba-output/scope.md; writes a dashboard to ba-output/scope-reviews/
/doc:proposal client="Acme" domain=acme.com   # branded, print-to-PDF proposal deck → doc-output/
/doc:magic-board topic="Acme invoice workflow"  # Miro-style walkthrough board with a guided tour → doc-output/
/doc:workflow project="Acme Onboarding"         # phased swimlane workflow doc (hover, before/after, KPIs) → doc-output/
/tl:review docs/tech-spec.md            # score a technical spec; writes a timestamped report to tl-output/
/tl:maturity repo=<path>                # read-only maturity score of a built project (4 domains + Audit Confidence)
```

You don't pre-sort files. Tell intake where your originals live; it **references them in place** (never copies/moves), summarizes each into `artifacts/`, registers them in `intake.index.md`, and builds the scope. `/ba:scope` modes: `auto` (default) · `incremental` · `full-refresh` · `dry-run` · `index-only` · `classify-only`.

**Reviewing the scope** before it goes out for estimate: `/ba:review` reads `ba-output/scope.md` (or any scope file you point it at), breaks it into features, and — like a paranoid BA — interrogates every thin line into concrete questions, scores each feature out of 10 on coverage depth across the nine D&D dimensions, and validates each against the client's shared examples. It writes an interactive HTML dashboard to `ba-output/scope-reviews/`; you then respond to the questions inside it, *Export responses*, and run `/ba:resolve` to close them and fold the answers back into the scope. Full guide: [plugins/ba/ba_readme.md](plugins/ba/ba_readme.md).

**Generating a client proposal:** `/doc:proposal client="Acme" domain=acme.com` produces a single-file, print-to-PDF HTML deck built to the Techjays proposal standard and style system. It pulls the client's logo from their domain and samples their brand accent, auto-drafts the problem/solution/value from `ba-output/scope.md` when a workspace exists (using the client's real numbers), and writes `doc-output/proposal-<client>-<timestamp>.html` — open it in Chrome/Edge and Save as PDF. Add free-text custom rules to tailor it (extra sections, tone, pricing, lean form). For a spatial walkthrough of a workflow or system, `/doc:magic-board topic="…"` builds a Miro-style infinite-canvas board with a guided next/next fly-through tour (drag to pan, scroll to zoom, `O` for overview), drafted from the BA scope when present. And `/doc:workflow project="…"` produces an interactive phased swimlane document of the scope — hover-over tooltips on each step, a per-phase before/after value panel (current pain → AI solution + hours saved), and efficiency KPIs. Full guide: [plugins/doc/doc_readme.md](plugins/doc/doc_readme.md).

**Reviewing a technical spec** is independent of intake — point `/tl:review` at any spec / architecture / HLD / SRS doc (`.md`, `.docx`, `.pdf`) and it produces an interactive HTML report plus a Markdown artifact, scoring each area out of 10 with findings and fixes. You then **close the findings**: respond to each one inside the HTML report, click *Export responses*, and run `/tl:resolve` on the downloaded file — the agent adjudicates each response, recomputes the verdict, logs decisions, and writes the next round. Each run is timestamped, so re-reviews never overwrite earlier ones. See [plugins/tl/tl_readme.md](plugins/tl/tl_readme.md) for the full guide and a worked example.

**Auditing a built project's maturity** is the third of three audits in Delivery OS — where `/tl:review` scores a design *document* and `/qa:audit` scores the *test harness*, `/tl:maturity` scores the *running system's reality* across four domains (Code Quality & Maintainability, Test Quality & Verifiability, Infrastructure & Operations, Security). It's **read-only**: it prefers the project's own enforced tooling as evidence, tags every finding `evidenced` or `attested`, reports a maturity score plus a separate **Audit Confidence**, and in preflight reminds you to run `/qa:audit` → `/qa:setup` if the mandatory tooling baseline (enforced lint, coverage gate, dependency + secret scanning) isn't yet in place. It never installs tooling or changes code — baseline gaps route back to QA.

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
  ba/                                # name: "ba" — /ba:scope + ba-agent + skills
  doc/                               # name: "doc" — /doc:proposal + doc-agent + doc-proposal skill (standard, style guide, HTML template)
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
