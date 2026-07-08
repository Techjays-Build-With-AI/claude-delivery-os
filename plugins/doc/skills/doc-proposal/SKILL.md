---
name: doc-proposal
description: Build a Techjays client proposal as a single-file, print-to-PDF HTML deck. Use whenever the user wants to create, draft, or generate a client proposal, pitch deck, or engagement proposal for a client. Gathers the client name and domain (to pull their logo online and sample their brand accent), auto-drafts content from the BA scope when a Delivery OS workspace exists, follows the Techjays proposal standard (section flow + voice rules) and style guide (design system), and produces one self-contained HTML file engineered to export to PDF cleanly. Honors custom rules the user passes (extra sections, tone, pricing, lean form). Trigger on "create a proposal", "proposal for <client>", "pitch deck", or similar.
---

# Techjays Client Proposal

You are producing a **Techjays client proposal**: one self-contained HTML file that reads beautifully on screen and exports to a clean PDF. The goal is organization-wide consistency — every proposal looks and reads like it came from the same senior proposal lead, built to the same standard.

Two bundled references govern the work. **Read both before building your first proposal:**
- **`references/proposal-standard.md`** — the governing spec: the section flow, the client-specific tokens, the Techjays brand layer, and the non-negotiable **voice rules**. When anything conflicts, the standard wins on flow and voice.
- **`references/proposal-style-guide.md`** — the design system: tokens, components, the full stylesheet (§9), the interaction script (§5), the responsive/print rules, and the client-brand/logo guidance (§4.19).

The starter deck is **`assets/proposal-template.html`** — it already contains the full stylesheet, the persistent UI, the scroll/print script, a client-logo slot, a client-accent slot, and the section skeleton with `{{TOKENS}}`. Start from it; don't rebuild the CSS from scratch.

## Workflow

### 1. Gather the inputs
Collect what the deck needs, asking only for what you can't infer or source:
- **Client legal name** and a **short name** (used in body copy and section titles).
- **Client domain** (e.g. `acme.com`) — drives the logo and the accent color. Strongly recommended.
- **Engagement title** (the value-prop headline) and a **one-line value statement**. You can draft these from the scope.
- **Direct contact** (name, title, email) — defaults to the Techjays contact if given.
- **Custom rules** the user passed — extra sections, tone, specific pricing, lean vs full form, brand overrides. Layer these on top of the defaults.

### 2. Source the content (auto-draft from the BA scope when present)
When a Delivery OS workspace exists, **read `ba-output/scope.md` and `shared-context/`** and draft from them:
- **Problem statement** — from the scope's current-state and pain points; use the client's own words where the registers captured them.
- **Solution** — from the scope's modules/workflows, as an end-to-end numbered workflow.
- **Value / ROI** — from the scope's value and the client's real numbers (time per unit, capacity reclaimed, risk reduced). **Never fabricate a metric.** If a number isn't in the scope, insert a clearly marked `[[NEEDS: …]]` placeholder and list it in your return summary.
- **Stakeholders, systems, glossary** — from `shared-context/` for names and accuracy.

With no workspace, use what the user provided or attached, and mark missing client numbers as `[[NEEDS: …]]` placeholders.

