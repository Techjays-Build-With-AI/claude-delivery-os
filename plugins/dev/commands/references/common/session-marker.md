# Session marker — the file the guard hook reads

`/dev:build` and `/dev:commit` each declare an active session by writing a row
into `.jetrix/cache/session.json`. The `guard` hook (`plugins/dev/hooks/guard.js`)
reads that file before a tool call and refuses the operations the session
forbids.

**This file is the only contract between the commands and the hook.** Neither
side reads the other's internals.

---

## 1. Location

```
<workspace_root>/.jetrix/cache/session.json
```

Inside gitignored `.jetrix/`, beside `repolocation.json` and `sync-state.json`.
The hook walks up from the tool call's working directory (up to 4 levels) to
find it, because a product repo usually sits one level under the workspace.

Absent, empty or unparseable → **the hook allows everything**. That is the
normal state and it is not an error.

---

## 2. Schema

```json
{
  "sessions": [
    {
      "id": "build-2026-11-04-1032-a1b2",
      "kind": "build",
      "repo": "C:/Users/selva/plugin-test/Inhouse-server",
      "task": "Subtask-7",
      "started_at": "2026-11-04T10:32:11Z",
      "gates_passed": false,
      "deny": {
        "git_commit": true,
        "git_push": true,
        "write_paths": []
      }
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `id` | `<kind>-<YYYY-MM-DD-HHMM>-<4 hex>` — unique per run, printed in refusals |
| `kind` | `build` · `commit` |
| `repo` | **absolute path, forward slashes.** The hook matches a tool call to a session by checking whether the call's path sits inside this one |
| `task` | the task ref, for the refusal message only |
| `started_at` | ISO-8601 UTC. Staleness is computed from this and nothing else |
| `gates_passed` | `commit` only — set true at Stage 7.5 once every finding is closed or dispositioned |
| `deny.git_commit` | refuse `git commit` in this repo |
| `deny.git_push` | refuse `git push` in this repo **while `gates_passed` is false** |
| `deny.write_paths` | repo-relative path prefixes that may not be written — the fix loop fills this with the test paths |

Unknown fields are ignored, so a newer command can add one without breaking an
older hook.

---

## 3. Who writes what

| Moment | Writer | Change |
|---|---|---|
| `/dev:build` Stage 1 | build | append `{kind: "build", deny: {git_commit: true, git_push: true}}` |
| `/dev:commit` Stage 1 | commit | append `{kind: "commit", gates_passed: false, deny: {git_push: true}}` |
| Stage 6 fix loop entry | commit | set `deny.write_paths` to this unit's test paths |
| Stage 6 fix loop exit | commit | empty `deny.write_paths` |
| `/dev:commit` Stage 7.5, all findings closed | commit | `gates_passed: true` |
| `/dev:build` Stage 11 | build | **remove the row** |
| `/dev:commit` Stage 9 | commit | **remove the row** |
| **any halt, in either command** | that command | **remove its own row** |

**Removal on halt is not optional.** A halt that leaves its row behind blocks
the user's next manual commit until the row goes stale. That is the single
failure most likely to get the hooks uninstalled, so every `BLOCKED` exit path
removes its own row before returning.

Writes are atomic — temp file then rename — because two units of one feature
can write concurrently.

---

## 4. Staleness

A row is **stale** when `started_at` is more than **4 hours** old.

No PID checks and no heartbeats: both are fiddly across platforms and both fail
in ways worse than the problem they solve. A crashed session therefore stops
restricting anything after four hours, and three cheaper paths clear it sooner:

| | |
|---|---|
| The hook ignores it | and prints one line naming the stale session |
| A new run of the same `kind` on the same `repo` **reclaims** the row | and says so in its first line — never silently inherits |
| `--clear-locks` on either command | removes every row for that repo and prints what it removed |

---

## 5. What the hook does with it

See `plugins/dev/hooks/guard.js`. In short:

1. No marker, unparseable marker, or no row covering this repo → **allow**.
2. Row is stale → **allow**, with one line.
3. `DELIVERY_OS_HOOK_BYPASS=1` → **allow**, and append to `.jetrix/cache/bypass.log`.
4. Otherwise, if the row forbids this operation → **refuse**, naming what
   blocked it, why, and the command that proceeds.

**Fail open on everything that is not an explicit refusal.** A developer with no
Delivery OS session running must never notice these hooks exist.
