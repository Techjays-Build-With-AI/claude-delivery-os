# Techjays Proposal Standard

The next proposal should be authored against the 6-section flow in §11. Future proposals should not deviate from this standard without a reason.

---

## 1. How to use this standard

1. Copy the most recent client proposal that already follows this standard to a new file (e.g. `proposal_<client>.html`).
2. Search-and-replace every token in §2.
3. Drop the Appendix (§11) unless the client asked for depth or a POC reference exists.
4. Renumber the footer page counters and `{{TOTAL_SLIDES}}`.
5. Render in a browser, choose "Print / Save as PDF", review at print preview.

The Techjays brand layer (§3), document format (§4), color system (§5), typography (§6), slide skeleton (§7), and footer watermark (§10) do not change per client.

---

## 2. Client-specific tokens

These are the only values that should change between proposals. Everything else is shared scaffolding.

| Token | Meaning | Example |
|---|---|---|
| `{{CLIENT_NAME}}` | Full legal name | `Harry Grodsky & Co., Inc.` |
| `{{CLIENT_SHORT}}` | Short name used in body copy and section titles | `Grodsky` |
| `{{CLIENT_TAGLINE}}` | One-line descriptor on the Title Deck meta block | `Mechanical Contracting · Since 1918` |
| `{{CLIENT_HERITAGE}}` | Heritage chip on the Title Deck eyebrow (omit if N/A) | `Since 1918` |
| `{{CLIENT_ACCENT}}` | Client's primary accent hex | `#B91C1C` (Grodsky red) |
| `{{CLIENT_ACCENT_DARK}}` | Hover/active variant | `#7F1818` |
| `{{CLIENT_ACCENT_TINT}}` | Mid tint for borders/highlights | `#FCA5A5` |
| `{{CLIENT_ACCENT_SOFT}}` | Soft tint for fills | `#FEE2E2` |
| `{{CLIENT_ACCENT_WASH}}` | Washed fill for full panes | `#FFF5F5` |
| `{{ENGAGEMENT_TITLE}}` | Title Deck h1, the value prop | `AI-Powered Estimating & Takeoff Automation` |
| `{{ENGAGEMENT_SUB}}` | One-line tagline under the title | `Turning weeks of takeoff into 20-minute AI runs.` |
| `{{ENGAGEMENT_WINDOW}}` | Start and end dates (used on §05 Timeline & Budget only; omitted from the Title Deck) | `Jun 2026 to Oct 2026` |
| `{{REFERENCE_PROJECT}}` | Footer watermark suffix, the demo/POC reference (drop entire clause if no POC) | `Yale Thermal Plant reference` |
| `{{CLIENT_MARQUE}}` | Footer left, pairing marque | `Grodsky × Techjays` |
| `{{TOTAL_SLIDES}}` | Total deck length (8 by default with Appendix, 7 if Appendix dropped) | `8` |
| `{{DATE_STAMP}}` | Top-right of Title Deck and Closing | `May 2026` |
| `{{CONTACT_NAME}}` | Title Deck and Closing | `Jennifer Davis` |
| `{{CONTACT_TITLE}}` | Title Deck and Closing | `Chief Commercial Officer` |
| `{{CONTACT_EMAIL}}` | Title Deck and Closing | `jdavis@techjays.com` |

**Match the accent and logo to the client's own brand. Start at their website.** Before writing any content, open the client's site and capture two things:

1. **Primary brand color.** Sample the dominant brand color (header, logo, primary buttons, links). That hex becomes `--client-accent` (the `base`), and the other four ramp steps are derived from it: `dark` (hover/active, ~20–30% darker), `tint` (mid, for borders), `soft` (light fill), `wash` (washed full-pane fill). Keep the accent distinct from any other client's deck so each proposal reads as that client's. Examples: Grodsky `#B91C1C` (red), Blue Signal `#0E5BC4` (blue), Integrity Staffing `#1C4A86` (navy).
2. **Logo.** Use the client's official logo on the Title Deck brand pair (and the footer marque text). Pull the logo asset from the site (or their press/brand kit) as an SVG or transparent PNG. Embed it base64 for offline portability, or reference its official URL when speed matters (see the placement priority and `.client-logo` sizing in the style guide §4.19). Until the official asset is in hand, use the placeholder text wordmark rendering the client name in their accent color (see §8). Replace it before sending.

If the client publishes a formal brand guide, prefer its official hex values over a sampled color. Grodsky's ramp was built from `#B91C1C` per [`Grodsky_Brand_Style_Guide.md`](../Grodsky_Brand_Style_Guide.md).

---

## 3. Techjays brand layer (do not change)

These elements are constant across every proposal:

