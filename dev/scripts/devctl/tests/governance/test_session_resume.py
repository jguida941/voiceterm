"""Tests for the session-resume command."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dev.scripts.devctl.commands.governance.session_resume import run
from dev.scripts.devctl.commands.governance.session_resume_authority_payload import (
    SessionResumeAuthorityPayload,
    SessionResumeCurrentSessionPayload,
    SessionResumePacketInboxPayload,
    build_session_resume_review_state_context,
)
from dev.scripts.devctl.commands.governance.session_resume_paths import (
    get_review_state_mtime,
    resolve_source_paths,
)
from dev.scripts.devctl.commands.governance.session_resume_support import (
    SessionCachePacket,
    build_from_sources,
    compute_blockers,
    derive_interaction_mode,
    derive_next_action,
    distill_key_rules,
    packet_from_mapping,
    try_cache_hit,
    write_cache,
)
from dev.scripts.devctl.runtime.authority_snapshot import AuthoritySnapshot
from dev.scripts.devctl.runtime.review_state_packet_models import (
    AgentAttentionRecord,
    PacketInboxState,
)
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
)


class TestSessionResumeAuthorityPayload(unittest.TestCase):
    """Authority payload serialization remains compact and behavior-stable."""

    def test_build_session_resume_authority_payload_serializes_nested_rows(self) -> None:
        payload = SessionResumeAuthorityPayload(
            reviewer_mode="tools_only",
            reviewer_freshness="fresh",
            operator_interaction_mode="local_terminal",
            observed_control_topology="no_live_agents",
            implementation_permission="blocked",
            attention={"status": "runtime_missing"},
            recovery_assessment={"decision": {"action_id": "ensure_runtime"}},
            current_session=SessionResumeCurrentSessionPayload(
                current_instruction="refresh the runtime",
                current_instruction_revision="rev-123",
                implementer_ack_state="missing",
            ),
            coordination=None,
            packet_inbox=SessionResumePacketInboxPayload.from_state(PacketInboxState(
                attention_revision="attn-123",
                agents=(
                    AgentAttentionRecord(
                        agent="codex",
                        current_instruction_packet_id="pkt-1",
                        latest_finding_packet_id="pkt-2",
                        pending_actionable_packet_ids=("pkt-a", "pkt-b"),
                        expired_unresolved_packet_ids=("pkt-c",),
                        attention_status="wake_required",
                        wake_reason="action_request_pending",
                        required_command="python3 dev/scripts/devctl.py review-channel --action inbox",
                        delivery_state="notified",
                    ),
                ),
            )),
            next_command="python3 dev/scripts/devctl.py review-channel --action status",
            governance={"push_enforcement": {"checkpoint_required": True}},
        ).to_dict()

        self.assertEqual(
            payload["current_session"],
            {
                "current_instruction": "refresh the runtime",
                "current_instruction_revision": "rev-123",
                "implementer_ack_state": "missing",
            },
        )
        self.assertEqual(
            payload["packet_inbox"],
            {
                "attention_revision": "attn-123",
                "agents": [
                    {
                        "agent": "codex",
                        "current_instruction_packet_id": "pkt-1",
                        "latest_finding_packet_id": "pkt-2",
                        "pending_actionable_total": 2,
                        "expired_unresolved_total": 1,
                        "attention_status": "wake_required",
                        "wake_reason": "action_request_pending",
                        "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox",
                        "delivery_state": "notified",
                    }
                ],
            },
        )
        self.assertEqual(
            payload["governance"],
            {"push_enforcement": {"checkpoint_required": True}},
        )

    def test_build_session_resume_review_state_context_uses_typed_role_agents(self) -> None:
        review_state_payload = {
            "collaboration": {
                "review_agent": "cursor",
                "coding_agent": "gemini",
                "role_assignments": (),
            },
            "queue": {
                "pending_total": 0,
                "stale_packet_count": 0,
            },
            "packet_inbox": {
                "attention_revision": "attn-123",
                "agents": [
                    {
                        "agent": "cursor",
                        "current_instruction_packet_id": "",
                        "latest_finding_packet_id": "",
                        "pending_actionable_packet_ids": [],
                        "expired_unresolved_packet_ids": ["rev_pkt_cursor_old"],
                        "attention_status": "review_needed",
                        "wake_reason": "expired_unresolved_packet",
                        "required_command": "",
                        "delivery_state": "notified",
                    },
                    {
                        "agent": "gemini",
                        "current_instruction_packet_id": "",
                        "latest_finding_packet_id": "",
                        "pending_actionable_packet_ids": [],
                        "expired_unresolved_packet_ids": [
                            "rev_pkt_gemini_old_1",
                            "rev_pkt_gemini_old_2",
                        ],
                        "attention_status": "review_needed",
                        "wake_reason": "expired_unresolved_packet",
                        "required_command": "",
                        "delivery_state": "notified",
                    },
                ],
            },
        }

        reviewer_context = build_session_resume_review_state_context(
            review_state_payload,
            fallback_open_findings="none",
            role="reviewer",
        )
        implementer_context = build_session_resume_review_state_context(
            review_state_payload,
            fallback_open_findings="none",
            role="implementer",
        )

        self.assertEqual(
            reviewer_context.open_findings,
            "1 expired unresolved review packet(s)",
        )
        self.assertEqual(
            implementer_context.open_findings,
            "2 expired unresolved review packet(s)",
        )


class TestSessionCachePacket(unittest.TestCase):
    """SessionCachePacket data contract tests."""

    def test_defaults(self) -> None:
        pkt = SessionCachePacket()
        self.assertEqual(pkt.schema_version, 3)
        self.assertEqual(pkt.contract_id, "SessionCachePacket")
        self.assertEqual(pkt.role, "implementer")
        self.assertEqual(pkt.blockers, "none")
        self.assertTrue(pkt.last_guard_ok)
        self.assertEqual(pkt.key_rules, ())
        self.assertEqual(pkt.head_at_push_time, "")
        self.assertEqual(pkt.operator_interaction_mode, "unresolved")
        self.assertEqual(pkt.resolved_phase, "idle")
        self.assertEqual(pkt.next_guard_bundle, "")
        self.assertEqual(pkt.next_recommended_command, "")
        self.assertIsNone(pkt.remote_control_attachment)

    def test_to_dict_converts_tuple(self) -> None:
        pkt = SessionCachePacket(key_rules=("a=1", "b=2"))
        d = pkt.to_dict()
        self.assertIsInstance(d["key_rules"], list)
        self.assertEqual(d["key_rules"], ["a=1", "b=2"])

    def test_roundtrip(self) -> None:
        original = SessionCachePacket(
            role="reviewer", branch="main", head_sha="abc123",
            blockers="checkpoint_required", key_rules=("safe_to_continue=True",),
        )
        restored = packet_from_mapping(original.to_dict())
        self.assertEqual(restored.role, original.role)
        self.assertEqual(restored.branch, original.branch)
        self.assertEqual(restored.head_sha, original.head_sha)
        self.assertEqual(restored.blockers, original.blockers)
        self.assertEqual(restored.key_rules, original.key_rules)

    def test_roundtrip_with_remote_control_attachment(self) -> None:
        original = SessionCachePacket(
            remote_control_attachment=RemoteControlAttachmentState(
                provider="claude",
                role="implementer",
                attachment_id="remote-attach-1",
                remote_session_id="session_abc123",
                status="attached",
            )
        )
        restored = packet_from_mapping(original.to_dict())
        self.assertIsNotNone(restored.remote_control_attachment)
        assert restored.remote_control_attachment is not None
        self.assertEqual(restored.remote_control_attachment.provider, "claude")

    def test_roundtrip_with_authority_snapshot(self) -> None:
        original = SessionCachePacket(
            authority_snapshot=AuthoritySnapshot(
                coordination_state="handshake_stale",
                current_instruction_revision="rev-123",
                implementer_ack_state="stale",
                actor_role="reviewer",
                actor_identity="codex",
                safe_to_continue=False,
            )
        )

        restored = packet_from_mapping(original.to_dict())

        self.assertIsNotNone(restored.authority_snapshot)
        assert restored.authority_snapshot is not None
        self.assertEqual(
            restored.authority_snapshot.coordination_state,
            "handshake_stale",
        )
        self.assertEqual(
            restored.authority_snapshot.current_instruction_revision,
            "rev-123",
        )
        self.assertEqual(restored.authority_snapshot.actor_role, "reviewer")
        self.assertEqual(restored.authority_snapshot.actor_identity, "codex")


class TestFieldDerivation(unittest.TestCase):
    """Blocker, interaction mode, next-action, and key-rules derivation."""

    def test_no_blockers(self) -> None:
        self.assertEqual(
            compute_blockers(checkpoint_required=False, safe_to_continue=True, authority_ok=True),
            "none",
        )

    def test_authority_failure(self) -> None:
        self.assertIn("startup_authority", compute_blockers(
            checkpoint_required=False, safe_to_continue=True, authority_ok=False,
        ))

    def test_checkpoint_required(self) -> None:
        self.assertEqual(compute_blockers(
            checkpoint_required=True, safe_to_continue=True, authority_ok=True,
        ), "checkpoint_required")

    def test_multiple_blockers(self) -> None:
        result = compute_blockers(checkpoint_required=True, safe_to_continue=False, authority_ok=False)
        for b in ("startup_authority", "checkpoint_required", "continuation_blocked"):
            self.assertIn(b, result)

    def test_interaction_mode_none_compact(self) -> None:
        self.assertEqual(derive_interaction_mode(None), "unresolved")

    def test_interaction_mode_no_collaboration(self) -> None:
        self.assertEqual(derive_interaction_mode({}), "unresolved")

    def test_interaction_mode_active_dual(self) -> None:
        self.assertEqual(
            derive_interaction_mode({"collaboration": {"reviewer_mode": "active_dual_agent"}}),
            "dual_agent",
        )

    def test_interaction_mode_single_agent(self) -> None:
        self.assertEqual(
            derive_interaction_mode({"collaboration": {"reviewer_mode": "single_agent"}}),
            "single_agent",
        )

    def test_interaction_mode_remote_control_attachment(self) -> None:
        self.assertEqual(
            derive_interaction_mode(
                {
                    "reviewer_runtime": {
                        "remote_control_attachment": {
                            "provider": "claude",
                            "session_name": "phone session",
                            "remote_session_id": "session_abc123",
                            "status": "attached",
                        }
                    }
                }
            ),
            "remote_control",
        )

    def test_next_action_no_receipt(self) -> None:
        self.assertIn("startup-context", derive_next_action(None, "none"))

    def test_next_action_blockers_with_command(self) -> None:
        self.assertEqual(
            derive_next_action({"push_next_step_command": "do-something"}, "checkpoint_required"),
            "do-something",
        )

    def test_next_action_blockers_without_command(self) -> None:
        self.assertIn("resolve blockers", derive_next_action({}, "startup_authority"))

    def test_next_action_run_push(self) -> None:
        self.assertIn("push --execute", derive_next_action({"push_action": "run_devctl_push"}, "none"))

    def test_next_action_default_bootstrap(self) -> None:
        self.assertIn("context-graph", derive_next_action({"push_action": "no_push_needed"}, "none"))

    def test_key_rules_length(self) -> None:
        rules = distill_key_rules(
            safe_to_continue=True, checkpoint_required=False,
            ack_current=True, review_gate_allows_push=True, last_guard_ok=True,
        )
        self.assertEqual(len(rules), 5)
        self.assertIn("safe_to_continue=True", rules)

    def test_key_rules_mixed(self) -> None:
        rules = distill_key_rules(
            safe_to_continue=False, checkpoint_required=True,
            ack_current=False, review_gate_allows_push=False, last_guard_ok=False,
        )
        self.assertIn("safe_to_continue=False", rules)
        self.assertIn("last_guard_ok=False", rules)


class TestCacheHitMiss(unittest.TestCase):
    """Cache hit and miss behavior tests."""

    def test_cache_miss_no_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(try_cache_hit(Path(td), head_sha="abc", role="implementer"))

    def test_cache_miss_wrong_sha(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
            cache_dir.mkdir(parents=True)
            pkt = SessionCachePacket(head_sha="old_sha", role="implementer")
            (cache_dir / "cache.json").write_text(json.dumps(pkt.to_dict()))
            self.assertIsNone(try_cache_hit(root, head_sha="new_sha", role="implementer"))

    def test_cache_miss_wrong_role(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
            cache_dir.mkdir(parents=True)
            pkt = SessionCachePacket(head_sha="abc", role="implementer")
            (cache_dir / "cache.json").write_text(json.dumps(pkt.to_dict()))
            self.assertIsNone(try_cache_hit(root, head_sha="abc", role="reviewer"))

    def test_cache_hit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
            cache_dir.mkdir(parents=True)
            pkt = SessionCachePacket(head_sha="abc123", role="implementer", branch="main")
            (cache_dir / "cache.json").write_text(json.dumps(pkt.to_dict()))
            result = try_cache_hit(root, head_sha="abc123", role="implementer")
            self.assertIsNotNone(result)
            self.assertEqual(result.branch, "main")

    def test_cache_miss_review_state_mtime_changed(self) -> None:
        """Cache invalidates when review_state.json mtime changes without a commit."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
            cache_dir.mkdir(parents=True)
            pkt = SessionCachePacket(
                head_sha="abc123", role="implementer", review_state_mtime=1000.0,
            )
            (cache_dir / "cache.json").write_text(json.dumps(pkt.to_dict()))
            # Same head and role but different mtime triggers a miss
            self.assertIsNone(try_cache_hit(
                root, head_sha="abc123", role="implementer", review_state_mtime=2000.0,
            ))

    def test_cache_hit_with_matching_mtime(self) -> None:
        """Cache hits when head, role, and review_state mtime all match."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
            cache_dir.mkdir(parents=True)
            pkt = SessionCachePacket(
                head_sha="abc123", role="implementer", review_state_mtime=42.5,
            )
            (cache_dir / "cache.json").write_text(json.dumps(pkt.to_dict()))
            result = try_cache_hit(
                root, head_sha="abc123", role="implementer", review_state_mtime=42.5,
            )
            self.assertIsNotNone(result)
            self.assertEqual(result.review_state_mtime, 42.5)

    def test_write_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkt = SessionCachePacket(head_sha="xyz", branch="develop")
            write_cache(root, pkt)
            cache_path = root / "dev" / "reports" / "session_cache" / "latest" / "cache.json"
            self.assertTrue(cache_path.is_file())
            payload = json.loads(cache_path.read_text())
            self.assertEqual(payload["head_sha"], "xyz")


class TestBuildFromSources(unittest.TestCase):
    """Integration test for building packet from source artifacts via read model."""

    def _make_sources(self, *, receipt=None, compact=None, review_state=None):
        """Build a sources dict matching the load_sources() shape."""
        return {
            "receipt": receipt,
            "review_state": review_state,
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": compact,
        }

    def test_build_with_receipt_and_compact(self) -> None:
        sources = self._make_sources(
            receipt={
                "current_branch": "feature/test",
                "advisory_action": "continue",
                "advisory_reason": "clean",
                "checkpoint_required": False,
                "safe_to_continue_editing": True,
                "startup_authority_ok": True,
                "review_gate_allows_push": True,
                "push_action": "no_push_needed",
                "operator_interaction_mode": "active_dual_agent",
            },
            compact={
                "current_session": {
                    "current_instruction": "Do the thing",
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "current",
                    "open_findings": "none",
                },
                "collaboration": {"reviewer_mode": "active_dual_agent"},
            },
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="sha1",
                sources_override=sources,
            )
            self.assertEqual(packet.branch, "unknown")  # git override returns "unknown"
            self.assertEqual(packet.current_instruction, "Do the thing")
            self.assertEqual(packet.ack_state, "current")
            self.assertTrue(packet.last_guard_ok)
            self.assertIn("ack_current=True", packet.key_rules)
            self.assertIsNotNone(packet.authority_snapshot)
            assert packet.authority_snapshot is not None
            self.assertEqual(packet.authority_snapshot.current_instruction_revision, "rev123")
            self.assertEqual(packet.authority_snapshot.implementer_ack_state, "current")

    def test_build_no_artifacts(self) -> None:
        sources = self._make_sources()
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="reviewer", head_sha="sha2",
                sources_override=sources,
            )
            self.assertEqual(packet.role, "reviewer")
            # No receipt means no push report either, so last_guard_ok defaults True
            self.assertTrue(packet.last_guard_ok)
            # No receipt means fail-closed: blockers must be bootstrap_required
            self.assertEqual(packet.blockers, "bootstrap_required")

    def test_build_uses_read_model_fields(self) -> None:
        """Prove build_from_sources delegates resolved state to ControlPlaneReadModel."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="2026-04-04T00:00:00Z",
            branch="read-model-branch",
            head_sha="rm_sha",
            worktree_clean=True,
            ahead_of_upstream=0,
            resolved_phase="idle",
            push_eligible=False,
            implementation_blocked=False,
            top_blocker="custom_blocker",
            next_action="do_something",
            next_command="python3 dev/scripts/devctl.py do-it",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="--",
            review_accepted=True,
            last_reviewed_sha="",
            attention_status="n/a",
            attention_summary="n/a",
            publisher_running=False,
            supervisor_running=False,
            codex_conductor_alive=False,
            claude_conductor_alive=False,
            pending_action_requests=0,
            last_guard_ok=False,
            check_details=(),
        )
        sources = self._make_sources(
            receipt={"advisory_action": "wait", "advisory_reason": "guard_fail"},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="sha3",
                read_model_override=model,
                sources_override=sources,
            )
            self.assertEqual(packet.branch, "read-model-branch")
            self.assertEqual(packet.blockers, "custom_blocker")
            self.assertEqual(packet.interaction_mode, "local_terminal")
            self.assertFalse(packet.last_guard_ok)
            self.assertEqual(packet.next_action, "python3 dev/scripts/devctl.py do-it")
            # advisory_action/reason now come from read model, not receipt
            self.assertEqual(packet.advisory_action, "do_something")
            self.assertEqual(packet.advisory_reason, "custom_blocker")
            self.assertIn("review_gate_allows_push=True", packet.key_rules)
            # v2 fields from read model
            self.assertEqual(packet.resolved_phase, "idle")
            self.assertEqual(packet.operator_interaction_mode, "local_terminal")
            self.assertEqual(packet.next_recommended_command, "python3 dev/scripts/devctl.py do-it")

    def test_build_from_sources_prefers_packet_backed_expired_findings_summary(self) -> None:
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="2026-04-04T00:00:00Z",
            branch="review-branch",
            head_sha="rm_sha",
            worktree_clean=True,
            ahead_of_upstream=0,
            resolved_phase="idle",
            push_eligible=False,
            implementation_blocked=False,
            top_blocker="1 pending review packet(s)",
            next_action="continue_review",
            next_command="python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="--",
            review_accepted=False,
            last_reviewed_sha="",
            attention_status="review_needed",
            attention_summary="stale packets need review",
            publisher_running=False,
            supervisor_running=False,
            codex_conductor_alive=False,
            claude_conductor_alive=False,
            pending_action_requests=0,
            last_guard_ok=True,
            check_details=(),
        )
        sources = self._make_sources(
            receipt={
                "advisory_action": "continue_review",
                "advisory_reason": "packet_attention",
                "checkpoint_required": False,
                "safe_to_continue_editing": True,
                "startup_authority_ok": True,
            },
            review_state={
                "current_session": {
                    "current_instruction": "Review the stale backlog",
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "missing",
                    "open_findings": "1 pending review packet(s)",
                },
                "queue": {
                    "pending_total": 0,
                    "pending_claude": 0,
                    "stale_packet_count": 1,
                    "derived_next_instruction": "",
                    "derived_next_instruction_source": {},
                },
                "packets": [
                    {
                        "packet_id": "rev_pkt_expired",
                        "status": "pending",
                        "kind": "action_request",
                        "from_agent": "operator",
                        "to_agent": "codex",
                        "summary": "Expired operator directive",
                        "body": "Still needs review.",
                        "requested_action": "review_only",
                        "expires_at_utc": "2000-01-01T00:00:00Z",
                    }
                ],
            },
        )

        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td),
                role="reviewer",
                head_sha="sha3",
                read_model_override=model,
                sources_override=sources,
            )

        self.assertEqual(
            packet.open_findings,
            "1 expired unresolved review packet(s)",
        )
        self.assertEqual(
            packet.blockers,
            "1 expired unresolved review packet(s)",
        )
        self.assertEqual(
            packet.advisory_reason,
            "1 expired unresolved review packet(s)",
        )


