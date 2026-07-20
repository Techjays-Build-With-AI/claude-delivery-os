# Stack bindings — resolving baseline capabilities to concrete tools per stack

The baseline profile and the maturity domains are written as **capabilities** (the *what*). This file is the **binding map** (the *how*): for each detected stack, which concrete tool and command satisfies each capability. The agent's job at scan time is **detect → bind → probe**, never invent policy.

- **Detect** the stack from manifests.
- **Bind** each capability to the stack's tool via the table below.
- **Probe** whether that tool is present, enforced, and passing (see `preflight-and-evidence.md`).

Both QA (when standing tooling up) and `/tl:maturity` (when reading tool output) resolve through this same map, so a capability means the same thing on both sides.

## Two tiers of tooling

| Tier | What | Who provides it |
|---|---|---|
| **Tier 1 — auditor's instruments** | Language-agnostic single binaries the audit brings **ephemerally** to get a reading when the project has nothing: `semgrep` (SAST), `trivy`/`osv-scanner` (deps + CVEs), `gitleaks` (secrets), `jscpd` (duplication), `lizard` (complexity), `hadolint` (Dockerfile), `checkov` (IaC) | the audit, from a throwaway cache — **never installed into the repo** |
| **Tier 2 — project toolchain** | The stack-native linter / formatter / type-checker / test runner + coverage that the project **should carry** and enforce (baseline) | the **project** — the audit *recommends* via QA, never installs |

Tier 1 is mostly stack-independent (the same Semgrep scans Python, .NET, and Ruby). Tier 2 is where the binding below matters.

## Detection keys

| Stack | Detect via |
|---|---|
| Node / TypeScript | `package.json` (+ `tsconfig.json` for TS) |
| Python | `pyproject.toml` / `requirements.txt` / `setup.cfg` |
| .NET | `*.sln` / `*.csproj` |
| Ruby on Rails | `Gemfile` (+ `config/application.rb`) |
| Go | `go.mod` |
| Java | `pom.xml` / `build.gradle` |
| PHP | `composer.json` |

For a stack not in this map, degrade gracefully: infer from ecosystem conventions, propose a best-guess binding, mark it `unrecognized-stack: inferred` in the report, and surface it as a candidate to add here. Never block the audit on an unknown stack — bind what you can, mark the rest `not measured`.

## Tier-2 binding table (capability → tool per stack)

| Capability | Node/TS | Python | .NET | Ruby on Rails | Go | Java |
|---|---|---|---|---|---|---|
| BL-01 Lint | eslint | ruff / flake8 | Roslyn analyzers | rubocop | golangci-lint | Checkstyle / PMD |
| BL-02 Format check | prettier `--check` | ruff format / black `--check` | `dotnet format --verify-no-changes` | rubocop / standardrb | `gofmt -l` | spotless / google-java-format |
| BL-03 Type check | `tsc --noEmit` | mypy / pyright | (compiler + analyzers) | Sorbet (if adopted) | (compiler) | (compiler) |
| BL-04/05 Unit + coverage | jest / vitest + c8 / nyc | pytest + coverage.py | `dotnet test` + coverlet | rspec / minitest + simplecov | `go test -cover` | JUnit + JaCoCo |
| SAST (D4) | semgrep (T1) | bandit / semgrep | security analyzers / semgrep | brakeman | gosec / govulncheck | SpotBugs / semgrep |
| Dep scan (BL-08) | `npm/pnpm audit`, osv-scanner | pip-audit / osv-scanner | `dotnet list package --vulnerable` | bundler-audit | govulncheck | OWASP dependency-check |
| Secret scan (BL-09) | gitleaks (T1) | gitleaks | gitleaks | gitleaks | gitleaks | gitleaks |
| Complexity (D1) | lizard / eslint-complexity | lizard / radon | lizard | lizard / flog | gocyclo / lizard | lizard / PMD |
| Duplication (D1) | jscpd | jscpd | jscpd | jscpd | jscpd | jscpd / PMD-CPD |

Coverage output formats to ingest (see `preflight-and-evidence.md`): lcov, cobertura, clover, JaCoCo XML, coverage.py XML. Lint/SAST: prefer **SARIF** where the tool emits it; otherwise the tool's native JSON/XML.

## Enforcement detection (the "enforced" rung)

A capability is **enforced** when it's wired into a gate, not just present. Detect enforcement from:

- **Pre-commit:** `.pre-commit-config.yaml`, `.husky/`, `lint-staged` config, `lefthook.yml`, `.githooks/`.
- **CI:** a workflow (`.github/workflows/*`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `Jenkinsfile`) whose steps run the tool **and** whose job gates the merge (required check / fails the pipeline).
- **Coverage gate:** a threshold configured to fail the build (jest `coverageThreshold`, `--cov-fail-under`, coverlet threshold, simplecov `minimum_coverage`, JaCoCo rule).

Present config with no gate = **present, not enforced** (partial credit + a finding). Wired-and-gated = **enforced**.
