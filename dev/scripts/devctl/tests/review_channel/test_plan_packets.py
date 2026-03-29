"""Focused tests for review-channel planning-packet plumbing."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.tests.test_review_channel_context_refs import (
    _review_channel_text,
)
from dev.scripts.devctl.review_channel.events import (
    post_packet,
    resolve_artifact_paths,
    transition_packet,
)
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketPostRequest,
    PacketTargetFields,
    PacketTransitionRequest,
)


class ReviewChannelPlanPacketTests(unittest.TestCase):
    def test_plan_patch_review_packets_preserve_plan_fields_through_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)

            bundle, event = post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketPostRequest(
                    from_agent="codex",
                    to_agent="operator",
                    kind="plan_patch_review",
                    summary="Apply accepted planning patch",
                    body="Patch the canonical plan progress log and ready gate.",
                    evidence_refs=("dev/active/platform_authority_loop.md#L412",),
                    context_pack_refs=(),
                    confidence=1.0,
                    requested_action="patch_plan",
                    policy_hint="operator_approval_required",
                    approval_required=True,
                    target=PacketTargetFields.from_values(
                        target_kind="plan",
                        target_ref="plan://MP-377/platform_authority_loop",
                        target_revision="sha256:abc123",
                        anchor_refs=["progress:proof_pass", "checklist:phase_1"],
                        intake_ref="intake://session-2026-03-19",
                        mutation_op="append_progress_log",
                    ),
                ),
            )
            refreshed, apply_event = transition_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketTransitionRequest(
                    action="apply",
                    packet_id=str(event["packet_id"]),
                    actor="operator",
                ),
            )

            packet = next(
                packet_row
                for packet_row in refreshed.review_state["packets"]
                if packet_row["packet_id"] == event["packet_id"]
            )

        self.assertEqual(bundle.review_state["packets"][0]["target_kind"], "plan")
        self.assertEqual(
            bundle.review_state["packets"][0]["target_ref"],
            "plan://MP-377/platform_authority_loop",
        )
        self.assertEqual(
            bundle.review_state["packets"][0]["anchor_refs"],
            ["progress:proof_pass", "checklist:phase_1"],
        )
        self.assertEqual(
            bundle.review_state["packets"][0]["mutation_op"],
            "append_progress_log",
        )
        self.assertEqual(packet["target_revision"], "sha256:abc123")
        self.assertEqual(packet["intake_ref"], "intake://session-2026-03-19")
        self.assertEqual(
            apply_event["anchor_refs"],
            ["progress:proof_pass", "checklist:phase_1"],
        )
        self.assertEqual(apply_event["mutation_op"], "append_progress_log")

    def test_plan_patch_review_packets_require_mutation_op(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)

            with self.assertRaisesRegex(
                ValueError,
                "require a valid --mutation-op",
            ):
                post_packet(
                    repo_root=root,
                    review_channel_path=review_channel_path,
                    artifact_paths=artifact_paths,
                    request=PacketPostRequest(
                        from_agent="codex",
                        to_agent="operator",
                        kind="plan_patch_review",
                        summary="Apply accepted planning patch",
                        body="Patch the canonical plan progress log and ready gate.",
                        evidence_refs=(),
                        context_pack_refs=(),
                        confidence=1.0,
                        requested_action="patch_plan",
                        policy_hint="operator_approval_required",
                        approval_required=True,
                        target=PacketTargetFields.from_values(
                            target_kind="plan",
                            target_ref="plan://MP-377/platform_authority_loop",
                            target_revision="sha256:abc123",
                            anchor_refs=["progress:proof_pass"],
                            intake_ref="intake://session-2026-03-19",
                        ),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
