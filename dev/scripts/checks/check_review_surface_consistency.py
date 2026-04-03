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
from dev.scripts.devctl.commands.review_channel._bridge_poll_support import (
    build_bridge_poll_result,
)
from dev.scripts.devctl.review_channel.handoff import (
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from dev.scripts.devctl.review_channel.heartbeat import compute_non_audit_worktree_hash
from dev.scripts.devctl.review_channel.turn_authority import build_reviewer_turn_authority


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    startup_payload: dict[str, object] | None = None,
    review_state_payload: dict[str, object] | None = None,
    compact_payload: dict[str, object] | None = None,
    commit_pipeline_payload: dict[str, object] | None = None,
    bridge_poll_payload: dict[str, object] | None = None,
    turn_authority_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    startup = startup_payload or build_startup_context(repo_root=repo_root).to_dict()
    review_state = review_state_payload or _load_review_state_payload(repo_root)
    compact = compact_payload or _load_json(_surface_path(repo_root, "compact.json"))
    commit_pipeline = commit_pipeline_payload or _load_json(
        _surface_path(repo_root, "commit_pipeline.json")
    )
    bridge_poll = bridge_poll_payload or _load_bridge_poll_payload(
        repo_root=repo_root,
        review_state_payload=review_state,
    )
    turn_authority = turn_authority_payload or _load_turn_authority_payload(
        repo_root=repo_root,
        review_state_payload=review_state,
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
        "bridge_poll": _nested(bridge_poll, "snapshot_id"),
        "turn_authority": _nested(turn_authority, "snapshot_id"),
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
    errors.extend(_bridge_poll_parity_errors(bridge_poll, turn_authority))
    return {
        "command": "check_review_surface_consistency",
        "ok": not errors,
        "snapshot_ids": snapshot_ids,
        "generation_ids": generation_ids,
        "bridge_poll": bridge_poll,
        "turn_authority": turn_authority,
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


def _load_bridge_poll_payload(
    *,
    repo_root: Path,
    review_state_payload: dict[str, object],
) -> dict[str, object]:
    bridge_text, current_worktree_hash = _bridge_runtime_inputs(
        repo_root=repo_root,
        review_state_payload=review_state_payload,
    )
    if not bridge_text:
        return {}
    return build_bridge_poll_result(
        bridge_text,
        current_worktree_hash=current_worktree_hash,
        typed_review_state=review_state_payload,
    ).to_dict()


def _load_turn_authority_payload(
    *,
    repo_root: Path,
    review_state_payload: dict[str, object],
) -> dict[str, object]:
    bridge_text, current_worktree_hash = _bridge_runtime_inputs(
        repo_root=repo_root,
        review_state_payload=review_state_payload,
    )
    if not bridge_text:
        return {}
    snapshot = extract_bridge_snapshot(bridge_text)
    bridge_liveness = summarize_bridge_liveness(
        snapshot,
        current_worktree_hash=current_worktree_hash,
    )
    return build_reviewer_turn_authority(
        snapshot=snapshot,
        bridge_liveness=bridge_liveness,
        typed_review_state=review_state_payload,
    ).to_dict()


def _bridge_runtime_inputs(
    *,
    repo_root: Path,
    review_state_payload: dict[str, object],
) -> tuple[str, str | None]:
    bridge_path = _resolve_bridge_path(repo_root=repo_root, review_state_payload=review_state_payload)
    if bridge_path is None or not bridge_path.exists():
        return "", None
    try:
        bridge_text = bridge_path.read_text(encoding="utf-8")
    except OSError:
        return "", None
    return bridge_text, _current_worktree_hash(repo_root=repo_root, bridge_path=bridge_path)


def _resolve_bridge_path(
    *,
    repo_root: Path,
    review_state_payload: dict[str, object],
) -> Path | None:
    bridge_rel = _nested(review_state_payload, "review", "bridge_path")
    if bridge_rel:
        return repo_root / bridge_rel
    return repo_root / "bridge.md"


def _current_worktree_hash(*, repo_root: Path, bridge_path: Path) -> str | None:
    try:
        bridge_rel = str(bridge_path.relative_to(repo_root))
    except ValueError:
        bridge_rel = bridge_path.name
    try:
        return compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=(bridge_rel,),
        )
    except (OSError, ValueError):
        return None


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


def _bridge_poll_parity_errors(
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> list[str]:
    if not bridge_poll or not turn_authority:
        return []
    errors: list[str] = []
    for field in (
        "effective_reviewer_mode",
        "launch_truth",
        "attention_status",
        "recovery_action_allowed",
        "implementation_blocked",
        "implementation_block_reason",
        "reviewed_hash_current",
        "review_needed",
        "next_turn_required",
        "next_turn_role",
        "next_turn_reason",
    ):
        if bridge_poll.get(field) != turn_authority.get(field):
            errors.append(
                "bridge-poll parity mismatch on "
                f"{field}: bridge-poll={bridge_poll.get(field)!r}, "
                f"turn-authority={turn_authority.get(field)!r}"
            )
    return errors


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
