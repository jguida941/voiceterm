"""Algebraic result cases for BypassLifecycle activation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .bypass_lifecycle_models import (
    BypassLifecycle,
    BypassLifecycleState,
    BypassReceipt,
)
from .typing_compat import assert_never


@dataclass(frozen=True, slots=True)
class BypassActivated:
    """Algebraic success case over the canonical BypassLifecycle contract."""

    lifecycle: BypassLifecycle
    receipt: BypassReceipt
    governed_exception_lifecycle_id: str
    kind: Literal["activated"] = "activated"


@dataclass(frozen=True, slots=True)
class BypassDenied:
    """Algebraic denial case over the canonical BypassLifecycle contract."""

    lifecycle: BypassLifecycle
    reason: str
    kind: Literal["denied"] = "denied"


BypassActivationResult = BypassActivated | BypassDenied


def bypass_activation_result(lifecycle: BypassLifecycle) -> BypassActivationResult:
    """Project the canonical lifecycle onto the request-evaluation result cases."""
    if lifecycle.state is BypassLifecycleState.ACTIVE:
        if lifecycle.receipt is None:
            raise ValueError("active_bypass_lifecycle_missing_receipt")
        return BypassActivated(
            lifecycle=lifecycle,
            receipt=lifecycle.receipt,
            governed_exception_lifecycle_id=(
                lifecycle.governed_exception.lifecycle_id
                if lifecycle.governed_exception is not None
                else lifecycle.evaluation.governed_exception_lifecycle_id
            ),
        )
    if lifecycle.state is BypassLifecycleState.DENIED:
        return BypassDenied(
            lifecycle=lifecycle,
            reason=lifecycle.evaluation.reason,
        )
    raise ValueError(f"unsupported_bypass_activation_state: {lifecycle.state}")


def bypass_activation_lifecycle(
    result: BypassActivationResult,
) -> BypassLifecycle:
    """Return the canonical lifecycle from an exhaustive activation result."""
    match result:
        case BypassActivated(lifecycle=lifecycle):
            return lifecycle
        case BypassDenied(lifecycle=lifecycle):
            return lifecycle
    assert_never(result)


__all__ = [
    "BypassActivated",
    "BypassActivationResult",
    "BypassDenied",
    "bypass_activation_lifecycle",
    "bypass_activation_result",
]
