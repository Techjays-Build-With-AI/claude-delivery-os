---
doc_type: baseline-profile
schema_version: 1.0
produced_by: delivery-os
scope: org-default
coverage_floor: 70
generated_at: 2026-07-19
---

# Baseline profile — the mandatory tooling floor every repo must carry

This file is the **org standard**: the minimum set of quality instruments every project in the organization is required to have, and to *enforce*. It exists so that two things stay true across the whole portfolio:

1. **The delivery loop's "signed off" means something.** A green loop on a repo with no enforced linting, no coverage gate, and no secret/dependency scanning is a false green. The baseline is what makes verification trustworthy.
2. **Every project is judged against the same bar.** A .NET service and a Rails app are held to the *same capabilities* — even though the concrete tools differ.

Two agents read this file:

- **QA** (`/qa:audit`, `/qa:setup`) reads it to know what it must stand up, and flags every unmet mandatory item as a **mandatory gap** (not a discretionary recommendation).
- **`/tl:maturity`** reads it in preflight to decide whether the floor is in place — if it isn't, it routes to QA before scoring.

## The WHAT vs the HOW (why this file names no tools)

This profile lists **capabilities**, never tool names. "Linting enforced" is a capability; whether it's ESLint, RuboCop, or Roslyn analyzers is a **binding** the agent resolves from the detected stack at scan time (see `tl-maturity-audit/references/stack-bindings.md`). Keeping the *what* here and the *how* in the binding map is what lets one org standard govern every stack without drifting into a different profile per language.

## The mandatory floor

Each row is a capability, whether it is mandatory, and where it must be **enforced** (present-but-unenforced does not satisfy a mandatory item — an unenforced check can silently rot). `Yes*` = mandatory only where the surface exists (type-checking on typed stacks; a UI for e2e).

| ID | Capability | Mandatory | Enforced where | Notes |
|---|---|---|---|---|
| BL-01 | Linting configured, runs clean or on a known baseline | Yes | pre-commit + CI | the project's own ruleset is the agreed bar |
| BL-02 | Formatting with a `check` mode | Yes | pre-commit + CI | CI fails on unformatted code |
| BL-03 | Type / analyzer checks | Yes* | pre-commit + CI | typed stacks only |
| BL-04 | Unit test runner present, smoke green | Yes | CI | a single command runs it |
| BL-05 | Coverage measured **and threshold-enforced** | Yes | CI | build fails below `coverage_floor` |
| BL-06 | CI runs the checks and **gates merges** | Yes | CI | cheap-to-expensive order |
| BL-07 | Pre-commit hook re-checks lint/format/type before push | Yes | git hook | husky+lint-staged / pre-commit / lefthook |
| BL-08 | Dependency vulnerability scan | Yes | CI | no high/critical unaddressed |
| BL-09 | Secret scanning | Yes | CI + history | no committed secrets |
| BL-10 | Testing conventions documented | Yes | repo | where tests live, how to run each level |

## Rules

- **Mandatory items are not skippable per project.** QA may not silently `Skip` a mandatory gap; skipping one is an explicit `DEC-###` in `shared-context/decision-log.md` with a rationale (e.g. "BL-08 deferred — air-gapped internal tool, no external deps").
- **A workspace may tighten, never silently loosen.** A project's `shared-context/baseline-profile.md` override may raise `coverage_floor` or add capabilities. Lowering the floor or dropping a mandatory item is a human-approved `DEC-###`, never an edit.
- **`coverage_floor`** here is the org default (70). It is the *minimum* enforced percentage; a workspace override may raise it.
- Adding or changing a mandatory capability is an org-level decision, logged and versioned (`schema_version`).

## Where it lives

- **Org default:** this file, shipped in `delivery-os-core/templates/baseline-profile.md`.
- **Workspace override (optional):** `shared-context/baseline-profile.md` — read in preference to the default when present; may only tighten.
