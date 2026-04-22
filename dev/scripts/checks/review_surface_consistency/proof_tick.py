"""Proof-tick parity checks for review-surface consistency reporting."""

from __future__ import annotations

from .models import ConvergencePassViolation
from .parity import _nested

_PROOF_TICK_FIELDS = (
    "reviewer_mode",
    "effective_reviewer_mode",
    "observed_control_topology",
    "current_instruction_revision",
    "ownership_status",
    "implementation_permission",
    "next_command",
    "snapshot_id",
    "generation_id",
    "head_sha",
    "worktree_hash",
    "zref",
)
_PROOF_TICK_FIELD_PATHS: dict[str, tuple[tuple[str, ...], ...]] = {
    "reviewer_mode": (("reviewer_mode",), ("reviewer_gate", "reviewer_mode")),
    "effective_reviewer_mode": (
        ("effective_reviewer_mode",),
        ("reviewer_gate", "effective_reviewer_mode"),
        ("reviewer_runtime", "effective_reviewer_mode"),
    ),
    "observed_control_topology": (
        ("observed_control_topology",),
        ("coordination", "observed_topology"),
        ("observed_topology",),
    ),
    "current_instruction_revision": (
        ("current_instruction_revision",),
        ("instruction_revision",),
        ("current_session", "current_instruction_revision"),
        ("authority_snapshot", "current_instruction_revision"),
    ),
    "ownership_status": (
        ("ownership_status",),
        ("coordination", "ownership_status"),
    ),
    "implementation_permission": (
        ("implementation_permission",),
        ("work_intake", "coordination", "implementation_permission"),
        ("authority_snapshot", "implementation_permission"),
    ),
    "next_command": (
        ("next_command",),
        ("next_recommended_command",),
        ("authority_snapshot", "next_command"),
        ("action_routing", "next_command"),
        ("push_decision", "next_step_command"),
    ),
    "snapshot_id": (("snapshot_id",), ("authority_snapshot", "snapshot_id")),
    "generation_id": (
        ("generation_id",),
        ("source_identity", "generation_id"),
        ("commit_pipeline", "generation_id"),
    ),
    # ``commit_sha`` on RemoteCommitPipelineContract is the approved content
    # commit. Snapshot receipt commits legitimately move the proof-tick HEAD.
    "head_sha": (
        ("head_sha",),
        ("head_commit_sha",),
        ("head_commit",),
        ("source_identity", "head_sha"),
    ),
    "worktree_hash": (
        ("worktree_hash",),
        ("source_identity", "worktree_hash"),
        ("worktree_identity",),
        ("bridge", "last_worktree_hash"),
    ),
    "zref": (("zref",), ("authority_snapshot", "zref")),
}


def proof_tick_field_parity_violations(
    surfaces: dict[str, dict[str, object]],
    *,
    ignored_fields: tuple[str, ...] = (),
) -> list[ConvergencePassViolation]:
    """Compare Phase 0 proof-tick fields across all surfaces that expose them."""
    rows = {
        surface: _proof_tick_fields(payload)
        for surface, payload in surfaces.items()
        if isinstance(payload, dict) and payload
    }
    violations: list[ConvergencePassViolation] = []
    for field in _PROOF_TICK_FIELDS:
        if field in ignored_fields:
            continue
        values = {
            surface: value
            for surface, payload in rows.items()
            if (value := payload.get(field, "")) != ""
        }
        if len(set(values.values())) <= 1:
            continue
        expected = next(iter(values.values()))
        for surface, actual in values.items():
            if actual == expected:
                continue
            violations.append(
                ConvergencePassViolation(
                    category="proof_tick_field_parity",
                    surface=surface,
                    field=field,
                    expected=expected,
                    actual=actual,
                    detail=(
                        f"proof-tick parity mismatch on {field}: "
                        f"{surface}={actual!r}, expected={expected!r}"
                    ),
                )
            )
    return violations


def proof_tick_fields(
    surfaces: dict[str, dict[str, object]],
) -> dict[str, dict[str, str]]:
    """Return normalized proof-tick fields for report/debug output."""
    return {
        surface: _proof_tick_fields(payload)
        for surface, payload in surfaces.items()
        if isinstance(payload, dict) and payload
    }


def _proof_tick_fields(payload: dict[str, object]) -> dict[str, str]:
    return {
        field: _first_nested(payload, paths)
        for field, paths in _PROOF_TICK_FIELD_PATHS.items()
    }


def _first_nested(
    mapping: dict[str, object],
    paths: tuple[tuple[str, ...], ...],
) -> str:
    for path in paths:
        value = _nested(mapping, *path)
        if value:
            return value
    return ""
