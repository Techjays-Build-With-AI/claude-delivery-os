---
description: Generate a Techjays client proposal as a single-file, print-to-PDF HTML deck built to the Techjays proposal standard and style guide. Pass the client name and their domain (used to pull their logo and brand color); the doc agent auto-drafts content from the BA scope when a Delivery OS workspace exists, brands the deck to the client, and writes a timestamped proposal-<client>-<timestamp>.html to doc-output/. Add free-text custom rules to tailor it.
argument-hint: "client=\"<Client Name>\" domain=<client.com> [title=\"<engagement title>\"] [\"<extra requirements / custom rules>\"]"
---

# /doc:proposal

You are the entry point for generating a **Techjays client proposal**. Parse the arguments and **delegate the actual work to the `doc-agent` subagent**, which runs in its own context and does the content sourcing and deck build.

## 1. Parse arguments

`$ARGUMENTS` may contain, in any order:
- **`client="<Client Name>"`** — the client's name (required). If omitted, ask for it and stop.
- **`domain=<client.com>`** — the client's website domain (strongly recommended). Used to pull the client's **logo** (`https://logo.clearbit.com/<domain>`, or the site's own logo) and to sample their **brand accent color**. If omitted, ask for it (or accept that the deck will use a text-wordmark placeholder and the Techjays accent).
- **`title="<engagement title>"`** — the engagement's value-prop headline for the title deck. Optional; the agent can draft one from the scope.
- **`out=<prefix>`** — optional output prefix override (default `doc-output/proposal-<client>`). A run timestamp is always appended.
- **Free-text custom rules** — anything else in quotes or trailing prose is treated as **additional requirements**: extra sections, tone, specific pricing, "use the lean 7-section form", "add a security & compliance section", "emphasize the migration story", brand-color overrides, etc. Pass these through verbatim; the agent layers them on top of the standard.

If a Delivery OS workspace exists (`ba-output/scope.md` present), tell the agent to auto-draft from it. If not, the agent uses what's provided/attached and marks any missing client numbers as placeholders.

## 2. Delegate

Invoke the **doc-agent** subagent with the parsed inputs. Pass it this instruction:

> Generate a Techjays client proposal using the `doc-proposal` skill. Client: `<client>`; domain: `<domain>`; engagement title: `<title or "draft from scope">`. Custom rules (verbatim, or "none"): `<custom rules>`.
>
> Build a **single-file, print-to-PDF HTML deck** from `assets/proposal-template.html`, following `references/proposal-standard.md` (governing content flow and voice rules) and `references/proposal-style-guide.md` (design system and components). When a Delivery OS workspace exists, auto-draft the problem statement, solution workflow, and value numbers from `ba-output/scope.md` and `shared-context/` (use the client's real numbers; never fabricate metrics — mark unknowns as placeholders). Brand the deck to the client: set the client-accent from their site, and place their logo on the title brand pair and closing via their domain (reference the online logo, and base64-embed it for offline portability where possible; fall back to favicon, then a text wordmark). Enforce the non-negotiable voice rules (no em-dashes, no contrastive negation, address the client by name, client's real numbers on the Value page) and the print rules (breakpoints scoped to `@media screen`, `@page` rules intact, Print/Save-PDF button present) so the deck exports to PDF cleanly. Layer the custom rules on top of the standard; flag any that would break a non-negotiable rule instead of silently applying it. Read a run timestamp (`YYYY-MM-DD-HHMMSS`) and write `doc-output/proposal-<client>-<timestamp>.html` (create `doc-output/` if absent). Return a short summary, the list of any placeholders still needing the user's numbers, and the file link.

## 3. Surface the result

When the agent returns, present its **summary**: what was built, which content came from the BA scope vs. supplied, and any placeholders the user still needs to fill (missing client metrics, the official logo asset, final pricing). Link to the generated `proposal-<client>-<timestamp>.html` and tell the user to open it in Chrome/Edge and choose **Print → Save as PDF** (with "Background graphics" enabled) to export. Keep it tight.
