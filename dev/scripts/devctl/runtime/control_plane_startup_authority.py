"""Startup-authority source selection for control-plane blocker routing."""

from __future__ import annotations

from typing import Any

from .value_coercion import coerce_bool, coerce_int, coerce_string


def startup_authority_from_receipt(
    receipt: dict[str, Any] | None,
) -> dict[str, Any]:
    """Project a startup receipt into blocker-reducer authority fields."""
    if not isinstance(receipt, dict):
        return {}
    return {
        "ok": receipt.get("startup_authority_ok", True),
        "startup_authority_ok": receipt.get("startup_authority_ok", True),
        "errors": receipt.get("startup_authority_errors", ()),
        "startup_authority_errors": receipt.get("startup_authority_errors", ()),
        "checkpoint_required": receipt.get("checkpoint_required", False),
        "safe_to_continue_editing": receipt.get("safe_to_continue_editing", True),
        "checkpoint_reason": receipt.get("push_reason")
        or receipt.get("advisory_reason"),
        "push_reason": receipt.get("push_reason"),
        "advisory_reason": receipt.get("advisory_reason"),
        "recommended_action": receipt.get("recommended_action"),
    }


def startup_authority_from_live_governance_or_receipt(
    *,
    governance: Any | None,
    receipt: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return live startup-authority state for control-plane reads.

    ``receipt.json`` is durable proof that startup-context ran, but it can lag
    the current index while an agent is actively staging a repair slice. The
    control plane is a live read model, so checkpoint state must come from the
    current ``ProjectGovernance.push_enforcement`` when available. Free-form
    receipt startup-authority errors are only carried forward when the receipt
    still matches those live checkpoint counters.
    """
    live = _startup_authority_from_governance(governance)
    if not live:
        return startup_authority_from_receipt(receipt)

    if _receipt_matches_live_startup_authority(receipt, live):
        merged = startup_authority_from_receipt(receipt)
        merged.update(live)
        return merged
    return live


def _startup_authority_from_governance(governance: Any | None) -> dict[str, Any]:
    push = getattr(governance, "push_enforcement", None)
    if push is None:
        return {}
    return {
        "checkpoint_required": bool(getattr(push, "checkpoint_required", False)),
        "safe_to_continue_editing": bool(
            getattr(push, "safe_to_continue_editing", True)
        ),
        "checkpoint_reason": coerce_string(
            getattr(push, "checkpoint_reason", "")
        ),
        "recommended_action": coerce_string(
            getattr(push, "recommended_action", "")
        ),
        "staged_path_count": coerce_int(getattr(push, "staged_path_count", 0)),
        "unstaged_path_count": coerce_int(getattr(push, "unstaged_path_count", 0)),
    }


def _receipt_matches_live_startup_authority(
    receipt: dict[str, Any] | None,
    live: dict[str, Any],
) -> bool:
    if not isinstance(receipt, dict):
        return False
    return (
        coerce_bool(receipt.get("checkpoint_required"))
        == coerce_bool(live.get("checkpoint_required"))
        and coerce_bool(receipt.get("safe_to_continue_editing", True))
        == coerce_bool(live.get("safe_to_continue_editing", True))
        and coerce_int(receipt.get("staged_path_count"))
        == coerce_int(live.get("staged_path_count"))
        and coerce_int(receipt.get("unstaged_path_count"))
        == coerce_int(live.get("unstaged_path_count"))
    )


__all__ = [
    "startup_authority_from_live_governance_or_receipt",
    "startup_authority_from_receipt",
]
