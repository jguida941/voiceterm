"""Tests for the startup-context advisory_action coherence contract.

Codex flagged a P1 where the startup receipt could advertise
``advisory_action=push_allowed`` alongside
``blockers=coordination_resync_required`` (or
``implementation_permission_blocked``) and a downgraded
``next_command=review-channel --action status``. Those three fields
are supposed to describe the same typed state, so the contradiction
made the summary receipt unreliable for the publish slice it was
supposed to authorize.

These tests pin the Path A fix: whenever the typed blocker list is
non-empty, the coerced ``advisory_action`` must not be ``push_allowed``.
They exercise the pure coercion helper and the shared blocker reader
so the contract is easy to reason about without standing up a full
``build_startup_context`` fixture tree.
"""

from __future__ import annotations

import unittest

from dev.scripts.devctl.commands.governance.startup_context import _summary_blockers
from dev.scripts.devctl.commands.governance.startup_context_advisory_coherence import (
    coerce_advisory_for_blockers as _coerce_advisory_for_blockers,
)


class CoerceAdvisoryForBlockersTests(unittest.TestCase):
    """Low-level: the pure coercion rule holds under typed blocker inputs."""

    def test_no_blockers_leaves_push_allowed_intact(self) -> None:
        action, reason = _coerce_advisory_for_blockers(
            "push_allowed",
            "worktree_clean_and_review_accepted",
            "none",
        )

        self.assertEqual(action, "push_allowed")
        self.assertEqual(reason, "worktree_clean_and_review_accepted")

    def test_non_push_allowed_action_is_not_mutated(self) -> None:
        """The coercion only fires against the contradiction case."""
        action, reason = _coerce_advisory_for_blockers(
            "checkpoint_allowed",
            "worktree_dirty_within_budget",
            "checkpoint_required",
        )

        self.assertEqual(action, "checkpoint_allowed")
        self.assertEqual(reason, "worktree_dirty_within_budget")

    def test_coordination_resync_blocker_downgrades_push_allowed(self) -> None:
        action, reason = _coerce_advisory_for_blockers(
            "push_allowed",
            "worktree_clean_and_review_accepted",
            "coordination_resync_required",
        )

        self.assertNotEqual(action, "push_allowed")
        self.assertEqual(action, "repair_reviewer_loop")
        self.assertIn("coordination_resync_required", reason)

    def test_implementation_permission_blocked_downgrades_push_allowed(self) -> None:
        action, reason = _coerce_advisory_for_blockers(
            "push_allowed",
            "worktree_clean_and_review_accepted",
            "implementation_permission_blocked",
        )

        self.assertNotEqual(action, "push_allowed")
        self.assertEqual(action, "repair_reviewer_loop")
        self.assertIn("implementation_permission_blocked", reason)

    def test_implementation_permission_suspended_downgrades_push_allowed(self) -> None:
        action, reason = _coerce_advisory_for_blockers(
            "push_allowed",
            "worktree_clean_and_review_accepted",
            "implementation_permission_suspended",
        )

        self.assertNotEqual(action, "push_allowed")
        self.assertEqual(action, "repair_reviewer_loop")
        self.assertIn("implementation_permission_suspended", reason)


class SummaryBlockersWithCoercionContractTests(unittest.TestCase):
    """Integration: the summary blocker reader triggers the coercion."""

    def _coerce_from_payload(self, payload: dict) -> tuple[str, str, str]:
        blockers_csv = _summary_blockers(payload)
        action, reason = _coerce_advisory_for_blockers(
            str(payload.get("advisory_action") or ""),
            str(payload.get("advisory_reason") or ""),
            blockers_csv,
        )
        return action, reason, blockers_csv

    def test_resync_required_blocks_push_allowed_action(self) -> None:
        """Coordination resync must never coexist with push_allowed."""
        payload = {
            "advisory_action": "push_allowed",
            "advisory_reason": "worktree_clean_and_review_accepted",
            "startup_authority": {"ok": True},
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": False,
                    "safe_to_continue_editing": True,
                }
            },
            "reviewer_gate": {
                "implementation_blocked": False,
                "review_gate_allows_push": True,
            },
            "coordination": {"resync_required": True},
            "implementation_permission": "allowed",
        }

        action, _reason, blockers_csv = self._coerce_from_payload(payload)

        self.assertIn("coordination_resync_required", blockers_csv)
        self.assertNotEqual(action, "push_allowed")

    def test_implementation_permission_blocked_blocks_push_allowed_action(self) -> None:
        """Typed implementation_permission must never coexist with push_allowed."""
        payload = {
            "advisory_action": "push_allowed",
            "advisory_reason": "worktree_clean_and_review_accepted",
            "startup_authority": {"ok": True},
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": False,
                    "safe_to_continue_editing": True,
                }
            },
            "reviewer_gate": {
                "implementation_blocked": False,
                "review_gate_allows_push": True,
            },
            "coordination": {},
            "implementation_permission": "blocked",
        }

        action, _reason, blockers_csv = self._coerce_from_payload(payload)

        self.assertIn("implementation_permission_blocked", blockers_csv)
        self.assertNotEqual(action, "push_allowed")

    def test_implementation_permission_suspended_blocks_push_allowed_action(self) -> None:
        payload = {
            "advisory_action": "push_allowed",
            "advisory_reason": "worktree_clean_and_review_accepted",
            "startup_authority": {"ok": True},
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": False,
                    "safe_to_continue_editing": True,
                }
            },
            "reviewer_gate": {
                "implementation_blocked": False,
                "review_gate_allows_push": True,
            },
            "coordination": {},
            "implementation_permission": "suspended",
        }

        action, _reason, blockers_csv = self._coerce_from_payload(payload)

        self.assertIn("implementation_permission_suspended", blockers_csv)
        self.assertNotEqual(action, "push_allowed")

    def test_clean_state_keeps_push_allowed(self) -> None:
        payload = {
            "advisory_action": "push_allowed",
            "advisory_reason": "worktree_clean_and_review_accepted",
            "startup_authority": {"ok": True},
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": False,
                    "safe_to_continue_editing": True,
                }
            },
            "reviewer_gate": {
                "implementation_blocked": False,
                "review_gate_allows_push": True,
            },
            "coordination": {"resync_required": False},
            "implementation_permission": "allowed",
        }

        action, reason, blockers_csv = self._coerce_from_payload(payload)

        self.assertEqual(blockers_csv, "none")
        self.assertEqual(action, "push_allowed")
        self.assertEqual(reason, "worktree_clean_and_review_accepted")


if __name__ == "__main__":
    unittest.main()
