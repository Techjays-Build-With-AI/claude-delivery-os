"""Materialize `comments.md` + `attachments/` next to a task.

Invoked by `/jetrix:pull task|list|sprint` after task-mcp returns
`task_comments_pull` + `task_attachments_pull` for one task. The bundle is:

    {
      "task_number": 42,
      "task_object_id": "6a61...",
      "title": "Document Classification",
      "comments":    <task_comments_pull response, verbatim>,
      "attachments": <task_attachments_pull response, verbatim>
    }

`--target-dir` is the task's own folder, so one script serves all three
kinds with no branching:

    features/<slug>/                     BA feature
    features/<slug>/subtask/<repo>/      sub-task
    tasks/<slug>/                        bug / story / ad-hoc task

Both outputs are written ONLY when there is something to write — a task with
no comments gets no `comments.md`, and a task with no file attachments gets
no `attachments/` folder. Both carry `readonly: true` in frontmatter, which
is what keeps `/jetrix:push` from ever sweeping them back up to MC.

File bytes are NOT fetched here. The script emits a `curl -K` config and the
caller downloads in parallel, so bytes go GCS -> disk without passing
through Claude's context.

Usage:
    python materialize-comments.py \
        --bundle            .jetrix/cache/.pull-comments.json \
        --target-dir        .jetrix/features/<slug> \
        --sync-state        .jetrix/cache/sync-state.json \
        --download-manifest .jetrix/cache/.attachment-downloads.curl
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys
import urllib.parse

ATTACHMENT_DIR = "attachments"


def _iso_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0, tzinfo=None
    ).isoformat() + "Z"


def _load_json(path: pathlib.Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null") or default
    except json.JSONDecodeError:
        return default


def _short_ts(value) -> str:
    """`2026-09-20T14:32:07.001Z` -> `2026-09-20 14:32`."""
    s = str(value or "")
    m = re.match(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})", s)
    return f"{m.group(1)} {m.group(2)}" if m else s


def _safe_name(name: str) -> str:
    """Filesystem-safe leaf name. Never allowed to escape the folder.

    Truncation keeps the extension — an agent opening a mockup needs the
    `.png`, and a 300-char name is otherwise cut mid-stem.
    """
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", (name or "").strip()).strip("-._")
    if not cleaned:
        return "file"
    if len(cleaned) <= 120:
        return cleaned
    stem, dot, ext = cleaned.rpartition(".")
    if dot and 0 < len(ext) <= 10:
        return stem[:120 - len(ext) - 1] + "." + ext
    return cleaned[:120]


def _safe_number(value) -> str:
    """Attachment number for the local filename. Coerced to int — it is
    interpolated ahead of the sanitised name, so a string like `../../x`
    would otherwise escape the folder that `_safe_name` protects."""
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return "x"


def _safe_download_url(url: str) -> bool:
    """Only plain http(s), and nothing that could add a line to curl's -K
    config. A quote or newline in a URL would let a crafted bundle inject
    its own `output =` directive and write anywhere on disk."""
    u = str(url or "")
    if any(c in u for c in '"\\\r\n\t') or any(ord(c) < 32 for c in u):
        return False
    return urllib.parse.urlparse(u).scheme in ("http", "https")


def _human_size(size) -> str:
    try:
        n = float(size)
    except (TypeError, ValueError):
        return "—"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return "—"


def _flatten(nodes: list, depth: int = 0) -> list[tuple[int, dict]]:
    out: list[tuple[int, dict]] = []
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        out.append((depth, node))
        out.extend(_flatten(node.get("replies") or [], depth + 1))
    return out


def _render_comments(bundle: dict, comments: dict, now: str) -> str:
    rows = _flatten(comments.get("comments") or [])
    title = bundle.get("title") or ""
    num = bundle.get("task_number")

    head = [
        "---",
        "doc_type: task-comments",
        "schema_version: 1.0",
        "produced_by: delivery-os",
        f"generated_at: {now}",
        f"task_number: {num}" if num is not None else "task_number:",
        f"task_object_id: {bundle.get('task_object_id') or ''}",
        f"comments: {comments.get('count', len(rows))}",
        f"unresolved: {comments.get('unresolved_count', 0)}",
        "readonly: true",
        "---",
        "",
        f"# Comments — TASK-{num}" + (f' "{title}"' if title else ""),
        "",
    ]

    body: list[str] = []
    for depth, c in rows:
        author = (c.get("author") or {}).get("name") or "Unknown"
        bits = [author, _short_ts(c.get("timestamp"))]
        if c.get("edited"):
            bits.append("edited")
        if c.get("resolved"):
            who = c.get("resolved_by")
            bits.append(f"resolved by {who}" if who else "resolved")
        elif not depth:
            # Resolution is a property of the thread, so flag it on the root
            # only — repeating it on every reply is noise.
            bits.append("**UNRESOLVED**")
        prefix = "↳ " if depth else ""
        body.append(
            f"{'#' * min(depth + 2, 6)} {prefix}[C-{c.get('comment_number')}] "
            + " · ".join(bits)
        )
        mentions = [m for m in (c.get("mentions") or []) if m]
        if mentions:
            body.append(f"*mentions: {', '.join(mentions)}*")
        body.append("")
        body.append((c.get("text") or "").strip())
        body.append("")

    return "\n".join(head + body).rstrip() + "\n"


def _render_attachments(bundle: dict, rows: list, now: str) -> str:
    num = bundle.get("task_number")
    title = bundle.get("title") or ""
    head = [
        "---",
        "doc_type: task-attachments",
        "schema_version: 1.0",
        "produced_by: delivery-os",
        f"generated_at: {now}",
        f"task_number: {num}" if num is not None else "task_number:",
        f"task_object_id: {bundle.get('task_object_id') or ''}",
        f"attachments: {len(rows)}",
        "readonly: true",
        "---",
        "",
        f"# Attachments — TASK-{num}" + (f' "{title}"' if title else ""),
        "",
        "| # | Name | Type | Size | Uploaded by | When | Local |",
        "|---|---|---|---|---|---|---|",
    ]
    for a, local in rows:
        cell = f"`{ATTACHMENT_DIR}/{local}`" if local else f"[link]({a.get('url') or ''})"
        head.append(
            f"| {a.get('attachment_number') or ''} | {a.get('name') or ''} "
            f"| {a.get('type') or ''} | {_human_size(a.get('size'))} "
            f"| {a.get('uploaded_by') or ''} | {_short_ts(a.get('created_at'))} | {cell} |"
        )
    return "\n".join(head) + "\n"


def _without_timestamp(text: str) -> str:
    return re.sub(r"^generated_at:.*$", "", text or "", count=1, flags=re.MULTILINE)


def _write_if_changed(path: pathlib.Path, content: str) -> bool:
    """Rewrite only on a real change — `generated_at` alone must not count, or
    every re-pull would dirty the file and defeat skip-unchanged."""
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old is not None and _without_timestamp(old) == _without_timestamp(content):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def materialize(
    *,
    bundle_path: pathlib.Path,
    target_dir: pathlib.Path,
    sync_state_path: pathlib.Path,
    manifest_path: pathlib.Path | None,
) -> int:
    bundle = _load_json(bundle_path, None)
    if not isinstance(bundle, dict):
        print(f"ERROR: bundle not readable: {bundle_path}", file=sys.stderr)
        return 1

    now = _iso_now()
    comments = bundle.get("comments") if isinstance(bundle.get("comments"), dict) else {}
    attachments = bundle.get("attachments") if isinstance(bundle.get("attachments"), dict) else {}
    att_rows = [a for a in (attachments.get("attachments") or []) if isinstance(a, dict)]

    sync_state = _load_json(sync_state_path, {})
    task_oid = str(bundle.get("task_object_id") or "")
    state_key = f"comments/{task_oid}" if task_oid else f"comments/task-{bundle.get('task_number')}"
    entry = sync_state.get(state_key) or {}
    written: list[str] = []

    # --- comments.md — only when there is at least one comment ---
    if comments.get("comments"):
        content = _render_comments(bundle, comments, now)
        chash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if _write_if_changed(target_dir / "comments.md", content):
            written.append("comments.md")
        entry["commentsHash"] = f"sha256:{chash}"
        entry["unresolved"] = comments.get("unresolved_count", 0)

    # --- attachments — only when the task actually has some ---
    downloads: list[tuple[str, pathlib.Path]] = []
    rejected: list[str] = []
    if att_rows:
        att_root = (target_dir / ATTACHMENT_DIR).resolve()
        table: list[tuple[dict, str]] = []
        for a in att_rows:
            if a.get("type") == "link" or not a.get("download_url"):
                table.append((a, ""))
                continue
            if not _safe_download_url(a["download_url"]):
                rejected.append(str(a.get("name") or a.get("attachment_id") or "?"))
                table.append((a, ""))
                continue
            local = f"{_safe_number(a.get('attachment_number'))}-{_safe_name(a.get('name') or '')}"
            dest = (att_root / local).resolve()
            # Belt and braces: whatever the two sanitisers produced, the
            # destination must still sit inside attachments/.
            if att_root not in dest.parents:
                rejected.append(str(a.get("name") or "?"))
                table.append((a, ""))
                continue
            table.append((a, local))
            downloads.append((a["download_url"], dest))

        content = _render_attachments(bundle, table, now)
        ahash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if _write_if_changed(target_dir / "attachments.md", content):
            written.append("attachments.md")
        entry["attachmentsHash"] = f"sha256:{ahash}"
        entry["attachments"] = len(att_rows)

    # Re-download only what is missing — a pulled file never changes in place
    # (a replaced file gets a new attachmentNumber, hence a new local name).
    pending = [(url, dest) for url, dest in downloads if not dest.exists()]
    if pending and manifest_path is not None:
        (target_dir / ATTACHMENT_DIR).mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for url, dest in pending:
            lines.append(f'url = "{url}"')
            lines.append(f'output = "{dest.as_posix()}"')
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif manifest_path is not None and manifest_path.exists():
        manifest_path.unlink()

    if entry:
        entry["taskNumber"] = bundle.get("task_number")
        entry["taskObjectId"] = task_oid
        entry["lastPulled"] = now
        sync_state[state_key] = entry
        sync_state_path.parent.mkdir(parents=True, exist_ok=True)
        sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    print(
        f"comments={len(comments.get('comments') or [])} "
        f"unresolved={comments.get('unresolved_count', 0)} "
        f"attachments={len(att_rows)} downloads={len(pending)} "
        f"written={','.join(written) or 'none'}"
    )
    if rejected:
        print(f"WARNING: refused unsafe download target(s): {', '.join(rejected)}", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--bundle",            required=True)
    ap.add_argument("--target-dir",        required=True)
    ap.add_argument("--sync-state",        required=True)
    ap.add_argument("--download-manifest", required=False)
    args = ap.parse_args()

    return materialize(
        bundle_path=pathlib.Path(args.bundle),
        target_dir=pathlib.Path(args.target_dir),
        sync_state_path=pathlib.Path(args.sync_state),
        manifest_path=pathlib.Path(args.download_manifest) if args.download_manifest else None,
    )


if __name__ == "__main__":
    sys.exit(main())
