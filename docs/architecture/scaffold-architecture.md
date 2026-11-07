---
title: Project Scaffold — Architecture
audience: Technical leads, engineers
status: current
---

# Project Scaffold — Architecture

When a project has no repository, the dev loop has nothing to build into. `/tl:scaffold` stands up
the initial application repository from the confirmed architecture — a real, green codebase with
tooling, standards and a design system already established.

---

## 1. Architecture

### 1.1 Position in the chain

```
  BA feature breakdown ──┐
  shared-context/        │
  architecture.md        ├──►  /tl:scaffold  ──►  green base repository
  technology-stack.md    │           │                     │
  TL context graph    ───┘           │                     ▼
                                     │            /dev:plan can now map
                                     │            features onto real files
                                     ▼
                           shared-context/
                           ├── architecture.md
                           ├── technology-stack.md
                           └── coding-standards.md
                           decision-log.md  ← one DEC-### per stack choice
```

Scaffold runs **once per repository**, before the first feature. Everything after it inherits what
it established — which is why its decisions are logged rather than assumed.

### 1.2 Inputs and outputs

| Reads | Writes |
|---|---|
| Tech spec / architecture document | Repository skeleton |
| TL context graph | Package-manager manifests |
| `shared-context/` | Lint, format, type-check, test, build tooling |
| User answers to open stack decisions | A minimal passing test and a green build |
| | `README.md` |
| | `shared-context/{architecture, technology-stack, coding-standards}.md` |
| | `DEC-###` per decision, in the decision log |

---

## 2. Process — seven steps

| Step | Action |
|---|---|
| 1 | Read the architecture; establish what is **decided** versus what is **open** |
| 2 | Resolve each open decision with the user — recommendation first |
| 3 | Determine the project structure |
| 4 | Scaffold the repository |
| 5 | Write the project design docs; log each decision |
| 6 | Verify the base build is green |
| 7 | Summarise |

### 2.1 Decided versus open

The architecture document rarely pins everything down. Step 1 splits the stack into what the
document actually states and what it leaves silent:

| Decision area | Typically |
|---|---|
| Frontend framework | Often stated |
| Backend language and framework | Often stated |
| Database engine | Often stated |
| Package manager | Often silent |
| Test, lint, format, type-check tooling | Usually silent |
| Hosting / CDN | Sometimes stated |
| Repository layout — monorepo or split | Often silent |
| Authentication approach | Often partially stated |

### 2.2 Asking, not guessing

**It executes a confirmed stack; it never silently invents one.** Each open decision is put to the
user with a clear recommendation and the trade-off behind it. The answer becomes a `DEC-###` in
the decision log, so six months later the question "why this test runner?" has an answer with a
date and a rationale.

This is the architectural point of the command. A scaffold that guesses produces a repository
nobody owns the decisions in.

### 2.3 Green before features

Step 6 is a gate, not a formality. The scaffold is not finished until:

- the package manager installs cleanly
- lint passes
- type-check passes
- the minimal test passes
- the build produces an artifact

**A scaffold that does not build is worse than no scaffold**, because the first feature then
inherits a broken baseline and cannot tell its own failures from the inherited ones.

---

## 3. Establishing the design system

A greenfield repository has no visual precedent, and the first screen written becomes the
precedent forever. The design system is therefore founded **before the first screen**.

### 3.1 Derive, never invent

The component library already ships a coherent scale. Take its defaults and **narrow** them to the
set this application uses. A scale reasoned out independently is a second system competing with
the library's.

If the scaffold picked no component library, that is a decision for the human — not something to
settle by writing CSS.

### 3.2 The six scales

