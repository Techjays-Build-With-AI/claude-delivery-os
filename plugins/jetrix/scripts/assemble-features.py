"""Assemble `feature_upsert_bundle` payloads from `features/*/`.

Invoked by `/jetrix:push feature` (see plugins/jetrix/commands/references/push/feature.md)
before the MCP call. Replaces the "for each folder, Read every file, assemble
in Claude context" iteration — walks the folders, reads files, applies the
strip / rewrite transforms, groups features by resolved `list_name`, and emits
one JSON blob Claude passes to N feature_upsert_bundle calls (one per group).

Enforces every existing contract:
  - halt on missing feature.md / acceptance-criteria.md (halts list surfaced
    in the JSON output; Claude reports and stops the push)
  - `title` fallback (frontmatter.title → body H1 → slug)
  - description = feature.md Objective + '\n\n## Workflow\n\n' + workflow.md
    body + '\n\n' + feature.md In-Scope + Out-of-Scope
  - assumptions = dependencies.md + '\n\n**Open questions**\n\n' + open-questions.md
    (inline '— none.' form when open-questions.md starts with it)
  - strip_file_paths + rewrite_feat_to_task on the six body wire-fields
  - blocker-aware status (open-questions Impact starts with 'Blocks',
    dependencies flagged unavailable/blocked/TBD → 'blocked'; else 'todo')
  - list_name fallback chain: frontmatter.list_name → mapped_scope-with-§-stripped
    → initiative → solution_slug (surfaced back to Claude as `solution_slug_fallback`)
  - skip-unchanged via folder hash vs sync-state.contentHash

Usage:
    python assemble-features.py \
        --project-root .jetrix/<slug> \
        --sync-state   .jetrix/cache/sync-state.json \
        --solution-slug PluginTest \
        --output       /tmp/features-assembled.json \
        [--slug user-auth ...]     # optional; default = every folder

The output JSON shape:
{
  "solution_slug":               "PluginTest",
  "groups":                      [{"list_name": "...", "features": [<payload>...]}, ...],
  "skipped_unchanged":           [<slug>, ...],
  "halts":                       [{"slug": "...", "reason": "..."}, ...],
  "solution_slug_fallback":      [<slug>, ...],       # features that fell all the way to solution_slug
  "solution_slug_fallback_slugs": [<slug>, ...]        # duplicate for symmetry with §3a UX
}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Any


# ---------------------------------------------------------------------------
# Transform: strip_file_paths — mirrors push/feature.md §3 verbatim.
# ---------------------------------------------------------------------------
def strip_file_paths(text: str) -> str:
    if not text:
        return text
    # File-reference prose  ("… — see foo.md.", "(see foo.md)", "see `foo.md`")
    text = re.sub(r'\s+—\s+see\s+[a-zA-Z0-9_-]+\.md\.?', '', text)
    text = re.sub(r'\s*\(see\s+[a-zA-Z0-9_-]+\.md\)\.?', '', text)
    text = re.sub(r'see\s+`[a-zA-Z0-9_-]+\.md`', '', text)

    # Bracketed provenance / citation callouts.
    text = re.sub(
        r'\[(?:code|SIMULATED|TL|QA|BA|DEBUG|NOTE|REVIEW|TODO|FIXME|INTERNAL)[ ›>][^\]]+\]',
        '', text,
    )

    # BA-internal ID refs (SRC/EX/DEC) — bracketed + bare.
    text = re.sub(r'\[(?:SRC|EX|DEC)-\d+(?:[ ›>][^\]]*)?\]', '', text)
    text = re.sub(r'\b(?:SRC|EX|DEC)-\d+\b', '', text)

    # Mid-content analysis-tag citations inside a larger bracket.
    text = re.sub(
        r'\b(?:SIMULATED|TL|QA|BA|DEBUG|NOTE|REVIEW|TODO|FIXME|INTERNAL|code)\s*[›>]\s*[^,\]\n]+',
        '', text,
    )

    # Bare code-ext filenames in prose.
    text = re.sub(
        r'\b[a-zA-Z][a-zA-Z0-9_-]*\.(md|js|ts|jsx|tsx|py|go|java|rb|rs|kt|swift|json|yaml|yml)\b\.?',
        '', text,
    )

    # Backticked code paths with "/".
    text = re.sub(
        r'`(src|controllers|models|routes|components|pages|endpoints|entities|api|utils|services|app|lib)/[^`]+`',
        '', text,
    )

    # Backticked bare filenames with code extensions.
    text = re.sub(
        r'`[a-zA-Z0-9_-]+\.(md|js|ts|jsx|tsx|py|go|java|rb|rs|kt|swift)`',
        '', text,
    )

    # --- Cleanup: debris left after strips ---
    text = re.sub(r'`{2,4}(?=\s|[.,;:!?)\]}]|$)', '', text)
    text = re.sub(r'(?<=[\s\(\[\{—])`{2,4}', '', text)
    text = re.sub(r'`\s+`', '', text)
    text = re.sub(r'``', '', text)

    text = re.sub(r'\(\s*[,;:]?\s*\)', '', text)
    text = re.sub(r'\[\s*[,;:]?\s*\]', '', text)
    text = re.sub(r'\{\s*[,;:]?\s*\}', '', text)

    text = re.sub(r'\(\s*,\s*', '(', text)
    text = re.sub(r'\s*,\s*\)', ')', text)
    text = re.sub(r'\[\s*,\s*', '[', text)
    text = re.sub(r'\s*,\s*\]', ']', text)

    text = re.sub(r'(—|--)\s*,\s*', r'\1 ', text)
    text = re.sub(r',\s*(—|--)\s*', r' \1 ', text)

    text = re.sub(r'\s+and\s*\.', '.', text)
    text = re.sub(r'\s+and\s*,', ',', text)
    text = re.sub(r'\s+and\s*(?=[)\]])', '', text)
    text = re.sub(r'—\s+and\s*(?=[.,;:!?])', '', text)

    text = re.sub(r'\bsee\s*,\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsee\s*(?=[)\]])', '', text, flags=re.IGNORECASE)
    text = re.sub(r'—\s*see\s*(?=[.,;:!?)\]]|$)', '', text, flags=re.IGNORECASE)

    text = re.sub(r',\s*,+', ',', text)
    text = re.sub(r';\s*;+', ';', text)
    text = re.sub(r'\s+([\.,;:!?])', r'\1', text)
    text = re.sub(r'([\.,;:!?])\s+([\.,;:!?])', r'\1\2', text)
    text = re.sub(r'(—|--)\s*\.', '.', text)

    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    text = re.sub(r'\|\s*#\s*\|\s*Scenario\s*\|', r'| No. | Scenario |', text)

    return text.strip()


def rewrite_feat_to_task(text: str, task_num_by_feat: dict[str, int]) -> str:
    if not text:
        return text
    def replace(m: re.Match) -> str:
        feat_id = m.group(0)
        num = task_num_by_feat.get(feat_id)
        return f'TASK-{num}' if num else feat_id
    return re.sub(r'\bFEAT-[A-Z]+-\d+\b', replace, text)


# ---------------------------------------------------------------------------
# Frontmatter + section extraction.
# ---------------------------------------------------------------------------
_FM_FENCE = re.compile(r'^---\r?\n', re.MULTILINE)


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_after_fm). YAML parsed with a minimal
    subset — enough for the fields this pipeline uses (scalars + lists)."""
    if not text.startswith('---'):
        return {}, text
    # Find closing fence.
    m = re.search(r'^---\s*$', text[3:], re.MULTILINE)
    if not m:
        return {}, text
    end = 3 + m.start()
    fm_block = text[3:end]
    body = text[end + len('---'):]
    body = body.lstrip('\r\n')

    fm: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw in fm_block.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith('#'):
            continue
        # List continuation "- value"
        if line.lstrip().startswith('- ') and current_list_key is not None:
            fm[current_list_key].append(_parse_scalar(line.lstrip()[2:]))
            continue
        # key: value
        mm = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$', line)
        if not mm:
            current_list_key = None
            continue
        key, raw_val = mm.group(1), mm.group(2).strip()
        if raw_val == '':
            current_list_key = key
            fm[key] = []
        else:
            current_list_key = None
            if raw_val.startswith('[') and raw_val.endswith(']'):
                inner = raw_val[1:-1].strip()
                if not inner:
                    fm[key] = []
                else:
                    fm[key] = [_parse_scalar(s.strip()) for s in inner.split(',')]
            else:
                fm[key] = _parse_scalar(raw_val)
    return fm, body


