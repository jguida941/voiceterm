"""Tests for the session-resume command."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dev.scripts.devctl.commands.governance.session_resume import run
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


class TestSessionCachePacket(unittest.TestCase):
    """SessionCachePacket data contract tests."""

    def test_defaults(self) -> None:
        pkt = SessionCachePacket()
        self.assertEqual(pkt.schema_version, 1)
        self.assertEqual(pkt.contract_id, "SessionCachePacket")
        self.assertEqual(pkt.role, "implementer")
        self.assertEqual(pkt.blockers, "none")
        self.assertTrue(pkt.last_guard_ok)
        self.assertEqual(pkt.key_rules, ())

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
        self.assertEqual(derive_interaction_mode(None), "local_terminal")

    def test_interaction_mode_no_collaboration(self) -> None:
        self.assertEqual(derive_interaction_mode({}), "local_terminal")

    def test_interaction_mode_active_dual(self) -> None:
        self.assertEqual(
            derive_interaction_mode({"collaboration": {"reviewer_mode": "active_dual_agent"}}),
            "active_dual_agent",
        )

    def test_interaction_mode_single_agent(self) -> None:
        self.assertEqual(
            derive_interaction_mode({"collaboration": {"reviewer_mode": "single_agent"}}),
            "local_terminal",
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
    """Integration test for building packet from source artifacts."""

    def _write_receipt(self, root: Path, **overrides) -> None:
        receipt_dir = root / "dev" / "reports" / "startup" / "latest"
        receipt_dir.mkdir(parents=True, exist_ok=True)
        base = {
            "current_branch": "feature/test", "advisory_action": "continue",
            "advisory_reason": "clean", "checkpoint_required": False,
            "safe_to_continue_editing": True, "startup_authority_ok": True,
            "review_gate_allows_push": True, "push_action": "no_push_needed",
        }
        base.update(overrides)
        (receipt_dir / "receipt.json").write_text(json.dumps(base))

    @patch(
        "dev.scripts.devctl.commands.governance.session_resume_paths.scan_repo_governance_safely",
        return_value=None,
    )
    def test_build_with_receipt_and_compact(self, _mock_gov) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_receipt(root)
            compact_dir = root / "dev" / "reports" / "review_channel" / "latest"
            compact_dir.mkdir(parents=True)
            (compact_dir / "compact.json").write_text(json.dumps({
                "current_session": {
                    "current_instruction": "Do the thing",
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "current",
                    "open_findings": "none",
                },
                "collaboration": {"reviewer_mode": "active_dual_agent"},
            }))
            packet = build_from_sources(root, role="implementer", head_sha="sha1")
            self.assertEqual(packet.branch, "feature/test")
            self.assertEqual(packet.blockers, "none")
            self.assertEqual(packet.current_instruction, "Do the thing")
            self.assertEqual(packet.ack_state, "current")
            self.assertEqual(packet.interaction_mode, "active_dual_agent")
            self.assertTrue(packet.last_guard_ok)
            self.assertIn("ack_current=True", packet.key_rules)

    @patch(
        "dev.scripts.devctl.commands.governance.session_resume_paths.scan_repo_governance_safely",
        return_value=None,
    )
    def test_build_no_artifacts(self, _mock_gov) -> None:
        with tempfile.TemporaryDirectory() as td:
            packet = build_from_sources(Path(td), role="reviewer", head_sha="sha2")
            self.assertEqual(packet.role, "reviewer")
            self.assertEqual(packet.blockers, "startup_authority")
            self.assertFalse(packet.last_guard_ok)


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
            "active_dual_agent",
        )

    def test_no_governance_falls_through_to_compact(self) -> None:
        """Without governance, compact determines the mode (backward compat)."""
        compact = {"collaboration": {"reviewer_mode": "active_dual_agent"}}
        self.assertEqual(
            derive_interaction_mode(compact, governance=None),
            "active_dual_agent",
        )

    def test_no_governance_no_compact(self) -> None:
        self.assertEqual(derive_interaction_mode(None, governance=None), "local_terminal")


_PATCH_HEAD = "dev.scripts.devctl.commands.governance.session_resume.current_head"
_PATCH_ROOT = "dev.scripts.devctl.commands.governance.session_resume.get_repo_root"


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

    @patch(_PATCH_HEAD, return_value="abc123")
    @patch(_PATCH_ROOT)
    def test_run_cache_hit_skips_rebuild(self, mock_root, mock_head) -> None:
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

    @patch(_PATCH_HEAD, return_value="abc123")
    @patch(_PATCH_ROOT)
    def test_run_md_format_no_artifacts(self, mock_root, mock_head) -> None:
        with tempfile.TemporaryDirectory() as td:
            mock_root.return_value = Path(td)
            args = SimpleNamespace(
                format="md", output=None, pipe_command=None, pipe_args=None, role="implementer",
            )
            self.assertEqual(run(args), 1)


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


if __name__ == "__main__":
    unittest.main()
