# Test-readiness rubric — the areas a QA audit scores

Score each **applicable** area /10, back every deduction with a `QAF-###` finding, and mark areas that don't apply `N/A` (don't zero-score them). The readiness score is the average of applicable areas; any `Blocker` finding caps the overall verdict downward. The guiding question for every area is the same: **can the dev delivery loop prove a feature against this?**

Severity guide: **Blocker** = the loop cannot meaningfully validate features until fixed. **Major** = the loop can validate but with a real, agreed gap. **Minor** = quality/maintainability gap. **Nit** = polish.

---

## 1. Unit test framework & runner
Is there a configured test runner, a discoverable test location/convention, and a single command to run unit tests? Do example tests actually pass? *No runner at all is a Blocker — the dev loop has nothing to run.*

## 2. Integration testing
Can components/modules be tested together (DB, services, in-process API) with a repeatable setup/teardown? Is there a way to spin up dependencies (test DB, containers) deterministically?

## 3. End-to-end / UI testing harness
For apps with a UI: is there an e2e tool configured (Playwright, Cypress, …), a base config, a way to run headless in CI, and a page-object/fixtures skeleton to keep specs maintainable? `N/A` for headless/back-end-only services — note why.

## 4. Coverage measurement & thresholds
Is coverage instrumented, reported in a machine-readable form, and enforced with a threshold that fails the build below the floor? No enforcement means coverage can silently rot — at least Major.

## 5. Linting
Is a linter configured with an agreed rule set and a single command, and does it run clean (or with a known baseline)? The dev loop runs lint as a gate — an absent or broken lint setup undermines it.

## 6. Formatting
Is an autoformatter configured with a check mode (so CI can fail on unformatted code) and an editor/pre-commit hook where useful?

## 7. Type checking
For typed or gradually-typed stacks: is a type-checker configured with a single command and a known baseline? `N/A` for untyped languages with no type tooling — note it.

## 8. CI test automation
Do the checks above run automatically on push/PR in CI, in the right cheap-to-expensive order, gating merges? A green suite that only ever runs locally is a Major gap — the loop's guarantees aren't enforced.

## 9. Test data & fixtures/factories
Is there a sanctioned way to build test data (factories/builders/fixtures) and reset state between tests, so tests are isolated and deterministic rather than order-dependent?

## 10. Mocking & test doubles for external dependencies
Can external services/APIs/time/randomness be stubbed or mocked deterministically? Without this, features that depend on unavailable services can't be validated — often a Blocker for those features.

## 11. Contract / API testing
For services exposing or consuming APIs: are request/response contracts asserted (schema/contract tests) so a breaking change is caught? Maps to the TL `EP-<AREA>-NN` endpoints. `N/A` if no API surface.

## 12. Test conventions & documentation
Is there a short, written testing convention (where tests live, how to name them, what each level covers, how to run them) so the dev agent writes feature tests consistently into the harness? An undocumented harness gets used inconsistently.

---

## Optional areas — score only where the project requires them
- **Accessibility testing** (a11y assertions in e2e).
- **Performance / load testing** (baseline budgets).
- **Security testing** (dependency scanning, SAST in CI).
- **Visual regression** (snapshot/screenshot diffing).

Mark these `N/A` unless the scope, the architecture, or the human asks for them — recommend, don't impose.

---

## Verdict bands (overall readiness score, average of applicable areas)
- **0.0–2.9 — Not testable.** No runnable suite; the dev loop can't prove anything. (Any Blocker forces at most this band until resolved.)
- **3.0–5.4 — Major gaps.** Something runs, but key levels (e2e, integration, coverage enforcement, or CI) are missing.
- **5.5–7.9 — Workable.** The dev loop can validate most features; specific, named gaps remain.
- **8.0–10.0 — Solid.** Runner, coverage enforcement, CI gating, fixtures, and conventions are in place; the harness is ready for the loop.