class TestRepoPackPaths(unittest.TestCase):
    """Paths resolve from active_path_config, not hardcoded literals."""

    @patch("dev.scripts.devctl.commands.governance.session_resume_paths.active_path_config")
    def test_resolve_source_paths_uses_active_config(self, mock_config) -> None:
        """resolve_source_paths reads review_status_dir_rel from repo-pack config."""
        from dev.scripts.devctl.repo_packs.voiceterm import RepoPathConfig

        custom = RepoPathConfig(review_status_dir_rel="custom/status/dir")
        mock_config.return_value = custom
        with tempfile.TemporaryDirectory() as td:
            paths = resolve_source_paths(Path(td), governance=None)
            self.assertEqual(paths["review_state"], Path("custom/status/dir/review_state.json"))
            self.assertEqual(paths["compact"], Path("custom/status/dir/compact.json"))

    @patch("dev.scripts.devctl.commands.governance.session_resume_paths.active_path_config")
    def test_get_review_state_mtime_uses_config_path(self, mock_config) -> None:
        """get_review_state_mtime resolves the review_state path via repo-pack config."""
        from dev.scripts.devctl.repo_packs.voiceterm import RepoPathConfig

        custom = RepoPathConfig(review_status_dir_rel="alt/review")
        mock_config.return_value = custom
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            alt_dir = root / "alt" / "review"
            alt_dir.mkdir(parents=True)
            rs_path = alt_dir / "review_state.json"
            rs_path.write_text(json.dumps({"current_session": {}}))
            mtime = get_review_state_mtime(root, governance=None)
            self.assertGreater(mtime, 0.0)

    @patch("dev.scripts.devctl.commands.governance.session_resume_paths.active_path_config")
    def test_get_review_state_mtime_absent_file(self, mock_config) -> None:
        from dev.scripts.devctl.repo_packs.voiceterm import RepoPathConfig

        mock_config.return_value = RepoPathConfig()
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(get_review_state_mtime(Path(td), governance=None), 0.0)