- **Company name:** `Techjays`
- **Descriptor:** `The AI Reimagination Company`
- **Tagline:** `Built by engineers who built AI at Google. Trusted across seven countries. Engineered for production.`
- **Logo:** embedded base64 PNG at `proposal_v3.html:270`. Copy that entire CSS `url("data:image/png;base64,…")` declaration verbatim into new proposals. Renders inside a `.brand` chip (white pill, 18×92 mark).
- **Default KPIs (Partnership slide):** `200+ Engineers, researchers & designers` / `40+ AI / ML projects shipped` / `7 Countries: UK, US, Canada, UAE, Australia, India, Bangladesh`.
- **Capabilities stripe:** AI Research & Development · Product Engineering · Enterprise-Scale Deployment · Data Engineering · Business Solutions & Discovery.
- **Domain Coverage stripe:** Construction & AEC · Manufacturing & Automotive · Retail, E-Commerce & Supply Chain · Banking & Financial Services · Healthcare & Life Sciences.
- **Closing headline convention:** `Let's Reimagine Together.`
- **Web:** `www.techjays.com`

---

## 4. Document format

- **Page:** US Letter, 8.5"×10" deck container, 8.5"×11" when printed.
- **Margin:** `@page { size: Letter; margin: 0; }`. Slide padding handles the inset.
- **Slide breaks:** every `.slide` is `page-break-after: always` so screen and print align.
- **Top accent border:** every slide carries a 4px `{{CLIENT_ACCENT}}` top border.
- **Light theme everywhere:** every slide uses a light background (`--card` / white). Title Deck and Closing are light too. See §13.
- **Print button:** floating "Print / Save as PDF" pill, top-right, screen-only (hidden in `@media print`).

---

## 5. Color system

Paste the full `:root` block at the top of any new proposal's stylesheet. The first half is the **Techjays universal palette**. The bottom 5 vars are the **client-accent slot** to replace per client.

```css
:root {
  /* Neutrals: universal */
  --ink: #0B1220;
  --body: #1F2937;
  --mute: #6B7280;
  --soft: #9CA3AF;
  --border: #E5E7EB;
  --hairline: #F3F4F6;
  --surface: #F9FAFB;
  --card: #FFFFFF;

  /* Techjays primary navy: universal */
  --accent: #0A2540;
  --accent-dark: #061A2F;
  --accent-tint: #D6E4F0;
  --accent-soft: #F0F5FA;
  --confidential: #8593AB;

  /* Status: universal */
  --green-accent: #047857;
  --green-tint: #D1FAE5;
  --green-soft: #ECFDF5;
  --warn: #B45309;
  --warn-tint: #FEF3C7;

  /* Client accent slot: replace per proposal */
  --client-accent:      {{CLIENT_ACCENT}};       /* e.g. #B91C1C */
  --client-accent-dark: {{CLIENT_ACCENT_DARK}};  /* e.g. #7F1818 */
  --client-accent-tint: {{CLIENT_ACCENT_TINT}};  /* e.g. #FCA5A5 */
  --client-accent-soft: {{CLIENT_ACCENT_SOFT}};  /* e.g. #FEE2E2 */
  --client-accent-wash: {{CLIENT_ACCENT_WASH}};  /* e.g. #FFF5F5 */
}
```

> Note on legacy decks: the Grodsky v3 deck declares the client ramp as `--grodsky-red*`. When porting, rename to `--client-accent*` so future search-and-replace stays mechanical.

---

## 6. Typography

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--body);
  background: #EEF1F4;
  line-height: 1.5;
  font-size: 13px;
}

h1, h2, h3, h4 { color: var(--ink); font-weight: 700; line-height: 1.15; letter-spacing: -0.01em; }
h1 { font-size: 24px; }
h2 { font-size: 18px; }
h3 { font-size: 15px; }
h4 { font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--mute); font-weight: 600; }
```

System font stack only. No web fonts (keeps print fidelity and offline rendering predictable).

---

## 7. Slide skeleton

Every interior slide (everything between Title Deck and Closing) follows this structure:

```html
<section class="slide">
  <header class="slide-header">
    <span class="eyebrow">{{SECTION_NAME}}</span>
    <span class="stamp">Section {{NN}}</span>
  </header>

  <div class="slide-body">
    <div class="title-block">
      <div class="kicker">{{SECTION_SUBTITLE}}</div>
      <h1>{{SLIDE_HEADLINE}}</h1>
      <p class="subhead">{{ONE_PARAGRAPH_LEAD}}</p>
    </div>

    <!-- content components here (see §12) -->
  </div>

  <footer class="slide-footer">
    <span class="marque">{{CLIENT_MARQUE}}</span>
    <span class="confidential">Confidential · Prepared for {{CLIENT_NAME}} · {{REFERENCE_PROJECT}}</span>
    <span class="pg">{{NN}} / {{TOTAL_SLIDES}}</span>
  </footer>
