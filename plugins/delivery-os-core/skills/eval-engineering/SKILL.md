---
name: eval-engineering
description: The Delivery OS method for building runnable evals (verifiers) for applied-AI / LLM behaviour — the shared contract the TL uses to DESIGN evals during feature planning and the dev agent uses to RUN and inspect them during the delivery loop. Read this before authoring or executing an eval unit. It defines what an eval is here (instruction + environment + verifier), how to decide which tool calls run live vs. simulated, how to write verifiers that resist reward hacking, the EVAL-<AREA>-NN unit schema under context/evals/, and the optional Harbor / LangSmith export for teams on that stack. Adapted from LangChain's eval-engineering method (https://www.langchain.com/blog/towards-automating-eval-engineering). It is gated to AI/LLM features — deterministic features are proven by the normal acceptance-map flow and need no eval.
---

# Eval Engineering (runnable verifiers for AI behaviour)

Deterministic code is proven by asserting an output equals an expected value. **AI behaviour can't be** — a model paraphrases, reorders, and drifts, so "the tests pass" tells you little about whether the behaviour is actually right. An **eval** closes that gap: it is a task you can rerun that scores whether an AI-driven behaviour did its job, and it becomes the durable evidence a feature's AI part works — and stays working as prompts, models, and tools change.

This skill is the **shared contract two agents speak**. The **TL** reads it during `tl-feature-planning` to *design* an eval for each AI-driven acceptance criterion; the **dev agent** reads it during `feature-delivery-loop` to *materialize, run, and inspect* those evals as part of validation. QA owns the harness they run on. The method is adapted from LangChain's eval-engineering write-up ([towards-automating-eval-engineering](https://www.langchain.com/blog/towards-automating-eval-engineering)); the design/run split and the Delivery OS document contract are ours.

## When an eval applies — the AI gate

Design and run evals **only for AI-bearing features** (`delivery-os-conventions` §5): a feature whose behaviour depends on a model's output — generation, classification/extraction, ranking or semantic search, RAG, or agentic tool use — or that declares `ai_component: true` / cites an `INT-###` to an LLM/AI provider. A deterministic CRUD feature is proven by the dev **acceptance map** alone and needs no eval — do not invent one for it. When it's genuinely unclear whether a feature is AI-bearing, that's an **open question**, not a silent skip: an AI criterion proven only by a deterministic assertion is a false green.

## What one eval is — three parts

An eval unit has the same three parts LangChain names, mapped onto Delivery OS:

- **Instruction** — the task handed to the system under test at the start: the input, context, and the goal, phrased the way the real feature receives it. It exercises one AI-driven acceptance criterion (or one distinct route through it).
- **Environment** — the tools, data, and fixtures the task runs against: seeded records, stub documents, the tools the model may call, and any preconditions. This is where the **live-vs-simulated** decision lives (below).
- **Verifier** — the scorer that decides pass/fail (or a graded score) for one run. It reads the model's output *and its trajectory* and returns a verdict with a reason. Designing a verifier that measures the intended behaviour — and can't be gamed — is the hard, central craft.

## Live vs. simulated — decide per tool

For every tool or dependency the instruction may invoke, decide in the environment whether it runs **live** or is **simulated** (a stub/fixture returning a canned result):

- **Simulate** a call that costs money per invocation, writes to production, sends a real message/email, is slow or flaky, or is non-deterministic in a way that would make the verifier's job impossible. A simulated tool returns a fixed, representative result so the eval is cheap, safe, and repeatable.
- **Run live** a read-only, free, deterministic call where the *real* behaviour is exactly what you're trying to verify (e.g. a local retrieval step whose quality is the point of the eval).

Record the decision on the eval unit (which tools are `live`, which are `simulated`, and the fixture each simulated one returns) so the dev agent wires the same environment when it runs.

## Verifiers that resist reward hacking

The failure mode to design against is **reward hacking** — the model satisfying the verifier *without doing the work*. LangChain's examples: claiming an action it never took, over-citing irrelevant sources to hit a "cites sources" check, exploiting answer material left in the environment, or satisfying a cheap proxy instead of the real goal. Guard against it:

- **Verify the trajectory, not just the final string.** If the criterion is "the agent updated the record," the verifier checks the record changed (or the tool was actually called), not that the model *said* it did.
- **Don't leave the answer reachable.** Keep expected outputs out of the environment the model can read.
- **Prefer behaviour-anchored checks over proxies.** "Grounded in the retrieved doc" beats "mentions the keyword"; a rubric or LLM-as-judge with explicit criteria beats a string match when output is open-ended.
- **Choose the verifier type to fit the criterion:** a **deterministic assertion** (state changed, tool called, schema valid) where the behaviour has a checkable effect; a **rubric / LLM-as-judge** (scored against named criteria) where the output is open-ended; a **structural check** (valid JSON, required fields, citation resolves) for format contracts. Combine them where a criterion has both an effect and a quality dimension.

