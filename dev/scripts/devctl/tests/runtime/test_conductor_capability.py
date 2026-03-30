"""Focused tests for typed conductor capability ownership."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime.conductor_capability import (
    build_conductor_capability_state,
    reviewer_local_implementation_allowed,
    reviewer_takeover_command,
)


class TestConductorCapability(unittest.TestCase):
    def test_reviewer_is_read_only_in_active_dual_agent(self) -> None:
        capability = build_conductor_capability_state(
            provider="codex",
            reviewer_mode="active_dual_agent",
        )

        self.assertEqual(capability.role, "reviewer")
        self.assertEqual(
            capability.startup_context_command,
            "python3 dev/scripts/devctl.py startup-context --role reviewer --format summary",
        )
        self.assertFalse(capability.may_edit_repo)
        self.assertTrue(capability.requires_explicit_takeover)
        self.assertEqual(capability.worker_unavailable_policy, "stay_reviewer_only")
        self.assertEqual(capability.queue_policy, "review_only")
        self.assertEqual(capability.takeover_command, reviewer_takeover_command())

    def test_reviewer_override_is_required_for_local_implementation(self) -> None:
        self.assertFalse(
            reviewer_local_implementation_allowed(
                reviewer_mode="active_dual_agent",
                reviewer_override=False,
            )
        )
        self.assertTrue(
            reviewer_local_implementation_allowed(
                reviewer_mode="active_dual_agent",
                reviewer_override=True,
            )
        )

    def test_implementer_capability_stays_execution_focused(self) -> None:
        capability = build_conductor_capability_state(
            provider="claude",
            reviewer_mode="active_dual_agent",
        )

        self.assertEqual(capability.role, "implementer")
        self.assertEqual(
            capability.startup_context_command,
            "python3 dev/scripts/devctl.py startup-context --role implementer --format summary",
        )
        self.assertTrue(capability.may_edit_repo)
        self.assertFalse(capability.requires_explicit_takeover)
        self.assertEqual(capability.worker_unavailable_policy, "self_execute")
        self.assertEqual(capability.queue_policy, "implement_assigned_work")
