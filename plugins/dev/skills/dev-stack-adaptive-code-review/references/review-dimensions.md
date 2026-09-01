# Review dimensions — 8 things to check on every diff

**Purpose.** Enumerate the review lens. For each dimension, the reviewer knows what to look for + what patterns to match against + what severity to emit.

Each dimension applies to every diff regardless of stack. Framework-specific SIGNALS live in `stack-signals.md`. Numeric limits (complexity, function length, nesting depth, duplication) come from `shared-context/coding-standards.md` — Dimension 8 fires when the diff exceeds the declared limit.

---

## Dimension 1 — Correctness

**Question.** Does this code actually do what `implementation.md` said?

**Signals.**

- Each implementation.md build sequence step should be represented by code in the diff. Missing steps = incomplete work.
- Function signatures match what the implementation.md `§1 Build sequence` + `§3 Operations exposed and consumed` described — request/message inputs, success payload shape, refusal codes.
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

## Dimension 8 — Clean code & anti-patterns

**Question.** Does the new code meet the engineering-standard limits declared in `shared-context/coding-standards.md` — complexity, length, nesting, duplication, recursion policy, magic values, boolean-flag arity, forbidden anti-patterns?

**Read `shared-context/coding-standards.md` first.** Its §6 (function complexity budget), §7 (duplication policy), §8 (recursion policy), §9 (constants & magic values), §12 (anti-patterns forbidden) declare the NUMERIC and CATEGORICAL limits. Dimension 8 checks the diff against those limits. If `coding-standards.md` is missing or a section is blank, escalate that as a Blocker on `dev/escalation-<n>.md` — the review cannot fire without the contract to check against, and the fix goes upstream to whoever authors standards.

**Signals.**

- **Complexity budget breach.** A new/modified function's cyclomatic complexity exceeds `coding-standards.md §6` limit. Signals from the diff: function contains more than N distinct branches (if/switch/case/ternary/&&/||/? patterns) where N is the declared threshold.
- **Function length breach.** Function body exceeds `§6` line limit.
- **Nesting depth breach.** Any block is indented deeper than `§6` declared depth.
- **Parameter arity breach.** Function signature has more parameters than `§6` limit, OR more boolean parameters than the boolean-flag sub-limit.
- **Duplication.** Two or more blocks of ≥ `§7`-declared identical (or near-identical, differing only in identifiers) lines appear either within the diff or between the diff and pre-existing code the diff references. A helper extraction is required.
- **Unnecessary recursion.** A function calls itself where the stack's `§8` recursion policy requires iteration — signals: no accumulator, no memoization on repeated sub-problems, unbounded input, or the stack's policy explicitly names this case as iterative-only. The reviewer describes WHY iteration is required in the finding, not just "recursion is bad."
- **Magic value.** A numeric or string literal outside the neutral small set (`0`, `1`, `-1`, `""`, `null`, `true`, `false`) appears inline instead of as a named constant. Repeated occurrences of the same literal in the diff amplify severity.
- **Anti-pattern hit.** The diff exhibits one of `§12`'s forbidden anti-patterns: god function/class/file (single unit doing multiple unrelated concerns), premature abstraction (interface/wrapper with one implementation and one caller in the diff), dead code (unreachable branch, unused declaration after refactor), comment-code mismatch (comment describes different behaviour than the code), silent catch (empty catch block with no explaining comment), magic sleep in tests, mock-only tests that assert nothing about SUT state.
- **State & side-effect leaks.** Hardcoded time / random / external IO in business logic where the repo's `§10` state policy requires injection.

**Severity guidance** (all thresholds come from `coding-standards.md` — Dimension 8 is enforcement, not policy):

- Complexity breach on a new function → **Major** (readability + testability compound).
- Complexity breach on a modified function that was already over limit and the diff makes it worse → **Major**.
- Complexity breach on a modified function that was over limit before the diff and the diff doesn't change complexity → **Nit** (pre-existing debt; not this diff's job unless the diff touches the offending branches).
- Duplication ≥ declared limit → **Major** (fragmentation risk).
- Unnecessary recursion where `§8` requires iteration → **Major** (correctness/perf risk on unbounded input; stack overflow risk on some stacks).
- Function length or nesting depth breach → **Major**.
- Parameter arity breach → **Minor** (fixable via config object) unless the extra parameters include ≥ 3 booleans, then **Major** (obvious refactor).
- Magic value single occurrence → **Nit**; ≥ 3 occurrences of the same literal → **Minor**; magic value inside a condition or off-by-one region → **Major**.
- God function / god class / god file → **Major** (splittable now, harder later).
- Premature abstraction (single-impl single-caller wrapper) → **Minor** with the suggestion to inline.
- Dead code → **Minor** (housekeeping) unless it's a security-relevant path being silently kept alive, then **Major**.
- Silent catch → **Blocker** (a swallowed error is a hidden bug).
- Comment-code mismatch → **Minor** (misleading, but usually mechanical fix).
- Hardcoded time / random / external IO in business logic → **Major** (Dimension 4 also covers testability; this dimension checks the standard's rule).

**Ignore.**

- Numeric literals used as their neutral small set values (loop counters starting at `0` / `1`, sentinel `-1`, empty string, boolean literals).
- Anti-patterns pre-existing in the file that the diff does not touch or amplify.
- Complexity in generated code (parser output, migration file, protobuf stub) — declare the generated file globs in `§6`, then Dimension 8 skips them.

**Finding format.** Every Dimension 8 finding names the specific rule breached, the exact numeric limit vs the observed value (for quantitative breaches), and the abstract refactor:

```yaml
- severity: Major
  category: clean_code
  rule: coding-standards.md §6 cyclomatic-limit
  file: <file>
  line: <line>
  observed: <observed value>
  limit: <limit from coding-standards.md>
  summary: "<one-line statement of the breach>"
  failure_scenario: "<concrete scenario where the breach causes harm — e.g. deep nesting makes the change-case impossible to review; unnecessary recursion causes stack overflow on inputs the plan lists as valid; god function will regress on the next unrelated edit>"
  fix_suggestion: "<the refactor, in prose — extract the inner block into a helper named X; replace recursion with iteration using accumulator Y; introduce a named constant Z; split the function on responsibility boundary W>"
```

---

## Applying dimensions to a diff

For each changed file:

1. Read the diff hunks
2. For each hunk, walk dimensions 1-8 in order
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
