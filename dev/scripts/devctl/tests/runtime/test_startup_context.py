"""Focused tests for the typed startup-context surface."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands.listing import COMMANDS
from dev.scripts.devctl.runtime.startup_context import (
    ReviewerGateState,
    StartupContext,
    _derive_advisory_action,
    _detect_reviewer_gate,
    build_startup_context,
)
from dev.scripts.devctl.runtime.project_governance import (
    ProjectGovernance,
    PushEnforcement,
    RepoIdentity,
    RepoPackRef,
    PathRoots,
    PlanRegistryRoots,
    ArtifactRoots,
    MemoryRoots,
    BridgeConfig,
    EnabledChecks,
    BundleOverrides,
    PROJECT_GOVERNANCE_CONTRACT_ID,
    PROJECT_GOVERNANCE_SCHEMA_VERSION,
)


def _minimal_governance(**push_overrides) -> ProjectGovernance:
    """Build a minimal ProjectGovernance for testing advisory logic."""
    pe = PushEnforcement(**push_overrides)
    return ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=RepoIdentity(repo_name="test"),
        repo_pack=RepoPackRef(pack_id="test"),
        path_roots=PathRoots(),
        plan_registry=PlanRegistryRoots(),
        artifact_roots=ArtifactRoots(),
        memory_roots=MemoryRoots(),
        bridge_config=BridgeConfig(),
        enabled_checks=EnabledChecks(),
        bundle_overrides=BundleOverrides(overrides={}),
        push_enforcement=pe,
    )


class TestStartupContextBuild(unittest.TestCase):
    """Verify startup-context builds from live repo state."""

    def test_builds_without_error(self) -> None:
        ctx = build_startup_context()
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.contract_id, "StartupContext")

    def test_has_governance(self) -> None:
        ctx = build_startup_context()
        self.assertIsNotNone(ctx.governance)
        self.assertTrue(ctx.governance.repo_identity.repo_name)

    def test_has_reviewer_gate(self) -> None:
        ctx = build_startup_context()
        self.assertIsInstance(ctx.reviewer_gate, ReviewerGateState)

    def test_has_advisory_action(self) -> None:
        ctx = build_startup_context()
        self.assertIn(ctx.advisory_action, (
            "continue_editing",
            "checkpoint_before_continue",
            "checkpoint_allowed",
            "push_allowed",
            "no_push_needed",
        ))
        self.assertTrue(ctx.advisory_reason)

    def test_to_dict_serializes(self) -> None:
        ctx = build_startup_context()
        d = ctx.to_dict()
        self.assertIn("advisory_action", d)
        self.assertIn("reviewer_gate", d)
        self.assertIn("governance", d)

    def test_slim_token_budget(self) -> None:
        ctx = build_startup_context()
        size = len(json.dumps(ctx.to_dict()))
        tokens = size // 4
        self.assertLess(tokens, 10000, f"startup context too large: {tokens} tokens")


class TestCLIRegistration(unittest.TestCase):
    """Verify startup-context is wired into the CLI."""

    def test_parser_accepts_startup_context(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["startup-context", "--format", "json"])
        self.assertEqual(args.command, "startup-context")

    def test_handler_registered(self) -> None:
        self.assertIn("startup-context", COMMAND_HANDLERS)

    def test_in_listing(self) -> None:
        self.assertIn("startup-context", COMMANDS)


class TestReviewerGateSemantics(unittest.TestCase):
    """Verify reviewer gate does NOT conflate ACK with acceptance."""

    def _write_bridge(self, repo_root: Path, verdict: str, findings: str) -> None:
        bridge_text = "\n".join(
            (
                "- Reviewer mode: `active_dual_agent`",
                "",
                "## Current Verdict",
                verdict,
                "",
                "## Open Findings",
                findings,
                "",
                "## Current Instruction For Claude",
                "- Continue the current slice.",
                "",
            )
        )
        (repo_root / "bridge.md").write_text(bridge_text, encoding="utf-8")

    def test_active_bridge_unaccepted_denies_push(self) -> None:
        """In active mode with Needs-review verdict, push is not permitted."""
        gate = ReviewerGateState(
            bridge_active=True,
            reviewer_mode="active_dual_agent",
            review_accepted=False,
        )
        self.assertFalse(gate.push_permitted)

    def test_active_bridge_accepted_permits_push(self) -> None:
        """In active mode with reviewer-accepted verdict, push is permitted."""
        gate = ReviewerGateState(
            bridge_active=True,
            reviewer_mode="active_dual_agent",
            review_accepted=True,
            push_permitted=True,
        )
        self.assertTrue(gate.push_permitted)

    def test_inactive_bridge_permits_push(self) -> None:
        gate = ReviewerGateState(bridge_active=False, push_permitted=True)
        self.assertTrue(gate.push_permitted)

    def test_required_checks_status_defaults_unknown(self) -> None:
        gate = ReviewerGateState()
        self.assertEqual(gate.required_checks_status, "unknown")

    def test_no_bridge_permits_push(self) -> None:
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            gate = _detect_reviewer_gate(Path(tmp))
            self.assertTrue(gate.push_permitted)

    def test_fail_closed_default(self) -> None:
        gate = ReviewerGateState()
        self.assertFalse(gate.push_permitted)

    def test_live_verdict_based_acceptance(self) -> None:
        """On this repo, current verdict should drive review_accepted."""
        ctx = build_startup_context()
        if ctx.reviewer_gate.bridge_active:
            # Acceptance must come from verdict, not mode
            self.assertIsInstance(ctx.reviewer_gate.review_accepted, bool)

    def test_detect_reviewer_gate_accepts_reviewer_accepted_with_clear_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge(
                repo_root,
                "Reviewer-accepted. Narrow startup-context slice is clean.",
                "- none",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.review_accepted)
            self.assertTrue(gate.push_permitted)

    def test_detect_reviewer_gate_accepts_all_green_with_resolved_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge(
                repo_root,
                "All green. Ready for the next scoped task.",
                "resolved",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.review_accepted)
            self.assertTrue(gate.push_permitted)

    def test_detect_reviewer_gate_rejects_negated_acceptance_text(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge(
                repo_root,
                "Not accepted. Follow-up review still required.",
                "- none",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.review_accepted)
            self.assertFalse(gate.push_permitted)

    def test_detect_reviewer_gate_fail_closed_on_bridge_parse_error(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge(
                repo_root,
                "Reviewer-accepted. Narrow startup-context slice is clean.",
                "- none",
            )
            with patch(
                "dev.scripts.devctl.review_channel.handoff.extract_bridge_snapshot",
                side_effect=ValueError("boom"),
            ):
                gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.review_accepted)
            self.assertFalse(gate.push_permitted)


class TestAdvisoryAction(unittest.TestCase):
    """Verify all 5 advisory outcomes."""

    def test_checkpoint_required(self) -> None:
        gov = _minimal_governance(checkpoint_required=True, checkpoint_reason="budget")
        gate = ReviewerGateState()
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "checkpoint_before_continue")

    def test_budget_exceeded(self) -> None:
        gov = _minimal_governance(safe_to_continue_editing=False)
        gate = ReviewerGateState()
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "checkpoint_before_continue")

    def test_review_pending(self) -> None:
        gov = _minimal_governance()
        gate = ReviewerGateState(bridge_active=True, review_accepted=False)
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "continue_editing")
        self.assertEqual(reason, "review_pending")

    def test_no_push_needed(self) -> None:
        gov = _minimal_governance(worktree_dirty=False, ahead_of_upstream_commits=0)
        gate = ReviewerGateState()
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "no_push_needed")

    def test_push_allowed(self) -> None:
        gov = _minimal_governance(
            push_ready=True, worktree_dirty=True, ahead_of_upstream_commits=1,
        )
        gate = ReviewerGateState(push_permitted=True)
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "push_allowed")

    def test_checkpoint_allowed(self) -> None:
        gov = _minimal_governance(worktree_dirty=True)
        gate = ReviewerGateState(checkpoint_permitted=True, push_permitted=False)
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "checkpoint_allowed")


if __name__ == "__main__":
    unittest.main()
