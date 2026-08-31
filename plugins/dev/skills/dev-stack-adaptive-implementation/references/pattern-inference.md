# Pattern inference — reading a repo before writing to it

**Purpose.** After stack detection, learn how THIS repo does the 8 things that matter for consistent code: imports, error handling, DI, config access, logging, folder structure, testing setup, naming. Not from framework docs — from the repo's own files.

**Budget.** ≤ 10 targeted file reads. If you can't infer a pattern from 10 reads, the repo doesn't have a strong convention for it — fall back to the framework's canonical style and log a `DEC-###` for the fallback.

---

## 1. What to infer (8 dimensions)

| # | Dimension | Why it matters |
|---|---|---|
| 1 | Folder structure | Where to put new files without introducing a parallel tree |
| 2 | Import style | Absolute vs relative; alias prefixes; whether cross-module imports are OK |
| 3 | Error handling | Custom errors vs Result vs exception; propagation style |
| 4 | Dependency injection | Constructor DI, framework container, manual instantiation |
| 5 | Config access | Env vars via `process.env` directly vs via a settings module |
| 6 | Logging | Which logger, which levels, structured vs unstructured |
| 7 | Testing setup | Where tests live, fixtures location, mocking approach |
| 8 | Naming | camelCase / snake_case / PascalCase per identifier kind |

---

## 2. Which files to read

