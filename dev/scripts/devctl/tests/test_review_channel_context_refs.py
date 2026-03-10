"""Focused tests for review-channel context-pack attachment plumbing."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands import review_channel as review_channel_command
from dev.scripts.devctl.review_channel.context_refs import resolve_context_pack_refs
from dev.scripts.devctl.review_channel.events import (
    post_packet,
    resolve_artifact_paths,
    transition_packet,
)


def _review_channel_text() -> str:
    return "\n".join(
        [
            "# Review Channel + Shared Screen Plan",
            "",
            "## Transitional Markdown Bridge (Current Operating Mode)",
            "",
            "| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |",
            "|---|---|---|---|---|---|",
            "| `AGENT-1` | Codex reviewer lane | `dev/active/review_channel.md` | `MP-355` | `../wt-a1` | `feature/a1` |",
        ]
    )


class ReviewChannelContextRefTests(unittest.TestCase):
    def test_resolve_context_pack_refs_aliases_session_handoff_and_reads_timestamp(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            export_path = root / ".voiceterm/memory/exports/session_handoff.json"
            export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_text(
                json.dumps(
                    {
                        "generated_at_utc": "2026-03-09T13:22:00Z",
                        "summary": "session handoff preview",
                    }
                ),
                encoding="utf-8",
            )
            args = SimpleNamespace(
                context_pack_ref=[
                    f"session_handoff:{export_path.relative_to(root).as_posix()}"
                ],
                context_pack_adapter_profile="claude",
            )

            refs = resolve_context_pack_refs(args, root)

        self.assertEqual(
            refs,
            [
                {
                    "pack_kind": "handoff_pack",
                    "pack_ref": ".voiceterm/memory/exports/session_handoff.json",
                    "adapter_profile": "claude",
                    "generated_at_utc": "2026-03-09T13:22:00Z",
                }
            ],
        )

    def test_command_module_uses_shared_context_pack_ref_resolver(self) -> None:
        self.assertIs(
            review_channel_command.resolve_context_pack_refs,
            resolve_context_pack_refs,
        )

    def test_event_packets_preserve_context_pack_refs_through_apply_and_actions_projection(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)
            context_pack_refs = [
                {
                    "pack_kind": "task_pack",
                    "pack_ref": ".voiceterm/memory/exports/task_pack.json",
                    "adapter_profile": "canonical",
                    "generated_at_utc": "2026-03-09T13:30:00Z",
                }
            ]

            bundle, event = post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                from_agent="codex",
                to_agent="operator",
                kind="approval_request",
                summary="Attach reviewed memory packs",
                body="Use the exported task pack for approval context.",
                evidence_refs=["code_audit.md#L1"],
                context_pack_refs=context_pack_refs,
                confidence=1.0,
                requested_action="approve_memory_context",
                policy_hint="operator_approval_required",
                approval_required=True,
            )
            refreshed, apply_event = transition_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                action="apply",
                packet_id=str(event["packet_id"]),
                actor="operator",
            )

            packet = next(
                packet_row
                for packet_row in refreshed.review_state["packets"]
                if packet_row["packet_id"] == event["packet_id"]
            )
            actions_payload = json.loads(
                Path(refreshed.projection_paths.actions_path).read_text(encoding="utf-8")
            )

        self.assertEqual(
            bundle.review_state["packets"][0]["context_pack_refs"],
            context_pack_refs,
        )
        self.assertEqual(packet["context_pack_refs"], context_pack_refs)
        self.assertEqual(apply_event["context_pack_refs"], context_pack_refs)
        self.assertEqual(
            actions_payload["actions"][0]["context_pack_refs"],
            context_pack_refs,
        )


if __name__ == "__main__":
    unittest.main()
