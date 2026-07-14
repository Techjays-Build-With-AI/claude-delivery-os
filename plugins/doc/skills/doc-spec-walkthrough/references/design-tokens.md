# Design Tokens

Same house style as `doc-workflow` so all Delivery OS docs match: dark navy
header, gold accent, light node fills with coloured borders.

## CSS Variables (`:root`)

```css
:root {
  --navy:        #1a2a4a;
  --navy-2:      #243b6e;
  --navy-ink:    #0d1b2a;
  --gold:        #c9a84c;
  --page:        #f4f6f9;
  --card:        #ffffff;
  --border:      #dde3ec;
  --text:        #1a1a2e;
  --muted:       #5a6a7a;
  --sidebar-w:   172px;   /* body offset is 180px */
}
```

## Core accent / role colours (use directly in CSS and SVG)

| Role | Hex | Usage |
|---|---|---|
| Gold accent | `#c9a84c` | Section labels, numbers, active nav border, example figures |
| Dark navy | `#0d1b2a` | Section headings, tooltip background |
| Navy gradient start | `#1a2a4a` | Header, sidebar, footer |
| Navy gradient end | `#243b6e` | Header / footer gradient stop |
| Page background | `#f4f6f9` | Body |
| Card | `#ffffff` | Section cards, example cards |
| Section divider | `#dde3ec` | `border-top` between sections |

## State / node colour mapping (LIGHT FILL + COLOURED BORDER)

Never use dark fills on states or steps. Fill is a light tint; the border and
text carry the colour.

| Node kind | fill | stroke | stroke-width | text |
|---|---|---|---|---|
| Start / entry pill | `#0e7a4f` | `#0a5c38` | 1.5, `rx=13` | `#ffffff` (filled) |
| Terminal / done pill | `#0e7a4f` | `#0a5c38` | 1.5, `rx=13` | `#ffffff` (filled) |
| Normal state / step | `#e8f0fb` | `#2471a3` | 1.5 | `#12314d` |
| Automated / AI state | `#e6f7ed` | `#1e8449` | 1.5 | `#12402a` |
| Decision / gate (diamond) | `#fdf3d9` | `#c9a84c` | 1.8 | `#7a5a00` |
| Blocked / failure (dashed) | `#fdeaea` | `#c0392b` | 1.5, `stroke-dasharray="5 3"` | `#8a1a1a` |
| System / passive | `#f8f9fb` | `#b0bac8` | 1.5 | `#3a4a5a` |

## Edge (transition) styles

| Edge kind | stroke | width | dash | marker |
|---|---|---|---|---|
| Normal transition | `#5a6a85` | 1.6 | none | arrow |
| Automated transition | `#1e8449` | 1.6 | none | arrow |
| Failure / branch back | `#c0392b` | 1.5 | `5 4` | arrow |
| Highlighted (on click) | `#c9a84c` | 2.6 | matches base | arrow |
| Dimmed (non-selected) | `#c9cfd8` | 1.2 | matches base | arrow |

Highlight/dim are applied by JS via classes, not baked into the SVG.

## Legend swatches (LIGHT FILL + BORDER)

| Label | Style |
|---|---|
| Automated by platform | `background:#e6f7ed; border:1.5px solid #1e8449` |
| Human / manual step | `background:#e8f0fb; border:1.5px solid #2471a3` |
| Decision / gate | `background:#fdf3d9; border:1.5px solid #c9a84c` |
| Blocked / failure | `background:#fdeaea; border:1.5px solid #c0392b; border-style:dashed` |

## Typography scale

| Element | size | weight | colour |
|---|---|---|---|
| Page title (h1) | 26px | 700 | #fff |
| Section heading (h2) | 20px | 700 | #0d1b2a |
| Section sub | 13px | 400 | #5a6a7a |
| Module eyebrow | 11px | 700 | #c9a84c, letter-spacing .12em, uppercase |
| Nav label | 12px | 500/700 | rgba(255,255,255,.55) / #fff |
| Card title | 15px | 700 | #0d1b2a |
| Body | 14-15px | 400 | #1a1a2e |
| Example figure | 22-28px | 800 | #c9a84c |
| SVG state title | 11px | 600 | per node |
| SVG small label | 10px | 400 | #5a6a85 |
| Mono (IDs, commands) | 13px | 500 | #12314d, `font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace` |

## Spacing

| Token | Value |
|---|---|
| Section padding-y | 44px |
| Content max-width | 1240px |
| Content padding-x | 32px |
| Sidebar width | 172px (body offset 180px) |
| Header padding | 36px 48px |
| Card gap | 18px |
| Card radius | 10px |
| Card padding | 20px |
