"""Tests for check_tandem_consistency.py — tandem-loop role-based guard."""

from __future__ import annotations

import json
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from dev.scripts.checks.tandem_consistency.report import build_report, render_md
from dev.scripts.checks.tandem_consistency.checks import (
    check_implementer_ack_freshness,
    check_implementer_completion_stall,
    check_launch_truth,
    check_plan_alignment,
    check_promotion_state,
    check_reviewed_hash_honesty,
    check_reviewer_freshness,
)


def _utc_stamp(offset_seconds: int = 0) -> str:
    ts = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _bridge(
    *,
    poll_utc: str | None = None,
    poll_local: str = "2026-03-15 01:00:00 EDT",
    reviewer_mode: str = "active_dual_agent",
    worktree_hash: str = "a" * 64,
    instruction: str = "Fix tandem guard hash check and role-profile seam.",
    ack: str = "Session 26 ack: fixing tandem guard hash check.",
    status: str = "Working on tandem guard role-profile implementation.",
    verdict: str = "In progress.",
    findings: str = "- M1: open.",
    plan_alignment: str = "- MASTER_PLAN, continuous_swarm.md",
    last_reviewed_scope: str = "- file.py",
    poll_status: str = "Reviewer active.",
) -> str:
    if poll_utc is None:
        poll_utc = _utc_stamp(-60)
    return textwrap.dedent(f"""\
        # Review Bridge

        - Last Codex poll: `{poll_utc}`
        - Last Codex poll (Local America/New_York): `{poll_local}`
        - Reviewer mode: `{reviewer_mode}`
        - Last non-audit worktree hash: `{worktree_hash}`

        ## Start-Of-Conversation Rules

        Rules here.

        ## Protocol

        Protocol here.

        ## Poll Status

        {poll_status}

        ## Current Verdict
        {verdict}

        ## Open Findings
        {findings}

        ## Claude Status
        {status}

        ## Claude Questions

        None.

        ## Claude Ack
        {ack}

        ## Current Instruction For Claude
        {instruction}

        ## Plan Alignment
        {plan_alignment}

        ## Last Reviewed Scope
        {last_reviewed_scope}
    """)


class TestReviewerFreshness:
    def test_fresh_heartbeat_passes(self):
        text = _bridge(poll_utc=_utc_stamp(-60))
        result = check_reviewer_freshness(text)
        assert result["ok"] is True
        assert result["role"] == "reviewer"

    def test_stale_heartbeat_fails(self):
        text = _bridge(poll_utc=_utc_stamp(-900))
        result = check_reviewer_freshness(text)
        assert result["ok"] is False
        assert "stale" in result["detail"].lower()

    def test_missing_heartbeat_fails(self):
        text = "# No metadata here\n## Poll Status\nHello."
        result = check_reviewer_freshness(text)
        assert result["ok"] is False

    def test_poll_due_status(self):
        text = _bridge(poll_utc=_utc_stamp(-200))
        result = check_reviewer_freshness(text)
        assert result["ok"] is True
        assert result["status"] == "poll_due"

    def test_ci_skips_staleness(self):
        text = _bridge(poll_utc=_utc_stamp(-900))
        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
            result = check_reviewer_freshness(text)
        assert result["ok"] is True

    def test_inactive_mode_skips_reviewer_freshness(self):
        text = _bridge(poll_utc=_utc_stamp(-900), reviewer_mode="tools_only")
        result = check_reviewer_freshness(text)
        assert result["ok"] is True
        assert result["status"] == "inactive"


class TestImplementerAckFreshness:
    def test_present_ack_passes(self):
        text = _bridge()
        result = check_implementer_ack_freshness(text)
        assert result["ok"] is True
        assert result["role"] == "implementer"

    def test_missing_ack_fails(self):
        text = _bridge(ack="")
        result = check_implementer_ack_freshness(text)
        assert result["ok"] is False

    def test_missing_status_fails(self):
        text = _bridge(status="")
        result = check_implementer_ack_freshness(text)
        assert result["ok"] is False

    def test_no_instruction_skips(self):
        text = _bridge(instruction="")
        result = check_implementer_ack_freshness(text)
        assert result["ok"] is True

    def test_tranche_aligned(self):
        text = _bridge(
            instruction="Fix M11 tandem guard hash check.",
            ack="Session 26 ack: fixing M11 tandem guard.",
            status="Working on tandem guard hash check.",
        )
        result = check_implementer_ack_freshness(text)
        assert result["ok"] is True
        assert result["tranche_aligned"] is True

    def test_tranche_misaligned(self):
        text = _bridge(
            instruction="Fix M11 tandem guard hash check.",
            ack="Widening pass 12 complete.",
            status="Pushed checkpoint.",
        )
        result = check_implementer_ack_freshness(text)
        assert result["ok"] is False
        assert result["tranche_aligned"] is False

    def test_inactive_mode_skips_ack_requirement(self):
        text = _bridge(reviewer_mode="single_agent", ack="", status="")
        result = check_implementer_ack_freshness(text)
        assert result["ok"] is True
        assert result["tranche_aligned"] is None


