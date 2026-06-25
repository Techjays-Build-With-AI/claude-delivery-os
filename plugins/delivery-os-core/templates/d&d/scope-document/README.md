# Scope Document Template (bundled)

This folder ships the **branded Techjays Scope Document** with the `delivery-os` (core) plugin so it travels with every install and is easy to version across releases.

```text
scope-document/
├── scope-document-template.docx   # the branded Word template (edit branding/styles here, in Word)
├── manifest.json                  # version, checksum, format, section-order contract
├── CHANGELOG.md                   # per-version history (semver)
└── README.md                      # this file
```

## Two layers — edit the right one

The template is split into the two things that change at different rates:

| You want to change… | Edit | Then |
|---------------------|------|------|
| **Branding / styling** — fonts, colours, header/footer, cover page, logo | `scope-document-template.docx` (in Word) | bump version, update checksum, log it |
| **Structure / content** — sections, headings, table columns, requirement conventions | `../../ba-output/scope.md` (markdown) **and** `plugins/ba/skills/ba-extraction/SKILL.md` | keep `manifest.json → conforms_section_order` in sync |

The markdown (`ba-output/scope.md`) is what the BA Agent actually writes; this `.docx` is the **render target** the (planned) Doc Agent applies branding from at scope-freeze. Keeping structure in markdown is deliberate — it diffs cleanly and is where most edits happen. The `.docx` carries only the branding that markdown can't express.

> ⚠️ If you change the section order or add/remove a section in the `.docx`, it is a **major** template change: update `conforms_section_order` in `manifest.json`, the markdown template, and the `ba-extraction` skill together so the BA output and the branded render stay 1:1.

## Update procedure (per plugin release)

1. Edit `scope-document-template.docx` in Word (or update the markdown structure — see table above).
2. Recompute the checksum and size:
   ```powershell
   (Get-FileHash .\scope-document-template.docx -Algorithm SHA256).Hash.ToLower()
   (Get-Item .\scope-document-template.docx).Length
   ```
3. Update `manifest.json`: `template_version`, `sha256`, `bytes`, `last_updated` (and `conforms_section_order` if structure changed).
4. Add an entry to `CHANGELOG.md`.
5. Bump the `delivery-os` plugin version in `marketplace.json` so teams receive the update.
