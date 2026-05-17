"""Tests for ReviewerModeAuthorityContract (P139 — closes rev_pkt_1335 chronic).

Defect addressed: three sources (`launch_authority.py:265-268` plus six
overwrite sites in `collaboration_session.py`) silently promoted
`effective_mode` over `declared_mode` without typed transition evidence.
This created TOCTOU oscillation across rounds.

These tests verify the typed authority contract:
  1. Declared mode wins without typed evidence.
  2. Authorized transition with typed evidence succeeds.
  3. Unauthorized transition falls back to declared.
  4. Evidence refs are recorded in the resolved state.
  5. The TOCTOU race is resolved by routing through the authority check.
"""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime.reviewer_mode import ReviewerMode
from dev.scripts.devctl.runtime.reviewer_mode_authority_contract import (
    ReviewerModeAuthorityState,
    is_transition_authorized,
    resolve_reviewer_mode_authority,
)


class TestReviewerModeAuthorityContract(unittest.TestCase):
    """Typed-authority test suite for reviewer_mode resolution."""

    def test_declared_mode_is_authority_without_evidence(self) -> None:
        """Without evidence refs the declared mode pins effective_mode."""
        state = resolve_reviewer_mode_authority(
            declared=ReviewerMode.TOOLS_ONLY.value,
            current_effective=ReviewerMode.ACTIVE_DUAL_AGENT.value,
            evidence_refs=(),
        )
        self.assertIsInstance(state, ReviewerModeAuthorityState)
        self.assertEqual(state.declared_mode, ReviewerMode.TOOLS_ONLY)
        self.assertEqual(state.effective_mode, ReviewerMode.TOOLS_ONLY)
        self.assertEqual(
            state.authority_source,
            "declared_mode_fallback_unauthorized_transition",
        )
        self.assertEqual(state.contract_id, "ReviewerModeAuthorityContract")
        self.assertEqual(state.schema_version, 1)

    def test_authorized_transition_with_typed_evidence_succeeds(self) -> None:
        """Activation with typed evidence is honoured."""
        state = resolve_reviewer_mode_authority(
            declared=ReviewerMode.TOOLS_ONLY.value,
            current_effective=ReviewerMode.ACTIVE_DUAL_AGENT.value,
            evidence_refs=("handshake://pkt_1335", "launch_authority://rev_42"),
        )
        self.assertEqual(state.declared_mode, ReviewerMode.TOOLS_ONLY)
        self.assertEqual(state.effective_mode, ReviewerMode.ACTIVE_DUAL_AGENT)
        self.assertEqual(state.authority_source, "authorized_transition")
        self.assertEqual(
            state.transition_evidence_refs,
            ("handshake://pkt_1335", "launch_authority://rev_42"),
        )

    def test_unauthorized_transition_falls_back_to_declared(self) -> None:
        """An edge not in the authorized set falls back even with evidence."""
        # OFFLINE -> ACTIVE_DUAL_AGENT is not an authorized edge.
        state = resolve_reviewer_mode_authority(
            declared=ReviewerMode.OFFLINE.value,
            current_effective=ReviewerMode.ACTIVE_DUAL_AGENT.value,
            evidence_refs=("handshake://pkt_x",),
        )
        self.assertEqual(state.effective_mode, ReviewerMode.OFFLINE)
        self.assertEqual(
            state.authority_source,
            "declared_mode_fallback_unauthorized_transition",
        )

    def test_evidence_refs_included_in_state(self) -> None:
        """Evidence refs are normalized (stripped, empties dropped) and recorded."""
        state = resolve_reviewer_mode_authority(
            declared=ReviewerMode.TOOLS_ONLY.value,
            current_effective=ReviewerMode.SINGLE_AGENT.value,
            evidence_refs=("  receipt://abc  ", "", "  "),
        )
        self.assertEqual(state.transition_evidence_refs, ("receipt://abc",))
        self.assertEqual(state.effective_mode, ReviewerMode.SINGLE_AGENT)
        self.assertEqual(state.authority_source, "authorized_transition")

    def test_toctou_race_resolved_by_authority_check(self) -> None:
        """Same declared mode resolves stably regardless of stale effective_mode."""
        # Simulate the chronic rev_pkt_1335 oscillation: bridge_liveness reports
        # stale active_dual_agent but declared mode is tools_only with no evidence.
        # Multiple resolutions must return the same authoritative effective_mode.
        results = []
        for stale_effective in (
            ReviewerMode.ACTIVE_DUAL_AGENT.value,
            ReviewerMode.SINGLE_AGENT.value,
            ReviewerMode.ACTIVE_DUAL_AGENT.value,
        ):
            state = resolve_reviewer_mode_authority(
                declared=ReviewerMode.TOOLS_ONLY.value,
                current_effective=stale_effective,
                evidence_refs=(),
            )
            results.append(state.effective_mode)
        self.assertEqual(
            results,
            [
                ReviewerMode.TOOLS_ONLY,
                ReviewerMode.TOOLS_ONLY,
                ReviewerMode.TOOLS_ONLY,
            ],
            "TOCTOU race: effective_mode must not oscillate without typed evidence",
        )
        self.assertTrue(
            is_transition_authorized(
                ReviewerMode.TOOLS_ONLY,
                ReviewerMode.ACTIVE_DUAL_AGENT,
                ("receipt://valid",),
            )
        )
        self.assertFalse(
            is_transition_authorized(
                ReviewerMode.TOOLS_ONLY,
                ReviewerMode.ACTIVE_DUAL_AGENT,
                (),
            )
        )


if __name__ == "__main__":
    unittest.main()
