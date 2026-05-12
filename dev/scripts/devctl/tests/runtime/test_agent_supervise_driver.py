"""Tests for typed agent supervision decisions."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from dev.scripts.devctl.runtime.agent_supervise_driver import (
    AgentSuperviseInput,
    evaluate_agent_supervision,
)
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BypassAuthorityScope,
    BypassReceipt,
)


def _receipt(**overrides: object) -> BypassReceipt:
    values = {
        "receipt_id": "bypass:spawn:test",
        "reason": "Operator approved scoped supervise-driver spawn.",
        "operator_signature": "operator",
        "ai_approval_evidence": "rev_pkt_3685",
        "requested_authority_scope": BypassAuthorityScope.AGENT_SPAWN_ONLY,
        "granted_at_utc": "2026-05-12T00:00:00Z",
        "granted_by_operator_actor_id": "operator",
    }
    values.update(overrides)
    return BypassReceipt(**values)


def _review_state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "packets": [
            {
                "packet_id": "rev_pkt_anchor",
                "kind": "continuation_anchor",
                "to_agent": "codex",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "posted_at": "2026-05-12T00:00:00Z",
            }
        ],
        "collaboration": {
            "loop_autonomy_ok": True,
            "loop_wake_mode": "continuous",
            "loop_driver_agent": "claude",
        },
    }
    state.update(overrides)
    return state


def _session_file(tmp_path: Path, *, mtime_epoch: float) -> Path:
    session = tmp_path / "rollout-2026-05-12T01-00-00-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl"
    session.write_text("{}\n", encoding="utf-8")
    os.utime(session, (mtime_epoch, mtime_epoch))
    return session


def test_supervise_driver_authorizes_spawn_on_freeze_with_existing_gates(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 901)

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            pid=0,
            repo_root=tmp_path,
            review_state=_review_state(),
            bypass_receipt=_receipt(),
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    assert report.status == "spawn_authorized"
    assert report.freeze_detected is True
    assert report.process_exit_detected is False
    assert report.spawn_action is not None
    assert report.spawn_action.continuation_anchor_packet_id == "rev_pkt_anchor"
    assert "review-channel --action launch" in report.next_command


def test_supervise_driver_blocks_freeze_without_bypass_receipt(tmp_path: Path) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 901)

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            repo_root=tmp_path,
            review_state=_review_state(),
            bypass_receipt=None,
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    assert report.status == "blocked"
    assert report.freeze_detected is True
    assert "bypass_receipt_missing" in report.blocked_reasons
    assert report.spawn_action is None


def test_supervise_driver_authorizes_spawn_on_process_exit_without_waiting_for_mtime(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp())

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            pid=99_999_999,
            repo_root=tmp_path,
            review_state=_review_state(),
            bypass_receipt=_receipt(),
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    assert report.status == "spawn_authorized"
    assert report.process_exit_detected is True
    assert report.freeze_detected is False
    assert report.spawn_action is not None
    assert report.spawn_action.staleness_seconds == 900


def test_supervise_driver_healthy_when_no_exit_or_freeze(tmp_path: Path) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 30)

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            repo_root=tmp_path,
            review_state=_review_state(),
            bypass_receipt=_receipt(),
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    assert report.status == "healthy"
    assert report.trigger_reason == ""
    assert report.spawn_action is None
