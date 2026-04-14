"""Regression tests for ``derive_operator_interaction_mode`` (rev_pkt_0463).

Covers the canonical precedence shared by startup-context, control-plane
read model, launcher discipline, ensure-follow, and reviewer-supervisor
autostart. Asserts the iterate-all-candidates behavior rather than the
earlier short-circuit-on-governance shape so the rev_pkt_0463 repro
(governance=``local_terminal`` + collaboration=``remote_control`` + no
attachment -> expect ``remote_control``) is pinned.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from dev.scripts.devctl.runtime.operator_context import (
    derive_operator_interaction_mode,
)


def _gov(mode: str) -> SimpleNamespace:
    return SimpleNamespace(bridge_config=SimpleNamespace(operator_interaction_mode=mode))


class DeriveOperatorInteractionModeTests(unittest.TestCase):
    def test_rev_pkt_0463_repro_collaboration_overrides_local_terminal(self) -> None:
        """Governance=local_terminal + collaboration=remote_control -> remote_control."""
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "collaboration": {"operator_interaction_mode": "remote_control"},
            },
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "remote_control")

    def test_reviewer_runtime_mode_overrides_local_terminal(self) -> None:
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "reviewer_runtime": {"operator_interaction_mode": "remote_control"},
            },
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "remote_control")

    def test_receipt_mode_overrides_local_terminal(self) -> None:
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload=None,
            receipt={"operator_interaction_mode": "remote_control"},
            reviewer_mode="",
        )
        self.assertEqual(mode, "remote_control")

    def test_attachment_override_when_no_non_local_terminal_mode(self) -> None:
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "reviewer_runtime": {
                    "remote_control_attachment": {
                        "provider": "claude",
                        "session_name": "remote-control-test",
                        "status": "attached",
                    },
                },
            },
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "remote_control")

    def test_local_terminal_preserved_without_typed_overrides(self) -> None:
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={},
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "local_terminal")

    def test_single_agent_reviewer_mode_fallback(self) -> None:
        mode = derive_operator_interaction_mode(
            governance=None,
            review_state_payload=None,
            receipt=None,
            reviewer_mode="single_agent",
        )
        self.assertEqual(mode, "single_agent")

    def test_dual_agent_reviewer_mode_fallback(self) -> None:
        mode = derive_operator_interaction_mode(
            governance=None,
            review_state_payload=None,
            receipt=None,
            reviewer_mode="active_dual_agent",
        )
        self.assertEqual(mode, "dual_agent")

    def test_reviewer_mode_fallback_for_empty_signal(self) -> None:
        """Empty reviewer_mode string normalizes to active_dual_agent -> dual_agent.

        This is the existing behavior of ``normalize_reviewer_mode('')`` — empty
        input falls through to the dual-agent default. Document it here so
        future changes to that helper don't silently shift this reducer's
        fallback.
        """
        mode = derive_operator_interaction_mode(
            governance=None,
            review_state_payload=None,
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "dual_agent")


if __name__ == "__main__":
    unittest.main()