</section>
```

Required rules:
- `.slide-header` is always `eyebrow` (left, kicker-cased) + `stamp` (right, `Section NN`).
- `.title-block` always carries kicker (uppercase, client-accent color) + h1 + optional subhead.
- The 4px `{{CLIENT_ACCENT}}` top border applies to every slide (defined on `.slide`).
- Background is always light (white / `--card`). Every slide. No dark gradient on any slide, including the Title Deck and Closing.

---

## 8. Title Deck pattern

The Title Deck opens the deck with the brand pair (Techjays + client logo), engagement title, one-line value statement, and direct contact. Scannable and short. No synopsis block on this page; the Value Gain page (§04) carries the at-a-glance outcome story.

Light theme: white background. No dark navy gradient.

```html
<section class="slide title-deck" id="s1" data-num="01" data-title="Title Deck">
  <div class="slide-inner hero-grid">
    <div>
      <div class="brand-pair">
        <svg class="tj-logo tj-logo-lg" viewBox="0 0 223 41" role="img" aria-label="Techjays"><use href="#tj-logo"/></svg>
        <span class="brand-x" aria-hidden="true">×</span>
        <!-- Replace this client wordmark with the official client logo SVG/PNG when provided. -->
        <svg class="client-logo client-logo-lg" viewBox="0 0 220 40" role="img" aria-label="{{CLIENT_NAME}}">
          <text x="0" y="29" font-family="Inter, system-ui, sans-serif" font-weight="800" font-size="28" letter-spacing="-1" fill="var(--navy-900)">{{CLIENT_LEAD}}</text>
          <text x="62" y="29" font-family="Inter, system-ui, sans-serif" font-weight="800" font-size="28" letter-spacing="-1" fill="var(--client-accent)">{{CLIENT_TAIL}}</text>
        </svg>
      </div>
      <div class="hero-tag" style="margin-top:2.4rem">A Proposal for {{CLIENT_NAME}}</div>
      <h1 class="hero-title">{{ENGAGEMENT_TITLE}}</h1>
      <p class="hero-sub">{{ENGAGEMENT_SUB}}</p>

      <div class="hero-meta">
        <div><strong>Prepared by</strong><span>Techjays</span></div>
        <div><strong>Prepared for</strong><span>{{CLIENT_NAME}}</span></div>
        <div><strong>Direct contact</strong><span>{{CONTACT_NAME}} · <a href="mailto:{{CONTACT_EMAIL}}">{{CONTACT_EMAIL}}</a></span></div>
      </div>
    </div>
  </div>
  <span class="slide-num">01 / {{TOTAL_SLIDES}}</span>
  <span class="confidential-mark">Confidential · Prepared for {{CLIENT_NAME}}</span>
</section>
```

What the Title Deck shows:
- Brand pair: Techjays mark + client logo (placeholder text SVG until the official one is in).
- Engagement title (`hero-title`).
- One-sentence value statement (`hero-sub`).
- Identification row: Prepared by, Prepared for, Direct Contact (name + email).

What the Title Deck does **not** show:
- Multi-sentence synopsis. Outcomes live on §04 Value Gain.
- Engagement window dates. Those live on §05 Timeline & Budget.
- Total price. Same.
- About-Techjays KPIs. Those live on §06 Partnership.

Background CSS: `.title-deck { background: var(--card); }`. Light theme inherits from the default slide.

---

## 9. Closing slide pattern

Mirror of the Title Deck. Same light background, same `{{CLIENT_ACCENT}}` top border. Headline is always `Let's Reimagine Together.`.

```html
<section class="slide closing">
  <header class="slide-header">
    <span class="brand"><span class="logo"></span></span>
    <span class="stamp">Confidential · {{DATE_STAMP}}</span>
  </header>

  <div class="center">
    <span class="cover-eyebrow"><span class="dot"></span>Closing · For {{CLIENT_SHORT}}, {{CLIENT_HERITAGE}}</span>
    <h1 class="big">Let's Reimagine Together.</h1>
    <p class="sub">{{CLOSING_PARAGRAPH}}</p>

    <div class="contact" style="grid-template-columns: 1fr 1fr;">
      <div>
        <div class="label">Direct</div>
        <div class="value">{{CONTACT_NAME}}<br>{{CONTACT_TITLE}}<br>{{CONTACT_EMAIL}}</div>
      </div>
      <div>
        <div class="label">Web</div>
        <div class="value">www.techjays.com</div>
      </div>
    </div>
  </div>

  <footer class="slide-footer">…standard footer…</footer>
</section>
```

