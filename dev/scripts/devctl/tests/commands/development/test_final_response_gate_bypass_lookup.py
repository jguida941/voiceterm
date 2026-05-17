"""BypassReceipt active-lookup gate over final_response_gate override prose.

Slice 5 of R313 A7 (T3): closes the Type-2 thin-proof hole where
``is_active_edit_only_override`` allowed continuation prose based on loose
``operator_override_*`` flags without verifying that an active ``BypassReceipt``
existed for the override scope. These tests pin the new contract that
``enforce_final_response_gate`` must AND-combine an active-receipt lookup into
``allow_final_response`` when override prose is present.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dev.scripts.devctl.commands.development.final_response_gate import (
    enforce_final_response_gate,
)
from dev.scripts.devctl.commands.development.orchestration_models import (
    DevelopmentAgentLoopInput,
    DevelopmentContinuationRequiredSignal,
    DevelopmentOrchestrationSnapshot,
)

UTC = timezone.utc


def _continuation_blocked() -> DevelopmentContinuationRequiredSignal:
    return DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        final_response_allowed=False,
        why_not_done="agent_loop_pending",
        reasons=("agent_loop_pending",),
    )


def _override_agent_decision() -> DevelopmentAgentLoopInput:
    return DevelopmentAgentLoopInput(
        actor_id="claude",
        actor_role="implementer",
        session_id="session_test",
        lifecycle_state="in_progress",
        required_action="continue_to_goal",
        loop_mode="operator_override_edit",
        should_continue_loop=True,
        safe_to_continue=True,
        may_mutate=False,
        proof_state="edit_only",
        operator_override_active=True,
        operator_override_edit_allowed=True,
        operator_override_scope="edit-only",
    )


def _orchestration_with(agent: DevelopmentAgentLoopInput) -> DevelopmentOrchestrationSnapshot:
    return DevelopmentOrchestrationSnapshot(
        signal_count=1,
        agent_loop_decisions=(agent,),
    )


def _write_active_bypass_lifecycle(
    repo_root: Path,
    *,
    expires_at_utc: str,
) -> None:
    store = repo_root / "dev" / "state" / "bypass_lifecycles.jsonl"
    store.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "lifecycle_id": "bypass_lc_001",
        "state": "bypass_active",
        "request": {
            "request_id": "req_001",
            "scope": "edit_only",
            "reason": "operator authorized edit-only repair",
            "actor": "operator",
            "requested_at_utc": "2026-05-17T00:00:00+00:00",
            "state": "bypass_active",
        },
        "evaluation": {
            "evaluation_id": "eval_001",
            "request_id": "req_001",
            "decision": "approved",
            "evaluated_at_utc": "2026-05-17T00:00:01+00:00",
            "evaluator_actor_id": "operator",
            "reason": "approved",
            "approved_scope": "edit_only",
        },
        "receipt": {
            "receipt_id": "rcpt_001",
            "reason": "operator approval",
            "operator_signature": "sig",
            "ai_approval_evidence": "evidence",
            "requested_authority_scope": "edit_only",
            "granted_at_utc": "2026-05-17T00:00:02+00:00",
            "granted_by_operator_actor_id": "operator",
            "state": "bypass_active",
            "expires_at_utc": expires_at_utc,
        },
    }
    store.write_text(json.dumps(row) + "\n", encoding="utf-8")


def test_override_with_active_receipt_does_not_emit_bypass_lookup_block(
    tmp_path: Path,
) -> None:
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    _write_active_bypass_lifecycle(tmp_path, expires_at_utc=future)
    result = enforce_final_response_gate(
        _continuation_blocked(),
        orchestration=_orchestration_with(_override_agent_decision()),
        repo_root=tmp_path,
    )
    # Active receipt present -> the bypass-lookup block must not be the source.
    assert result.source != "bypass_receipt_active_lookup"
    assert (
        result.gate_failure is None
        or result.gate_failure.gate_id != "bypass_receipt_active_lookup.required"
    )


def test_override_without_any_receipt_downgrades_allow_final_response(
    tmp_path: Path,
) -> None:
    # No bypass lifecycle store written -> no active receipt present.
    result = enforce_final_response_gate(
        _continuation_blocked(),
        orchestration=_orchestration_with(_override_agent_decision()),
        repo_root=tmp_path,
    )
    assert result.allow_final_response is False
    assert result.source == "bypass_receipt_active_lookup"
    assert result.reason == (
        "bypass_receipt_active_lookup:bypass_receipt_not_present"
    )
    assert result.gate_failure is not None
    assert result.gate_failure.gate_id == "bypass_receipt_active_lookup.required"
    assert result.gate_failure.bypass_receipt_kind == "BypassReceipt"
    assert "BypassReceipt" in result.why_not_done


def test_override_with_expired_receipt_fails_active_lookup(tmp_path: Path) -> None:
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    _write_active_bypass_lifecycle(tmp_path, expires_at_utc=past)
    result = enforce_final_response_gate(
        _continuation_blocked(),
        orchestration=_orchestration_with(_override_agent_decision()),
        repo_root=tmp_path,
    )
    # Expired receipt is not active -> falls through to BYPASS_RECEIPT_NOT_PRESENT.
    assert result.allow_final_response is False
    assert result.source == "bypass_receipt_active_lookup"
    assert result.reason.startswith("bypass_receipt_active_lookup:")
