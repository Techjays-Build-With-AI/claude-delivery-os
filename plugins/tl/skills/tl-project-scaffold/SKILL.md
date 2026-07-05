---
name: tl-project-scaffold
description: Scaffold the initial application repository for a project from its confirmed architecture, so a greenfield workspace has a real, green codebase for the dev agent to build features into. Use whenever there is no product repo yet and one is needed — "scaffold the project", "set up the codebase", "bootstrap the app", "create the initial repo", or when the dev loop reports project-zero (no repository to implement into). It reads the architecture / technology-stack from the tech spec, the TL context graph, and shared-context; determines the base stack and project structure; and — for any required decision the architecture does not pin down (frontend framework, backend language/framework, database engine, package manager, test/lint/build tooling, hosting/CDN, repo layout, auth approach) — asks the user with a clear recommendation rather than guessing. It then creates the skeleton, package-manager manifests, lint/format/type/test/build tooling, a minimal passing test and green build, a README, and writes context/project/{architecture.md, technology-stack.md, coding-standards.md}, logging each stack decision as DEC-###. It executes a confirmed stack; it never silently invents one, and it does not implement product features (that is the dev agent's job).
---

# TL Project Scaffold (confirmed architecture → initial green repository)

You stand up **project zero** — the first, empty codebase a team (and the dev agent) builds into. The feature breakdown says *what* to build and the context graph says *which pages/endpoints/entities*; scaffolding answers *what application, in what stack, with what tooling, laid out how* — and produces a real repository with a green base build. Until this exists, the dev loop has nothing to implement into.

Your defining constraint is the same guardrail the dev agent respects: **you execute a confirmed stack; you do not guess one.** The stack is an architecture decision. Where the tech spec / architecture pins a choice down, you follow it. Where it is silent on something you must decide to scaffold, you **ask the user — with a recommendation and a one-line rationale** — and record their answer as a decision. You never quietly pick a framework or database and scaffold on top of the guess.

## Operating contract

Read the **`delivery-os-conventions`** contract first if it isn't in context — the workspace layout, the frontmatter standard, stable IDs, and the controlled vocabulary. Your **inputs**, in priority order:

1. The **architecture / tech spec** — a spec document the user points you at, or `context/project/architecture.md` / `context/project/technology-stack.md` if they exist. This is the primary source of the intended stack and structure. Use the `docx`/`pdf` skills to extract it if it isn't Markdown.
2. The **TL context graph** (`context/frontend|backend|database` indexes) — the shape of what will be built (how many frontend surfaces, backend domains, entities) informs the skeleton's structure and whether it's a frontend app, an API service, a full-stack app, or a monorepo.
3. **`shared-context/`** — `project-profile.md` (platform, constraints), `system-landscape.md` (systems it must fit), `glossary.md`.
4. The **user** — for any required decision the sources above leave open (see the decision list in `references/scaffold-guide.md`).

Your **output** is a real repository plus the project design docs that describe it:

```text
<repo-target>/                 # the scaffolded application (git-initialised)
  <stack-conventional skeleton>  # e.g. src/, app/, tests/, per the chosen stack
  <package-manager manifests>    # package.json / pyproject.toml / go.mod / …
  <lint/format/type/test/build config>
  <one trivial passing test>     # proves the base build is green
  README.md
context/project/               # the design docs that pin the stack (created on demand)
  architecture.md              # the architecture the scaffold realises (confirmed)
  technology-stack.md          # the exact stack + versions chosen
  coding-standards.md          # conventions the dev agent will follow
```

Where the repo target lives is itself a decision — ask if unclear, recommending a sensible default (a `./app` subfolder of the workspace, the workspace root, or a sibling repo path the user gives). Never scaffold over existing application code without confirmation.

## Workflow

Follow the detailed method in **`references/scaffold-guide.md`** (the required-decision checklist, recommended defaults, the skeleton/tooling checklist, and the green-base verification). In brief:

### 1. Read the architecture and establish what's decided vs open
Read the tech spec / architecture, the context graph, and `shared-context/`. Extract every stack choice the architecture **confirms** (frontend framework, backend language/framework, database, hosting, etc.). List every required choice it leaves **open** against the checklist in `references/scaffold-guide.md`.

### 2. Resolve open decisions with the user — recommendation first
For each open decision, ask the user a focused question with a **recommended option and a one-line why**, grounded in the project profile and the context graph (e.g. "No frontend framework is specified. Recommend **React + Vite + TypeScript** — the context graph is 12 pages of interactive UI and the team profile lists React. Alternatives: Next.js if you want SSR/routing built in; SvelteKit if you prefer a lighter runtime."). Batch related questions. Don't proceed to scaffold a layer whose stack is still unconfirmed — an unresolved *critical* stack decision is a stop, not a guess.

### 3. Determine the project structure
From the confirmed stack and the context graph, decide the layout: single app vs monorepo, folder structure, where frontend/backend/shared code live. Follow the chosen stack's idiomatic conventions rather than inventing a bespoke layout.

### 4. Scaffold the repository
Create the skeleton, package-manager manifests, and the lint/format/type-check/test/build tooling for the stack. Add a minimal **passing** test and confirm a **green base build**. Initialise git (don't commit secrets; add a `.gitignore`). Add a README describing how to install, run, test, and build. Prefer official generators/starters for the stack where they exist (e.g. `create-vite`, `create-next-app`, `spring init`, `poetry new`) over hand-rolling.

### 5. Write the project design docs and log decisions
Write `context/project/technology-stack.md` (the exact stack + versions), `context/project/architecture.md` (the architecture the scaffold realises — confirmed, or reconciled with the spec), and `context/project/coding-standards.md` (naming, structure, lint/format rules, test conventions — the conventions the dev agent will follow). Append a `DEC-###` row to `shared-context/decision-log.md` for **every** stack decision made — both the ones the spec confirmed and the ones the user just answered — with confidence (`Confirmed` where the spec/user pinned it, `Assumed` only where explicitly accepted as a default).

### 6. Verify the base is green
Run install → lint → type-check → test → build in the shell. The base build **must be green** before you hand off — that is the exact readiness item the dev agent checks. If it isn't green, fix the scaffold or report precisely what fails; don't declare the repo ready.

### 7. Summarise in chat
Report: the confirmed stack and structure, which decisions the spec supplied vs which the user answered, the `DEC-###` logged, the repo location, and the green-base result (install/lint/type/test/build). Tell the user the workspace is now build-ready and they can run `/dev:build <feature>` (or `/dev:bootstrap` will now pass).

## Boundaries

You **execute** a confirmed stack; you don't decide the product's architecture unilaterally — where the spec is silent you ask the user with a recommendation, and a genuinely undecided *critical* stack choice is a stop, not a guess. You scaffold the **initial** repository and its tooling; you do **not** implement product features, endpoints, pages, or business logic — that is the dev agent's `feature-delivery-loop`. You don't scaffold over existing application code without explicit confirmation, and you don't commit secrets or provision live infrastructure. This skill is the authoring counterpart that produces the codebase the `feature-delivery-loop` then builds into.

## Return value

Return the scaffold summary: the confirmed stack + structure, spec-supplied vs user-answered decisions, `DEC-###` logged, repo location, and the green-base verification result — plus the next action (`/dev:build <feature>`).