def _parse_scalar(s: str):
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if s.lower() in ('true', 'false'):
        return s.lower() == 'true'
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def strip_h1(body: str) -> tuple[str | None, str]:
    """If body's first non-empty line is `# ...`, return (heading, body_after)."""
    lines = body.split('\n')
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx >= len(lines) or not lines[idx].startswith('# '):
        return None, body
    heading = lines[idx][2:].strip()
    return heading, '\n'.join(lines[idx + 1:]).lstrip('\n')


def read_body(path: pathlib.Path) -> str:
    """Read a .md file, strip frontmatter, strip H1. Return body only."""
    if not path.exists():
        return ""
    _, body = split_frontmatter(path.read_text(encoding='utf-8'))
    _, body = strip_h1(body)
    return body.strip()


def extract_section(body: str, header: str, next_headers: list[str]) -> str:
    """Return content between `## <header>` and the next matching `## <next>`
    header (or end of body). Empty if header not present."""
    start_pat = re.compile(rf'^##\s+{re.escape(header)}\s*$', re.MULTILINE)
    m = start_pat.search(body)
    if not m:
        return ""
    start = m.end()
    end = len(body)
    for nh in next_headers:
        p = re.compile(rf'^##\s+{re.escape(nh)}\s*$', re.MULTILINE)
        mm = p.search(body, pos=start)
        if mm and mm.start() < end:
            end = mm.start()
    return body[start:end].strip()


