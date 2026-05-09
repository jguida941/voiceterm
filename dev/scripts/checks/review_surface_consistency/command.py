"""Verify startup/review/compact pipeline surfaces share one snapshot stamp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dev.scripts.devctl.runtime.startup_context import build_startup_context
from dev.scripts.devctl.runtime.review_state_parser import review_state_from_payload
from dev.scripts.devctl.runtime.validation_scope import (
    add_validation_scope_argument,
    apply_validation_scope_to_report,
    validation_scope_from_args,
)

from .models import ConvergencePassResult
from .parity import (
    bridge_poll_parity_violations,
    disk_turn_authority_parity_errors,
    disk_turn_authority_parity_violations,
    recovery_surface_parity_violations,
)
from .payloads import load_bridge_poll_payload, load_turn_authority_payload
from .proof_tick import proof_tick_field_parity_violations, proof_tick_fields
from .snapshot_fields import (
    generation_ids as surface_generation_ids,
    provenance_errors,
    provenance_payloads,
    snapshot_errors,
    snapshot_ids as surface_snapshot_ids,
    zrefs as surface_zrefs,
)
from .support import _load_json, _nested, load_review_state_payload, surface_path

_UNSET = object()


def build_report(
    *,
    repo_root: Path = Path(__file__).resolve().parents[4],
    disk_review_state_payload: dict[str, object] | None = _UNSET,
    **payload_overrides: object,
) -> dict[str, object]:
    startup_payload = _payload_override(payload_overrides, "startup_payload")
    review_state_payload = _payload_override(payload_overrides, "review_state_payload")
    compact_payload = _payload_override(payload_overrides, "compact_payload")
    commit_pipeline_payload = _payload_override(
        payload_overrides, "commit_pipeline_payload"
    )
    bridge_poll_payload = _payload_override(payload_overrides, "bridge_poll_payload")
    turn_authority_payload = _payload_override(payload_overrides, "turn_authority_payload")
    control_plane_payload = _payload_override(payload_overrides, "control_plane_payload")
    session_resume_payload = _payload_override(payload_overrides, "session_resume_payload")
    status_payload = _payload_override(payload_overrides, "status_payload")
    registry_payload = _payload_override(payload_overrides, "registry_payload")
    bridge_compat_payload = _payload_override(payload_overrides, "bridge_compat_payload")
    if payload_overrides:
        unexpected = ", ".join(sorted(payload_overrides))
        raise TypeError(f"unexpected payload override(s): {unexpected}")
    review_state = review_state_payload or load_review_state_payload(repo_root)
    startup = startup_payload
    if startup is None:
        typed_review_state = (
            review_state_from_payload(review_state)
            if isinstance(review_state, dict)
            else None
        )
        startup = build_startup_context(
            repo_root=repo_root,
            review_state=typed_review_state,
            caller_role="observer",
        ).to_dict()
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
    snapshot_ids = surface_snapshot_ids(
        startup=startup,
        review_state=review_state,
        compact=compact,
        commit_pipeline=commit_pipeline,
        bridge_poll=bridge_poll,
        turn_authority=turn_authority,
    )
    zrefs = surface_zrefs(
        startup=startup,
        review_state=review_state,
        compact=compact,
        commit_pipeline=commit_pipeline,
        bridge_poll=bridge_poll,
        turn_authority=turn_authority,
    )
    generation_ids = surface_generation_ids(
        review_state=review_state,
        compact=compact,
        commit_pipeline=commit_pipeline,
    )
    provenance = provenance_payloads(review_state=review_state)
    proof_tick_surfaces = _proof_tick_surfaces(
        startup=startup,
        review_state=review_state,
        compact=compact,
        commit_pipeline=commit_pipeline,
        bridge_poll=bridge_poll,
        turn_authority=turn_authority,
        control_plane=control_plane_payload,
        session_resume=session_resume_payload,
        status=status_payload,
        registry=registry_payload,
        bridge_compat=bridge_compat_payload,
    )
    errors = snapshot_errors(snapshot_ids, zrefs, generation_ids)
    errors.extend(provenance_errors(provenance))
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
    violations.extend(
        proof_tick_field_parity_violations(
            proof_tick_surfaces,
            ignored_fields=_dynamic_proof_tick_fields(startup),
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
        zrefs=zrefs,
        generation_ids=generation_ids,
        provenance=provenance,
        proof_tick_fields=proof_tick_fields(proof_tick_surfaces),
        bridge_poll=bridge_poll,
        turn_authority=turn_authority,
        disk_parity_warnings=tuple(disk_warnings),
        errors=tuple(errors),
        violations=tuple(violations),
    ).to_dict()


def _proof_tick_surfaces(
    *,
    startup: dict[str, object],
    review_state: dict[str, object],
    compact: dict[str, object],
    commit_pipeline: dict[str, object],
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
    control_plane: dict[str, object] | None,
    session_resume: dict[str, object] | None,
    status: dict[str, object] | None,
    registry: dict[str, object] | None,
    bridge_compat: dict[str, object] | None,
) -> dict[str, dict[str, object]]:
    surfaces = {
        "coordination_snapshot": _nested_payload(review_state, "coordination"),
        "authority_snapshot": _nested_payload(review_state, "authority_snapshot"),
        "control_plane_read_model": control_plane or {},
        "startup_context": startup,
        "session_resume": session_resume or {},
        "review_channel_status": status or {},
        "persisted_review_state": review_state,
        "registry_agents": registry or _nested_payload(review_state, "registry"),
        "bridge_compat": bridge_compat or bridge_poll or turn_authority,
        "compact_projection": compact,
        "commit_pipeline": commit_pipeline,
    }
    return {
        surface: payload
        for surface, payload in surfaces.items()
        if isinstance(payload, dict) and payload
    }


def _dynamic_proof_tick_fields(startup: dict[str, object]) -> tuple[str, ...]:
    ownership_status = _nested(startup, "coordination", "ownership_status")
    if ownership_status == "scope_unknown_dirty_paths":
        return ("next_command", "ownership_status")
    return ()


def _nested_payload(payload: object, *keys: str) -> dict[str, object]:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return dict(current) if isinstance(current, dict) else {}


def _payload_override(
    payload_overrides: dict[str, object],
    key: str,
) -> dict[str, object] | None:
    value = payload_overrides.pop(key, None)
    return value if isinstance(value, dict) else None


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
    for surface, zref in sorted((report.get("zrefs") or {}).items()):
        lines.append(f"- {surface}.zref: {zref or 'missing'}")
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
    add_validation_scope_argument(parser)
    return parser.parse_args(argv)


def _emit_report(report: dict[str, object], *, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(_render_report(report))


def main() -> int:
    args = _parse_args()
    report = build_report()
    report = apply_validation_scope_to_report(
        report,
        validation_scope_from_args(args),
        reason=(
            "review-surface consistency compares live projection proof ticks; "
            "governed publication validation records it as advisory evidence."
        ),
    )
    _emit_report(report, output_format=args.format)
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