Headline is always `Let's Reimagine Together.` (Techjays-universal). Background is white (`--card`). No dark navy gradient. Override any legacy `.closing` CSS that bleeds in a navy gradient.

---

## 10. Confidentiality watermark

Every slide footer carries the same three-part watermark:

```html
<footer class="slide-footer">
  <span class="marque">{{CLIENT_MARQUE}}</span>
  <span class="confidential">Confidential · Prepared for {{CLIENT_NAME}} · {{REFERENCE_PROJECT}}</span>
  <span class="pg">{{NN}} / {{TOTAL_SLIDES}}</span>
</footer>
```

Rules:
- **Always present** on every slide, including the Title Deck and Closing.
- The `Confidential` and `Prepared for {{CLIENT_NAME}}` clauses are mandatory.
- `{{REFERENCE_PROJECT}}` is optional. Drop the trailing ` · {{REFERENCE_PROJECT}}` clause if no POC, demo, or representative artifact was shared.
- `{{CLIENT_MARQUE}}` uses `×` (multiplication sign), never an `x`.
- Page count uses tabular numerals, zero-padded: `01 / 06`, never `1 / 6`.

---

## 11. The 8-section flow

A standard proposal is **8 slides** (7 required + Appendix). The Appendix is the only section that may be dropped, and only when the client has not asked for depth.

| # | Section | Status | Purpose |
|---|---|---|---|
| 01 | Title Deck | **Required** | Brand pair (Techjays × client), engagement title, one-line value statement, direct contact. No synopsis block. |
| 02 | Problem Statement | **Required** | What the client is solving for, in their own words. Pull-quote + format/customer breakdown |
| 03 | Solution | **Required** | The end-to-end workflow as numbered steps (inbox to system-of-record). Abstract pillars and architecture move to the Appendix |
| 04 | Value Gain | **Required** | What the client gets back: time per unit, capacity reclaimed per resource, risk reduced, speed to onboard next. Numbers must be the client's |
| 05 | Timeline & Budget | **Required** | Two-phase timeline strip + fixed-price table + zero-risk callout ("No invoice until each milestone is delivered and signed off by {{CLIENT_NAME}}") |
| 06 | Partnership | **Required** | Long-term partnership promise. Title is the principle: "We are here for the long-term partnership. Your success is our success." |
| 07 | Closing | **Required** | "Let's Reimagine Together." + closing quote + signoff with direct contact |
| 08 | Appendix | **Recommended (visually distinct)** | Per-phase weekly/monthly detail, design pillars, system architecture. Distinct treatment: cream background, thick coral top border, "Appendix · Optional Deep Dive" pill badge replacing the eyebrow |

Keep the Appendix when:
- The client asked for week-by-week or month-by-month detail.
- The §03 Solution workflow has design depth (pillars, architecture) the reader will want to verify.
- A POC or representative artifact was shared.

Otherwise drop it. The 7-section flow is the lean form. After dropping, renumber section stamps and page counters mechanically.

### Where the content lives

- **Brand pair on the Title Deck.** Side-by-side Techjays logo and client logo, separated by a small "×". Use a placeholder SVG with `<text>` elements rendering the client name in their accent colors until the official logo is provided.
- **Pull-quote on Problem Statement.** Paraphrased from intake, attributed to the client's role. The artifact list (formats, customers, system names) sits in a check-grid below.
- **Solution as workflow.** Ten numbered `.wf-step` cards walking the document from inbox to system-of-record. Real system names in **strong**. Abstract framing belongs in the Appendix.
- **Value Gain.** 4-card metrics row (time per unit, hours reclaimed per resource, onboarding speed, target risk metric), then a 2-column `.split` (Time and capacity / Risk and opportunity). Use the client's numbers.
- **Timeline & Budget.** Two-phase timeline strip, invest table with Phase 1 + Phase 2 + Total (no Phase 3 row on the main page), and a coral-bordered zero-risk callout. Phase 3 is mentioned in the Appendix if relevant.
- **Partnership.** Concise. New title carries the principle. KPI row + 4 commitment cards (we grow with you, same team longer horizon, your success metric, compliance and control). Onboarding steps belong with the engagement narrative, not the partnership message.
- **Closing.** Clean signoff. Closing quote + closing sub + signoff brand row with direct contact email.
- **Appendix.** Visually distinct. `.slide.appendix-slide` adds a cream background, a thick coral top border, and the pill-shaped "Appendix · Optional Deep Dive" badge. Contains week-by-week, month-by-month, design pillars, architecture diagram.

### Where the old content went

Earlier versions of this guide had a synopsis block on the Title Deck and 6 main sections. The content reorganized:

