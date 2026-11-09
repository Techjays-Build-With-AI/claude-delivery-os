# UI consistency — writing a screen that belongs in this app

**Purpose.** `pattern-inference.md` makes new code structurally match the repo. This makes it *look*
like the repo, and makes the repo worth looking like. A section that imports correctly and names
things correctly, then renders its own fonts, its own spacing and its own motion, reads as bolted
on — because it is.

**Budget.** ≤ 4 targeted reads in follow mode, on top of pattern-inference's. Establish mode (§2)
costs more and happens once per repo.

**Stack-agnostic.** Web, mobile and desktop all have a component library, a token source and a set
of primitives, whatever they are called. Every rule below names the decision, not the syntax.

---

## 0. Which mode are you in

| The repo has | Mode | Do |
|---|---|---|
| a component library **and** a token source | **follow** | §1 detect, then §3–§8 |
| a library but no tokens | **follow + establish tokens** | §2.1 only, from the library's own scales, then §3–§8 |
| neither — a fresh scaffold | **establish** | §2 in full, **before the first screen**, then §3–§8 |

**Establish mode is a one-time act and it must happen on the first UI feature, not drift in.**
Every rule in this file works by matching a precedent. Write the first screen without a system and
the precedent becomes whatever that screen happened to do — and §3's "match the neighbour" will
then propagate it, faithfully, forever. A bad scale is as contagious as a good one.

---

## 1. Detect the system before writing anything

| Look for | Where | What you get |
|---|---|---|
| **Component library** | the dependency manifest | Bootstrap, Tailwind, MUI, Chakra, Ant, SwiftUI, Compose, Flutter widgets |
| **Token source** | `:root` CSS vars, a theme file, `tailwind.config`, a design-tokens module | the real colours, type scale and spacing steps |
| **Layout primitives** | one existing page | the container/row/column or stack/grid wrappers every screen uses |
| **Shared components** | the shared/common folder | the table, form field, button, modal, empty state you are expected to reuse |
| **Motion** | the token source, or any transition in a shared component | the durations and easings already in use |
| **State treatments** | one existing list or table | how this app renders loading, empty and error |

Record what you found in the build summary (§9). "No token source" is a finding, not a silence —
it is what puts you in establish mode.

---

## 2. No system yet — establish one before the first screen

**Derive, never invent.** The component library already ships a coherent scale: Tailwind's spacing
and type scales, MUI's theme defaults, Material/Cupertino, Compose's `MaterialTheme`, Bootstrap's
`$spacers`. Take its defaults and *narrow* them to the set this app uses. A scale you reasoned out
yourself is a second system competing with the library's.

**A repo should never reach you in establish mode.** `/tl:scaffold` asks the styling question,
installs the system, and writes `shared-context/ui-standards.md` with a pointer to it in the repo's
`CLAUDE.md` — **read that document first, every time.** Establish mode is the exception: a repo
scaffolded before that rule existed, a reverse-mapped brownfield repo, or a hand-made one.

When you are in it anyway, **establish the system and keep building — do not stall.** Install the
library the repo's `CLAUDE.md` or `shared-context/technology-stack.md` names; where neither names
one, use **Tailwind + shadcn/ui** and log it as a `DEC-###`. Settle the direction and palette by
§2.4, derive the six scales from the library's published defaults, compose the primitives, and say
so in the build summary (§9).

**Then write it down as `shared-context/ui-standards.md`**, with the pointer block in the repo's
`CLAUDE.md` — both shapes are in `tl-project-scaffold/references/scaffold-guide.md` §4. Where the
document already exists, extend it in place rather than starting a second one, and where the repo
already carries its own styling rules with stable ids, carry those ids over unchanged so existing
checks and `DEC-###` citations keep resolving.

Establishing a system and leaving no document behind means the next session establishes a second
one. That is the duplication this file exists to prevent, and it is the whole reason establish mode
writes anything at all.

Stopping for a `PB-###` here was the old rule and it did not survive contact with a build: a hard
stall mid-feature always loses to "write just enough CSS to make the page legible", and nothing
downstream checks the difference. Raise a `PB-###` only for the brand-level choices in §2.3 — hue,
typeface, logo — and carry on with neutral defaults until they are answered. What you must never do
is write per-screen CSS *instead of* a system; that is the one outcome this file exists to prevent.

### 2.1 The six scales

