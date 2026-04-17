"""Verify startup/review/compact pipeline surfaces share one snapshot stamp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dev.scripts.devctl.runtime.startup_context import build_startup_context

from .models import ConvergencePassResult
from .parity import (
    bridge_poll_parity_violations,
    disk_turn_authority_parity_errors,
    disk_turn_authority_parity_violations,
    recovery_surface_parity_violations,
)
from .payloads import load_bridge_poll_payload, load_turn_authority_payload
from .support import _load_json, _nested, load_review_state_payload, surface_path

_UNSET = object()


def build_report(
    *,
    repo_root: Path = Path(__file__).resolve().parents[4],
    startup_payload: dict[str, object] | None = None,
    review_state_payload: dict[str, object] | None = None,
    compact_payload: dict[str, object] | None = None,
    commit_pipeline_payload: dict[str, object] | None = None,
    bridge_poll_payload: dict[str, object] | None = None,
    turn_authority_payload: dict[str, object] | None = None,
    disk_review_state_payload: dict[str, object] | None = _UNSET,
) -> dict[str, object]:
    startup = startup_payload or build_startup_context(repo_root=repo_root).to_dict()
    review_state = review_state_payload or load_review_state_payload(repo_root)
    compact = compact_payload or _load_json(surface_path(repo_root, "compact.json"))
    commit_pipeline = commit_pipeline_payload or _load_json(
        surface_path(repo_root, "commit_pipeline.json")
    )
    bridge_poll = bridge_poll_payload or load_bridge_poll_payload(
        repo_root=repo_root,
        review_state_payload=review_state,
    )
    turn_authority = turn_authority_payload or load_turn_authority_payload(
        repo_root=repo_root,
        review_state_payload=review_state,
    )
    snapshot_ids = _snapshot_ids(
        startup=startup,
        review_state=review_state,
        compact=compact,
        commit_pipeline=commit_pipeline,
        bridge_poll=bridge_poll,
        turn_authority=turn_authority,
    )
    generation_ids = _generation_ids(
        review_state=review_state,
        compact=compact,
        commit_pipeline=commit_pipeline,
    )
    errors = _snapshot_errors(snapshot_ids, generation_ids)
    violations = [
        _raw_error_violation(error)
        for error in errors
    ]
    violations.extend(
        bridge_poll_parity_violations(
            bridge_poll=bridge_poll,
            turn_authority=turn_authority,
        )
    )
    violations.extend(
        recovery_surface_parity_violations(
            review_state=review_state,
            compact=compact,
            bridge_poll=bridge_poll,
            turn_authority=turn_authority,
        )
    )
    disk_violations, disk_warnings = disk_turn_authority_parity_violations(
        repo_root=repo_root,
        turn_authority=turn_authority,
        bridge_poll=bridge_poll,
        disk_review_state_override=(
            None if disk_review_state_payload is _UNSET else disk_review_state_payload
        ),
        disk_override_provided=disk_review_state_payload is not _UNSET,
    )
    violations.extend(disk_violations)
    errors = [violation.detail for violation in violations]
    return ConvergencePassResult(
        ok=not errors,
        snapshot_ids=snapshot_ids,
        generation_ids=generation_ids,
        bridge_poll=bridge_poll,
        turn_authority=turn_authority,
        disk_parity_warnings=tuple(disk_warnings),
        errors=tuple(errors),
        violations=tuple(violations),
    ).to_dict()


def _disk_turn_authority_parity_errors(
    *,
    repo_root: Path,
    turn_authority: dict[str, object],
    bridge_poll: dict[str, object],
    disk_review_state_override: dict[str, object] | None = None,
    disk_override_provided: bool = False,
) -> tuple[list[str], list[str]]:
    return disk_turn_authority_parity_errors(
        repo_root=repo_root,
        turn_authority=turn_authority,
        bridge_poll=bridge_poll,
        disk_review_state_override=disk_review_state_override,
        disk_override_provided=disk_override_provided,
    )


def _snapshot_ids(
    *,
    startup: dict[str, object],
    review_state: dict[str, object],
    compact: dict[str, object],
    commit_pipeline: dict[str, object],
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> dict[str, str]:
    return {
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


def _generation_ids(
    *,
    review_state: dict[str, object],
    compact: dict[str, object],
    commit_pipeline: dict[str, object],
) -> dict[str, str]:
    return {
        "review_state_commit_pipeline": _nested(review_state, "commit_pipeline", "generation_id"),
        "review_state_doctor": _nested(review_state, "_compat", "doctor", "generation_id"),
        "compact_doctor": _nested(compact, "doctor", "generation_id"),
        "commit_pipeline": _nested(commit_pipeline, "generation_id"),
    }


def _snapshot_errors(
    snapshot_ids: dict[str, str],
    generation_ids: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    missing = [surface for surface, value in snapshot_ids.items() if not value]
    if missing:
        errors.append("missing snapshot_id on: " + ", ".join(sorted(missing)))
    nonempty_snapshots = sorted({value for value in snapshot_ids.values() if value})
    nonempty_generations = sorted({value for value in generation_ids.values() if value})
    if len(nonempty_snapshots) > 1:
        errors.append("snapshot_id mismatch: " + ", ".join(nonempty_snapshots))
    if len(nonempty_generations) > 1:
        errors.append("pipeline generation mismatch: " + ", ".join(nonempty_generations))
    return errors


def _raw_error_violation(error: str):
    from .models import ConvergencePassViolation

    return ConvergencePassViolation(
        category="snapshot_consistency",
        detail=error,
    )


def _render_report(report: dict[str, object]) -> str:
    lines = ["# check_review_surface_consistency", ""]
    lines.append(f"- ok: {report.get('ok')}")
    for surface, snapshot_id in sorted((report.get("snapshot_ids") or {}).items()):
        lines.append(f"- {surface}: {snapshot_id or 'missing'}")
    disk_warnings = report.get("disk_parity_warnings") or []
    if disk_warnings:
        lines.append("")
        lines.append("## Disk Parity Warnings")
        for warning in disk_warnings:
            lines.append(f"- {warning}")
    errors = report.get("errors") or []
    if errors:
        lines.append("")
        lines.append("## Errors")
        for error in errors:
            lines.append(f"- {error}")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser.parse_args(argv)


def _emit_report(report: dict[str, object], *, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(_render_report(report))


def main() -> int:
    args = _parse_args()
    report = build_report()
    _emit_report(report, output_format=args.format)
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