- **Synopsis block** → split: identification block (Prepared by / Prepared for / Direct contact) on Title Deck, outcomes on §04 Value Gain.
- **Solution pillars + architecture** → moved off §03 (which now carries the workflow) into §08 Appendix. The workflow IS the solution.
- **Onboarding steps (Discovery call, Phase 1 kickoff, etc.)** → folded into Timeline & Budget or removed; the engagement narrative is implied by the timeline + invest table.
- **Capabilities + Domain stripes** → dropped from the main flow. KPIs row carries the Techjays positioning on §06 Partnership.
- **About Techjays KPIs** → §06 Partnership (3-card row).
- **Outcomes & commercial metrics** → §04 Value Gain (the new outcome-focused page).
- **Phase 1, Phase 2, Phase 3 weekly/monthly detail** → §08 Appendix.

---

## 12. Component library

Every reusable block. Use the existing class names so styles already work.

### `.pillar`: numbered card with big numeral
Used for the 3-pillar Solution slide and engagement-phase cards.
```html
<div class="pillar">
  <div class="pn">01</div>
  <div>
    <h3>{{Pillar title}}</h3>
    <p>{{Pillar body}}</p>
  </div>
</div>
```

### `.metric` / `.metric.accent`: outcome metric tile
4-up grid for outcome metrics. `.accent` flips to client-accent gradient.
```html
<div class="cards c-4">
  <div class="metric accent"><div class="v">$2.4M</div><div class="l">AI material estimate</div></div>
  <div class="metric"><div class="v">20 min</div><div class="l">vs. 3 to 5 days manual</div></div>
</div>
```

### `.kpi`: large headline metric (client-accent washed)
3-up row on the Partnership slide.
```html
<div class="kpi-row">
  <div class="kpi"><div class="v">200+</div><div class="l">Engineers, researchers & designers</div></div>
</div>
```

### `.cards.c-2 / .c-3 / .c-4` + `.card` (`.tinted`, `.accent`)
Generic content card grid.
```html
<div class="cards c-3">
  <div class="card"><h3>…</h3><p>…</p></div>
  <div class="card tinted">…</div>
  <div class="card accent">…</div>
</div>
```

### `.compare`: before/after two-pane
Manual baseline vs AI takeoff.
```html
<div class="compare">
  <div class="pane manual">
    <h4>Manual baseline</h4>
    <div class="row"><span class="label">Material total</span><span class="val">$2,399,464</span></div>
  </div>
  <div class="pane ai">
    <h4>AI takeoff (Techjays POC)</h4>
    <div class="row"><span class="label">Material total</span><span class="val">~$2,400,000</span></div>
  </div>
</div>
```

### `.timeline`: 5-segment colored strip
Used on the Timeline & Budget slide.
```html
<div class="timeline">
  <div class="seg discovery"><div class="month">{{Month}}</div><div class="what">{{What}}</div></div>
  <div class="seg impl">…</div>
  <div class="seg uat">…</div>
</div>
```

### `.phase-strip`: Window / Cadence / Price header
3-cell strip at the top of every phase block.
```html
<div class="phase-strip">
  <div class="cell"><div class="l">Window</div><div class="v">Month 1 · Jun 2026</div></div>
  <div class="cell"><div class="l">Effort</div><div class="v">4 weeks · cross-functional team</div></div>
  <div class="cell price"><div class="l">Investment</div><div class="v">$50,000</div></div>
</div>
```

### `.weeks` and `.months`: period grid (Appendix only)
```html
<div class="weeks">
  <div class="week">
    <span class="wk">Week 1</span>
    <h3>{{Title}}</h3>
    <p>{{Body}}</p>
  </div>
</div>
```

### `.deliverables`: green-checkmark list
```html
<div class="deliverables">
  <h4>Discovery deliverables</h4>
  <ul>
    <li>{{Item}}</li>
  </ul>
</div>
```

### `.milestones`: payment-milestone 3-up
```html
<div class="milestones">
  <div class="ms"><h4>Phase 1 · Discovery</h4><p>50% on kickoff. 50% on roadmap delivery.</p></div>
</div>
```

### `.steps`: numbered next-steps list
Lives on §06 Partnership (or §05 Timeline & Budget when used as engagement onboarding steps).
```html
<div class="steps">
  <div class="step">
    <div class="n">1</div>
    <div><h4>{{Step title}}</h4><p>{{Step body}}</p></div>
  </div>
</div>
```

### `.pull-quote`: italic blockquote with client attribution
The listening-back moment on the Problem Statement slide. Use the client's actual words from the intake email or call.
```html
<div class="pull-quote">
  <p>{{Verbatim client quote}}</p>
  <div class="attrib">{{Attribution}}</div>
</div>
```