| Scale | Rule | Typical shape |
|---|---|---|
| Spacing | One base unit; every margin, padding and gap is a multiple | 4 px base → 4 8 12 16 24 32 48 64 |
| Type | One ratio, few steps, each pairing size **with** line-height and weight | xs s base lg xl 2xl 3xl |
| Radius | One scale, applied by component role | none sm md lg full |
| Elevation | One shadow set; depth means layer, not decoration | flat raised overlay modal |
| Colour | **Semantic names only** | `surface` `text` `border` `action` `danger` `success` `focus` |
| Motion | One duration set and one easing set | fast base slow · standard decelerate accelerate |

**Colour tokens are named for their job, never their value.** `--color-action`, not
`--color-blue`. The hue is a brand decision that can change; the job does not. A component
referencing a palette entry directly breaks the day the brand changes, and dark mode makes every
such reference wrong at once.

**Type steps carry three values.** A size without a paired line-height is how vertical rhythm
dies — two headings at the same size sit at different heights because each page picked its own
leading.

### 3.3 One token home per stack

| Stack | Token home |
|---|---|
| Tailwind | `tailwind.config` theme extension |
| Plain CSS / SCSS | Custom properties in one global stylesheet |
| MUI / Chakra / Ant | The theme object, one file |
| Bootstrap | SCSS variable overrides before the import |
| SwiftUI | One theme enum of static values |
| Jetpack Compose | `MaterialTheme` plus a tokens object |
| Flutter | `ThemeData` plus a tokens class |

**One file, one source of truth, imported everywhere.** Two token files is two systems.

### 3.4 What the agent decides, and what it does not

| Decision | Who |
|---|---|
| The scales, derived from the library's own defaults | **Agent** |
| Which semantic tokens exist and what they are named | **Agent** |
| Brand hue, typeface, logo, illustration style | **Human** — raised as a blocker |
| A novel interaction the library has no precedent for | **Human** — raised as a blocker |

Deriving a coherent system from a library's defaults is not inventing a brand. Choosing the brand
is.

### 3.5 The component set to establish

Where the library ships one, wrap it rather than restyling at each call site; where it does not,
compose it from primitives once:

```
  Button · IconButton · FormField · Select · Checkbox · Radio · Toggle
  Modal · Drawer · Table · Pagination · FilterBar · Card · Badge
  Alert · Toast · Tabs · Tooltip · Avatar · Breadcrumb
  EmptyState · LoadingState · ErrorState · PageHeader · Stack · Grid
```

---

## 4. Best-practice checks

**Accessibility is a floor, not a preference.** The established palette is verified once at
establish time against published contrast ratios — 4.5 : 1 for text, 3 : 1 for large text and
non-text, 24 × 24 px minimum targets, a visible focus indicator at 3 : 1 with a 2 px perimeter. A
token pair either clears the ratio or it does not, so the palette is checked once rather than
argued about per screen.

**Motion uses published values.** Duration bands and easing curves come from a published system
rather than being hand-tuned. A curve that is nearly right reads as wrong beside a component using
the real one.

**Coding standards are written, not assumed.** `shared-context/coding-standards.md` is authored at
scaffold time so the first code review has something to review against.

**No product features.** The scaffold creates structure, tooling and a baseline. It does not
implement behaviour — that is the dev loop's job, and mixing the two makes it impossible to tell
which decisions were architectural and which were incidental.

---

## 5. Evidence

| Artifact | Proves |
|---|---|
| `shared-context/architecture.md` | The confirmed shape of the system |
| `shared-context/technology-stack.md` | What was chosen, at what version |
| `shared-context/coding-standards.md` | What later reviews check against |
| `decision-log.md` `DEC-###` entries | Every stack decision, its options and why one was taken |
| Green base build | The baseline actually works |
| The established token home | Where every later feature inherits its visual values |
| Scaffold summary | What was founded and where |

In establish mode the summary states what was created, because every later feature inherits it —
the token file, the primitives, and what the global stylesheet is allowed to hold.

---

## 6. Boundaries

The scaffold **never** silently invents a stack, **never** implements product features, and
**never** proceeds past a red build. Brand identity and any interaction without a library
precedent are escalated to a human rather than chosen.