class TestReviewedHashHonesty:
    def test_valid_hash_passes(self):
        text = _bridge(worktree_hash="b" * 64)
        result = check_reviewed_hash_honesty(text)
        assert result["ok"] is True
        assert result["role"] == "reviewer"

    def test_short_hash_fails(self):
        text = _bridge(worktree_hash="abc123")
        result = check_reviewed_hash_honesty(text)
        assert result["ok"] is False

    def test_missing_hash_fails(self):
        text = "# No hash here\n## Poll Status\nHello."
        result = check_reviewed_hash_honesty(text)
        assert result["ok"] is False


class TestImplementerCompletionStall:
    def test_active_stall_fails(self):
        text = _bridge(
            status="Instruction unchanged. Continuing to poll while Codex reviews.",
            ack="Codex should review and promote the next slice.",
        )
        result = check_implementer_completion_stall(text)
        assert result["ok"] is False
        assert result["stalled"] is True

    def test_explicit_wait_state_allows_polling(self):
        text = _bridge(
            instruction="Hold steady while Codex commits/pushes the accepted slice.",
            status="Continuing to poll while Codex commits/pushes.",
            ack="Waiting for reviewer promotion.",
        )
        result = check_implementer_completion_stall(text)
        assert result["ok"] is True
        assert result["wait_state"] is True

    def test_inactive_mode_waiting_for_review_fails(self):
        text = _bridge(
            reviewer_mode="single_agent",
            status="Instruction unchanged. Continuing to poll for Codex review.",
            ack="Waiting for Codex review.",
        )
        result = check_implementer_completion_stall(text)
        assert result["ok"] is False
        assert result["reviewer_mode"] == "single_agent"

    def test_no_stall_markers_passes(self):
        text = _bridge(status="Still implementing the active slice.")
        result = check_implementer_completion_stall(text)
        assert result["ok"] is True
        assert result["stalled"] is False


class TestPlanAlignment:
    def test_valid_alignment_passes(self):
        text = _bridge()
        result = check_plan_alignment(text)
        assert result["ok"] is True
        assert result["role"] == "operator"
        assert "chain is complete" in result["detail"]

    def test_missing_master_plan_fails(self):
        text = _bridge(plan_alignment="- continuous_swarm.md only")
        result = check_plan_alignment(text)
        assert result["ok"] is False

    def test_missing_continuous_swarm_fails(self):
        text = _bridge(plan_alignment="- MASTER_PLAN only")
        result = check_plan_alignment(text)
        assert result["ok"] is False
        assert "continuous_swarm.md" in result["detail"]


class TestPromotionState:
    def test_active_work_passes(self):
        text = _bridge()
        result = check_promotion_state(text)
        assert result["ok"] is True
        assert result["status"] == "active"

    def test_no_instruction_fails(self):
        text = _bridge(instruction="")
        result = check_promotion_state(text)
        assert result["ok"] is False

    def test_accepted_no_findings_ready(self):
        text = _bridge(verdict="All slices accepted.", findings="")
        result = check_promotion_state(text)
        assert result["ok"] is True
        assert result["status"] == "ready_for_promotion"

    def test_inactive_mode_marks_promotion_inactive(self):
        text = _bridge(reviewer_mode="offline")
        result = check_promotion_state(text)
        assert result["ok"] is True
        assert result["status"] == "inactive"


class TestLaunchTruth:
    def test_consistent_state_passes(self):
        text = _bridge()
        result = check_launch_truth(text)
        assert result["ok"] is True
        assert result["role"] == "system"

    def test_missing_ack_reports_issue(self):
        text = _bridge(ack="")
        result = check_launch_truth(text)
        assert any("ACK" in issue for issue in result["issues"])

    def test_inactive_mode_marks_launch_truth_inactive(self):
        text = _bridge(reviewer_mode="paused", ack="", status="")
        result = check_launch_truth(text)
        assert result["ok"] is True
        assert result["overall_state"] == "inactive"


