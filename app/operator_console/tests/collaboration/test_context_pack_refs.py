"""Focused tests for operator-console collaboration context-pack handling."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.operator_console.workflows import build_operator_decision_command
from app.operator_console.state.core.models import ApprovalRequest, ContextPackRef
from app.operator_console.collaboration.context_pack_refs import (
    context_pack_ref_lines,
    parse_context_pack_refs,
)
from app.operator_console.state.review.operator_decisions import (
    approval_request_from_payload,
    record_operator_decision,
)
from app.operator_console.state.review.review_state import parse_pending_approvals


def _approval(*, pack_kind: str = "task_pack") -> ApprovalRequest:
    return ApprovalRequest(
        packet_id="pkt-1",
        from_agent="codex",
        to_agent="operator",
        summary="Approve guarded push",
        body="Need operator approval before push.",
        policy_hint="operator_approval_required",
        requested_action="git_push",
        status="pending",
        evidence_refs=("bridge.md#L1",),
        context_pack_refs=(
            ContextPackRef(
                pack_kind=pack_kind,
                pack_ref=".voiceterm/memory/exports/task_pack.json",
                adapter_profile="canonical",
                generated_at_utc="2026-03-09T13:30:00Z",
            ),
        ),
    )


class OperatorConsoleContextPackRefTests(unittest.TestCase):
    def test_parse_context_pack_refs_deduplicates_rows(self) -> None:
        refs = parse_context_pack_refs(
            [
                {"pack_kind": "task_pack", "pack_ref": "a.json"},
                {"pack_kind": "task_pack", "pack_ref": "a.json"},
            ]
        )

        self.assertEqual(len(refs), 1)
        self.assertEqual(context_pack_ref_lines(refs), ("task_pack: a.json",))

    def test_parse_pending_approvals_reads_context_pack_refs(self) -> None:
        approvals = parse_pending_approvals(
            {
                "packets": [
                    {
                        "packet_id": "pkt-1",
                        "from_agent": "codex",
                        "to_agent": "operator",
                        "summary": "Approve guarded push",
                        "body": "Need operator approval before push.",
                        "policy_hint": "operator_approval_required",
                        "requested_action": "git_push",
                        "approval_required": True,
                        "status": "pending",
                        "context_pack_refs": [
                            {
                                "pack_kind": "session_handoff",
                                "pack_ref": ".voiceterm/memory/exports/session_handoff.json",
                                "adapter_profile": "claude",
                            }
                        ],
                    }
                ]
            }
        )

        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0].context_pack_refs[0].pack_kind, "handoff_pack")
        self.assertEqual(
            approvals[0].context_pack_refs[0].pack_ref,
            ".voiceterm/memory/exports/session_handoff.json",
        )

    def test_build_operator_decision_command_includes_context_pack_refs(self) -> None:
        command = build_operator_decision_command(
            approval=_approval(),
            decision="approve",
            note="Looks good.",
        )

        payload = json.loads(command[command.index("--approval-json") + 1])
        self.assertEqual(
            payload["context_pack_refs"],
            [
                {
                    "pack_kind": "task_pack",
                    "pack_ref": ".voiceterm/memory/exports/task_pack.json",
                    "adapter_profile": "canonical",
                    "generated_at_utc": "2026-03-09T13:30:00Z",
                }
            ],
        )

    def test_operator_decision_payload_round_trips_context_pack_refs(self) -> None:
        approval = approval_request_from_payload(
            {
                "packet_id": "pkt-1",
                "from_agent": "codex",
                "to_agent": "operator",
                "summary": "Approve guarded push",
                "body": "Need operator approval before push.",
                "policy_hint": "operator_approval_required",
                "requested_action": "git_push",
                "status": "pending",
                "evidence_refs": ["bridge.md#L1"],
                "context_pack_refs": [
                    {
                        "pack_kind": "task_pack",
                        "pack_ref": ".voiceterm/memory/exports/task_pack.json",
                        "adapter_profile": "canonical",
                    }
                ],
            }
        )

        self.assertEqual(len(approval.context_pack_refs), 1)
        self.assertEqual(approval.context_pack_refs[0].pack_kind, "task_pack")

    def test_record_operator_decision_writes_context_pack_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact = record_operator_decision(
                Path(tmpdir),
                approval=_approval(),
                decision="approve",
            )
            latest_payload = json.loads(
                Path(artifact.latest_json_path).read_text(encoding="utf-8")
            )

        self.assertEqual(
            latest_payload["context_pack_refs"],
            [
                {
                    "pack_kind": "task_pack",
                    "pack_ref": ".voiceterm/memory/exports/task_pack.json",
                    "adapter_profile": "canonical",
                    "generated_at_utc": "2026-03-09T13:30:00Z",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
