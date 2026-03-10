from __future__ import annotations

import unittest

from app.operator_console.state.snapshots.analytics_snapshot import RepoAnalyticsSnapshot
from app.operator_console.state.core.models import (
    AgentLaneData,
    ApprovalRequest,
    OperatorConsoleSnapshot,
)
from app.operator_console.state.snapshots.phone_status_snapshot import PhoneControlSnapshot
from app.operator_console.state.presentation.presentation_state import (
    build_activity_text,
    build_analytics_view_state,
    build_status_bar_text,
    build_system_banner_state,
    classify_approval_risk,
    snapshot_digest,
)


def _lane(
    *,
    provider_name: str,
    role_label: str,
    status_hint: str,
    state_label: str,
    rows: tuple[tuple[str, str], ...],
    raw_text: str = "raw lane text",
    risk_label: str | None = None,
    confidence_label: str | None = None,
) -> AgentLaneData:
    return AgentLaneData(
        provider_name=provider_name,
        lane_title=f"{provider_name} Bridge Monitor",
        role_label=role_label,
        status_hint=status_hint,
        state_label=state_label,
        rows=rows,
        raw_text=raw_text,
        risk_label=risk_label,
        confidence_label=confidence_label,
    )


def _approval(packet_id: str = "pkt-1") -> ApprovalRequest:
    return ApprovalRequest(
        packet_id=packet_id,
        from_agent="codex",
        to_agent="operator",
        summary="Approve guarded action",
        body="Need operator approval first.",
        policy_hint="operator_approval_required",
        requested_action="git_push",
        status="pending",
        evidence_refs=("code_audit.md#L1",),
    )


def _snapshot(
    *,
    codex_lane: AgentLaneData | None = None,
    claude_lane: AgentLaneData | None = None,
    operator_lane: AgentLaneData | None = None,
    pending_approvals: tuple[ApprovalRequest, ...] = (),
    warnings: tuple[str, ...] = (),
    review_state_path: str | None = "review_state.json",
    last_codex_poll: str | None = "2026-03-08T20:00:00Z",
    last_worktree_hash: str | None = "abc12345",
) -> OperatorConsoleSnapshot:
    return OperatorConsoleSnapshot(
        codex_panel_text="codex panel",
        claude_panel_text="claude panel",
        operator_panel_text="operator panel",
        codex_session_text="codex session",
        claude_session_text="claude session",
        raw_bridge_text="# Code Audit Channel",
        review_mode="review",
        last_codex_poll=last_codex_poll,
        last_worktree_hash=last_worktree_hash,
        pending_approvals=pending_approvals,
        warnings=warnings,
        review_state_path=review_state_path,
        codex_lane=codex_lane,
        claude_lane=claude_lane,
        operator_lane=operator_lane,
    )


class ApprovalRiskTests(unittest.TestCase):
    def test_classify_approval_risk_is_case_insensitive(self) -> None:
        self.assertEqual(classify_approval_risk("CRITICAL"), "high")
        self.assertEqual(classify_approval_risk("Review"), "medium")
        self.assertEqual(classify_approval_risk("INFO"), "low")
        self.assertEqual(classify_approval_risk("something-else"), "unknown")