### 3. Brand the deck to the client
- **Accent color.** Sample the client's primary brand color from their site (or a published brand guide). Set `--client-accent` in the template's `:root`. Keep the Techjays teal/coral system as the base; the client accent personalizes the title/brand-pair and a few tasteful highlights.
- **Logo (priority order, per style guide §4.19).**
  1. **Base64-embedded (preferred, offline-portable).** If you can obtain the official logo (user-provided, or the site's logo asset), inline it as `<img class="client-logo" src="data:image/…;base64,…">`.
  2. **Online by domain (default when no asset in hand).** Set the logo `src` to `https://logo.clearbit.com/<domain>` (a widely-used logo-by-domain service). It renders in-browser and embeds into the PDF when saved online. Note it needs network at view/print time.
  3. **Favicon fallback.** `https://www.google.com/s2/favicons?domain=<domain>&sz=128` if Clearbit has no logo.
  4. **Text wordmark (last resort).** Render the client name in their accent color; replace before sending.
  Pair it with the Techjays mark on the title deck and the closing signoff. Size by height (`.client-logo{height:50px;width:auto;max-width:280px;object-fit:contain}`).

### 4. Build the deck
Fill every `{{TOKEN}}` in the template and assemble the sections per the standard's flow, using the style guide's components. Recommended section flow (map to the standard):
1. **Title deck** — Techjays × client logo brand pair, engagement title, one-line value, direct contact.
2. **Problem** — the client's situation in their own words (pull-quote / today–tomorrow).
3. **Solution** — the end-to-end workflow as numbered steps.
4. **Value gain** — the client's real outcome numbers (a reader who reads only this page gets the ROI).
5. **Timeline & budget** — phased timeline + fixed-price table + the zero-risk callout ("No invoice until each milestone is delivered and signed off by <Client>").
6. **Partnership** — the long-term promise + Techjays KPIs.
7. **Closing** — "Let's Reimagine Together." + signoff with the direct contact.
8. **Appendix** (optional) — weekly/monthly detail, architecture; keep only if the client asked for depth.

Apply the **non-negotiable voice rules** as you write (see below). Then layer the user's **custom rules** — add/reorder/drop sections, adjust tone or pricing, honor brand overrides. If a custom rule would break a non-negotiable voice or brand rule, apply the rest and flag that one in your return summary rather than silently breaking the standard.

### 5. Make it print-perfect (hard requirement)
The deck must Save-as-PDF cleanly. Verify before delivering:
- Every responsive breakpoint is scoped to **`@media screen and (…)`** (US Letter @96dpi is 816px, below the 980px breakpoint — an unscoped query collapses the PDF to single-column rows). The template already does this; keep it if you add CSS.
- The `@page { margin:0 }` and `@media print` rules are intact; dark slides invert to white with accent colors preserved.
- `break-inside: avoid` stays on cards so components don't split across pages.
- The floating **Print / Save PDF** button is present (screen-only).
- The client logo loads (if referencing it online, note that the user must be online when saving the PDF; base64 is best for archiving).

### 6. Deliver
Read a run timestamp (`YYYY-MM-DD-HHMMSS`; `date +%Y-%m-%d-%H%M%S`) and write the single file to **`doc-output/proposal-<client>-<timestamp>.html`** (create `doc-output/` if absent; beside the working dir if there's no workspace). **Save it as UTF-8 (no BOM); do not route the HTML through a shell or editor that re-encodes it.** The proposal contains non-ASCII glyphs (§, ×, —, →, …); if a Windows code page mangles them the page shows mojibake (`§`→`Â§`, `—`→`â€"`) despite `<meta charset="utf-8">`. After writing, verify the file shows those glyphs and not `Â`/`â€`/`Ã` sequences — e.g. `node -e "process.exit(/Â.|â€.|Ã./.test(require('fs').readFileSync(process.argv[1],'utf8'))?1:0)" doc-output/proposal-<client>-<timestamp>.html` (nonzero = mojibake, rewrite as UTF-8). Return a short summary: what was built, which content came from the BA scope vs. supplied, and every `[[NEEDS: …]]` placeholder still to fill (missing client metrics, the official logo, final pricing). Tell the user to open it in Chrome/Edge and choose **Print → Save as PDF** with "Background graphics" enabled.

## Non-negotiable voice rules

AI drafts violate these by default. Scan your own output and fix every instance before delivering.
1. **No em-dashes (—).** Periods, commas, or parentheses instead. En-dashes only in ranges (`Jul–Oct 2026`, `$37,500–$50,000`).
2. **No contrastive negation.** No "not X but Y", "X, not Y", ". Not X." Use the assertive form ("An estimator's tool the client can audit", not "…not a black box").
3. **Address the client by name** in section titles and body ("Designed for <Client>'s operating reality", never "your operating reality").
4. **Value uses the client's real numbers.** Never assert a metric or quality bar the client hasn't given. Mark unknowns as placeholders.
5. **Single file, offline-portable, system fonts.** No external CSS/JS/CDN/webfont. The file must open and print offline (base64 the client logo for true offline).

## Principles

- **Consistency over cleverness.** The value of this skill is that every proposal is unmistakably Techjays. Follow the standard; reserve creativity for the client's story, not the chrome.
- **Never fabricate client data.** Pricing, metrics, and quality thresholds come from the client or the scope. A marked placeholder is always better than an invented number.
- **The client's brand, the Techjays craft.** Their logo and accent make it theirs; the layout, voice, and rigor make it ours.
- **PDF is a first-class deliverable.** A proposal that looks great on screen but breaks in the PDF has failed. Treat the print rules as part of the content.