Every visual value in the app comes from one of these. There is no seventh source.

| Scale | Rule | Typical shape |
|---|---|---|
| **Spacing** | one base unit; every margin, padding and gap is a multiple of it | 4px base → 4 8 12 16 24 32 48 64 |
| **Type** | one ratio, few steps, each step pairs a size **with** a line-height and weight | xs s base lg xl 2xl 3xl |
| **Radius** | one scale, applied by component role, not per instance | none sm md lg full |
| **Elevation** | one shadow set; depth means layer, not decoration | flat raised overlay modal |
| **Colour** | **semantic names only** | `surface` `surface-muted` `text` `text-muted` `border` `action` `action-hover` `danger` `warning` `success` `focus` |
| **Motion** | one duration set + one easing set (§6) | fast base slow · standard decelerate accelerate |

**Every token pair clears WCAG 2.2 AA contrast before the system is considered established** —
4.5:1 for body text, 3:1 for large text and for borders, icons and focus rings (§10.1). Verify the
pairs once, here, rather than discovering a failure screen by screen.

**Colour tokens are named for their job, never their value.** `--color-action`, not `--color-blue`,
and never `blue-500` referenced directly in a component. The hue is a brand decision that can
change; the job does not. A component referencing `blue-500` breaks the day the brand turns green,
and every such reference has to be found by hand. Dark mode makes all of them wrong at once.

**Type steps carry three values, not one.** A size without a paired line-height is how vertical
rhythm dies — two headings at the same size sit at different heights because each page picked its
own leading.

### 2.2 Where the scales live, per stack

| Stack | Token home | Consumed as |
|---|---|---|
| Tailwind | `tailwind.config.{js,ts}` → `theme.extend` | utility classes only |
| Plain CSS / SCSS | `:root` custom properties in one global stylesheet | `var(--space-4)` |
| MUI / Chakra / Ant | the theme object, one file | `theme.spacing(2)`, `sx`, styled API |
| Bootstrap | SCSS variable overrides before the import | variables + utilities |
| SwiftUI | one `Theme` / `DesignSystem` enum of static values | `Theme.spacing.md` |
| Jetpack Compose | `MaterialTheme` + a custom `Tokens` object | `MaterialTheme.spacing.md` |
| Flutter | `ThemeData` + a `Tokens` class | `Theme.of(context)` / `Tokens.spaceMd` |

**One file, one source of truth, imported everywhere.** Two token files is two systems.

### 2.3 What the agent decides, and what it does not

| Decision | Who |
|---|---|
| The scales themselves, derived from the library's defaults | **agent** |
| Which semantic tokens exist and what they are named | **agent** |
| Design direction, and the palette mapped from a published system (§2.4) | **agent** |
| Brand hue, font family, logo, illustration style | **human** → `PB-###` |
| A novel interaction the library has no precedent for | **human** → `PB-###` |

Deriving a coherent system from a library's own defaults is not inventing a brand. Choosing the
brand is.

### 2.4 Direction and palette — research them, never taste them

**A consistent app is not yet a good one.** §§1–3 make every screen agree with every other screen.
A government form is perfectly consistent. What follows is what makes the agreement worth having,
and it is the one part of this file where you look outside the repo before deciding.

**Settle the direction from the product, not from preference.** Read
`shared-context/` and the scope: who uses this, how often, how much data is on a screen at once, is
it read or operated. A personal to-do app used twice a day and a dashboard watched all day are
different visual problems. Write the answer as three or four lines — density, tone, what the screen
should feel like to return to — and put it at the top of the `ui-system` block. Everything below it
is then a consequence rather than a choice.

**Build the palette from a published system.** WebFetch one and map it onto the semantic roles in
§2.1 — do not pick hex values:

| Source | Use it when |
|---|---|
| **Radix Colors** — `radix-ui.com/colors` | default; its scales are built for semantic steps (background, interactive, border, solid, text) and ship light and dark pairs |
| **Material 3 tonal palettes** — `m3.material.io/styles/color` | the repo already uses Material, or the product wants its tonal system |
| **The component library's own themes** | shadcn, MUI or Chakra ship themes — prefer a real one over a new one |

Record which source and which scale, in the `DEC-###`. A palette whose origin you cannot name is a
palette you invented.