class TestGovernanceReviewRoot(unittest.TestCase):
    """session-resume paths resolve from governance review-root when available."""

    def _make_governance(self, review_root: str):
        from dev.scripts.devctl.runtime.project_governance_contract import (
            ArtifactRoots,
            BridgeConfig,
            BundleOverrides,
            EnabledChecks,
            MemoryRoots,
            PathRoots,
            PlanRegistry,
            ProjectGovernance,
            RepoIdentity,
            RepoPackRef,
        )

        return ProjectGovernance(
            schema_version=1,
            contract_id="ProjectGovernance",
            repo_identity=RepoIdentity(repo_name="test"),
            repo_pack=RepoPackRef(pack_id="test"),
            path_roots=PathRoots(),
            plan_registry=PlanRegistry(),
            artifact_roots=ArtifactRoots(review_root=review_root),
            memory_roots=MemoryRoots(),
            bridge_config=BridgeConfig(),
            enabled_checks=EnabledChecks(),
            bundle_overrides=BundleOverrides(overrides={}),
        )

    @patch("dev.scripts.devctl.commands.governance.session_resume_paths.active_path_config")
    def test_governance_review_root_overrides_config(self, mock_config) -> None:
        """When governance has a review_root, paths resolve from that root."""
        from dev.scripts.devctl.repo_packs.voiceterm import RepoPathConfig

        mock_config.return_value = RepoPathConfig(review_status_dir_rel="default/status")
        gov = self._make_governance("custom/governance/review")
        with tempfile.TemporaryDirectory() as td:
            paths = resolve_source_paths(Path(td), governance=gov)
            self.assertEqual(
                paths["review_state"],
                Path("custom/governance/review/review_state.json"),
            )
            self.assertEqual(
                paths["compact"],
                Path("custom/governance/review/compact.json"),
            )

    @patch("dev.scripts.devctl.commands.governance.session_resume_paths.active_path_config")
    def test_empty_governance_review_root_falls_back(self, mock_config) -> None:
        """When governance review_root is empty, repo-pack config is used."""
        from dev.scripts.devctl.repo_packs.voiceterm import RepoPathConfig

        mock_config.return_value = RepoPathConfig(review_status_dir_rel="fallback/dir")
        gov = self._make_governance("")
        with tempfile.TemporaryDirectory() as td:
            paths = resolve_source_paths(Path(td), governance=gov)
            self.assertEqual(
                paths["review_state"],
                Path("fallback/dir/review_state.json"),
            )

    @patch("dev.scripts.devctl.commands.governance.session_resume_paths.active_path_config")
    def test_no_governance_uses_config(self, mock_config) -> None:
        """Without governance, repo-pack config paths are used (backward compat)."""
        from dev.scripts.devctl.repo_packs.voiceterm import RepoPathConfig

        mock_config.return_value = RepoPathConfig(review_status_dir_rel="pack/status")
        with tempfile.TemporaryDirectory() as td:
            paths = resolve_source_paths(Path(td), governance=None)
            self.assertEqual(
                paths["review_state"],
                Path("pack/status/review_state.json"),
            )


class TestGovernanceInteractionMode(unittest.TestCase):
    """interaction_mode reads from governance BridgeConfig first, not reviewer_mode."""

    def _make_governance(self, interaction_mode: str):
        """Build a minimal ProjectGovernance with the given interaction_mode."""
        from dev.scripts.devctl.runtime.project_governance_contract import (
            ArtifactRoots,
            BridgeConfig,
            BundleOverrides,
            EnabledChecks,
            MemoryRoots,
            PathRoots,
            PlanRegistry,
            ProjectGovernance,
            RepoIdentity,
            RepoPackRef,
        )

        return ProjectGovernance(
            schema_version=1,
            contract_id="ProjectGovernance",
            repo_identity=RepoIdentity(repo_name="test"),
            repo_pack=RepoPackRef(pack_id="test"),
            path_roots=PathRoots(),
            plan_registry=PlanRegistry(),
            artifact_roots=ArtifactRoots(),
            memory_roots=MemoryRoots(),
            bridge_config=BridgeConfig(operator_interaction_mode=interaction_mode),
            enabled_checks=EnabledChecks(),
            bundle_overrides=BundleOverrides(overrides={}),
        )

    def test_governance_mode_overrides_compact(self) -> None:
        """When governance says active_dual_agent, compact's reviewer_mode is ignored."""
        gov = self._make_governance("active_dual_agent")
        compact = {"collaboration": {"reviewer_mode": "single_agent"}}
        self.assertEqual(
            derive_interaction_mode(compact, governance=gov),
            "active_dual_agent",
        )

    def test_governance_local_terminal_overrides_compact(self) -> None:
        """When governance says local_terminal, compact's dual-agent is ignored."""
        gov = self._make_governance("local_terminal")
        compact = {"collaboration": {"reviewer_mode": "active_dual_agent"}}
        self.assertEqual(
            derive_interaction_mode(compact, governance=gov),
            "local_terminal",
        )

    def test_empty_governance_falls_through_to_compact(self) -> None:
        """When governance has empty interaction_mode, compact is used as fallback."""
        gov = self._make_governance("")
        compact = {"collaboration": {"reviewer_mode": "active_dual_agent"}}
        self.assertEqual(
            derive_interaction_mode(compact, governance=gov),
            "dual_agent",
        )

    def test_no_governance_falls_through_to_compact(self) -> None:
        """Without governance, compact determines the mode."""
        compact = {"collaboration": {"reviewer_mode": "active_dual_agent"}}
        self.assertEqual(
            derive_interaction_mode(compact, governance=None),
            "dual_agent",
        )

    def test_no_governance_no_compact(self) -> None:
        self.assertEqual(derive_interaction_mode(None, governance=None), "unresolved")


_PATCH_HEAD = "dev.scripts.devctl.commands.governance.session_resume.current_head"
_PATCH_ROOT = "dev.scripts.devctl.commands.governance.session_resume.get_repo_root"
# Cache-hit tests exercise the head/role/mtime-only freshness gate; the
# typed continuity gate is covered by the Leg 3 test suite
# (dev/scripts/devctl/tests/governance/test_session_resume_support.py).
# Stub the CLI resolver to None so legacy cases behave like callers that
# cannot build a SessionContinuityState (for example an empty tempdir).
_PATCH_CONTINUITY = "dev.scripts.devctl.commands.governance.session_resume._resolve_continuity"


