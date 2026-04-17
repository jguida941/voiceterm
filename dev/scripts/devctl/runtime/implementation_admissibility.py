"""Shared reducer for implementation mutability on the current control tick."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

ImplementationAdmissibility = Literal["allowed", "checkpoint_required", "blocked"]


@dataclass(frozen=True, slots=True)
class ImplementationAdmissibilityState:
    """Single typed answer to whether implementation mutation may proceed."""

    schema_version: int = 1
    contract_id: str = "ImplementationAdmissibility"
    status: ImplementationAdmissibility = "allowed"
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        return payload


def derive_implementation_admissibility(
    *,
    implementation_permission: object = "",
    checkpoint_required: object = False,
    safe_to_continue_editing: object = True,
    resync_required: object = False,
) -> ImplementationAdmissibilityState:
    """Return one bounded mutation answer from startup/runtime authority."""
    reasons: list[str] = []
    permission = str(implementation_permission or "").strip()
    checkpoint = bool(checkpoint_required)
    safe = bool(safe_to_continue_editing)
    resync = bool(resync_required)

    if resync:
        reasons.append("coordination_resync_required")
    if not permission:
        reasons.append("implementation_permission_missing")
    if permission in {"blocked", "suspended"}:
        reasons.append(f"implementation_permission_{permission}")
    if checkpoint:
        reasons.append("checkpoint_required")
    if not safe:
        reasons.append("safe_to_continue_editing_false")

    if resync or not permission or permission in {"blocked", "suspended"}:
        status: ImplementationAdmissibility = "blocked"
    elif checkpoint or not safe:
        status = "checkpoint_required"
    else:
        status = "allowed"

    return ImplementationAdmissibilityState(
        status=status,
        reasons=tuple(reasons),
    )


__all__ = [
    "ImplementationAdmissibility",
    "ImplementationAdmissibilityState",
    "derive_implementation_admissibility",
]