# ---------------------------------------------------------------------------
# Feature assembly.
# ---------------------------------------------------------------------------
REQUIRED_FILES = ("feature.md", "acceptance-criteria.md")
TAB_FIELDS = ("description", "business_rules", "acceptance_criteria",
              "nfrs", "test_scenarios", "assumptions")


def _folder_hash(dir_path: pathlib.Path) -> str:
    h = hashlib.sha256()
    for f in sorted(dir_path.glob("*.md")):
        h.update(f.read_bytes())
    return h.hexdigest()


def _resolve_list_name(fm: dict, solution_slug: str) -> tuple[str, bool]:
    """Return (list_name, is_solution_slug_fallback)."""
    ln = (fm.get("list_name") or "").strip()
    if ln:
        return ln, False
    ms = (fm.get("mapped_scope") or "").strip()
    if ms.startswith("§"):
        # Strip everything up to and including first whitespace.
        parts = ms.split(None, 1)
        if len(parts) == 2:
            return parts[1].strip(), False
    if ms:
        return ms, False
    init = (fm.get("initiative") or "").strip()
    if init:
        return init, False
    return solution_slug, True


def _detect_blocked(feat_dir: pathlib.Path) -> bool:
    oq_path = feat_dir / "open-questions.md"
    if oq_path.exists():
        for line in oq_path.read_text(encoding='utf-8').splitlines():
            # Look for a table row where Status=Open AND Impact starts with "Blocks"
            cells = [c.strip() for c in line.split("|")]
            if len(cells) < 4:
                continue
            # Heuristic: any cell equal to "Open" AND any cell whose lowercase starts with "blocks"
            has_open = any(c.lower() == "open" for c in cells)
            has_blocks = any(c.lower().startswith("blocks") for c in cells)
            if has_open and has_blocks:
                return True
    dep_path = feat_dir / "dependencies.md"
    if dep_path.exists():
        body = dep_path.read_text(encoding='utf-8').lower()
        for token in ("unavailable", "not available", "blocked", "tbd"):
            if token in body:
                return True
    return False


