"""Reusable receipt-state gates for typed lifecycle contracts."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

ReceiptT = TypeVar("ReceiptT")
StateT = TypeVar("StateT")


def require_receipt_state(
    receipt: ReceiptT | None,
    *,
    state_getter: Callable[[ReceiptT], StateT],
    required_state: StateT,
    error_factory: Callable[[], Exception],
    is_usable: Callable[[ReceiptT], bool] | None = None,
) -> ReceiptT:
    """Return a receipt only when it is in the required lifecycle state."""
    if receipt is not None and state_getter(receipt) == required_state:
        if is_usable is None or is_usable(receipt):
            return receipt
    raise error_factory()
