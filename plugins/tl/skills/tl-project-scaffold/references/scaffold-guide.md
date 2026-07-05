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

Batch related questions (all frontend choices together, all backend together). Only ask what you actually need to scaffold; don't turn it into a survey. Record the user's answer with confidence `Confirmed`; if the user says "use your recommendation", record it `Assumed` and note it was an accepted default.

---

## 3. Skeleton + tooling checklist

Prefer the stack's **official generator/starter** over hand-rolling — it gives an idiomatic, green baseline you can trust:

- Frontend: `create-vite`, `create-next-app`, `ng new`, `npm create svelte`, …
- Backend: `spring init`, `nest new`, `poetry new` / `uv init`, `go mod init` + layout, `dotnet new webapi`, …
- Full-stack/monorepo: the framework's monorepo template or a workspaces layout (`pnpm-workspace.yaml`, `turbo`, `nx`), only if the layout decision was monorepo.

Whatever the generator leaves out, ensure the repo has:

- [ ] **Package-manager manifest(s)** with pinned/compatible versions (`package.json`, `pyproject.toml`, `go.mod`, …).
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

## 4. Project design docs (context/project/)

Write these so the dev agent (and future TL runs) build against a confirmed foundation:

- **`technology-stack.md`** — the exact stack and versions chosen, one row per layer, each citing the `DEC-###` that decided it.
- **`architecture.md`** — the architecture the scaffold realises: components, how they fit, the repo layout, and the runtime shape. Reconcile with the spec; where you filled a gap, mark it and cite the decision.
- **`coding-standards.md`** — naming, folder structure, lint/format rules, test conventions, error-handling and logging conventions. This is the file the dev agent's implementation step follows, so make it concrete.

Every layer carries standard frontmatter (`doc_type`, `produced_by: tl`, `schema_version`, `generated_at`).

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
