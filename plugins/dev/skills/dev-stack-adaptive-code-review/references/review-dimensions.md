# Review dimensions — 7 things to check on every diff

**Purpose.** Enumerate the review lens. For each dimension, the reviewer knows what to look for + what patterns to match against + what severity to emit.

Each dimension applies to every diff regardless of stack. Framework-specific SIGNALS live in `stack-signals.md`.

---

## Dimension 1 — Correctness

**Question.** Does this code actually do what `implementation.md` said?

**Signals.**

- Each implementation.md build sequence step should be represented by code in the diff. Missing steps = incomplete work.
- Function signatures match what the implementation.md build sequence / TL Implementation §2 API endpoints described (e.g. `POST /supplier` request body, response shape, refusal codes).
- Business rule enforcement points (see Dimension 5) are wired up.
- Off-by-one errors, wrong operators (`===` vs `==`, `>=` vs `>`), inverted conditions.
- Error paths that don't propagate to the caller.
- Race conditions in async code (missing `await`; parallel `Promise.all` where sequential was required).

**Severity guidance.**

- Missing implementation.md build sequence step → **Blocker** (feature is incomplete)
- Wrong endpoint contract → **Blocker** (violates TL spec)
- Off-by-one / inverted condition → **Major** (behavioural bug)
- Missing `await` → **Major** (async correctness)

