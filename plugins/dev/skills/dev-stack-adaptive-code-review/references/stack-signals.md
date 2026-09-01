# Stack signals — pattern-based idiom checks per language / framework

**Purpose.** Concrete signals to look for when applying the 7 dimensions. Not a per-stack playbook — instead, patterns that appear IN THE REPO which the reviewer matches against the diff.

Every signal is: *"the repo uses X pattern; if the diff violates X consistently, flag."* Never *"the framework docs say X; if the diff violates X, flag."*

---

## TypeScript / JavaScript signals

### Error handling patterns

Read one existing service + one existing controller in the repo. Recognize:

- **Custom-error hierarchy**: files with `class XError extends ApplicationError` or similar
- **Result type**: functions returning `{ ok: true, value: T } | { ok: false, error: E }` or `Result<T, E>` from a lib like neverthrow
- **Framework HTTP exceptions**: `throw new HttpException(...)` (NestJS), `res.status(400).json(...)` (Express raw)
- **Silent async**: `.catch(() => {})` — usually a bug

Applied to review:
- Diff uses `throw new Error(...)` when repo has custom hierarchy → Major
- Diff returns raw dict instead of typed Result → Major (if repo uses Result)
- Diff has `.catch(() => {})` — always a Blocker (silent failures)

### Import style signals

Grep 2-3 existing source files for import lines:

- `import X from '@/foo/bar'` (alias) → alias-first
- `import X from '../foo/bar'` (relative) → relative-first
- `import X from 'src/foo/bar'` (path from root) → root-path style
- `import { X } from 'foo/bar'` (barrel) vs deep imports

Applied:
- Diff uses relative in alias-first repo → Minor
- Diff mixes styles within one file → Minor

### DI style signals