**Verify before you write it down.** Every foreground/background pair in the palette clears
WCAG 2.2 AA (§10.1) — 4.5:1 for body text, 3:1 for large text and UI boundaries — in **both** light
and dark. A pair that fails is not a styling preference to revisit later; it is not in the palette.

**Where the references come from, strongest first.**

| Source | How you use it |
|---|---|
| **A reference the user hands you** — a screenshot, a mock-up, a photo of a whiteboard, their existing product, a brand hue, a logo, a font | **Read it.** You can see images. Pull the direction out of it: layout, density, weight, how colour is used, what the eye lands on first. Name it in the `DEC-###` as the source. It outranks everything below, and research only fills what it leaves open |
| **The component library's own blocks**, indexed by the surface you are building | the structural reference, and the only one that arrives as code. shadcn ships `dashboard-01`, `sidebar-0x`, `login-0x` at `ui.shadcn.com/blocks`, installable with `npx shadcn add <block>`; MUI, Chakra and Material ship equivalents. Start from the block that matches the surface rather than composing one from parts. Check the licence at the source before shipping it |
| **A published design system** whose domain matches the product | for patterns the library has no opinion on — data tables, dense dashboards, long service forms. Take the pattern and its rationale, not its brand |

**Ask for a reference before you invent one.** Where the user has given no visual direction and a
human is present, ask — one line, offering to work from any screenshot they like. A picture they
chose beats a palette you derived, every time, and it costs one question.

**You can look at an image you can name — you cannot browse for one.** `WebFetch` returns text and
never sees a picture, but downloading the file does: `curl` the direct image URL into your
scratchpad, then read the file. Looking at the library's own block previews before composing a
screen is worth doing, and it costs two calls.

The limit is the URL, not the picture. Get it out of the page's markup first — ask `WebFetch` for
the image URLs on a documented page, then fetch what it names. A site that renders its gallery
through script or behind a login returns nothing to read the URLs out of, so there is no route to
its images at all. For *curated* taste — "make it feel like this" — ask the user; choosing is what
they are better at, and you cannot shop.

**Never claim to have seen what you only read about.** Describing a design from alt text, a
filename or a search result, as though you had looked at it, is the one failure here that
contaminates everything downstream.

**References inform direction; they are never copied.** Reproducing another company's proprietary
design, layout or brand is out, whatever the resemblance is worth — including from a reference the
user supplied, unless it is their own product or their own brand. Take the principle, leave the
artefact.

---

## 3. Five rules, and they are hard

**Reuse before you create.** Search the shared folder for a component that does the job. Write a new
one only when nothing fits, and compose it from the primitives already there. A second table
implementation in a repo that has one is a defect, not a style choice.

**Never add a second UI library.** Whatever the manifest already has is the library. Adding another
to get one component is how an app ends up with three button styles.

**No hardcoded visual values where a token exists.** No hex colours, no `px` font sizes, no magic
spacing, no inline `transition: 0.3s`. Use the variable, the theme key or the library's scale.
Where no token exists, use the library's own default scale rather than a number you chose.

**Match the neighbour, not your taste.** Open the section that will sit next to yours and copy its
shape: same container, same heading level, same spacing rhythm, same table and form components, same
empty and loading states. Consistency with one real neighbour beats any general principle.

**No new stylesheet when the repo has a system.** A per-component `.css` file alongside a
Bootstrap or Tailwind app means the system was ignored. Extend the existing stylesheet or use the
library's utilities.

---

## 4. Reusable, or it is a defect

**A visual element used on two screens is a shared component.** The second use is the trigger — not
a guess that it might be reused later, and not waiting for a third.

**The set nearly every app needs.** Where the library ships one, wrap it rather than restyling it at
each call site; where it does not, compose it from primitives once:

`Button` · `IconButton` · `FormField` (label + control + hint + error) · `Select` ·
`Checkbox` / `Radio` / `Toggle` · `Modal` · `Drawer` · `Table` / `DataTable` · `Pagination` ·
`FilterBar` · `Card` · `Badge` · `Alert` / `Toast` · `Tabs` · `Tooltip` · `Avatar` ·
`Breadcrumb` · `EmptyState` · `LoadingState` / `Skeleton` · `ErrorState` · `PageHeader` ·
`Stack` / `Grid` layout primitives.

**Variants live inside the component, never at the call site.** `<Button variant="danger" size="sm">`
— not a `className` that re-colours a button from outside. The moment a caller restyles a component,
that component has two definitions and only one of them is reviewed.

