"""Focused tests for pending-packet rewrite guards on review-channel instructions."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.bridge_support import (
    apply_scope_if_requested,
)
from dev.scripts.devctl.review_channel.pending_packets import (
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

    def test_reviewer_guard_ignores_packets_for_other_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_pending_packet(root, to_agent="claude")

            assert_no_pending_reviewer_packets(
                repo_root=root,
                action_label="reviewer checkpoint",
            )

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
