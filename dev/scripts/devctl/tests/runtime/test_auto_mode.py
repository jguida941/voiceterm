"""Tests for the auto-mode state machine contracts."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime.auto_mode import (
    AUTO_MODE_CONTRACT_ID,
    AUTO_MODE_SCHEMA_VERSION,
    AutoModeInputs,
    AutoModePhase,
    AutoModeState,
    auto_mode_state_from_mapping,
    resolve_auto_mode_phase,
)


class AutoModePhaseEnumTests(unittest.TestCase):
    """Verify AutoModePhase enum contract stability."""

    def test_all_phases_present(self) -> None:
        expected = {
            "reviewing", "implementing", "testing",
            "committing", "pushing", "idle",
        }
        actual = {p.value for p in AutoModePhase}
        self.assertEqual(expected, actual)

    def test_str_coercion(self) -> None:
        self.assertEqual(str(AutoModePhase.REVIEWING), "reviewing")
        self.assertEqual(str(AutoModePhase.IDLE), "idle")


class AutoModeStateTests(unittest.TestCase):
    """Verify AutoModeState dataclass and serialization."""

    def test_defaults(self) -> None:
        state = AutoModeState()
        self.assertEqual(state.phase, "idle")
        self.assertEqual(state.phase_started_utc, "")
        self.assertEqual(state.operator_interaction_mode, "local_terminal")
        self.assertFalse(state.reviewer_alive)
        self.assertFalse(state.implementer_alive)
        self.assertEqual(state.last_commit_sha, "")
        self.assertTrue(state.last_guard_ok)
        self.assertEqual(state.pending_action_requests, 0)
        self.assertEqual(state.next_transition, "")

    def test_to_dict_roundtrip(self) -> None:
        state = AutoModeState(
            phase="implementing",
            reviewer_alive=True,
            last_commit_sha="abc123",
        )
        d = state.to_dict()
        self.assertEqual(d["phase"], "implementing")
        self.assertTrue(d["reviewer_alive"])
        self.assertEqual(d["last_commit_sha"], "abc123")

    def test_frozen(self) -> None:
        state = AutoModeState()
        with self.assertRaises(AttributeError):
            state.phase = "pushing"  # type: ignore[misc]


class AutoModeFromMappingTests(unittest.TestCase):
    """Verify deserialization from JSON-like mappings."""

    def test_empty_mapping_returns_defaults(self) -> None:
        state = auto_mode_state_from_mapping({})
        self.assertEqual(state.phase, "idle")
        self.assertTrue(state.last_guard_ok)

    def test_non_dict_returns_defaults(self) -> None:
        state = auto_mode_state_from_mapping("not a dict")
        self.assertEqual(state.phase, "idle")

    def test_full_mapping(self) -> None:
        state = auto_mode_state_from_mapping({
            "phase": "pushing",
            "reviewer_alive": True,
            "implementer_alive": True,
            "last_commit_sha": "deadbeef",
            "last_guard_ok": False,
            "pending_action_requests": 3,
            "next_transition": "run governed push",
        })
        self.assertEqual(state.phase, "pushing")
        self.assertTrue(state.reviewer_alive)
        self.assertTrue(state.implementer_alive)
        self.assertEqual(state.last_commit_sha, "deadbeef")
        self.assertFalse(state.last_guard_ok)
        self.assertEqual(state.pending_action_requests, 3)
        self.assertEqual(state.next_transition, "run governed push")


class ResolveAutoModePhaseTests(unittest.TestCase):
    """Verify phase resolution from typed inputs."""

    def _inputs(self, **overrides) -> AutoModeInputs:
        defaults = {
            "push_decision_action": "",
            "push_decision_reason": "",
            "worktree_clean": True,
            "review_gate_allows_push": False,
            "reviewer_mode": "single_agent",
            "implementation_blocked": False,
            "implementer_status": "",
            "last_guard_ok": True,
            "current_head_commit": "abc123",
            "pending_action_requests": 0,
            "operator_interaction_mode": "local_terminal",
            "timestamp_utc": "2026-04-04T12:00:00Z",
        }
        defaults.update(overrides)
        return AutoModeInputs(**defaults)

    def test_idle_when_no_signals(self) -> None:
        state = resolve_auto_mode_phase(self._inputs())
        self.assertEqual(state.phase, "idle")
        self.assertIn("no active work", state.next_transition)

    def test_pushing_when_push_eligible(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="run_devctl_push",
        ))
        self.assertEqual(state.phase, "pushing")
        self.assertIn("push", state.next_transition)

    def test_committing_when_dirty_await_checkpoint(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="await_checkpoint",
            worktree_clean=False,
        ))
        self.assertEqual(state.phase, "committing")
        self.assertIn("commit", state.next_transition)

    def test_idle_when_clean_await_checkpoint(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="await_checkpoint",
            worktree_clean=True,
        ))
        self.assertEqual(state.phase, "idle")

    def test_testing_when_guard_failed(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            last_guard_ok=False,
        ))
        self.assertEqual(state.phase, "testing")
        self.assertIn("guard", state.next_transition)

    def test_reviewing_when_await_review(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="await_review",
        ))
        self.assertEqual(state.phase, "reviewing")
        self.assertIn("reviewer", state.next_transition)

    def test_reviewing_when_implementation_blocked(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            implementation_blocked=True,
        ))
        self.assertEqual(state.phase, "reviewing")

    def test_implementing_when_dirty_worktree(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            worktree_clean=False,
        ))
        self.assertEqual(state.phase, "implementing")
        self.assertIn("editing", state.next_transition)

    def test_reviewer_alive_for_dual_agent(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            reviewer_mode="active_dual_agent",
        ))
        self.assertTrue(state.reviewer_alive)

    def test_reviewer_not_alive_for_single_agent(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            reviewer_mode="single_agent",
        ))
        self.assertFalse(state.reviewer_alive)

    def test_implementer_alive_when_implementing(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            implementer_status="implementing",
        ))
        self.assertTrue(state.implementer_alive)

    def test_implementer_not_alive_when_idle(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            implementer_status="",
        ))
        self.assertFalse(state.implementer_alive)

    def test_head_commit_preserved(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            current_head_commit="deadbeef1234",
        ))
        self.assertEqual(state.last_commit_sha, "deadbeef1234")

    def test_timestamp_preserved(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            timestamp_utc="2026-04-04T15:30:00Z",
        ))
        self.assertEqual(state.phase_started_utc, "2026-04-04T15:30:00Z")

    def test_no_push_needed_with_clean_worktree_is_idle(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="no_push_needed",
            worktree_clean=True,
        ))
        self.assertEqual(state.phase, "idle")

    def test_guard_failure_overrides_review_await(self) -> None:
        """Guard failures take priority over review-pending state."""
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="await_review",
            last_guard_ok=False,
        ))
        self.assertEqual(state.phase, "testing")

    def test_push_overrides_guard_failure(self) -> None:
        """Push-eligible takes highest priority even with guard failure."""
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="run_devctl_push",
            last_guard_ok=False,
        ))
        self.assertEqual(state.phase, "pushing")


class AutoModeContractTests(unittest.TestCase):
    """Verify contract ID and schema version stability."""

    def test_contract_id(self) -> None:
        self.assertEqual(AUTO_MODE_CONTRACT_ID, "AutoModeState")

    def test_schema_version(self) -> None:
        self.assertEqual(AUTO_MODE_SCHEMA_VERSION, 1)


if __name__ == "__main__":
    unittest.main()
