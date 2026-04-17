"""Support helpers for startup action-routing checkpoints and review gates."""

from __future__ import annotations

from collections.abc import Mapping
from types import SimpleNamespace


def commit_permission_context(
    *,
    ctx_payload: Mapping[str, object],
    implementation_permission: str,
) -> SimpleNamespace:
    reviewer_gate = reviewer_gate_payload(ctx_payload)
    push = push_enforcement(ctx_payload)
    push_action = str(_mapping(ctx_payload.get("push_decision")).get("action") or "").strip()
    coordination = _mapping(ctx_payload.get("coordination"))
    observed_topology = str(
        ctx_payload.get("observed_control_topology")
        or coordination.get("observed_topology")
        or ""
    ).strip()
    governance = (
        SimpleNamespace(
            push_enforcement=SimpleNamespace(
                checkpoint_required=bool(push.get("checkpoint_required", False)),
                safe_to_continue_editing=push_safe_to_continue(push),
            )
        )
        if push
        else None
    )
    return SimpleNamespace(
        implementation_permission=implementation_permission,
        observed_control_topology=observed_topology,
        reviewer_gate=(
            SimpleNamespace(
                review_gate_allows_push=bool(
                    reviewer_gate.get("review_gate_allows_push", False)
                ),
                implementation_blocked=bool(
                    reviewer_gate.get("implementation_blocked", False)
                ),
                implementation_block_reason=str(
                    reviewer_gate.get("implementation_block_reason") or ""
                ).strip(),
                checkpoint_permitted=bool(
                    reviewer_gate.get("checkpoint_permitted", True)
                ),
            )
            if reviewer_gate is not None
            else None
        ),
        governance=governance,
        push_decision=SimpleNamespace(action=push_action),
        advisory_action=str(ctx_payload.get("advisory_action") or "").strip(),
    )


def push_enforcement(ctx_payload: Mapping[str, object]) -> Mapping[str, object]:
    governance = _mapping(ctx_payload.get("governance"))
    push = _mapping(governance.get("push_enforcement"))
    if push:
        return push
    bridge_liveness = _mapping(ctx_payload.get("bridge_liveness"))
    return _mapping(bridge_liveness.get("push_enforcement"))


def push_safe_to_continue(push_payload: Mapping[str, object]) -> bool:
    safe_to_continue = push_payload.get("safe_to_continue_editing")
    if safe_to_continue is None:
        return not bool(push_payload.get("checkpoint_required", False))
    return bool(safe_to_continue)


def checkpoint_commit_allowed(
    *,
    ctx_payload: Mapping[str, object],
    implementation_permission: str,
) -> bool:
    reviewer_gate = reviewer_gate_payload(ctx_payload)
    if reviewer_gate is None:
        return False
    if implementation_permission not in {"blocked", "suspended"}:
        return False
    if not bool(reviewer_gate.get("checkpoint_permitted", True)):
        return False
    if review_authority(reviewer_gate) not in {"valid", "stale"}:
        return False

    push_action = str(_mapping(ctx_payload.get("push_decision")).get("action") or "").strip()
    advisory_action = str(ctx_payload.get("advisory_action") or "").strip()
    return push_action == "await_checkpoint" or advisory_action in {
        "checkpoint_allowed",
        "checkpoint_before_continue",
    }


def review_authority(reviewer_gate: Mapping[str, object]) -> str:
    if bool(reviewer_gate.get("review_gate_allows_push", False)):
        return "valid"
    if bool(reviewer_gate.get("implementation_blocked", False)):
        reason = str(reviewer_gate.get("implementation_block_reason") or "").strip()
        if reason == "checkpoint_required":
            return "valid"
        return "stale" if reason else "missing"
    return "valid"


def reviewer_gate_payload(
    ctx_payload: Mapping[str, object],
) -> Mapping[str, object] | None:
    reviewer_gate = _mapping(ctx_payload.get("reviewer_gate"))
    if reviewer_gate:
        return reviewer_gate
    reviewer_runtime = _mapping(ctx_payload.get("reviewer_runtime"))
    if reviewer_runtime:
        return {
            "review_gate_allows_push": bool(reviewer_runtime.get("publish_clear", False)),
            "implementation_blocked": bool(
                reviewer_runtime.get("implementation_blocked", False)
            ),
            "implementation_block_reason": str(
                reviewer_runtime.get("implementation_block_reason") or ""
            ).strip(),
            "checkpoint_permitted": True,
        }
    doctor = _mapping(ctx_payload.get("doctor"))
    if doctor:
        return {
            "review_gate_allows_push": bool(doctor.get("publish_clear", False)),
            "implementation_blocked": bool(doctor.get("implementation_blocked", False)),
            "implementation_block_reason": str(
                doctor.get("implementation_block_reason") or ""
            ).strip(),
            "checkpoint_permitted": True,
        }
    return None


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