### `.ref-frame`: dashed "reference artifact" frame
For showing back the artifact the client sent (a bid, a screenshot, a spec).
```html
<div class="ref-frame">
  <span class="ref-label">{{Artifact name}} · the reference you sent us</span>
  <p class="ref-gloss">{{One-line gloss}}</p>
  <!-- content -->
</div>
```

### `.arch`: inline architecture diagram
A horizontal data-flow strip with boxes and arrows.
```html
<div class="arch">
  <div class="arch-row">
    <div class="arch-node"><div class="h">{{Input}}</div><div class="s">{{Subtext}}</div></div>
    <div class="arch-arrow">→</div>
    <div class="arch-node accent"><div class="h">{{Processor}}</div><div class="s">{{Subtext}}</div></div>
    <div class="arch-arrow">→</div>
    <div class="arch-node"><div class="h">{{Output}}</div><div class="s">{{Subtext}}</div></div>
  </div>
</div>
```

### `.tuned`: 2-column "Designed for client" fit cards
Lives on §06 Partnership when commitments are worth promising in writing.
```html
<div class="tuned">
  <div class="item"><div class="h">{{Commitment}}</div><div class="b">{{Detail}}</div></div>
</div>
```

### `.stripes` + `.modalities`: capability/domain lists
Used on Partnership. Keep the Techjays defaults (§3) unless there's a strong reason to vary them.

### `.script`: accent-colored question list (Appendix intake)
```html
<div class="script">
  <h4>The standard intake script · questions we answer in Week 1</h4>
  <ul>
    <li>{{Question}}</li>
  </ul>
</div>
```

### `.brand-pair`: side-by-side logos on the Title Deck
Techjays mark + small "×" + client logo. Placeholder client wordmark uses inline `<text>` until the official logo SVG/PNG is provided.
```html
<div class="brand-pair">
  <svg class="tj-logo tj-logo-lg"><use href="#tj-logo"/></svg>
  <span class="brand-x" aria-hidden="true">×</span>
  <svg class="client-logo client-logo-lg" viewBox="0 0 220 40" role="img" aria-label="{{CLIENT_NAME}}">…</svg>
</div>
```

### `.value-grid` / `.value-card`: outcome metrics on §04 Value Gain
4-up row of stat cards (time per unit, hours reclaimed per resource, onboarding speed, target risk metric).
```html
<div class="value-grid">
  <div class="value-card">
    <div class="value-stat">~88%</div>
    <div class="value-label">Time per unit</div>
    <p>{{Before/after one-liner with the client's numbers.}}</p>
  </div>
</div>
```

### `.risk-callout`: zero-risk billing promise on §05 Timeline & Budget
Coral-bordered callout sitting under the invest table.
```html
<div class="risk-callout">
  <div class="risk-icon">{{check-circle SVG}}</div>
  <div><strong>Zero risk.</strong> No invoice until each milestone is delivered and signed off by {{CLIENT_NAME}}.</div>
</div>
```

### `.slide.appendix-slide` + `.appendix-mark`: visually distinct Appendix
Cream background, 8px coral top border, "Appendix · Optional Deep Dive" pill badge replacing the eyebrow. Marks page 08 as a separate experience from the main flow.
```html
<section class="slide alt appendix-slide" data-num="08" data-title="Appendix">
  <div class="slide-inner">
    <div class="appendix-mark">Appendix · Optional Deep Dive</div>
    <h2 class="h-section">Implementation detail.</h2>
    …
  </div>
</section>
```

### `.confidential-mark`: per-slide confidential watermark
Centered at the bottom of every slide, opposite the page number. Visible in print.
```html
<span class="confidential-mark">Confidential · Prepared for {{CLIENT_NAME}}</span>
```

### `table.invest` + `.recommended-row` + `.optional-tag`: investment table
Lives on §05 Timeline & Budget.
```html
<table class="invest">
  <thead>
    <tr><th>Phase</th><th>Window</th><th style="text-align:right;">Investment (USD)</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><div class="phase-name">Phase 1 · Discovery & Proof</div><div class="phase-sub">…</div></td>
      <td>Month 1</td>
      <td class="amount">$50,000</td>
    </tr>
    <tr class="recommended-row">
      <td><div class="phase-name">Phase 3 · Scale & Optimize <span class="optional-tag">Optional</span></div>…</td>
      <td>Monthly</td>
      <td class="amount">$37,500 to $50,000 / month</td>
    </tr>
  </tbody>
</table>
```

---

## 13. Voice & messaging conventions

The first four rules are non-negotiable. AI-generated drafts violate them by default. Reject any draft that does.

