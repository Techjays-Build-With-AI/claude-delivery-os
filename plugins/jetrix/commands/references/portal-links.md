# Linking into the Jetrix portal

<!-- rule: portal-deep-link phrases: "Solution Explorer and Mission Control are two different routes" | "never hand-build a path that is not in the table" -->

**Jetrix only.** Every printed portal link comes from this file. A link assembled from memory
lands the teammate on a real page that does not hold the thing you told them to click, which
costs more than printing no link at all.

## The base

`https://app.jetrix.ai/` for production, `https://staging-jetrix.web.app/` for staging — the
environment this machine's MCPs are registered against, the same pairing `/delivery-os:setup` §1
prints. A staging Solution does not exist to production, so the wrong base is a 404 with no hint why.

## Solution Explorer and Mission Control are two different routes

| Destination | Path | Takes |
|---|---|---|
| Solution Explorer — Basic Details, Team & Roles, **Connections**, Automation | `/solutions/explorer/solution/<encoded>` | **encoded** params |
| Mission Control — the task board, sprints, Knowledge Hub | `/solutions/mission-control/solution/<solutionId>` | the raw 24-char id |
| One task | `/task/<taskId>` | the task id |

The two differ in more than the segment: Explorer takes a **base64 blob**, Mission Control takes
the **raw id**. Pasting the id where the blob belongs decodes to `{ solutionId: "0" }` and the page
loads empty, which reads like a permissions problem rather than a bad link. **Never hand-build a
path that is not in the table.**

## Building the Explorer blob

The portal encodes its Explorer params as plain base64 of a JSON object (`utilities/urlEncoder.ts`):

```bash
ENC=$(printf '{"solutionId":"%s"}' "<solutionId>" | base64 | tr -d '\n')
echo "<portal-base>/solutions/explorer/solution/$ENC"
```

A 24-character hex id always encodes without `+` or `/`, so the result is path-safe as written —
no percent-encoding, and no `base64 -w0` needed outside GNU coreutils.

## The Connections tab is a click, not a link

The Solution page opens on **Basic Details** every time; its tab is component state, not a URL
param, so no link can land on Connections directly. Say both halves — the link, then the click:

```
  https://staging-jetrix.web.app/solutions/explorer/solution/eyJzb2x1dGlvbklkIjoiNmFmZGFiMGZjYWMyYmY5ZjQxYWFhMzUwIn0=
  → Connections tab → wire the apps → Save → Build map
```

Writing only "open the portal → Connections tab" leaves the teammate to find the Solution by hand
in a list that may hold a hundred of them.
