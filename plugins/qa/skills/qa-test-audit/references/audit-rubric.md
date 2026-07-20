# Test-readiness rubric — the areas a QA audit scores

Score each **applicable** area /10, back every deduction with a `QAF-###` finding, and mark areas that don't apply `N/A` (don't zero-score them). The readiness score is the average of applicable areas; any `Blocker` finding caps the overall verdict downward. The guiding question for every area is the same: **can the dev delivery loop prove a feature against this?**

Severity guide: **Blocker** = the loop cannot meaningfully validate features until fixed. **Major** = the loop can validate but with a real, agreed gap. **Minor** = quality/maintainability gap. **Nit** = polish.

---

## 0. Baseline pass — the mandatory floor (run first)

Before the /10 area scoring, check the repo against the active **baseline profile** (`shared-context/baseline-profile.md` if present, else the `delivery-os-core` org default). Each mandatory capability (`BL-01`…`BL-10`) must be **present AND enforced** (in pre-commit and/or merge-gating CI) — a present-but-unenforced check does not satisfy a mandatory item.

- For each unmet mandatory `BL-##`, record a **mandatory gap** finding — a `QAF-###` marked `baseline: BL-##`, severity at least `Major` (`Blocker` when it means the loop can't validate at all, e.g. no runner). These are **not discretionary**: the human may not silently `Skip` one; skipping is an explicit `DEC-###` with a rationale, and it stays listed in the gates' `baseline_unmet`.
- Resolve each `BL-##` to the stack's concrete tool via `tl-maturity-audit/references/stack-bindings.md` so the recommendation names the right tool (ESLint vs RuboCop vs Roslyn, coverlet vs c8, etc.).
- Set `baseline_status: Met` in the quality-gate contract only when every mandatory item is enforced; otherwise `Unmet` with the `baseline_unmet` list. The dev readiness gate and the TL maturity audit both read this.

Note the deltas from the discretionary areas below: **pre-commit enforcement (BL-07), dependency scanning (BL-08), and secret scanning (BL-09)** are **mandatory** under the baseline even though they appear as optional/CI concerns in the area scoring — the baseline promotes them to a required floor.

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
