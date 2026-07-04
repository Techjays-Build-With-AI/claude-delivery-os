# Validation suite — checks, when they apply, and how to evidence them

The check catalogue for `dev-validation`. Run what applies to the change; mark the rest `N/A`. Detect the actual command from the repo (package scripts, Makefile, CI workflow) — the commands below are common examples, not assumptions.

Run cheap-to-expensive so failures surface fast.

| Check | Applies when | Typical command (detect from repo) | Evidence |
|---|---|---|---|
| **Lint** | Always | `npm run lint`, `ruff`, `golangci-lint` | Lint report / clean exit |
| **Format** | Always | `prettier --check`, `black --check` | Diff / clean exit |
| **Type check** | Typed languages | `tsc --noEmit`, `mypy` | Type-check output |
| **Unit tests** | Always | `npm test`, `pytest`, `go test ./...` | Test report + named specs |
| **Integration tests** | Change spans services / DB | `npm run test:integration` | Integration report |
| **API-contract tests** | Endpoint added/changed | contract/schema tests, `dredd` | Contract result |
| **Build** | Always | `npm run build`, `docker build` | Build log / artifact |
| **DB migration validation** | Schema/migration change | migrate up **and down** on a scratch DB | Migration log; confirmed reversible |
| **Security scan** | Always (light) / auth-touching (deep) | `npm audit`, `bandit`, secret scan | Scan report |
| **Dependency check** | Deps added/updated | lockfile audit, license/version check | Audit output |
| **End-to-end tests** | User-facing flow | `playwright`, `cypress` | E2E run + trace/screenshot |
| **Accessibility** | UI feature (optional gate) | `axe`, `pa11y` | a11y report |
| **Performance** | Perf-sensitive (optional gate) | load/profiling harness | Perf numbers vs budget |
| **Feature-specific acceptance tests** | Always | the tests written for this feature's criteria | Named spec per criterion |

## Rules

- **Never make a suite green by weakening it.** Don't skip, delete, or `.only`/`xfail` a failing test to pass the gate — that is a permission-boundary violation. A failing test is a repair or an escalation.
- **Migrations must be proven reversible** — run `up` then `down` on a scratch database. A migration that can't roll back, or that risks data loss, is an escalation.
- **Capture failing output**, not just "failed" — the delivery loop's repair step needs the cause and the failing artifact.
- **Every acceptance criterion needs an evidence artifact** in `dev/acceptance-map.md`: a named test file, a run log, or a screenshot. "Looks right" is not evidence.
- **Feature-specific acceptance tests are mandatory** — the generic suite proves the code runs; these prove *this feature's* criteria. Map each criterion to at least one.
- Mark a criterion `Not Covered` when nothing validates it, `Blocked` when it can't be validated (undefined rule, missing external access) — never silently pass it.
