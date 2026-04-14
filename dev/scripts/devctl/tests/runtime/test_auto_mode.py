"""Tests for the auto-mode state machine contracts."""

from __future__ import annotations

import unittest
import unittest.mock

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
            reviewer_mode="active_dual_agent",
        ))
        self.assertEqual(state.phase, "pushing")
        self.assertIn("push", state.next_transition)

    def test_reviewing_when_push_eligible_but_both_roles_dead(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="run_devctl_push",
            reviewer_mode="single_agent",
            implementer_status="",
        ))
        self.assertEqual(state.phase, "reviewing")
        self.assertIn("resume a live participant", state.next_transition)

    def test_committing_when_dirty_await_checkpoint(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="await_checkpoint",
            worktree_clean=False,
            reviewer_mode="active_dual_agent",
        ))
        self.assertEqual(state.phase, "committing")
        self.assertIn("commit", state.next_transition)

    def test_reviewing_when_await_checkpoint_and_both_roles_dead(self) -> None:
        state = resolve_auto_mode_phase(self._inputs(
            push_decision_action="await_checkpoint",
            worktree_clean=False,
            reviewer_mode="single_agent",
            implementer_status="",
        ))
        self.assertEqual(state.phase, "reviewing")
        self.assertIn("resume a live participant", state.next_transition)

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
            reviewer_mode="active_dual_agent",
        ))
        self.assertEqual(state.phase, "pushing")

    def test_head_drift_forces_reviewing(self) -> None:
        """When HEAD has moved past last_reviewed_sha, phase is reviewing."""
        state = resolve_auto_mode_phase(self._inputs(
            current_head_commit="new_head_abc",
            last_reviewed_sha="old_reviewed_123",
        ))
        self.assertEqual(state.phase, "reviewing")
        self.assertIn("HEAD moved", state.next_transition)

    def test_no_drift_when_head_matches_reviewed(self) -> None:
        """When HEAD matches last_reviewed_sha, no drift is detected."""
        state = resolve_auto_mode_phase(self._inputs(
            current_head_commit="same_sha",
            last_reviewed_sha="same_sha",
        ))
        self.assertEqual(state.phase, "idle")

    def test_no_drift_when_reviewed_sha_empty(self) -> None:
        """When no push has happened yet, no drift is detected."""
        state = resolve_auto_mode_phase(self._inputs(
            current_head_commit="abc123",
            last_reviewed_sha="",
        ))
        self.assertEqual(state.phase, "idle")

    def test_dirty_worktree_overrides_head_drift(self) -> None:
        """Dirty worktree takes priority over head drift."""
        state = resolve_auto_mode_phase(self._inputs(
            worktree_clean=False,
            current_head_commit="new_head",
            last_reviewed_sha="old_reviewed",
        ))
        self.assertEqual(state.phase, "implementing")

    def test_guard_failure_overrides_head_drift(self) -> None:
        """Guard failure takes priority over head drift."""
        state = resolve_auto_mode_phase(self._inputs(
            last_guard_ok=False,
            current_head_commit="new_head",
            last_reviewed_sha="old_reviewed",
        ))
        self.assertEqual(state.phase, "testing")


class AutoModeContractTests(unittest.TestCase):
    """Verify contract ID and schema version stability."""

    def test_contract_id(self) -> None:
        self.assertEqual(AUTO_MODE_CONTRACT_ID, "AutoModeState")

    def test_schema_version(self) -> None:
        self.assertEqual(AUTO_MODE_SCHEMA_VERSION, 1)


class LaunchInteractionModeTests(unittest.TestCase):
    """Verify governance-first interaction mode resolution for launch paths."""

    def _make_governance(self, interaction_mode: str):
        from dev.scripts.devctl.runtime.project_governance_contract import (
            ArtifactRoots,
            BridgeConfig,
            BundleOverrides,
            EnabledChecks,
            MemoryRoots,
            PathRoots,
            PlanRegistry,
            ProjectGovernance,
            RepoIdentity,
            RepoPackRef,
        )

        return ProjectGovernance(
            schema_version=1,
            contract_id="ProjectGovernance",
            repo_identity=RepoIdentity(repo_name="test"),
            repo_pack=RepoPackRef(pack_id="test"),
            path_roots=PathRoots(),
            plan_registry=PlanRegistry(),
            artifact_roots=ArtifactRoots(),
            memory_roots=MemoryRoots(),
            bridge_config=BridgeConfig(operator_interaction_mode=interaction_mode),
            enabled_checks=EnabledChecks(),
            bundle_overrides=BundleOverrides(overrides={}),
        )

    @unittest.mock.patch(
        "dev.scripts.devctl.commands.review_channel.bridge_action_support"
        ".scan_repo_governance_safely",
    )
    def test_remote_control_governance_forces_headless_interaction(self, mock_gov) -> None:
        """Launch with remote_control governance resolves interaction_mode correctly."""
        from dev.scripts.devctl.commands.review_channel.bridge_action_support import (
            resolve_launch_interaction_mode,
        )
        from pathlib import Path

        mock_gov.return_value = self._make_governance("remote_control")
        mode = resolve_launch_interaction_mode(
            repo_root=Path("/tmp/fake"),
            args_fallback="local_terminal",
        )
        self.assertEqual(mode, "remote_control")

    @unittest.mock.patch(
        "dev.scripts.devctl.commands.review_channel.bridge_action_support"
        ".scan_repo_governance_safely",
    )
    def test_empty_governance_falls_back_to_args(self, mock_gov) -> None:
        """When governance has no interaction_mode, args fallback is used."""
        from dev.scripts.devctl.commands.review_channel.bridge_action_support import (
            resolve_launch_interaction_mode,
        )
        from pathlib import Path

        mock_gov.return_value = self._make_governance("")
        mode = resolve_launch_interaction_mode(
            repo_root=Path("/tmp/fake"),
            args_fallback="dual_agent",
        )
        self.assertEqual(mode, "dual_agent")

    @unittest.mock.patch(
        "dev.scripts.devctl.commands.review_channel.bridge_action_support"
        ".scan_repo_governance_safely",
    )
    def test_no_governance_falls_back_to_args(self, mock_gov) -> None:
        """Without governance, args fallback determines the mode."""
        from dev.scripts.devctl.commands.review_channel.bridge_action_support import (
            resolve_launch_interaction_mode,
        )
        from pathlib import Path

        mock_gov.return_value = None
        mode = resolve_launch_interaction_mode(
            repo_root=Path("/tmp/fake"),
            args_fallback="single_agent",
        )
        self.assertEqual(mode, "single_agent")


