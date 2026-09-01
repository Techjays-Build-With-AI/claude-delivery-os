# Stack detection — deterministic ladder

**Purpose.** Identify the target repo's language, framework, ORM, testing framework, package manager, and config style from FILE SIGNALS ONLY. No LLM guessing, no natural-language parsing of README.md. Files at repo root + one level down are enough for 99% of stacks.

**Runtime.** ≤ 5 file reads per detection pass. Faster than trying to remember stack docs.

**Fallback.** For every dimension, if no signal fires, mark it `Unknown` in the detected-stack record and fall back to what `shared-context/technology-stack.md` declares (if the workspace has one). Never guess; unknown is a data point.

---

## 1. Language detection

Read the top-level file listing. Signal priority (first match wins):

| Signal | Language |
|---|---|
| `pyproject.toml` OR `setup.py` OR `requirements.txt` | Python |
| `package.json` AND `tsconfig.json` | TypeScript |
| `package.json` (no tsconfig) | JavaScript |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml` OR `build.gradle` OR `build.gradle.kts` | Java (Maven / Gradle) |
| `*.csproj` OR `*.sln` OR `global.json` | C# (.NET) |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `mix.exs` | Elixir |
| `pubspec.yaml` | Dart / Flutter |

Multi-language repos (e.g. Node backend + Flutter mobile in a monorepo): detect at the **subfolder level** matching the task's target repo path from `.jetrix/cache/repolocation.json`.

---

## 2. Framework detection

Given the language, read the specific dependency manifest for these signals:

### TypeScript / JavaScript

Read `package.json` `dependencies` + `devDependencies`. Signal priority:

| Signal (first match wins) | Framework |
|---|---|
| `next` | Next.js |
| `@nestjs/core` | NestJS |
| `@remix-run/react` | Remix |
| `@sveltejs/kit` | SvelteKit |
| `@angular/core` | Angular |
| `nuxt` OR `@nuxt/kit` | Nuxt |
| `astro` | Astro |
| `express` | Express |
| `fastify` | Fastify |
| `koa` | Koa |
| `hono` | Hono |
| `react` (no Next/Remix/Nuxt) | React (SPA) |
| `vue` (no Nuxt/SvelteKit) | Vue |
| `svelte` (no SvelteKit) | Svelte |
| `react-native` | React Native |

### Python

Read `pyproject.toml` `[tool.poetry.dependencies]` OR `requirements.txt`:

| Signal | Framework |
|---|---|
| `fastapi` | FastAPI |
| `django` | Django |
| `flask` | Flask |
| `starlette` (no FastAPI) | Starlette |
| `tornado` | Tornado |
| `celery` | Celery (worker) |

### Go

Read `go.mod`:

| Signal | Framework |
|---|---|
| `github.com/gin-gonic/gin` | Gin |
| `github.com/labstack/echo` | Echo |
| `github.com/gofiber/fiber` | Fiber |
| `github.com/gorilla/mux` | Gorilla Mux |
| (none of the above) | Go std net/http |

### .NET / C#

Read `*.csproj`:

| Signal | Framework |
|---|---|
| `Microsoft.AspNetCore.App` | ASP.NET Core |
| `Microsoft.NET.Sdk.Web` | ASP.NET Core (SDK-style) |
| `Microsoft.Maui.Controls` | .NET MAUI |

### Java

Read `pom.xml` OR `build.gradle`:

| Signal | Framework |
|---|---|
| `spring-boot-starter-web` OR `org.springframework.boot` | Spring Boot |
| `micronaut-http-server` | Micronaut |
| `quarkus-resteasy` | Quarkus |

### Dart / Flutter

Read `pubspec.yaml`:

| Signal | Framework |
|---|---|
| `sdk: flutter` | Flutter |

---

## 3. ORM / data layer detection

For backend stacks, read the dep manifest again:

### TypeScript / JavaScript backend

| Signal | ORM / data layer |
|---|---|
| `prisma` OR `@prisma/client` | Prisma |
| `typeorm` | TypeORM |
| `sequelize` | Sequelize |
| `mongoose` | Mongoose (MongoDB) |
| `drizzle-orm` | Drizzle |
| `mikro-orm` | MikroORM |
| `kysely` | Kysely |
| `knex` (no other ORM) | Knex query builder |
| Raw `pg` / `mysql2` / `mongodb` clients | Raw driver |

### Python backend

| Signal | ORM |
|---|---|
| `sqlalchemy` | SQLAlchemy |
| `django` (Django ORM built-in) | Django ORM |
| `tortoise-orm` | Tortoise |
| `sqlmodel` | SQLModel |
| `motor` / `pymongo` | MongoDB driver |
| `asyncpg` / `psycopg2` (no ORM) | Raw driver |

### Go

| Signal | ORM |
|---|---|
| `gorm.io/gorm` | GORM |
| `github.com/uptrace/bun` | Bun |
| `github.com/jmoiron/sqlx` | sqlx |
| `database/sql` only | std lib |

### .NET

| Signal | ORM |
|---|---|
| `Microsoft.EntityFrameworkCore` | Entity Framework Core |
| `Dapper` | Dapper |

### Java

| Signal | ORM |
|---|---|
| `spring-boot-starter-data-jpa` | JPA/Hibernate via Spring Data |
| `mybatis-spring-boot-starter` | MyBatis |

---

## 4. Testing framework detection

Read `devDependencies` (or test deps in Python's `pyproject.toml [tool.poetry.dev-dependencies]`, etc.). Also glance at test config files at repo root.

### TypeScript / JavaScript

| Signal | Test framework |
|---|---|
| `vitest` OR `vitest.config.ts` | Vitest |
| `jest` OR `jest.config.js` | Jest |
| `@playwright/test` OR `playwright.config.ts` | Playwright (E2E) |
| `cypress` OR `cypress.config.js` | Cypress (E2E) |
| `mocha` | Mocha |
| `@types/supertest` | Supertest (integration for HTTP) |
| `@testing-library/react` | RTL (component tests) |
| `@testing-library/vue` | Vue Testing Library |

### Python

| Signal | Test framework |
|---|---|
| `pytest` OR `pytest.ini` OR `pyproject.toml [tool.pytest.ini_options]` | pytest |
| `unittest2` OR just `unittest` (std lib) | unittest |
| `hypothesis` | + property-based |
| `httpx` in dev deps | integration for HTTP |

### Go

| Signal | Test framework |
|---|---|
| `testify` | std testing + testify |
| No test framework dep | std testing |

### .NET

| Signal | Test framework |
|---|---|
| `xunit` in `.csproj` | xUnit |
| `nunit` | NUnit |
| `MSTest.TestFramework` | MSTest |

### Java

| Signal | Test framework |
|---|---|
| `spring-boot-starter-test` | JUnit 5 + Spring Test |
| `junit` (no boot) | JUnit |
| `testng` | TestNG |

### Flutter

| Signal | Test framework |
|---|---|
| `flutter_test` in dev deps | flutter_test |
| `integration_test` | integration_test |
| `patrol` | patrol |

---

## 5. Package manager detection

Read for lockfile presence:

| Signal | Package manager |
|---|---|
| `pnpm-lock.yaml` | pnpm |
| `yarn.lock` | yarn |
| `package-lock.json` | npm |
| `bun.lockb` | bun |
| `poetry.lock` | poetry |
| `pipfile.lock` | pipenv |
| `uv.lock` | uv |
| `go.sum` | go modules |
| `Cargo.lock` | cargo |
| `Gemfile.lock` | bundler |
| `composer.lock` | composer |

Use this for **exact install commands** during `qa-greenfield-harness` when it adds test dependencies.

---

## 6. Config style detection

Look for:

| Signal | Config style |
|---|---|
| `.env` OR `.env.example` at repo root | dotenv-style env vars |
| `config/` folder with `*.json` / `*.yaml` | file-based config (12-factor variant) |
| `application.yml` / `application.properties` (Spring) | Spring-style profiles |
| `appsettings.json` / `appsettings.<env>.json` | .NET config |
| `settings.py` (Django) | Django settings |

Also: how are env vars accessed in existing source? Grep a couple of source files for `process.env`, `os.environ`, `System.getenv`, `Configuration["..."]`, etc.

---

## 7. What to record

Write to `dev/implementation-log.md` (or output to caller if the log doesn't exist yet):

```yaml
detected_stack:
  language:          TypeScript
  framework:         NestJS
  orm:               Prisma
  testing_unit:      Jest
  testing_e2e:       Playwright
  package_manager:   pnpm
  config_style:      dotenv
  detected_at:       2026-08-31T14:22:07Z
  fallbacks:
    - none
  signals_read:
    - package.json (deps: @nestjs/core, prisma, playwright)
    - tsconfig.json (present)
    - pnpm-lock.yaml (present)
    - .env.example (present)
```

This block is what `dev-stack-adaptive-implementation`'s downstream phases (pattern inference, code writing, test writing) key off of. Record every signal that fired so the choice is auditable.

---

## 8. Multi-repo / monorepo edge cases

If the task's target repo is a subfolder within a larger monorepo:

- Run detection on the subfolder, not the monorepo root
- If subfolder inherits from monorepo root (e.g. TypeScript config at root, package.json in subfolder), MERGE signals: subfolder-local wins on conflict
- If the monorepo uses a tool like Nx / Turborepo, note it in `detected_stack.monorepo_tool` for future skills

---

## 9. Sanity check against `shared-context/technology-stack.md`

If the workspace has this file, compare the detected stack against what's declared:

- **Match** → confidence high, proceed
- **Mismatch** → log a `DEC-###` noting the discrepancy; prefer detected (file evidence) over declared (may be stale)
- **`shared-context/technology-stack.md` missing** → the detection IS the stack record; consider (later) proposing it as an update to the shared-context via TL

Never halt on a mismatch — the code exists as it is, and that's what we must match.
