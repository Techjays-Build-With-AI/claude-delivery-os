"""Materialize `context/features/<slug>/*.md` from a feature_pull_bundle JSON.

Invoked by `/jetrix:pull scope` (see plugins/jetrix/commands/references/pull/scope.md)
after task-mcp returns the feature bundle. Replaces the "for each feature, write
files" iteration in the plugin markdown so the pull is O(1) tool calls instead
of O(features * files).

Usage:
    python materialize-features.py \
        --bundle       .jetrix/cache/.pull-features.json \
        --project-root .jetrix/<solution-slug> \
        --sync-state   .jetrix/cache/sync-state.json

The bundle file is the raw JSON body of the `feature_pull_bundle` MCP response.
Contract (fields written per feature) mirrors the table in the reference file.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import sys


# Wire-field -> local file. Order preserved to keep folder-hash stable.
FIELDS = (
    ("description",            "feature.md"),
    ("business_rules",         "business-rules.md"),
    ("acceptance_criteria",    "acceptance-criteria.md"),
    ("nfrs",                   "nfrs.md"),
    ("test_scenarios",         "test-scenarios.md"),
    ("assumptions",            "dependencies.md"),
    ("implementation_details", "tl-plan.md"),
)


def _iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _frontmatter(feat: dict, is_feature_md: bool, today: str) -> str:
    lines = ["---"]
    for key in ("feature_id", "initiative", "slug"):
        if feat.get(key):
            lines.append(f"{key}: {feat[key]}")
    if is_feature_md and feat.get("list_name"):
        lines.append(f"list_name: {feat['list_name']}")
    if feat.get("task_number") is not None:
        lines.append(f"jetrix_task_id: {feat['task_number']}")
    if feat.get("task_object_id"):
        lines.append(f"jetrix_task_object_id: {feat['task_object_id']}")
    if feat.get("status"):
        lines.append(f"status: {feat['status']}")
    meta = feat.get("metadata") if isinstance(feat.get("metadata"), dict) else {}
    deps = feat.get("depends_on_features") or meta.get("dependsOnFeatureIds") or []
    if deps:
        lines.append(f"depends_on_features: {json.dumps(deps)}")
    ucs = feat.get("use_cases") or meta.get("useCases") or []
    if ucs:
        lines.append(f"use_cases: {json.dumps(ucs)}")
    lines.append(f"generated_at: {today}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _load_json(path: pathlib.Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null") or default
    except json.JSONDecodeError:
        return default


def materialize(bundle_path: pathlib.Path, project_root: pathlib.Path, sync_state_path: pathlib.Path) -> int:
    bundle = _load_json(bundle_path, {})
    features = bundle.get("features") or []
    if not features:
        print("no features in bundle")
        return 0

    today = datetime.datetime.utcnow().date().isoformat()
    now = _iso_now()

    sync_state = _load_json(sync_state_path, {})

    updated: list[str] = []
    unchanged: list[str] = []
    skipped: list[str] = []

    for feat in features:
        slug = feat.get("slug") or feat.get("feature_id")
        if not slug:
            skipped.append("(missing slug/feature_id)")
            continue

        feat_dir = project_root / "context" / "features" / slug
        feat_dir.mkdir(parents=True, exist_ok=True)

        changed_any = False
        folder_hash_input: list[str] = []

        for wire_key, fname in FIELDS:
            body = feat.get(wire_key) or ""
            if fname != "feature.md" and not body.strip():
                continue

            fm = _frontmatter(feat, fname == "feature.md", today)
            if fname == "feature.md":
                title = feat.get("title") or slug
                content = f"{fm}\n# {title}\n\n{body}\n"
            else:
                content = f"{fm}\n{body}\n"

            target = feat_dir / fname
            old = target.read_text(encoding="utf-8") if target.exists() else None
            if old != content:
                target.write_text(content, encoding="utf-8")
                changed_any = True
            folder_hash_input.append(content)

        folder_hash = hashlib.sha256("".join(folder_hash_input).encode("utf-8")).hexdigest()
        key = f"tasks/{feat.get('feature_id') or slug}"
        sync_state[key] = {
            "taskNumber":   feat.get("task_number"),
            "taskObjectId": feat.get("task_object_id"),
            "slug":         slug,
            "contentHash":  f"sha256:{folder_hash}",
            "lastPulled":   now,
        }
        (updated if changed_any else unchanged).append(slug)

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    print(f"updated={len(updated)} unchanged={len(unchanged)} skipped={len(skipped)}")
    for s in updated:
        print(f"  updated   {s}")
    for s in unchanged:
        print(f"  unchanged {s}")
    for s in skipped:
        print(f"  skipped   {s}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Materialize feature folders from a feature_pull_bundle JSON.")
    ap.add_argument("--bundle",       required=True, help="Path to the feature_pull_bundle JSON on disk.")
    ap.add_argument("--project-root", required=True, help="Absolute path to <workspace>/.jetrix/<slug>/.")
    ap.add_argument("--sync-state",   required=True, help="Absolute path to <workspace>/.jetrix/cache/sync-state.json.")
    args = ap.parse_args()

    return materialize(
        bundle_path=pathlib.Path(args.bundle),
        project_root=pathlib.Path(args.project_root),
        sync_state_path=pathlib.Path(args.sync_state),
    )


if __name__ == "__main__":
    sys.exit(main())