class StatusProjectionPacketCountTests(unittest.TestCase):
    """Verify status projection carries real pending packet counts."""

    def test_queue_counts_from_pending_packets(self) -> None:
        """_build_queue_state derives counts from pending packet tuples."""
        from dev.scripts.devctl.review_channel.status_projection import (
            _build_queue_state,
        )

        packets = (
            {"status": "pending", "to_agent": "codex", "packet_id": "p1"},
            {"status": "pending", "to_agent": "codex", "packet_id": "p2"},
            {"status": "pending", "to_agent": "claude", "packet_id": "p3"},
            {"status": "acked", "to_agent": "codex", "packet_id": "p4"},
        )
        queue = _build_queue_state(None, pending_packets=packets)
        self.assertEqual(queue.pending_total, 3)
        self.assertEqual(queue.pending_codex, 2)
        self.assertEqual(queue.pending_claude, 1)
        self.assertEqual(queue.pending_cursor, 0)
        self.assertEqual(queue.pending_operator, 0)

    def test_queue_counts_empty_packets(self) -> None:
        """Empty packet tuple yields zero counts (backward compat)."""
        from dev.scripts.devctl.review_channel.status_projection import (
            _build_queue_state,
        )

        queue = _build_queue_state(None, pending_packets=())
        self.assertEqual(queue.pending_total, 0)
        self.assertEqual(queue.pending_codex, 0)

    def test_count_pending_by_target(self) -> None:
        """_count_pending_by_target groups only pending packets by to_agent."""
        from dev.scripts.devctl.review_channel.status_projection import (
            _count_pending_by_target,
        )

        packets = (
            {"status": "pending", "to_agent": "operator"},
            {"status": "pending", "to_agent": "operator"},
            {"status": "pending", "to_agent": "cursor"},
            {"status": "dismissed", "to_agent": "operator"},
        )
        counts = _count_pending_by_target(packets)
        self.assertEqual(counts["operator"], 2)
        self.assertEqual(counts["cursor"], 1)
        self.assertNotIn("dismissed", counts)