class TestRunCommand(unittest.TestCase):
    """End-to-end CLI dispatch tests for session-resume."""

    @patch(_PATCH_HEAD, return_value="abc123")
    @patch(_PATCH_ROOT)
    def test_run_cache_miss_builds_and_caches(self, mock_root, mock_head) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mock_root.return_value = root
            receipt_dir = root / "dev" / "reports" / "startup" / "latest"
            receipt_dir.mkdir(parents=True)
            (receipt_dir / "receipt.json").write_text(json.dumps({
                "current_branch": "main", "advisory_action": "no_push_needed",
                "advisory_reason": "clean_worktree", "checkpoint_required": False,
                "safe_to_continue_editing": True, "startup_authority_ok": True,
                "review_gate_allows_push": True, "push_action": "no_push_needed",
            }))
            args = SimpleNamespace(
                format="json", output=None, pipe_command=None, pipe_args=None, role="implementer",
            )
            self.assertEqual(run(args), 0)
            cache_path = root / "dev" / "reports" / "session_cache" / "latest" / "cache.json"
            self.assertTrue(cache_path.is_file())

    @patch(_PATCH_CONTINUITY, return_value=None)
    @patch(_PATCH_HEAD, return_value="abc123")
    @patch(_PATCH_ROOT)
    def test_run_cache_hit_skips_rebuild(self, mock_root, mock_head, mock_cont) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mock_root.return_value = root
            cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
            cache_dir.mkdir(parents=True)
            pkt = SessionCachePacket(
                head_sha="abc123", role="implementer", branch="cached",
                blockers="none", last_guard_ok=True,
            )
            (cache_dir / "cache.json").write_text(json.dumps(pkt.to_dict()))
            args = SimpleNamespace(
                format="summary", output=None, pipe_command=None, pipe_args=None, role="implementer",
            )
            self.assertEqual(run(args), 0)

    @patch(_PATCH_CONTINUITY, return_value=None)
    @patch(_PATCH_HEAD, return_value="abc123")
    @patch(_PATCH_ROOT)
    def test_run_json_cache_hit_returns_zero_even_with_blockers(
        self,
        mock_root,
        mock_head,
        mock_cont,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mock_root.return_value = root
            cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
            cache_dir.mkdir(parents=True)
            pkt = SessionCachePacket(
                head_sha="abc123",
                role="implementer",
                blockers="8 pending review packet(s)",
                authority_snapshot=AuthoritySnapshot(
                    coordination_state="single_agent_authoritative",
                    safe_to_continue=True,
                ),
            )
            (cache_dir / "cache.json").write_text(json.dumps(pkt.to_dict()))
            args = SimpleNamespace(
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
                role="implementer",
            )

            self.assertEqual(run(args), 0)

    @patch(_PATCH_HEAD, return_value="abc123")
    @patch(_PATCH_ROOT)
    def test_run_md_format_no_artifacts_fails_closed(self, mock_root, mock_head) -> None:
        """No artifacts: session-resume fails closed with non-zero exit."""
        with tempfile.TemporaryDirectory() as td:
            mock_root.return_value = Path(td)
            args = SimpleNamespace(
                format="md", output=None, pipe_command=None, pipe_args=None, role="implementer",
            )
            self.assertEqual(run(args), 1)

    @patch(_PATCH_CONTINUITY, return_value=None)
    @patch(_PATCH_HEAD, return_value="abc123")
    @patch(_PATCH_ROOT)
    def test_run_bootstrap_format_uses_human_renderer(self, mock_root, mock_head, mock_cont) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mock_root.return_value = root
            cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
            cache_dir.mkdir(parents=True)
            pkt = SessionCachePacket(
                head_sha="abc123",
                role="reviewer",
                blockers="none",
                last_guard_ok=True,
            )
            (cache_dir / "cache.json").write_text(json.dumps(pkt.to_dict()))
            args = SimpleNamespace(
                format="bootstrap",
                output=None,
                pipe_command=None,
                pipe_args=None,
                role="reviewer",
            )
            self.assertEqual(run(args), 0)

    @patch("dev.scripts.devctl.commands.governance.session_resume.build_from_sources")
    @patch("dev.scripts.devctl.commands.governance.session_resume.load_current_review_state")
    @patch(_PATCH_CONTINUITY, return_value=None)
    @patch(_PATCH_HEAD, return_value="abc123")
    @patch(_PATCH_ROOT)
    def test_run_threads_frozen_review_state_into_build(
        self,
        mock_root,
        mock_head,
        mock_cont,
        mock_load_current_review_state,
        mock_build_from_sources,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mock_root.return_value = root
            mock_load_current_review_state.return_value = object()
            mock_build_from_sources.return_value = SessionCachePacket(
                head_sha="abc123",
                role="implementer",
            )
            args = SimpleNamespace(
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
                role="implementer",
            )

            self.assertEqual(run(args), 0)
            mock_load_current_review_state.assert_called_once()
            self.assertEqual(
                mock_load_current_review_state.call_args.args[0],
                root,
            )
            self.assertFalse(
                mock_load_current_review_state.call_args.kwargs["prefer_cached_projection"],
            )
            mock_build_from_sources.assert_called_once()
            self.assertIs(
                mock_build_from_sources.call_args.kwargs["review_state"],
                mock_load_current_review_state.return_value,
            )


class TestBuildGovernedReviewRoot(unittest.TestCase):
    """build_from_sources respects governance review_root for artifact loading."""

    def _make_governance(self, review_root: str):
        from dev.scripts.devctl.runtime.project_governance_contract import (
            ArtifactRoots,
            BridgeConfig,
            BundleOverrides,
            EnabledChecks,
            MemoryRoots,
            PathRoots,
            PlanRegistry,
            ProjectGovernance,
            RepoIdentity,
            RepoPackRef,
        )

        return ProjectGovernance(
            schema_version=1,
            contract_id="ProjectGovernance",
            repo_identity=RepoIdentity(repo_name="test"),
            repo_pack=RepoPackRef(pack_id="test"),
            path_roots=PathRoots(),
            plan_registry=PlanRegistry(),
            artifact_roots=ArtifactRoots(review_root=review_root),
            memory_roots=MemoryRoots(),
            bridge_config=BridgeConfig(),
            enabled_checks=EnabledChecks(),
            bundle_overrides=BundleOverrides(overrides={}),
        )

    @patch("dev.scripts.devctl.commands.governance.session_resume_support.load_sources")
    @patch("dev.scripts.devctl.commands.governance.session_resume_support.resolve_source_paths")
    @patch("dev.scripts.devctl.commands.governance.session_resume_support.read_json_artifact")
    def test_governed_review_root_loads_from_governed_path(
        self, mock_read, mock_paths, mock_load,
    ) -> None:
        """When governance has a review_root, review_state loads from that root."""
        mock_load.return_value = {
            "receipt": {"advisory_action": "continue"},
            "review_state": None,
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": None,
        }
        mock_paths.return_value = {
            "receipt": Path("dev/reports/startup/latest/receipt.json"),
            "review_state": Path("custom_review/review_state.json"),
            "compact": Path("custom_review/compact.json"),
        }
        governed_review_data = {"current_session": {"current_instruction": "governed"}}
        mock_read.side_effect = lambda p: governed_review_data if "review_state" in str(p) else None
        gov = self._make_governance("custom_review")
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc123",
                governance=gov,
            )
            # Verify resolve_source_paths was called with governance
            mock_paths.assert_called_once()
            call_kwargs = mock_paths.call_args
            self.assertIs(call_kwargs.kwargs.get("governance"), gov)

    def test_governed_review_root_reads_correct_artifact(self) -> None:
        """End-to-end: governed review_root causes review_state to load from governed dir."""
        gov = self._make_governance("custom_review")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Create governed review_state with identifiable content
            gov_dir = root / "custom_review"
            gov_dir.mkdir(parents=True)
            gov_rs = gov_dir / "review_state.json"
            gov_rs.write_text(json.dumps({
                "current_session": {"current_instruction": "from governed path"},
            }))
            # Create a receipt so we don't hit bootstrap_required
            receipt_dir = root / "dev" / "reports" / "startup" / "latest"
            receipt_dir.mkdir(parents=True)
            (receipt_dir / "receipt.json").write_text(json.dumps({
                "advisory_action": "continue", "advisory_reason": "ok",
            }))
            packet = build_from_sources(
                root, role="implementer", head_sha="sha1", governance=gov,
            )
            self.assertEqual(packet.current_instruction, "from governed path")


class TestFrozenReviewStatePrecedence(unittest.TestCase):
    """Typed review_state should outrank stale compact data when both exist."""

    @patch("dev.scripts.devctl.commands.governance.session_resume_support.build_control_plane_read_model")
    @patch("dev.scripts.devctl.commands.governance.session_resume_support.read_json_artifact")
    @patch("dev.scripts.devctl.commands.governance.session_resume_support.resolve_source_paths")
    @patch("dev.scripts.devctl.commands.governance.session_resume_support.load_sources")
    @patch("dev.scripts.devctl.commands.governance.session_resume_support.load_git_state")
    def test_frozen_review_state_overrides_loaded_compact(
        self,
        mock_load_git_state,
        mock_load_sources,
        mock_resolve_source_paths,
        mock_read_json_artifact,
        mock_build_model,
    ) -> None:
        class FrozenReviewState:
            def to_dict(self) -> dict[str, object]:
                return {
                    "current_session": {
                        "current_instruction": "typed instruction",
                    },
                    "bridge": {
                        "head_at_push_time": "typed-sha",
                    },
                }

        frozen = FrozenReviewState()
        mock_load_git_state.return_value = {
            "branch": "main",
            "head": "abc123",
            "clean": True,
            "ahead": 0,
        }
        mock_load_sources.return_value = {
            "receipt": {"advisory_action": "continue", "advisory_reason": "ok"},
            "review_state": {
                "current_session": {
                    "current_instruction": "stale instruction",
                },
                "bridge": {"head_at_push_time": "stale-sha"},
            },
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": {
                "current_session": {
                    "current_instruction": "stale compact instruction",
                },
                "bridge": {"head_at_push_time": "stale-compact-sha"},
            },
        }
        mock_resolve_source_paths.return_value = {
            "compact": Path("custom/status/compact.json"),
        }
        mock_read_json_artifact.return_value = {
            "current_session": {
                "current_instruction": "stale compact instruction",
            },
            "bridge": {"head_at_push_time": "stale-compact-sha"},
        }
        mock_build_model.return_value = SimpleNamespace(
            top_blocker="none",
            next_action="n/a",
            next_command="",
            resolved_phase="idle",
            last_guard_ok=True,
            reviewer_observation=None,
            coordination=None,
            branch="main",
            reviewer_mode="single_agent",
            operator_interaction_mode="unresolved",
            reviewer_freshness="--",
            review_accepted=False,
            attention_status="n/a",
            attention_summary="n/a",
            publisher_running=False,
            supervisor_running=False,
            codex_conductor_alive=False,
            claude_conductor_alive=False,
            pending_action_requests=0,
            check_details=(),
        )

        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td),
                role="reviewer",
                head_sha="abc123",
                review_state=frozen,
            )

        self.assertEqual(packet.current_instruction, "typed instruction")
        self.assertEqual(packet.last_reviewed_sha, "typed-sha")