def _mock_hash_matching():
    """Mock the worktree hash computation to return the default test hash."""
    return mock.patch(
        "dev.scripts.checks.tandem_consistency.reviewer_checks.compute_non_audit_worktree_hash",
        return_value="a" * 64,
    )


class TestBuildReport:
    def test_full_report_passes(self):
        text = _bridge()
        with _mock_hash_matching():
            report = build_report(bridge_text=text)
        assert report["ok"] is True
        assert report["total_checks"] == 7
        assert report["passed"] == 7
        assert report["failed"] == 0
        role_summary = report["role_summary"]
        assert role_summary["reviewer"] == "healthy"
        assert role_summary["implementer"] == "healthy"
        assert role_summary["operator"] == "healthy"

    def test_no_bridge_skips(self):
        report = build_report(bridge_text=None)
        assert report["ok"] is True
        assert report["bridge_present"] is False

    def test_stale_reviewer_degrades(self):
        text = _bridge(poll_utc=_utc_stamp(-900))
        with _mock_hash_matching():
            report = build_report(bridge_text=text)
        assert report["ok"] is False
        assert report["role_summary"]["reviewer"] == "degraded"

    def test_hash_mismatch_degrades(self):
        text = _bridge()
        with mock.patch(
            "dev.scripts.checks.tandem_consistency.reviewer_checks.compute_non_audit_worktree_hash",
            return_value="b" * 64,
        ):
            report = build_report(bridge_text=text, repo_root=Path("."))
        # Hash mismatch fails in local tandem review
        assert report["ok"] is False
        hash_check = next(c for c in report["checks"] if c["check"] == "reviewed_hash_honesty")
        assert hash_check["matches_current"] is False
        assert hash_check["ok"] is False


class TestRenderMd:
    def test_markdown_output(self):
        text = _bridge()
        with _mock_hash_matching():
            report = build_report(bridge_text=text)
        md = render_md(report)
        assert "check_tandem_consistency" in md
        assert "[PASS]" in md

    def test_json_output(self):
        text = _bridge()
        with _mock_hash_matching():
            report = build_report(bridge_text=text)
        parsed = json.loads(json.dumps(report))
        assert parsed["ok"] is True


# ─── Typed review_state.json path tests ────────────────────────────────


def _typed_state(
    *,
    reviewer_mode: str = "active_dual_agent",
    reviewer_freshness: str = "fresh",
    last_codex_poll_age_seconds: int = 60,
    claude_ack_current: bool = True,
    implementer_completion_stall: bool = False,
    review_accepted: bool = False,
    current_instruction: str = "Fix the tandem guard.",
    implementer_ack: str = "Session 45 ack: fixing tandem guard.",
    implementer_status: str = "Working on tandem guard.",
    implementer_ack_state: str = "current",
    open_findings: str = "- H1: open.",
    last_reviewed_scope: str = "- file.py",
) -> dict[str, object]:
    """Build a minimal typed review_state.json payload for testing."""
    return {
        "bridge": {
            "reviewer_mode": reviewer_mode,
            "reviewer_freshness": reviewer_freshness,
            "last_codex_poll_age_seconds": last_codex_poll_age_seconds,
            "claude_ack_current": claude_ack_current,
            "implementer_completion_stall": implementer_completion_stall,
            "review_accepted": review_accepted,
            "current_instruction": current_instruction,
            "open_findings": open_findings,
        },
        "current_session": {
            "current_instruction": current_instruction,
            "implementer_ack": implementer_ack,
            "implementer_status": implementer_status,
            "implementer_ack_state": implementer_ack_state,
            "open_findings": open_findings,
            "last_reviewed_scope": last_reviewed_scope,
        },
    }


