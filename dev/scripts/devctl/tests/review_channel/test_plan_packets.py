"""Focused tests for review-channel planning-packet plumbing."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.cli import build_parser
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
    PacketRuntimeApprovalFields,
    PacketTargetFields,
    PacketTransitionRequest,
)


class ReviewChannelPlanPacketTests(unittest.TestCase):
    def test_cli_accepts_runtime_commit_approval_fields(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "post",
                "--from-agent",
                "operator",
                "--to-agent",
                "system",
                "--kind",
                "commit_approval",
                "--summary",
                "Approve governed commit pipeline",
                "--body",
                "Operator approved the guarded staged snapshot.",
                "--target-kind",
                "runtime",
                "--target-ref",
                "remote_commit_pipeline:pipeline-123",
                "--target-revision",
                "gen-9",
                "--pipeline-generation",
                "gen-9",
                "--staged-snapshot-hash",
                "tree-123",
                "--guard-results-summary",
                "bundle.tooling pass; doctor still blocked on runtime_missing",
            ]
        )

        self.assertEqual(args.kind, "commit_approval")
        self.assertEqual(args.target_kind, "runtime")
        self.assertEqual(args.pipeline_generation, "gen-9")
        self.assertEqual(args.staged_snapshot_hash, "tree-123")
        self.assertEqual(
            args.guard_results_summary,
            "bundle.tooling pass; doctor still blocked on runtime_missing",
        )

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
                    guidance_refs=(
                        "probe_design_smells@dev/active/platform_authority_loop.md:412",
                    ),
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
            bundle.review_state["packets"][0]["guidance_refs"],
            ["probe_design_smells@dev/active/platform_authority_loop.md:412"],
        )
        self.assertEqual(
            bundle.review_state["packets"][0]["mutation_op"],
            "append_progress_log",
        )
        self.assertEqual(packet["target_revision"], "sha256:abc123")
        self.assertEqual(packet["intake_ref"], "intake://session-2026-03-19")
        self.assertEqual(
            packet["guidance_refs"],
            ["probe_design_smells@dev/active/platform_authority_loop.md:412"],
        )
        self.assertEqual(
            apply_event["anchor_refs"],
            ["progress:proof_pass", "checklist:phase_1"],
        )
        self.assertEqual(
            apply_event["guidance_refs"],
            ["probe_design_smells@dev/active/platform_authority_loop.md:412"],
        )
        self.assertEqual(apply_event["mutation_op"], "append_progress_log")

    def test_commit_approval_packets_preserve_runtime_fields_through_apply(self) -> None:
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
                    from_agent="operator",
                    to_agent="system",
                    kind="commit_approval",
                    summary="Approve governed commit pipeline",
                    body="Operator approved the guarded staged snapshot.",
                    evidence_refs=("dev/reports/review_channel/latest/guard.json",),
                    confidence=1.0,
                    requested_action="approve_commit_pipeline",
                    policy_hint="operator_approval_required",
                    approval_required=False,
                    target=PacketTargetFields.from_values(
                        target_kind="runtime",
                        target_ref="remote_commit_pipeline:pipeline-123",
                        target_revision="gen-9",
                    ),
                    runtime_approval=PacketRuntimeApprovalFields.from_values(
                        pipeline_generation="gen-9",
                        staged_snapshot_hash="tree-123",
                        guard_results_summary=(
                            "bundle.tooling pass; review-channel doctor "
                            "still reports runtime_missing"
                        ),
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
            actions_payload = json.loads(
                Path(refreshed.projection_paths.actions_path).read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(bundle.review_state["packets"][0]["target_kind"], "runtime")
        self.assertEqual(
            bundle.review_state["packets"][0]["target_ref"],
            "remote_commit_pipeline:pipeline-123",
        )
        self.assertEqual(bundle.review_state["packets"][0]["pipeline_generation"], "gen-9")
        self.assertEqual(
            bundle.review_state["packets"][0]["staged_snapshot_hash"],
            "tree-123",
        )
        self.assertEqual(
            packet["guard_results_summary"],
            "bundle.tooling pass; review-channel doctor still reports runtime_missing",
        )
        self.assertEqual(apply_event["pipeline_generation"], "gen-9")
        self.assertEqual(apply_event["staged_snapshot_hash"], "tree-123")
        self.assertEqual(
            actions_payload["actions"][0]["guard_results_summary"],
            "bundle.tooling pass; review-channel doctor still reports runtime_missing",
        )

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

    def test_commit_approval_packets_require_runtime_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)

            with self.assertRaisesRegex(
                ValueError,
                "require --pipeline-generation",
            ):
                post_packet(
                    repo_root=root,
                    review_channel_path=review_channel_path,
                    artifact_paths=artifact_paths,
                    request=PacketPostRequest(
                        from_agent="operator",
                        to_agent="system",
                        kind="commit_approval",
                        summary="Approve governed commit pipeline",
                        body="Operator approved the guarded staged snapshot.",
                        requested_action="approve_commit_pipeline",
                        policy_hint="operator_approval_required",
                        target=PacketTargetFields.from_values(
                            target_kind="runtime",
                            target_ref="remote_commit_pipeline:pipeline-123",
                            target_revision="gen-9",
                        ),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
