# Eval runner (applied-AI features only)

How the delivery loop **materializes, runs, and inspects** the evals the TL designed, during the `TESTING` phase, and feeds them into `dev/acceptance-map.md`. Read this with the shared **`eval-engineering`** skill (the method and the unit schema). This applies **only to AI-bearing features** with `EVAL-<AREA>-NN` units under `context/evals/<feature-slug>/`; a deterministic feature has no evals and is proven by the standard suite.

---

## 1. Detect — are there evals to run?

After the standard `dev-validation` suite, check whether the feature is AI-bearing (`delivery-os-conventions` §5) and has eval units in `context/evals/<feature-slug>/` (via `context/evals/eval-index.md`). If it's AI-bearing but has **no** evals, that's a planning gap — the planning gate (`readiness-and-planning.md` §0) should have had the TL design them; if it didn't, re-delegate to `tl-feature-planning` for this feature rather than proving an AI criterion with a deterministic assertion. If it's not AI-bearing, there's nothing to do here.

## 2. Materialize — build a runnable verifier from each unit

For each `EVAL-<AREA>-NN` unit, turn the design into something executable in the repo's own test/tooling:

- **Instruction** → the input/goal handed to the system under test (call the real feature entry point where you can).
- **Environment** → seed the fixtures the unit names, and wire its **tool table**: run `live` tools against the real (read-only/free/deterministic) dependency; replace `simulated` tools with a stub returning the unit's canned result. Never let an eval hit a paid, prod-writing, or message-sending path the unit marked `simulated`.
- **Verifier** → implement the unit's pass condition as the type it declares — a deterministic assertion (state changed / tool actually called / schema valid), a rubric or LLM-as-judge scored against the named criteria, or a structural check. Keep expected answers **out of** the environment the model can read.

Prefer the project's existing test framework and any eval-runner command QA exposes in `quality-gates.md` (gate `QG-011` if present); fall back to a scoped harness for this run when none exists, and note that in the log. If the team runs LangChain's stack, the unit's Harbor export can be run instead — same verifier, same verdict.

## 3. Run and inspect both sides

Run each verifier and record the raw result in `dev/implementation-log.md`. Then **inspect both sides before trusting a pass** — the model's *trajectory* and the verifier's *verdict*:

- Did the model actually **do the work**, or did it satisfy the check without it (claimed an action it never took, over-cited to hit a "cites sources" bar, exploited answer material left in the environment, met a proxy not the goal)? A pass that survives only because the verifier is shallow is a **reward-hacked pass** — treat it as a failure, and record why.
- Did a **false fail** come from the eval (a too-strict verifier, a bad fixture) rather than the code? That's an eval defect — feed it back to the TL (`tl-feature-planning`) to revise the unit; don't "fix" the code to satisfy a wrong verifier.

Because model output is non-deterministic, run a flaky-looking eval a small fixed number of times and record the pass rate rather than a single sample where the unit calls for it.

## 4. Feed the acceptance map

Map each AI-driven acceptance criterion to its eval as the evidence, using the standard result values (`Passed` · `Failed` · `Blocked` · `Waived` · `Not Covered`) in `dev/acceptance-map.md`, with the eval id and run artifact as the evidence. An AI criterion with a designed eval that wasn't run is `Not Covered`, not `Passed`. A reward-hacked or failing eval is `Failed` — hand it to the repair loop.

## 5. Repair, within the loop's limits

A failing eval is a failure like any other: identify the cause, decide if it's actionable, make a focused fix, and rerun the eval first then the broader suite — honouring the loop's **3 focused attempts / 2 broad cycles** limit. Escalate when: the same eval fails after three focused fixes; a fix reward-hacks a different eval; the failure is an **eval defect** (→ TL to revise the unit); or the AI behaviour genuinely can't meet the criterion (a product/AI decision → escalate, don't loosen the verifier to force green).

## Boundaries

You **run and inspect**; you don't redesign what an eval measures (that's the TL's `EVAL-` unit), you don't loosen a verifier or delete expected-answer guards to force a pass, and you don't run a `simulated` tool live. Reward-hacking that you can't rule out is a `Failed`, not a `Passed` — and a genuinely wrong eval goes back to the TL, not quietly around.