class TestTypedPathReviewerFreshness:
    """Verify check_reviewer_freshness prefers typed state when available."""

    def test_typed_fresh_passes(self):
        text = _bridge()
        result = check_reviewer_freshness(
            text, typed_state=_typed_state(reviewer_freshness="fresh", last_codex_poll_age_seconds=30)
        )
        assert result["ok"] is True
        assert result["status"] == "fresh"

    def test_typed_stale_fails(self):
        text = _bridge()
        result = check_reviewer_freshness(
            text, typed_state=_typed_state(last_codex_poll_age_seconds=700)
        )
        assert result["ok"] is False
        assert "stale" in result["detail"].lower()

    def test_typed_inactive_mode_passes(self):
        text = _bridge()
        result = check_reviewer_freshness(
            text, typed_state=_typed_state(reviewer_mode="single_agent")
        )
        assert result["ok"] is True
        assert result["status"] == "inactive"

    def test_falls_back_to_bridge_when_typed_missing(self):
        text = _bridge(poll_utc=_utc_stamp(-60))
        result = check_reviewer_freshness(text, typed_state=None)
        assert result["ok"] is True


class TestTypedPathImplementerAck:
    """Verify check_implementer_ack_freshness prefers typed state."""

    def test_typed_ack_current_passes(self):
        text = _bridge()
        result = check_implementer_ack_freshness(
            text, typed_state=_typed_state(claude_ack_current=True)
        )
        assert result["ok"] is True
        assert result["tranche_aligned"] is True

    def test_typed_ack_stale_fails(self):
        text = _bridge()
        result = check_implementer_ack_freshness(
            text, typed_state=_typed_state(claude_ack_current=False)
        )
        assert result["ok"] is False
        assert result["tranche_aligned"] is False

    def test_falls_back_to_bridge_when_typed_missing(self):
        text = _bridge()
        result = check_implementer_ack_freshness(text, typed_state=None)
        assert result["ok"] is True  # bridge fixture has matching ack


class TestTypedPathCompletionStall:
    """Verify check_implementer_completion_stall uses typed pre-computed flag."""

    def test_typed_not_stalled_passes(self):
        text = _bridge()
        result = check_implementer_completion_stall(
            text, typed_state=_typed_state(implementer_completion_stall=False)
        )
        assert result["ok"] is True
        assert result["stalled"] is False

    def test_typed_stalled_fails(self):
        text = _bridge()
        result = check_implementer_completion_stall(
            text, typed_state=_typed_state(implementer_completion_stall=True)
        )
        assert result["ok"] is False
        assert result["stalled"] is True

    def test_falls_back_to_bridge_when_typed_missing(self):
        text = _bridge()
        result = check_implementer_completion_stall(text, typed_state=None)
        assert result["ok"] is True


class TestTypedPathPromotionState:
    """Verify check_promotion_state uses typed review_accepted."""

    def test_typed_accepted_no_findings_ready(self):
        text = _bridge()
        result = check_promotion_state(
            text,
            typed_state=_typed_state(review_accepted=True, open_findings="(none)"),
        )
        assert result["ok"] is True
        assert result["status"] == "ready_for_promotion"

    def test_typed_not_accepted_active(self):
        text = _bridge()
        result = check_promotion_state(
            text, typed_state=_typed_state(review_accepted=False)
        )
        assert result["ok"] is True
        assert result["status"] == "active"

    def test_falls_back_to_bridge_when_typed_missing(self):
        text = _bridge()
        result = check_promotion_state(text, typed_state=None)
        assert result["ok"] is True


class TestTypedPathBuildReport:
    """Verify build_report annotates typed_review_state_available."""

    def test_report_with_typed_state(self, tmp_path):
        text = _bridge()
        state_dir = tmp_path / "dev" / "reports" / "review_channel" / "latest"
        state_dir.mkdir(parents=True)
        (state_dir / "review_state.json").write_text(
            json.dumps(_typed_state()), encoding="utf-8"
        )
        with _mock_hash_matching():
            report = build_report(bridge_text=text, repo_root=tmp_path)
        assert report["typed_review_state_available"] is True

    def test_report_without_typed_state(self):
        text = _bridge()
        with _mock_hash_matching():
            report = build_report(bridge_text=text, repo_root=None)
        assert report["typed_review_state_available"] is False

    def test_report_uses_review_state_candidate_path(self, tmp_path):
        text = _bridge()
        state_dir = (
            tmp_path
            / "dev"
            / "reports"
            / "review_channel"
            / "projections"
            / "latest"
        )
        state_dir.mkdir(parents=True)
        (state_dir / "review_state.json").write_text(
            json.dumps(_typed_state()), encoding="utf-8"
        )
        with _mock_hash_matching():
            report = build_report(bridge_text=text, repo_root=tmp_path)
        assert report["typed_review_state_available"] is True
