"""Post-download apply step for `/jetrix:pull scope`.

Reads the curl parallel-download log, atomically moves successful transfers
from a staging dir into `<project_root>/<rel_path>`, and updates
`sync-state.json` with per-file `documentId`, `version`, `contentHash`,
`lastPulled` sourced from the manifest sidecar.

Invoked by `/jetrix:pull scope` (see plugins/jetrix/commands/references/pull/scope.md)
after `curl --parallel` finishes. Replaces the "curl -o <final_path>" data-loss
pattern — on any non-200 the staging file is discarded and the local original
(if any) stays untouched.

Usage:
    python apply-scope-manifest.py \
        --staging      /tmp/jetrix-pull-XXXX \
        --project-root .jetrix/<solution-slug> \
        --sync-state   .jetrix/cache/sync-state.json \
        --curl-log     /tmp/curl-log-XXXX \
        --manifest     /tmp/manifest-XXXX.json

The curl log is a series of `<staged_absolute_path>|<http_code>` lines
(produced by `-w "%{filename_effective}|%{http_code}\n" --parallel`).
The manifest file is a JSON object keyed by relative path:
    { "ba-output/scope.md": { "documentId": "...", "version": 3, "contentHash": "..." }, ... }
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import shutil
import sys


def _iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_json(path: pathlib.Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null") or default
    except json.JSONDecodeError:
        return default


def apply(
    staging: pathlib.Path,
    project_root: pathlib.Path,
    sync_state_path: pathlib.Path,
    curl_log_path: pathlib.Path,
    manifest_path: pathlib.Path,
) -> int:
    manifest = _load_json(manifest_path, {})
    ok: list[str] = []
    fail: list[tuple[str, str]] = []

    for raw in curl_log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if "|" not in line:
            continue
        staged, code = line.rsplit("|", 1)
        staged = staged.strip()
        code = code.strip()
        if not staged.startswith(str(staging)):
            continue  # unrelated curl stderr line
        try:
            rel = str(pathlib.Path(staged).relative_to(staging)).replace("\\", "/")
        except ValueError:
            continue
        if code == "200":
            target = project_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(staged, target)
            ok.append(rel)
        else:
            fail.append((rel, code))

    sync_state = _load_json(sync_state_path, {})
    now = _iso_now()
    for rel in ok:
        meta = manifest.get(rel, {})
        ch = meta.get("contentHash") or ""
        entry = {
            "documentId":  meta.get("documentId"),
            "version":     meta.get("version"),
            "contentHash": f"sha256:{ch}" if ch and not ch.startswith("sha256:") else (ch or None),
            "lastPulled":  now,
        }
        sync_state[rel] = {k: v for k, v in entry.items() if v is not None}

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    print(f"downloaded={len(ok)} failed={len(fail)}")
    for rel in ok:
        print(f"  OK   {rel}")
    for rel, code in fail:
        print(f"  FAIL {rel} (HTTP {code})")
    return 1 if fail else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--staging",      required=True)
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--sync-state",   required=True)
    ap.add_argument("--curl-log",     required=True)
    ap.add_argument("--manifest",     required=True)
    args = ap.parse_args()

    return apply(
        staging=pathlib.Path(args.staging).resolve(),
        project_root=pathlib.Path(args.project_root).resolve(),
        sync_state_path=pathlib.Path(args.sync_state).resolve(),
        curl_log_path=pathlib.Path(args.curl_log).resolve(),
        manifest_path=pathlib.Path(args.manifest).resolve(),
    )


if __name__ == "__main__":
    sys.exit(main())
