"""Focused tests for the typed startup-context surface."""

from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands.listing import COMMANDS
from dev.scripts.devctl.commands.governance.startup_context import (
    _render_markdown,
    _render_summary,
)
from dev.scripts.devctl.commands.governance import startup_context as startup_context_command
from dev.scripts.devctl.runtime.startup_context import (
    ReviewerGateState,
    StartupContext,
    blocks_new_implementation,
    _derive_advisory_action,
    _derive_push_decision,
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

    def test_has_push_decision(self) -> None:
        ctx = build_startup_context()
        self.assertTrue(ctx.push_decision.action)

    def test_has_advisory_action(self) -> None:
        ctx = build_startup_context()
        self.assertIn(ctx.advisory_action, (
            "continue_editing",
            "await_review",
            "checkpoint_before_continue",
            "checkpoint_allowed",
            "push_allowed",
            "no_push_needed",
        ))
        self.assertTrue(ctx.advisory_reason)

    def test_has_work_intake(self) -> None:
        ctx = build_startup_context()
        self.assertIsNotNone(ctx.work_intake)
        self.assertTrue(ctx.work_intake.contract_id)

    def test_has_quality_signals_dict(self) -> None:
        ctx = build_startup_context()
        self.assertIsInstance(ctx.quality_signals, dict)

    def test_to_dict_serializes(self) -> None:
        ctx = build_startup_context()
        d = ctx.to_dict()
        self.assertIn("advisory_action", d)
        self.assertIn("reviewer_gate", d)
        self.assertIn("push_decision", d)
        self.assertIn("governance", d)
        self.assertIn("work_intake", d)
        self.assertIn("quality_signals", d)
        self.assertIn("rule_summary", d)
        self.assertIn("match_evidence", d)
        self.assertIn("rejected_rule_traces", d)

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

    def test_parser_accepts_summary_output(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["startup-context", "--format", "summary"])
        self.assertEqual(args.command, "startup-context")
        self.assertEqual(args.format, "summary")

    def test_handler_registered(self) -> None:
        self.assertIn("startup-context", COMMAND_HANDLERS)

    def test_in_listing(self) -> None:
        self.assertIn("startup-context", COMMANDS)

    def test_markdown_renders_configured_memory_roots(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {"repo_name": "test", "current_branch": "feature/x"},
                    "memory_roots": {
                        "memory_root": ".claude/memory",
                        "context_store_root": "dev/context",
                    },
                },
            }
        )

        self.assertIn("## Continuity Roots", rendered)
        self.assertIn("`.claude/memory`", rendered)
        self.assertIn("`dev/context`", rendered)

    def test_markdown_renders_quality_signals(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {"repo_name": "test", "current_branch": "feature/x"},
                },
                "quality_signals": {
                    "probe_report": {
                        "generated_at": "2026-03-23T00:00:00Z",
                        "risk_hints": 81,
                        "files_with_hints": 14,
                    },
                    "governance_review": {
                        "generated_at_utc": "2026-03-23T00:00:00Z",
                        "total_findings": 95,
                        "open_finding_count": 19,
                        "fixed_count": 62,
                        "cleanup_rate_pct": 65.26,
                    },
                },
            }
        )

        self.assertIn("## Quality Signals", rendered)
        self.assertIn("**probe-report**", rendered)
        self.assertIn("**governance-review**", rendered)

    def test_markdown_renders_work_intake(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {"repo_name": "test", "current_branch": "feature/x"},
                },
                "work_intake": {
                    "confidence": "high",
                    "active_target": {
                        "plan_path": "dev/active/platform_authority_loop.md",
                        "target_kind": "session_resume",
                    },
                    "continuity": {
                        "alignment_status": "aligned",
                        "alignment_reason": "scope_and_instruction_match",
                        "summary": "Land the first startup intake packet.",
                    },
                    "routing": {
                        "selected_workflow_profile": "bundle.tooling",
                        "preflight_command": "python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
                        "rule_summary": "Selected bundle.tooling for edit-first work.",
                        "match_evidence": [
                            {
                                "rule_id": "work_intake.prefer_bundle_tooling",
                                "summary": "bundle.tooling is available.",
                                "evidence": ["advisory_action=continue_editing"],
                            }
                        ],
                        "rejected_rule_traces": [
                            {
                                "rule_id": "work_intake.select_post_push_bundle",
                                "summary": "Use the post-push bundle when startup is push-ready.",
                                "rejected_because": "Startup is not push-ready yet.",
                                "evidence": [],
                            }
                        ],
                    },
                    "warm_refs": [
                        "AGENTS.md",
                        "dev/active/INDEX.md",
                        "dev/active/platform_authority_loop.md",
                    ],
                    "writeback_sinks": [
                        "dev/active/platform_authority_loop.md",
                        "dev/active/MASTER_PLAN.md",
                    ],
                },
            }
        )

        self.assertIn("## Work Intake", rendered)
        self.assertIn("dev/active/platform_authority_loop.md", rendered)
        self.assertIn("continuity_summary: Land the first startup intake packet.", rendered)
        self.assertIn("selected_workflow_profile: `bundle.tooling`", rendered)
        self.assertIn(
            "workflow_profile_rule_summary: Selected bundle.tooling for edit-first work.",
            rendered,
        )

    def test_markdown_renders_startup_and_push_rule_explanations(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "push_allowed",
                "advisory_reason": "worktree_clean_and_review_accepted",
                "rule_summary": "Startup allows the governed push path.",
                "match_evidence": [
                    {
                        "rule_id": "startup_advisory.push_allowed",
                        "summary": "All startup prerequisites for push are satisfied.",
                        "evidence": ["worktree_clean=True"],
                    }
                ],
                "rejected_rule_traces": [
                    {
                        "rule_id": "startup_advisory.no_push_needed",
                        "summary": "Stop because nothing remains to push.",
                        "rejected_because": "The branch still has remote work to publish.",
                        "evidence": [],
                    }
                ],
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {"repo_name": "test", "current_branch": "feature/x"},
                },
                "push_decision": {
                    "action": "run_devctl_push",
                    "reason": "push_preconditions_satisfied",
                    "push_eligible_now": True,
                    "has_remote_work_to_push": True,
                    "next_step_summary": "Use the governed push path now.",
                    "next_step_command": "python3 dev/scripts/devctl.py push --execute",
                    "rule_summary": "Push uses the governed path now.",
                    "match_evidence": [
                        {
                            "rule_id": "startup_push.run_devctl_push",
                            "summary": "Push prerequisites are green.",
                            "evidence": ["review_gate_allows_push=True"],
                        }
                    ],
                    "rejected_rule_traces": [
                        {
                            "rule_id": "startup_push.no_push_needed",
                            "summary": "Declare that no governed push is needed.",
                            "rejected_because": "The branch still has work to publish upstream.",
                            "evidence": [],
                        }
                    ],
                },
            }
        )

        self.assertIn(
            "startup_rule_summary: Startup allows the governed push path.",
            rendered,
        )
        self.assertIn("push_rule_summary: Push uses the governed path now.", rendered)

    def test_markdown_renders_push_next_step_guidance(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "push_allowed",
                "advisory_reason": "worktree_clean_and_review_accepted",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {"repo_name": "test", "current_branch": "feature/x"},
                },
                "push_decision": {
                    "action": "run_devctl_push",
                    "reason": "push_preconditions_satisfied",
                    "push_eligible_now": True,
                    "has_remote_work_to_push": True,
                    "next_step_summary": "Use the governed push path now.",
                    "next_step_command": (
                        "python3 dev/scripts/devctl.py push --execute"
                    ),
                },
            }
        )

        self.assertIn("next_step_summary: Use the governed push path now.", rendered)
        self.assertIn(
            "next_step_command: `python3 dev/scripts/devctl.py push --execute`",
            rendered,
        )

    def test_push_decision_recovers_remote_published_post_push_failure(self) -> None:
        governance = _minimal_governance(
            upstream_ref="origin/feature/x",
            ahead_of_upstream_commits=0,
            worktree_clean=True,
            worktree_dirty=False,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            latest_push_report_path="dev/reports/push/latest.json",
            latest_push_report_status="published_remote",
            latest_push_report_reason="post_push_bundle_failed",
            latest_push_report_published_remote=True,
            latest_push_report_post_push_green=False,
        )

        decision = _derive_push_decision(
            governance,
            ReviewerGateState(
                review_accepted=True,
                review_gate_allows_push=True,
            ),
        )

        self.assertEqual(decision.action, "no_push_needed")
        self.assertEqual(decision.reason, "remote_publish_recorded_post_push_pending")
        self.assertIn("Remote publication already succeeded", decision.next_step_summary)
        self.assertIn("dev/reports/push/latest.json", decision.next_step_summary)

    def test_summary_renders_compact_step_zero_guidance(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "checkpoint_allowed",
                "advisory_reason": "worktree_dirty_within_budget",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "implementation_block_reason": "",
                },
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    }
                },
                "push_decision": {
                    "action": "await_checkpoint",
                    "next_step_command": "",
                },
            }
        )

        self.assertEqual(
            rendered,
            "\n".join(
                (
                    "action=checkpoint_allowed",
                    "reason=worktree_dirty_within_budget",
                    "blockers=none",
                    "next=python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md",
                )
            ),
        )

    def test_summary_reports_blockers_and_rerun_when_checkpoint_is_required(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "checkpoint_before_continue",
                "advisory_reason": "dirty_path_budget_exceeded",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "implementation_block_reason": "",
                },
                "startup_authority": {"ok": False},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": True,
                        "safe_to_continue_editing": False,
                    }
                },
                "push_decision": {
                    "action": "await_checkpoint",
                    "next_step_command": "",
                },
            }
        )

        self.assertIn("blockers=startup_authority,checkpoint_required", rendered)
        self.assertIn(
            "next=checkpoint current slice, then rerun python3 dev/scripts/devctl.py startup-context --format summary",
            rendered,
        )

    def test_command_fails_closed_when_checkpoint_required(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=True,
                safe_to_continue_editing=False,
                checkpoint_reason="budget",
            ),
            reviewer_gate=ReviewerGateState(),
            advisory_action="checkpoint_before_continue",
            advisory_reason="budget",
        )
        args = build_parser().parse_args(["startup-context", "--format", "json"])

        def _fake_emit(*_args, **kwargs):
            options = kwargs["options"]
            self.assertFalse(options.ok)
            return 1

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ), patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            side_effect=_fake_emit,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 1)

    def test_command_stays_green_within_budget(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=False,
                safe_to_continue_editing=True,
            ),
            reviewer_gate=ReviewerGateState(),
            advisory_action="continue_editing",
            advisory_reason="clean_worktree",
        )
        args = build_parser().parse_args(["startup-context", "--format", "json"])

        def _fake_emit(*_args, **kwargs):
            options = kwargs["options"]
            self.assertTrue(options.ok)
            return 0

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ), patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            side_effect=_fake_emit,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 0)

    def test_command_fails_closed_when_startup_authority_is_red(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=False,
                safe_to_continue_editing=True,
            ),
            reviewer_gate=ReviewerGateState(),
            advisory_action="continue_editing",
            advisory_reason="clean_worktree",
        )
        args = build_parser().parse_args(["startup-context", "--format", "json"])

        def _fake_emit(*_args, **kwargs):
            options = kwargs["options"]
            self.assertFalse(options.ok)
            return 1

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": False,
                "checks_run": 10,
                "checks_passed": 8,
                "errors": ["over budget"],
                "warnings": [],
            },
        ), patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            side_effect=_fake_emit,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 1)


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
        self.assertFalse(gate.review_gate_allows_push)

    def test_active_bridge_accepted_permits_push(self) -> None:
        """In active mode with reviewer-accepted verdict, push is permitted."""
        gate = ReviewerGateState(
            bridge_active=True,
            reviewer_mode="active_dual_agent",
            review_accepted=True,
            review_gate_allows_push=True,
        )
        self.assertTrue(gate.review_gate_allows_push)

    def test_inactive_bridge_permits_push(self) -> None:
        gate = ReviewerGateState(
            bridge_active=False,
            review_gate_allows_push=True,
        )
        self.assertTrue(gate.review_gate_allows_push)

    def test_required_checks_status_defaults_unknown(self) -> None:
        gate = ReviewerGateState()
        self.assertEqual(gate.required_checks_status, "unknown")

    def test_no_bridge_permits_push(self) -> None:
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            gate = _detect_reviewer_gate(Path(tmp))
            self.assertTrue(gate.review_gate_allows_push)

    def test_fail_closed_default(self) -> None:
        gate = ReviewerGateState()
        self.assertFalse(gate.review_gate_allows_push)

    def test_live_verdict_based_acceptance(self) -> None:
        """On this repo, current verdict should drive review_accepted."""
        ctx = build_startup_context()
        if ctx.reviewer_gate.bridge_active:
            # Acceptance must come from verdict, not mode
            self.assertIsInstance(ctx.reviewer_gate.review_accepted, bool)

    def test_detect_reviewer_gate_requires_typed_review_state_for_bridge_sessions(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge(
                repo_root,
                "Reviewer-accepted. Narrow startup-context slice is clean.",
                "- none",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.review_accepted)
            self.assertFalse(gate.review_gate_allows_push)
            self.assertTrue(gate.implementation_blocked)
            self.assertEqual(
                gate.implementation_block_reason,
                "typed_review_state_required",
            )


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
        gov = _minimal_governance(worktree_clean=False, worktree_dirty=True)
        gate = ReviewerGateState(bridge_active=True, review_accepted=False)
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "continue_editing")
        self.assertEqual(reason, "review_pending")

    def test_await_review_when_worktree_clean_but_review_pending(self) -> None:
        gov = _minimal_governance(worktree_clean=True, worktree_dirty=False)
        gate = ReviewerGateState(bridge_active=True, review_accepted=False)
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "await_review")
        self.assertEqual(reason, "review_pending_before_push")

    def test_push_decision_requires_checkpoint_when_worktree_dirty(self) -> None:
        gov = _minimal_governance(worktree_clean=False, worktree_dirty=True)
        gate = ReviewerGateState(review_gate_allows_push=False)
        decision = _derive_push_decision(gov, gate)
        self.assertEqual(decision.action, "await_checkpoint")
        self.assertFalse(decision.push_eligible_now)
        self.assertIn("checkpoint", decision.next_step_summary.lower())

    def test_push_decision_waits_for_review_when_clean_but_unaccepted(self) -> None:
        gov = _minimal_governance(worktree_clean=True, worktree_dirty=False)
        gate = ReviewerGateState(review_gate_allows_push=False)
        decision = _derive_push_decision(gov, gate)
        self.assertEqual(decision.action, "await_review")
        self.assertEqual(decision.reason, "review_pending_before_push")
        self.assertEqual(
            decision.next_step_command,
            "python3 dev/scripts/devctl.py review-channel --action status "
            "--terminal none --format json",
        )

    def test_push_decision_runs_devctl_push_when_preconditions_hold(self) -> None:
        gov = _minimal_governance(
            worktree_clean=True,
            worktree_dirty=False,
            ahead_of_upstream_commits=1,
            upstream_ref="origin/feature/test",
        )
        gate = ReviewerGateState(review_gate_allows_push=True)
        decision = _derive_push_decision(gov, gate)
        self.assertEqual(decision.action, "run_devctl_push")
        self.assertTrue(decision.push_eligible_now)
        self.assertEqual(
            decision.next_step_command,
            "python3 dev/scripts/devctl.py push --execute",
        )

    def test_reviewer_loop_blocked(self) -> None:
        gov = _minimal_governance()
        gate = ReviewerGateState(
            bridge_active=True,
            review_accepted=False,
            implementation_blocked=True,
            implementation_block_reason="claude_ack_stale",
        )
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "checkpoint_before_continue")
        self.assertEqual(reason, "claude_ack_stale")

    def test_no_push_needed(self) -> None:
        gov = _minimal_governance(worktree_dirty=False, ahead_of_upstream_commits=0)
        gate = ReviewerGateState()
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "no_push_needed")

    def test_push_allowed(self) -> None:
        gov = _minimal_governance(
            worktree_clean=True, worktree_dirty=False, ahead_of_upstream_commits=1,
        )
        gate = ReviewerGateState(review_gate_allows_push=True)
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "push_allowed")

    def test_checkpoint_allowed(self) -> None:
        gov = _minimal_governance(worktree_dirty=True, worktree_clean=False)
        gate = ReviewerGateState(
            checkpoint_permitted=True,
            review_gate_allows_push=False,
        )
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "checkpoint_allowed")

    def test_blocks_new_implementation_when_checkpoint_required(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=True,
                safe_to_continue_editing=False,
            ),
        )
        self.assertTrue(blocks_new_implementation(ctx))

    def test_blocks_new_implementation_allows_clean_context(self) -> None:
        ctx = StartupContext(governance=_minimal_governance())
        self.assertFalse(blocks_new_implementation(ctx))

    def test_blocks_new_implementation_when_reviewer_loop_is_blocked(self) -> None:
        ctx = StartupContext(
            reviewer_gate=ReviewerGateState(
                implementation_blocked=True,
                implementation_block_reason="claude_ack_stale",
            )
        )
        self.assertTrue(blocks_new_implementation(ctx))


