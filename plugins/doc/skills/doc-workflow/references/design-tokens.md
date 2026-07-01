# Design Tokens

## CSS Variables (`:root`)

```css
:root {
  --navy:        #0F2545;
  --navy-dark:   #0A1A35;
  --navy-mid:    #1A2A4A;
  --navy-tint:   #93AAD7;
  --teal:        #1E4D8B;
  --teal-dark:   #163A6B;
  --teal-light:  #EEF2F8;
  --teal-border: #93AAD7;
  --green:       #166534;
  --green-bg:    #F0FDF4;
  --grey-actor:  #6B7280;
  --border:      #E5E7EB;
  --paper:       #F4F5F7;
  --text:        #111827;
}
```

## Hardcoded colour table (use directly in SVG and CSS)

| Role | Hex | Usage |
|---|---|---|
| Gold accent | `#c9a84c` | Phase labels, metric numbers, active nav border, value panel text |
| Dark navy | `#0d1b2a` | Section headings, KPI tooltip background |
| Navy gradient start | `#1a2a4a` | Header, sidebar, phase label column |
| Navy gradient end | `#243b6e` | Header gradient stop |
| Page background | `#f4f6f9` | Body |
| Section divider | `#dde3ec` | `border-top` between sections |
| Phase band (alt 1) | `#f4f7ff` | Odd phase row background |
| Phase band (alt 2) | `#f7fafd` | Even phase row background |
| Value panel bg | `#f0f4f9` | Right-column background behind white cards |

## Actor → SVG node colour mapping

**Critical: Original uses LIGHT FILL with COLOURED BORDER — do not use dark fills.**

| Actor type | fill | stroke | stroke-width | text colour |
|---|---|---|---|---|
| Human / Manager / Coordinator | `#e8f0fb` | `#2471a3` | 1.5 | `#1a1a2e` |
| AI / Automation | `#e6f7ed` | `#1e8449` | 1.5 | `#1a1a2e` |
| Vendor / External | `#ECFDF3` | `#86EFAC` | 1.5 | `#14532D` |
| System / Passive | `#f8f9fb` | `#b0bac8` | 1.5 | `#3a4a5a` |
| Decision diamond | `#fdf3d9` | `#c9a84c` | 1.8 | `#7a5a00` |
| Exit / Adverse (dashed) | `#fdeaea` | `#c0392b` | 1.5, `stroke-dasharray="5 3"` | `#8a1a1a` |
| START pill | `#0e7a4f` | `#0a5c38` | 1.5, `rx="13"` | `#ffffff` |

## Swimlane legend swatches (above SVG, using `<span class="legend-swatch">`)

Match these exactly — they use LIGHT FILL + BORDER, not solid dark colours:

| Label | Style |
|---|---|
| Automated by platform | `background:#e6f7ed; border:1.5px solid #1e8449` |
| Human action required | `background:#e8f0fb; border:1.5px solid #2471a3` |
| Decision / conditional | `background:#fdf3d9; border:1.5px solid #c9a84c` |
| Exit / adverse action | `background:#fdeaea; border:1.5px solid #c0392b; border-style:dashed` |

## Typography scale

| Element | font-size | font-weight | colour |
|---|---|---|---|
| Page title (h1) | 26px | 700 | #fff |
| Section heading | 20px | 700 | #0d1b2a |
| Section sub | 13px | 400 | #5a6a7a |
| Nav label | 12px | 500/700 | rgba(255,255,255,.55)/white |
| Metric number | 36px | 800 | #c9a84c |
| Metric label | 13px | 700 | #0d1b2a |
| Metric sub | 11.5px | 400 | #6a7a8a |
| SVG phase label | 9.5px | 700 | #c9a84c |
| SVG col header | 10.5px | 700 | #c9a84c, letter-spacing:0.06em |
| SVG node title | 10.5px | 600 | per actor fill |
| SVG value panel headline | 28-34px | 800 | #c9a84c |
| SVG value panel detail | 10px | 400 | #5a6a85 |
| SVG value panel footer | 10px | 700 | #c9a84c |

## Spacing system

| Token | Value |
|---|---|
| Section padding-y | 44px |
| Content max-width | 1480px |
| Content padding-x | 32px |
| Sidebar width | 172px (body offset: 180px) |
| Header padding | 36px 48px |
| Grid gap (metrics) | 18px |
| Grid gap (systems) | 24px |
