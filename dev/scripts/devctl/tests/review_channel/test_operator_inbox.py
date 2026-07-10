"""Tests for the operator-facing review-channel inbox alias."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.review_channel.event_handler import _run_event_action
from dev.scripts.devctl.review_channel.events import (
    load_or_refresh_event_bundle,
    post_packet,
    resolve_artifact_paths,
)
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketPostRequest,
    PacketTargetFields,
)


def _review_channel_text() -> str:
    return "# Review Channel\n"


class OperatorInboxTests(unittest.TestCase):
    def test_cli_accepts_operator_inbox_action(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "operator-inbox",
                "--terminal",
                "none",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "review-channel")
        self.assertEqual(args.action, "operator-inbox")
        self.assertEqual(args.status, None)

    def test_operator_inbox_is_read_only_for_action_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)
            post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketPostRequest(
                    from_agent="claude",
                    to_agent="operator",
                    kind="action_request",
                    summary="Run bridge parity check",
                    body="python3 dev/scripts/checks/check_review_channel_bridge.py",
                    evidence_refs=(),
                    context_pack_refs=(),
                    confidence=1.0,
                    requested_action="run_check",
                    policy_hint="review_only",
                    approval_required=False,
                    target=PacketTargetFields.from_values(
                        target_kind="runtime",
                        target_ref="guard:check_review_channel_bridge",
                        target_revision="tree-123",
                    ),
                ),
            )
            parser = build_parser()
            args = parser.parse_args(
                [
                    "review-channel",
                    "--action",
                    "operator-inbox",
                    "--terminal",
                    "none",
                    "--format",
                    "json",
                ]
            )

            report, exit_code = _run_event_action(
                args=args,
                repo_root=root,
                paths={
                    "review_channel_path": review_channel_path,
                    "artifact_paths": artifact_paths,
                },
            )
            refreshed = load_or_refresh_event_bundle(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "ok")
        self.assertTrue(report["exit_ok"])
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["target"], "operator")
        self.assertEqual(report["status_filter"], "pending")
        packet = report["packets"][0]
        self.assertEqual(packet["packet_id"], "rev_pkt_0001")
        self.assertEqual(packet["to_agent"], "operator")
        self.assertEqual(packet["delivery_observed_by"], "")
        self.assertFalse(packet["delivery_observed_at_utc"])

        refreshed_packet = next(
            item
            for item in refreshed.review_state["packets"]
            if item["packet_id"] == "rev_pkt_0001"
        )
        self.assertEqual(refreshed_packet["delivery_observed_by"], "")
        self.assertFalse(refreshed_packet["delivery_observed_at_utc"])


if __name__ == "__main__":
    unittest.main()