1. **No em-dashes (—).** Use periods, commas, or parentheses instead. The em-dash is a well-known AI-prose tell and reads as machine-written to executives. (En-dashes are still fine for ranges: `Jul–Oct 2026`, `$37,500–$50,000`.)
2. **No contrastive negation.** Avoid "not X but Y", "X, not Y", and ". Not X." patterns. Find the assertive form. Replace "An estimator's tool, not a black box" with "An estimator's tool the client can audit." The negation pattern is a recognizable AI tic, and it forces the reader to model the rejected idea before the accepted one.
3. **Light theme only.** Every slide, including Title Deck and Closing, uses the light background (`--card`) with a 4px `{{CLIENT_ACCENT}}` top border. Dark navy gradients are out. The reader is an executive, and dark mode reads as developer tooling.
4. **Value lives on a dedicated page.** §04 Value Gain carries 4 outcome metrics (time per unit, capacity reclaimed, risk reduced, speed to onboard next) plus a 2-column split (Time and capacity / Risk and opportunity). The numbers must be the client's, never aspirational defaults. A reader who reads only §04 should understand the ROI.

Additional conventions:

- **Address the client by name** in section titles and subheadings. Use `Designed for {{CLIENT_SHORT}}'s Operating Reality` rather than "Designed for Your Operating Reality".
- **The Problem Statement uses the client's own words** via `.pull-quote` and the artifact they shared via `.ref-frame`. This is the proposal's empathy anchor. Keep it even when the client's words were terse.
- **Phases gate each other.** Discovery exits with a signed Phase 2 SOW or an honest no-go. State this on Timeline & Budget.
- **Pricing is fixed-price per phase, milestone-based payments.** State this on §05. Phase 3 is monthly. Outcome-based pricing is offered as a Discovery option and is never the default.
- **End Partnership with "what we need from you."** A concrete ask (signed SOW, named sponsor, sample data) so the proposal is actionable.
- **Quality bar is the client's number.** v3 commits to `90% sustained accuracy` because Grodsky set it during the demo. For new clients, replace with their threshold, defined in Discovery. Never assert a threshold the client hasn't agreed to.
- **Generalize Grodsky-specific commitments.** "Concurrent-run mode", "efficiency over headcount", "the green cells" are Grodsky framings. Keep the *pattern* (a measurable bar set by the client, safety-first rollout, preservation of human authority) and rewrite the words.
- **Date conventions.** Months as `Jun 2026`. Ranges as `Jul–Oct 2026` (en-dash). Dollar amounts with comma thousands and no decimals (`$250,000`).

---

## 14. Print / PDF behavior

> **Scope responsive breakpoints to `@media screen`.** US Letter at 96dpi is 816px wide, below the usual 980px breakpoint. A bare `@media (max-width: 980px)` fires during print and collapses every grid to one column with shrunken padding, producing a PDF of stacked rows with no structure. This is the most common print defect and it has recurred across proposals. Always write `@media screen and (max-width: …)`. As a safeguard, re-assert the multi-column grid templates inside `@media print` and keep `overflow: visible` on `.slide` in print so tall content is never clipped.

Two pieces have to be in place for the deck to print correctly:

```html
<!-- top of <body>, screen-only -->
<div class="pdf-btn-wrap">
  <button class="pdf-btn" type="button" onclick="window.print()">
    Print / Save as PDF
  </button>
  <span class="pdf-hint">In the print dialog, choose "Save as PDF"</span>
</div>
```

```css
@page { size: Letter; margin: 0; }
@media print {
  html, body { background: white; }
  .pdf-btn-wrap { display: none !important; }
  .slide {
    width: 8.5in;
    min-height: 11in;
    margin: 0;
    box-shadow: none;
    border-top: 4px solid var(--client-accent);
    page-break-after: always;
    page-break-inside: avoid;
  }
  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
  /* Avoid splitting components across pages */
  .pillar, .card, .week, .months .mo, .step, .green-list, .green-numbers,
  .compare .pane, .metric, .kpi, .pull-quote, .deliverables, .milestones .ms,
  table.invest { break-inside: avoid; page-break-inside: avoid; }
}
```

---

## 15. Build checklist for a new proposal

