# Eval design (applied-AI features only)

How the TL designs runnable **evals** for a feature's AI behaviour during planning, so the dev loop can later run them as the proof that behaviour works. Read this together with the shared **`eval-engineering`** skill (the method, the unit schema, the reward-hacking guard, the Harbor export) — this file is the *planning-time* how-to. Skip all of it for a deterministic feature: those are proven by the dev acceptance-map alone.

---

## 1. Is this feature AI-bearing?

Design evals **only** when the feature's behaviour depends on a model's output (`delivery-os-conventions` §5): generation, classification/extraction, ranking or semantic search, RAG, or agentic tool use — or it declares `ai_component: true` / cites an `INT-###` to an LLM/AI provider. Reuse the same LLM/AI determination `tl-spec-review` makes. If a feature has both AI and deterministic parts, evals cover only the **AI-driven acceptance criteria**; the deterministic criteria stay on the normal acceptance-map. When it's genuinely unclear, raise an **open question** rather than guessing either way.

## 2. One eval per AI-driven acceptance criterion

Walk the feature's `acceptance-criteria.md`. For each criterion whose truth depends on model output, author one `EVAL-<AREA>-NN` unit (a distinct route through a criterion — a different input class, a failure path — can be its own eval). For each, decide:

- **Instruction** — the real input and goal the feature receives, phrased as production would phrase it. Ground it in the feature's `workflow.md` and the business rule (`BR-###`) or integration (`INT-###`) behind the behaviour.
- **Environment** — the fixtures and seeded data the task needs, and the **tool table**: for every tool the behaviour may call, mark it `live` or `simulated`, and for each simulated tool give the canned result. Simulate anything that costs money, writes to production, sends a real message, or is non-deterministic enough to defeat the verifier; run live only the read-only, deterministic behaviour you're actually verifying.
- **Verifier** — the scoring method and the exact pass condition. Pick by criterion shape: a **deterministic assertion** where the behaviour has a checkable effect (a record changed, a tool was actually called, output validates against a schema); a **rubric / LLM-as-judge** with named criteria where the output is open-ended; a **structural check** for format/citation contracts. Note explicitly the **reward-hacking risks** the verifier must resist (claimed-but-not-done actions, over-citing, reachable answers) and how it resists them — verify the trajectory, not just the final string, and keep expected answers out of the environment.

## 3. Link it into the graph

Every eval unit links back like any other `context/` node:

- **Verifies** the acceptance criterion it proves, and cites the `EP-<AREA>-NN` / `ENT-<AREA>-NN` units the behaviour exercises and the `BR-###`/`INT-###` behind it.
- Appears as a row in `context/evals/eval-index.md` (id, feature, criterion, verifier type, live/sim, status).
- **Reuse before create:** a criterion two features share gets one eval with both features linked — not a duplicate. Match on the criterion + behaviour it verifies.

## 4. Log decisions; escalate real unknowns

Append a `DEC-###` to `shared-context/decision-log.md` for each material eval-design choice (a chosen verifier type, a simulate-vs-live call with cost/safety impact, a rubric's pass bar). Where designing the verifier surfaces a genuinely undecided point that changes behaviour — an undefined success criterion for the AI output, an unknown ground-truth source, an integration contract you can't see — record an **open question** on the eval unit rather than inventing a pass condition. You are the design authority for *how the behaviour is verified*, not for inventing what "correct" means when the scope is silent.

## 5. You design; dev runs

Stop at the design. You author the instruction, the environment (including the live/sim decisions), and the verifier intent — enough that the dev loop can materialize a runnable verifier and execute it without re-deciding what the eval measures. You do **not** run the eval, wire live infrastructure, or write production scoring code; the `feature-delivery-loop` (via `dev-validation` and the loop's `references/eval-runner.md`) does that and inspects both sides at run time.

## Completion — evals for this feature are designed when

- [ ] Every AI-driven acceptance criterion maps to an `EVAL-<AREA>-NN` unit (instruction · environment · verifier).
- [ ] Each eval's tools are marked `live` or `simulated`, with a fixture for every simulated one.
- [ ] Each verifier states its pass condition and the reward-hacking risks it resists, and checks the trajectory where the criterion is about an action.
- [ ] Each eval links to the criterion it verifies and the `EP-/ENT-` units it exercises, and appears in `eval-index.md`.
- [ ] Material choices are `DEC-###`; genuine unknowns are open questions, not invented pass conditions.
- [ ] Shared criteria reuse one eval; no duplicates.
