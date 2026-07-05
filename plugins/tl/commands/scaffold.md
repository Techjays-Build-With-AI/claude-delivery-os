---
description: Scaffold the initial application repository from the project's confirmed architecture so a greenfield workspace has a real, green codebase to build features into. Reads the tech spec / architecture, the TL context graph, and shared-context; asks you (with a recommendation) for any required stack decision the architecture doesn't pin down; then creates the skeleton, tooling, coding-standards, and a green base build, logging each stack decision. Executes a confirmed stack — never silently guesses one — and does not implement product features.
argument-hint: "<spec-or-architecture doc | (blank = read context/project + shared-context)> [repo=<target path>]"
---

# /tl:scaffold

You stand up **project zero** — the first application repository — from the confirmed architecture. Delegate the work to the **`tl-agent`** subagent, which runs `tl-project-scaffold` in its own context.

## 1. Parse arguments

`$ARGUMENTS` may contain:
- An optional **architecture / tech-spec** source — a path to a spec document, or blank to read `context/project/architecture.md` / `technology-stack.md` and `shared-context/`.
- An optional **`repo=`** target — where the code should be created. If omitted, the skill asks and recommends a default.

If there is no architecture source anywhere (no spec, no `context/project/`, no useful `shared-context/`), tell the user the stack must be decided first — the scaffold will ask for the required choices with recommendations, but it can't run against a completely empty design.

## 2. Delegate

Invoke the **tl-agent** subagent with the source. Pass it this instruction:

> Scaffold the initial application repository using the `tl-project-scaffold` skill — follow `references/scaffold-guide.md`. Read the architecture / tech spec at `<source>` (or `context/project/` + `shared-context/`), the TL context graph (`context/frontend|backend|database` indexes), and `shared-context/project-profile.md`. Extract every stack choice the architecture **confirms**; for every required choice it leaves **open** (application type, repo layout, repo target, frontend framework, backend language/framework, database, package manager, test framework, …), **ask the user with a recommended option and a one-line rationale grounded in the project profile and context graph** — never guess a critical stack decision silently. Then scaffold: the idiomatic skeleton (prefer official generators), package-manager manifests, lint/format/type/test/build tooling, one trivial passing test, a README, and a `.gitignore`; write `context/project/{technology-stack.md, architecture.md, coding-standards.md}`; and append a `DEC-###` row to `shared-context/decision-log.md` for every stack decision. Run install → lint → type-check → test → build and confirm the **base build is green** — that is the exact readiness item the dev agent checks. Do **not** implement product features. Return the confirmed stack + structure, which decisions the spec supplied vs the user answered, the `DEC-###` logged, the repo location, and the green-base result.
>
> Architecture source: `<source>` · Repo target: `<repo or ask>`

## 3. Surface the result

Present the scaffold summary: the confirmed **stack and structure**, the decisions the spec supplied vs the ones the user answered, the `DEC-###` logged, the **repo location**, and the **green-base verification** (install/lint/type/test/build). Tell the user the workspace is now build-ready — they can run `/dev:build <feature>` (and `/dev:bootstrap` will now pass). If a critical stack decision is still unresolved, lead with the question the user needs to answer.
