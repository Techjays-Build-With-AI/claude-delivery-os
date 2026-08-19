"""Assemble `feature_update_implementation` payloads from `context/features/*/tl-plan.md`.

Invoked by `/jetrix:push implementation` (see plugins/jetrix/commands/references/push/implementation.md)
before the MCP call. Walks feature folders, extracts feature_id + task_object_id
from feature.md's frontmatter, strips frontmatter + H1 from tl-plan.md, applies
the 60 KB size gate, detects blocker signals, skips unchanged (via
`sync-state.implementation_hash`), and emits ONE JSON blob ready for
`feature_update_implementation`.

Contract preserved verbatim:
  - Skip feature if no tl-plan.md → surface as `no-tl-plan` skip
  - Skip if feature.md has no feature_id → surface as `no-feature-id` skip
  - Skip if feature.md has no jetrix_task_object_id → surface as `no-task-object-id`
  - Body integrity: strip frontmatter + strip CRLF + strip leading blank lines
  - Sanity check: body contains no `\\r`, no leading `doc_type:` / `schema_version:` /
    `produced_by:` / `feature_id:` / `composed_at:` / `inputs_hash:` line
  - Size gate: > 60 000 chars → skip loud (SPLIT_REQUIRED); 55 000–60 000 → warn
  - Blocker signals: open-questions Impact starts with 'Blocks' / dependencies
    flagged / tl-plan.md contains '[HELD]' → status = "blocked"; else "readyForDev"
  - Skip-unchanged via body hash vs sync-state.implementation_hash

Usage:
    python assemble-implementation.py \
        --project-root .jetrix/<slug> \
        --sync-state   .jetrix/cache/sync-state.json \
        --output       /tmp/impl-assembled.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys


SIZE_CAP     = 60_000   # MC Joi validator on implementationDetails
SIZE_WARN_AT = 55_000
LEAKED_FM_KEYS = ("doc_type:", "schema_version:", "produced_by:",
                  "feature_id:", "composed_at:", "inputs_hash:")


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    m = re.search(r"^---\s*$", text[3:], re.MULTILINE)
    if not m:
        return text
    end = 3 + m.start() + len("---")
    return text[end:].lstrip("\r\n")


def _get_fm_scalar(text: str, key: str) -> str:
    m = re.search(rf'^{re.escape(key)}\s*:\s*(.+?)\s*$', text, re.MULTILINE)
    if not m:
        return ""
    val = m.group(1).strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1]
    return val.strip()


def _detect_blocked(feat_dir: pathlib.Path, tl_plan_body: str) -> bool:
    # tl-plan.md marker
    if "[HELD]" in tl_plan_body:
        return True
    # open-questions.md — table row with Status=Open AND Impact starts with 'Blocks'
    oq = feat_dir / "open-questions.md"
    if oq.exists():
        for line in oq.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.split("|")]
            if any(c.lower() == "open" for c in cells) and any(c.lower().startswith("blocks") for c in cells):
                return True
    # dependencies.md flags
    dep = feat_dir / "dependencies.md"
    if dep.exists():
        body = dep.read_text(encoding="utf-8").lower()
        for token in ("unavailable", "not available", "blocked", "tbd"):
            if token in body:
                return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--sync-state",   required=True)
    ap.add_argument("--output",       required=True)
    args = ap.parse_args()

    project_root    = pathlib.Path(args.project_root).resolve()
    sync_state_path = pathlib.Path(args.sync_state).resolve()

    features_root = project_root / "context" / "features"
    if not features_root.exists():
        pathlib.Path(args.output).write_text(json.dumps({
            "features": [], "skipped": [], "warnings": [],
            "halts": [{"reason": "context/features/ missing"}],
        }, indent=2), encoding="utf-8")
        print("no context/features/")
        return 0

    sync_state = {}
    if sync_state_path.exists():
        try:
            sync_state = json.loads(sync_state_path.read_text(encoding="utf-8") or "null") or {}
        except json.JSONDecodeError:
            sync_state = {}

    features: list[dict] = []
    skipped:  list[dict] = []   # {slug, reason} — no-tl-plan, no-feature-id, unchanged, size-cap
    warnings: list[dict] = []   # {slug, message}

    for feat_dir in sorted(d for d in features_root.iterdir() if d.is_dir()):
        slug = feat_dir.name

        feature_md = feat_dir / "feature.md"
        tl_plan    = feat_dir / "tl-plan.md"

        if not feature_md.exists():
            continue  # not a feature folder
        if not tl_plan.exists():
            skipped.append({"slug": slug, "reason": "no-tl-plan"})
            continue

        fm_text = _read(feature_md)
        # Extract just the frontmatter block for field lookups.
        fm_end_m = re.search(r"^---\s*$", fm_text[3:], re.MULTILINE) if fm_text.startswith("---") else None
        fm_block = fm_text[3:3 + fm_end_m.start()] if fm_end_m else ""

        feature_id     = _get_fm_scalar(fm_block, "feature_id")
        task_object_id = _get_fm_scalar(fm_block, "jetrix_task_object_id")

        if not feature_id:
            skipped.append({"slug": slug, "reason": "no-feature-id"})
            continue
        if not task_object_id:
            skipped.append({"slug": slug, "reason": "no-task-object-id"})
            continue

        body = _strip_frontmatter(_read(tl_plan)).replace("\r", "")
        # Strip leading blank lines.
        body = re.sub(r"^\s*\n+", "", body)

        # Sanity: body must not start with a leaked frontmatter key.
        first_line = body.splitlines()[0] if body else ""
        if any(first_line.startswith(k) for k in LEAKED_FM_KEYS):
            warnings.append({"slug": slug, "message": f"body starts with leaked frontmatter key: {first_line[:40]!r}"})

        size = len(body)
        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        # Size gate.
        if size > SIZE_CAP:
            skipped.append({"slug": slug, "reason": f"size-cap ({size} > {SIZE_CAP})"})
            continue
        if size > SIZE_WARN_AT:
            warnings.append({"slug": slug, "message": f"{size} chars, near {SIZE_CAP} cap"})

        # Skip-unchanged.
        prev = sync_state.get(f"tasks/{feature_id}", {})
        prev_impl_hash = (prev.get("implementation_hash") or "").replace("sha256:", "")
        if prev_impl_hash == body_hash:
            skipped.append({"slug": slug, "reason": f"unchanged (hash={body_hash[:16]})"})
            continue

        status = "blocked" if _detect_blocked(feat_dir, body) else "readyForDev"

        features.append({
            "feature_id":             feature_id,
            "slug":                   slug,
            "task_object_id":         task_object_id,
            "implementation_details": body,
            "status":                 status,
            "_local_impl_hash":       body_hash,
            "_local_size":            size,
        })

    output = {
        "features": features,
        "skipped":  skipped,
        "warnings": warnings,
        "halts":    [],
    }
    pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.output).write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"to_push={len(features)} skipped={len(skipped)} warnings={len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
