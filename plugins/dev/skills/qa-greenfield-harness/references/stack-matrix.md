# Stack matrix — deterministic per-stack framework picks

**Every row is canonical. Same stack + same layer → same picks. No LLM choice, no user prompt.**

If a stack ends up not matching any row, use the closest-match row and log an assumption in `dev/test-decision.md`.

---

## Frontend

| Framework | Unit | Integration | E2E | Coverage | Notes |
|---|---|---|---|---|---|
| React (SPA — Vite) | Vitest | Vitest + Testing Library | Playwright | @vitest/coverage-v8 | Idiomatic for Vite-based repos |
| React (Next.js App Router) | Vitest | Vitest + Testing Library + msw | Playwright | @vitest/coverage-v8 | msw for API mocking in RSC contexts |
| React (Next.js Pages Router) | Jest | Jest + Testing Library + msw | Playwright | Jest built-in coverage | Legacy but common |
| React (CRA) | Jest | Jest + Testing Library | Playwright | Jest built-in coverage | Preserve CRA's Jest wiring |
| Vue 3 (Vite) | Vitest | Vitest + Vue Test Utils | Playwright | @vitest/coverage-v8 | Idiomatic |
| Nuxt 3 | Vitest | Vitest + @nuxt/test-utils | Playwright | @vitest/coverage-v8 | Nuxt-native testing |
| Angular | Jest | Jest + Testing Library Angular | Playwright | Jest coverage | Migrate from Karma if present |
| SvelteKit | Vitest | Vitest + Testing Library Svelte | Playwright | @vitest/coverage-v8 | |
| Astro | Vitest | Vitest | Playwright | @vitest/coverage-v8 | Content-heavy sites — light unit |
| Remix | Vitest | Vitest + Testing Library | Playwright | @vitest/coverage-v8 | |
| React Native | Jest | Jest + RN Testing Library | Detox | Jest coverage | Detox for device E2E |

---

## Backend

| Framework | Unit | Integration | E2E / Contract | Coverage | Notes |
|---|---|---|---|---|---|
| Express (Node) | Vitest | Vitest + Supertest | Playwright API | @vitest/coverage-v8 | Modern default |
| NestJS | Jest | @nestjs/testing + Supertest | Playwright API | Jest coverage | Nest ships with Jest wiring |
| Fastify | Vitest | Vitest + Fastify.inject | Playwright API | @vitest/coverage-v8 | inject() beats Supertest for Fastify |
| Koa | Vitest | Vitest + Supertest | Playwright API | @vitest/coverage-v8 | |
| Hono | Vitest | Vitest + hono/testing | Playwright API | @vitest/coverage-v8 | Native testing helpers |
| FastAPI | pytest | pytest + httpx.AsyncClient | Schemathesis | pytest-cov | httpx.AsyncClient for ASGI apps |
| Django | pytest | pytest + pytest-django | Schemathesis | pytest-cov | pytest-django for ORM fixtures |
| Flask | pytest | pytest + Flask test client | Schemathesis | pytest-cov | |
| Starlette | pytest | pytest + httpx.AsyncClient | Schemathesis | pytest-cov | |
| Spring Boot | JUnit 5 | @SpringBootTest + MockMvc | RestAssured | JaCoCo | Standard Spring test stack |
| ASP.NET Core | xUnit | WebApplicationFactory | RestAssured.Net | coverlet | WebApplicationFactory is idiomatic |
| Gin (Go) | std testing + testify/require | httptest.NewServer | httptest based | go test -cover | |
| Echo (Go) | std testing + testify | echo.NewContext (unit) + httptest (int) | httptest based | go test -cover | |
| Fiber (Go) | std testing + testify | fiber.App.Test() | httptest based | go test -cover | Fiber.Test() over httptest for perf |

---

## Mobile

| Framework | Unit | Widget / Component | Integration / E2E | Coverage |
|---|---|---|---|---|
| Flutter | flutter_test | flutter_test (widget) | patrol OR integration_test | lcov via `flutter test --coverage` |
| React Native | Jest | Jest + RN Testing Library | Detox | Jest coverage |

---

## Database / Migrations

| Stack | Test tool | Notes |
|---|---|---|
| Postgres (Prisma migrations) | Prisma migrate reset + Vitest/Jest tests hitting constraints | Reset in `beforeAll`; assert via SQL |
| Postgres (raw migrations) | pgTAP OR integration tests in the backend layer | pgTAP for DB-only repos |
| MongoDB | Testcontainers-based integration OR in-memory (mongodb-memory-server) | Prefer real Mongo via Testcontainers for correctness |
| MySQL | Testcontainers-based integration | |

---

## Coverage floors — greenfield defaults

Per gate, in generated `qa/quality-gates.md`:

| Gate | Coverage / threshold | Rationale |
|---|---|---|
| unit | 100% pass, ≥ 60% line coverage | Aggressive for greenfield; developer bumps via `/qa:setup` |
| integration | 100% pass | Coverage not measured at integration level (function-level noise) |
| e2e | 100% pass (frontend only) | Frontend layer; backend gets contract tests instead |
| lint | 100% pass | Every framework's default linter (eslint / ruff / gofmt / dotnet format) |
| type-check | 100% pass | Only for typed languages (TS, Python w/ mypy declared, C#, Go, Rust, Java) |
| format | 100% pass | prettier / black / gofmt / dotnet format |

---

## Package manager commands per PM

Use the detected PM (from `stack-detection.md` §5). Install dev deps for the picked frameworks.

| Package manager | Add dev dep command | Test run command shape |
|---|---|---|
| pnpm | `pnpm add -D <pkg>` | `pnpm test` (define scripts in package.json) |
| npm | `npm i -D <pkg>` | `npm test` |
| yarn | `yarn add -D <pkg>` | `yarn test` |
| bun | `bun add -d <pkg>` | `bun test` |
| poetry | `poetry add --group dev <pkg>` | `poetry run pytest` |
| pip (via requirements-dev.txt) | Append + `pip install -r requirements-dev.txt` | `pytest` |
| uv | `uv add --dev <pkg>` | `uv run pytest` |
| go | `go get -u <pkg>` | `go test ./...` |
| cargo | `cargo add --dev <pkg>` | `cargo test` |
| maven | Add `<dependency scope="test">` | `mvn test` |
| gradle | Add `testImplementation "<pkg>"` | `./gradlew test` |
| dotnet | `dotnet add package <pkg> --version` | `dotnet test` |
| flutter | Add to `pubspec.yaml` dev_dependencies + `flutter pub get` | `flutter test` |

---

## Fallback ladder (if no matrix row matches)

If the detected framework isn't in the matrix (rare edge cases: Perfect, Deno-native without a framework, Zig, etc.):

1. Fall back to the language's dominant testing tool per its ecosystem (e.g. Zig → `zig test` built-in; Deno → `deno test`)
2. Fall back to a generic HTTP client + integration test (e.g. `curl` in a shell script + a JSON schema check)
3. Log the fallback prominently in `dev/test-decision.md` as `assumption: no matrix row; used <tool> because <reason>`

Never leave the harness un-bootstrapped. The whole point of this skill is UNBLOCK.
