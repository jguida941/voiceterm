"""Tests for reusable receipt-state lifecycle gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pytest

from dev.scripts.devctl.runtime.receipt_state_gate import require_receipt_state

ReceiptState = Literal["requested", "active", "expired"]


class ReceiptStateRequired(ValueError):
    pass


@dataclass(frozen=True)
class ReceiptFixture:
    state: ReceiptState
    usable: bool = True


def _required_state_error() -> ReceiptStateRequired:
    return ReceiptStateRequired("active receipt required")


def test_require_receipt_state_returns_matching_usable_receipt() -> None:
    receipt = ReceiptFixture(state="active")

    resolved = require_receipt_state(
        receipt,
        state_getter=lambda item: item.state,
        required_state="active",
        is_usable=lambda item: item.usable,
        error_factory=_required_state_error,
    )

    assert resolved is receipt


@pytest.mark.parametrize(
    "receipt",
    (
        None,
        ReceiptFixture(state="requested"),
        ReceiptFixture(state="active", usable=False),
    ),
)
def test_require_receipt_state_rejects_missing_wrong_or_unusable_receipts(
    receipt: ReceiptFixture | None,
) -> None:
    with pytest.raises(ReceiptStateRequired, match="active receipt required"):
        require_receipt_state(
            receipt,
            state_getter=lambda item: item.state,
            required_state="active",
            is_usable=lambda item: item.usable,
            error_factory=_required_state_error,
        )
