# Gates template — the minimal `qa/quality-gates.md` this skill writes

**Purpose.** Every bootstrap emits ONE `qa/quality-gates.md` with `harness_status: Active` and a Required table naming exact commands per gate. Downstream `/dev:build` Stage 8 reads this file to run validation; `/dev:commit` re-reads it in Stage 5 for regression detection.

**No optional gates in the bootstrap.** Optional gates come from `/qa:setup`'s interactive plan later. This template is the minimal viable harness.

---

## Frontmatter (fixed shape)

```yaml
---
doc_type: quality-gates
schema_version: 1.0
produced_by: dev
harness_status: Active                       # never Draft on a successful bootstrap
baseline_status: BootstrappedByGreenfield    # tag for /tl:maturity + /qa:audit to know origin
bootstrapped_by: qa-greenfield-harness
bootstrapped_at: <ISO>
last_updated: <ISO>
---
```

---

## Body sections (in order)

```markdown
# Quality Gates

**Harness status:** Active
**Origin:** bootstrapped by `qa-greenfield-harness` on <date>. To customize (swap frameworks, adjust coverage floor, add security scanning), run:
  1. `/qa:audit` — assess the current harness
  2. `/qa:plan <approvals>` — draft your changes
  3. `/qa:setup` — apply

## Required gates

| QG | Check | Command (in target repo) | Threshold | Layer |
|---|---|---|---|---|
| QG-001 | unit tests    | <framework-specific> | pass 100% | any |
| QG-002 | coverage      | <coverage command>    | ≥ 60% line coverage | any |
| QG-003 | lint          | <linter command>      | pass 100% | any |
| QG-004 | format        | <formatter command>   | pass 100% | any |
| QG-005 | type-check    | <type checker>        | pass 100% | typed languages only |
| QG-006 | integration   | <integration command> | pass 100% | any |
| QG-007 | e2e           | <e2e command>         | pass 100% | frontend only |

## Optional gates

*(none — add via `/qa:audit` → `/qa:plan` → `/qa:setup`)*

## Notes

- Coverage floor is 60% (greenfield default). Raise via `/qa:setup`.
- Security scanning (SAST, dependency vuln, secret detection) is NOT enabled here. Enable via `/qa:setup`.
- Contract testing (Pact / OpenAPI schema) is NOT enabled here. Enable via `/qa:setup` for multi-service repos.
- E2E is only listed as Required for frontend layer. Backend gets integration/contract as its equivalent.
```

---

## Per-stack Required table content

### React (SPA — Vite + Vitest + Playwright)

```
| QG-001 | unit tests    | pnpm test              | pass 100%    | frontend |
| QG-002 | coverage      | pnpm test:coverage     | ≥ 60% lines  | frontend |
| QG-003 | lint          | pnpm lint              | pass 100%    | frontend |
| QG-004 | format        | pnpm format:check      | pass 100%    | frontend |
| QG-005 | type-check    | pnpm typecheck         | pass 100%    | frontend |
| QG-006 | integration   | pnpm test              | pass 100%    | frontend | (integration lives in vitest for SPA)
| QG-007 | e2e           | pnpm test:e2e          | pass 100%    | frontend |
```

Also add scripts to `package.json`:

```json
{
  "scripts": {
    "test":          "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:e2e":      "playwright test",
    "lint":          "eslint . --max-warnings=0",
    "format:check":  "prettier --check .",
    "typecheck":     "tsc --noEmit"
  }
}
```

### NestJS + Jest + Playwright

```
| QG-001 | unit tests    | pnpm test              | pass 100%    | backend |
| QG-002 | coverage      | pnpm test:cov          | ≥ 60% lines  | backend |
| QG-003 | lint          | pnpm lint              | pass 100%    | backend |
| QG-004 | format        | pnpm format:check      | pass 100%    | backend |
| QG-005 | type-check    | pnpm build             | pass 100%    | backend | (tsc via build)
| QG-006 | integration   | pnpm test:e2e          | pass 100%    | backend | (NestJS calls integration "e2e")
| — | | | | |
```

