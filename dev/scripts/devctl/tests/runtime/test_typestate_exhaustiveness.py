"""P102 typestate exhaustiveness fixture."""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Literal, assert_never

LifecycleState = Literal["requested", "active", "expired"]


@dataclass(frozen=True)
class LifecycleReceiptFixture:
    receipt_id: str
    state: LifecycleState


def render_lifecycle_state(receipt: LifecycleReceiptFixture) -> str:
    match receipt.state:
        case "requested":
            return "waiting_for_activation"
        case "active":
            return "usable"
        case "expired":
            return "closed"
    assert_never(receipt.state)


class TypestateExhaustivenessTests(unittest.TestCase):
    def test_render_lifecycle_state_handles_every_literal_state(self) -> None:
        cases: tuple[tuple[LifecycleState, str], ...] = (
            ("requested", "waiting_for_activation"),
            ("active", "usable"),
            ("expired", "closed"),
        )

        for state, expected in cases:
            receipt = LifecycleReceiptFixture(
                receipt_id=f"receipt:{state}",
                state=state,
            )
            self.assertEqual(render_lifecycle_state(receipt), expected)
