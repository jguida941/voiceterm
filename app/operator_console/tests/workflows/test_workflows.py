"""Tests for the workflows package: command builders, render helpers,
and terminal app live support."""

from __future__ import annotations

import json
import sys
import unittest

from app.operator_console.state.core.models import (
    ApprovalRequest,
)
from app.operator_console.workflows import (
    DEVCTL_ENTRYPOINT,
    DEVCTL_PYTHON,
    OPERATOR_DECISION_MODULE,
    REVIEW_CHANNEL_SUBCOMMAND,
    build_launch_command,
    build_operator_decision_command,
    build_orchestrate_status_command,
    build_process_audit_command,
    build_review_channel_post_command,
    build_rollover_command,
    build_status_command,
    build_swarm_run_command,
    build_triage_command,
    render_command,
    terminal_app_live_support_detail,
    terminal_app_live_supported,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _approval(packet_id: str = "pkt-1") -> ApprovalRequest:
    return ApprovalRequest(
        packet_id=packet_id,
        from_agent="codex",
        to_agent="operator",
        summary="Approve guarded push",
        body="Need operator approval.",
        policy_hint="operator_approval_required",
        requested_action="git_push",
        status="pending",
    )


# ---------------------------------------------------------------------------
# Package-level constants
# ---------------------------------------------------------------------------


class PackageConstantsTests(unittest.TestCase):
    """Verify the public constants exported at the package level."""

    def test_devctl_entrypoint_is_string(self) -> None:
        self.assertIsInstance(DEVCTL_ENTRYPOINT, str)
        self.assertTrue(DEVCTL_ENTRYPOINT.endswith(".py"))

    def test_devctl_python_matches_current_executable(self) -> None:
        self.assertEqual(DEVCTL_PYTHON, sys.executable)

    def test_review_channel_subcommand(self) -> None:
        self.assertEqual(REVIEW_CHANNEL_SUBCOMMAND, "review-channel")

    def test_operator_decision_module_is_dotted_path(self) -> None:
        self.assertIn(".", OPERATOR_DECISION_MODULE)


# ---------------------------------------------------------------------------
# Command builder: launch / rollover / status / triage / process-audit
# ---------------------------------------------------------------------------


class BuildLaunchCommandTests(unittest.TestCase):
    def test_dry_run_includes_dry_run_flag(self) -> None:
        cmd = build_launch_command(live=False)
        self.assertIn("--dry-run", cmd)

    def test_live_excludes_dry_run_flag(self) -> None:
        cmd = build_launch_command(live=True)
        self.assertNotIn("--dry-run", cmd)

    def test_includes_action_launch(self) -> None:
        cmd = build_launch_command(live=True)
        idx = cmd.index("--action")
        self.assertEqual(cmd[idx + 1], "launch")

    def test_heartbeat_refresh_flag(self) -> None:
        cmd = build_launch_command(
            live=True,
            refresh_bridge_heartbeat_if_stale=True,
        )
        self.assertIn("--refresh-bridge-heartbeat-if-stale", cmd)

    def test_scope_and_promotion_plan_flags(self) -> None:
        cmd = build_launch_command(
            live=True,
            scope="dev/active/operator_console.md",
            promotion_plan="dev/active/operator_console.md",
        )
        self.assertIn("--scope", cmd)
        self.assertIn("dev/active/operator_console.md", cmd)
        self.assertIn("--promotion-plan", cmd)

    def test_blank_scope_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_launch_command(live=True, scope="   ")


class BuildRolloverCommandTests(unittest.TestCase):
    def test_basic_structure(self) -> None:
        cmd = build_rollover_command(
            threshold_pct=80,
            await_ack_seconds=30,
            live=True,
        )
        self.assertIn("--rollover-threshold-pct", cmd)
        self.assertIn("80", cmd)
        self.assertIn("--await-ack-seconds", cmd)
        self.assertIn("30", cmd)

    def test_threshold_pct_out_of_range(self) -> None:
        with self.assertRaises(ValueError):
            build_rollover_command(threshold_pct=0, await_ack_seconds=10, live=True)
        with self.assertRaises(ValueError):
            build_rollover_command(threshold_pct=101, await_ack_seconds=10, live=True)

    def test_negative_await_ack_seconds(self) -> None:
        with self.assertRaises(ValueError):
            build_rollover_command(threshold_pct=50, await_ack_seconds=-1, live=True)


class BuildStatusCommandTests(unittest.TestCase):
    def test_default_includes_ci(self) -> None:
        cmd = build_status_command()
        self.assertIn("--ci", cmd)

    def test_no_ci_flag(self) -> None:
        cmd = build_status_command(include_ci=False)
        self.assertNotIn("--ci", cmd)

    def test_require_ci_adds_both_flags(self) -> None:
        cmd = build_status_command(require_ci=True)
        self.assertIn("--ci", cmd)
        self.assertIn("--require-ci", cmd)

    def test_format_flag(self) -> None:
        cmd = build_status_command(output_format="json")
        idx = cmd.index("--format")
        self.assertEqual(cmd[idx + 1], "json")


class BuildTriageCommandTests(unittest.TestCase):
    def test_basic_structure(self) -> None:
        cmd = build_triage_command()
        self.assertIn("triage", cmd)
        self.assertIn("--ci", cmd)

    def test_no_ci(self) -> None:
        cmd = build_triage_command(include_ci=False)
        self.assertNotIn("--ci", cmd)


class BuildProcessAuditCommandTests(unittest.TestCase):
    def test_strict_default(self) -> None:
        cmd = build_process_audit_command()
        self.assertIn("--strict", cmd)

    def test_non_strict(self) -> None:
        cmd = build_process_audit_command(strict=False)
        self.assertNotIn("--strict", cmd)


class BuildOrchestrateStatusCommandTests(unittest.TestCase):
    def test_basic_structure(self) -> None:
        cmd = build_orchestrate_status_command()
        self.assertIn("orchestrate-status", cmd)


# ---------------------------------------------------------------------------
# Command builder: review-channel post
# ---------------------------------------------------------------------------


class BuildReviewChannelPostCommandTests(unittest.TestCase):
    def test_valid_post(self) -> None:
        cmd = build_review_channel_post_command(
            to_agent="codex",
            summary="Test summary",
            body="Test body",
        )
        self.assertIn("--to-agent", cmd)
        self.assertIn("codex", cmd)
        self.assertIn("--summary", cmd)

    def test_invalid_to_agent(self) -> None:
        with self.assertRaises(ValueError):
            build_review_channel_post_command(
                to_agent="invalid",
                summary="s",
                body="b",
            )

    def test_invalid_from_agent(self) -> None:
        with self.assertRaises(ValueError):
            build_review_channel_post_command(
                to_agent="codex",
                from_agent="invalid",
                summary="s",
                body="b",
            )

    def test_invalid_kind(self) -> None:
        with self.assertRaises(ValueError):
            build_review_channel_post_command(
                to_agent="codex",
                summary="s",
                body="b",
                kind="bogus",
            )

    def test_empty_summary_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_review_channel_post_command(
                to_agent="codex",
                summary="  ",
                body="b",
            )

    def test_empty_body_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_review_channel_post_command(
                to_agent="codex",
                summary="s",
                body="  ",
            )

    def test_normalizes_agent_names(self) -> None:
        cmd = build_review_channel_post_command(
            to_agent="  CODEX  ",
            from_agent="  CLAUDE  ",
            summary="s",
            body="b",
        )
        idx_to = cmd.index("--to-agent")
        idx_from = cmd.index("--from-agent")
        self.assertEqual(cmd[idx_to + 1], "codex")
        self.assertEqual(cmd[idx_from + 1], "claude")


# ---------------------------------------------------------------------------
# Command builder: swarm run
# ---------------------------------------------------------------------------


class BuildSwarmRunCommandTests(unittest.TestCase):
    def test_basic_structure(self) -> None:
        cmd = build_swarm_run_command(
            plan_doc="dev/active/operator_console.md",
            mp_scope="MP-359",
        )
        self.assertIn("swarm_run", cmd)
        self.assertIn("--plan-doc", cmd)
        self.assertIn("--mp-scope", cmd)
        self.assertIn("--continuous", cmd)

    def test_empty_plan_doc_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_swarm_run_command(plan_doc="", mp_scope="MP-1")

    def test_empty_mp_scope_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_swarm_run_command(plan_doc="plan.md", mp_scope="  ")

    def test_max_cycles_zero_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_swarm_run_command(
                plan_doc="plan.md",
                mp_scope="MP-1",
                continuous_max_cycles=0,
            )

    def test_non_continuous(self) -> None:
        cmd = build_swarm_run_command(
            plan_doc="plan.md",
            mp_scope="MP-1",
            continuous=False,
        )
        self.assertNotIn("--continuous", cmd)

    def test_run_label_included(self) -> None:
        cmd = build_swarm_run_command(
            plan_doc="plan.md",
            mp_scope="MP-1",
            run_label="audit-run",
        )
        self.assertIn("--run-label", cmd)
        self.assertIn("audit-run", cmd)

    def test_no_feedback_sizing_flag(self) -> None:
        cmd = build_swarm_run_command(
            plan_doc="plan.md",
            mp_scope="MP-1",
            feedback_sizing=False,
        )
        self.assertIn("--no-feedback-sizing", cmd)
        self.assertNotIn("--feedback-sizing", cmd)


# ---------------------------------------------------------------------------
# Command builder: operator decision
# ---------------------------------------------------------------------------


class BuildOperatorDecisionCommandTests(unittest.TestCase):
    def test_approve_command(self) -> None:
        cmd = build_operator_decision_command(
            approval=_approval(),
            decision="approve",
        )
        self.assertIn("--decision", cmd)
        idx = cmd.index("--decision")
        self.assertEqual(cmd[idx + 1], "approve")

    def test_deny_command(self) -> None:
        cmd = build_operator_decision_command(
            approval=_approval(),
            decision="deny",
        )
        idx = cmd.index("--decision")
        self.assertEqual(cmd[idx + 1], "deny")

    def test_invalid_decision_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_operator_decision_command(
                approval=_approval(),
                decision="maybe",
            )

    def test_note_included_when_non_empty(self) -> None:
        cmd = build_operator_decision_command(
            approval=_approval(),
            decision="approve",
            note="Looks good",
        )
        self.assertIn("--note", cmd)

    def test_note_excluded_when_blank(self) -> None:
        cmd = build_operator_decision_command(
            approval=_approval(),
            decision="approve",
            note="   ",
        )
        self.assertNotIn("--note", cmd)

    def test_approval_json_in_command(self) -> None:
        cmd = build_operator_decision_command(
            approval=_approval("pkt-42"),
            decision="approve",
        )
        idx = cmd.index("--approval-json")
        payload = json.loads(cmd[idx + 1])
        self.assertEqual(payload["packet_id"], "pkt-42")


# ---------------------------------------------------------------------------
# Render command
# ---------------------------------------------------------------------------


class RenderCommandTests(unittest.TestCase):
    def test_simple_command(self) -> None:
        rendered = render_command(["echo", "hello world"])
        self.assertIn("echo", rendered)
        self.assertIn("hello world", rendered)

    def test_empty_command(self) -> None:
        rendered = render_command([])
        self.assertEqual(rendered, "")


# ---------------------------------------------------------------------------
# Terminal app live support
# ---------------------------------------------------------------------------


class TerminalAppLiveSupportTests(unittest.TestCase):
    def test_darwin_is_supported(self) -> None:
        self.assertTrue(terminal_app_live_supported(platform_name="darwin"))

    def test_linux_is_not_supported(self) -> None:
        self.assertFalse(terminal_app_live_supported(platform_name="linux"))

    def test_detail_darwin(self) -> None:
        detail = terminal_app_live_support_detail(platform_name="darwin")
        self.assertIn("macOS", detail)

    def test_detail_linux(self) -> None:
        detail = terminal_app_live_support_detail(platform_name="linux")
        self.assertIn("Dry Run", detail)
        self.assertIn("linux", detail)


if __name__ == "__main__":
    unittest.main()
