"""Focused tests for pending-packet rewrite guards on review-channel instructions."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.bridge_support import (
    apply_scope_if_requested,
)
from dev.scripts.devctl.review_channel.pending_packets import (
    load_pending_packet_queue,
    assert_no_pending_reviewer_packets,
    load_pending_packets,
)
from dev.scripts.devctl.review_channel.promotion import (
    promote_bridge_instruction,
    scope_bridge_instruction,
)


def _bridge_text(*, verdict: str, findings: str, instruction: str) -> str:
    return "\n".join(
        [
            "# Review Bridge",
            "",
            "## Start-Of-Conversation Rules",
            "",
            "- Last Codex poll: `2026-04-08T01:00:00Z`",
            "- Reviewer mode: `active_dual_agent`",
            "- Last non-audit worktree hash: `"
            + ("a" * 64)
            + "`",
            "- Current instruction revision: `rev-123456789abc`",
            "",
            "## Poll Status",
            "",
            "- active reviewer loop",
            "",
            "## Current Verdict",
            "",
            verdict,
            "",
            "## Open Findings",
            "",
            findings,
            "",
            "## Current Instruction For Claude",
            "",
            instruction,
            "",
            "## Claude Status",
            "",
            "- pending",
            "",
            "## Claude Questions",
            "",
            "- none",
            "",
            "## Claude Ack",
            "",
            "- pending",
            "",
            "## Last Reviewed Scope",
            "",
            "- dev/active/platform_authority_loop.md",
            "",
        ]
    )


def _plan_text(item: str) -> str:
    return "\n".join(
        [
            "# Platform Authority Loop",
            "",
            "Execution plan contract: required",
            "",
            "## Scope",
            "",
            "- keep runtime authority coherent",
            "",
            "## Execution Checklist",
            "",
            "### Phase 1",
            f"- [ ] {item}",
            "",
            "## Progress Log",
            "",
            "- none",
            "",
            "## Session Resume",
            "",
            "- none",
            "",
            "## Audit Evidence",
            "",
            "- none",
        ]
    )


def _write_pending_packet(root: Path, *, to_agent: str = "codex") -> None:
    path = root / "dev/reports/review_channel/events/trace.ndjson"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": 1,
        "event_id": "rev_evt_0001",
        "packet_id": "rev_pkt_0001",
        "trace_id": "trace_0001",
        "event_type": "packet_posted",
        "status": "pending",
        "from_agent": "claude",
        "to_agent": to_agent,
        "kind": "finding",
        "summary": "Preserve earlier dashboard finding before rewriting instruction",
    }
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")


def _write_packet_events(
    root: Path,
    *,
    packets: list[dict[str, object]],
) -> None:
    path = root / "dev/reports/review_channel/events/trace.ndjson"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.dumps(packet) for packet in packets]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


class PendingPacketInstructionRewriteGuardTests(unittest.TestCase):
    def test_scope_dry_run_derives_candidate_without_rewriting_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bridge_path = root / "bridge.md"
            original = _bridge_text(
                verdict="- accepted",
                findings="- none",
                instruction="- hold steady",
            )
            bridge_path.write_text(original, encoding="utf-8")
            plan_path = root / "dev/active/platform_authority_loop.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(
                _plan_text("Prefer packet-backed reviewer authority before rewrites."),
                encoding="utf-8",
            )

            candidate = apply_scope_if_requested(
                args=SimpleNamespace(
                    action="launch",
                    scope="platform_authority_loop",
                    dry_run=True,
                ),
                repo_root=root,
                bridge_path=bridge_path,
            )
            self.assertIsNotNone(candidate)
            self.assertEqual(bridge_path.read_text(encoding="utf-8"), original)

    def test_load_pending_packets_reads_live_packet_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_pending_packet(root)

            pending = load_pending_packets(root)

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["packet_id"], "rev_pkt_0001")

    def test_load_pending_packets_ignores_expired_rows_and_tracks_stale_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            now = datetime.now(timezone.utc)
            _write_packet_events(
                root,
                packets=[
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0001",
                        "packet_id": "rev_pkt_live",
                        "trace_id": "trace_live",
                        "event_type": "packet_posted",
                        "status": "pending",
                        "from_agent": "claude",
                        "to_agent": "codex",
                        "kind": "finding",
                        "summary": "Live pending packet",
                        "expires_at_utc": (
                            now + timedelta(minutes=30)
                        ).isoformat().replace("+00:00", "Z"),
                    },
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0002",
                        "packet_id": "rev_pkt_expired",
                        "trace_id": "trace_expired",
                        "event_type": "packet_posted",
                        "status": "pending",
                        "from_agent": "claude",
                        "to_agent": "codex",
                        "kind": "finding",
                        "summary": "Expired pending packet",
                        "expires_at_utc": (
                            now - timedelta(minutes=30)
                        ).isoformat().replace("+00:00", "Z"),
                    },
                ],
            )

            pending = load_pending_packets(root)
            queue = load_pending_packet_queue(root)

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["packet_id"], "rev_pkt_live")
        self.assertEqual(queue.stale_packet_count, 1)

    def test_reviewer_guard_ignores_packets_for_other_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_pending_packet(root, to_agent="claude")

            assert_no_pending_reviewer_packets(
                repo_root=root,
                action_label="reviewer checkpoint",
            )

    def test_resolved_approval_request_does_not_stay_in_live_or_stale_queue(self) -> None:
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_packet_events(
                root,
                packets=[
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0001",
                        "packet_id": "rev_pkt_request",
                        "trace_id": "trace_commit_approval",
                        "event_type": "packet_posted",
                        "status": "pending",
                        "from_agent": "system",
                        "to_agent": "operator",
                        "kind": "commit_approval",
                        "summary": "Approve governed commit",
                        "approval_required": True,
                        "target_ref": "remote_commit_pipeline:pipeline-123",
                        "pipeline_generation": "gen-123",
                        "expires_at_utc": (
                            now + timedelta(minutes=30)
                        ).isoformat().replace("+00:00", "Z"),
                    },
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0002",
                        "packet_id": "rev_pkt_decision",
                        "trace_id": "trace_commit_approval",
                        "event_type": "packet_posted",
                        "status": "pending",
                        "from_agent": "operator",
                        "to_agent": "system",
                        "kind": "commit_approval",
                        "summary": "Approved",
                        "approval_required": False,
                        "target_ref": "remote_commit_pipeline:pipeline-123",
                        "pipeline_generation": "gen-123",
                        "expires_at_utc": (
                            now + timedelta(minutes=30)
                        ).isoformat().replace("+00:00", "Z"),
                    },
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0003",
                        "packet_id": "rev_pkt_decision",
                        "trace_id": "trace_commit_approval",
                        "event_type": "packet_applied",
                        "status": "applied",
                        "from_agent": "operator",
                        "to_agent": "system",
                        "kind": "commit_approval",
                        "summary": "Approved",
                        "approval_required": False,
                        "target_ref": "remote_commit_pipeline:pipeline-123",
                        "pipeline_generation": "gen-123",
                    },
                ],
            )

            queue = load_pending_packet_queue(root)

        self.assertEqual(queue.pending_packets, ())
        self.assertEqual(queue.stale_packet_count, 0)

    def test_acked_approval_decision_does_not_clear_live_request(self) -> None:
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_packet_events(
                root,
                packets=[
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0001",
                        "packet_id": "rev_pkt_request",
                        "trace_id": "trace_commit_approval",
                        "event_type": "packet_posted",
                        "status": "pending",
                        "from_agent": "system",
                        "to_agent": "operator",
                        "kind": "commit_approval",
                        "summary": "Approve governed commit",
                        "approval_required": True,
                        "target_ref": "remote_commit_pipeline:pipeline-123",
                        "pipeline_generation": "gen-123",
                        "expires_at_utc": (
                            now + timedelta(minutes=30)
                        ).isoformat().replace("+00:00", "Z"),
                    },
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0002",
                        "packet_id": "rev_pkt_decision",
                        "trace_id": "trace_commit_approval",
                        "event_type": "packet_posted",
                        "status": "pending",
                        "from_agent": "operator",
                        "to_agent": "system",
                        "kind": "commit_approval",
                        "summary": "Acked only",
                        "approval_required": False,
                        "target_ref": "remote_commit_pipeline:pipeline-123",
                        "pipeline_generation": "gen-123",
                    },
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0003",
                        "packet_id": "rev_pkt_decision",
                        "trace_id": "trace_commit_approval",
                        "event_type": "packet_acked",
                        "status": "acked",
                        "from_agent": "operator",
                        "to_agent": "system",
                        "kind": "commit_approval",
                        "summary": "Acked only",
                        "approval_required": False,
                        "target_ref": "remote_commit_pipeline:pipeline-123",
                        "pipeline_generation": "gen-123",
                    },
                ],
            )

            queue = load_pending_packet_queue(root)

        self.assertEqual(len(queue.pending_packets), 1)
        self.assertEqual(queue.pending_packets[0]["packet_id"], "rev_pkt_request")

    def test_non_approval_history_rows_do_not_clear_matching_live_packets(self) -> None:
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_packet_events(
                root,
                packets=[
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0001",
                        "packet_id": "rev_pkt_live",
                        "trace_id": "trace_finding",
                        "event_type": "packet_posted",
                        "status": "pending",
                        "from_agent": "claude",
                        "to_agent": "codex",
                        "kind": "finding",
                        "summary": "Live finding packet",
                        "approval_required": False,
                        "target_ref": "dashboard.py",
                        "pipeline_generation": "gen-123",
                        "expires_at_utc": (
                            now + timedelta(minutes=30)
                        ).isoformat().replace("+00:00", "Z"),
                    },
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0002",
                        "packet_id": "rev_pkt_history",
                        "trace_id": "trace_finding",
                        "event_type": "packet_posted",
                        "status": "pending",
                        "from_agent": "claude",
                        "to_agent": "codex",
                        "kind": "finding",
                        "summary": "Applied finding packet",
                        "approval_required": False,
                        "target_ref": "dashboard.py",
                        "pipeline_generation": "gen-123",
                    },
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0003",
                        "packet_id": "rev_pkt_history",
                        "trace_id": "trace_finding",
                        "event_type": "packet_applied",
                        "status": "applied",
                        "from_agent": "claude",
                        "to_agent": "codex",
                        "kind": "finding",
                        "summary": "Applied finding packet",
                        "approval_required": False,
                        "target_ref": "dashboard.py",
                        "pipeline_generation": "gen-123",
                    },
                ],
            )

            queue = load_pending_packet_queue(root)

        self.assertEqual(len(queue.pending_packets), 1)
        self.assertEqual(queue.pending_packets[0]["packet_id"], "rev_pkt_live")

    def test_scope_bridge_instruction_refuses_pending_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _bridge_text(
                    verdict="- changes_requested",
                    findings="- F1: keep prior finding visible",
                    instruction="- hold steady",
                ),
                encoding="utf-8",
            )
            plan_path = root / "dev/active/platform_authority_loop.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(
                _plan_text("Preserve reviewer packet truth before scoped launch."),
                encoding="utf-8",
            )
            _write_pending_packet(root)

            with self.assertRaisesRegex(ValueError, "pending review packet"):
                scope_bridge_instruction(
                    repo_root=root,
                    bridge_path=bridge_path,
                    scope_plan_path=plan_path,
                )

    def test_promote_bridge_instruction_refuses_pending_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _bridge_text(
                    verdict="- accepted",
                    findings="- none",
                    instruction="- next unchecked plan item",
                ),
                encoding="utf-8",
            )
            plan_path = root / "dev/active/platform_authority_loop.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(
                _plan_text("Expose active agent/runtime counts to the operator."),
                encoding="utf-8",
            )
            _write_pending_packet(root)

            with self.assertRaisesRegex(ValueError, "pending review packet"):
                promote_bridge_instruction(
                    repo_root=root,
                    bridge_path=bridge_path,
                    promotion_plan_path=plan_path,
                )