**Ignore.** Trivial refactors (renaming a local var — that's Nit at most). Perfect-vs-good discussions.

---

## Dimension 2 — Convention adherence

**Question.** Does this new code match the repo's existing conventions?

**Signals.**

- Naming: does the new code follow `inferred_patterns.naming.functions` (camelCase, snake_case, PascalCase)?
- Imports: does the new code use aliases the repo uses (`@/services/...`) vs relative (`../services/...`)?
- File placement: is the new file where similar existing files live?
- Async style: does the repo use `async/await` OR `.then()` chains? Match.
- Comment style: does the repo use JSDoc / docstrings? Match.

**Severity guidance.**

- New public API using different naming case than existing → **Major** (breaks readability)
- Import style differs from repo dominant → **Minor** (readable but off-pattern)
- Comment format inconsistent → **Nit**

**Ignore.** Preferences the repo doesn't clearly express. If the repo mixes both styles 50/50, don't flag either.

---

## Dimension 3 — Error handling

**Question.** Does the new code handle errors the way the repo handles errors?

**Signals.**

- Custom error classes: if `inferred_patterns.error_handling` is *"custom errors inheriting from ApplicationError"*, does the new code throw one of those OR introduce a new one that inherits properly?
- Result types: if the repo uses `Result<T, E>` returns, does the new code follow?
- Try/catch: does the new code wrap risky operations OR does the repo let framework middleware handle it? Match.
- Error propagation: does the new code silently swallow errors, or does it propagate?
- Logging in the error path: matches repo's logging style?

**Severity guidance.**

- New code throws plain `Error` where repo uses custom errors → **Major**
- Silently swallows an error (empty catch block, error ignored) → **Blocker** (silent failures are bugs)
- Missing try/catch on risky op where repo pattern is to wrap → **Major**
- Missing error logging → **Minor** if repo pattern is to log; **Major** if BR requires audit trail

**Ignore.** Empty `catch` blocks with a comment explaining why (`// intentionally ignored — pattern retry handled elsewhere`).

---

## Dimension 4 — Testability

**Question.** Is the new code structured so tests can exercise it?

**Signals.**

- Hardcoded time (e.g. `new Date()` inside business logic without DI'd clock) → tests can't control time
- Hardcoded external calls (e.g. `axios.get(...)` inside a service instead of DI'd HTTP client) → tests can't mock
- Static/singleton state that persists across tests → flakiness
- Dependencies constructed inside the class (no injection) → tests can't swap
- Global state modification (env var write, `sys.path.append`) → test pollution

**Severity guidance.**

- Hardcoded time / random / external call inside business logic → **Major**
- Global state mutation → **Major**
- Static class without DI where repo pattern is DI → **Major**

**Ignore.** Pure utility functions that don't need DI (a `formatCurrency(number)` function doesn't need DI'd anything).

---

## Dimension 5 — Business rule enforcement

**Question.** Every parent-declared `BR-N` that applies to this diff — is it enforced in code?

**Signals.**

- For each `BR-N` in parent's `business-rules.md`, look for a code path that enforces it:
  - DB-level: unique constraint, foreign key, check constraint
  - Service-level: pre-write validation, pre-check query
  - Middleware / framework-level: guards, decorators
- If the BR is "tax_id unique per country" and the diff adds a supplier endpoint — is there ANYWHERE the uniqueness is checked?

**Severity guidance.**

- BR that applies to diff's domain has no enforcement → **Blocker** (feature is incorrect)
- BR enforcement is wrong (e.g. checks wrong condition) → **Blocker**
- BR enforcement is only at one layer where multi-layer is required (e.g. UI checks but no server check — security bypass) → **Major**

**Ignore.** BRs from parent that don't apply to this sub-task's layer (a UI-scoped BR doesn't need enforcement in a backend sub-task).

---

## Dimension 6 — Naming

**Question.** Do identifiers match the repo's naming conventions AND business language?

**Signals.**

- Match `inferred_patterns.naming` for casing (see Dimension 2 — this is more granular)
- Business language: `Supplier`, not `SupplierEntity`. `sendConfirmationEmail`, not `sendConfirmationEmailWithNodemailer`.
- No framework name in identifier: `SupplierListPage`, not `SupplierListReactPage`.
- No implementation-detail leakage: `createSupplier`, not `createSupplierViaHttpEndpoint`.
- Consistent verb choice: if repo uses `create`, `read`, `update`, `delete`, don't introduce `add`, `fetch`, `patch`, `remove`.

**Severity guidance.**

- Framework name in a class / function identifier → **Major** (leaks stack)
- Business-language violation (using technical term where business term applies) → **Minor**
- Inconsistent verb choice → **Minor**

**Ignore.** Internal helper names that aren't exposed (a private `_computeHash` inside a class).

---

## Dimension 7 — Reuse

**Question.** Does the new code reuse existing abstractions where possible, or introduce parallel ones?

**Signals.**

- Repo has a `UserRepository` — does the new `SupplierRepository` follow the same pattern (same base class, same method signatures where equivalent)? OR does it introduce a competing abstraction?
- Repo has utility functions (`formatCurrency`, `getConfig`) — does the new code use them or reimplement?
- Repo has middleware (`AuthGuard`, `RateLimitGuard`) — does the new endpoint use it or duplicate the logic inline?

**Severity guidance.**

- Introduces a new pattern parallel to an existing one → **Major** (fragmentation)
- Duplicates utility function logic → **Minor**
- Doesn't use existing middleware for a role the middleware handles → **Major** (also a security concern)

**Ignore.** New patterns that genuinely diverge (a new subsystem legitimately needs its own abstractions). But flag as a discussion point if unclear.

---

## Applying dimensions to a diff

For each changed file:

1. Read the diff hunks
2. For each hunk, walk dimensions 1-7 in order
3. For any signal that fires, record a candidate finding
4. After all hunks in the file are reviewed, deduplicate: multiple hunks with the same underlying issue → one finding
5. Move to next file

For each finding written to `dev/code-review-findings.md` OR emitted via `ReportFindings`:

```yaml
- severity: Major
  category: error_handling
  file: src/supplier/service.ts
  line: 42                                  # line number in the diff, or in the file post-change
  summary: "New code throws plain Error; repo pattern is custom error classes inheriting from ApplicationError."
  failure_scenario: "In production, this error would bypass the AppErrorFilter and return a 500 with a generic message instead of the expected 4xx with a business error code. Downstream services expecting DuplicateSupplierError would see 500 and retry, causing amplification."
  fix_suggestion: |
    Introduce a new DuplicateSupplierError class:

      class DuplicateSupplierError extends ApplicationError {
        constructor(taxId: string, country: string) {
          super(`Supplier already registered: ${taxId} / ${country}`, 'DUPLICATE_TAX_ID', 409);
        }
      }

    Then in service.ts:42:
      throw new DuplicateSupplierError(taxId, country);

    See src/order/errors/DuplicateOrderError.ts for a similar existing example.
```

---

## Not this skill's job

- Reviewing style (lint / format catches these)
- Reviewing security (`security-review` skill's job in `/dev:commit` Stage 3)
- Reviewing test coverage numbers (Stage 8 acceptance-map covers correctness; QA gates cover the numbers)
- Reviewing performance micro-optimizations (only NFR-declared perf targets are checked)
- Speculating about "future maintenance burden" without concrete evidence