- Constructor DI decorated (NestJS `@Injectable`, InversifyJS `@inject`)
- Manual composition root (services instantiated in `main.ts` and passed down)
- Framework container (Awilix, tsyringe)
- No DI at all (services `new`'d at call site)

Applied:
- Diff introduces manual `new` where repo uses DI → Major
- Diff introduces DI where repo doesn't use it → Major (parallel pattern)

### Async signals

- `async/await` throughout (modern)
- `.then().catch()` chains (older codebases)
- Mixed (usually async is winning; match dominant)

Applied:
- Diff uses `.then()` chains in async-heavy repo → Minor
- Diff has `Promise.all` where sequential is required (per business logic ordering) → Blocker

### React signals

- Function components vs class components
- Hooks vs HOCs vs render props
- State management: local `useState`, Context, Redux, Zustand, Jotai, Recoil
- Styling: CSS Modules, Tailwind, styled-components, emotion

Applied:
- Diff adds class component in a hooks-only repo → Major
- Diff introduces new state management library → Major (fragmentation)
- Diff adds styled-components in a Tailwind repo → Major

### NestJS signals

- Module registration in `AppModule` or feature-module
- `@Injectable()` on services, `@Controller()` on controllers, DTO validation via `class-validator`
- Guards, interceptors, pipes registered globally or per-route

Applied:
- New service without `@Injectable()` → Major
- New endpoint without `@UseGuards(AuthGuard)` where all other endpoints have it → Blocker (security)
- New DTO without `class-validator` decorators → Major (validation gap)

### Express signals

- Middleware chain style (`app.use(...)`) vs router-based (`express.Router()`)
- Error handling via 4-arg middleware `(err, req, res, next) => ...`
- Async wrappers (e.g. `express-async-errors`)

Applied:
- Diff adds unwrapped async handler where repo uses async-error middleware → Major (uncaught rejection)
- Diff uses `res.status(400).json(...)` where repo throws to error middleware → Major (inconsistent)

---

## Python signals

### Error handling

- Custom exception hierarchy (`class SupplierAlreadyExists(ApplicationError):`)
- `raise ValueError(...)` or `raise Exception(...)` (framework-agnostic)
- Return `Result` type via `returns` library or ADT-style

Applied:
- Diff uses bare `Exception` where repo has hierarchy → Major
- Diff catches broad `Exception` → Major (should catch specific)
- Diff has `except: pass` → Blocker

### Import signals

- Absolute vs relative imports
- `from foo import bar` vs `import foo.bar`
- Namespace / package structure

Applied:
- Diff uses relative in an absolute-import repo → Minor

### Type hints

- Fully-typed codebase (`def foo(x: int) -> str:`)
- Partially typed
- Untyped

Applied:
- Diff adds untyped functions in fully-typed repo → Major (breaks mypy)
- Diff uses `Any` where a specific type is inferrable → Minor

### FastAPI signals

- Pydantic models for request/response
- Dependencies via `Depends(...)`
- Router grouping via `APIRouter`

Applied:
- Diff adds endpoint without Pydantic model on request → Major
- Diff hardcodes DB session instead of `Depends(get_db)` → Major

### Django signals

- Model-View-Template split
- ORM query style (`objects.filter(...)` vs raw SQL)
- Forms / DRF serializers

Applied:
- Diff bypasses ORM with raw SQL where similar queries use ORM → Major
- Diff uses `objects.raw()` without SQL injection guard → Blocker

---

## Go signals

### Error handling

- Idiomatic: `if err != nil { return err }` propagation, wrapping with `fmt.Errorf("... %w", err)`
- Custom error types via structs implementing `Error()`
- Panic (rare, should only be at init)

Applied:
- Diff swallows error (`_ = doThing()`) → Blocker unless commented
- Diff panics in request handler → Major
- Diff doesn't wrap error → Minor

### Import signals

- Grouped imports: std, third-party, project (blank lines between)

Applied:
- Diff mixes groups → Nit (usually auto-formatted, but occasionally slips)

### Interface signals

- Small interfaces at consumer side
- Struct methods

Applied:
- Diff introduces god-interface (10+ methods) → Major (usually a design smell in Go)

---

## Java / Spring Boot signals

### Error handling

- Checked exceptions in signatures OR RuntimeExceptions with @ControllerAdvice
- ResponseEntity patterns

Applied:
- Diff throws generic `Exception` → Major
- Diff swallows in catch block → Blocker

### DI signals

- Constructor injection via `@Autowired` or Lombok's `@RequiredArgsConstructor`
- Field injection (older style; usually flagged)

Applied:
- Diff uses field injection in constructor-injection repo → Major

### Persistence

- JPA/Hibernate via Spring Data
- MyBatis
- JDBC direct

Applied:
- Diff uses raw JDBC in Spring Data repo → Major

---

## .NET / C# signals

### Error handling

- Custom exception classes
- Result pattern via a lib
- Exception filters

Applied:
- Diff swallows in catch → Blocker
- Diff throws `Exception` (base) → Major

### DI signals

- `services.AddScoped<IFoo, Foo>()` in `Program.cs` / `Startup.cs`
- Interface-based injection

Applied:
- Diff instantiates directly instead of via DI → Major (parallel pattern)
- Diff missing interface for testability → Major

### EF Core signals

- DbContext usage patterns
- Async methods (`.ToListAsync()`)
- No-tracking queries for reads

Applied:
- Diff uses sync `.ToList()` in async-heavy repo → Major
- Diff doesn't `.AsNoTracking()` on a read that never writes → Minor (perf)

---

## SQL / Migrations signals

### Migration patterns

- Reversible migrations (up + down)
- Idempotent operations (`CREATE TABLE IF NOT EXISTS`)
- Constraints named explicitly (not auto-generated)

Applied:
- Diff adds constraint without name → Minor (harder to alter later)
- Diff has DDL without a rollback path → Major (breaks rollback story)
- Diff uses `SELECT *` in a migration script (usually a smell) → Minor

### Index strategy

Applied:
- Diff adds composite index on wrong column order → Major (perf)
- Diff drops index without adding a replacement → Major (perf regression)

---

## Universal signals (any stack)

### Magic values

Applied:
- Diff has `if (x > 30) ...` where 30 is unexplained → Minor
- Diff has string literal `'DUPLICATE_TAX_ID'` used in 3+ places without a constant → Minor

### Comments

Applied:
- Comment says "TODO" without an owner or issue → Nit
- Comment contradicts the code below it → Major
- Comment leaks stack (e.g. "using axios because fetch is broken here") → Minor

### Naming

Applied:
- Function name doesn't match what it does (e.g. `getUser` that also creates one) → Major
- Variable name is single letter outside a very short block → Nit
- Class name uses framework name → Major

---

## What NOT to flag (regardless of stack)

- Formatting (lint/format handles)
- Ordering of imports (auto-formatter's job)
- Missing type hints on obviously-typed local vars in gradual-typing repos
- "You could write this more cleverly" — cleverness isn't a virtue in review
- Style preferences that the repo itself hasn't established

The reviewer is a bar-raiser only for behaviour + convention, not for style.
