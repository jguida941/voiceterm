"""Focused tests for review-channel planning-packet plumbing."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.tests.test_review_channel_context_refs import (
    _review_channel_text,
)
from dev.scripts.devctl.review_channel.events import (
    post_packet,
    refresh_event_bundle,
    resolve_artifact_paths,
    transition_packet,
)
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketGuardBundleEvidenceFields,
    PacketPostRequest,
    PacketRuntimeApprovalFields,
    PacketTargetFields,
    PacketTransitionRequest,
    packet_kind_schema,
    validate_post_request,
)
from dev.scripts.devctl.review_channel.packet_attestation import (
    PacketGuardAttestation,
)
from dev.scripts.devctl.runtime.master_plan_contract import PlanProposal


class ReviewChannelPlanPacketTests(unittest.TestCase):
    def test_packet_kind_schema_requires_body_uniformly(self) -> None:
        self.assertTrue(packet_kind_schema("finding").body_required)
        with self.assertRaisesRegex(ValueError, "body is required"):
            validate_post_request(
                PacketPostRequest(
                    from_agent="codex",
                    to_agent="claude",
                    kind="finding",
                    summary="Finding body is required",
                    body="",
                ),
                valid_agent_ids=("codex", "claude"),
            )

    def test_carrier_packet_rejects_plan_proposal(self) -> None:
        with self.assertRaisesRegex(ValueError, "Carrier packet kinds"):
            validate_post_request(
                PacketPostRequest(
                    from_agent="codex",
                    to_agent="claude",
                    kind="system_notice",
                    summary="Carrier cannot mutate plan",
                    body="This notice must remain communication-only.",
                    plan_proposal=PlanProposal(
                        target_ref="plan://MP-377/platform_authority_loop",
                        mutation_op="update_status",
                    ),
                ),
                valid_agent_ids=("codex", "claude"),
            )

    def test_cli_accepts_plan_gap_review_target_fields(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "post",
                "--from-agent",
                "codex",
                "--to-agent",
                "claude",
                "--kind",
                "plan_gap_review",
                "--summary",
                "Gap review on checklist closure",
                "--body",
                "The current plan still needs explicit closure evidence.",
                "--target-kind",
                "plan",
                "--target-ref",
                "plan://MP-377/platform_authority_loop",
                "--target-revision",
                "sha256:abc123",
                "--anchor-ref",
                "checklist:phase_2a",
                "--anchor-ref",
                "progress:finding_closure_gate",
                "--intake-ref",
                "intake://session-2026-03-19",
            ]
        )

        self.assertEqual(args.kind, "plan_gap_review")
        self.assertEqual(args.target_kind, "plan")
        self.assertEqual(args.target_ref, "plan://MP-377/platform_authority_loop")
        self.assertEqual(args.target_revision, "sha256:abc123")
        self.assertEqual(
            args.anchor_ref,
            ["checklist:phase_2a", "progress:finding_closure_gate"],
        )
        self.assertEqual(args.intake_ref, "intake://session-2026-03-19")

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

    def test_cli_accepts_full_guard_bundle_evidence(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "post",
                "--from-agent",
                "codex",
                "--to-agent",
                "claude",
                "--kind",
                "action_request",
                "--summary",
                "Stage verified commit pipeline",
                "--body",
                "Full guard profile passed.",
                "--requested-action",
                "stage_commit_pipeline",
                "--target-kind",
                "runtime",
                "--target-ref",
                "devctl_commit:abc123",
                "--target-revision",
                "abc123",
                "--full-guard-bundle-evidence=--profile ci",
            ]
        )

        self.assertEqual(args.full_guard_bundle_evidence, "--profile ci")

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
                    guard_attestation=PacketGuardAttestation(
                        packet_id=str(event["packet_id"]),
                        attestation_kind="plan_patch_guard",
                        plan_revision_before="sha256:before",
                        plan_revision_after="sha256:after",
                        mutation_op="append_progress_log",
                        attested_by="operator",
                    ),
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
        self.assertEqual(
            apply_event["metadata"]["guard_attestation"]["contract_id"],
            "PacketGuardAttestation",
        )

    def test_plan_target_proposal_collision_rejects_live_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)
            request = PacketPostRequest(
                from_agent="codex",
                to_agent="operator",
                kind="plan_patch_review",
                summary="Patch one plan row",
                body="Patch the same plan row once.",
                target=PacketTargetFields.from_values(
                    target_kind="plan",
                    target_ref="plan://MP-377/platform_authority_loop",
                    target_revision="sha256:abc123",
                    anchor_refs=["progress:proof_pass"],
                    intake_ref="intake://session-2026-03-19",
                    mutation_op="append_progress_log",
                ),
            )
            post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=request,
            )

            with self.assertRaisesRegex(ValueError, "PlanProposalConflict"):
                post_packet(
                    repo_root=root,
                    review_channel_path=review_channel_path,
                    artifact_paths=artifact_paths,
                    request=request,
                )

    def test_runtime_action_request_target_is_not_plan_proposal(self) -> None:
        request = PacketPostRequest(
            from_agent="codex",
            to_agent="claude",
            kind="action_request",
            summary="Run the same runtime check",
            body="Run the check; this is communication, not plan mutation.",
            requested_action="run_check",
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref="devctl_check:bundle.runtime",
                target_revision="0233390f",
            ),
        )

        validate_post_request(
            request,
            valid_agent_ids=("codex", "claude"),
            existing_packets=(
                {
                    "packet_id": "rev_pkt_runtime_existing",
                    "kind": "action_request",
                    "target_kind": "runtime",
                    "target_ref": "devctl_check:bundle.runtime",
                    "target_revision": "0233390f",
                    "requested_action": "run_check",
                    "status": "pending",
                },
            ),
        )

    def test_packet_apply_requires_guard_attestation_for_work_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)
            _, event = post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketPostRequest(
                    from_agent="codex",
                    to_agent="claude",
                    kind="action_request",
                    summary="Run guarded check",
                    body="Run a check and report the ActionResult.",
                    requested_action="run_check",
                    policy_hint="safe_auto_apply",
                    target=PacketTargetFields.from_values(
                        target_kind="runtime",
                        target_ref="guard:check_review_channel_bridge",
                        target_revision="tree-123",
                    ),
                ),
            )

            with self.assertRaisesRegex(ValueError, "PacketGuardAttestation"):
                transition_packet(
                    repo_root=root,
                    review_channel_path=review_channel_path,
                    artifact_paths=artifact_paths,
                    request=PacketTransitionRequest(
                        action="apply",
                        packet_id=str(event["packet_id"]),
                        actor="claude",
                    ),
                )

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
                    guard_attestation=PacketGuardAttestation(
                        packet_id=str(event["packet_id"]),
                        attestation_kind="commit_approval_guard",
                        run_record_ids=("run-guard",),
                        pipeline_generation="gen-9",
                        staged_snapshot_hash="tree-123",
                        operator_signature="operator",
                        attested_by="operator",
                    ),
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

    def test_operator_cannot_ack_or_apply_packet_targeted_to_another_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)

            _, event = post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketPostRequest(
                    from_agent="codex",
                    to_agent="claude",
                    kind="finding",
                    summary="Reviewer finding",
                    body="Claude should read this in its own lane.",
                ),
            )

            for action in ("ack", "apply"):
                with self.subTest(action=action):
                    verb = "acked" if action == "ack" else "applied"
                    with self.assertRaisesRegex(
                        ValueError,
                        f"Packet {event['packet_id']} can only be {verb} by claude.",
                    ):
                        transition_packet(
                            repo_root=root,
                            review_channel_path=review_channel_path,
                            artifact_paths=artifact_paths,
                            request=PacketTransitionRequest(
                                action=action,
                                packet_id=str(event["packet_id"]),
                                actor="operator",
                            ),
                        )

    def test_system_targeted_runtime_approval_remains_operator_owned(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)

            _, event = post_packet(
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
                    runtime_approval=PacketRuntimeApprovalFields.from_values(
                        pipeline_generation="gen-9",
                        staged_snapshot_hash="tree-123",
                        guard_results_summary="bundle.tooling pass",
                    ),
                ),
            )

            with self.assertRaisesRegex(
                ValueError,
                f"Packet {event['packet_id']} can only be applied by operator.",
            ):
                transition_packet(
                    repo_root=root,
                    review_channel_path=review_channel_path,
                    artifact_paths=artifact_paths,
                    request=PacketTransitionRequest(
                        action="apply",
                        packet_id=str(event["packet_id"]),
                        actor="system",
                    ),
                )

            refreshed, _ = transition_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketTransitionRequest(
                    action="apply",
                    packet_id=str(event["packet_id"]),
                    actor="operator",
                    guard_attestation=PacketGuardAttestation(
                        packet_id=str(event["packet_id"]),
                        attestation_kind="commit_approval_guard",
                        run_record_ids=("run-guard",),
                        pipeline_generation="gen-9",
                        staged_snapshot_hash="tree-123",
                        operator_signature="operator",
                        attested_by="operator",
                    ),
                ),
            )

            packet = next(
                row
                for row in refreshed.review_state["packets"]
                if row["packet_id"] == event["packet_id"]
            )
            self.assertEqual(packet["status"], "applied")

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


    def test_action_request_packet_posts_and_transitions_through_event_store(self) -> None:
        """Action request packets use the same event transport as all other packets."""
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
                    to_agent="claude",
                    kind="action_request",
                    summary="Run focused bridge check",
                    body="python3 dev/scripts/checks/check_review_channel_bridge.py",
                    evidence_refs=(),
                    context_pack_refs=(),
                    confidence=1.0,
                    requested_action="run_check",
                    policy_hint="safe_auto_apply",
                    approval_required=False,
                    target=PacketTargetFields.from_values(
                        target_kind="runtime",
                        target_ref="guard:check_review_channel_bridge",
                        target_revision="tree-123",
                    ),
                ),
            )

            # Verify the packet landed with the correct kind and status
            posted_packet = bundle.review_state["packets"][0]
            self.assertEqual(posted_packet["kind"], "action_request")
            self.assertEqual(posted_packet["status"], "pending")
            self.assertEqual(posted_packet["requested_action"], "run_check")
            self.assertEqual(
                posted_packet["delivery_emitted_at_utc"],
                posted_packet["posted_at"],
            )
            self.assertEqual(posted_packet["delivery_observed_at_utc"], "")
            self.assertEqual(
                posted_packet["body"],
                "python3 dev/scripts/checks/check_review_channel_bridge.py",
            )
            self.assertEqual(posted_packet["target_kind"], "runtime")
            self.assertEqual(
                posted_packet["target_ref"],
                "guard:check_review_channel_bridge",
            )

            # Transition the packet to applied via the same event store
            refreshed, apply_event = transition_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketTransitionRequest(
                    action="apply",
                    packet_id=str(event["packet_id"]),
                    actor="claude",
                    guard_attestation=PacketGuardAttestation(
                        packet_id=str(event["packet_id"]),
                        attestation_kind="run_check_result",
                        action_result_ids=("action-result-bridge-check",),
                        attested_by="claude",
                    ),
                ),
            )
            applied_packet = next(
                p for p in refreshed.review_state["packets"]
                if p["packet_id"] == event["packet_id"]
            )
            self.assertEqual(applied_packet["status"], "applied")
            self.assertTrue(applied_packet["execution_started_at_utc"])
            self.assertEqual(applied_packet["execution_started_by"], "claude")
            self.assertEqual(apply_event["kind"], "action_request")

    def test_inbox_marks_action_request_packet_observed(self) -> None:
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
                    from_agent="codex",
                    to_agent="claude",
                    kind="action_request",
                    summary="Run focused bridge check",
                    body="python3 dev/scripts/checks/check_review_channel_bridge.py",
                    evidence_refs=(),
                    context_pack_refs=(),
                    confidence=1.0,
                    requested_action="run_check",
                    policy_hint="safe_auto_apply",
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
                    "inbox",
                    "--target",
                    "claude",
                    "--actor",
                    "claude",
                    "--status",
                    "pending",
                    "--terminal",
                    "none",
                    "--format",
                    "json",
                ]
            )

            from dev.scripts.devctl.commands.review_channel.event_handler import (
                _run_event_action,
            )

            report, exit_code = _run_event_action(
                args=args,
                repo_root=root,
                paths={
                    "review_channel_path": review_channel_path,
                    "artifact_paths": artifact_paths,
                },
            )

        self.assertEqual(exit_code, 0)
        packet = report["packets"][0]
        self.assertEqual(packet["packet_id"], "rev_pkt_0001")
        self.assertEqual(packet["delivery_observed_by"], "claude")
        self.assertTrue(packet["delivery_observed_at_utc"])
        self.assertEqual(
            report["queue"]["derived_next_instruction_source"]["control_state"],
            "execution_pending",
        )
        self.assertTrue(
            report["queue"]["derived_next_instruction_source"]["wake_required"]
        )

    def test_expired_inbox_surfaces_stale_action_request_without_delivery_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)
            event_log_path = Path(artifact_paths.event_log_path)
            event_log_path.parent.mkdir(parents=True, exist_ok=True)
            expired_at = (
                datetime.now(timezone.utc) - timedelta(minutes=30)
            ).isoformat().replace("+00:00", "Z")
            event_log_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "event_id": "rev_evt_0001",
                        "session_id": "session-1",
                        "project_id": "proj-1",
                        "packet_id": "rev_pkt_0001",
                        "trace_id": "trace_0001",
                        "timestamp_utc": "2026-04-15T02:00:00Z",
                        "source": "review_channel",
                        "plan_id": "MP-377",
                        "event_type": "packet_posted",
                        "from_agent": "codex",
                        "to_agent": "claude",
                        "kind": "action_request",
                        "summary": "Re-check the stale packet path",
                        "body": "run the expired inbox visibility proof",
                        "requested_action": "review_only",
                        "policy_hint": "review_only",
                        "approval_required": False,
                        "status": "pending",
                        "expires_at_utc": expired_at,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            parser = build_parser()
            args = parser.parse_args(
                [
                    "review-channel",
                    "--action",
                    "inbox",
                    "--target",
                    "claude",
                    "--status",
                    "expired",
                    "--terminal",
                    "none",
                    "--format",
                    "json",
                ]
            )

            from dev.scripts.devctl.commands.review_channel.event_handler import (
                _run_event_action,
            )

            report, exit_code = _run_event_action(
                args=args,
                repo_root=root,
                paths={
                    "review_channel_path": review_channel_path,
                    "artifact_paths": artifact_paths,
                },
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["queue"]["stale_packet_count"], 1)
        self.assertEqual(
            [packet["packet_id"] for packet in report["packets"]],
            ["rev_pkt_0001"],
        )
        self.assertEqual(report["packets"][0]["delivery_observed_at_utc"], "")
        self.assertEqual(report["packets"][0]["delivery_observed_by"], "")

    def test_action_request_priority_drives_queue_instruction_after_later_instruction_post(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)

            bundle, action_event = post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketPostRequest(
                    from_agent="claude",
                    to_agent="codex",
                    kind="action_request",
                    summary="Execute the governed push",
                    body="push the reviewed slice",
                    evidence_refs=(),
                    context_pack_refs=(),
                    confidence=1.0,
                    requested_action="push",
                    policy_hint="review_only",
                    approval_required=False,
                    target=PacketTargetFields.from_values(
                        target_kind="runtime",
                        target_ref="remote_commit_pipeline:pipeline-123",
                        target_revision="gen-9",
                    ),
                    runtime_approval=PacketRuntimeApprovalFields.from_values(
                        pipeline_generation="gen-9",
                        staged_snapshot_hash="tree-123",
                        guard_results_summary="bundle.tooling pass",
                    ),
                ),
            )
            parser = build_parser()
            inbox_args = parser.parse_args(
                [
                    "review-channel",
                    "--action",
                    "inbox",
                    "--target",
                    "codex",
                    "--status",
                    "pending",
                    "--terminal",
                    "none",
                    "--format",
                    "json",
                ]
            )

            from dev.scripts.devctl.commands.review_channel.event_handler import (
                _run_event_action,
            )

            _run_event_action(
                args=inbox_args,
                repo_root=root,
                paths={
                    "review_channel_path": review_channel_path,
                    "artifact_paths": artifact_paths,
                },
            )
            post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketPostRequest(
                    from_agent="claude",
                    to_agent="codex",
                    kind="instruction",
                    summary="Later commentary packet",
                    body="narrative update",
                    evidence_refs=(),
                    context_pack_refs=(),
                    confidence=1.0,
                    requested_action="review_only",
                    policy_hint="review_only",
                    approval_required=False,
                ),
            )

            bundle = refresh_event_bundle(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )

        self.assertEqual(
            bundle.review_state["queue"]["derived_next_instruction_source"]["packet_id"],
            action_event["packet_id"],
        )
        self.assertEqual(
            bundle.review_state["queue"]["derived_next_instruction_source"]["selection_policy"],
            "action_request_priority",
        )
        self.assertTrue(
            bundle.review_state["queue"]["derived_next_instruction"].startswith(
                "Priority action_request: Execute the governed push"
            )
        )

    def test_runtime_action_request_packets_require_typed_runtime_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)

            with self.assertRaisesRegex(
                ValueError,
                "Runtime action_request packets must set --target-kind runtime",
            ):
                post_packet(
                    repo_root=root,
                    review_channel_path=review_channel_path,
                    artifact_paths=artifact_paths,
                    request=PacketPostRequest(
                        from_agent="codex",
                        to_agent="claude",
                        kind="action_request",
                        summary="Commit the current staged changes",
                        body="-m 'fix: resolve bridge drift'",
                        requested_action="commit",
                        policy_hint="safe_auto_apply",
                        approval_required=False,
                    ),
                )

    def test_stage_commit_pipeline_requires_full_guard_bundle_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)

            with self.assertRaisesRegex(
                ValueError,
                "Stage-commit action_request packets require "
                "--full-guard-bundle-evidence",
            ):
                post_packet(
                    repo_root=root,
                    review_channel_path=review_channel_path,
                    artifact_paths=artifact_paths,
                    request=PacketPostRequest(
                        from_agent="codex",
                        to_agent="claude",
                        kind="action_request",
                        summary="Stage verified commit pipeline",
                        body="Full guard evidence was omitted.",
                        requested_action="stage_commit_pipeline",
                        policy_hint="safe_auto_apply",
                        approval_required=False,
                        target=PacketTargetFields.from_values(
                            target_kind="runtime",
                            target_ref="devctl_commit:abc123",
                            target_revision="abc123",
                        ),
                    ),
                )

    def test_stage_commit_pipeline_preserves_full_guard_bundle_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)
            session_dir = Path(artifact_paths.projections_root) / "sessions"
            session_dir.mkdir(parents=True, exist_ok=True)
            (session_dir / "codex-conductor.json").write_text(
                json.dumps(
                    {
                        "provider": "codex",
                        "role": "review_agent",
                        "session_name": "codex-conductor",
                        "prepared_at": "2026-04-27T20:00:00Z",
                        "prepared_session_token": "session-token-1",
                        "prepared_head_sha": "abc123",
                        "prepared_instruction_revision": "rev-1",
                        "workspace_root": str(root),
                    }
                ),
                encoding="utf-8",
            )

            bundle, event = post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketPostRequest(
                    from_agent="codex",
                    to_agent="claude",
                    kind="action_request",
                    summary="Stage verified commit pipeline",
                    body="Full guard profile passed.",
                    requested_action="stage_commit_pipeline",
                    policy_hint="safe_auto_apply",
                    approval_required=False,
                    target=PacketTargetFields.from_values(
                        target_kind="runtime",
                        target_ref="devctl_commit:abc123",
                        target_revision="abc123",
                    ),
                    guard_bundle_evidence=PacketGuardBundleEvidenceFields.from_values(
                        full_guard_bundle_evidence="--profile ci",
                    ),
                ),
            )

            posted_packet = bundle.review_state["packets"][0]
            outcome_events = [
                json.loads(line)
                for line in Path(artifact_paths.event_log_path)
                .read_text(encoding="utf-8")
                .splitlines()
                if '"event_type": "agent_session_outcome"' in line
            ]
            session_outcomes = bundle.review_state["collaboration"][
                "session_outcomes"
            ]

            self.assertEqual(
                posted_packet["requested_action"],
                "stage_commit_pipeline",
            )
            self.assertEqual(
                posted_packet["full_guard_bundle_evidence"],
                "--profile ci",
            )
            self.assertEqual(outcome_events[0]["outcome"], "completed_handoff")
            self.assertEqual(
                outcome_events[0]["handoff_packet_id"],
                event["packet_id"],
            )
            self.assertEqual(
                outcome_events[0]["prepared_session_token"],
                "session-token-1",
            )
            self.assertEqual(session_outcomes[0]["outcome"], "completed_handoff")
            self.assertEqual(session_outcomes[0]["provider"], "codex")

    def test_system_stage_commit_pipeline_safe_auto_applies(self) -> None:
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
                    from_agent="system",
                    to_agent="claude",
                    kind="action_request",
                    summary="Stage verified commit pipeline",
                    body="Full guard profile passed.",
                    requested_action="stage_commit_pipeline",
                    policy_hint="safe_auto_apply",
                    approval_required=False,
                    target=PacketTargetFields.from_values(
                        target_kind="runtime",
                        target_ref="devctl_commit:abc123",
                        target_revision="abc123",
                    ),
                    guard_bundle_evidence=PacketGuardBundleEvidenceFields.from_values(
                        full_guard_bundle_evidence="--profile ci",
                    ),
                ),
            )

            packet = bundle.review_state["packets"][0]
            events = [
                json.loads(line)
                for line in Path(artifact_paths.event_log_path)
                .read_text(encoding="utf-8")
                .splitlines()
            ]

        self.assertEqual(packet["status"], "applied")
        self.assertEqual(packet["acked_by"], "system")
        self.assertEqual(packet["execution_started_by"], "system")
        self.assertEqual(packet["full_guard_bundle_evidence"], "--profile ci")
        self.assertEqual(len(event["safe_auto_apply_event_ids"]), 2)
        self.assertIn("packet_acked", {row["event_type"] for row in events})
        self.assertIn("packet_applied", {row["event_type"] for row in events})

    def test_commit_action_request_packets_preserve_runtime_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)

            bundle, _ = post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketPostRequest(
                    from_agent="codex",
                    to_agent="claude",
                    kind="action_request",
                    summary="Commit the current staged changes",
                    body="Commit the approved remote-commit pipeline.",
                    requested_action="commit",
                    policy_hint="operator_approval_required",
                    approval_required=True,
                    target=PacketTargetFields.from_values(
                        target_kind="runtime",
                        target_ref="remote_commit_pipeline:pipeline-123",
                        target_revision="gen-9",
                    ),
                    runtime_approval=PacketRuntimeApprovalFields.from_values(
                        pipeline_generation="gen-9",
                        staged_snapshot_hash="tree-123",
                        guard_results_summary="bundle.tooling pass",
                    ),
                ),
            )

            posted_packet = bundle.review_state["packets"][0]

        self.assertEqual(posted_packet["kind"], "action_request")
        self.assertEqual(posted_packet["requested_action"], "commit")
        self.assertEqual(posted_packet["target_kind"], "runtime")
        self.assertEqual(
            posted_packet["target_ref"],
            "remote_commit_pipeline:pipeline-123",
        )
        self.assertEqual(posted_packet["pipeline_generation"], "gen-9")
        self.assertEqual(posted_packet["staged_snapshot_hash"], "tree-123")


if __name__ == "__main__":
    unittest.main()
