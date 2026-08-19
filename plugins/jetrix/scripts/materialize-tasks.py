"""Materialize `tasks/<slug>.md` from a task_pull_bundle JSON.

Invoked by `/jetrix:pull list` (see plugins/jetrix/commands/references/pull/list.md)
for the non-FEATURE tasks in an MC List (bugs, chores, ad-hoc tasks). Feature
tasks in the same List go through `materialize-features.py` — different on-disk
layout (folder-of-7-files vs single-file).

Each non-feature task becomes ONE file at `tasks/<slug or task-N>.md`:

    ---
    task_number: 230
    task_object_id: 6a7c376e...
    task_type: task
    title: ...
    status: inProgress
    priority: high
    list_id: 6a61...
    list_name: Reported Issues
    sprint_id:
    sprint_number:
    metadata:
      externalId: TASK-LOGIN-BUG
      externalInitiative: q3-hotfixes
    last_pulled: 2026-08-13T...
    ---

    # {title}

    ## Description
    {description verbatim}

    ## Business Rules
    ...

Empty section fields are omitted so the file doesn't fill with blank headings.

Usage:
    python materialize-tasks.py \
        --bundle       .jetrix/cache/.pull-tasks.json \
        --project-root .jetrix/<solution-slug> \
        --sync-state   .jetrix/cache/sync-state.json
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import sys


SECTIONS = (
    ("description",           "Description"),
    ("business_rules",        "Business Rules"),
    ("acceptance_criteria",   "Acceptance Criteria"),
    ("nfrs",                  "NFRs"),
    ("test_scenarios",        "Test Scenarios"),
    ("assumptions",           "Assumptions / Dependencies"),
    ("implementation_details","Implementation"),
)


def _iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_json(path: pathlib.Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null") or default
    except json.JSONDecodeError:
        return default


def _yaml_scalar(value) -> str:
    """Serialize a scalar for YAML frontmatter — quoted string when needed."""
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    s = str(value)
    if any(c in s for c in ':#{}[],&*!|>\'"%@`') or s != s.strip():
        return json.dumps(s)
    return s


def _frontmatter(task: dict, now: str) -> str:
    lines = ["---"]

    def emit(key: str, val):
        v = _yaml_scalar(val)
        if v == "":
            lines.append(f"{key}:")
        else:
            lines.append(f"{key}: {v}")

    emit("task_number",    task.get("task_number"))
    emit("task_object_id", task.get("task_object_id"))
    emit("task_type",      task.get("task_type") or "task")
    emit("title",          task.get("title") or "")
    emit("status",         task.get("status") or "")
    emit("priority",       task.get("priority") or "")
    emit("list_id",        task.get("list_id") or "")
    emit("list_name",      task.get("list_name") or "")
    emit("sprint_id",      task.get("sprint_id") or "")
    emit("sprint_number",  task.get("sprint_number") if task.get("sprint_number") is not None else "")

    meta = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
    if meta:
        lines.append("metadata:")
        for k, v in meta.items():
            lines.append(f"  {k}: {_yaml_scalar(v)}")
    else:
        lines.append("metadata:")

    lines.append(f"last_pulled: {now}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _body(task: dict) -> str:
    parts = [f"\n# {task.get('title') or task.get('slug') or ''}\n"]
    for wire, header in SECTIONS:
        value = (task.get(wire) or "").strip()
        if not value:
            continue
        parts.append(f"\n## {header}\n{value}\n")
    return "".join(parts)


def _slug(task: dict) -> str:
    slug = (task.get("slug") or "").strip()
    if slug:
        return slug
    num = task.get("task_number")
    if num is not None:
        return f"task-{num}"
    oid = (task.get("task_object_id") or "")[:8]
    return f"task-{oid or 'unknown'}"


def materialize(bundle_path: pathlib.Path, project_root: pathlib.Path, sync_state_path: pathlib.Path) -> int:
    bundle = _load_json(bundle_path, {})
    tasks = bundle.get("tasks") or []
    if not tasks:
        print("no tasks in bundle")
        return 0

    now = _iso_now()
    sync_state = _load_json(sync_state_path, {})
    written: list[str] = []
    unchanged: list[str] = []

    tasks_dir = project_root / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        # Skip if task_type is feature — those go through materialize-features.py.
        if (task.get("task_type") or "").lower() == "feature":
            continue

        slug = _slug(task)
        target = tasks_dir / f"{slug}.md"
        content = _frontmatter(task, now) + _body(task)

        old = target.read_text(encoding="utf-8") if target.exists() else None
        if old != content:
            target.write_text(content, encoding="utf-8")
            written.append(slug)
        else:
            unchanged.append(slug)

        rel = str(target.relative_to(project_root.parent)).replace("\\", "/") \
            if project_root.parent in target.parents else f"tasks/{slug}.md"
        # Sync-state key = repo-relative task file path (matches push side).
        state_key = f"tasks/{slug}.md"
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        sync_state[state_key] = {
            "taskNumber":   task.get("task_number"),
            "taskObjectId": task.get("task_object_id"),
            "slug":         slug,
            "contentHash":  f"sha256:{content_hash}",
            "lastPulled":   now,
        }

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    print(f"written={len(written)} unchanged={len(unchanged)}")
    for s in written:
        print(f"  written   tasks/{s}.md")
    for s in unchanged:
        print(f"  unchanged tasks/{s}.md")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--bundle",       required=True)
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--sync-state",   required=True)
    args = ap.parse_args()

    return materialize(
        bundle_path=pathlib.Path(args.bundle),
        project_root=pathlib.Path(args.project_root),
        sync_state_path=pathlib.Path(args.sync_state),
    )


if __name__ == "__main__":
    sys.exit(main())