class PresentationStateTests(unittest.TestCase):
    def test_build_activity_text_includes_warnings_and_bridge_metadata(self) -> None:
        snapshot = _snapshot(
            codex_lane=_lane(
                provider_name="Codex",
                role_label="Reviewer",
                status_hint="active",
                state_label="Reviewing",
                rows=(("Poll", "active"),),
            ),
            warnings=("bridge stalled",),
        )

        activity_text = build_activity_text(snapshot)

        self.assertIn("Codex - Reviewer", activity_text)
        self.assertIn("Warnings", activity_text)
        self.assertIn("bridge stalled", activity_text)
        self.assertIn("review_state.json", activity_text)
        self.assertIn("abc12345", activity_text)

    def test_build_analytics_view_state_returns_kpis_from_snapshot(self) -> None:
        snapshot = _snapshot(
            codex_lane=_lane(
                provider_name="Codex",
                role_label="Reviewer",
                status_hint="active",
                state_label="Reviewing",
                rows=(("Poll", "active"),),
            ),
            claude_lane=_lane(
                provider_name="Claude",
                role_label="Implementer",
                status_hint="warning",
                state_label="Waiting",
                rows=(("Ack", "paused"),),
            ),
            operator_lane=_lane(
                provider_name="Operator",
                role_label="Bridge State",
                status_hint="warning",
                state_label="Approval needed",
                rows=(("Approvals", "1"),),
            ),
            pending_approvals=(_approval(),),
            warnings=("needs attention",),
            last_worktree_hash="abcdef1234",
        )
        repo_analytics = RepoAnalyticsSnapshot(
            branch="develop",
            changed_files=7,
            added_files=1,
            modified_files=4,
            deleted_files=1,
            renamed_files=0,
            untracked_files=1,
            conflicted_files=0,
            top_paths=("app/operator_console/views/ui_pages.py",),
            changelog_updated=False,
            master_plan_updated=True,
            mutation_score_pct=82.5,
            mutation_age_hours=5.0,
            mutation_note=None,
            ci_runs_total=4,
            ci_success_runs=2,
            ci_failed_runs=1,
            ci_pending_runs=1,
            ci_note=None,
        )
        phone_snapshot = PhoneControlSnapshot(
            available=True,
            phase="running",
            reason="round_active",
            mode_effective="report-only",
            unresolved_count=3,
            risk="medium",
            latest_working_branch="feature/mp-359",
            next_actions=("refresh-status", "dispatch-report-only"),
            warnings_count=0,
            errors_count=0,
            age_minutes=2.5,
            source_run_url="https://example.invalid/run/1",
            note=None,
        )

        view_state = build_analytics_view_state(
            snapshot,
            repo_analytics=repo_analytics,
            phone_snapshot=phone_snapshot,
        )

        self.assertIn("REPO-VISIBLE REVIEW SIGNALS", view_state.text)
        self.assertIn("phone-status artifacts", view_state.text)
        self.assertIn("PENDING APPROVALS: 1", view_state.text)
        self.assertIn("WORKING TREE & HOTSPOTS", view_state.repo_text)
        self.assertIn("QUALITY & CI", view_state.quality_text)
        self.assertIn("MOBILE RELAY", view_state.phone_text)
        self.assertEqual(view_state.kpi_values["dirty_files"], "7")
        self.assertEqual(view_state.kpi_values["mutation_score"], "82%")
        self.assertEqual(view_state.kpi_values["ci_runs"], "2/4")
        self.assertEqual(view_state.kpi_values["warnings"], "1")
        self.assertEqual(view_state.kpi_values["pending_approvals"], "1")
        self.assertEqual(view_state.kpi_values["phone_phase"], "Running")

    def test_snapshot_digest_changes_when_structured_lane_state_changes(self) -> None:
        base_snapshot = _snapshot(
            codex_lane=_lane(
                provider_name="Codex",
                role_label="Reviewer",
                status_hint="active",
                state_label="Reviewing",
                rows=(("Poll", "active"),),
                raw_text="same raw text",
                risk_label="medium",
            )
        )
        changed_snapshot = _snapshot(
            codex_lane=_lane(
                provider_name="Codex",
                role_label="Reviewer",
                status_hint="stale",
                state_label="Waiting",
                rows=(("Poll", "active"),),
                raw_text="same raw text",
                risk_label="high",
            )
        )

        self.assertNotEqual(
            snapshot_digest(base_snapshot),
            snapshot_digest(changed_snapshot),
        )

    def test_build_system_banner_state_prefers_approval_queue_signal(self) -> None:
        snapshot = _snapshot(
            codex_lane=_lane(
                provider_name="Codex",
                role_label="Reviewer",
                status_hint="active",
                state_label="Reviewing",
                rows=(("Verdict", "pending"),),
                risk_label="medium",
                confidence_label="guarded",
            ),
            operator_lane=_lane(
                provider_name="Operator",
                role_label="Bridge State",
                status_hint="warning",
                state_label="Approval needed",
                rows=(("Approvals", "1"),),
            ),
            pending_approvals=(_approval(),),
        )

        banner = build_system_banner_state(snapshot)

        self.assertEqual(banner.health_label, "DEGRADED")
        self.assertIn("1 approval waiting", banner.detail_text)
        self.assertEqual(banner.risk_text, "Risk: medium")
        self.assertEqual(banner.confidence_text, "Confidence: guarded")

    def test_build_status_bar_text_supports_simple_and_technical_modes(self) -> None:
        snapshot = _snapshot(
            codex_lane=_lane(
                provider_name="Codex",
                role_label="Reviewer",
                status_hint="active",
                state_label="Reviewing",
                rows=(("Verdict", "pending"),),
            ),
        )

        simple_text = build_status_bar_text(snapshot, audience_mode="simple")
        technical_text = build_status_bar_text(snapshot, audience_mode="technical")

        self.assertIn("Read mode: Simple", simple_text)
        self.assertIn("Structured state available", simple_text)
        self.assertIn("review_state: review_state.json", technical_text)
        self.assertIn("Worktree hash: abc12345", technical_text)