class TestNoArtifactFailClosed(unittest.TestCase):
    """Session-resume must fail closed when no receipt exists."""

    def _make_sources(self, *, receipt=None, compact=None, review_state=None):
        return {
            "receipt": receipt,
            "review_state": review_state,
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": compact,
        }

    def test_no_receipt_sets_bootstrap_required(self) -> None:
        """Without a receipt, blockers must be 'bootstrap_required', not 'none'."""
        sources = self._make_sources()
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="sha1",
                sources_override=sources,
            )
            self.assertEqual(packet.blockers, "bootstrap_required")

    def test_receipt_present_uses_model_blocker(self) -> None:
        """With a receipt, blockers come from the read model's top_blocker."""
        sources = self._make_sources(
            receipt={"advisory_action": "continue", "advisory_reason": "ok"},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="sha1",
                sources_override=sources,
            )
            self.assertEqual(packet.blockers, "none")

    def test_no_receipt_with_review_state_still_fails_closed(self) -> None:
        """Even with review_state but no receipt, blockers = bootstrap_required."""
        sources = self._make_sources(
            review_state={"current_session": {"current_instruction": "do stuff"}},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="reviewer", head_sha="sha2",
                sources_override=sources,
            )
            self.assertEqual(packet.blockers, "bootstrap_required")