Note: no QG-007 for backend — integration IS the last gate.

### FastAPI + pytest + Schemathesis

```
| QG-001 | unit tests    | poetry run pytest tests/unit          | pass 100%    | backend |
| QG-002 | coverage      | poetry run pytest --cov=app --cov-fail-under=60 | ≥ 60%  | backend |
| QG-003 | lint          | poetry run ruff check .               | pass 100%    | backend |
| QG-004 | format        | poetry run ruff format --check .      | pass 100%    | backend |
| QG-005 | type-check    | poetry run mypy app                    | pass 100%    | backend | (if mypy detected in deps; else omit)
| QG-006 | integration   | poetry run pytest tests/integration    | pass 100%    | backend |
| QG-007 | contract      | poetry run schemathesis run ...        | pass 100%    | backend | (against OpenAPI spec)
```

### Go (Gin) + std testing + testify

```
| QG-001 | unit tests    | go test ./...                          | pass 100%    | backend |
| QG-002 | coverage      | go test -cover ./... (min 60%)         | ≥ 60%        | backend |
| QG-003 | lint          | golangci-lint run                       | pass 100%    | backend |
| QG-004 | format        | gofmt -l -d . (no output = pass)       | pass 100%    | backend |
| QG-005 | type-check    | go vet ./...                            | pass 100%    | backend |
| QG-006 | integration   | go test ./internal/... -tags=integration | pass 100%   | backend |
```

### ASP.NET Core + xUnit

```
| QG-001 | unit tests    | dotnet test                             | pass 100%    | backend |
| QG-002 | coverage      | dotnet test /p:CollectCoverage=true /p:Threshold=60 | ≥ 60% | backend |
| QG-003 | lint          | dotnet format --verify-no-changes       | pass 100%    | backend |
| QG-004 | format        | (same as lint for .NET)                 | —            | —       |
| QG-005 | type-check    | dotnet build --no-restore -warnaserror  | pass 100%    | backend |
| QG-006 | integration   | dotnet test --filter Category=Integration | pass 100%  | backend |
```

### Spring Boot + JUnit 5

```
| QG-001 | unit tests    | ./mvnw test                             | pass 100%    | backend |
| QG-002 | coverage      | ./mvnw test jacoco:check                | ≥ 60% lines  | backend |
| QG-003 | lint          | ./mvnw checkstyle:check                 | pass 100%    | backend |
| QG-004 | format        | ./mvnw spotless:check                   | pass 100%    | backend |
| QG-005 | type-check    | ./mvnw compile                          | pass 100%    | backend |
| QG-006 | integration   | ./mvnw test -Dtest=*IT                  | pass 100%    | backend |
```

### Flutter + flutter_test

```
| QG-001 | unit tests    | flutter test                            | pass 100%    | mobile |
| QG-002 | coverage      | flutter test --coverage                 | ≥ 60% lines  | mobile |
| QG-003 | lint          | flutter analyze                         | pass 100%    | mobile |
| QG-004 | format        | dart format --set-exit-if-changed .     | pass 100%    | mobile |
| QG-005 | type-check    | (built into `flutter analyze`)          | —            | —       |
| QG-006 | integration   | flutter test integration_test/          | pass 100%    | mobile |
| QG-007 | e2e           | flutter drive --driver=integration_test/... | pass 100% | mobile |
```

### React Native + Jest + Detox

```
| QG-001 | unit tests    | pnpm test                               | pass 100%    | mobile |
| QG-002 | coverage      | pnpm test -- --coverage                 | ≥ 60% lines  | mobile |
| QG-003 | lint          | pnpm lint                               | pass 100%    | mobile |
| QG-004 | format        | pnpm format:check                       | pass 100%    | mobile |
| QG-005 | type-check    | pnpm typecheck                          | pass 100%    | mobile |
| QG-006 | integration   | pnpm test                               | pass 100%    | mobile |
| QG-007 | e2e           | pnpm detox test                          | pass 100%    | mobile |
```

