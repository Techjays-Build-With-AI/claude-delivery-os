"""Assemble `feature_update_implementation` payloads from `features/*/tl-plan.md`.

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
        --project-root .jetrix \
        --sync-state   .jetrix/cache/sync-state.json \
        --output       /tmp/impl-assembled.json

    (Legacy v1 workspaces pass `--project-root .jetrix/<slug>` instead; the
    caller auto-detects either shape.)

v2.1 additions (IMPLEMENTED):
  - Also walks `features/<slug>/subtask/<repo>/implementation.md` for
    features with sub-task folders on disk, emitting
    `subtask_implementations_by_parent[<slug>] = [ ... ]`. Each row matches
    `task-mcp.subtask_update_implementation`'s per-item schema
    (subtask_object_id + implementation_details + status), plus
    `_local_impl_hash` for the response-apply step.
  - Skip-unchanged via `sync-state.subtasks/<subtask_object_id>.implementationHash`
    — matches materialize-subtasks.py's key so pull → push round-trips
    are no-ops.
  - Sub-task blocker detection reuses the same signals as parent
    (`[HELD]` in implementation.md; parent's open-questions / dependencies
    still gate) but sub-tasks don't have their own open-questions files —
    only tl-plan.md marker + parent-level signals count.
  - Same 60 KB size cap applies per sub-task.
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


def _get_subtask_fm_scalar(text: str, key: str) -> str:
    """Read a frontmatter scalar from a sub-task tab file. Same shape as
    the parent variant but scoped to the frontmatter block only."""
    if not text.startswith("---"):
        return ""
    m = re.search(r"^---\s*$", text[3:], re.MULTILINE)
    fm_block = text[3:3 + m.start()] if m else ""
    return _get_fm_scalar(fm_block, key)


def _walk_subtask_implementations(
    feat_dir: pathlib.Path,
    parent_feature_id: str,
    parent_blocked: bool,
    sync_state: dict,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Walk features/<slug>/subtask/*/implementation.md and assemble per-sub-task
    implementation payloads.

    Returns (payloads, skipped, warnings). Empty subtask/ folder → empty results.
    """
    subtask_root = feat_dir / "subtask"
    if not subtask_root.exists() or not subtask_root.is_dir():
        return [], [], []

    payloads: list[dict] = []
    skipped:  list[dict] = []
    warnings: list[dict] = []

    for sub_dir in sorted(subtask_root.iterdir()):
        if not sub_dir.is_dir():
            continue

        impl_md = sub_dir / "implementation.md"
        desc_md = sub_dir / "description.md"

        # implementation.md required — Description alone is not a buildable
        # sub-task push. Description tab lives on `feature_upsert_bundle`'s
        # sub-task path, not the Implementation-tab push.
        if not impl_md.exists():
            skipped.append({
                "slug":         f"{feat_dir.name}/subtask/{sub_dir.name}",
                "reason":       "no-implementation",
            })
            continue

        # Identity — pulled from description.md's frontmatter (all three tab
        # files share it per §v2.1); implementation.md's frontmatter also
        # carries it as a fallback.
        identity_source = desc_md if desc_md.exists() else impl_md
        id_text = _read(identity_source)
        subtask_object_id = _get_subtask_fm_scalar(id_text, "jetrix_subtask_object_id")
        external_id       = _get_subtask_fm_scalar(id_text, "feature_id")
        subtask_number    = _get_subtask_fm_scalar(id_text, "subtask_number")

        if not subtask_object_id:
            # Sub-task hasn't been pushed yet — /jetrix:push feature §7 must
            # create it first (via subtask_upsert_bundle) before its
            # Implementation can be updated by object_id.
            skipped.append({
                "slug":   f"{feat_dir.name}/subtask/{sub_dir.name}",
                "reason": "no-subtask-object-id (run /jetrix:push feature first)",
            })
            continue

        if external_id and parent_feature_id and external_id != parent_feature_id:
            warnings.append({
                "slug":    f"{feat_dir.name}/subtask/{sub_dir.name}",
                "message": (
                    f"sub-task feature_id ({external_id}) does not match "
                    f"parent's ({parent_feature_id}) — pushing anyway per "
                    "object_id, but sync-state may be inconsistent"
                ),
            })

        body = _strip_frontmatter(_read(impl_md)).replace("\r", "")
        body = re.sub(r"^\s*\n+", "", body)

        first_line = body.splitlines()[0] if body else ""
        if any(first_line.startswith(k) for k in LEAKED_FM_KEYS):
            warnings.append({
                "slug":    f"{feat_dir.name}/subtask/{sub_dir.name}",
                "message": f"body starts with leaked frontmatter key: {first_line[:40]!r}",
            })

        size = len(body)
        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        if size > SIZE_CAP:
            skipped.append({
                "slug":   f"{feat_dir.name}/subtask/{sub_dir.name}",
                "reason": f"size-cap ({size} > {SIZE_CAP})",
            })
            continue
        if size > SIZE_WARN_AT:
            warnings.append({
                "slug":    f"{feat_dir.name}/subtask/{sub_dir.name}",
                "message": f"{size} chars, near {SIZE_CAP} cap",
            })

        prev = sync_state.get(f"subtasks/{subtask_object_id}", {})
        prev_impl_hash = (prev.get("implementationHash") or "").replace("sha256:", "")
        if prev_impl_hash == body_hash:
            skipped.append({
                "slug":   f"{feat_dir.name}/subtask/{sub_dir.name}",
                "reason": f"unchanged (hash={body_hash[:16]})",
            })
            continue

        # Blocker detection for sub-tasks: `[HELD]` in implementation.md or
        # parent-level blocker signals propagate. Sub-tasks don't have their
        # own open-questions.md.
        sub_blocked = parent_blocked or ("[HELD]" in body)

        payloads.append({
            "subtask_object_id":      subtask_object_id,
            "external_id":            external_id,
            "subtask_number":         subtask_number,
            "implementation_details": body,
            "status":                 "blocked" if sub_blocked else "todo",
            "_local_impl_hash":       body_hash,
            "_local_size":            size,
        })

    return payloads, skipped, warnings


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

    features_root = project_root / "features"
    if not features_root.exists():
        pathlib.Path(args.output).write_text(json.dumps({
            "features": [], "skipped": [], "warnings": [],
            "halts": [{"reason": "features/ missing"}],
        }, indent=2), encoding="utf-8")
        print("no features/")
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
    # v2.1 — sub-task Implementation payloads grouped by parent slug so the
    # push flow can iterate `for parent, subs in bundle.items()` and issue
    # one subtask_update_implementation call per parent.
    subtask_implementations_by_parent: dict[str, list[dict]] = {}
    subtask_parent_context: dict[str, dict] = {}  # slug → {feature_id, task_object_id}

    for feat_dir in sorted(d for d in features_root.iterdir() if d.is_dir()):
        slug = feat_dir.name

        feature_md = feat_dir / "feature.md"
        tl_plan    = feat_dir / "tl-plan.md"

        if not feature_md.exists():
            continue  # not a feature folder

        fm_text = _read(feature_md)
        # Extract just the frontmatter block for field lookups.
        fm_end_m = re.search(r"^---\s*$", fm_text[3:], re.MULTILINE) if fm_text.startswith("---") else None
        fm_block = fm_text[3:3 + fm_end_m.start()] if fm_end_m else ""

        feature_id     = _get_fm_scalar(fm_block, "feature_id")
        task_object_id = _get_fm_scalar(fm_block, "jetrix_task_object_id")

        parent_blocked_for_subs = False
        parent_pushed = False

        if not tl_plan.exists():
            skipped.append({"slug": slug, "reason": "no-tl-plan"})
        elif not feature_id:
            skipped.append({"slug": slug, "reason": "no-feature-id"})
        elif not task_object_id:
            skipped.append({"slug": slug, "reason": "no-task-object-id"})
        else:
            body = _strip_frontmatter(_read(tl_plan)).replace("\r", "")
            body = re.sub(r"^\s*\n+", "", body)

            first_line = body.splitlines()[0] if body else ""
            if any(first_line.startswith(k) for k in LEAKED_FM_KEYS):
                warnings.append({"slug": slug, "message": f"body starts with leaked frontmatter key: {first_line[:40]!r}"})

            size = len(body)
            body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

            if size > SIZE_CAP:
                skipped.append({"slug": slug, "reason": f"size-cap ({size} > {SIZE_CAP})"})
            else:
                if size > SIZE_WARN_AT:
                    warnings.append({"slug": slug, "message": f"{size} chars, near {SIZE_CAP} cap"})

                prev = sync_state.get(f"tasks/{feature_id}", {})
                prev_impl_hash = (prev.get("implementation_hash") or "").replace("sha256:", "")
                if prev_impl_hash == body_hash:
                    skipped.append({"slug": slug, "reason": f"unchanged (hash={body_hash[:16]})"})
                else:
                    parent_blocked_for_subs = _detect_blocked(feat_dir, body)
                    status = "blocked" if parent_blocked_for_subs else "readyForDev"

                    features.append({
                        "feature_id":             feature_id,
                        "slug":                   slug,
                        "task_object_id":         task_object_id,
                        "implementation_details": body,
                        "status":                 status,
                        "_local_impl_hash":       body_hash,
                        "_local_size":            size,
                    })
                    parent_pushed = True

        # v2.1 — walk sub-task implementations even if the parent is skipped
        # (a re-composed sub-task with the parent's tl-plan.md unchanged
        # still needs to land). parent_blocked_for_subs propagates only when
        # we actually detected it from parent's tl-plan; when we didn't
        # compute it (skip path), leave sub-tasks to detect from their own
        # `[HELD]` marker.
        if feature_id and task_object_id and (feat_dir / "subtask").exists():
            sub_payloads, sub_skipped, sub_warnings = _walk_subtask_implementations(
                feat_dir=feat_dir,
                parent_feature_id=feature_id,
                parent_blocked=parent_blocked_for_subs,
                sync_state=sync_state,
            )
            skipped.extend(sub_skipped)
            warnings.extend(sub_warnings)
            if sub_payloads:
                subtask_implementations_by_parent[slug] = sub_payloads
                subtask_parent_context[slug] = {
                    "feature_id":            feature_id,
                    "parent_task_object_id": task_object_id,
                }

        # Unused local — quiet the linter.
        _ = parent_pushed

    subtask_count = sum(len(v) for v in subtask_implementations_by_parent.values())
    output = {
        "features": features,
        "skipped":  skipped,
        "warnings": warnings,
        "halts":    [],
        # v2.1 additions
        "subtask_implementations_by_parent": subtask_implementations_by_parent,
        "subtask_parent_context":            subtask_parent_context,
    }
    pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.output).write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(
        f"to_push={len(features)} skipped={len(skipped)} warnings={len(warnings)} "
        f"subtasks_to_push={subtask_count} "
        f"subtask_parents={len(subtask_implementations_by_parent)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