class TestGovernedCacheHitPath(unittest.TestCase):
    """Prove run() resolves governance before computing mtime for cache."""

    @patch(_PATCH_HEAD, return_value="abc123")
    @patch(_PATCH_ROOT)
    def test_governed_review_root_busts_cache_on_same_head(self, mock_root, mock_head) -> None:
        """Cache built from default path must miss when governed review-root changes."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mock_root.return_value = root
            # Create default review_state at repo-pack path
            default_dir = root / "dev" / "reports" / "review_channel" / "latest"
            default_dir.mkdir(parents=True)
            default_rs = default_dir / "review_state.json"
            default_rs.write_text("{}")
            # Build a cache from default path
            cache_dir = root / "dev" / "reports" / "session_cache" / "latest"
            cache_dir.mkdir(parents=True)
            pkt = SessionCachePacket(
                head_sha="abc123", role="implementer", branch="main",
                review_state_mtime=default_rs.stat().st_mtime,
                current_instruction="stale instruction",
            )
            (cache_dir / "cache.json").write_text(json.dumps(pkt.to_dict()))
            # Now create a DIFFERENT review_state at governed path
            governed_dir = root / "governed" / "review"
            governed_dir.mkdir(parents=True)
            governed_rs = governed_dir / "review_state.json"
            governed_rs.write_text('{"updated": true}')
            # Patch governance to point to governed path
            with patch(
                "dev.scripts.devctl.commands.governance.session_resume.resolve_governance"
            ) as mock_gov:
                mock_gov_obj = MagicMock()
                mock_gov_obj.artifact_roots.review_root = str(governed_dir)
                mock_gov.return_value = mock_gov_obj
                # run() should see different mtime → cache miss → rebuild
                # Even though HEAD is same, governed review_state has different mtime
                from dev.scripts.devctl.commands.governance.session_resume_paths import get_review_state_mtime
                governed_mtime = get_review_state_mtime(root, governance=mock_gov_obj)
                self.assertNotEqual(governed_mtime, pkt.review_state_mtime)


class TestRegistration(unittest.TestCase):
    """Verify the command is properly registered in the CLI."""

    def test_in_command_handlers(self) -> None:
        from dev.scripts.devctl.cli import COMMAND_HANDLERS
        self.assertIn("session-resume", COMMAND_HANDLERS)

    def test_in_listing(self) -> None:
        from dev.scripts.devctl.commands.listing import COMMANDS
        self.assertIn("session-resume", COMMANDS)

    def test_in_read_only_commands(self) -> None:
        from dev.scripts.devctl.cli import READ_ONLY_COMMANDS
        self.assertIn("session-resume", READ_ONLY_COMMANDS)


class TestLastReviewedSha(unittest.TestCase):
    """AUD-22: session-resume surfaces last_reviewed_sha so Codex knows when HEAD moved."""

    def _make_sources(self, *, receipt=None, compact=None, review_state=None):
        return {
            "receipt": receipt,
            "review_state": review_state,
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": compact,
        }

    def test_last_reviewed_sha_from_compact_bridge(self) -> None:
        """last_reviewed_sha is extracted from compact bridge head_at_push_time."""
        sources = self._make_sources(
            receipt={"advisory_action": "continue", "advisory_reason": "ok"},
            compact={
                "bridge": {"head_at_push_time": "abc123def456"},
                "current_session": {},
            },
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="new_head_sha",
                sources_override=sources,
            )
            self.assertEqual(packet.last_reviewed_sha, "abc123def456")
            self.assertEqual(packet.head_sha, "new_head_sha")

    def test_head_moved_after_push(self) -> None:
        """When HEAD differs from last_reviewed_sha, session-resume exposes the drift."""
        old_push_sha = "aaa111bbb222ccc333"
        new_head_sha = "ddd444eee555fff666"
        sources = self._make_sources(
            receipt={"advisory_action": "continue", "advisory_reason": "ok"},
            compact={
                "bridge": {"head_at_push_time": old_push_sha},
                "current_session": {},
            },
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha=new_head_sha,
                sources_override=sources,
            )
            self.assertNotEqual(packet.head_sha, packet.last_reviewed_sha)
            self.assertEqual(packet.head_sha, new_head_sha)
            self.assertEqual(packet.last_reviewed_sha, old_push_sha)

    def test_no_push_sha_returns_empty(self) -> None:
        """When no push has happened, last_reviewed_sha is empty."""
        sources = self._make_sources(
            receipt={"advisory_action": "continue", "advisory_reason": "ok"},
            compact={"bridge": {}, "current_session": {}},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="some_sha",
                sources_override=sources,
            )
            self.assertEqual(packet.last_reviewed_sha, "")

    def test_roundtrip_preserves_last_reviewed_sha(self) -> None:
        """packet_from_mapping preserves last_reviewed_sha across serialization."""
        original = SessionCachePacket(
            head_sha="new_head", last_reviewed_sha="old_reviewed",
        )
        restored = packet_from_mapping(original.to_dict())
        self.assertEqual(restored.last_reviewed_sha, "old_reviewed")

    def test_render_markdown_includes_last_reviewed(self) -> None:
        """Markdown output includes last_reviewed line when SHA is present."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_markdown,
        )
        packet = SessionCachePacket(
            head_sha="aabbccdd", last_reviewed_sha="11223344",
        )
        md = render_markdown(packet)
        self.assertIn("last_reviewed", md)
        self.assertIn("112233", md)

    def test_render_summary_includes_last_reviewed(self) -> None:
        """Summary output includes last_reviewed when SHA is present."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_summary,
        )
        packet = SessionCachePacket(
            head_sha="aabbccdd", last_reviewed_sha="11223344",
        )
        summary = render_summary(packet)
        self.assertIn("last_reviewed=112233", summary)

    def test_render_bootstrap_reviewer_includes_role_packet_and_diff_range(self) -> None:
        """Bootstrap format gives reviewer-specific commands and diff guidance."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_bootstrap,
        )

        packet = SessionCachePacket(
            role="reviewer",
            head_sha="aabbccddeeff0011",
            last_reviewed_sha="1122334455667788",
            operator_interaction_mode="active_dual_agent",
            resolved_phase="reviewing",
            next_guard_bundle="bundle.tooling",
        )

        md = render_bootstrap(packet)
        self.assertIn("Reviewer Bootstrap Packet", md)
        self.assertIn(
            "python3 dev/scripts/devctl.py session-resume --role reviewer --format bootstrap",
            md,
        )
        self.assertIn("1122334455667788..aabbccddeeff0011", md)
        self.assertIn(
            "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
            md,
        )
        self.assertIn("Stay reviewer-only", md)

    def test_render_bootstrap_implementer_mentions_ack_and_instruction(self) -> None:
        """Bootstrap format gives implementer-specific starter guidance."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_bootstrap,
        )

        packet = SessionCachePacket(
            role="implementer",
            instruction_revision="rev-123",
            current_instruction="Implement the bounded slice.",
            operator_interaction_mode="active_dual_agent",
        )

        md = render_bootstrap(packet)
        self.assertIn("Implementer Bootstrap Packet", md)
        self.assertIn(
            "python3 dev/scripts/devctl.py session-resume --role implementer --format bootstrap",
            md,
        )
        self.assertIn("Acknowledge the live `instruction_revision` before coding.", md)
        self.assertIn("Current instruction revision to acknowledge: `rev-123`.", md)
        self.assertIn("Implement the bounded slice.", md)

    def test_render_bootstrap_reviewer_prefers_review_candidate(self) -> None:
        """Reviewer bootstrap should prefer a typed review candidate over raw diff range."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_bootstrap,
        )
        from dev.scripts.devctl.runtime.review_state_models import (
            ReviewCandidateRecord,
        )

        packet = SessionCachePacket(
            role="reviewer",
            head_sha="bbbbbbbbbbbbbbbb",
            last_reviewed_sha="aaaaaaaaaaaaaaaa",
            operator_interaction_mode="active_dual_agent",
            review_candidate=ReviewCandidateRecord(
                candidate_id="review-candidate-123",
                instruction_revision="rev-123",
                artifact_kind="dirty_tree",
                base_sha="aaaaaaaaaaaaaaaa",
                head_sha="bbbbbbbbbbbbbbbb",
                worktree_hash="c" * 64,
                changed_paths=("tracked.txt",),
                implementer_status_written=True,
                ready_for_review=True,
                valid=True,
                implementer_state_hash="state-123",
            ),
        )

        md = render_bootstrap(packet)
        self.assertIn("review_target", md)
        self.assertIn("review-candidate-123", md)
        self.assertIn("Prefer frozen review candidate", md)
        self.assertNotIn("Review the exact diff range", md)


    def test_render_bootstrap_reviewer_status_poll_before_context_graph(self) -> None:
        """Reviewer Run In Order must put review-channel status before context-graph."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_bootstrap,
        )

        packet = SessionCachePacket(
            role="reviewer",
            head_sha="aabbccddeeff0011",
            operator_interaction_mode="active_dual_agent",
        )

        md = render_bootstrap(packet)
        status_idx = md.index("review-channel --action status")
        context_idx = md.index("context-graph --mode bootstrap")
        self.assertLess(
            status_idx,
            context_idx,
            "Reviewer must poll review-channel status before context-graph",
        )

    def test_render_bootstrap_reviewer_conversation_starter_includes_status_poll(self) -> None:
        """Reviewer Conversation Starter must mention review-channel status before context-graph."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_bootstrap,
        )

        packet = SessionCachePacket(
            role="reviewer",
            head_sha="aabbccddeeff0011",
            operator_interaction_mode="active_dual_agent",
        )

        md = render_bootstrap(packet)
        starter_section = md[md.index("### Conversation Starter"):]
        next_section_idx = starter_section.find("\n### ", 1)
        if next_section_idx > 0:
            starter_section = starter_section[:next_section_idx]
        self.assertIn("review-channel --action status", starter_section)
        status_idx = starter_section.index("review-channel --action status")
        context_idx = starter_section.index("context-graph --mode bootstrap")
        self.assertLess(
            status_idx,
            context_idx,
            "Reviewer Conversation Starter must put review-channel status before context-graph",
        )

    def test_render_bootstrap_reviewer_requires_pending_inbox_before_questions(
        self,
    ) -> None:
        """Reviewer bootstrap must consume pending inbox guidance before bridge-only analysis."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_bootstrap,
        )

        packet = SessionCachePacket(
            role="reviewer",
            head_sha="aabbccddeeff0011",
            operator_interaction_mode="active_dual_agent",
        )

        md = render_bootstrap(packet)
        self.assertIn(
            "If `Pending Inbox` already names a reviewer-targeted packet or `required_command`, run that repo-owned inbox command immediately before bridge-only analysis or operator questions.",
            md,
        )

    def test_render_bootstrap_implementer_no_status_poll_step(self) -> None:
        """Implementer Run In Order must not include review-channel status as a step."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_bootstrap,
        )

        packet = SessionCachePacket(
            role="implementer",
            instruction_revision="rev-456",
            operator_interaction_mode="active_dual_agent",
        )

        md = render_bootstrap(packet)
        run_in_order_section = md[md.index("### Run In Order"):]
        next_section_idx = run_in_order_section.find("\n### ", 1)
        if next_section_idx > 0:
            run_in_order_section = run_in_order_section[:next_section_idx]
        self.assertNotIn("review-channel --action status", run_in_order_section)

    def test_render_bootstrap_implementer_requires_packet_inbox_before_operator_question(
        self,
    ) -> None:
        """Implementer bootstrap must force the typed inbox step before asking."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_bootstrap,
        )

        packet = SessionCachePacket(
            role="implementer",
            instruction_revision="rev-456",
            operator_interaction_mode="active_dual_agent",
        )

        md = render_bootstrap(packet)
        self.assertIn(
            "run `python3 dev/scripts/devctl.py review-channel --action inbox --target claude --status pending --format md` immediately before asking what to do next.",
            md,
        )
        self.assertIn(
            "Do not ask the operator whether to continue a permitted probe or pull a pending packet when the typed inbox already provides the next non-destructive step.",
            md,
        )


class TestV2Fields(unittest.TestCase):
    """v2 fields: resolved_phase, next_guard_bundle, operator_interaction_mode,
    head_at_push_time, next_recommended_command."""

    def _make_sources(self, *, receipt=None, compact=None, review_state=None):
        return {
            "receipt": receipt,
            "review_state": review_state,
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": compact,
        }

    def test_resolved_phase_from_read_model(self) -> None:
        """resolved_phase is sourced from the ControlPlaneReadModel."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="t", branch="b", head_sha="h",
            worktree_clean=True, ahead_of_upstream=0,
            resolved_phase="implementing",
            push_eligible=False, implementation_blocked=False,
            top_blocker="none", next_action="n/a", next_command="",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="--", review_accepted=False,
            last_reviewed_sha="", attention_status="n/a",
            attention_summary="n/a",
            publisher_running=False, supervisor_running=False,
            codex_conductor_alive=False, claude_conductor_alive=False,
            pending_action_requests=0, last_guard_ok=True,
            check_details=(),
        )
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                read_model_override=model, sources_override=sources,
            )
            self.assertEqual(packet.resolved_phase, "implementing")

    def test_operator_interaction_mode_from_read_model(self) -> None:
        """operator_interaction_mode mirrors the read model field."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="t", branch="b", head_sha="h",
            worktree_clean=True, ahead_of_upstream=0,
            resolved_phase="idle",
            push_eligible=False, implementation_blocked=False,
            top_blocker="none", next_action="n/a", next_command="",
            reviewer_mode="active_dual_agent",
            operator_interaction_mode="active_dual_agent",
            reviewer_freshness="--", review_accepted=False,
            last_reviewed_sha="", attention_status="n/a",
            attention_summary="n/a",
            publisher_running=False, supervisor_running=False,
            codex_conductor_alive=False, claude_conductor_alive=False,
            pending_action_requests=0, last_guard_ok=True,
            check_details=(),
        )
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                read_model_override=model, sources_override=sources,
            )
            self.assertEqual(packet.operator_interaction_mode, "active_dual_agent")

    def test_head_at_push_time_from_bridge(self) -> None:
        """head_at_push_time is extracted from bridge metadata."""
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
            compact={
                "bridge": {"head_at_push_time": "pushed_sha_123"},
                "current_session": {},
            },
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="current_sha",
                sources_override=sources,
            )
            self.assertEqual(packet.head_at_push_time, "pushed_sha_123")
            # last_reviewed_sha should match head_at_push_time
            self.assertEqual(packet.last_reviewed_sha, "pushed_sha_123")

    def test_next_guard_bundle_from_changed_paths(self) -> None:
        """next_guard_bundle classifies changed paths to a bundle name."""
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                sources_override=sources,
                changed_paths=["dev/scripts/devctl/commands/governance/session_resume_support.py"],
            )
            self.assertEqual(packet.next_guard_bundle, "bundle.tooling")

    def test_next_guard_bundle_runtime(self) -> None:
        """Runtime paths produce bundle.runtime."""
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                sources_override=sources,
                changed_paths=["rust/src/bin/voiceterm/main.rs"],
            )
            self.assertEqual(packet.next_guard_bundle, "bundle.runtime")

    def test_next_guard_bundle_empty_when_no_paths(self) -> None:
        """Empty changed paths produce empty guard bundle."""
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                sources_override=sources,
                changed_paths=[],
            )
            self.assertEqual(packet.next_guard_bundle, "")

    def test_next_recommended_command_from_read_model(self) -> None:
        """next_recommended_command comes from the read model next_command."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="t", branch="b", head_sha="h",
            worktree_clean=True, ahead_of_upstream=0,
            resolved_phase="pushing",
            push_eligible=True, implementation_blocked=False,
            top_blocker="none",
            next_action="run_devctl_push",
            next_command="python3 dev/scripts/devctl.py push --execute",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="--", review_accepted=True,
            last_reviewed_sha="", attention_status="n/a",
            attention_summary="n/a",
            publisher_running=False, supervisor_running=False,
            codex_conductor_alive=False, claude_conductor_alive=False,
            pending_action_requests=0, last_guard_ok=True,
            check_details=(),
        )
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                read_model_override=model, sources_override=sources,
            )
            self.assertEqual(
                packet.next_recommended_command,
                "python3 dev/scripts/devctl.py push --execute",
            )

    def test_attention_command_overrides_stale_read_model_next_command(self) -> None:
        """Typed attention/recovery guidance wins when the live surface already degraded."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="t", branch="b", head_sha="h",
            worktree_clean=False, ahead_of_upstream=0,
            resolved_phase="pushing",
            push_eligible=False, implementation_blocked=False,
            top_blocker="none",
            next_action="run_devctl_push",
            next_command="python3 dev/scripts/devctl.py push --execute",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="overdue", review_accepted=False,
            last_reviewed_sha="", attention_status="checkpoint_required",
            attention_summary="checkpoint required",
            publisher_running=False, supervisor_running=False,
            codex_conductor_alive=False, claude_conductor_alive=False,
            pending_action_requests=0, last_guard_ok=True,
            check_details=(),
        )
        sources = self._make_sources(
            review_state={
                "attention": {
                    "status": "checkpoint_required",
                    "summary": "The current worktree has exceeded the checkpoint budget.",
                    "recommended_action": "Cut a checkpoint before continuing.",
                    "recommended_command": (
                        "python3 dev/scripts/devctl.py commit -m "
                        "\"<descriptive message>\""
                    ),
                },
                "current_session": {
                    "current_instruction": "Do the thing",
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "stale",
                },
            },
        )

        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                read_model_override=model, sources_override=sources,
            )

        self.assertEqual(
            packet.next_recommended_command,
            "python3 dev/scripts/devctl.py commit -m \"<descriptive message>\"",
        )
        self.assertEqual(
            packet.next_action,
            "python3 dev/scripts/devctl.py commit -m \"<descriptive message>\"",
        )
        assert packet.authority_snapshot is not None
        self.assertEqual(
            packet.authority_snapshot.next_command,
            "python3 dev/scripts/devctl.py commit -m \"<descriptive message>\"",
        )

    def test_authority_snapshot_prefers_coordination_resync_over_push_guidance(self) -> None:
        """AuthoritySnapshot stays blocker-aware even when the read model says push."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="t", branch="b", head_sha="h",
            worktree_clean=True, ahead_of_upstream=23,
            resolved_phase="pushing",
            push_eligible=True, implementation_blocked=False,
            top_blocker="1 pending review packet(s)",
            next_action="run_devctl_push",
            next_command="python3 dev/scripts/devctl.py push --execute",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="overdue", review_accepted=True,
            last_reviewed_sha="", attention_status="healthy",
            attention_summary="Review loop signals are fresh.",
            publisher_running=False, supervisor_running=False,
            codex_conductor_alive=True, claude_conductor_alive=False,
            pending_action_requests=1, last_guard_ok=True,
            check_details=(),
        )
        sources = self._make_sources(
            review_state={
                "attention": {
                    "status": "healthy",
                    "summary": "Review loop signals are fresh.",
                },
                "recovery_assessment": {
                    "diagnosis": {
                        "status": "healthy",
                        "root_cause": "Review loop signals are fresh.",
                    },
                    "decision": {
                        "action_id": "continue_scoped_loop",
                        "command": "",
                        "execution_owner": "system",
                    },
                },
                "current_session": {
                    "current_instruction": "Do the thing",
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "missing",
                },
                "bridge": {
                    "reviewer_mode": "single_agent",
                    "effective_reviewer_mode": "single_agent",
                    "reviewer_freshness": "overdue",
                },
                "reviewer_runtime": {
                    "reviewer_mode": "single_agent",
                    "effective_reviewer_mode": "single_agent",
                    "reviewer_freshness": "overdue",
                    "publish_clear": True,
                    "review_acceptance": {
                        "review_accepted": True,
                        "open_findings": "1 pending review packet(s)",
                    },
                },
                "coordination": {
                    "observed_topology": "dual_agent",
                    "resync_required": True,
                    "current_slice": "Priority action_request",
                    "active_target": {
                        "plan_path": "dev/active/ai_governance_platform.md",
                    },
                },
            },
        )

        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="reviewer", head_sha="abc",
                read_model_override=model, sources_override=sources,
            )

        assert packet.authority_snapshot is not None
        self.assertEqual(
            packet.authority_snapshot.next_command,
            "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
        )
        self.assertTrue(packet.authority_snapshot.observed_control_topology)
        self.assertTrue(packet.authority_snapshot.implementation_permission)

    def test_advisory_action_from_read_model_not_receipt(self) -> None:
        """advisory_action is derived from read model next_action, not receipt."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="t", branch="b", head_sha="h",
            worktree_clean=True, ahead_of_upstream=0,
            resolved_phase="idle",
            push_eligible=False, implementation_blocked=False,
            top_blocker="none",
            next_action="model_derived_action",
            next_command="model_derived_command",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="--", review_accepted=False,
            last_reviewed_sha="", attention_status="n/a",
            attention_summary="n/a",
            publisher_running=False, supervisor_running=False,
            codex_conductor_alive=False, claude_conductor_alive=False,
            pending_action_requests=0, last_guard_ok=True,
            check_details=(),
        )
        sources = self._make_sources(
            receipt={
                "advisory_action": "receipt_action_should_be_ignored",
                "advisory_reason": "receipt_reason_should_be_ignored",
            },
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                read_model_override=model, sources_override=sources,
            )
            # Advisory comes from read model, not receipt
            self.assertEqual(packet.advisory_action, "model_derived_action")
            self.assertEqual(packet.advisory_reason, "none")

    def test_build_from_sources_preserves_review_candidate(self) -> None:
        """build_from_sources should lift the typed review candidate into the session cache."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="t", branch="b", head_sha="abc",
            worktree_clean=False, ahead_of_upstream=0,
            resolved_phase="reviewing",
            push_eligible=False, implementation_blocked=False,
            top_blocker="none",
            next_action="review_candidate_present",
            next_command="python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
            reviewer_mode="active_dual_agent",
            operator_interaction_mode="active_dual_agent",
            reviewer_freshness="fresh", review_accepted=False,
            last_reviewed_sha="oldsha", attention_status="healthy",
            attention_summary="healthy",
            publisher_running=False, supervisor_running=False,
            codex_conductor_alive=True, claude_conductor_alive=True,
            pending_action_requests=0, last_guard_ok=True,
            check_details=(),
        )
        sources = self._make_sources(
            review_state={
                "current_session": {
                    "current_instruction": "- review `tracked.txt`",
                    "current_instruction_revision": "rev-123",
                    "implementer_status": "- implemented the slice",
                    "implementer_ack": "- ready for review",
                    "implementer_ack_state": "current",
                },
                "review_candidate": {
                    "candidate_id": "review-candidate-123",
                    "instruction_revision": "rev-123",
                    "artifact_kind": "dirty_tree",
                    "base_sha": "oldsha",
                    "head_sha": "abc",
                    "worktree_hash": "e" * 64,
                    "changed_paths": ["tracked.txt"],
                    "implementer_status_written": True,
                    "ready_for_review": True,
                    "valid": True,
                    "implementer_state_hash": "state-123",
                },
                "bridge": {"head_at_push_time": "oldsha"},
            },
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="reviewer", head_sha="abc",
                read_model_override=model, sources_override=sources,
            )
            assert packet.review_candidate is not None
            self.assertEqual(
                packet.review_candidate.candidate_id,
                "review-candidate-123",
            )

    def test_roundtrip_preserves_v2_fields(self) -> None:
        """packet_from_mapping preserves all v2 fields across serialization."""
        from dev.scripts.devctl.platform.coordination_snapshot_models import (
            CoordinationSnapshot,
        )
        from dev.scripts.devctl.runtime.review_state_models import (
            ReviewCandidateRecord,
        )

        original = SessionCachePacket(
            head_sha="abc",
            head_at_push_time="old_push_sha",
            operator_interaction_mode="active_dual_agent",
            resolved_phase="testing",
            next_guard_bundle="bundle.tooling",
            next_recommended_command="python3 dev/scripts/devctl.py check --profile ci",
            review_candidate=ReviewCandidateRecord(
                candidate_id="review-candidate-123",
                instruction_revision="rev-123",
                artifact_kind="dirty_tree",
                base_sha="old_push_sha",
                head_sha="abc",
                worktree_hash="d" * 64,
                changed_paths=("tracked.txt",),
                implementer_status_written=True,
                ready_for_review=True,
                valid=True,
                implementer_state_hash="state-123",
            ),
            coordination=CoordinationSnapshot(
                current_slice="Wire remote-control bootstrap through CoordinationSnapshot.",
                declared_topology="multi_agent_orchestrated",
                observed_topology="single_agent",
                recommended_topology="single_agent",
                fanout_posture="planned_scaffolding_only",
                safe_to_fanout=False,
                worktree_strategy="isolated_worker_worktrees",
                resync_required=True,
                resync_reasons=("declared_topology:multi_agent_orchestrated",),
            ),
        )
        restored = packet_from_mapping(original.to_dict())
        self.assertEqual(restored.head_at_push_time, "old_push_sha")
        self.assertEqual(restored.operator_interaction_mode, "active_dual_agent")
        self.assertEqual(restored.resolved_phase, "testing")
        self.assertEqual(restored.next_guard_bundle, "bundle.tooling")
        self.assertEqual(
            restored.next_recommended_command,
            "python3 dev/scripts/devctl.py check --profile ci",
        )
        assert restored.review_candidate is not None
        self.assertEqual(
            restored.review_candidate.candidate_id,
            "review-candidate-123",
        )
        assert restored.coordination is not None
        self.assertEqual(
            restored.coordination.current_slice,
            "Wire remote-control bootstrap through CoordinationSnapshot.",
        )
        self.assertTrue(restored.coordination.resync_required)

    def test_render_markdown_includes_v2_fields(self) -> None:
        """Markdown output includes phase, mode, and bundle."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_markdown,
        )
        packet = SessionCachePacket(
            head_sha="aabbccdd",
            head_at_push_time="11223344",
            operator_interaction_mode="active_dual_agent",
            resolved_phase="testing",
            next_guard_bundle="bundle.runtime",
            next_recommended_command="run checks",
        )
        md = render_markdown(packet)
        self.assertIn("phase", md)
        self.assertIn("testing", md)
        self.assertIn("head_at_push", md)
        self.assertIn("112233", md)
        self.assertIn("guard_bundle", md)
        self.assertIn("bundle.runtime", md)
        self.assertIn("active_dual_agent", md)

    def test_render_summary_includes_v2_fields(self) -> None:
        """Summary output includes phase, mode, and bundle."""
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            render_summary,
        )
        packet = SessionCachePacket(
            head_sha="aabbccdd",
            head_at_push_time="11223344",
            operator_interaction_mode="active_dual_agent",
            resolved_phase="implementing",
            next_guard_bundle="bundle.tooling",
            next_recommended_command="run checks",
        )
        summary = render_summary(packet)
        self.assertIn("phase=implementing", summary)
        self.assertIn("head_at_push=112233", summary)
        self.assertIn("guard_bundle=bundle.tooling", summary)
        self.assertIn("mode=active_dual_agent", summary)

    def test_to_dict_includes_v3_fields(self) -> None:
        """to_dict() includes the extended session packet fields in the output."""
        pkt = SessionCachePacket(
            head_at_push_time="push_sha",
            operator_interaction_mode="active_dual_agent",
            resolved_phase="committing",
            next_guard_bundle="bundle.runtime",
            next_recommended_command="push --execute",
        )
        d = pkt.to_dict()
        self.assertEqual(d["head_at_push_time"], "push_sha")
        self.assertEqual(d["operator_interaction_mode"], "active_dual_agent")
        self.assertEqual(d["resolved_phase"], "committing")
        self.assertEqual(d["next_guard_bundle"], "bundle.runtime")
        self.assertEqual(d["next_recommended_command"], "push --execute")
        self.assertEqual(d["schema_version"], 3)


class TestGuardBundleFromReviewScope(unittest.TestCase):
    """When head_sha != last_reviewed_sha and worktree is clean, guard bundle
    derives from the commit-range diff instead of empty local diffs."""

    def _make_sources(self, *, receipt=None, compact=None, review_state=None):
        return {
            "receipt": receipt,
            "review_state": review_state,
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": compact,
        }

    @patch(
        "dev.scripts.devctl.commands.governance.session_resume_support"
        "._git_commit_range_paths",
        return_value=["rust/src/bin/voiceterm/main.rs"],
    )
    @patch(
        "dev.scripts.devctl.commands.governance.session_resume_support"
        "._git_changed_paths",
        return_value=[],
    )
    def test_clean_worktree_uses_commit_range(
        self, mock_local, mock_range,
    ) -> None:
        """Guard bundle resolves from commit range when worktree is clean."""
        old_sha = "aaa111bbb222"
        new_sha = "ccc333ddd444"
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
            compact={
                "bridge": {"head_at_push_time": old_sha},
                "current_session": {},
            },
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="reviewer", head_sha=new_sha,
                sources_override=sources,
            )
            # local diffs checked first (empty), then commit-range fallback
            self.assertEqual(packet.next_guard_bundle, "bundle.runtime")
            mock_local.assert_called_once()
            mock_range.assert_called_once_with(Path(td), old_sha, new_sha)

    @patch(
        "dev.scripts.devctl.commands.governance.session_resume_support"
        "._git_commit_range_paths",
        return_value=["README.md"],
    )
    @patch(
        "dev.scripts.devctl.commands.governance.session_resume_support"
        "._git_changed_paths",
        return_value=["rust/src/bin/voiceterm/main.rs"],
    )
    def test_dirty_worktree_takes_priority_over_commit_range(
        self, mock_local, mock_range,
    ) -> None:
        """Dirty local runtime changes must not be hidden by docs-only commit range."""
        old_sha = "aaa111bbb222"
        new_sha = "ccc333ddd444"
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
            compact={
                "bridge": {"head_at_push_time": old_sha},
                "current_session": {},
            },
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="reviewer", head_sha=new_sha,
                sources_override=sources,
            )
            # Local runtime diff takes priority — NOT docs from commit range
            self.assertEqual(packet.next_guard_bundle, "bundle.runtime")
            mock_local.assert_called_once()
            mock_range.assert_not_called()


class TestReadModelPureProjection(unittest.TestCase):
    """build_from_sources projects checkpoint truth from shared push enforcement."""

    def _make_sources(self, *, receipt=None, compact=None, review_state=None):
        return {
            "receipt": receipt,
            "review_state": review_state,
            "push_report": None,
            "publisher_hb": None,
            "supervisor_hb": None,
            "codex_conductor": None,
            "claude_conductor": None,
            "full_json": None,
            "compact_json": compact,
        }

    def _make_governance(self, **push_overrides):
        from dev.scripts.devctl.runtime.project_governance_contract import (
            ArtifactRoots,
            BridgeConfig,
            BundleOverrides,
            EnabledChecks,
            MemoryRoots,
            PathRoots,
            PlanRegistry,
            ProjectGovernance,
            RepoIdentity,
            RepoPackRef,
        )
        from dev.scripts.devctl.runtime.project_governance_push import PushEnforcement

        return ProjectGovernance(
            schema_version=1,
            contract_id="ProjectGovernance",
            repo_identity=RepoIdentity(repo_name="test"),
            repo_pack=RepoPackRef(pack_id="test"),
            path_roots=PathRoots(),
            plan_registry=PlanRegistry(),
            artifact_roots=ArtifactRoots(),
            memory_roots=MemoryRoots(),
            bridge_config=BridgeConfig(),
            enabled_checks=EnabledChecks(),
            bundle_overrides=BundleOverrides(overrides={}),
            push_enforcement=PushEnforcement(**push_overrides),
        )

    def test_safe_to_continue_uses_push_enforcement_truth(self) -> None:
        """safe_to_continue follows push_enforcement, not the read-model blocker."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="t", branch="b", head_sha="h",
            worktree_clean=True, ahead_of_upstream=0,
            resolved_phase="idle",
            push_eligible=False, implementation_blocked=False,
            top_blocker="none",
            next_action="fix guards", next_command="",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="--", review_accepted=False,
            last_reviewed_sha="", attention_status="n/a",
            attention_summary="n/a",
            publisher_running=False, supervisor_running=False,
            codex_conductor_alive=False, claude_conductor_alive=False,
            pending_action_requests=0, last_guard_ok=False,
            check_details=(),
        )
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
        )
        governance = self._make_governance(
            checkpoint_required=False,
            safe_to_continue_editing=False,
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                governance=governance,
                read_model_override=model,
                sources_override=sources,
            )
            self.assertIn("safe_to_continue=False", packet.key_rules)
            self.assertEqual(packet.blockers, "continuation_blocked")

    def test_checkpoint_required_uses_push_enforcement_truth(self) -> None:
        """checkpoint_required follows push_enforcement, not the read-model phase."""
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="t", branch="b", head_sha="h",
            worktree_clean=False, ahead_of_upstream=0,
            resolved_phase="idle",
            push_eligible=False, implementation_blocked=False,
            top_blocker="none", next_action="commit", next_command="",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="--", review_accepted=False,
            last_reviewed_sha="", attention_status="n/a",
            attention_summary="n/a",
            publisher_running=False, supervisor_running=False,
            codex_conductor_alive=False, claude_conductor_alive=False,
            pending_action_requests=0, last_guard_ok=True,
            check_details=(),
        )
        sources = self._make_sources(
            receipt={"advisory_action": "continue"},
        )
        governance = self._make_governance(
            checkpoint_required=True,
            safe_to_continue_editing=True,
            checkpoint_reason="staged_index_budget_exceeded",
        )
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(
                Path(td), role="implementer", head_sha="abc",
                governance=governance,
                read_model_override=model,
                sources_override=sources,
            )
            self.assertIn("checkpoint_required=True", packet.key_rules)
            self.assertEqual(packet.blockers, "checkpoint_required")
            assert packet.authority_snapshot is not None
            self.assertFalse(packet.authority_snapshot.safe_to_continue)
            self.assertIn("implementation.edit", packet.authority_snapshot.blocked_actions)


