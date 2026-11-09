# Scaffold guide — required decisions, defaults, and the scaffold checklist

The method behind `tl-project-scaffold`. Read this before scaffolding. It holds the required-decision checklist (what must be pinned down before you can scaffold a layer), how to recommend a default, the skeleton/tooling checklist, and the green-base verification.

---

## 1. Required decisions

These are the choices a scaffold can't proceed without. For each: take it from the architecture/spec if it's stated (confidence `Confirmed`); if it's silent, **ask the user with a recommendation** (§2). A decision marked **critical** blocks scaffolding of its layer until resolved — never guess it silently.

| Decision | Critical? | Where the spec usually states it |
|---|---|---|
| **Application type** — frontend app · API service · full-stack app · CLI · worker/job | ✕-critical | architecture overview |
| **Repo layout** — single package · monorepo (workspaces) · polyrepo | ✕-critical | architecture / team convention |
| **Repo target location** — where the code is created | ✕-critical | ask (recommend `./app` or a given path) |
| **Frontend framework + language** (if there's a UI) | ✕-critical (for UI) | tech stack; context graph = # of pages |
| **UI styling approach + component library** (if there's a UI) | ✕-critical (for UI) | rarely stated — **ask the user** (§2); default **Tailwind + shadcn/ui** if they decline |
| **Backend language + framework** (if there's server logic) | ✕-critical (for backend) | tech stack; context graph = # of endpoints |
| **Database engine** (if there's persistence) | ✕-critical (for data) | data schema; context graph entities |
| **Package manager** | ✕-critical | convention (npm/pnpm/yarn, pip/poetry/uv, go mod, …) |
| **Test framework** | ✕-critical | tech stack / convention |
| **Lint + format tooling** | non-critical → recommend | convention |
| **Type checking** (typed langs) | non-critical → recommend | convention |
| **Build tooling / bundler** | non-critical → recommend | framework default |
| **Hosting / CDN / deploy target** | non-critical for scaffold → note as open | infra section |
| **Auth approach** | non-critical for scaffold → note as open | security section |
| **CI provider** | non-critical → recommend a starter workflow | delivery section |
| **Node/Python/Go version** (runtime) | non-critical → recommend LTS | tech stack |

Hosting, auth, and CI don't block the initial skeleton — record them as open decisions for later rather than stalling the scaffold, unless the spec already states them.

---

## 2. How to recommend a default

When a required decision is open, ask a **focused question with a recommended option first and a one-line rationale grounded in the project**, plus 1–2 credible alternatives with their trade-off. Ground the recommendation in evidence you have — the project profile, the team's stated skills, and the shape of the context graph (many interactive pages → a component framework; mostly endpoints + jobs → an API service; heavy relational entities → a SQL engine).

Example:

> **Database engine isn't specified.** Recommend **PostgreSQL** — the context graph has 9 relational entities with foreign-key relationships and the data-register implies transactions. Alternatives: MySQL if the team standardises on it; SQLite only for a throwaway/local prototype.

> **Nothing specifies how the UI is styled.** Recommend **Tailwind + shadcn/ui** — the context graph has 11 pages sharing forms, tables and dialogs, and shadcn drops those in as editable source the dev agent extends instead of re-inventing. Alternatives: MUI if you want a themed component set out of the box; Tailwind alone if you'd rather own every primitive.

**Styling is a required decision, not a detail you can defer.** It is the one choice on this list
the architecture almost never states, and the only one whose absence is invisible until a human
opens the app. A repo scaffolded without it reaches `/dev:build` with no library and no tokens,
and the first feature becomes the design system by accident.

**Ask the styling question in two parts: the library, and a reference.** The second half is the one
that decides whether the app looks designed. *"Send me any screenshot of a UI you'd like this to
feel like — a product you use, a mock-up, a sketch — and I'll build the direction from it."*
You can read images; you cannot go and find them, so this is the only way a
visual reference ever reaches you. One picture the user chose carries more than any palette you
derive, and asking costs a single line. Where they give one, record it as the source in the styling
`DEC-###`; where they don't, fall back to the researched path below.

**If the user declines to choose, scaffold Tailwind + shadcn/ui** and record it `Assumed`. A default is the path most projects take — unattended runs skip every question — so it has to be the good outcome, not the minimal one. Tailwind alone leaves the agent inventing what each component looks like; shadcn gives it designed source to extend at the same install cost. Do not scaffold
a UI repo with no styling system at all — "plain CSS, decided later" is the outcome this row exists
to prevent. Brand-level choices inside the system — hue, typeface, logo — stay open questions; the
scales and the semantic token names do not.

Batch related questions (all frontend choices together, all backend together). Only ask what you actually need to scaffold; don't turn it into a survey. Record the user's answer with confidence `Confirmed`; if the user says "use your recommendation", record it `Assumed` and note it was an accepted default.

---

## 3. Skeleton + tooling checklist

Prefer the stack's **official generator/starter** over hand-rolling — it gives an idiomatic, green baseline you can trust:

- Frontend: `create-vite`, `create-next-app`, `ng new`, `npm create svelte`, …
- Backend: `spring init`, `nest new`, `poetry new` / `uv init`, `go mod init` + layout, `dotnet new webapi`, …
- Full-stack/monorepo: the framework's monorepo template or a workspaces layout (`pnpm-workspace.yaml`, `turbo`, `nx`), only if the layout decision was monorepo.

### 3.1 Research the structure — do not invent it

**A generator gives you a hello-world tree, not a production layout.** `create-vite` gives you
`src/App.tsx` and stops. What goes beside it — how features are sliced, where hooks, API modules,
types and shared components live — is the decision that every later feature inherits, and it is the
one most often improvised.

**Before creating folders, look up the current recommended structure for the exact stack and major
version you just confirmed.** Use `WebFetch` against, in this order:

1. **The framework's own documentation** — its project-structure / directory-structure page. This is
   authoritative and version-specific.
2. **The framework's official starter or template repository** — what its maintainers actually ship.
3. **One widely-adopted community reference** for the architectural pattern (feature-sliced design,
   hexagonal, layered) where the framework's docs stay deliberately unopinionated.

**Pin it to the version you are installing.** A structure recommended for v5 can be wrong for v7 —
routing, server components and data loading all move between majors. Fetch for the version in the
manifest, not for the framework in general.

**Record the sources** in `shared-context/architecture.md` and cite them in the `DEC-###` for the
layout. A structure nobody can trace is a structure the next person will argue with.

**Prefer boring and conventional.** The goal is a layout a developer joining the project recognises
on sight — not the cleverest arrangement available. Where sources disagree, follow the framework's
own docs.

### 3.2 Build the structure, then prove it with one worked example

**Create the folders you documented, and put one real unit in each.** A standards document that
describes `src/features/<slug>/`, `src/hooks/` and `src/lib/apiClient.ts` in a repo that contains
none of them is not a standard — it is a wish. The first feature then has no neighbour to match,
invents its own arrangement, and *that* becomes the architecture.

Scaffold one reference implementation per unit kind the stack has — one feature slice, one page or
screen, one hook, one API module, one type module; one route, one service, one model, one migration
— wired end to end and covered by the trivial passing test. It can be a health check or an "about"
page; it does not need product meaning. It needs to exist, because **`match the neighbour` is the
rule every later feature runs on, and this is what supplies the neighbour.**

Then write `coding-standards.md` §2 to describe **what you actually built**, not what you intended
to build, and mark it `confirmed` rather than `inferred`.

Whatever the generator leaves out, ensure the repo has:

- [ ] **Package-manager manifest(s)** with pinned/compatible versions (`package.json`, `pyproject.toml`, `go.mod`, …).
- [ ] **UI styling system** (if there's a UI) — chosen library installed, its token source created (spacing · type · radius · elevation · semantic colour · motion), and the base primitives composed once (`Button`, `FormField`, `Card`, `EmptyState`, `LoadingState`, `ErrorState`). Every token pair clears WCAG 2.2 AA contrast before the scaffold is called done.
- [ ] **Design direction and palette researched, not chosen by taste** — follow `dev-stack-adaptive-implementation` `references/ui-consistency.md` §2.4: settle the direction from the scope, map the palette from a published system (Radix Colors by default), verify every pair at AA in light and dark, and cite the source in the styling `DEC-###`. That file is the single definition; do not restate the method here. A brand the user already owns outranks all of it.
- [ ] **Lint + format** config (ESLint + Prettier, Ruff/Black, golangci-lint, …) with a runnable script.
- [ ] **Type checking** for typed languages (`tsconfig.json`, `mypy.ini`, …) with a runnable script.
- [ ] **Test framework** wired with **one trivial passing test** (proves the harness runs).
- [ ] **Build** script that produces an artifact / compiles cleanly.
- [ ] **`.gitignore`** appropriate to the stack (never commit `node_modules`, `.env`, secrets, build output).
- [ ] **`.env.example`** if the app needs configuration — placeholders only, never real secrets.
- [ ] **README.md** — how to install, run, test, build, and the project layout.
- [ ] **git initialised** on a base branch (don't force a first commit if the user's flow differs; at minimum leave a clean, staged tree).

Keep the scaffold **minimal and idiomatic** — a skeleton with a green build, not a half-built feature. Do not add product pages, endpoints, or business logic; the dev agent's `feature-delivery-loop` does that per feature.

---

## 4. Project design docs (shared-context/)

Write these so the dev agent (and future TL runs) build against a confirmed foundation:

- **`technology-stack.md`** — the exact stack and versions chosen, one row per layer, each citing the `DEC-###` that decided it. **A repo with a UI carries a `Styling` row and a `Design tokens` row**, naming the library and the token file's path. A frontend table listing only tooling — language, bundler, test runner, linter — is how an app ends up with no design system.
- **`architecture.md`** — the architecture the scaffold realises: components, how they fit, the repo layout, and the runtime shape. Reconcile with the spec; where you filled a gap, mark it and cite the decision.
- **`coding-standards.md`** — the file the dev agent's implementation step follows AND the review dimension checks against. Mandatory sections (concrete, per-stack values — no vague words like "reasonable" or "clean"; every limit is a NUMBER a lint tool or reviewer can check):

  1. **Naming** — casing rule per identifier kind (function, type, constant, module, file, test) with 1-line examples; forbidden suffixes/prefixes.
  2. **Folder structure & file placement** — where each kind of unit lives; how a new unit joins an existing folder vs starting a new one.
  3. **Lint & format rules** — the enabled rulesets (name them), the delta from stock defaults, the format command.
  4. **Test conventions** — file location relative to source, filename pattern, test naming, fixture location, mocking approach, coverage floor per test tier.
  5. **Error-handling & logging** — the ONE error paradigm (exceptions / result types / codes), how errors propagate, the ONE logger, level policy, what NEVER gets logged (PII, secrets, tokens).
  6. **Function complexity budget** — cyclomatic complexity limit per function, maximum function length in lines, maximum nesting depth, maximum parameter count, maximum boolean-flag parameters. Numeric limits, not words. If lint has a plugin that enforces the limit, name it and set the threshold to the same number.
  7. **Duplication policy** — the maximum duplicated block size before extraction is required (e.g. "identical ≥ 8 lines → extract"); the maximum copy-of-pattern rate (e.g. "≥ 3 near-identical blocks → helper required").
  8. **Recursion policy** — when recursion is idiomatic in this stack (tail-call safe? memoized? bounded input?), when iteration is the required alternative, what a recursive function MUST document (base case, termination proof, worst-case depth). Stack-dependent — record what applies here.
  9. **Constants & magic values** — where numeric/string literals other than the neutral small set (`0`, `1`, `-1`, `""`, `null`, `true`, `false`) live; naming rule for constant groups; enum usage rule.
  10. **State & side effects** — where global mutable state is allowed (usually nowhere); how config is read; how time / random / external IO gets injected so tests can control them.
  11. **Comments & documentation** — when a comment is required, when it's forbidden, the doc-comment format for public exports, the "why not what" rule.
  12. **Anti-patterns forbidden in this repo** — explicit list (god function / god class / god file, boolean-flag chains beyond §6's limit, premature abstraction with one implementation + one caller, dead code left behind, comment-code mismatch, silent catches, magic sleeps in tests, snapshot-only tests, mocks that assert nothing). Every entry has ONE line naming what the reviewer flags on.


### Authoring the two-tier engineering standards (v2 contract)

Full contract:
`plugins/delivery-os-core/skills/delivery-os-conventions/references/engineering-standards.md`.

**Infer first, ask only what is left, never invent.**

| Step | Action |
|---|---|
| 1 | Detect language, framework, architecture |
| 2 | Read lint config, package manifests, test layout, a sample of source |
| 3 | Derive module boundaries and the **actual** dependency direction between layers |
| 4 | Write only rules the evidence supports |
| 5 | **Ask** the developer for the gated decisions evidence cannot settle |
| 6 | Anything still open → `status: needs-author` |
| 7 | Stamp `source:` provenance on every rule |

**The status decides whether a rule is policy:**

| Evidence | status | Enforced? |
|---|---|---|
| A lint config declares the limit | `confirmed` — the config **is** the approval, `source.type: tooling-config` | yes |
| The code consistently does X | `inferred` — evidence of practice, **not** approval | **no**, until a human confirms |
| Nothing in the repo settles it | `needs-author` | no; a gated section stays unresolved |
| The section does not apply | `not-applicable` with a one-line reason | n/a |

**Observed practice is not policy.** A repo that consistently skips input
validation is consistently wrong; promoting that to a `confirmed` rule would
encode the defect as the standard. Inferred rules are proposals, surfaced in the
run summary for a human to confirm.

**Never invent a threshold to make the document look complete.** No retry
behaviour anywhere → `needs-author`, not `3`.

**Set `enforcement.available` honestly.** A §13 dependency-direction rule names
`dependency-analysis` as its method, but no stack in the QA harness matrix
installs a dependency-graph checker — so it ships `available: false` and is
reviewer-validated until `/qa:setup` wires one.

**Frontmatter:** `standards_version: 2`, `migration_status`,
`gated_sections: ["1-12", "13", "19", "20"]`.

  Sections 1–5 describe existing repo shape (name what IS). Sections 6–12 declare ENFORCEABLE limits (name what MUST NOT happen). The dev agent's write-time check (Rule 13 in `dev-stack-adaptive-implementation`) and the code-review Dimension 8 both read this file — if a section is missing or vague, they can't enforce it.

  Where a limit is stack-specific (e.g. cyclomatic threshold, recursion policy), pick the value that matches the stack's lint ecosystem defaults. Record the value and the rationale; don't leave it blank.

Every layer carries standard frontmatter (`doc_type`, `produced_by: tl`, `schema_version`, `generated_at`).

---

### Write the UI standard — `shared-context/ui-standards.md`

**The UI standard is a document, not a note in `CLAUDE.md`.** It sits beside `coding-standards.md`
and carries the same weight: `coding-standards.md` governs the code, `ui-standards.md` governs the
screen, and on anything visual the UI file wins. Write it for any repo with a rendered UI.

Standard frontmatter (`doc_type: ui-standards`, `produced_by: tl`, `schema_version`, `status`,
`generated_at`, `applies_to`). Sections:

| § | Holds |
|---|---|
| 1 Direction | the §2.4 paragraph — who uses this, how often, how dense, how a screen should feel to return to. Everything else is a consequence of it. Plus what is *not* decided: brand hue, typeface, logo, dark mode |
| 2 The scales | spacing · type · radius · elevation · colour · motion, each with its token names and its current state. Name the gaps explicitly — a scale you left out is the one the next feature invents |
| 3 Colour and contrast | the palette, its published source, and a **measured ratio per token** against its background with the floor it must clear. A failing row is an open defect with the fix, not a note |
| 4 Rules | the enforceable one-line rules, each with a stable id. Where a project already has such ids, carry them over unchanged so existing checks and `DEC-###` citations keep resolving |
| 5 Reuse | the primitives directory, what is already in it, and the second-use trigger |
| 6 What every screen owes | interactive states, data-surface states, motion on change, nothing by colour alone |
| 7 Open | the `PB-###` items and any measured defect, with an owner |

**Do not duplicate it anywhere.** A visual rule stated in two places is a visual rule that will
disagree with itself. `ui-consistency.md` stays the method — how to derive a system; this file is
the result for this product.

### Point the repo at it — `<repo>/CLAUDE.md`

A document nobody is pointed at is a document nobody opens. Write a **short pointer** block at the
repo root — creating the file if absent and replacing the block in place when it is already there,
never touching anything outside the delimiters. Same convention and same shape as the
`delivery-os:code-context` block: it points, it does not restate.

```markdown
<!-- delivery-os:ui-system -->
## UI system

The UI standard is `<path>/shared-context/ui-standards.md` — direction, token scales, the measured
contrast table, primitives, and the `<RULE-PREFIX>-###` rules. **Read it before writing or changing
a screen.**

Styling: **<library>**. Tokens: `<token file>`. Primitives: `<primitives dir>`.

Every visual value comes from a token. No raw hex, no px font sizes, no magic spacing, no inline
transitions. Check the primitives directory before writing a component; the second use of an
element is what makes it shared, not the third. Never add a second UI library.
<!-- /delivery-os:ui-system -->
```

Fill the angle-bracket values; the rest is fixed text. If this block starts growing past about
fifteen lines, the content belongs in `ui-standards.md` and the block has stopped being a pointer.

---

## 5. Green-base verification

Before handing off, run the full base sequence in the shell and confirm each step is green:

```text
install → lint → format-check → type-check → test → build
```

This is the exact readiness item the dev agent checks ("Repository is in a usable state; base build is green"). If any step fails, fix the scaffold or report precisely which step failed and why — a red base is not a finished scaffold. Record the verification result in the summary.

---

## 6. Decision logging

Append a `DEC-###` row to `shared-context/decision-log.md` for **every** stack decision — both spec-confirmed and user-answered — so the foundation is auditable and `tl-spec-review` / the dev loop can trace why the stack is what it is. Confidence: `Confirmed` where the spec or the user pinned it; `Assumed` only where a default was explicitly accepted. Open items you deliberately deferred (hosting, auth, CI) are recorded as open questions, not silent assumptions.