class AutoModeFromControlPlaneReadModelTests(unittest.TestCase):
    """Verify auto-mode derives inputs from ControlPlaneReadModel."""

    def _build_model(self, **overrides):
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            build_control_plane_read_model,
        )
        from pathlib import Path

        sources = {
            "receipt": None,
            "review_state": None,
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": None,
        }
        git = {
            "branch": "feature/test",
            "head": "abc1234",
            "clean": True,
            "ahead": 0,
        }
        sources.update(overrides.pop("sources", {}))
        git.update(overrides.pop("git", {}))
        return build_control_plane_read_model(
            Path("/tmp/nonexistent"),
            sources_override=sources,
            git_override=git,
        )

    def test_idle_from_empty_read_model(self) -> None:
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model()
        inputs = inputs_from_read_model(model)
        state = resolve_auto_mode_phase(inputs)
        self.assertEqual(state.phase, "idle")
        self.assertEqual(inputs.operator_interaction_mode, "single_agent")
        self.assertTrue(inputs.last_guard_ok)

    def test_pushing_from_read_model_with_push_receipt(self) -> None:
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(
            sources={
                "receipt": {"push_action": "run_devctl_push"},
                "review_state": {"bridge": {"reviewer_mode": "active_dual_agent"}},
            },
        )
        inputs = inputs_from_read_model(model)
        state = resolve_auto_mode_phase(inputs)
        self.assertEqual(state.phase, "pushing")
        self.assertEqual(inputs.push_decision_action, "run_devctl_push")

    def test_reviewing_from_read_model_when_push_receipt_but_both_roles_dead(self) -> None:
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(
            sources={
                "receipt": {"push_action": "run_devctl_push"},
            },
        )
        inputs = inputs_from_read_model(model)
        state = resolve_auto_mode_phase(inputs)
        self.assertEqual(state.phase, "reviewing")
        self.assertIn("resume a live participant", state.next_transition)

    def test_testing_from_read_model_with_guard_failure(self) -> None:
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(
            sources={
                "push_report": {"preflight_step": {"returncode": 1}},
            },
        )
        inputs = inputs_from_read_model(model)
        state = resolve_auto_mode_phase(inputs)
        self.assertEqual(state.phase, "testing")
        self.assertFalse(inputs.last_guard_ok)

    def test_implementing_from_dirty_worktree(self) -> None:
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(git={"clean": False})
        inputs = inputs_from_read_model(model)
        state = resolve_auto_mode_phase(inputs)
        self.assertEqual(state.phase, "implementing")
        self.assertFalse(inputs.worktree_clean)

    def test_reviewer_mode_propagates_from_read_model(self) -> None:
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(
            sources={
                "review_state": {
                    "bridge": {"reviewer_mode": "active_dual_agent"},
                },
            },
        )
        inputs = inputs_from_read_model(model)
        state = resolve_auto_mode_phase(inputs)
        self.assertEqual(inputs.reviewer_mode, "active_dual_agent")
        self.assertTrue(state.reviewer_alive)

    def test_head_sha_propagates(self) -> None:
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(git={"head": "deadbeef9876"})
        inputs = inputs_from_read_model(model)
        self.assertEqual(inputs.current_head_commit, "deadbeef9876")

    def test_pending_actions_propagate(self) -> None:
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(
            sources={
                "review_state": {
                    "packets": [
                        {"status": "pending", "packet_id": "p1"},
                        {"status": "pending", "packet_id": "p2"},
                        {"status": "acked", "packet_id": "p3"},
                    ],
                },
            },
        )
        inputs = inputs_from_read_model(model)
        self.assertEqual(inputs.pending_action_requests, 2)

    def test_implementation_blocked_propagates(self) -> None:
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(
            sources={"receipt": {"implementation_blocked": True}},
        )
        inputs = inputs_from_read_model(model)
        state = resolve_auto_mode_phase(inputs)
        self.assertTrue(inputs.implementation_blocked)
        self.assertEqual(state.phase, "reviewing")

    def test_read_model_and_direct_inputs_agree_on_phase(self) -> None:
        """The read-model path and direct AutoModeInputs produce the same phase."""
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(
            sources={"receipt": {"push_action": "await_review"}},
        )
        from_model = resolve_auto_mode_phase(inputs_from_read_model(model))
        from_direct = resolve_auto_mode_phase(AutoModeInputs(
            push_decision_action="await_review",
        ))
        self.assertEqual(from_model.phase, from_direct.phase)

    def test_implementer_alive_from_claude_conductor(self) -> None:
        """claude_conductor_alive in read model maps to implementer_alive=True."""
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model(
            sources={
                "claude_conductor": {"session_pid": 99999},
            },
        )
        # session_pid check uses os.kill(pid, 0) which will fail for
        # a non-existent PID, so inject via a read-model override instead
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        alive_model = ControlPlaneReadModel(
            timestamp=model.timestamp,
            branch=model.branch,
            head_sha=model.head_sha,
            worktree_clean=model.worktree_clean,
            ahead_of_upstream=model.ahead_of_upstream,
            resolved_phase=model.resolved_phase,
            push_eligible=model.push_eligible,
            implementation_blocked=model.implementation_blocked,
            top_blocker=model.top_blocker,
            next_action=model.next_action,
            next_command=model.next_command,
            reviewer_mode=model.reviewer_mode,
            operator_interaction_mode=model.operator_interaction_mode,
            reviewer_freshness=model.reviewer_freshness,
            review_accepted=model.review_accepted,
            last_reviewed_sha=getattr(model, "last_reviewed_sha", ""),
            attention_status=model.attention_status,
            attention_summary=model.attention_summary,
            publisher_running=model.publisher_running,
            supervisor_running=model.supervisor_running,
            codex_conductor_alive=model.codex_conductor_alive,
            claude_conductor_alive=True,
            pending_action_requests=model.pending_action_requests,
            last_guard_ok=model.last_guard_ok,
            check_details=model.check_details,
        )
        inputs = inputs_from_read_model(alive_model)
        self.assertEqual(inputs.implementer_status, "active")
        state = resolve_auto_mode_phase(inputs)
        self.assertTrue(state.implementer_alive)

    def test_implementer_not_alive_when_conductor_dead(self) -> None:
        """claude_conductor_alive=False maps to implementer_alive=False."""
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )

        model = self._build_model()
        inputs = inputs_from_read_model(model)
        self.assertEqual(inputs.implementer_status, "")
        state = resolve_auto_mode_phase(inputs)
        self.assertFalse(state.implementer_alive)


if __name__ == "__main__":
    unittest.main()
