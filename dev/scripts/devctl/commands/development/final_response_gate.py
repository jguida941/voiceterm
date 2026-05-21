"""Typed final-response gate for the `/develop` controller."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .final_response_gate_agent_loop import (
    agent_loop_blocking_packet_id,
    agent_loop_next_required_command,
    edit_only_override_why_not_done,
    fallback_next_required_command,
    final_action_for_agent_loop,
    final_user_action_for_agent_loop,
    is_active_edit_only_override,
    prioritized_agent_loop_decisions,
)
from .orchestration_models import DevelopmentContinuationRequiredSignal
from ...runtime.bypass_lifecycle_models import BypassAuthorityScope
from ...runtime.bypass_receipt_active_lookup_gate import (
    BypassReceiptActiveLookupCheck,
    BypassReceiptActiveLookupFailureCode,
    require_active_bypass_receipt_for_override,
)
from ...runtime.ground_truth_probe_gate import (
    DEFAULT_MAX_RECEIPT_AGE_SECONDS,
    GroundTruthProbeReceiptCheck,
    GroundTruthProbeReceiptFailureCode,
    require_recent_ground_truth_receipt,
)
from ...runtime.typed_gate_failure import TypedGateFailure
from ...runtime.value_coercion import coerce_bool

FINAL_RESPONSE_GATE_CONTRACT_ID = "FinalResponseGateResult"
FINAL_RESPONSE_GATE_SCHEMA_VERSION = 1

_FINAL_BLOCKING_AGENT_ACTIONS = frozenset(
    {
        "open_packet_body",
        "post_continuation_anchor",
        "continue_from_continuation_anchor",
        "triage_pending_packet",
        "triage_packet",
        "run_next_command",
        "pivot_to_packet",
        "continue_to_goal",
    }
)


@dataclass(frozen=True, slots=True)
class FinalResponseGateResult:
    """Decision for whether an agent may emit a final response."""

    schema_version: int = FINAL_RESPONSE_GATE_SCHEMA_VERSION
    contract_id: str = FINAL_RESPONSE_GATE_CONTRACT_ID
    allow_final_response: bool = True
    action: str = "allow_final_response"
    reason: str = "typed_controller_closed"
    next_required_command: str = ""
    required_packet_kind: str = ""
    required_packet_command: str = ""
    blocking_packet_id: str = ""
    source: str = "continuation_signal"
    continuation_state: str = "may_stop"
    user_action: str = "Final response allowed"
    continuation_goal: str = ""
    why_not_done: str = ""
    stop_policy: str = "stop_only_when_typed_controller_closed"
    gate_failure: TypedGateFailure | None = None
    # Phase 0.6.A v4.29 chain wiring link 8 (rev_pkt_4696): preserve the six
    # typed BlockerSnapshot fields from the upstream AgentLoopDecision so the
    # final-response gate surfaces typed owner/target/reason and stop_anchor
    # instead of emitting an unrunnable command as ``next_required_command``.
    # When ``repair_command_runnable`` is False the gate MUST set
    # ``next_required_command`` to empty and route the agent to ``stop_anchor``
    # or operator action via the typed fields below.
    blocker_owner: str = ""
    blocker_target: str = ""
    blocker_reason: str = ""
    repair_command: str = ""
    stop_anchor: str = ""
    repair_command_runnable: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def enforce_final_response_gate(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    packet_attention: Any | None = None,
    orchestration: Any | None = None,
    next_slice_id: str = "",
    current_plan_row_id: str = "",
    repo_root: Path | None = None,
    ground_truth_expected_trigger_paths: Iterable[str] = (),
    ground_truth_max_age_seconds: int = DEFAULT_MAX_RECEIPT_AGE_SECONDS,
    now_utc: datetime | None = None,
) -> FinalResponseGateResult:
    """Return the typed gate result for final-response emission."""
    live_block = _live_final_response_block(
        continuation,
        packet_attention=packet_attention,
        orchestration=orchestration,
        next_slice_id=next_slice_id,
        current_plan_row_id=current_plan_row_id,
        repo_root=repo_root,
        ground_truth_expected_trigger_paths=ground_truth_expected_trigger_paths,
        ground_truth_max_age_seconds=ground_truth_max_age_seconds,
        now_utc=now_utc,
    )
    if live_block is not None:
        return live_block
    if continuation.final_response_allowed:
        return FinalResponseGateResult()
    return FinalResponseGateResult(
        allow_final_response=False,
        action=(
            continuation.required_final_response_action
            or "run_next_command"
        ),
        reason=continuation.reasons[0] if continuation.reasons else "continuation_required",
        next_required_command=fallback_next_required_command(
            continuation.next_required_command
        ),
        required_packet_kind=continuation.required_packet_kind,
        required_packet_command=continuation.required_packet_command,
        continuation_state=continuation.user_continue_state,
        user_action=continuation.user_action,
        continuation_goal=continuation.continuation_goal,
        why_not_done=continuation.why_not_done,
        stop_policy=continuation.stop_policy,
    )


def _live_final_response_block(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    packet_attention: Any | None,
    orchestration: Any | None,
    next_slice_id: str = "",
    current_plan_row_id: str = "",
    repo_root: Path | None = None,
    ground_truth_expected_trigger_paths: Iterable[str] = (),
    ground_truth_max_age_seconds: int = DEFAULT_MAX_RECEIPT_AGE_SECONDS,
    now_utc: datetime | None = None,
) -> FinalResponseGateResult | None:
    packet_block = _packet_attention_final_response_block(
        continuation,
        packet_attention=packet_attention,
        current_plan_row_id=current_plan_row_id,
        next_slice_id=next_slice_id,
    )
    if packet_block is not None:
        return packet_block
    agent_block = _agent_loop_final_response_block(
        continuation,
        orchestration=orchestration,
        next_slice_id=next_slice_id,
        current_plan_row_id=current_plan_row_id,
        repo_root=repo_root,
        now_utc=now_utc,
    )
    if agent_block is not None:
        return agent_block
    return _ground_truth_receipt_final_response_block(
        continuation,
        repo_root=repo_root,
        next_slice_id=next_slice_id,
        expected_trigger_paths=ground_truth_expected_trigger_paths,
        max_age_seconds=ground_truth_max_age_seconds,
        now_utc=now_utc,
    )


def _ground_truth_receipt_final_response_block(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    repo_root: Path | None,
    next_slice_id: str = "",
    expected_trigger_paths: Iterable[str] = (),
    max_age_seconds: int = DEFAULT_MAX_RECEIPT_AGE_SECONDS,
    now_utc: datetime | None = None,
) -> FinalResponseGateResult | None:
    if repo_root is None:
        return None
    check = require_recent_ground_truth_receipt(
        repo_root=repo_root,
        slice_id=next_slice_id,
        now_utc=now_utc,
        max_age_seconds=max_age_seconds,
        expected_trigger_paths=tuple(expected_trigger_paths),
    )
    if check.ok:
        return None
    failure_code = str(check.failure_code)
    reason = f"ground_truth_probe_receipt:{failure_code}"
    next_required_command = fallback_next_required_command(
        "python3 dev/scripts/devctl.py ground-truth-probe --record --format md"
    )
    gate_failure = TypedGateFailure(
        gate_id="ground_truth_probe_receipt.recent",
        violation_reason=reason,
        bypass_invocation=(
            "python3 dev/scripts/devctl.py bypass --action request "
            "--scope edit-only --reason ground_truth_probe_receipt_unavailable"
        ),
        bypass_receipt_kind="BypassReceipt",
        contract_definition_path=(
            "dev/scripts/devctl/runtime/ground_truth_probe_gate.py"
        ),
        exception_lifecycle_class="GovernedExceptionLifecycle",
    )
    return FinalResponseGateResult(
        allow_final_response=False,
        action="run_next_command",
        reason=reason,
        next_required_command=next_required_command,
        required_packet_kind=continuation.required_packet_kind,
        required_packet_command=continuation.required_packet_command,
        blocking_packet_id="",
        source="ground_truth_probe_receipt",
        continuation_state="must_continue",
        user_action=(
            "Record a recent GroundTruthProbeRunReceipt before final response."
        ),
        continuation_goal=next_slice_id or continuation.continuation_goal,
        why_not_done=_ground_truth_why_not_done(check),
        stop_policy=continuation.stop_policy,
        gate_failure=gate_failure,
    )


def _ground_truth_why_not_done(check: GroundTruthProbeReceiptCheck) -> str:
    code = check.failure_code
    if code == GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_RECEIPT_MISSING:
        return (
            "No GroundTruthProbeRunReceipt exists yet; record one before "
            "emitting a final response."
        )
    if code == GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_RECEIPT_STALE:
        return (
            "The latest GroundTruthProbeRunReceipt is stale "
            f"(age_seconds={check.age_seconds}); record a fresh one."
        )
    if code == GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_VERDICT_UNSATISFIED:
        verdict = check.receipt.verdict if check.receipt is not None else "missing"
        return (
            "The latest GroundTruthProbeRunReceipt verdict is "
            f"'{verdict}'; resolve the unsatisfied probes."
        )
    if code == GroundTruthProbeReceiptFailureCode.GROUND_TRUTH_PROBE_TRIGGER_MISMATCH:
        return (
            "The latest GroundTruthProbeRunReceipt trigger digest does not "
            "match the expected design surface; rerun the probe."
        )
    return "Ground-truth probe receipt is not satisfied."


def _packet_attention_final_response_block(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    packet_attention: Any | None,
    current_plan_row_id: str = "",
    next_slice_id: str = "",
) -> FinalResponseGateResult | None:
    if packet_attention is None:
        return None
    # v4.45.5 (rev_pkt_4743): shared coerce_bool so projected
    # ``attention_required="false"`` no longer ranks as True.
    attention_required = coerce_bool(_field(packet_attention, "attention_required"))
    pending_packet_count = _int(_field(packet_attention, "pending_packet_count"))
    # v4.45.5: migrated wake_required / pivot_required to shared coerce_bool.
    wake_required = coerce_bool(_field(packet_attention, "wake_required"))
    pivot_required = coerce_bool(_field(packet_attention, "pivot_required"))
    if not (
        attention_required
        or pending_packet_count > 0
        or wake_required
        or pivot_required
    ):
        return None
    wake_reason = _text(_field(packet_attention, "wake_reason"))
    attention_reason = _text(_field(packet_attention, "attention_reason"))
    reason = wake_reason or attention_reason or "packet_attention_required"
    continuation_goal = (
        current_plan_row_id
        or _non_packet_goal(next_slice_id)
        or _text(_field(packet_attention, "latest_attention_packet_id"))
    )
    return FinalResponseGateResult(
        allow_final_response=False,
        action="continue_to_goal",
        reason=f"packet_attention:{reason}",
        next_required_command=fallback_next_required_command(
            _text(_field(packet_attention, "required_command"))
            or continuation.next_required_command,
            actor=_text(_field(packet_attention, "agent")),
        ),
        required_packet_kind=continuation.required_packet_kind,
        required_packet_command=continuation.required_packet_command,
        blocking_packet_id=_text(
            _field(packet_attention, "latest_attention_packet_id")
        )
        if continuation_goal == _text(_field(packet_attention, "latest_attention_packet_id"))
        else "",
        source="packet_attention",
        continuation_state="must_continue",
        user_action="Continue to goal",
        continuation_goal=continuation_goal,
        why_not_done=(
            "A scoped packet requires attention before a final response is allowed."
        ),
        stop_policy=continuation.stop_policy,
    )


def _agent_loop_final_response_block(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    orchestration: Any | None,
    next_slice_id: str = "",
    current_plan_row_id: str = "",
    repo_root: Path | None = None,
    now_utc: datetime | None = None,
) -> FinalResponseGateResult | None:
    if orchestration is None:
        return None
    decisions = tuple(getattr(orchestration, "agent_loop_decisions", ()) or ())
    for agent_decision in prioritized_agent_loop_decisions(decisions):
        required_action = _text(_field(agent_decision, "required_action"))
        # v4.45.6 (rev_pkt_4747): shared coerce_bool so projection
        # ``should_continue_loop="false"`` short-circuits the final-gate
        # block for non-blocking actions. Pre-v4.45.6 the raw ``bool()``
        # truthified the string and forced a block even when the
        # required_action was non-blocking.
        should_continue = coerce_bool(
            _field(agent_decision, "should_continue_loop")
        )
        if (
            required_action not in _FINAL_BLOCKING_AGENT_ACTIONS
            and not should_continue
        ):
            continue
        if _stale_packet_agent_loop_decision(
            agent_decision,
            current_plan_row_id=current_plan_row_id,
            required_action=required_action,
        ):
            continue
        active_edit_override = is_active_edit_only_override(agent_decision)
        if active_edit_override:
            receipt_check = require_active_bypass_receipt_for_override(
                repo_root=repo_root,
                required_scope=BypassAuthorityScope.EDIT_ONLY,
                target_role=_text(_field(agent_decision, "target_role")),
                now_utc=now_utc,
            )
            if not receipt_check.ok:
                return _bypass_receipt_missing_final_response_block(
                    continuation,
                    check=receipt_check,
                    next_slice_id=next_slice_id,
                )
        action = (
            "continue_to_goal"
            if active_edit_override
            else final_action_for_agent_loop(required_action, continuation)
        )
        required_packet_kind = continuation.required_packet_kind
        if required_action == "post_continuation_anchor" and not required_packet_kind:
            required_packet_kind = "continuation_anchor"
        next_required_command = agent_loop_next_required_command(
            agent_decision,
            continuation=continuation,
            required_action=required_action,
            next_slice_id=next_slice_id,
        )
        # v4.29 link 8 (rev_pkt_4696): read typed BlockerSnapshot fields from
        # the AgentLoopDecision so the gate can surface owner/target/reason
        # plus stop_anchor instead of an unrunnable command. The
        # ``_repair_command_runnable_from_field`` helper preserves the True
        # default for legacy decisions that lack the field.
        blocker_owner_value = _text(_field(agent_decision, "blocker_owner"))
        blocker_target_value = _text(_field(agent_decision, "blocker_target"))
        blocker_reason_value = _text(_field(agent_decision, "blocker_reason"))
        repair_command_value = _text(_field(agent_decision, "repair_command"))
        stop_anchor_value = _text(_field(agent_decision, "stop_anchor"))
        runnable_value = _repair_command_runnable_from_field(agent_decision)
        if not runnable_value:
            # v4.29 unrunnable refusal: do NOT emit the upstream
            # repair_command as the gate's next_required_command. The agent
            # MUST route to ``stop_anchor`` or operator override; the
            # owner/target/reason fields stay populated so consumers can act
            # on the typed handoff.
            next_required_command = ""
        blocking_packet_id = agent_loop_blocking_packet_id(
            agent_decision,
            required_action=required_action,
            next_required_command=next_required_command,
        )
        reason = f"agent_loop:{required_action or 'continue_required'}"
        return FinalResponseGateResult(
            allow_final_response=False,
            action=action,
            reason=reason,
            next_required_command=next_required_command,
            blocker_owner=blocker_owner_value,
            blocker_target=blocker_target_value,
            blocker_reason=blocker_reason_value,
            repair_command=repair_command_value,
            stop_anchor=stop_anchor_value,
            repair_command_runnable=runnable_value,
            required_packet_kind=required_packet_kind,
            required_packet_command=continuation.required_packet_command,
            blocking_packet_id=blocking_packet_id,
            source="agent_loop_decision",
            continuation_state="must_continue",
            user_action=(
                "Continue scoped implementation edits"
                if active_edit_override
                else ""
            ) or (
                _text(_field(agent_decision, "user_action"))
                or final_user_action_for_agent_loop(required_action)
            ),
            continuation_goal=(
                current_plan_row_id
                or _non_packet_goal(next_slice_id)
                or _text(_field(agent_decision, "continuation_goal"))
                or blocking_packet_id
                or continuation.continuation_goal
            ),
            why_not_done=(
                edit_only_override_why_not_done(agent_decision)
                if active_edit_override
                else ""
            ) or (
                _text(_field(agent_decision, "why_not_done"))
                or continuation.why_not_done
                or "The agent loop still has a typed goal before final response."
            ),
            stop_policy=continuation.stop_policy,
            gate_failure=_gate_failure_for_agent_loop(
                agent_decision,
                required_action=required_action,
                reason=reason,
                next_required_command=next_required_command,
            ),
        )
    return None


def _bypass_receipt_missing_final_response_block(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    check: BypassReceiptActiveLookupCheck,
    next_slice_id: str = "",
) -> FinalResponseGateResult:
    """Refuse final response when override prose lacks an active BypassReceipt.

    Slice 5 of R313 A7 (T3): downgrades ``allow_final_response`` to False with
    a typed ``BYPASS_RECEIPT_NOT_PRESENT`` failure code so loose-flag override
    cannot escape the gate without typed authority.
    """

    failure_code = str(check.failure_code)
    reason = f"bypass_receipt_active_lookup:{failure_code}"
    next_required_command = fallback_next_required_command(
        "python3 dev/scripts/devctl.py bypass --action request "
        "--scope edit-only --reason operator_override_requires_active_receipt"
    )
    gate_failure = TypedGateFailure(
        gate_id="bypass_receipt_active_lookup.required",
        violation_reason=reason,
        bypass_invocation=next_required_command,
        bypass_receipt_kind="BypassReceipt",
        contract_definition_path=(
            "dev/scripts/devctl/runtime/bypass_receipt_active_lookup_gate.py"
        ),
        exception_lifecycle_class="BypassLifecycle",
    )
    return FinalResponseGateResult(
        allow_final_response=False,
        action="run_next_command",
        reason=reason,
        next_required_command=next_required_command,
        required_packet_kind=continuation.required_packet_kind,
        required_packet_command=continuation.required_packet_command,
        blocking_packet_id="",
        source="bypass_receipt_active_lookup",
        continuation_state="must_continue",
        user_action=(
            "Request an active BypassReceipt before honoring an edit-only "
            "operator override."
        ),
        continuation_goal=next_slice_id or continuation.continuation_goal,
        why_not_done=_bypass_receipt_why_not_done(check),
        stop_policy=continuation.stop_policy,
        gate_failure=gate_failure,
    )


def _bypass_receipt_why_not_done(check: BypassReceiptActiveLookupCheck) -> str:
    code = check.failure_code
    if code == BypassReceiptActiveLookupFailureCode.BYPASS_RECEIPT_NOT_PRESENT:
        return (
            "Override prose claims edit-only authority but no active BypassReceipt "
            "was found in the lifecycle store; request one before final response."
        )
    if code == BypassReceiptActiveLookupFailureCode.BYPASS_RECEIPT_EXPIRED:
        return (
            "The most recent BypassReceipt for the override scope is expired; "
            "request a fresh receipt."
        )
    if code == BypassReceiptActiveLookupFailureCode.BYPASS_RECEIPT_SCOPE_INSUFFICIENT:
        return (
            "The active BypassReceipt does not grant edit-only authority for "
            "this override claim."
        )
    return "BypassReceipt active-lookup check failed."


def _gate_failure_for_agent_loop(
    agent_decision: Any,
    *,
    required_action: str,
    reason: str,
    next_required_command: str,
) -> TypedGateFailure:
    existing = _field(agent_decision, "gate_failure")
    if isinstance(existing, Mapping):
        gate_id = _text(existing.get("gate_id")) or f"agent_loop.{required_action}"
        violation_reason = _text(existing.get("violation_reason")) or reason
        contract_path = _text(existing.get("contract_definition_path"))
        receipt_kind = _text(existing.get("bypass_receipt_kind")) or "BypassReceipt"
        lifecycle_class = (
            _text(existing.get("exception_lifecycle_class"))
            or "GovernedExceptionLifecycle"
        )
    else:
        gate_id = f"agent_loop.{required_action or 'continue_required'}"
        violation_reason = reason
        contract_path = "dev/scripts/devctl/commands/development/final_response_gate.py:95"
        receipt_kind = "BypassReceipt"
        lifecycle_class = "GovernedExceptionLifecycle"
    return TypedGateFailure(
        gate_id=gate_id,
        violation_reason=violation_reason,
        bypass_invocation=(
            next_required_command
            if "--operator-override" in next_required_command
            else ""
        ),
        bypass_receipt_kind=receipt_kind,
        contract_definition_path=contract_path,
        exception_lifecycle_class=lifecycle_class,
    )


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _field(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _non_packet_goal(value: str) -> str:
    text = _text(value)
    if not text:
        return ""
    blocked_prefixes = (
        "packet",
        "communication-packet",
        "runtime-attention",
        "checkpoint",
        "review-loop",
        "rev_pkt_",
    )
    if any(text.startswith(prefix) for prefix in blocked_prefixes):
        return ""
    return text


def _stale_packet_agent_loop_decision(
    agent_decision: Any,
    *,
    current_plan_row_id: str,
    required_action: str,
) -> bool:
    if not current_plan_row_id:
        return False
    packet_id = (
        _text(_field(agent_decision, "attention_packet_id"))
        or _text(_field(agent_decision, "active_packet_id"))
        or _text(_field(agent_decision, "legacy_unscoped_packet_id"))
    )
    plan_target_ref = _text(_field(agent_decision, "plan_target_ref"))
    if plan_target_ref in {current_plan_row_id, f"plan:{current_plan_row_id}"}:
        return False
    packet_actions = {
        "ingest_packet_semantics",
        "open_packet_body",
        "pivot_to_packet",
        "triage_packet",
        "triage_pending_packet",
    }
    return bool(packet_id or plan_target_ref) and required_action in packet_actions


# v4.45.5 (rev_pkt_4743): local ``_truthy`` retired in favor of shared
# ``runtime.value_coercion.coerce_bool`` (imported at module top). The
# previous local helper diverged on ``"y"`` (truthy treated as False;
# coerce_bool treats as True) — unintentional divergence per codex's
# audit. The shared normalizer is now the single canonical boolean
# coercion in this surface.


def _repair_command_runnable_from_field(agent_decision: Any) -> bool:
    """Return repair_command_runnable preserving the True default when absent.

    v4.29 link 8 (rev_pkt_4696): an AgentLoopDecision row that predates the
    typed-blocker fields produces ``_field(agent_decision, "repair_command_runnable")
    -> None``. ``_truthy(None)`` returns False, which would silently flip every
    legacy decision into unrunnable territory. Treat missing/None as True
    (the dataclass contract default) so only an EXPLICIT False/"false"/"0"
    from upstream disables runnable-command emission.
    """
    value = _field(agent_decision, "repair_command_runnable")
    if value is None:
        return True
    # v4.45.5 (rev_pkt_4743): use shared coerce_bool so the helper picks up
    # ``"y"`` as True (matches the rest of the bool boundary). Pre-v4.45.5
    # _truthy treated ``"y"`` as False — an unintentional divergence codex
    # called out for parity.
    return coerce_bool(value)


__all__ = [
    "FINAL_RESPONSE_GATE_CONTRACT_ID",
    "FINAL_RESPONSE_GATE_SCHEMA_VERSION",
    "FinalResponseGateResult",
    "enforce_final_response_gate",
]