Given the detected stack, pick 6-10 files from THIS list (skip categories the stack doesn't have):

### Backend (any stack)

1. **The main entry point** — `index.ts` / `main.py` / `main.go` / `Program.cs` / `Application.java`
2. **The router / routes definition file** — `routes/index.ts` / `urls.py` / `routes.go` / `Startup.cs`
3. **One existing endpoint handler** — pick one from the router — see error handling, DI, config in action
4. **One existing service / domain class** — see DI style, business logic style
5. **One existing ORM / data-access file** — schema definition + how queries are written
6. **The test setup / config** — `vitest.config.ts` / `jest.config.js` / `conftest.py` / `TestBase.cs`
7. **One existing test file** — see fixture style, mocking style, assertion style
8. **The config module** — `config.ts` / `settings.py` / `appsettings.json` — see how env vars are loaded

### Frontend

1. **The main entry point** — `main.tsx` / `main.ts` / `App.vue` / `index.tsx`
2. **The router setup** — `routes.tsx` / `router/index.ts` / `App.svelte`
3. **One existing page / route component** — see component structure
4. **One existing shared component** — see style structure, prop types
5. **The API client / service layer** — see how HTTP calls are made, error handling
6. **The state management setup** — Redux/Zustand/Vuex/Pinia if present
7. **One existing test file** — see component testing patterns
8. **The build config** — `vite.config.ts` / `next.config.js` — see aliases, plugins

### Mobile (Flutter / RN)

1. `lib/main.dart` / `App.tsx`
2. One screen widget / one screen component
3. State management setup (Riverpod, Redux, MobX, Provider, Zustand)
4. API client
5. One existing test

**Grep the file paths from the router / entry to find real examples** — don't read a template file by accident.

---

## 3. Inference rules per dimension

### Folder structure (dimension 1)

Read the entry point + router. Note the folder tree pattern:

- Feature-first (`features/supplier/{page, service, model}.ts`)
- Layer-first (`pages/`, `services/`, `models/` separately)
- Domain-driven (`domains/supplier/{application, domain, infrastructure}/`)
- Flat (everything at one level)

**Rule.** New files go into the SAME layout. If the repo is feature-first, put new backend files under `features/<slug>/`. Never introduce `services/` at repo root when the repo uses feature-first.

### Import style (dimension 2)

Read 2-3 source files. Note:

- Absolute paths: `import X from '@/services/foo'` (with alias) or `import X from 'src/services/foo'`
- Relative: `import X from '../../services/foo'`
- Mixed (usually alias for cross-module, relative for same-module)

**Rule.** Match the DOMINANT style. If the repo has both but 80% of files use aliases, use aliases.

### Error handling (dimension 3)

Read an endpoint handler + a service class:

- **Throw custom errors:** `throw new NotFoundError('supplier not found')` — inherits from base
- **Throw plain errors:** `throw new Error('...')` and use middleware to convert to responses
- **Return `Result<T, E>`:** `return { ok: false, error: ... }` — functional style
- **HTTP-first:** `throw new HttpException(404, '...')` — framework-native

**Rule.** Match the style. If the repo uses `throw new SupplierNotFoundError(...)`, create parallel error classes for new not-found paths in this feature. Never mix paradigms.

### Dependency injection (dimension 4)

Read an endpoint handler + a service class:

- **Constructor DI (framework-managed):** `constructor(private prisma: PrismaService) {}` — NestJS / Spring / .NET
- **Constructor DI (manual):** service instantiated at composition root, passed down explicitly
- **Framework container without constructors:** `@inject()` decorators, or `useContext(...)` (React)
- **Manual instantiation:** `const service = new SupplierService(new PrismaClient())` at every call site (rare in well-structured repos)

**Rule.** Match. If the repo uses NestJS's `@Injectable` + `@Module` registration, new services go through that mechanism.

### Config access (dimension 5)

Grep 1-2 files for how env vars are accessed:

- **Direct:** `process.env.DATABASE_URL` at call site
- **Config module:** `import { config } from '@/config'; config.database.url`
- **Framework-typed:** `Settings(BaseSettings)` in Python; `ConfigService` in NestJS; `IConfiguration` in .NET
- **12-factor library:** `dotenv-safe`, `@nestjs/config`, etc.

**Rule.** New env vars are added to the SAME module + registered in the SAME way. Never sprinkle `process.env.NEW_VAR` if the repo uses a config module.

### Logging (dimension 6)

Grep for how errors / important events are logged:

- Console (`console.log`, `console.error`)
- Structured logger (`winston`, `pino`, `structlog`, `Serilog`, `Logrus`)
- Framework's logger (NestJS's `Logger`, Django's `logging`)

**Rule.** Match. Same level conventions (info for lifecycle, warn for recoverable, error for unrecoverable). Structured logs use the same shape (`{ event, taskId, ... }` or similar).

### Testing setup (dimension 7)

Read the test config + one existing test:

- Test file location: `*.test.ts` next to source, or `tests/` mirror folder, or `__tests__/` subfolders
- Fixture location: `fixtures/` folder, or inline in `beforeEach`, or via a factory library
- Mocking approach: `vi.mock(...)` / `jest.mock(...)` / `@patch(...)` / hand-rolled mocks / DI-swap
- Assertion style: `expect(x).toBe(y)` / `assert.equal(x, y)` / `x.Should().Be(y)`

**Rule.** Match. New tests go where existing tests go, use the same mocking approach, use the same assertion style.

### Naming (dimension 8)

Grep a few files for identifier casing per kind:

| Identifier kind | TypeScript convention | Python convention | Go convention |
|---|---|---|---|
| File name | `camelCase.ts` OR `kebab-case.ts` OR `PascalCase.tsx` (components) | `snake_case.py` | `snake_case.go` |
| Class | `PascalCase` | `PascalCase` | `PascalCase` (exported) |
| Function | `camelCase` | `snake_case` | `camelCase` (private), `PascalCase` (exported) |
| Constant | `SCREAMING_SNAKE_CASE` | `SCREAMING_SNAKE_CASE` | `PascalCase` |
| Local var | `camelCase` | `snake_case` | `camelCase` |

**Language defaults are strong** — but the repo might deviate (e.g. TS repo using `snake_case` for functions to match a Python-backed team). **Match the repo, not the language default.**

---

## 4. What to write down

Append to `dev/implementation-log.md`:

```yaml
inferred_patterns:
  folder_structure:  feature-first (features/<slug>/{page,service,model}.ts)
  import_style:      absolute with @/ alias (100%)
  error_handling:    custom error classes inheriting from ApplicationError; middleware converts to HTTP
  dependency_injection: NestJS @Injectable + @Module registration
  config_access:     ConfigService via constructor injection
  logging:           NestJS Logger, structured messages { event, taskId }
  testing:
    location:        *.spec.ts next to source
    fixtures:        factories/ folder
    mocking:         @nestjs/testing Test.createTestingModule + overrides
    assertions:      expect(x).toBe(y) (Jest style)
  naming:
    files:           camelCase.ts (services), PascalCase.tsx (components)
    classes:         PascalCase
    functions:       camelCase
    constants:       SCREAMING_SNAKE_CASE
    local_vars:      camelCase
  inferred_at:       2026-08-31T14:22:11Z
  files_read:
    - src/main.ts
    - src/app.module.ts
    - src/features/user/user.controller.ts
    - src/features/user/user.service.ts
    - src/features/user/user.service.spec.ts
    - src/config/configuration.ts
    - vitest.config.ts (skipped — no Vitest, uses Jest)
  fallbacks:  none
```

---

## 5. Handling fallbacks

If a dimension can't be inferred (e.g. no existing tests, no logging in any file read):

1. Log the missing signal
2. Fall back to what the framework's canonical docs recommend
3. Log a `DEC-###` in `shared-context/decision-log.md`: `Chose <fallback> for <dimension> because repo has no existing pattern`

Never guess silently. A fallback is a decision the reader must be able to trace.

---

## 6. When repo patterns conflict with the plan

If the dev-plan says "add a Repository class" but the repo pattern is "service classes call ORM directly, no Repository layer" — DO NOT add the Repository. Match the repo. Log a `DEC-###` recording the deviation from the plan's wording, and note that the plan's intent (data access abstraction) is achieved through the existing service pattern.

Rationale: the plan is a spec of BEHAVIOUR, not of STRUCTURE. Structure matches the repo.

**Exception:** if the plan-blocker fold explicitly locked in a structure (e.g. "PB-005 resolution: introduce Repository pattern"), the fold's decision wins over inferred pattern. This is one of the cases the plan-blocker loop is for.