---

## Test config file contents (per stack) — minimal working

### `vitest.config.ts` (React SPA)

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment:  'jsdom',
    globals:      true,
    setupFiles:   './tests/setup.ts',
    coverage: {
      provider:  'v8',
      reporter:  ['text', 'html', 'lcov'],
      lines:     60,
      functions: 60,
      branches:  60,
      statements: 60,
    },
  },
});
```

Plus a minimal `tests/setup.ts`:

```typescript
import '@testing-library/jest-dom/vitest';
```

### `playwright.config.ts` (frontend)

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir:  './tests/e2e',
  fullyParallel: true,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    trace:   'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

### `pytest.ini` (Python backend)

```ini
[pytest]
minversion       = 7.0
testpaths        = tests
python_files     = test_*.py
python_classes   = Test*
python_functions = test_*
addopts          = --strict-markers --tb=short
markers          =
    integration: integration tests (slower)
    e2e: end-to-end tests
```

Plus `.coveragerc`:

```ini
[run]
source  = app
omit    = */tests/*, */migrations/*

[report]
fail_under = 60
show_missing = true
```

### `jest.config.js` (NestJS backend)

```javascript
/** @type {import('jest').Config} */
module.exports = {
  testEnvironment:     'node',
  testRegex:            '.*\\.spec\\.ts$',
  moduleFileExtensions: ['js', 'json', 'ts'],
  rootDir:              'src',
  transform: {
    '^.+\\.(t|j)s$': 'ts-jest',
  },
  collectCoverageFrom: ['**/*.(t|j)s'],
  coverageDirectory:   '../coverage',
  coverageThreshold: {
    global: {
      lines:      60,
      functions:  60,
      branches:   60,
      statements: 60,
    },
  },
};
```

### `.gitignore` additions (append; don't clobber)

```
coverage/
.nyc_output/
htmlcov/
playwright-report/
test-results/
.pytest_cache/
__pycache__/
*.pyc
```

Only append lines that aren't already present.

---

## `qa/quality-gates.md` full example (React SPA)

Complete file the skill writes for a React SPA target repo:

```markdown
---
doc_type: quality-gates
schema_version: 1.0
produced_by: dev
harness_status: Active
baseline_status: BootstrappedByGreenfield
bootstrapped_by: qa-greenfield-harness
bootstrapped_at: 2026-08-31T14:22:33Z
last_updated: 2026-08-31T14:22:33Z
---

# Quality Gates

**Harness status:** Active
**Origin:** bootstrapped by `qa-greenfield-harness` on 2026-08-31.

To customize (swap frameworks, adjust coverage floor, add security scanning), run:
  1. `/qa:audit` — assess the current harness
  2. `/qa:plan <approvals>` — draft your changes
  3. `/qa:setup` — apply

## Required gates

| QG | Check | Command (in target repo) | Threshold | Layer |
|---|---|---|---|---|
| QG-001 | unit tests    | pnpm test                        | pass 100%    | frontend |
| QG-002 | coverage      | pnpm test:coverage               | ≥ 60% lines  | frontend |
| QG-003 | lint          | pnpm lint                        | pass 100%    | frontend |
| QG-004 | format        | pnpm format:check                | pass 100%    | frontend |
| QG-005 | type-check    | pnpm typecheck                   | pass 100%    | frontend |
| QG-006 | integration   | pnpm test                        | pass 100%    | frontend |
| QG-007 | e2e           | pnpm test:e2e                    | pass 100%    | frontend |

## Optional gates

*(none — add via `/qa:audit` → `/qa:plan` → `/qa:setup`)*

## Notes

- Coverage floor is 60% (greenfield default). Raise via `/qa:setup`.
- Security scanning (SAST, dependency vuln, secret detection) is NOT enabled here. Enable via `/qa:setup`.
- Contract testing (Pact / OpenAPI schema) is NOT enabled here. Enable via `/qa:setup` for multi-service repos.
```

Every stack combo produces the same structural document — only the Required table rows + Notes differ.