def assemble_feature(feat_dir: pathlib.Path, fm: dict, task_num_by_feat: dict[str, int]) -> dict:
    slug = fm.get("slug") or feat_dir.name

    # --- feature.md body: split into Objective / In Scope / Out of Scope. ---
    feature_md = feat_dir / "feature.md"
    fm_dict, feat_body = split_frontmatter(feature_md.read_text(encoding='utf-8'))
    _, feat_body = strip_h1(feat_body)
    objective   = extract_section(feat_body, "Objective",    ["In Scope", "Out of Scope"])
    in_scope    = extract_section(feat_body, "In Scope",     ["Out of Scope"])
    out_scope   = extract_section(feat_body, "Out of Scope", [])
    workflow_body = read_body(feat_dir / "workflow.md")

    # description = Objective + Workflow + In Scope + Out of Scope
    desc_parts = []
    if objective: desc_parts.append(objective)
    if workflow_body:
        desc_parts.append("## Workflow\n\n" + workflow_body)
    scope_block = ""
    if in_scope:  scope_block += "## In Scope\n\n" + in_scope + "\n"
    if out_scope: scope_block += "\n## Out of Scope\n\n" + out_scope
    if scope_block:
        desc_parts.append(scope_block.strip())
    if not (in_scope or out_scope):
        # Legacy fallback: no scope headings → old body + workflow order.
        desc_parts = []
        if feat_body.strip(): desc_parts.append(feat_body.strip())
        if workflow_body:     desc_parts.append("## Workflow\n\n" + workflow_body)
    description = "\n\n".join(desc_parts).strip()

    business_rules      = read_body(feat_dir / "business-rules.md")
    acceptance_criteria = read_body(feat_dir / "acceptance-criteria.md")
    nfrs                = read_body(feat_dir / "nfrs.md")
    test_scenarios      = read_body(feat_dir / "test-scenarios.md")

    # assumptions = dependencies + "\n\n**Open questions**\n\n" + open-questions
    deps_body = read_body(feat_dir / "dependencies.md")
    oq_body   = read_body(feat_dir / "open-questions.md")
    assumptions = deps_body
    if oq_body:
        if oq_body.lstrip().startswith("— none"):
            assumptions += "\n\n**Open questions** " + oq_body.lstrip()
        else:
            assumptions += "\n\n**Open questions**\n\n" + oq_body

    # Apply strip + rewrite on all six body fields.
    fields = {
        "description":          description,
        "business_rules":       business_rules,
        "acceptance_criteria":  acceptance_criteria,
        "nfrs":                 nfrs,
        "test_scenarios":       test_scenarios,
        "assumptions":          assumptions,
    }
    for k, v in fields.items():
        v = strip_file_paths(v)
        v = rewrite_feat_to_task(v, task_num_by_feat)
        fields[k] = v

    # title fallback: frontmatter.title → H1 → slug
    title = fm.get("title") or ""
    if not title:
        h1, _ = strip_h1(feat_body)
        title = h1 or slug

    # Blocker-aware status
    status = "blocked" if _detect_blocked(feat_dir) else "todo"

    payload = {
        "feature_id":    fm.get("feature_id"),
        "slug":          slug,
        "initiative":    fm.get("initiative") or "",
        "task_object_id": fm.get("jetrix_task_object_id") or None,
        "title":         title,
        **fields,
        "metadata": {
            "externalId":         fm.get("feature_id"),
            "externalInitiative": fm.get("initiative"),
            "externalSlug":       slug,
            "dependsOnFeatureIds": fm.get("depends_on_features") or [],
            "useCases":            fm.get("use_cases") or [],
        },
        "status":   status,
        "priority": fm.get("priority") or "",
    }
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--project-root",  required=True)
    ap.add_argument("--sync-state",    required=True)
    ap.add_argument("--solution-slug", required=True)
    ap.add_argument("--output",        required=True, help="Path to write the assembled JSON.")
    ap.add_argument("--slug",          action="append", help="Optional: restrict to specific slug(s).")
    args = ap.parse_args()

    project_root = pathlib.Path(args.project_root).resolve()
    sync_state_path = pathlib.Path(args.sync_state).resolve()

    features_root = project_root / "features"
    if not features_root.exists():
        print(json.dumps({"error": "features/ missing", "solution_slug": args.solution_slug}))
        return 2

    sync_state = {}
    if sync_state_path.exists():
        try:
            sync_state = json.loads(sync_state_path.read_text(encoding='utf-8') or "null") or {}
        except json.JSONDecodeError:
            sync_state = {}

    # Build task_num_by_feat from previously pushed features in sync-state.
    task_num_by_feat: dict[str, int] = {}
    for key, entry in sync_state.items():
        if not isinstance(entry, dict) or not key.startswith("tasks/"):
            continue
        fid  = key[len("tasks/"):]
        tnum = entry.get("taskNumber")
        if fid and tnum is not None:
            task_num_by_feat[fid] = int(tnum)

    halts:      list[dict] = []
    skipped:    list[str]  = []
    groups:     dict[str, list[dict]] = {}
    fallback_slugs: list[str] = []

    dirs = sorted(d for d in features_root.iterdir() if d.is_dir())
    if args.slug:
        wanted = set(args.slug)
        dirs = [d for d in dirs if d.name in wanted]

    for feat_dir in dirs:
        slug = feat_dir.name

        # Prereq: required files must exist.
        missing = [f for f in REQUIRED_FILES if not (feat_dir / f).exists()]
        if missing:
            halts.append({"slug": slug, "reason": f"missing required files: {', '.join(missing)}"})
            continue

        # Frontmatter must have feature_id.
        feature_md_text = (feat_dir / "feature.md").read_text(encoding='utf-8')
        fm, _ = split_frontmatter(feature_md_text)
        if not fm.get("feature_id"):
            halts.append({"slug": slug, "reason": "feature.md missing feature_id in frontmatter"})
            continue

        # Skip-unchanged via folder hash.
        current_hash = _folder_hash(feat_dir)
        state_key = f"tasks/{fm['feature_id']}"
        prev = sync_state.get(state_key, {})
        prev_hash = (prev.get("contentHash") or "").replace("sha256:", "")
        if prev_hash and prev_hash == current_hash:
            skipped.append(slug)
            continue

        payload = assemble_feature(feat_dir, fm, task_num_by_feat)
        payload["_local_content_hash"] = current_hash  # for the write-back step

        list_name, is_fallback = _resolve_list_name(fm, args.solution_slug)
        if is_fallback:
            fallback_slugs.append(slug)
        groups.setdefault(list_name, []).append(payload)

    output = {
        "solution_slug":              args.solution_slug,
        "groups":                     [{"list_name": ln, "features": feats} for ln, feats in groups.items()],
        "skipped_unchanged":          skipped,
        "halts":                      halts,
        "solution_slug_fallback":     fallback_slugs,
    }
    pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.output).write_text(json.dumps(output, indent=2), encoding='utf-8')

    print(f"groups={len(groups)} to_push={sum(len(v) for v in groups.values())} "
          f"skipped_unchanged={len(skipped)} halts={len(halts)} solution_slug_fallback={len(fallback_slugs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