1. Copy the most recent client proposal that follows this standard to `proposal/proposal_<client>.html`.
2. Visit the client's website first (§2). Sample their primary brand color and build the 5-step `--client-accent*` ramp from it, and grab their official logo. Prefer a published brand guide's hex values when one exists.
3. Search-and-replace every `{{TOKEN}}` from §2, using the sampled accent ramp.
4. Put the client's official logo on the Title Deck brand pair and the footer marque. Until the asset is in hand, use the placeholder text wordmark in the client accent color, and replace it before sending.
4. Rewrite §02 Problem Statement with the client's verbatim words and the artifact they sent.
5. Fill §04 Value Gain with the client's actual numbers (time per unit, hours reclaimed per resource, onboarding speed, target risk metric).
6. Add the zero-risk callout to §05 Timeline & Budget: "Zero risk. No invoice until each milestone is delivered and signed off by {{CLIENT_NAME}}."
7. Use the new Partnership title verbatim: "We are here for the long-term partnership. Your success is our success."
8. Confirm Title Deck, Closing, and all interior slides use a light background. No navy gradients anywhere.
9. Confirm the Appendix uses the visually distinct `.slide.appendix-slide` treatment (cream background, coral top border, "Appendix · Optional Deep Dive" pill badge).
10. Confirm every slide carries a confidential watermark (`Confidential · Prepared for {{CLIENT_NAME}}`).
11. Decide on the Appendix: keep it (default, recommended) or drop it (only if the client has not asked for depth). Renumber every `Section NN` stamp and `NN / TT` page counter mechanically.
12. Scan for em-dashes (`—`) and contrastive negation patterns (`, not `, ` not only `, `. Not `). Replace each instance before sending.
13. Open in Chrome/Edge → confirm scroll-snap is `proximity` (tall slides scroll, short ones snap), page transitions render cleanly, the confidential mark sits centered below the content with breathing room.
14. Confirm every responsive breakpoint is scoped to `@media screen and (…)`. Letter @96dpi is 816px wide, so an unscoped `max-width: 980px` query collapses the printed PDF to single-column rows. Grep the file for `@media (max-width` and ensure none remain unscoped.
15. Save as PDF and proof on paper sizing: structure stays multi-column, padding is preserved, and "Background graphics" is enabled in the print dialog so accent borders and fills render.

---

## 16. AI generation prompt

When generating a draft with Claude / ChatGPT / Cursor, paste this prompt verbatim as the system prompt or first user turn. It encodes the non-negotiable rules.

```
You are writing a Techjays client proposal as a single self-contained HTML file. Follow this standard exactly.

STRUCTURE: 8 slides in this order.
  01 Title Deck         brand pair (Techjays × client logo), engagement title, one-line value statement, direct contact
  02 Problem Statement  what the client is solving for, in their own words (pull-quote + format/customer breakdown)
  03 Solution           end-to-end workflow as numbered steps (inbox to system-of-record)
  04 Value Gain         4 outcome metrics + 2-column split (time and capacity / risk and opportunity)
  05 Timeline & Budget  two-phase timeline + fixed-price table + zero-risk callout
  06 Partnership        long-term partnership ("Your success is our success") + KPIs + commitment cards
  07 Closing            "Let's Reimagine Together." + closing quote + signoff with direct contact
  08 Appendix           visually distinct deep dive: weekly/monthly detail, design pillars, system architecture

Drop slide 08 only when the client has not asked for depth. Otherwise keep it.

VOICE RULES (non-negotiable):
  1. No em-dashes anywhere. Use periods, commas, or parentheses. En-dashes are fine in ranges only (Jul–Oct 2026, $37,500–$50,000).
  2. No contrastive negation. Never write "not X but Y", "X, not Y", or ". Not X." Find the assertive form.
  3. Light theme only. Every slide is a light background. No dark navy gradients anywhere, including Title Deck and Closing.
  4. §04 Value Gain carries 4 outcome metrics with the client's actual numbers. A reader who reads only §04 should understand the ROI.
  5. Address the client by name in section titles (avoid generic "your operating reality").
  6. Use the client's own words on Problem Statement, via a pull-quote and the artifact they sent.
  7. Partnership page title is the principle: "We are here for the long-term partnership. Your success is our success."
  8. Timeline & Budget includes the zero-risk callout: "Zero risk. No invoice until each milestone is delivered and signed off by {{CLIENT_NAME}}."
  9. Appendix uses .slide.appendix-slide treatment (cream background, coral top border, "Appendix · Optional Deep Dive" pill badge replacing the eyebrow).
 10. Every slide has a centered confidential watermark ("Confidential · Prepared for {{CLIENT_NAME}}").

FORMAT:
  - Tokens: search-and-replace {{CLIENT_NAME}}, {{CLIENT_SHORT}}, {{CLIENT_ACCENT}}, {{ENGAGEMENT_TITLE}}, {{ENGAGEMENT_SUB}}, {{ENGAGEMENT_WINDOW}}, {{CONTACT_NAME}}, {{CONTACT_TITLE}}, {{CONTACT_EMAIL}}, and the rest from §2.
  - Dates: "Jun 2026", ranges "Jul–Oct 2026" with an en-dash.
  - Money: comma thousands, no decimals ($250,000). Ranges with en-dash ($37,500–$50,000).
  - Page counter: zero-padded tabular numerals (01 / 08).

Before returning the file, scan your own draft for em-dashes and contrastive negation. Replace every instance.
```
