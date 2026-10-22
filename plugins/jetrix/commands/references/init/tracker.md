# /jetrix:init — resolving the tracker

Decides which project-management tool this workspace binds to and how to call it. Runs once at
bind; a refresh preserves everything it recorded.

## 2. Resolve the tracker

**Default is `jetrix`.** Read it in this order — `project.json`'s `tracker.provider` on a re-run, then `--tracker=`, then the default. Never ask when one of those answers.

Known trackers:

| `--tracker=` | MCP | Add it with |
|---|---|---|
| `jetrix` | `project-mcp` · `scope-mcp` · `task-mcp` | already registered by `/delivery-os:setup` |
| `jira` | `atlassian` | `claude mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp` |
| `clickup` | `clickup` | `claude mcp add --transport http clickup <url>` |
| `azure` | `azure` | `claude mcp add --transport http azure <url>` |
| anything else | whatever it was registered as | the user adds it; §6 finds it |

### 2a. On `jetrix`, make no check

`/delivery-os:setup` registered those three. If a call fails because the tool isn't there, say `Run /delivery-os:setup first — it registers all three.` and stop. Do not pre-check.

**Never run `claude mcp list`** for any check here — it health-checks every registered server over the network, so on a machine with many connectors the command appears to hang before doing any work.

### 2b. On any other tracker, find its MCP first

The user installed it, so verify it before resolving anything. Resolve with `ToolSearch` — MCP tools may be deferred, so an empty tool list is not an answer:

- `ToolSearch` the tracker name (`jira atlassian issue`, `clickup task`, …). Tools returned → registered; record the server name as `tracker.mcp`, since it is whatever the user typed at `claude mcp add` (`atlassian`, `claude_ai_Atlassian_Rovo`, …) and we never assume it.
- Nothing returned → print the `claude mcp add` line from the table (or, for an unknown tracker, `claude mcp add --transport http <name> <its-mcp-url>`), say `Nothing was written.`, and stop.

### 2c. Map the tracker's tools once

Read the returned schemas and propose the mapping. Ten keys, `null` where the tracker cannot do it:

```
browse[] · resolve_project · resolve_container · create_container
create_issue · update_issue · read_issue · child_issues
comments · attachments · set_status · put_document
```

**`resolve_container` and `create_container` are what §12 needs.** On ClickUp they are `clickup_get_lists` and `clickup_create_list`; on Jira, epic search and epic create; where a tracker files issues straight into the project, both are `null` and §12 records `container_kind: none`. A tracker that can list containers but not create them gets `create_container: null` — §12 then offers only the existing ones and says where to make a new one.

**`browse` is an ordered list, because “project” is not one level in every tool.** Jetrix has Solutions; Jira has Projects; ClickUp has Workspace → Space → Folder → List, and tasks live in the List. Record the tools that walk from the root down to whatever holds tasks — a flat tracker is simply a one-element list:

```
jetrix    browse: [project_list_solutions]
jira      browse: [jira_get_visible_projects]
clickup   browse: [clickup_get_workspaces, clickup_get_spaces,
                   clickup_get_folders, clickup_get_lists]
```

Also propose a `status_map` from the statuses the schemas expose, with a key for **each of the seven shared `status` values** in `delivery-os-conventions` §5 — `todo`, `readyForDev`, `agentExecuting`, `inProgress`, `devReview`, `blocked`, `done`. Never a key for `phase`; it is local and never pushed. Several keys usually collapse onto one of the tracker’s own statuses (`agentExecuting` and `inProgress` are typically both "in progress") — propose that collapse rather than leaving a value unmapped, because an unmapped value means `/jetrix:push` has nothing to send for a task in the middle of a build. **Always show the status map for confirmation** — it is the one part discovery guesses badly, and it is used in **both** directions: push maps ours → theirs, pull maps theirs → ours by inverting it (`delivery-os-conventions` §5). Confirming a wrong value breaks the pull as well as the push. Store both in `project.json` §16; a re-run never asks again.

### 2d. Capabilities

Set from the tracker, and branch on these — never on the provider name:

| | `jetrix` | every other tracker |
|---|---|---|
| `apps` | `true` — repos come from the Solution | `false` — repo path + dev branch asked in §13 |
| `tabs` | `7` — one file per tab | `1` — the six BA files plus Implementation as `##` sections in one body |
| `documents` | `scope-mcp` — publishes `scope.html` to Dashboard → Reports | `none` — `scope.html` is still rendered, it just stays local |
