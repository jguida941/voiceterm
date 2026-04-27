"""Tests for review-surface snapshot consistency guard."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dev.scripts.devctl.tests.conftest import load_repo_module


# Shared fixture payloads for snapshot-id agreement tests.  Disk parity is
# tested separately; these fixtures pass disk_review_state_payload=None so the
# disk check is skipped and the snapshot-id logic is isolated.

_MATCHING_AUTHORITY_FIELDS: dict[str, object] = {
    "effective_reviewer_mode": "active_dual_agent",
    "launch_truth": "live_runtime",
    "attention_status": "healthy",
    "recovery_action_allowed": "",
    "diagnosis_status": "healthy",
    "decision_action_id": "continue_scoped_loop",
    "decision_command": "",
    "decision_execution_owner": "system",
    "decision_requires_approval": False,
    "decision_can_auto_fix": False,
    "implementation_blocked": False,
    "implementation_block_reason": "",
    "reviewed_hash_current": True,
    "review_needed": False,
    "next_turn_required": False,
    "next_turn_role": "",
    "next_turn_reason": "up_to_date",
}

_STATUS_SOURCE_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
_PROVENANCE_OBSERVED_FIELDS = ["head_sha", "worktree_hash", "generation_id"]
_PROVENANCE_INFERRED_FIELDS = ["snapshot_id", "zref"]


def _source_identity(generation_id: str) -> dict[str, str]:
    return {
        "generation_id": generation_id,
        "head_sha": f"head-{generation_id}",
        "worktree_hash": f"worktree-{generation_id}",
    }


def _provenance(generation_id: str) -> dict[str, object]:
    return {
        "source_identity": _source_identity(generation_id),
        "source_contract": "ReviewState",
        "source_command": _STATUS_SOURCE_COMMAND,
        "observed_fields": list(_PROVENANCE_OBSERVED_FIELDS),
        "inferred_fields": list(_PROVENANCE_INFERRED_FIELDS),
    }


class CheckReviewSurfaceConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_repo_module(
            "check_review_surface_consistency",
            "dev/scripts/checks/check_review_surface_consistency.py",
        )

    def test_build_report_passes_when_all_surfaces_share_snapshot_id(self) -> None:
        zref = "zref-123"
        report = self.script.build_report(
            startup_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                "push_decision": {"snapshot_id": "snap-123", "zref": zref},
            },
            review_state_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                **_provenance("gen-9"),
                "recovery_assessment": {
                    "diagnosis": {"status": "healthy"},
                    "decision": {
                        "action_id": "continue_scoped_loop",
                        "command": "",
                    },
                },
                "attention": {
                    "status": "healthy",
                    "owner": "system",
                    "summary": "",
                    "recommended_action": "",
                    "recommended_command": "",
                },
                "commit_pipeline": {
                    "snapshot_id": "snap-123",
                    "zref": zref,
                    "generation_id": "gen-9",
                },
                "registry": {
                    "zref": zref,
                    "agents": [],
                    **_provenance("gen-9"),
                },
                "_compat": {
                    "doctor": {
                        "snapshot_id": "snap-123",
                        "generation_id": "gen-9",
                        "status": "healthy",
                        "diagnosis_status": "healthy",
                        "decision_action_id": "continue_scoped_loop",
                        "decision_command": "",
                    },
                    "bridge_projection": {
                        "metadata": {
                            "snapshot_id": "snap-123",
                            "zref": zref,
                            **_provenance("gen-9"),
                        },
                    },
                },
            },
            compact_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                "push_decision": {"snapshot_id": "snap-123", "zref": zref},
                "doctor": {
                    "snapshot_id": "snap-123",
                    "generation_id": "gen-9",
                    "status": "healthy",
                    "diagnosis_status": "healthy",
                    "decision_action_id": "continue_scoped_loop",
                    "decision_command": "",
                },
            },
            commit_pipeline_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                "generation_id": "gen-9",
            },
            bridge_poll_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                **_MATCHING_AUTHORITY_FIELDS,
            },
            turn_authority_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                **_MATCHING_AUTHORITY_FIELDS,
            },
            disk_review_state_payload=None,
        )

        self.assertTrue(report["ok"])
        self.assertEqual(report["contract_id"], "ConvergencePassResult")
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["violations"], [])

    def test_build_report_reuses_frozen_review_state_for_startup_context(
        self,
    ) -> None:
        zref = "zref-123"
        review_state_payload = {
            "snapshot_id": "snap-123",
            "zref": zref,
            **_provenance("gen-9"),
            "recovery_assessment": {
                "diagnosis": {"status": "healthy"},
                "decision": {
                    "action_id": "continue_scoped_loop",
                    "command": "",
                },
            },
            "attention": {
                "status": "healthy",
                "owner": "system",
                "summary": "",
                "recommended_action": "",
                "recommended_command": "",
            },
            "commit_pipeline": {
                "snapshot_id": "snap-123",
                "zref": zref,
                "generation_id": "gen-9",
            },
            "registry": {
                "zref": zref,
                "agents": [],
                **_provenance("gen-9"),
            },
            "_compat": {
                "doctor": {
                    "snapshot_id": "snap-123",
                    "generation_id": "gen-9",
                    "status": "healthy",
                    "diagnosis_status": "healthy",
                    "decision_action_id": "continue_scoped_loop",
                    "decision_command": "",
                },
                "bridge_projection": {
                    "metadata": {
                        "snapshot_id": "snap-123",
                        "zref": zref,
                        **_provenance("gen-9"),
                    },
                },
            },
        }
        build_startup_context_mock = Mock(
            return_value=SimpleNamespace(
                to_dict=lambda: {
                    "snapshot_id": "snap-123",
                    "zref": zref,
                    "push_decision": {"snapshot_id": "snap-123", "zref": zref},
                }
            )
        )
        with patch.dict(
            self.script.build_report.__globals__,
            {
                "build_startup_context": build_startup_context_mock,
                "review_state_from_payload": lambda payload: payload,
            },
        ):
            report = self.script.build_report(
                review_state_payload=review_state_payload,
                compact_payload={
                    "snapshot_id": "snap-123",
                    "zref": zref,
                    "push_decision": {"snapshot_id": "snap-123", "zref": zref},
                    "doctor": {
                        "snapshot_id": "snap-123",
                        "generation_id": "gen-9",
                        "status": "healthy",
                        "diagnosis_status": "healthy",
                        "decision_action_id": "continue_scoped_loop",
                        "decision_command": "",
                    },
                },
                commit_pipeline_payload={
                    "snapshot_id": "snap-123",
                    "zref": zref,
                    "generation_id": "gen-9",
                },
                bridge_poll_payload={
                    "snapshot_id": "snap-123",
                    "zref": zref,
                    **_MATCHING_AUTHORITY_FIELDS,
                },
                turn_authority_payload={
                    "snapshot_id": "snap-123",
                    "zref": zref,
                    **_MATCHING_AUTHORITY_FIELDS,
                },
                disk_review_state_payload=None,
            )

        self.assertIn("ok", report)
        build_startup_context_mock.assert_called_once()
        self.assertIn("repo_root", build_startup_context_mock.call_args.kwargs)
        self.assertIs(
            build_startup_context_mock.call_args.kwargs["review_state"],
            review_state_payload,
        )
        self.assertEqual(
            build_startup_context_mock.call_args.kwargs["caller_role"],
            "observer",
        )

    def test_build_report_fails_when_snapshot_ids_diverge(self) -> None:
        report = self.script.build_report(
            startup_payload={
                "snapshot_id": "snap-123",
                "push_decision": {"snapshot_id": "snap-123"},
            },
            review_state_payload={
                "snapshot_id": "snap-123",
                "recovery_assessment": {
                    "diagnosis": {"status": "review_loop_relaunch_required"},
                    "decision": {
                        "action_id": "relaunch_review_loop",
                        "command": "launch",
                    },
                },
                "attention": {
                    "status": "review_loop_relaunch_required",
                    "owner": "system",
                    "summary": "",
                    "recommended_action": "",
                    "recommended_command": "launch",
                },
                "commit_pipeline": {
                    "snapshot_id": "snap-999",
                    "generation_id": "gen-9",
                },
                "_compat": {
                    "doctor": {
                        "snapshot_id": "snap-123",
                        "generation_id": "gen-8",
                        "status": "healthy",
                        "diagnosis_status": "healthy",
                        "decision_action_id": "continue_scoped_loop",
                        "decision_command": "",
                    },
                    "bridge_projection": {
                        "metadata": {"snapshot_id": "snap-123"},
                    },
                },
            },
            compact_payload={
                "snapshot_id": "snap-123",
                "push_decision": {"snapshot_id": "snap-123"},
                "doctor": {
                    "snapshot_id": "snap-123",
                    "generation_id": "gen-9",
                    "status": "healthy",
                    "diagnosis_status": "healthy",
                    "decision_action_id": "continue_scoped_loop",
                    "decision_command": "",
                },
            },
            commit_pipeline_payload={
                "snapshot_id": "snap-999",
                "generation_id": "gen-9",
            },
            bridge_poll_payload={
                "snapshot_id": "snap-123",
                "effective_reviewer_mode": "tools_only",
                "launch_truth": "detached_runtime_only",
                "attention_status": "review_loop_relaunch_required",
                "recovery_action_allowed": "launch",
                "diagnosis_status": "review_loop_relaunch_required",
                "decision_action_id": "relaunch_review_loop",
                "decision_command": "launch",
                "decision_execution_owner": "system",
                "decision_requires_approval": True,
                "decision_can_auto_fix": False,
                "implementation_blocked": True,
                "implementation_block_reason": "review_loop_relaunch_required",
                "reviewed_hash_current": True,
                "review_needed": False,
                "next_turn_required": True,
                "next_turn_role": "reviewer",
                "next_turn_reason": "up_to_date",
            },
            turn_authority_payload={
                "snapshot_id": "snap-123",
                "effective_reviewer_mode": "tools_only",
                "launch_truth": "detached_runtime_only",
                "attention_status": "review_loop_relaunch_required",
                "recovery_action_allowed": "launch",
                "diagnosis_status": "review_loop_relaunch_required",
                "decision_action_id": "relaunch_review_loop",
                "decision_command": "launch",
                "decision_execution_owner": "system",
                "decision_requires_approval": True,
                "decision_can_auto_fix": False,
                "implementation_blocked": True,
                "implementation_block_reason": "review_loop_relaunch_required",
                "reviewed_hash_current": True,
                "review_needed": False,
                "next_turn_required": True,
                "next_turn_role": "reviewer",
                "next_turn_reason": "review_loop_relaunch_required",
            },
            disk_review_state_payload=None,
        )

        self.assertFalse(report["ok"])
        self.assertIn("snapshot_id mismatch", "\n".join(report["errors"]))
        self.assertIn("pipeline generation mismatch", "\n".join(report["errors"]))

    def test_build_report_fails_when_provenance_tuple_diverges(self) -> None:
        zref = "zref-123"
        report = self.script.build_report(
            startup_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                "push_decision": {"snapshot_id": "snap-123", "zref": zref},
            },
            review_state_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                **_provenance("gen-9"),
                "recovery_assessment": {
                    "diagnosis": {"status": "healthy"},
                    "decision": {
                        "action_id": "continue_scoped_loop",
                        "command": "",
                    },
                },
                "attention": {
                    "status": "healthy",
                    "owner": "system",
                    "summary": "",
                    "recommended_action": "",
                    "recommended_command": "",
                },
                "commit_pipeline": {
                    "snapshot_id": "snap-123",
                    "zref": zref,
                    "generation_id": "gen-9",
                },
                "registry": {
                    "zref": zref,
                    "agents": [],
                    **_provenance("gen-9"),
                    "source_command": "python3 dev/scripts/devctl.py review-channel --action doctor --terminal none --format json",
                },
                "_compat": {
                    "doctor": {
                        "snapshot_id": "snap-123",
                        "generation_id": "gen-9",
                        "status": "healthy",
                        "diagnosis_status": "healthy",
                        "decision_action_id": "continue_scoped_loop",
                        "decision_command": "",
                    },
                    "bridge_projection": {
                        "metadata": {
                            "snapshot_id": "snap-123",
                            "zref": zref,
                            **_provenance("gen-9"),
                        },
                    },
                },
            },
            compact_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                "push_decision": {"snapshot_id": "snap-123", "zref": zref},
                "doctor": {
                    "snapshot_id": "snap-123",
                    "generation_id": "gen-9",
                    "status": "healthy",
                    "diagnosis_status": "healthy",
                    "decision_action_id": "continue_scoped_loop",
                    "decision_command": "",
                },
            },
            commit_pipeline_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                "generation_id": "gen-9",
            },
            bridge_poll_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                **_MATCHING_AUTHORITY_FIELDS,
            },
            turn_authority_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                **_MATCHING_AUTHORITY_FIELDS,
            },
            disk_review_state_payload=None,
        )

        self.assertFalse(report["ok"])
        self.assertIn("provenance mismatch", "\n".join(report["errors"]))
        self.assertIn("review_state_registry", "\n".join(report["errors"]))

    def test_build_report_fails_when_source_identity_omits_observed_key(self) -> None:
        zref = "zref-123"
        incomplete_provenance = _provenance("gen-9")
        incomplete_provenance["source_identity"] = {
            "generation_id": "gen-9",
            "head_sha": "head-gen-9",
        }
        report = self.script.build_report(
            startup_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                "push_decision": {"snapshot_id": "snap-123", "zref": zref},
            },
            review_state_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                **incomplete_provenance,
                "recovery_assessment": {
                    "diagnosis": {"status": "healthy"},
                    "decision": {
                        "action_id": "continue_scoped_loop",
                        "command": "",
                    },
                },
                "attention": {
                    "status": "healthy",
                    "owner": "system",
                    "summary": "",
                    "recommended_action": "",
                    "recommended_command": "",
                },
                "commit_pipeline": {
                    "snapshot_id": "snap-123",
                    "zref": zref,
                    "generation_id": "gen-9",
                },
                "registry": {
                    "zref": zref,
                    "agents": [],
                    **incomplete_provenance,
                },
                "_compat": {
                    "doctor": {
                        "snapshot_id": "snap-123",
                        "generation_id": "gen-9",
                        "status": "healthy",
                        "diagnosis_status": "healthy",
                        "decision_action_id": "continue_scoped_loop",
                        "decision_command": "",
                    },
                    "bridge_projection": {
                        "metadata": {
                            "snapshot_id": "snap-123",
                            "zref": zref,
                            **incomplete_provenance,
                        },
                    },
                },
            },
            compact_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                "push_decision": {"snapshot_id": "snap-123", "zref": zref},
                "doctor": {
                    "snapshot_id": "snap-123",
                    "generation_id": "gen-9",
                    "status": "healthy",
                    "diagnosis_status": "healthy",
                    "decision_action_id": "continue_scoped_loop",
                    "decision_command": "",
                },
            },
            commit_pipeline_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                "generation_id": "gen-9",
            },
            bridge_poll_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                **_MATCHING_AUTHORITY_FIELDS,
            },
            turn_authority_payload={
                "snapshot_id": "snap-123",
                "zref": zref,
                **_MATCHING_AUTHORITY_FIELDS,
            },
            disk_review_state_payload=None,
        )

        self.assertFalse(report["ok"])
        self.assertIn("missing source_identity keys", "\n".join(report["errors"]))
        self.assertIn("worktree_hash", "\n".join(report["errors"]))

    def test_build_report_compares_frozen_nine_surface_proof_tick_fields(self) -> None:
        payloads = self._phase_zero_payloads()
        report = self.script.build_report(**payloads, disk_review_state_payload=None)

        self.assertTrue(report["ok"])
        proof_surfaces = report["proof_tick_fields"]
        for surface in (
            "coordination_snapshot",
            "authority_snapshot",
            "control_plane_read_model",
            "startup_context",
            "session_resume",
            "review_channel_status",
            "persisted_review_state",
            "registry_agents",
            "bridge_compat",
        ):
            self.assertIn(surface, proof_surfaces)
        self.assertEqual(
            proof_surfaces["session_resume"]["next_command"],
            "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
        )

        drifted = dict(payloads["session_resume_payload"])
        drifted["next_recommended_command"] = "python3 dev/scripts/devctl.py stale"
        failed = self.script.build_report(
            **{**payloads, "session_resume_payload": drifted},
            disk_review_state_payload=None,
        )

        self.assertFalse(failed["ok"])
        self.assertIn(
            "proof-tick parity mismatch on next_command",
            "\n".join(failed["errors"]),
        )

    def test_build_report_uses_startup_context_as_reviewer_mode_authority(
        self,
    ) -> None:
        payloads = self._phase_zero_payloads()
        startup = payloads["startup_payload"]
        coordination = payloads["review_state_payload"]["coordination"]
        assert isinstance(startup, dict)
        assert isinstance(coordination, dict)
        startup["reviewer_gate"] = {"reviewer_mode": "single_agent"}
        coordination["reviewer_mode"] = "tools_only"

        report = self.script.build_report(**payloads, disk_review_state_payload=None)

        self.assertFalse(report["ok"])
        reviewer_mode_violations = [
            violation
            for violation in report["violations"]
            if violation["category"] == "proof_tick_field_parity"
            and violation["field"] == "reviewer_mode"
        ]
        self.assertEqual(len(reviewer_mode_violations), 1)
        self.assertEqual(reviewer_mode_violations[0]["surface"], "coordination_snapshot")
        self.assertEqual(reviewer_mode_violations[0]["expected"], "single_agent")
        self.assertIn(
            "from startup_context",
            reviewer_mode_violations[0]["detail"],
        )

    def test_build_report_compares_operator_interaction_mode_axis(self) -> None:
        payloads = self._phase_zero_payloads()
        startup = payloads["startup_payload"]
        control_plane = payloads["control_plane_payload"]
        assert isinstance(startup, dict)
        assert isinstance(control_plane, dict)
        startup["interaction_mode"] = "remote_control"
        startup["reviewer_gate"] = {"operator_interaction_mode": "remote_control"}
        control_plane["operator_interaction_mode"] = "local_terminal"

        report = self.script.build_report(**payloads, disk_review_state_payload=None)

        self.assertFalse(report["ok"])
        self.assertIn(
            "proof-tick parity mismatch on operator_interaction_mode",
            "\n".join(report["errors"]),
        )
        mode_violations = [
            violation
            for violation in report["violations"]
            if violation["category"] == "proof_tick_field_parity"
            and violation["field"] == "operator_interaction_mode"
        ]
        self.assertEqual(len(mode_violations), 1)
        self.assertEqual(mode_violations[0]["surface"], "control_plane_read_model")
        self.assertEqual(mode_violations[0]["expected"], "remote_control")

    def test_build_report_uses_startup_context_as_implementation_permission_authority(
        self,
    ) -> None:
        payloads = self._phase_zero_payloads()
        startup = payloads["startup_payload"]
        assert isinstance(startup, dict)
        startup["implementation_permission"] = "blocked"

        report = self.script.build_report(**payloads, disk_review_state_payload=None)

        self.assertFalse(report["ok"])
        permission_violations = [
            violation
            for violation in report["violations"]
            if violation["category"] == "proof_tick_field_parity"
            and violation["field"] == "implementation_permission"
        ]
        self.assertTrue(permission_violations)
        self.assertTrue(
            all(
                violation["expected"] == "blocked"
                for violation in permission_violations
            )
        )
        self.assertTrue(
            any(
                "from startup_context" in violation["detail"]
                for violation in permission_violations
            )
        )

    def test_build_report_uses_authority_snapshot_as_next_command_authority(
        self,
    ) -> None:
        payloads = self._phase_zero_payloads()
        review_state = payloads["review_state_payload"]
        startup = payloads["startup_payload"]
        assert isinstance(review_state, dict)
        assert isinstance(startup, dict)
        authority = dict(review_state["authority_snapshot"])
        authority["next_command"] = "python3 dev/scripts/devctl.py authoritative-next"
        review_state["authority_snapshot"] = authority
        startup["next_command"] = "python3 dev/scripts/devctl.py stale-startup"

        report = self.script.build_report(**payloads, disk_review_state_payload=None)

        self.assertFalse(report["ok"])
        next_command_violations = [
            violation
            for violation in report["violations"]
            if violation["category"] == "proof_tick_field_parity"
            and violation["field"] == "next_command"
        ]
        self.assertTrue(next_command_violations)
        self.assertTrue(
            all(
                violation["expected"]
                == "python3 dev/scripts/devctl.py authoritative-next"
                for violation in next_command_violations
            )
        )
        self.assertTrue(
            any(
                "from authority_snapshot" in violation["detail"]
                for violation in next_command_violations
            )
        )

    def test_build_report_allows_dirty_startup_dynamic_command(self) -> None:
        payloads = self._phase_zero_payloads()
        startup = dict(payloads["startup_payload"])
        coordination = dict(startup["coordination"])
        coordination["ownership_status"] = "scope_unknown_dirty_paths"
        startup["coordination"] = coordination
        startup["next_command"] = (
            "python3 dev/scripts/devctl.py commit -m \"<descriptive message>\""
        )

        report = self.script.build_report(
            **{**payloads, "startup_payload": startup},
            disk_review_state_payload=None,
        )

        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])

    def test_build_report_accepts_receipt_parent_commit_pipeline_sha(self) -> None:
        payloads = self._phase_zero_payloads()
        review_state = payloads["review_state_payload"]
        compact = payloads["compact_payload"]
        assert isinstance(review_state, dict)
        assert isinstance(compact, dict)
        for pipeline in (
            review_state["commit_pipeline"],
            compact["commit_pipeline"],
            payloads["commit_pipeline_payload"],
        ):
            assert isinstance(pipeline, dict)
            pipeline["commit_sha"] = "parent-content-head"

        report = self.script.build_report(**payloads, disk_review_state_payload=None)

        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])

    def _phase_zero_payloads(self) -> dict[str, object]:
        snapshot_id = "snap-phase0"
        zref = "zref_phase0_head"
        generation_id = "gen-phase0"
        head_sha = "head-gen-phase0"
        worktree_hash = "worktree:sha256:phase0"
        next_command = (
            "python3 dev/scripts/devctl.py review-channel --action status "
            "--terminal none --format json"
        )
        source_identity = {
            "generation_id": generation_id,
            "head_sha": head_sha,
            "worktree_hash": worktree_hash,
        }
        provenance = {
            "source_identity": source_identity,
            "source_contract": "ReviewState",
            "source_command": _STATUS_SOURCE_COMMAND,
            "observed_fields": list(_PROVENANCE_OBSERVED_FIELDS),
            "inferred_fields": list(_PROVENANCE_INFERRED_FIELDS),
        }
        coordination = {
            "snapshot_id": snapshot_id,
            "zref": zref,
            **provenance,
            "observed_topology": "single_agent",
            "ownership_status": "clear",
        }
        authority = {
            "snapshot_id": snapshot_id,
            "zref": zref,
            **provenance,
            "reviewer_mode": "single_agent",
            "observed_control_topology": "single_agent",
            "current_instruction_revision": "rev-phase0",
            "implementation_permission": "active",
            "next_command": next_command,
        }
        review_state = {
            "snapshot_id": snapshot_id,
            "zref": zref,
            **provenance,
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "observed_control_topology": "single_agent",
            "current_instruction_revision": "rev-phase0",
            "ownership_status": "clear",
            "implementation_permission": "active",
            "next_command": next_command,
            "coordination": coordination,
            "authority_snapshot": authority,
            "current_session": {"current_instruction_revision": "rev-phase0"},
            "recovery_assessment": {
                "diagnosis": {"status": "healthy"},
                "decision": {
                    "action_id": "continue_scoped_loop",
                    "command": next_command,
                    "execution_owner": "system",
                    "rationale": "Continue the scoped loop.",
                },
            },
            "attention": {
                "status": "healthy",
                "owner": "system",
                "summary": "",
                "recommended_action": "Continue the scoped loop.",
                "recommended_command": next_command,
            },
            "commit_pipeline": {
                "snapshot_id": snapshot_id,
                "zref": zref,
                "generation_id": generation_id,
                "commit_sha": head_sha,
                "worktree_identity": worktree_hash,
            },
            "registry": {
                "snapshot_id": snapshot_id,
                "zref": zref,
                **provenance,
                "agents": [],
            },
            "_compat": {
                "doctor": {
                    "snapshot_id": snapshot_id,
                    "generation_id": generation_id,
                    "status": "healthy",
                    "diagnosis_status": "healthy",
                    "decision_action_id": "continue_scoped_loop",
                    "decision_command": next_command,
                },
                "bridge_projection": {
                    "metadata": {
                        "snapshot_id": snapshot_id,
                        "zref": zref,
                        **provenance,
                    },
                },
            },
        }
        bridge_surface = {
            "snapshot_id": snapshot_id,
            "zref": zref,
            **_MATCHING_AUTHORITY_FIELDS,
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "current_instruction_revision": "rev-phase0",
            "decision_command": next_command,
        }
        return {
            "startup_payload": {
                "snapshot_id": snapshot_id,
                "zref": zref,
                "observed_control_topology": "single_agent",
                "implementation_permission": "active",
                "next_command": next_command,
                "authority_snapshot": authority,
                "coordination": coordination,
                "current_session": {"current_instruction_revision": "rev-phase0"},
                "push_decision": {"snapshot_id": snapshot_id, "zref": zref},
            },
            "review_state_payload": review_state,
            "compact_payload": {
                "snapshot_id": snapshot_id,
                "zref": zref,
                "authority_snapshot": authority,
                "current_session": {"current_instruction_revision": "rev-phase0"},
                "recovery_assessment": review_state["recovery_assessment"],
                "push_decision": {"snapshot_id": snapshot_id, "zref": zref},
                "doctor": {
                    "snapshot_id": snapshot_id,
                    "generation_id": generation_id,
                    "status": "healthy",
                    "diagnosis_status": "healthy",
                    "decision_action_id": "continue_scoped_loop",
                    "decision_command": next_command,
                },
                "commit_pipeline": review_state["commit_pipeline"],
            },
            "commit_pipeline_payload": review_state["commit_pipeline"],
            "bridge_poll_payload": bridge_surface,
            "turn_authority_payload": bridge_surface,
            "control_plane_payload": {
                "snapshot_id": snapshot_id,
                "zref": zref,
                "head_sha": head_sha,
                "reviewer_mode": "single_agent",
                "next_command": next_command,
                "coordination": coordination,
                **provenance,
            },
            "session_resume_payload": {
                "snapshot_id": snapshot_id,
                "zref": zref,
                "head_sha": head_sha,
                "instruction_revision": "rev-phase0",
                "next_recommended_command": next_command,
                "authority_snapshot": authority,
                "coordination": coordination,
                **provenance,
            },
            "status_payload": {
                "snapshot_id": snapshot_id,
                "zref": zref,
                "reviewer_mode": "single_agent",
                "effective_reviewer_mode": "single_agent",
                "observed_control_topology": "single_agent",
                "current_instruction_revision": "rev-phase0",
                "ownership_status": "clear",
                "implementation_permission": "active",
                "next_command": next_command,
                "authority_snapshot": authority,
                "coordination": coordination,
                **provenance,
            },
            "registry_payload": review_state["registry"],
            "bridge_compat_payload": bridge_surface,
        }

    def test_build_report_does_not_conflate_coordination_topology_with_control_topology(
        self,
    ) -> None:
        payloads = self._phase_zero_payloads()
        startup = payloads["startup_payload"]
        review_state = payloads["review_state_payload"]
        compact = payloads["compact_payload"]
        status = payloads["status_payload"]
        control_plane = payloads["control_plane_payload"]
        session_resume = payloads["session_resume_payload"]
        for payload in (
            startup,
            review_state,
            compact,
            status,
            control_plane,
            session_resume,
        ):
            coordination = payload.get("coordination")
            if isinstance(coordination, dict):
                coordination["observed_topology"] = "dual_agent"

        report = self.script.build_report(**payloads, disk_review_state_payload=None)

        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])

    def test_build_report_fails_when_queue_instruction_does_not_reach_current_session(
        self,
    ) -> None:
        payloads = self._phase_zero_payloads()
        review_state = payloads["review_state_payload"]
        assert isinstance(review_state, dict)
        review_state["queue"] = {
            "derived_next_instruction": (
                "Priority action_request: Run governed checkpoint"
            ),
            "derived_next_instruction_source": {"packet_id": "rev_pkt_1818"},
        }
        review_state["current_session"] = {
            "current_instruction": "",
            "current_instruction_revision": "",
        }

        report = self.script.build_report(**payloads, disk_review_state_payload=None)

        self.assertFalse(report["ok"])
        self.assertIn(
            "queue/current-session parity mismatch",
            "\n".join(report["errors"]),
        )

    def test_build_report_fails_when_attention_drifts_from_recovery_assessment(self) -> None:
        report = self.script.build_report(
            startup_payload={
                "snapshot_id": "snap-321",
                "push_decision": {"snapshot_id": "snap-321"},
            },
            review_state_payload={
                "snapshot_id": "snap-321",
                "recovery_assessment": {
                    "diagnosis": {
                        "status": "implementer_state_reset_required",
                        "root_cause": "Implementer ACK (`Claude Ack` compatibility heading) is stale for the live instruction.",
                    },
                    "decision": {
                        "action_id": "reset_implementer_state",
                        "command": "python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md",
                        "execution_owner": "reviewer",
                        "rationale": "Reset the implementer state before resuming work.",
                    },
                },
                "attention": {
                    "status": "healthy",
                    "owner": "operator",
                    "summary": "stale summary",
                    "recommended_action": "old action",
                    "recommended_command": "legacy command",
                },
                "commit_pipeline": {
                    "snapshot_id": "snap-321",
                    "generation_id": "gen-3",
                },
                "_compat": {
                    "doctor": {
                        "snapshot_id": "snap-321",
                        "generation_id": "gen-3",
                        "status": "implementer_state_reset_required",
                        "diagnosis_status": "implementer_state_reset_required",
                        "decision_action_id": "reset_implementer_state",
                        "decision_command": "python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md",
                    },
                    "bridge_projection": {
                        "metadata": {"snapshot_id": "snap-321"},
                    },
                },
            },
            compact_payload={
                "snapshot_id": "snap-321",
                "push_decision": {"snapshot_id": "snap-321"},
                "doctor": {
                    "snapshot_id": "snap-321",
                    "generation_id": "gen-3",
                    "status": "implementer_state_reset_required",
                    "diagnosis_status": "implementer_state_reset_required",
                    "decision_action_id": "reset_implementer_state",
                    "decision_command": "python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md",
                },
            },
            commit_pipeline_payload={
                "snapshot_id": "snap-321",
                "generation_id": "gen-3",
            },
            bridge_poll_payload={
                "snapshot_id": "snap-321",
                "effective_reviewer_mode": "active_dual_agent",
                "launch_truth": "live_runtime",
                "attention_status": "implementer_state_reset_required",
                "recovery_action_allowed": "python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md",
                "diagnosis_status": "implementer_state_reset_required",
                "decision_action_id": "reset_implementer_state",
                "decision_command": "python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md",
                "decision_execution_owner": "reviewer",
                "decision_requires_approval": False,
                "decision_can_auto_fix": True,
                "implementation_blocked": False,
                "implementation_block_reason": "",
                "reviewed_hash_current": False,
                "review_needed": True,
                "next_turn_required": True,
                "next_turn_role": "implementer",
                "next_turn_reason": "implementer_ack_stale",
            },
            turn_authority_payload={
                "snapshot_id": "snap-321",
                "effective_reviewer_mode": "active_dual_agent",
                "launch_truth": "live_runtime",
                "attention_status": "implementer_state_reset_required",
                "recovery_action_allowed": "python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md",
                "diagnosis_status": "implementer_state_reset_required",
                "decision_action_id": "reset_implementer_state",
                "decision_command": "python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md",
                "decision_execution_owner": "reviewer",
                "decision_requires_approval": False,
                "decision_can_auto_fix": True,
                "implementation_blocked": False,
                "implementation_block_reason": "",
                "reviewed_hash_current": False,
                "review_needed": True,
                "next_turn_required": True,
                "next_turn_role": "implementer",
                "next_turn_reason": "implementer_ack_stale",
            },
            disk_review_state_payload=None,
        )

        self.assertFalse(report["ok"])
        self.assertIn(
            "attention projection mismatch on review_state.attention.status",
            "\n".join(report["errors"]),
        )
        self.assertIn(
            "attention projection mismatch on review_state.attention.recommended_command",
            "\n".join(report["errors"]),
        )


class DiskTurnAuthorityParityTests(unittest.TestCase):
    """Tests for disk-artifact parity between review_state.json and turn-authority."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_repo_module(
            "check_review_surface_consistency",
            "dev/scripts/checks/check_review_surface_consistency.py",
        )

    def _base_payloads(self, **overrides: object) -> dict[str, object]:
        """Return minimal payloads with consistent snapshot_ids and authority fields."""
        zref = "zref-1"
        base = {
            "startup_payload": {
                "snapshot_id": "snap-1",
                "zref": zref,
                "push_decision": {"snapshot_id": "snap-1", "zref": zref},
            },
            "review_state_payload": {
                "snapshot_id": "snap-1",
                "zref": zref,
                **_provenance("g1"),
                "recovery_assessment": {
                    "diagnosis": {"status": "healthy"},
                    "decision": {
                        "action_id": "continue_scoped_loop",
                        "command": "",
                        "execution_owner": "system",
                        "rationale": "",
                    },
                },
                "attention": {
                    "status": "healthy",
                    "owner": "system",
                    "summary": "",
                    "recommended_action": "",
                    "recommended_command": "",
                },
                "commit_pipeline": {
                    "snapshot_id": "snap-1",
                    "zref": zref,
                    "generation_id": "g1",
                },
                "registry": {
                    "zref": zref,
                    "agents": [],
                    **_provenance("g1"),
                },
                "_compat": {
                    "doctor": {
                        "snapshot_id": "snap-1",
                        "generation_id": "g1",
                        "status": "healthy",
                        "diagnosis_status": "healthy",
                        "decision_action_id": "continue_scoped_loop",
                        "decision_command": "",
                    },
                    "bridge_projection": {
                        "metadata": {
                            "snapshot_id": "snap-1",
                            "zref": zref,
                            **_provenance("g1"),
                        }
                    },
                },
            },
            "compact_payload": {
                "snapshot_id": "snap-1",
                "zref": zref,
                "push_decision": {"snapshot_id": "snap-1", "zref": zref},
                "doctor": {
                    "snapshot_id": "snap-1",
                    "generation_id": "g1",
                    "status": "healthy",
                    "diagnosis_status": "healthy",
                    "decision_action_id": "continue_scoped_loop",
                    "decision_command": "",
                },
            },
            "commit_pipeline_payload": {
                "snapshot_id": "snap-1",
                "zref": zref,
                "generation_id": "g1",
            },
            "bridge_poll_payload": {
                "snapshot_id": "snap-1",
                "zref": zref,
                **_MATCHING_AUTHORITY_FIELDS,
            },
            "turn_authority_payload": {
                "snapshot_id": "snap-1",
                "zref": zref,
                **_MATCHING_AUTHORITY_FIELDS,
            },
        }
        base.update(overrides)
        return base

    def test_disk_parity_passes_when_disk_matches_authority(self) -> None:
        report = self.script.build_report(
            **self._base_payloads(),
            disk_review_state_payload={
                "reviewer_runtime": {
                    "effective_reviewer_mode": "active_dual_agent",
                },
                "bridge": {
                    "launch_truth": "live_runtime",
                },
                "attention": {
                    "status": "healthy",
                },
            },
        )
        self.assertTrue(report["ok"], f"errors: {report['errors']}")
        self.assertEqual(report["errors"], [])

    def test_disk_parity_fails_on_effective_mode_mismatch(self) -> None:
        report = self.script.build_report(
            **self._base_payloads(),
            disk_review_state_payload={
                "reviewer_runtime": {
                    "effective_reviewer_mode": "tools_only",
                },
                "bridge": {
                    "launch_truth": "live_runtime",
                },
                "attention": {
                    "status": "healthy",
                },
            },
        )
        self.assertFalse(report["ok"])
        error_text = "\n".join(report["errors"])
        self.assertIn("disk-artifact parity mismatch on effective_reviewer_mode", error_text)
        self.assertNotIn("launch_truth", error_text)
        self.assertNotIn("attention_status", error_text)

    def test_disk_parity_fails_on_launch_truth_mismatch(self) -> None:
        report = self.script.build_report(
            **self._base_payloads(),
            disk_review_state_payload={
                "reviewer_runtime": {
                    "effective_reviewer_mode": "active_dual_agent",
                },
                "bridge": {
                    "launch_truth": "detached_runtime_only",
                },
                "attention": {
                    "status": "healthy",
                },
            },
        )
        self.assertFalse(report["ok"])
        error_text = "\n".join(report["errors"])
        self.assertIn("disk-artifact parity mismatch on launch_truth", error_text)

    def test_disk_parity_fails_on_attention_status_mismatch(self) -> None:
        report = self.script.build_report(
            **self._base_payloads(),
            disk_review_state_payload={
                "reviewer_runtime": {
                    "effective_reviewer_mode": "active_dual_agent",
                },
                "bridge": {
                    "launch_truth": "live_runtime",
                },
                "attention": {
                    "status": "reviewer_poll_due",
                },
            },
        )
        self.assertFalse(report["ok"])
        error_text = "\n".join(report["errors"])
        self.assertIn("disk-artifact parity mismatch on attention_status", error_text)

    def test_disk_parity_warns_when_no_disk_artifact(self) -> None:
        report = self.script.build_report(
            **self._base_payloads(),
            disk_review_state_payload=None,
        )
        self.assertTrue(report["ok"])
        warnings = report.get("disk_parity_warnings", [])
        self.assertTrue(
            any("not found" in w for w in warnings),
            f"expected 'not found' warning, got: {warnings}",
        )

    def test_disk_parity_warns_when_no_authority_payload(self) -> None:
        """When both turn-authority and bridge-poll are empty, disk check is skipped."""
        errors, warnings = self.script._disk_turn_authority_parity_errors(
            repo_root=self.script.REPO_ROOT,
            turn_authority={},
            bridge_poll={},
            disk_review_state_override={
                "reviewer_runtime": {"effective_reviewer_mode": "active_dual_agent"},
                "bridge": {"launch_truth": "live_runtime"},
                "attention": {"status": "healthy"},
            },
            disk_override_provided=True,
        )
        self.assertEqual(errors, [])
        self.assertTrue(
            any("no turn-authority" in w for w in warnings),
            f"expected skip warning, got: {warnings}",
        )

    def test_disk_parity_warns_when_disk_has_no_typed_sections(self) -> None:
        report = self.script.build_report(
            **self._base_payloads(),
            disk_review_state_payload={"snapshot_id": "snap-1"},
        )
        self.assertTrue(report["ok"])
        warnings = report.get("disk_parity_warnings", [])
        self.assertTrue(
            any("no reviewer_runtime" in w for w in warnings),
            f"expected typed-section warning, got: {warnings}",
        )

    def test_disk_parity_skips_field_when_disk_value_missing(self) -> None:
        """When a specific field is absent from disk sections, skip that comparison."""
        report = self.script.build_report(
            **self._base_payloads(),
            disk_review_state_payload={
                "reviewer_runtime": {},
                "bridge": {},
                "attention": {},
            },
        )
        self.assertTrue(report["ok"], f"errors: {report['errors']}")

    def test_disk_parity_uses_bridge_poll_when_turn_authority_empty(self) -> None:
        """When turn-authority is empty, bridge-poll fields are used as authority source."""
        errors, warnings = self.script._disk_turn_authority_parity_errors(
            repo_root=self.script.REPO_ROOT,
            turn_authority={},
            bridge_poll={
                "effective_reviewer_mode": "active_dual_agent",
                "launch_truth": "live_runtime",
                "attention_status": "healthy",
            },
            disk_review_state_override={
                "reviewer_runtime": {
                    "effective_reviewer_mode": "active_dual_agent",
                },
                "bridge": {
                    "launch_truth": "live_runtime",
                },
                "attention": {
                    "status": "healthy",
                },
            },
            disk_override_provided=True,
        )
        self.assertEqual(errors, [], f"unexpected errors: {errors}")
        self.assertEqual(warnings, [])

    def test_disk_parity_reports_all_three_mismatches(self) -> None:
        report = self.script.build_report(
            **self._base_payloads(),
            disk_review_state_payload={
                "reviewer_runtime": {
                    "effective_reviewer_mode": "tools_only",
                },
                "bridge": {
                    "launch_truth": "detached_runtime_only",
                },
                "attention": {
                    "status": "reviewer_heartbeat_stale",
                },
            },
        )
        self.assertFalse(report["ok"])
        error_text = "\n".join(report["errors"])
        self.assertIn("effective_reviewer_mode", error_text)
        self.assertIn("launch_truth", error_text)
        self.assertIn("attention_status", error_text)

    def test_build_report_flags_green_doctor_when_diagnosis_is_degraded(self) -> None:
        report = self.script.build_report(
            **self._base_payloads(
                review_state_payload={
                    "snapshot_id": "snap-1",
                    "recovery_assessment": {
                        "diagnosis": {"status": "implementer_state_reset_required"},
                        "decision": {
                            "action_id": "reset_implementer_state",
                            "command": "reset",
                            "execution_owner": "system",
                            "rationale": "",
                        },
                    },
                    "attention": {
                        "status": "implementer_state_reset_required",
                        "owner": "system",
                        "summary": "",
                        "recommended_action": "",
                        "recommended_command": "reset",
                    },
                    "commit_pipeline": {"snapshot_id": "snap-1", "generation_id": "g1"},
                    "_compat": {
                        "doctor": {
                            "snapshot_id": "snap-1",
                            "generation_id": "g1",
                            "status": "healthy",
                            "diagnosis_status": "implementer_state_reset_required",
                            "decision_action_id": "reset_implementer_state",
                            "decision_command": "reset",
                        },
                        "bridge_projection": {"metadata": {"snapshot_id": "snap-1"}},
                    },
                },
                compact_payload={
                    "snapshot_id": "snap-1",
                    "push_decision": {"snapshot_id": "snap-1"},
                    "doctor": {
                        "snapshot_id": "snap-1",
                        "generation_id": "g1",
                        "status": "healthy",
                        "diagnosis_status": "implementer_state_reset_required",
                        "decision_action_id": "reset_implementer_state",
                        "decision_command": "reset",
                    },
                },
                bridge_poll_payload={
                    "snapshot_id": "snap-1",
                    **{
                        **_MATCHING_AUTHORITY_FIELDS,
                        "attention_status": "implementer_state_reset_required",
                        "recovery_action_allowed": "reset",
                        "diagnosis_status": "implementer_state_reset_required",
                        "decision_action_id": "reset_implementer_state",
                        "decision_command": "reset",
                    },
                },
                turn_authority_payload={
                    "snapshot_id": "snap-1",
                    **{
                        **_MATCHING_AUTHORITY_FIELDS,
                        "attention_status": "implementer_state_reset_required",
                        "recovery_action_allowed": "reset",
                        "diagnosis_status": "implementer_state_reset_required",
                        "decision_action_id": "reset_implementer_state",
                        "decision_command": "reset",
                    },
                },
            ),
            disk_review_state_payload=None,
        )

        self.assertFalse(report["ok"])
        self.assertIn("reports healthy while diagnosis", "\n".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
