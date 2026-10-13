# Scope Document Template — Changelog

Tracks the bundled `scope-document-template.docx`. Versioned independently of the plugin so template edits are auditable across plugin releases.

The version here is mirrored in `manifest.json` (`template_version`) and should be bumped on every change using semver:
- **major** — section added/removed/reordered (changes the `conforms_section_order` contract; coordinate with `ba-extraction` and `scope.md`).
- **minor** — new optional field, table column, or guidance.
- **patch** — wording, branding, styling, typo fixes (no structural change).

## 2.0.0 — 2026-10-12
**Major — two sections added, `conforms_section_order` changed.** Markdown structure only;
`scope-document-template.docx` is unchanged, so `sha256` and `bytes` are the same.

- **§0 What We Understand This To Be** — a half-page understanding brief under the cover
  block, ahead of §1. The cheapest correction point in the engagement: a reader who
  disagrees with it disagrees in two minutes, while the same disagreement found at §3.7
  costs a rewrite.
- **§4b Global Non-Functional Requirements & Constraints** — device and browser reach,
  language and locale, data residency and retention, volume and concurrency, availability,
  accessibility, regulatory. Cross-cutting statements belonged to no module and were being
  dropped; this is where they live.

Both sections are **omitted when the sources carry nothing for them**, so an engagement
that produces neither still conforms.

Coordinated with `plugins/ba/skills/ba-extraction/SKILL.md` (structure list §1b and §5b)
and `templates/ba/scope.md`, per the README's major-change rule.

**Not done here:** the `delivery-os` plugin version in `marketplace.json` is unchanged, so
teams do not receive this yet. Bump it at release time.

## 1.0.0 — 2026-06-18
- Initial bundling of the Techjays D&D Scope Document Template into `delivery-os-core`.
- Source: D&D Documentation pack, "02 - Scope Document Template.docx".
