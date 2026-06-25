# Scope Document Template — Changelog

Tracks the bundled `scope-document-template.docx`. Versioned independently of the plugin so template edits are auditable across plugin releases.

The version here is mirrored in `manifest.json` (`template_version`) and should be bumped on every change using semver:
- **major** — section added/removed/reordered (changes the `conforms_section_order` contract; coordinate with `ba-extraction` and `scope.md`).
- **minor** — new optional field, table column, or guidance.
- **patch** — wording, branding, styling, typo fixes (no structural change).

## 1.0.0 — 2026-06-18
- Initial bundling of the Techjays D&D Scope Document Template into `delivery-os-core`.
- Source: D&D Documentation pack, "02 - Scope Document Template.docx".