class TestFrozenReviewStateZrefSafety(unittest.TestCase):
    """Verify getattr-safe access to snapshot_id/zref on frozen review-state stubs."""

    def test_legacy_stub_without_snapshot_id_or_zref_produces_empty_defaults(self) -> None:
        class LegacyFrozenReviewState:
            def to_dict(self) -> dict[str, object]:
                return {"current_session": {}, "bridge": {}}

        payload = {"review_state": LegacyFrozenReviewState().to_dict()}
        packet = packet_from_mapping(
            {
                "generated_at_utc": "2026-01-01T00:00:00Z",
                "role": "implementer",
                "branch": "main",
                "head_sha": "abc123",
                "snapshot_id": "",
                "zref": "",
                "advisory_action": "continue",
                "advisory_reason": "ok",
                "blockers": "",
                "interaction_mode": "local_terminal",
                "current_instruction": "",
                "instruction_revision": "",
                "ack_state": "",
                "open_findings": "none",
                "last_guard_ok": True,
                "review_state_mtime": 0.0,
                "last_reviewed_sha": "",
                "done_summary": "",
                "next_action": "",
                "key_rules": [],
                "head_at_push_time": "",
            }
        )
        self.assertEqual(packet.snapshot_id, "")
        self.assertEqual(packet.zref, "")

    def test_stub_with_zref_roundtrips_correctly(self) -> None:
        packet = packet_from_mapping(
            {
                "generated_at_utc": "2026-01-01T00:00:00Z",
                "role": "implementer",
                "branch": "main",
                "head_sha": "abc123",
                "snapshot_id": "snap-abc12345",
                "zref": "zref_abc12345_def67890",
                "advisory_action": "continue",
                "advisory_reason": "ok",
                "blockers": "",
                "interaction_mode": "local_terminal",
                "current_instruction": "",
                "instruction_revision": "",
                "ack_state": "",
                "open_findings": "none",
                "last_guard_ok": True,
                "review_state_mtime": 0.0,
                "last_reviewed_sha": "",
                "done_summary": "",
                "next_action": "",
                "key_rules": [],
                "head_at_push_time": "",
            }
        )
        self.assertEqual(packet.snapshot_id, "snap-abc12345")
        self.assertEqual(packet.zref, "zref_abc12345_def67890")

    def test_getattr_on_none_review_state_returns_empty(self) -> None:
        self.assertEqual(getattr(None, "snapshot_id", ""), "")
        self.assertEqual(getattr(None, "zref", ""), "")


if __name__ == "__main__":
    unittest.main()