**A component owns the spacing inside it; the caller owns the space around it.** A component with an
outer margin cannot be reused in a layout that spaces its own children — this is the most common
reason a "reusable" component gets copied instead of reused.

---

## 5. Naming and location

**Name by role, never by appearance.** `btn-primary`, `card-surface`, `text-muted` — not
`btn-blue`, `card-white`, `text-grey`. An appearance name is a lie the first time the theme changes.

**One naming convention per repo, whatever it already uses.** BEM, utility-first, CSS modules,
styled-components — detect it (§1) and follow it. Mixing two is worse than either.

| Stack | Component file | Styles |
|---|---|---|
| Utility-first (Tailwind) | `components/<Role>/<Role>.tsx` | utilities inline; shared recipes defined once, not re-typed |
| CSS modules | `components/<Role>/<Role>.tsx` | `<Role>.module.css` beside it |
| Global stylesheet (Bootstrap/SCSS) | `components/<Role>/<Role>.tsx` | a partial in the global sheet, imported once |
| CSS-in-JS / MUI | `components/<Role>/<Role>.tsx` | `styled` / `sx` in the same file, tokens from the theme |
| SwiftUI / Compose / Flutter | one view / composable / widget per file, by role | styling from the theme object, never literals |

**Never a stray stylesheet at a page.** Page-level CSS is where consistency dies: it is invisible to
every other page and it always duplicates a token.

**Global CSS holds only** the reset/normalize, the token definitions, base element styles (`body`,
headings, links) and font-face declarations. Component rules do not belong there.

---

## 6. Motion — one system, not one per page

**Three duration steps and three easings, applied by rule.** Motion that differs per page is the
clearest signal that several people built the app without talking to each other.

| Use | Duration | Easing |
|---|---|---|
| hover, focus, small state change | `fast` (~100–150ms) | standard |
| dropdown, tooltip, accordion, tab | `base` (~200–250ms) | decelerate in, accelerate out |
| modal, drawer, page transition | `slow` (~300–400ms) | decelerate in, accelerate out |

These map onto Material Design 3's published duration bands and easing curves — take the real
values from §10.2 rather than hand-tuning near-misses.

**Animate only compositor-friendly properties** — `transform` and `opacity`. Animating `width`,
`height`, `top` or `margin` forces layout every frame and is the usual reason a UI feels cheap on a
mid-range phone.

**Enter and exit are not the same curve.** Things arriving decelerate; things leaving accelerate. A
modal that fades out on the curve it faded in with feels sticky.

**Honour reduced motion.** `prefers-reduced-motion` (or the platform equivalent) drops transforms
and keeps opacity. An accessibility requirement, not a nicety.

**No per-element duration literals.** `transition: 0.3s` written inline is a seventh scale.

---

## 7. States — what separates a product from a demo

**Every interactive element ships five states**, taken from the library's own treatment:
`default` · `hover` · `focus-visible` · `active` · `disabled`.

**A visible focus state is never removed.** `outline: none` without a replacement makes the app
unusable by keyboard and fails WCAG 2.2 SC 2.4.13 outright — the indicator needs 3:1 contrast against
the unfocused state and at least a 2px perimeter (§10.1).

**Every data surface ships four**: `loading` · `empty` · `error` · `populated`.

Build them with the shared `LoadingState` / `EmptyState` / `ErrorState` components. A screen that
renders only the populated case is unfinished — the other three are what users hit on a slow
connection, on day one with no data, and when the API is down.

**An empty state says what to do next**, not just "No data". The difference between a demo and a
product lives almost entirely in these three states.

---

## 8. Density and alignment

**One density per surface type.** Table rows, form fields and list items each have a height, and it
is the same on every screen. Two tables at different row heights read as two applications.

**Align to the grid.** Every element starts on a spacing-scale multiple. Optical exceptions (an icon
beside text) are fine; arbitrary 13px offsets are not.

**One container width and one page padding**, defined once and used by every page. A page that sets
its own max-width will not line up with the one beside it.

---

## 9. What the build summary must say

One line in follow mode, so a reviewer can check it rather than take it on trust:

```
UI: react-bootstrap · tokens from src/styles/_variables.scss · reused DataTable, FormField, EmptyState
    new: AssetFilters (composes Row/Col/Form.Control) · no new stylesheet
```

