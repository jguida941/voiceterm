"""Regression tests for Phase 0.4-Bootstrap authority ordering."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from dev.scripts.devctl.commands.review_channel import bridge_support
from dev.scripts.devctl.commands.review_channel.bridge_success_report import (
    BridgeSuccessReportRequest,
    build_bridge_success_report,
)
from dev.scripts.devctl.commands.review_channel.event_action_support import (
    EventActionContext,
)
from dev.scripts.devctl.commands.review_channel.event_handler import (
    _review_channel_lifecycle_gate,
)
from dev.scripts.devctl.review_channel.bridge_runtime_state import BridgeStateContext
from dev.scripts.devctl.review_channel.launch_authority_ordering import (
    evaluate_launch_bypass_authority,
    require_valid_launch_bypass_if_requested,
)
from dev.scripts.devctl.runtime.control_decision_obedience import (
    build_attempted_action_receipt,
    evaluate_control_decision_obedience,
)
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BypassAuthorityScope,
    BypassEvaluation,
    BypassEvaluationDecision,
    BypassLifecycle,
    BypassLifecycleState,
    BypassReceipt,
    BypassRequest,
)

NOW = datetime(2026, 5, 18, 20, 30, tzinfo=timezone.utc)


def _args(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "action": "launch",
        "execution_mode": "markdown-bridge",
        "dry_run": True,
        "reviewer_mode": "",
        "reason": "",
        "bypass_receipt_id": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _stale_bridge(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Bridge",
                "",
                "- Reviewer mode: `active_dual_agent`",
                "- Last Codex poll: `2026-05-18T10:00:00Z`",
                "",
                "## Current Instruction For Implementer",
                "",
                "Fix the launcher authority ordering.",
                "",
                "## Last Reviewed Scope",
                "",
                "dev/scripts/devctl/review_channel/",
                "",
                "## Poll Status",
                "",
                "stale",
            ]
        ),
        encoding="utf-8",
    )


def _bridge_context(tmp_path: Path) -> BridgeStateContext:
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True)
    review_channel_path.write_text("lanes patched by test\n", encoding="utf-8")
    bridge_path = tmp_path / "bridge.md"
    _stale_bridge(bridge_path)
    status_dir = tmp_path / "dev/reports/review_channel/latest"
    status_dir.mkdir(parents=True)
    return BridgeStateContext(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        status_dir=status_dir,
    )


def _patch_bridge_prereqs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bridge_support,
        "ensure_launcher_prereqs",
        lambda **_kwargs: ("", []),
    )
    monkeypatch.setattr(
        bridge_support,
        "maybe_refresh_stale_bridge_heartbeat",
        lambda **_kwargs: None,
    )


def _write_lifecycle(
    root: Path,
    *,
    receipt_id: str,
    scope: BypassAuthorityScope = BypassAuthorityScope.EDIT_ONLY,
    expires_at_utc: str = "2026-05-19T00:00:00+00:00",
    state: BypassLifecycleState = BypassLifecycleState.ACTIVE,
) -> None:
    store_path = root / "dev/state/bypass_lifecycles.jsonl"
    store_path.parent.mkdir(parents=True)
    request = BypassRequest(
        request_id="request-1",
        scope=scope,
        reason="operator-approved launch precondition bypass",
        actor="operator",
        requested_at_utc="2026-05-18T20:00:00+00:00",
        target_surface="review-channel-launch",
    )
    evaluation = BypassEvaluation(
        evaluation_id="evaluation-1",
        request_id=request.request_id,
        decision=BypassEvaluationDecision.APPROVED,
        evaluated_at_utc="2026-05-18T20:00:00+00:00",
        evaluator_actor_id="operator",
        reason="operator_approved_bypass_request",
        approved_scope=scope,
    )
    receipt = BypassReceipt(
        receipt_id=receipt_id,
        reason="operator-approved launch precondition bypass",
        operator_signature="operator",
        ai_approval_evidence="test",
        requested_authority_scope=scope,
        granted_at_utc="2026-05-18T20:00:00+00:00",
        granted_by_operator_actor_id="operator",
        expires_at_utc=expires_at_utc,
    )
    lifecycle = BypassLifecycle(
        lifecycle_id=f"gel:bypass:{receipt_id}",
        state=state,
        request=request,
        evaluation=evaluation,
        receipt=receipt,
    )
    store_path.write_text(json.dumps(lifecycle.to_dict()) + "\n", encoding="utf-8")


def test_stale_bridge_without_receipt_rejects_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_bridge_prereqs(monkeypatch)

    with pytest.raises(ValueError, match="live bridge contract"):
        bridge_support.bridge_launch_state(
            args=_args(),
            context=_bridge_context(tmp_path),
            bridge_actions={"launch"},
            build_bridge_guard_report_fn=lambda **_kwargs: {"ok": True},
        )


def test_stale_bridge_with_invalid_receipt_rejects_before_bridge(
    tmp_path: Path,
) -> None:
    args = _args(bypass_receipt_id="bypass:missing")

    with pytest.raises(ValueError, match="invalid_receipt"):
        require_valid_launch_bypass_if_requested(
            args=args,
            repo_root=tmp_path,
            now_utc=NOW,
        )

    assert args.launch_authority_report["bypass_receipt_validated"] is False
    assert args.launch_authority_report["rejected_reason"] == "invalid_receipt"


def test_stale_bridge_with_expired_receipt_rejects_before_bridge(
    tmp_path: Path,
) -> None:
    receipt_id = "bypass:expired"
    _write_lifecycle(
        tmp_path,
        receipt_id=receipt_id,
        expires_at_utc="2026-05-18T19:00:00+00:00",
    )
    args = _args(bypass_receipt_id=receipt_id)

    with pytest.raises(ValueError, match="expired_receipt"):
        require_valid_launch_bypass_if_requested(
            args=args,
            repo_root=tmp_path,
            now_utc=NOW,
        )

    assert args.launch_authority_report["rejected_reason"] == "expired_receipt"


def test_stale_bridge_with_valid_receipt_reaches_launch_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_bridge_prereqs(monkeypatch)
    receipt_id = "bypass:grant-20260517T161231716807"
    _write_lifecycle(tmp_path, receipt_id=receipt_id)
    authority_report = evaluate_launch_bypass_authority(
        repo_root=tmp_path,
        bypass_receipt_id=receipt_id,
        now_utc=NOW,
    )

    result = bridge_support.bridge_launch_state(
        args=_args(bypass_receipt_id=receipt_id),
        context=_bridge_context(tmp_path),
        bridge_actions={"launch"},
        launch_authority_report=authority_report,
        build_bridge_guard_report_fn=lambda **_kwargs: {"ok": True},
    )

    assert authority_report["bypass_receipt_validated"] is True
    assert authority_report["bridge_gate_bypassed"] is True
    assert authority_report["bypass_scope"] == "launch_precondition_only"
    assert result.bridge_liveness["codex_poll_state"] in {"stale", "missing"}


def test_launch_success_report_carries_structured_bypass_fields() -> None:
    receipt_id = "bypass:grant-20260517T161231716807"
    args = _args(bypass_receipt_id=receipt_id)
    args.launch_authority_report = {
        "bypass_receipt_id": receipt_id,
        "bypass_receipt_validated": True,
        "bridge_gate_bypassed": True,
        "bypass_scope": "launch_precondition_only",
        "rejected_reason": "",
    }
    args.terminal = "none"
    args.terminal_profile = None
    args.approval_mode = None
    args.dangerous = False
    args.rollover_threshold_pct = None
    args.rollover_trigger = None
    args.await_ack_seconds = 0
    args.launch_visibility = "visible"
    args.codex_workers = 0
    args.claude_workers = 0

    report, exit_code = build_bridge_success_report(
        BridgeSuccessReportRequest(
            args=args,
            bridge_liveness={"overall_state": "fresh"},
            attention={},
            reviewer_worker=None,
            codex_lanes=[],
            claude_lanes=[],
            terminal_profile_applied=None,
            warnings=[],
            sessions=[],
            handoff_bundle=None,
            projection_paths=None,
            launched=False,
            handoff_ack_required=False,
            handoff_ack_observed=None,
        )
    )

    assert exit_code == 0
    assert report["bypass_receipt_id"] == receipt_id
    assert report["bypass_receipt_validated"] is True
    assert report["bridge_gate_bypassed"] is True
    assert report["bypass_scope"] == "launch_precondition_only"
    assert report["rejected_reason"] == ""


def test_valid_receipt_does_not_bypass_staging_commit_push_or_raw_git() -> None:
    decision = {
        "contract_id": "AgentLoopDecision",
        "source_snapshot_id": "snapshot-1",
        "may_mutate": False,
        "can_run_next_command": False,
    }
    attempted = build_attempted_action_receipt(
        action_kind="raw-git.push",
        command=(
            "python3 dev/scripts/devctl.py raw-git push guardir branch "
            "--bypass-receipt-id bypass:valid"
        ),
        mutates=True,
        writes_state=True,
        executes_command=True,
    ).to_dict()

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(attempted,),
    ).to_dict()

    assert report["ok"] is False
    assert {
        violation["reason"] for violation in report["violations"]
    } >= {
        "mutation_attempt_after_may_mutate_false",
        "command_attempt_after_can_run_next_command_false",
    }


def test_operator_authored_post_reaches_post_path_before_obedience_gate(
    tmp_path: Path,
) -> None:
    args = SimpleNamespace(
        action="post",
        kind="finding",
        from_agent="operator",
        to_agent="codex",
        role="operator",
        actor_role="operator",
        session_id="operator-session",
        control_decision_payload={
            "contract_id": "AgentLoopDecision",
            "source_snapshot_id": "snapshot-1",
            "actor_id": "codex",
            "actor_role": "reviewer",
            "session_id": "codex-session",
            "decision": "wait",
            "may_mutate": False,
            "can_run_next_command": False,
        },
    )
    context = EventActionContext(
        args=args,
        repo_root=tmp_path,
        review_channel_path=tmp_path / "dev/active/review_channel.md",
        artifact_paths=None,
        build_event_report_fn=None,
    )

    gate = _review_channel_lifecycle_gate(args=args, context=context)

    assert gate["ok"] is True
    assert gate["operator_source_authority"] is True
    assert gate["authority_ordering"] == (
        "operator_source_before_control_decision_obedience"
    )


def _orchestrator_post_args(*, kind: str, from_agent: str = "codex") -> SimpleNamespace:
    return SimpleNamespace(
        action="post",
        kind=kind,
        from_agent=from_agent,
        to_agent="claude",
        role="reviewer",
        actor_role="reviewer",
        session_id="codex-session",
        control_decision_payload={
            "contract_id": "AgentLoopDecision",
            "source_snapshot_id": "snapshot-orchestrator",
            "actor_id": "codex",
            "actor_role": "reviewer",
            "session_id": "codex-session",
            "decision": "wait",
            "may_mutate": False,
            "can_run_next_command": False,
        },
    )


def test_orchestrator_codex_task_started_reaches_post_path_before_obedience_gate(
    tmp_path: Path,
) -> None:
    """Codex orchestrator (TandemRole.REVIEWER) may post task_started without AgentLoopDecision (role-flip rev_pkt_4488)."""
    args = _orchestrator_post_args(kind="task_started")
    context = EventActionContext(
        args=args,
        repo_root=tmp_path,
        review_channel_path=tmp_path / "dev/active/review_channel.md",
        artifact_paths=None,
        build_event_report_fn=None,
    )

    gate = _review_channel_lifecycle_gate(args=args, context=context)

    assert gate["ok"] is True
    assert gate["orchestrator_source_authority"] is True
    assert gate["authority_ordering"] == (
        "orchestrator_source_before_control_decision_obedience"
    )


def test_orchestrator_codex_finding_reaches_post_path_before_obedience_gate(
    tmp_path: Path,
) -> None:
    """Codex orchestrator may post finding (evidence) without AgentLoopDecision."""
    args = _orchestrator_post_args(kind="finding")
    context = EventActionContext(
        args=args,
        repo_root=tmp_path,
        review_channel_path=tmp_path / "dev/active/review_channel.md",
        artifact_paths=None,
        build_event_report_fn=None,
    )

    gate = _review_channel_lifecycle_gate(args=args, context=context)

    assert gate["ok"] is True
    assert gate["orchestrator_source_authority"] is True


def test_non_orchestrator_claude_task_started_falls_through_to_obedience_gate(
    tmp_path: Path,
) -> None:
    """Non-orchestrator (claude) task_started without decision is NOT exempted - gate proceeds normally."""
    args = _orchestrator_post_args(kind="task_started", from_agent="claude")
    context = EventActionContext(
        args=args,
        repo_root=tmp_path,
        review_channel_path=tmp_path / "dev/active/review_channel.md",
        artifact_paths=None,
        build_event_report_fn=None,
    )

    gate = _review_channel_lifecycle_gate(args=args, context=context)

    # Falls through to ControlDecisionObeyedGuard - no orchestrator bypass
    assert "orchestrator_source_authority" not in gate or (
        gate.get("orchestrator_source_authority") is not True
    )


def test_orchestrator_authority_strict_scope_rejects_non_post_kinds(
    tmp_path: Path,
) -> None:
    """Codex/reviewer cannot use orchestrator authority for kinds outside {task_started, finding}.

    Anti-sprawl per rev_pkt_4488 directive: do NOT weaken VCS/edit gates.
    Strict scope is review-channel POST + only task_started/finding kinds.
    """
    args = _orchestrator_post_args(kind="task_produced")  # not in orchestrator-authorized kinds
    context = EventActionContext(
        args=args,
        repo_root=tmp_path,
        review_channel_path=tmp_path / "dev/active/review_channel.md",
        artifact_paths=None,
        build_event_report_fn=None,
    )

    gate = _review_channel_lifecycle_gate(args=args, context=context)

    # task_produced from codex is outside orchestrator scope - gate proceeds
    assert "orchestrator_source_authority" not in gate or (
        gate.get("orchestrator_source_authority") is not True
    )
