"""Recovery-authority helpers for startup-context render surfaces."""

from __future__ import annotations

from ...runtime.recovery_authority import RecoveryAuthorityState


def append_recovery_authority_summary_lines(
    ctx_dict: dict[str, object],
    lines: list[str],
) -> None:
    """Append compact recovery authority fields to summary output."""
    for field_name in ("recovery_action", "recovery_basis", "recovery_scope"):
        value = str(ctx_dict.get(field_name) or "").strip()
        if value:
            lines.append(f"{field_name}={value}")


def recovery_authority_payload(ctx: object) -> dict[str, object]:
    """Return a serializable recovery authority payload for machine output."""
    authority = getattr(ctx, "recovery_authority", None)
    if authority is not None and hasattr(authority, "to_dict"):
        payload = authority.to_dict()
        if isinstance(payload, dict):
            return payload
    return RecoveryAuthorityState(reason="no_recovery_assessment").to_dict()


def apply_recovery_authority_summary(
    summary: dict[str, object],
    ctx: object,
) -> None:
    """Project recovery authority fields into a machine summary mapping."""
    payload = recovery_authority_payload(ctx)
    summary["recovery_action"] = payload.get("recovery_action", "none")
    summary["recovery_basis"] = payload.get("recovery_basis", "none")
    summary["recovery_scope"] = payload.get("recovery_scope", "this_session")
    summary["recovery_authority"] = payload
