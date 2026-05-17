"""Tests for the typed monitor snapshot runtime surface."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.runtime.monitor_snapshot import (
    MonitorSelfAudit,
    MonitorSnapshot,
    MonitorSourceLabel,
    _build_summary,
    build_monitor_snapshot,
    write_latest_monitor_snapshot,
)


class _FakeReviewState:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def to_dict(self) -> dict[str, object]:
        return dict(self._payload)


def _sample_snapshot() -> MonitorSnapshot:
    return MonitorSnapshot(
        schema_version=1,
        contract_id="MonitorSnapshot",
        command="monitor",
        timestamp="2026-04-10T18:10:00Z",
        snapshot_id="snap-123",
        mode="remote_phone",
        agent="operator",
        canonical_runtime_state={"resolved_phase": "active"},
        observational_telemetry={"publisher_running": True},
        verdict_presence={"present": False, "current_verdict": ""},
        worktree_state={"branch": "develop", "head_sha": "abc123"},
        source_labels=(
            MonitorSourceLabel(
                source_id="review_state",
                classification="authority",
                path="dev/review_status/review_state.json",
                present=True,
            ),
        ),
        summary={
            "state": "active",
            "main_problem": "none",
            "can_work_continue": True,
            "can_code_be_pushed": False,
            "who_needs_to_act": "implementer",
            "what_should_happen_next": "continue editing",
            "confidence": "high",
        },
        self_audit=MonitorSelfAudit(
            should_emit_finding=False,
            finding_type="observer_self_audit",
            reasons=(),
        ),
    )


class MonitorSnapshotRuntimeTests(unittest.TestCase):
    def test_build_monitor_snapshot_classifies_sources_and_self_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            (repo_root / "dev/review_status").mkdir(parents=True)
            (repo_root / "dev/review_status/review_state.json").write_text(
                "{}",
                encoding="utf-8",
            )
            (repo_root / "dev/review_status/publisher_heartbeat.json").write_text(
                "{}",
                encoding="utf-8",
            )
            (repo_root / "dev/review_status/reviewer_supervisor_heartbeat.json").write_text(
                "{}",
                encoding="utf-8",
            )
            (repo_root / "dev/review_status/compact.json").write_text(
                "{}",
                encoding="utf-8",
            )
            (repo_root / "dev/review_status/full.json").write_text(
                "{}",
                encoding="utf-8",
            )
            (repo_root / "dev/reports/startup/latest").mkdir(parents=True)
            (repo_root / "dev/reports/startup/latest/receipt.json").write_text(
                "{}",
                encoding="utf-8",
            )

            review_state = _FakeReviewState(
                {
                    "bridge": {
                        "review_needed": True,
                        "reviewed_hash_current": False,
                    },
                    "reviewer_runtime": {
                        "review_acceptance": {
                            "current_verdict": "accepted_with_followups",
                        }
                    },
                }
            )
            startup = SimpleNamespace(
                snapshot_id="snap-321",
                implementation_permission="blocked",
                observed_control_topology="no_live_agents",
                push_decision=SimpleNamespace(
                    next_step_command=(
                        "python3 dev/scripts/devctl.py review-channel "
                        "--action status --terminal none --format json"
                    )
                ),
                reviewer_gate=SimpleNamespace(implementation_blocked=True),
                coordination=SimpleNamespace(resync_required=True),
                recovery_authority=SimpleNamespace(
                    recovery_action="observe_only",
                    recovery_basis="none",
                    recovery_scope="entire_lane",
                ),
            )
            model = SimpleNamespace(
                resolved_phase="active",
                operator_interaction_mode="remote_control",
                reviewer_mode="active_dual_agent",
                top_blocker="reviewer stale",
                next_action="await_review",
                next_command="python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
                review_accepted=False,
                last_guard_ok=True,
                pending_action_requests=2,
                publisher_running=False,
                supervisor_running=False,
                codex_conductor_alive=False,
                claude_conductor_alive=False,
                reviewer_freshness="8m ago",
                attention_status="reviewer_heartbeat_stale",
                attention_summary="publisher missing",
                branch="develop",
                head_sha="deadbeef",
                worktree_clean=False,
                ahead_of_upstream=3,
                push_eligible=False,
            )

            with (
                patch(
                    "dev.scripts.devctl.runtime.monitor_snapshot.scan_repo_governance_safely",
                    return_value=None,
                ),
                patch(
                    "dev.scripts.devctl.runtime.review_state_locator.load_current_review_state",
                    return_value=review_state,
                ),
                patch(
                    "dev.scripts.devctl.runtime.monitor_snapshot.build_startup_context",
                    return_value=startup,
                ),
                patch(
                    "dev.scripts.devctl.runtime.monitor_snapshot.build_control_plane_read_model",
                    return_value=model,
                ),
            ):
                snapshot = build_monitor_snapshot(
                    repo_root=repo_root,
                    review_status_dir=Path("dev/review_status"),
                )

        self.assertEqual(snapshot.snapshot_id, "snap-321")
        self.assertEqual(snapshot.summary["state"], "blocked")
        self.assertFalse(snapshot.summary["can_work_continue"])
        self.assertEqual(snapshot.summary["implementation_admissibility"], "blocked")
        self.assertEqual(snapshot.summary["who_needs_to_act"], "operator")
        self.assertTrue(snapshot.self_audit.should_emit_finding)
        self.assertIn("coordination_resync_required", snapshot.self_audit.reasons)
        self.assertIn("stale_verdict_replayed", snapshot.self_audit.reasons)
        self.assertEqual(snapshot.verdict_presence["current_verdict"], "accepted_with_followups")
        labels = {row.source_id: row.classification for row in snapshot.source_labels}
        self.assertEqual(labels["review_state"], "authority")
        self.assertEqual(labels["publisher_heartbeat"], "telemetry")
        self.assertEqual(labels["compact_projection"], "projection")
        self.assertEqual(labels["git_status"], "diagnostic")

    def test_checkpoint_gate_projects_checkpoint_required_summary(self) -> None:
        startup = SimpleNamespace(
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    checkpoint_required=True,
                    safe_to_continue_editing=False,
                )
            ),
            implementation_permission="active",
            coordination=SimpleNamespace(resync_required=False),
        )
        model = SimpleNamespace(
            push_eligible=False,
            last_guard_ok=True,
            resolved_phase="committing",
            top_blocker="checkpoint required",
            next_command="python3 dev/scripts/devctl.py startup-context --format summary",
        )

        summary = _build_summary(
            startup=startup,
            model=model,
            self_audit=MonitorSelfAudit(
                should_emit_finding=False,
                finding_type="",
                reasons=(),
            ),
        )

        self.assertEqual(summary["state"], "checkpoint_required")
        self.assertFalse(summary["can_work_continue"])
        self.assertEqual(summary["implementation_admissibility"], "checkpoint_required")

    def test_write_latest_monitor_snapshot_writes_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            output_root = repo_root / "dev/review_status"
            output_root.mkdir(parents=True)
            snapshot = _sample_snapshot()
            with patch(
                "dev.scripts.devctl.runtime.monitor_snapshot.build_monitor_snapshot",
                return_value=snapshot,
            ):
                paths = write_latest_monitor_snapshot(
                    repo_root=repo_root,
                    review_status_dir=output_root,
                )

            json_payload = json.loads(Path(paths.json_path).read_text(encoding="utf-8"))
            markdown_payload = Path(paths.markdown_path).read_text(encoding="utf-8")

        self.assertEqual(json_payload["contract_id"], "MonitorSnapshot")
        self.assertEqual(json_payload["summary"]["state"], "active")
        self.assertIn("Remote Phone Monitor", markdown_payload)


if __name__ == "__main__":
    unittest.main()
