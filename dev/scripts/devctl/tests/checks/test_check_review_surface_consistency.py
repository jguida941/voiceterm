"""Tests for review-surface snapshot consistency guard."""

from __future__ import annotations

import unittest

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


class CheckReviewSurfaceConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_repo_module(
            "check_review_surface_consistency",
            "dev/scripts/checks/check_review_surface_consistency.py",
        )

    def test_build_report_passes_when_all_surfaces_share_snapshot_id(self) -> None:
        report = self.script.build_report(
            startup_payload={
                "snapshot_id": "snap-123",
                "push_decision": {"snapshot_id": "snap-123"},
            },
            review_state_payload={
                "snapshot_id": "snap-123",
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
                    "generation_id": "gen-9",
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
                "snapshot_id": "snap-123",
                "generation_id": "gen-9",
            },
            bridge_poll_payload={
                "snapshot_id": "snap-123",
                **_MATCHING_AUTHORITY_FIELDS,
            },
            turn_authority_payload={
                "snapshot_id": "snap-123",
                **_MATCHING_AUTHORITY_FIELDS,
            },
            disk_review_state_payload=None,
        )

        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])

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
        self.assertIn("bridge-poll parity mismatch", "\n".join(report["errors"]))
        self.assertIn("diagnosis parity mismatch", "\n".join(report["errors"]))
        self.assertIn("reports healthy while diagnosis", "\n".join(report["errors"]))

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
                        "root_cause": "Claude Ack is stale for the live instruction.",
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
        base = {
            "startup_payload": {
                "snapshot_id": "snap-1",
                "push_decision": {"snapshot_id": "snap-1"},
            },
            "review_state_payload": {
                "snapshot_id": "snap-1",
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
                "commit_pipeline": {"snapshot_id": "snap-1", "generation_id": "g1"},
                "_compat": {
                    "doctor": {
                        "snapshot_id": "snap-1",
                        "generation_id": "g1",
                        "status": "healthy",
                        "diagnosis_status": "healthy",
                        "decision_action_id": "continue_scoped_loop",
                        "decision_command": "",
                    },
                    "bridge_projection": {"metadata": {"snapshot_id": "snap-1"}},
                },
            },
            "compact_payload": {
                "snapshot_id": "snap-1",
                "push_decision": {"snapshot_id": "snap-1"},
                "doctor": {
                    "snapshot_id": "snap-1",
                    "generation_id": "g1",
                    "status": "healthy",
                    "diagnosis_status": "healthy",
                    "decision_action_id": "continue_scoped_loop",
                    "decision_command": "",
                },
            },
            "commit_pipeline_payload": {"snapshot_id": "snap-1", "generation_id": "g1"},
            "bridge_poll_payload": {
                "snapshot_id": "snap-1",
                **_MATCHING_AUTHORITY_FIELDS,
            },
            "turn_authority_payload": {
                "snapshot_id": "snap-1",
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