class TestTypedReviewStateGatePath(unittest.TestCase):
    """Verify the typed review_state.json path preserves bridge_review_accepted semantics."""

    def _write_bridge_and_typed_state(
        self,
        repo_root: Path,
        verdict: str,
        findings: str,
        reviewer_mode: str = "active_dual_agent",
        claude_ack_current: bool = True,
        attention_status: str = "healthy",
    ) -> None:
        """Write both bridge.md and review_state.json for typed-path testing."""
        bridge_text = "\n".join(
            (
                f"- Reviewer mode: `{reviewer_mode}`",
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

        # Create the typed state projection directory
        state_dir = repo_root / "dev" / "reports" / "review_channel" / "latest"
        state_dir.mkdir(parents=True, exist_ok=True)
        # Compute review_accepted the same way the projection does:
        # verdict must match accepted patterns AND findings must be clear.
        import re
        _ACCEPTED_RE = re.compile(
            r"^(?:reviewer[- ]accepted|accepted|all\s+green|resolved)\b",
            re.IGNORECASE,
        )
        _CLEAR_RE = re.compile(
            r"^(?:\(none\)|none|no\s+blockers|all\s+clear|all\s+green|resolved)\b",
            re.IGNORECASE,
        )
        verdict_ok = bool(verdict.strip() and _ACCEPTED_RE.match(verdict.strip().splitlines()[0].lstrip("- ").strip()))
        finding_lines = [ln.lstrip("- ").strip().lower() for ln in findings.splitlines() if ln.strip()]
        findings_ok = not finding_lines or all(_CLEAR_RE.match(ln) is not None for ln in finding_lines)
        review_accepted = verdict_ok and findings_ok

        state_payload = {
            "bridge": {
                "reviewer_mode": reviewer_mode,
                "open_findings": findings,
                "review_accepted": review_accepted,
                "claude_ack_current": claude_ack_current,
            },
            "attention": {
                "status": attention_status,
            },
            "current_session": {
                "implementer_ack_state": (
                    "current" if claude_ack_current else "stale"
                ),
                "open_findings": findings,
            },
        }
        (state_dir / "review_state.json").write_text(
            json.dumps(state_payload), encoding="utf-8"
        )

    def test_typed_path_uses_bridge_review_accepted_semantics(self) -> None:
        """Typed path must use verdict-based acceptance, not ack_state."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Reviewer-accepted. Clean slice.",
                "- none",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.review_accepted)
            self.assertTrue(gate.review_gate_allows_push)

    def test_typed_path_rejects_when_verdict_not_accepted(self) -> None:
        """Typed path must reject when verdict is not accepted even if ack is current."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Several findings remain.",
                "- Bridge dirtiness coupling",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.review_accepted)
            self.assertFalse(gate.review_gate_allows_push)

    def test_typed_path_blocks_new_implementation_when_ack_is_stale(self) -> None:
        """Active dual-agent stale ack should fail closed for new implementation slices."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Implementer ack is stale.",
                "- none",
                claude_ack_current=False,
                attention_status="claude_ack_stale",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.implementation_blocked)
            self.assertEqual(gate.implementation_block_reason, "claude_ack_stale")

    def test_typed_path_does_not_block_single_agent_lanes(self) -> None:
        """Single-agent reviewer mode should not trip the implementation block."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Single-agent review mode.",
                "- none",
                reviewer_mode="single_agent",
                claude_ack_current=False,
                attention_status="claude_ack_stale",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.implementation_blocked)

    def test_typed_path_uses_governance_review_root_candidate(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Reviewer-accepted. Clean slice.",
                "- none",
            )
            portable_state = repo_root / "portable" / "review_state.json"
            portable_state.parent.mkdir(parents=True, exist_ok=True)
            portable_state.write_text(
                (
                    repo_root
                    / "dev"
                    / "reports"
                    / "review_channel"
                    / "latest"
                    / "review_state.json"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (
                repo_root
                / "dev"
                / "reports"
                / "review_channel"
                / "latest"
                / "review_state.json"
            ).unlink()

            governance = replace(
                _minimal_governance(),
                artifact_roots=ArtifactRoots(
                    audit_root="",
                    review_root="portable",
                    governance_log_root="",
                    probe_report_root="",
                ),
            )
            gate = _detect_reviewer_gate(repo_root, governance=governance)

        self.assertTrue(gate.review_accepted)
        self.assertTrue(gate.review_gate_allows_push)

    def test_typed_path_does_not_block_when_implementer_was_freshly_reset_pending(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Fresh instruction reset is pending.",
                "- none",
                claude_ack_current=False,
                attention_status="claude_ack_stale",
            )
            state_path = (
                repo_root
                / "dev"
                / "reports"
                / "review_channel"
                / "latest"
                / "review_state.json"
            )
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            payload["current_session"]["implementer_status"] = "- pending"
            payload["current_session"]["implementer_ack"] = "- pending"
            payload["current_session"]["implementer_ack_state"] = "pending"
            state_path.write_text(json.dumps(payload), encoding="utf-8")

            gate = _detect_reviewer_gate(repo_root)

        self.assertFalse(gate.implementation_blocked)

    def test_typed_path_requires_typed_state_when_bridge_exists(self) -> None:
        """When review_state.json is absent, startup stays fail-closed."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            bridge_text = "\n".join(
                (
                    "- Reviewer mode: `active_dual_agent`",
                    "",
                    "## Current Verdict",
                    "- Reviewer-accepted. Clean slice.",
                    "",
                    "## Open Findings",
                    "- none",
                    "",
                    "## Current Instruction For Claude",
                    "- Continue.",
                    "",
                )
            )
            (repo_root / "bridge.md").write_text(bridge_text, encoding="utf-8")
            gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.review_accepted)
            self.assertFalse(gate.review_gate_allows_push)
            self.assertTrue(gate.implementation_blocked)
            self.assertEqual(
                gate.implementation_block_reason,
                "typed_review_state_required",
            )

    @patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot")
    def test_typed_path_prefers_refreshed_review_state_projection(
        self,
        refresh_status_snapshot_mock,
    ) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "bridge.md").write_text("# Review Bridge\n", encoding="utf-8")
            review_channel_path = repo_root / "dev" / "active" / "review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
            state_path = (
                repo_root
                / "dev"
                / "reports"
                / "review_channel"
                / "latest"
                / "review_state.json"
            )
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "bridge": {
                            "reviewer_mode": "active_dual_agent",
                            "review_accepted": True,
                            "claude_ack_current": True,
                        },
                        "current_session": {
                            "implementer_ack_state": "current",
                        },
                    }
                ),
                encoding="utf-8",
            )

            def _refresh(*, repo_root, bridge_path, review_channel_path, output_root):
                state_path.write_text(
                    json.dumps(
                        {
                            "bridge": {
                                "reviewer_mode": "active_dual_agent",
                                "review_accepted": False,
                                "claude_ack_current": False,
                            },
                            "attention": {"status": "claude_ack_stale"},
                            "current_session": {
                                "implementer_status": "Working on a stale tranche.",
                                "implementer_ack": "Old ack",
                                "implementer_ack_state": "stale",
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return type(
                    "Snapshot",
                    (),
                    {
                        "projection_paths": type(
                            "ProjectionPaths",
                            (),
                            {"review_state_path": str(state_path)},
                        )()
                    },
                )()

            refresh_status_snapshot_mock.side_effect = _refresh
            governance = replace(
                _minimal_governance(),
                artifact_roots=ArtifactRoots(
                    audit_root="",
                    review_root="dev/reports/review_channel/latest",
                    governance_log_root="",
                    probe_report_root="",
                ),
                bridge_config=BridgeConfig(
                    bridge_path="bridge.md",
                    review_channel_path="dev/active/review_channel.md",
                    bridge_active=True,
                ),
            )

            gate = _detect_reviewer_gate(repo_root, governance=governance)

        self.assertFalse(gate.review_accepted)
        self.assertFalse(gate.review_gate_allows_push)
        self.assertTrue(gate.implementation_blocked)
        self.assertEqual(gate.implementation_block_reason, "claude_ack_stale")

    def test_typed_path_inactive_mode_permits_push(self) -> None:
        """When reviewer mode is inactive, push is permitted regardless."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review.",
                "- findings here",
                reviewer_mode="single_agent",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.review_gate_allows_push)
            self.assertFalse(gate.bridge_active)


class TestPushExclusionPaths(unittest.TestCase):
    """Verify non-authoritative paths are excluded from dirty count."""

    def test_worktree_change_counts_excludes_bridge(self) -> None:
        from dev.scripts.devctl.governance.push_state import _worktree_change_counts
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            # Simulate a git repo with bridge.md dirty
            import subprocess
            subprocess.run(["git", "init"], cwd=tmp, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp, capture_output=True)
            subprocess.run(["git", "config", "user.name", "test"], cwd=tmp, capture_output=True)
            (repo_root / "bridge.md").write_text("initial")
            (repo_root / "code.py").write_text("print('hello')")
            subprocess.run(["git", "add", "."], cwd=tmp, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmp, capture_output=True)
            # Modify both files
            (repo_root / "bridge.md").write_text("modified bridge")
            (repo_root / "code.py").write_text("print('modified')")

            # Without exclusion: both files dirty
            dirty, untracked = _worktree_change_counts(repo_root)
            self.assertEqual(dirty, 2)

            # With exclusion: bridge excluded
            dirty, untracked = _worktree_change_counts(
                repo_root, exclude_paths=("bridge.md",)
            )
            self.assertEqual(dirty, 1)

    def test_checkpoint_policy_parses_compat_paths(self) -> None:
        from dev.scripts.devctl.governance.push_policy import PushCheckpointPolicy
        policy = PushCheckpointPolicy(
            compatibility_projection_paths=("bridge.md",),
        )
        self.assertEqual(policy.compatibility_projection_paths, ("bridge.md",))

    def test_worktree_change_counts_excludes_advisory_context(self) -> None:
        from dev.scripts.devctl.governance.push_state import _worktree_change_counts
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            import subprocess

            subprocess.run(["git", "init"], cwd=tmp, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmp,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "test"],
                cwd=tmp,
                capture_output=True,
            )
            (repo_root / "code.py").write_text("print('hello')")
            subprocess.run(["git", "add", "."], cwd=tmp, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmp, capture_output=True)
            (repo_root / "convo.md").write_text("scratch context")

            dirty, untracked = _worktree_change_counts(repo_root)
            self.assertEqual((dirty, untracked), (1, 1))

            dirty, untracked = _worktree_change_counts(
                repo_root,
                exclude_paths=("convo.md",),
            )
            self.assertEqual((dirty, untracked), (0, 0))

    def test_checkpoint_policy_parses_advisory_context_paths(self) -> None:
        from dev.scripts.devctl.governance.push_policy import PushCheckpointPolicy

        policy = PushCheckpointPolicy(advisory_context_paths=("convo.md",))

        self.assertEqual(policy.advisory_context_paths, ("convo.md",))

    def test_checkpoint_policy_default_empty(self) -> None:
        from dev.scripts.devctl.governance.push_policy import PushCheckpointPolicy
        policy = PushCheckpointPolicy()
        self.assertEqual(policy.compatibility_projection_paths, ())
        self.assertEqual(policy.advisory_context_paths, ())


if __name__ == "__main__":
    unittest.main()
