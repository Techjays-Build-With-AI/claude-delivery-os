---
description: Greenfield entry point — ensure a usable product repository exists before feature development begins. Detects whether the workspace has a real, green codebase; if not (project-zero), it delegates to the TL project-scaffold (which reads the architecture and asks you, with a recommendation, for any missing stack decision) to stand one up, then verifies a green base build. Run this once per project before /dev:build when starting from scratch. Never guesses the stack itself and never implements features.
argument-hint: "<spec-or-architecture doc | (blank)> [repo=<target path>]"
---

# /dev:bootstrap

You make a **greenfield** workspace build-ready. The dev loop can't implement into a project that has no repository; this is the one-time step that ensures one exists (with a green base build) before `/dev:build` runs. Delegate the work to the **`dev-agent`** subagent.

## 1. Parse arguments

`$ARGUMENTS` may contain an optional **architecture / tech-spec** source and an optional **`repo=`** target for the scaffolded code. Both are optional — the scaffold reads `context/project/` + `shared-context/` if no spec is given, and asks (with a recommendation) for a repo target if none is passed.

## 2. Delegate

Invoke the **dev-agent** subagent. Pass it this instruction:

> Bootstrap this workspace for development. First **detect the repository state**: is there a usable product repo (an app skeleton, package-manager files, runnable lint/test/build, a green base build)? 
> - **Brownfield (repo already usable)** — nothing to scaffold. Report the repo location and that it's build-ready, and tell the user to run `/dev:build <feature>`. Stop.
> - **Project-zero (no repo / no usable base)** — scaffold one by delegating to the TL `tl-project-scaffold` skill (the same work `/tl:scaffold` does): read the architecture / `context/project/` + `shared-context/` and the context graph, extract the confirmed stack, **ask the user with a recommendation for any required stack decision the architecture doesn't pin down** (never guess a critical one), scaffold the skeleton + lint/format/type/test/build tooling + `.gitignore` + README, write `context/project/{technology-stack.md, architecture.md, coding-standards.md}`, log each stack decision as `DEC-###`, and run `install → lint → type-check → test → build` to confirm a **green base**. If the TL scaffold skill/plugin isn't available, stop and tell the user to run `/tl:scaffold` (or install the tl plugin) — do not scaffold with a guessed stack.
> - **Re-verify** the base build is green after scaffolding.
>
> Architecture source: `<source or context/project>` · Repo target: `<repo or ask>`
>
> Return the repository state found, the confirmed stack + structure (if scaffolded), which decisions the spec supplied vs the user answered, the `DEC-###` logged, the repo location, and the green-base result. Do **not** implement any product features — that's `/dev:build`.

## 3. Surface the result

Present the outcome: whether the repo already existed or was scaffolded, the confirmed **stack and structure**, spec-supplied vs user-answered decisions, `DEC-###` logged, the **repo location**, and the **green-base verification**. Close with the next action — the workspace is now build-ready, so run `/dev:build <feature>` (or leave it blank to take the next feature at `READY_FOR_DEV`). If a critical stack decision is still open, lead with the question the user needs to answer.
