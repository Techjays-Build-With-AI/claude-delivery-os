# Which git host this repo is on, and what that changes

<!-- rule: git-host-resolution phrases: "the remote URL is the authority, never the config" | "A host that does not resolve halts" -->

Every command that raises or edits a pull request needs three facts: the **host**, the
**owner/workspace**, and the **repo/slug**. All three are in one place — the target repo's
`origin` remote. **The remote URL is the authority, never the config**: `project.json` is
gitignored and goes stale, a repo may be cloned after `/jetrix:init` ran, and a remote can be
repointed. The URL is what `git push` just used.

**The host is per repo, not per workspace.** A frontend on GitHub and a backend on Bitbucket is
an ordinary arrangement, so resolve against the repo you are about to open a PR in — never once
for the run.

## The resolver

```bash
resolve_git_host() {           # $1 = absolute path to the target repo
  ORIGIN=$(git -C "$1" config --get remote.origin.url)
  # Strip scheme/user and the trailing .git, then split host / owner / repo.
  STRIPPED=$(printf '%s' "$ORIGIN" | sed -E 's#^(ssh://)?(git@)?##; s#^https?://([^@]+@)?##; s#\.git$##; s#:#/#')
  HOST=$(printf '%s' "$STRIPPED" | cut -d/ -f1)
  OWNER=$(printf '%s' "$STRIPPED" | cut -d/ -f2)
  REPO=$(printf '%s' "$STRIPPED" | cut -d/ -f3)
  case "$HOST" in
    github.com)    PROVIDER=github ;;
    bitbucket.org) PROVIDER=bitbucket ;;
    *)             PROVIDER=$(read apps[].git_host for this repo from project.json) ;;
  esac
}
```

**Check `OWNER` and `REPO` are both non-empty before using them.** `sed` returns its input
unchanged when the pattern does not match, so a host-specific regex silently yields the whole URL
as the "owner" rather than failing — the defect this file replaces turned
`git@bitbucket.org:acme/api.git` into `OWNER=git@bitbucket.org:acme`, posted it to
`api.github.com`, and reported a GitHub 404 for a repository that was never on GitHub.

**A host that does not resolve halts** with `blocker: unknown-git-host`, naming the host and the
remote. Self-hosted installs — Bitbucket Data Center, GitHub Enterprise, GitLab — sit on company
domains that say nothing, so they are declared once in `project.json` `apps[].git_host` and read
from there. Guessing from a domain name is how a PR gets opened against the wrong system.

## What differs per provider

Everything before the PR is plain `git` and identical on both. Only the PR call changes.

| | `github` | `bitbucket` |
|---|---|---|
| API base | `https://api.github.com` | `https://api.bitbucket.org/2.0` |
| Create PR | `POST /repos/$OWNER/$REPO/pulls` | `POST /repositories/$OWNER/$REPO/pullrequests` |
| Body | `{title, body, head, base}` | `{title, description, source:{branch:{name}}, destination:{branch:{name}}}` |
| PR URL in the answer | `.html_url` | `.links.html.href` |
| List open PRs for a branch | `GET /repos/$O/$R/pulls?head=$O:<branch>&base=<base>&state=open` | `GET /repositories/$O/$R/pullrequests?q=source.branch.name="<branch>"&state=OPEN` |
| Update a PR body | `PATCH /repos/$O/$R/pulls/<n>` with `{body}` | `PUT /repositories/$O/$R/pullrequests/<n>` with `{title, description}` |
| Comment | `POST /repos/$O/$R/issues/<n>/comments` `{body}` | `POST /repositories/$O/$R/pullrequests/<n>/comments` `{content:{raw}}` |
| Auth header | `Authorization: Bearer <token>` | `Authorization: Bearer <token>`, or Basic for an app password |
| Extra headers | `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28` | `Content-Type: application/json` |
| Official CLI | `gh` | **none** |
| Compare URL | `https://github.com/$O/$R/compare/<base>...<head>?expand=1` | `https://bitbucket.org/$O/$R/pull-requests/new?source=<head>&dest=<base>` |

**Bitbucket's `title` is required on `PUT`** — sending only `description` clears the title. Send both.

## What this does to the ladder

The ladder in `stage-8-9-push-pr.md` §9c is unchanged in shape; only its membership differs.

| Step | `github` | `bitbucket` |
|---|---|---|
| 1 — official CLI | `gh pr create` | **absent** — no CLI exists; go straight to step 2 |
| 2 — token from the credential store | `host=github.com` | `host=bitbucket.org` |
| 3 — token from the CLI's own config | `~/.config/gh/hosts.yml` | **absent** |
| 4 — web compare URL | as above | as above |

So Bitbucket runs a **two-step ladder plus the web fallback**, and `9c.i` must never offer to
install `gh` on a non-GitHub repo — it would install a tool that cannot talk to that host.

Step 2 carries both: the OS credential helper caches whatever host you authenticated against for
`git push`, so a Bitbucket app password or access token is already there for the taking. That is
why no new auth flow, OAuth consumer or app install is needed on either host.

## What is not here

Mission Control's repo integration is a GitHub App (`installation_id`) and has no Bitbucket
equivalent. Nothing in this plugin reads it — `/jetrix:init` does not persist it — so a Bitbucket
repo runs the whole delivery loop; only MC's own Integration tab stays GitHub-only.
