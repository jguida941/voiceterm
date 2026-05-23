"""Focused tests for typed conductor capability ownership."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime.conductor_capability import (
    build_conductor_capability_state,
    context_graph_bootstrap_command,
    reviewer_local_implementation_allowed,
    reviewer_takeover_command,
    session_resume_command_for_role,
)


class TestConductorCapability(unittest.TestCase):
    def test_reviewer_is_read_only_in_active_dual_agent(self) -> None:
        capability = build_conductor_capability_state(
            provider="codex",
            role="reviewer",
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
            role="implementer",
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

    def test_missing_mode_fails_closed_for_implementer_capability(self) -> None:
        capability = build_conductor_capability_state(
            provider="claude",
            role="implementer",
            reviewer_mode="",
        )

        self.assertFalse(capability.may_edit_repo)
        self.assertEqual(capability.queue_policy, "inactive")

    def test_explicit_role_override_allows_swapped_provider_assignments(self) -> None:
        reviewer = build_conductor_capability_state(
            provider="claude",
            role="reviewer",
            reviewer_mode="active_dual_agent",
        )
        implementer = build_conductor_capability_state(
            provider="codex",
            role="implementer",
            reviewer_mode="active_dual_agent",
        )

        self.assertEqual(reviewer.provider, "claude")
        self.assertEqual(reviewer.role, "reviewer")
        self.assertFalse(reviewer.may_edit_repo)
        self.assertEqual(implementer.provider, "codex")
        self.assertEqual(implementer.role, "implementer")
        self.assertTrue(implementer.may_edit_repo)

    def test_legacy_mode_alone_cannot_grant_implementer_edit_capability(self) -> None:
        """A reviewer-mode label alone cannot grant mutation authority."""
        capability = build_conductor_capability_state(
            provider="codex",
            role="implementer",
            reviewer_mode="active_dual_agent",
            collaboration={"role_assignments": []},
        )
        self.assertFalse(capability.may_edit_repo)
        self.assertEqual(capability.queue_policy, "inactive")
        self.assertIn(
            "typed role_assignments",
            capability.status_summary,
        )

    def test_typed_implementation_role_assignment_grants_implementer_edit_capability(self) -> None:
        """A live implementation-capable role opens implementer edit capability."""
        capability = build_conductor_capability_state(
            provider="codex",
            role="implementer",
            reviewer_mode="active_dual_agent",
            collaboration={
                "role_assignments": [
                    {
                        "agent_id": "codex",
                        "provider": "codex",
                        "role_id": "implementation",
                        "live": True,
                    }
                ]
            },
        )
        self.assertTrue(capability.may_edit_repo)

    def test_typed_implementation_role_assignment_must_bind_current_provider(self) -> None:
        capability = build_conductor_capability_state(
            provider="codex",
            role="implementer",
            reviewer_mode="active_dual_agent",
            collaboration={
                "role_assignments": [
                    {
                        "agent_id": "claude",
                        "provider": "claude",
                        "role_id": "implementation",
                        "live": True,
                    }
                ]
            },
        )

        self.assertFalse(capability.may_edit_repo)
        self.assertEqual(capability.queue_policy, "inactive")

    def test_v4553_no_collaboration_param_preserves_legacy_back_compat(self) -> None:
        """When `collaboration` is omitted, the legacy `reviewer_mode`
        path continues to grant implementer capability — this is the
        back-compat for callers not yet updated.
        """
        capability = build_conductor_capability_state(
            provider="codex",
            role="implementer",
            reviewer_mode="active_dual_agent",
        )
        self.assertTrue(capability.may_edit_repo)

    def test_single_agent_no_live_mutation_capability_fails_closed(self) -> None:
        """Single-agent reviewer-mode still needs typed mutation authority."""
        capability = build_conductor_capability_state(
            provider="codex",
            role="reviewer",
            reviewer_mode="single_agent",
            collaboration={"role_assignments": []},
        )
        self.assertFalse(capability.may_edit_repo)
        self.assertEqual(capability.worker_unavailable_policy, "inactive")

    def test_single_agent_typed_live_implementation_role_grants_mutation(self) -> None:
        """Single-agent mutation opens only from implementation/mutation evidence."""
        capability = build_conductor_capability_state(
            provider="codex",
            role="reviewer",
            reviewer_mode="single_agent",
            collaboration={
                "role_assignments": [
                    {
                        "agent_id": "codex",
                        "provider": "codex",
                        "role_id": "implementation",
                        "live": True,
                    }
                ]
            },
        )
        self.assertTrue(capability.may_edit_repo)

    def test_typed_mutation_role_assignment_must_bind_current_provider(self) -> None:
        capability = build_conductor_capability_state(
            provider="codex",
            role="reviewer",
            reviewer_mode="single_agent",
            collaboration={
                "role_assignments": [
                    {
                        "agent_id": "claude",
                        "provider": "claude",
                        "role_id": "implementation",
                        "live": True,
                    }
                ]
            },
        )

        self.assertFalse(capability.may_edit_repo)
        self.assertEqual(capability.worker_unavailable_policy, "inactive")

    def test_tdd_role_does_not_grant_single_agent_mutation(self) -> None:
        capability = build_conductor_capability_state(
            provider="codex",
            role="reviewer",
            reviewer_mode="single_agent",
            collaboration={
                "role_assignments": [
                    {
                        "agent_id": "codex",
                        "provider": "codex",
                        "role_id": "tdd_first_role",
                        "live": True,
                    }
                ]
            },
        )

        self.assertFalse(capability.may_edit_repo)
        self.assertEqual(capability.worker_unavailable_policy, "inactive")

    def test_role_bootstrap_commands_are_canonical(self) -> None:
        self.assertEqual(
            session_resume_command_for_role("reviewer"),
            "python3 dev/scripts/devctl.py session-resume --role reviewer --format bootstrap",
        )
        self.assertEqual(
            session_resume_command_for_role("implementer"),
            "python3 dev/scripts/devctl.py session-resume --role implementer --format bootstrap",
        )
        self.assertEqual(
            context_graph_bootstrap_command(),
            "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md",
        )
