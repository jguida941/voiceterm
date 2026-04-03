#!/usr/bin/env python3
"""Verify startup/review/compact pipeline surfaces share one snapshot stamp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.governance_scan import scan_repo_governance_safely
from dev.scripts.devctl.runtime.review_state_locator import resolve_review_state_path
from dev.scripts.devctl.runtime.startup_context import build_startup_context


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    startup_payload: dict[str, object] | None = None,
    review_state_payload: dict[str, object] | None = None,
    compact_payload: dict[str, object] | None = None,
    commit_pipeline_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    startup = startup_payload or build_startup_context(repo_root=repo_root).to_dict()
    review_state = review_state_payload or _load_review_state_payload(repo_root)
    compact = compact_payload or _load_json(_surface_path(repo_root, "compact.json"))
    commit_pipeline = commit_pipeline_payload or _load_json(
        _surface_path(repo_root, "commit_pipeline.json")
    )
    snapshot_ids = {
        "startup_context": _nested(startup, "snapshot_id"),
        "startup_push_decision": _nested(startup, "push_decision", "snapshot_id"),
        "review_state": _nested(review_state, "snapshot_id"),
        "review_state_commit_pipeline": _nested(
            review_state, "commit_pipeline", "snapshot_id"
        ),
        "review_state_doctor": _nested(review_state, "_compat", "doctor", "snapshot_id"),
        "review_state_bridge_projection": _nested(
            review_state,
            "_compat",
            "bridge_projection",
            "metadata",
            "snapshot_id",
        ),
        "compact": _nested(compact, "snapshot_id"),
        "compact_push_decision": _nested(compact, "push_decision", "snapshot_id"),
        "compact_doctor": _nested(compact, "doctor", "snapshot_id"),
        "commit_pipeline": _nested(commit_pipeline, "snapshot_id"),
    }
    generation_ids = {
        "review_state_commit_pipeline": _nested(review_state, "commit_pipeline", "generation_id"),
        "review_state_doctor": _nested(review_state, "_compat", "doctor", "generation_id"),
        "compact_doctor": _nested(compact, "doctor", "generation_id"),
        "commit_pipeline": _nested(commit_pipeline, "generation_id"),
    }
    nonempty_snapshots = sorted({value for value in snapshot_ids.values() if value})
    nonempty_generations = sorted({value for value in generation_ids.values() if value})
    errors: list[str] = []
    missing = [surface for surface, value in snapshot_ids.items() if not value]
    if missing:
        errors.append("missing snapshot_id on: " + ", ".join(sorted(missing)))
    if len(nonempty_snapshots) > 1:
        errors.append(
            "snapshot_id mismatch: " + ", ".join(nonempty_snapshots)
        )
    if len(nonempty_generations) > 1:
        errors.append(
            "pipeline generation mismatch: " + ", ".join(nonempty_generations)
        )
    return {
        "command": "check_review_surface_consistency",
        "ok": not errors,
        "snapshot_ids": snapshot_ids,
        "generation_ids": generation_ids,
        "errors": errors,
    }


def _surface_path(repo_root: Path, filename: str) -> Path:
    review_state_path = resolve_review_state_path(
        repo_root,
        governance=scan_repo_governance_safely(repo_root),
    )
    if review_state_path is None:
        return repo_root / filename
    return review_state_path.parent / filename


def _load_review_state_payload(repo_root: Path) -> dict[str, object]:
    review_state_path = resolve_review_state_path(
        repo_root,
        governance=scan_repo_governance_safely(repo_root),
    )
    return _load_json(review_state_path)


def _load_json(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _nested(payload: object, *keys: str) -> str:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return str(current or "").strip()


def _render_report(report: dict[str, object]) -> str:
    lines = ["# check_review_surface_consistency", ""]
    lines.append(f"- ok: {report.get('ok')}")
    for surface, snapshot_id in sorted((report.get("snapshot_ids") or {}).items()):
        lines.append(f"- {surface}: {snapshot_id or 'missing'}")
    errors = report.get("errors") or []
    if errors:
        lines.append("")
        lines.append("## Errors")
        for error in errors:
            lines.append(f"- {error}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_report(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
