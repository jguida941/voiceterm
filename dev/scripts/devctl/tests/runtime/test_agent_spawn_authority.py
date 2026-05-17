"""Tests for typed dead-peer spawn authority."""

from __future__ import annotations

from dev.scripts.devctl.runtime.agent_spawn_authority import (
    SpawnDeadAgentAction,
    compute_spawn_authority,
)
from dev.scripts.devctl.runtime.collaboration_wake_contract import LoopAutonomyState
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BypassAuthorityScope,
    BypassReceipt,
)


def _receipt(**overrides: object) -> BypassReceipt:
    values = {
        "receipt_id": "bypass:spawn:test",
        "reason": (
            "Operator authorized scoped peer resurrection while continuation "
            "anchor work remains live."
        ),
        "operator_signature": "operator",
        "ai_approval_evidence": "rev_pkt_3689",
        "requested_authority_scope": BypassAuthorityScope.AGENT_SPAWN_ONLY,
        "granted_at_utc": "2026-05-11T19:00:00Z",
        "granted_by_operator_actor_id": "operator",
    }
    values.update(overrides)
    return BypassReceipt(**values)


def _compute(**overrides: object) -> SpawnDeadAgentAction | None:
    values = {
        "target_actor_id": "codex",
        "target_role": "implementer",
        "agent_mind_cursor_age_seconds": 901,
        "continuation_anchor_live": True,
        "continuation_anchor_packet_id": "rev_pkt_3685",
        "bypass_receipt": _receipt(),
        "staleness_threshold_seconds": 900,
    }
    values.update(overrides)
    return compute_spawn_authority(**values)


def test_compute_spawn_authority_returns_action_when_all_gates_pass() -> None:
    action = _compute(
        loop_autonomy_state=LoopAutonomyState(
            loop_wake_mode="continuous",
            loop_driver_agent="claude",
            loop_autonomy_ok=True,
        )
    )

    assert action is not None
    assert action.target_actor_id == "codex"
    assert action.target_role == "implementer"
    assert action.bypass_receipt_id == "bypass:spawn:test"
    assert action.continuation_anchor_packet_id == "rev_pkt_3685"
    assert action.staleness_seconds == 901
    assert action.detected_at_utc.endswith("Z")
    assert "agent_mind_cursor_stale:901s" in action.reason
    assert "loop_autonomy:continuous/driver:claude" in action.reason


def test_compute_spawn_authority_allows_wider_edit_scope() -> None:
    action = _compute(
        bypass_receipt=_receipt(
            requested_authority_scope=BypassAuthorityScope.EDIT_ONLY
        )
    )

    assert action is not None
    assert action.bypass_receipt_id == "bypass:spawn:test"


def test_compute_spawn_authority_blocks_fresh_agent_mind_cursor() -> None:
    assert _compute(agent_mind_cursor_age_seconds=899) is None


def test_compute_spawn_authority_allows_threshold_boundary() -> None:
    assert _compute(agent_mind_cursor_age_seconds=900) is not None


def test_compute_spawn_authority_requires_live_continuation_anchor() -> None:
    assert _compute(continuation_anchor_live=False) is None
    assert _compute(continuation_anchor_packet_id="") is None


def test_compute_spawn_authority_requires_bypass_receipt() -> None:
    assert _compute(bypass_receipt=None) is None


def test_compute_spawn_authority_blocks_expired_bypass_receipt() -> None:
    assert (
        _compute(bypass_receipt=_receipt(expires_at_utc="2000-01-01T00:00:00Z"))
        is None
    )


def test_compute_spawn_authority_blocks_revoked_bypass_receipt() -> None:
    assert _compute(
        bypass_receipt=_receipt(revoked_at_utc="2026-05-11T19:30:00Z")
    ) is None


def test_compute_spawn_authority_blocks_when_loop_autonomy_is_not_green() -> None:
    assert (
        _compute(
            loop_autonomy_state=LoopAutonomyState(
                loop_wake_mode="manual_nudge_required",
                loop_driver_agent="claude",
                loop_autonomy_ok=False,
                loop_gap_summary="watcher requires manual nudge",
            )
        )
        is None
    )


def test_compute_spawn_authority_accepts_loop_autonomy_mapping() -> None:
    action = _compute(
        loop_autonomy_state={
            "loop_wake_mode": "tick_based",
            "loop_wake_interval_seconds": 30,
            "loop_driver_agent": "claude",
            "loop_autonomy_ok": True,
        }
    )

    assert action is not None
    assert "loop_autonomy:tick_based/driver:claude" in action.reason