In **establish mode**, say what was founded and where, because every later feature inherits it:

```
UI (established): tailwind · tokens in tailwind.config.ts (spacing 4px base, type 7 steps,
    semantic colours, motion fast/base/slow) · primitives: Button, FormField, Table, Modal,
    EmptyState, LoadingState, ErrorState · global.css holds reset + tokens only
```

If you had to break a rule, name which and why. An unexplained break reads as an oversight.

---

## 10. Published standards this file defers to

**These are not preferences.** Where a published spec gives a number, use the number — it is
checkable in review, and in the accessibility cases it is a legal requirement in several markets.
Cite the source in the build summary when a value comes from here.

### 10.1 Accessibility — WCAG 2.2 Level AA (hard floor)

| Requirement | Value | Applies to |
|---|---|---|
| Text contrast | **4.5:1** | body text against its background |
| Large-text contrast | **3:1** | ≥ 24px, or ≥ 18.66px bold |
| Non-text contrast | **3:1** | icons, graphical objects, input borders, focus indicators, against adjacent colour |
| Target size (SC 2.5.8) | **≥ 24 × 24 CSS px** | every interactive target; spacing counts if it pushes neighbours apart |
| Focus appearance | **3:1** between focused and unfocused state, area ≥ a **2px** perimeter of the component | every focusable element |

**This is what makes §2's colour tokens testable.** A semantic token pair (`text` on `surface`,
`action` on `surface`) either clears 4.5:1 or it does not — so the palette is verified once, at
establish time, rather than argued about per screen. Check every pair when you found the system,
and again whenever a token value changes.

**Target size is the rule most often missed on mobile.** A 20px icon button passes visual review
and fails SC 2.5.8. Give the *target* 24px even when the glyph is smaller.

### 10.2 Motion — Material Design 3 duration and easing tokens

M3 publishes duration bands and cubic-bezier easings; §6's three steps map onto them, so take the
real values rather than inventing near-misses:

| §6 step | M3 band | Range |
|---|---|---|
| `fast` | short | **50–200ms** |
| `base` | medium | **250–400ms** |
| `slow` | long | **450–600ms** |

M3's `standard` easing is `cubic-bezier(0.2, 0.0, 0.0, 1.0)`. Use the published curves for
standard / decelerate / accelerate rather than hand-tuned ones — a curve that is nearly right reads
as wrong beside a component that uses the real one.

Durations above 600ms (M3's extra-long, 700–1000ms) are for deliberate, attention-carrying
transitions only. A dropdown at 700ms feels broken.

### 10.3 Token file format — W3C Design Tokens (DTCG)

When the stack's token home is a data file rather than framework config (§2.2), write it in the
**DTCG format**: JSON, `$`-prefixed properties (`$value`, `$type`), tokens able to reference other
tokens by alias. It is a W3C Community Group **Candidate Recommendation** and is stable.

Two reasons it matters here: a token file in a standard format can be read by design tooling without
a bespoke parser, and alias support is what lets `action` point at a palette entry so the brand hue
changes in exactly one place.

### 10.4 Pattern reference — when the library gives no precedent

Before inventing a component or an interaction, check how a mature system solved it. These are
reference material for *patterns and states*, not libraries to install (§3 still forbids a second
library):

| System | Strongest for |
|---|---|
| **Material Design 3** (m3.material.io) | motion, elevation, state layers, adaptive layout |
| **Apple HIG** (developer.apple.com/design) | iOS/macOS platform conventions, touch targets |
| **GOV.UK Design System** | accessible form patterns, error summaries, plain-language empty and error states |
| **IBM Carbon**, **Atlassian**, **Shopify Polaris**, **GitHub Primer** | data tables, filtering, empty states, enterprise density |

**Read them for the pattern, then build it from the repo's own library and tokens.** Copying another
system's visual language into an app built on a different one produces exactly the collision this
file exists to prevent.

---

## 11. Still a human decision

Brand identity — the hue, the typeface, the logo, the illustration style — and any interaction the
library has no precedent for are a **`PB-###` for the human**, raised at `/dev:plan` time, never
invented at build time.

What is *not* a human decision: deriving a coherent spacing, type, radius, elevation and motion
system from the component library's own defaults. That is this file's job, and leaving it undone is
what produces an app where every screen is internally tidy and no two of them agree.
