"""Tests for the governed `startup-context --repair` contract."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands.listing import COMMANDS
from dev.scripts.devctl.runtime.startup_repair import (
    StartupRepairActionRecord,
    StartupRepairIssue,
    StartupRepairResult,
    build_startup_repair_result,
    select_safe_repair_action,
)
from dev.scripts.devctl.runtime.project_governance import (
    PROJECT_GOVERNANCE_CONTRACT_ID,
    PROJECT_GOVERNANCE_SCHEMA_VERSION,
    ArtifactRoots,
    BridgeConfig,
    BundleOverrides,
    DocRegistry,
    DocPolicy,
    EnabledChecks,
    MemoryRoots,
    PathRoots,
    PlanRegistry,
    ProjectGovernance,
    PushEnforcement,
    RepoIdentity,
    RepoPackRef,
)
from dev.scripts.devctl.runtime.review_state_models import (
    AgentRegistryState,
    ReviewAttentionState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
    ReviewQueueState,
    ReviewSessionState,
    ReviewState,
)
from dev.scripts.devctl.runtime.startup_context import ReviewerGateState, StartupContext


def _minimal_governance(**push_overrides) -> ProjectGovernance:
    return ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=RepoIdentity(
            repo_name="test-repo",
            current_branch="feature/test",
        ),
        repo_pack=RepoPackRef(pack_id="test"),
        path_roots=PathRoots(),
        plan_registry=PlanRegistry(),
        artifact_roots=ArtifactRoots(review_root="dev/reports/review_channel/latest"),
        memory_roots=MemoryRoots(),
        bridge_config=BridgeConfig(
            bridge_mode="active_dual_agent",
            bridge_path="bridge.md",
            review_channel_path="dev/active/review_channel.md",
            bridge_active=True,
        ),
        enabled_checks=EnabledChecks(),
        bundle_overrides=BundleOverrides(overrides={}),
        doc_policy=DocPolicy(),
        doc_registry=DocRegistry(),
        push_enforcement=PushEnforcement(**push_overrides),
    )


def _ctx(
    *,
    push_overrides: dict[str, object] | None = None,
    reviewer_gate: ReviewerGateState | None = None,
) -> StartupContext:
    return StartupContext(
        governance=_minimal_governance(**(push_overrides or {})),
        reviewer_gate=reviewer_gate
        or ReviewerGateState(
            bridge_active=True,
            reviewer_mode="active_dual_agent",
            review_accepted=False,
        ),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )


def _review_state(
    *,
    status: str,
    owner: str,
    summary: str,
    recommended_action: str,
    recommended_command: str,
    bridge_overrides: dict[str, object] | None = None,
    errors: tuple[str, ...] = (),
) -> ReviewState:
    bridge_kwargs: dict[str, object] = {
        "overall_state": "fresh",
        "codex_poll_state": "fresh",
        "reviewer_freshness": "fresh",
        "reviewer_mode": "active_dual_agent",
        "last_codex_poll_utc": "2026-03-30T00:00:00Z",
        "last_codex_poll_age_seconds": 0,
        "last_worktree_hash": "",
        "current_instruction": "",
        "open_findings": "",
        "claude_status": "",
        "claude_ack": "",
        "claude_ack_current": False,
        "current_instruction_revision": "",
        "claude_ack_revision": "",
        "last_reviewed_scope": "",
    }
    if bridge_overrides:
        bridge_kwargs.update(bridge_overrides)
    return ReviewState(
        schema_version=1,
        contract_id="ReviewState",
        command="review-channel",
        action="status",
        timestamp="2026-03-30T00:00:00Z",
        ok=True,
        review=ReviewSessionState(
            plan_id="MP-377",
            controller_run_id="",
            session_id="markdown-bridge",
            surface_mode="markdown-bridge",
            active_lane="review",
        ),
        queue=ReviewQueueState(
            pending_total=0,
            pending_codex=0,
            pending_claude=0,
            pending_cursor=0,
            pending_operator=0,
            stale_packet_count=0,
            derived_next_instruction="",
            derived_next_instruction_source={},
        ),
        current_session=ReviewCurrentSessionState(
            current_instruction="",
            current_instruction_revision="",
            implementer_status="",
            implementer_ack="",
            implementer_ack_revision="",
            implementer_ack_state="unknown",
        ),
        bridge=ReviewBridgeState(**bridge_kwargs),
        attention=ReviewAttentionState(
            status=status,
            owner=owner,
            summary=summary,
            recommended_action=recommended_action,
            recommended_command=recommended_command,
        ),
        packets=(),
        registry=AgentRegistryState(timestamp="2026-03-30T00:00:00Z", agents=()),
        errors=errors,
    )


class StartupRepairContractTests(unittest.TestCase):
    def test_parser_accepts_startup_context_repair_mode(self) -> None:
        args = cli.build_parser().parse_args(
            ["startup-context", "--repair", "--format", "json"]
        )
        self.assertEqual(args.command, "startup-context")
        self.assertTrue(args.repair)

    def test_repair_is_not_a_second_top_level_command(self) -> None:
        self.assertIn("startup-context", cli.COMMAND_HANDLERS)
        self.assertIn("startup-context", COMMANDS)
        self.assertNotIn("startup-repair", cli.COMMAND_HANDLERS)
        self.assertNotIn("startup-repair", COMMANDS)

    def test_build_result_exposes_safe_runtime_fix(self) -> None:
        result = build_startup_repair_result(
            ctx=_ctx(),
            authority_report={"ok": True, "errors": [], "warnings": []},
            startup_receipt_path="dev/reports/startup/latest/receipt.json",
            review_state=_review_state(
                status="publisher_missing",
                owner="system",
                summary="Persistent heartbeat publisher is missing.",
                recommended_action="Start the publisher.",
                recommended_command="python3 dev/scripts/devctl.py review-channel --action ensure --start-publisher-if-missing --terminal none --format json",
            ),
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.next_action, "apply_safe_fixes")
        self.assertEqual(result.safe_fix_available_count, 1)
        self.assertEqual(result.issues[0].apply_action, "ensure_runtime")
        self.assertTrue(result.issues[0].safe_to_apply_now)

    def test_tracked_state_fix_is_blocked_by_checkpoint_boundary(self) -> None:
        result = build_startup_repair_result(
            ctx=_ctx(
                push_overrides={
                    "checkpoint_required": True,
                    "safe_to_continue_editing": False,
                }
            ),
            authority_report={"ok": False, "errors": ["checkpoint required"], "warnings": []},
            startup_receipt_path="dev/reports/startup/latest/receipt.json",
            review_state=_review_state(
                status="implementer_state_reset_required",
                owner="codex",
                summary="Stale implementer state must be reset.",
                recommended_action="Reset implementer state.",
                recommended_command="python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --reviewer-mode active_dual_agent --reason stale-implementer-launch-block --terminal none --format json",
            ),
        )

        self.assertEqual(result.next_action, "approval_required")
        self.assertEqual(result.issue_count, 2)
        repair_issue = next(
            issue for issue in result.issues if issue.issue_id == "implementer_state_reset_required"
        )
        self.assertTrue(repair_issue.repairable)
        self.assertFalse(repair_issue.safe_to_apply_now)
        self.assertTrue(repair_issue.blocked_by_approval_boundary)

    def test_review_issue_suppresses_duplicate_startup_authority_issue(self) -> None:
        result = build_startup_repair_result(
            ctx=_ctx(
                reviewer_gate=ReviewerGateState(
                    bridge_active=True,
                    reviewer_mode="active_dual_agent",
                    review_accepted=False,
                    implementation_blocked=True,
                    implementation_block_reason="bridge_contract_error",
                )
            ),
            authority_report={
                "ok": False,
                "errors": ["Reviewer loop blocks a new implementation slice: bridge_contract_error"],
                "warnings": [],
            },
            startup_receipt_path="dev/reports/startup/latest/receipt.json",
            review_state=_review_state(
                status="bridge_contract_error",
                owner="codex",
                summary="Bridge contract is inconsistent.",
                recommended_action="Re-render the bridge.",
                recommended_command="python3 dev/scripts/devctl.py review-channel --action render-bridge --terminal none --format json",
            ),
        )

        self.assertEqual(result.issue_count, 1)
        self.assertEqual(result.issues[0].issue_id, "bridge_contract_error")

    def test_bridge_contract_error_without_live_conductors_requires_manual_follow_up(
        self,
    ) -> None:
        result = build_startup_repair_result(
            ctx=_ctx(
                reviewer_gate=ReviewerGateState(
                    bridge_active=True,
                    reviewer_mode="active_dual_agent",
                    review_accepted=False,
                    implementation_blocked=True,
                    implementation_block_reason="review_loop_relaunch_required",
                )
            ),
            authority_report={
                "ok": False,
                "errors": [
                    "Reviewer loop blocks a new implementation slice: review_loop_relaunch_required"
                ],
                "warnings": [],
            },
            startup_receipt_path="dev/reports/startup/latest/receipt.json",
            review_state=_review_state(
                status="review_loop_relaunch_required",
                owner="codex",
                summary="Bridge contract is inconsistent.",
                recommended_action="Inspect the live review status.",
                recommended_command="python3 dev/scripts/devctl.py review-channel --action launch --terminal terminal-app --format json",
                bridge_overrides={
                    "codex_conductor_active": False,
                    "claude_conductor_active": False,
                },
                errors=(
                    "Reviewer mode is `active_dual_agent` but no live repo-owned Codex or Claude conductor sessions are present.",
                ),
            ),
        )

        self.assertEqual(result.issue_count, 1)
        self.assertEqual(result.next_action, "manual_follow_up")
        self.assertEqual(result.safe_fix_available_count, 0)
        issue = result.issues[0]
        self.assertEqual(issue.issue_class, "manual_follow_up")
        self.assertEqual(issue.issue_id, "review_loop_relaunch_required")
        self.assertFalse(issue.repairable)
        self.assertEqual(issue.apply_action, "")
        self.assertIn("no live repo-owned Codex or Claude conductor sessions", issue.detail)

    def test_select_safe_repair_action_uses_priority_order(self) -> None:
        result = StartupRepairResult(
            ok=False,
            issues=(
                StartupRepairIssue(
                    issue_id="bridge_contract_error",
                    issue_class="safe_local_repair",
                    source="review_channel",
                    owner="codex",
                    summary="Bridge repair needed.",
                    repairable=True,
                    safe_to_apply_now=True,
                    apply_action="render_bridge",
                    changes_tracked_state=True,
                ),
                StartupRepairIssue(
                    issue_id="publisher_missing",
                    issue_class="safe_local_repair",
                    source="review_channel",
                    owner="system",
                    summary="Publisher missing.",
                    repairable=True,
                    safe_to_apply_now=True,
                    apply_action="ensure_runtime",
                ),
            ),
        )

        self.assertEqual(select_safe_repair_action(result), "ensure_runtime")


class StartupRepairCommandTests(unittest.TestCase):
    def test_apply_safe_fixes_dispatch_emits_machine_output(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            output_path = Path(tempdir) / "startup-repair.json"
            args = cli.build_parser().parse_args(
                [
                    "startup-context",
                    "--repair",
                    "--apply-safe-fixes",
                    "--format",
                    "json",
                    "--output",
                    str(output_path),
                ]
            )
            first_state = SimpleNamespace(
                result=StartupRepairResult(
                    ok=False,
                    safe_fix_available_count=1,
                    next_action="apply_safe_fixes",
                    issues=(),
                ),
                runtime_paths=None,
            )
            second_state = SimpleNamespace(
                result=StartupRepairResult(
                    ok=True,
                    issue_count=0,
                    safe_fix_available_count=0,
                    applied_actions=(
                        StartupRepairActionRecord(
                            action_id="ensure_runtime",
                            ok=True,
                            exit_code=0,
                        ),
                    ),
                ),
                runtime_paths=None,
            )

            with patch(
                "dev.scripts.devctl.commands.governance.startup_repair._collect_state",
                side_effect=[first_state, second_state],
            ), patch(
                "dev.scripts.devctl.commands.governance.startup_repair.select_safe_repair_action",
                side_effect=["ensure_runtime"],
            ), patch(
                "dev.scripts.devctl.commands.governance.startup_repair._apply_safe_repair_action",
                return_value=StartupRepairActionRecord(
                    action_id="ensure_runtime",
                    ok=True,
                    exit_code=0,
                ),
            ):
                rc = cli.COMMAND_HANDLERS[args.command](args)
                payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(payload["command"], "startup-context")
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["applied_actions"]), 1)

    def test_apply_safe_fixes_requires_repair_flag(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "startup-context",
                "--apply-safe-fixes",
                "--format",
                "json",
            ]
        )

        rc = cli.COMMAND_HANDLERS[args.command](args)

        self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
