# Project structure — where a file goes

`shared-context/coding-standards.md § <repo>` §2 (Folder structure & file
placement) declares where each kind of file lives in one repository. This file
says **how to decide what §2 should contain**, and **how to honour it when
writing a new file**.

Two readers:

| Reader | When |
|---|---|
| `tl-project-scaffold` → `references/scaffold-guide.md` §3.1 | creating a repo's folders |
| `dev-stack-adaptive-implementation` → Rule 15 | placing a new file in an existing repo |

---

## 1. Structure is a decision, not an observation

<!-- rule: file-placement-source scope: plugins phrases: "A confirmed §2 outranks what the repo does" -->

Most of §1–12 can be inferred from code that already exists — naming, error
handling and test style leave evidence in every file. **§2 usually cannot.** A
generator leaves a hello-world tree, and a hello-world tree is evidence of
nothing: it is what the generator shipped, not what anyone chose.

So §2 is the gated section most likely to need `engineering-standards.md` §3
step 5 — *ask the developer* — and the one most often filled in with `inferred`
instead.

A §2 left at `inferred` is not policy. Rule 13 skips it, placement falls back to
whatever the generator left behind, and the first screen becomes the structure
by accident — after which every later file matches the accident.

## 2. First ask: does the framework already decide?

Where the framework ships a documented layout, §2 is **transcription, not a
decision**. Take the layout from the framework's own project-structure page,
pin it to the major version being installed, and write it as `confirmed` with
`source.type: framework-docs`.

**Apply the test, do not look for your stack in a list.** The table below is
examples; the stacks in it are the ones seen so far, not the ones that are
allowed. Any framework -- Svelte, Remix, Angular, Astro, Phoenix, .NET, Ktor,
Axum, Flutter, one released next month -- resolves by answering two questions
about the framework in front of you:

1. **Do its own docs have a project-structure / directory-structure page that
   names folders?** Yes -> transcription. Transcribe that page, version-pinned.
2. **Does its official generator or CLI produce more than an entry file and
   config?** Yes -> transcription. Transcribe what it generates.

Neither -> **a decision**. Go to §3, choose an axis, ask the developer, and
record it as `confirmed` with a `DEC-###`.

Both questions are answered by looking, not by knowing the framework. An
unfamiliar stack is not a blocker; it is two `WebFetch` calls on the ladder in
`scaffold-guide.md` §3.1.

| Stack | Layout dictated by | §2 is |
|---|---|---|
| Django | the framework — apps, `models.py` / `views.py` / `urls.py` | transcription |
| Rails | the framework — MVC | transcription |
| Laravel | the framework | transcription |
| Next.js (app router) | the framework — `app/` routing | transcription |
| NestJS | the framework — modules | transcription |
| Spring Boot | convention — packages by layer or by feature | a small choice |
| Express / Fastify | **nothing** — the generator gives you one file | **a decision** |
| React SPA (Vite, CRA) | **nothing** — `src/App.tsx`, and it stops | **a decision** |
| Vue SPA (Vite) | partial — SFC conventions, no app layout | **a decision** |
| FastAPI | **nothing** beyond `main.py` | **a decision** |
| Go service | community layouts, genuinely contested | **a decision** |

**React is both the common case and the hardest one.** It ships no opinion, so a
React repo either inherits a structure somebody chose or drifts into the
generator's default. Never record that default as `inferred` evidence.

## 3. When it is a decision: the two axes

| | Type-first | Feature-first |
|---|---|---|
| Groups by | what a file **is** | what a file is **for** |
| Shape | `components/` `pages/` `hooks/` `api/` | `features/<slug>/` + shared `components/` `hooks/` `lib/` |
| Good for | few features, one team, short-lived | anything expected to grow |
| Fails as | one feature's files scatter; `components/` becomes a dumping ground | features too small to deserve a folder |

The crossover is roughly **3 features or 15 components**. Past it, type-first
costs more to navigate than it saves.

**Default to feature-first for anything expected to grow.** Record the choice as
a `DEC-###` and write it into §2 as `confirmed`.

**Per-component subfolders are a separate question.** `Button/Button.tsx` earns
its folder at 4+ files per component (source, styles, test, types, stories);
below that it is overhead. Flat co-location inside a feature folder is the usual
answer, and fixing the grouping axis usually removes the pressure for it.

## 4. Default shapes where a choice is required

Boring and conventional beats clever. A developer joining the project should
recognise the tree.

**A stack not shown here has no default shape, and inventing one is the failure
this file exists to prevent.** Derive it from the §3.1 ladder -- framework docs,
then official starter, then one widely-adopted community reference for the
pattern -- and once it is `confirmed`, add the shape here so the next repo on
that stack starts from a decision instead of repeating the research.

**React SPA — feature-first**

```
src/
  features/<slug>/   components, hooks and api.ts for one feature
  components/        cross-feature primitives only
  hooks/             cross-feature hooks
  lib/               apiClient, framework-free helpers
  pages/             one route entry per screen (thin; delegates to features/)
```

**Express / Fastify — layered**

```
src/
  server.ts          process entry only
  app.ts             createApp(deps)
  config/            env loading, the only reader of process.env
  routes/<resource>.ts    parse, validate, call service, shape response
  services/<resource>.ts  business logic, no framework types
  models/<Entity>.ts      schema and model
  middleware/
```

**FastAPI**

```
app/
  main.py            app factory only
  api/routes/<resource>.py
  services/<resource>.py
  models/            ORM models
  schemas/           pydantic request/response
  core/config.py
```

**Go service**

```
cmd/<binary>/main.go
internal/<domain>/   handler.go, service.go, repository.go
pkg/                 only what is genuinely importable by other modules
```

## 5. Placing a file in a repo that already exists

**Write the new file to §2; leave the existing files where they are.** Structure
drift is repaid by moving files deliberately, never as a side effect of an
unrelated feature.

| §2 status | Where the new file goes |
|---|---|
| `confirmed` | **A confirmed §2 outranks what the repo does.** Create the folder if it is missing |
| `inferred`, absent, or silent on this kind of file | match the repo, and report the mismatch in the run summary |

**Report, never halt.** Placement is a judgement call with real edge cases, and
a halt on a path guess costs more than the misplacement it prevents. Name the
file, the path §2 implies, and the path chosen.

A `confirmed` §2 that names a folder the repo does not have yet is not a
conflict — it is the first file of that folder.