An eval is only trustworthy once you've **inspected both sides** — the model's trajectory and the verifier's verdict — and confirmed the verifier passes for the right reason and fails for the right reason. That inspection is the dev agent's job at run time, and the TL's job to make possible by designing the verifier to be inspectable.

## The loop — design, run, improve, rerun

Eval engineering is iterative, exactly as the source describes: **build an eval → run it → inspect both sides → revise the task, environment, or verifier → rerun.** Where real production traces exist (a team on LangSmith), mining a genuine failure into an eval is the strongest seed; where they don't, design the eval from the acceptance criterion and the feature's workflow. Either way the first eval needn't be perfect — a reward-hacked pass or a false fail found on inspection is a signal to revise the eval, not to accept the result.

## The EVAL unit — schema and location

Eval units live in the `context/evals/` layer (a sibling of `frontend/backend/database`), authored by the TL and run by dev:

```text
context/evals/
  eval-index.md                       # one row per eval: id, feature, criterion, verifier type, live/sim, status
  <feature-slug>/
    <eval-slug>.md                    # EVAL-<AREA>-NN — one eval unit
```

Each `EVAL-<AREA>-NN` unit file carries frontmatter (`doc_type: eval`, `produced_by: tl`, the `FEAT-` it belongs to, `status`) and these sections:

- **Verifies** — the acceptance criterion (and `EP-/ENT-` units) this eval proves; cite the `INT-###`/`BR-###` behind the behaviour.
- **Instruction** — the task/input given to the system under test.
- **Environment** — fixtures and seeded data; a **tool table** marking each tool `live` or `simulated` with the simulated result.
- **Verifier** — the scoring method (deterministic / rubric / structural), the exact pass condition, and the **reward-hacking risks** it must resist.
- **Notes** — assumptions, open questions, and (if adopted) the Harbor export mapping.

`EVAL-<AREA>-NN` is append-only and follows the same area/sequence rule as the other `context/` IDs. Reuse before you create: a shared eval covering a criterion two features share gets one file with both features linked, not a duplicate.

## Optional Harbor / LangSmith export (hybrid)

The native form above is stack-agnostic and needs no external tooling. For teams that run LangChain's stack, an eval unit maps cleanly to a **Harbor task** — export on demand:

```text
evals/<task-id>/
  task.toml         # metadata + which tools are live/simulated
  instruction.md    # the Instruction section
  environment/      # a Dockerfile + fixtures realising the Environment
  tests/            # the Verifier as a runnable scorer
```

Trace mining is likewise optional: where LangSmith traces are available (`langsmith-cli`), seed evals from real production failures; otherwise design from the acceptance criteria. Never make the native flow depend on Docker, Harbor, or LangSmith — they are an *export target*, not a prerequisite.

## Roles — who does what

- **TL (`tl-feature-planning`)** — **designs** evals during planning: one per AI-driven acceptance criterion, with the live-vs-simulated calls and reward-hacking risks decided, linked into the graph, logged as `DEC-###`. It designs; it does not run.
- **Dev (`feature-delivery-loop` → `dev-validation`)** — **materializes and runs** the evals during the `TESTING` phase, **inspects both sides**, feeds pass/fail into the acceptance map, and iterates failures through the bounded repair loop. It runs; it does not redesign the eval's intent (a genuinely wrong eval is fed back to the TL).
- **QA (`qa-quality-gates`)** — owns the **harness** the evals run on and may expose an eval-runner gate in `quality-gates.md`. It owns neither the design nor the run.

## Principles

- **Evals are the evidence AI behaviour works** — the non-deterministic analogue of a passing test. No AI-bearing feature is done without them; no deterministic feature needs them.
- **Verify the trajectory, not the claim.** Design and check against what the model *did*, so a reward-hacked pass can't survive inspection.
- **Decide live-vs-simulated deliberately.** Simulate the costly, prod-writing, and non-deterministic; run live only what you're actually verifying.
- **Iterate the eval, not just the agent.** A false green or false red found on inspection revises the task/environment/verifier.
- **Native first, Harbor optional.** The method works with no external stack; LangSmith/Harbor are an export, never a dependency.
- **Design and run are separate hands.** TL authors intent; dev proves it; QA hosts it.
