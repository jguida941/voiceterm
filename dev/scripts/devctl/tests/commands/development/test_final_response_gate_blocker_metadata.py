"""Phase 0.6.A v4.29 link 8 (rev_pkt_4696) final_response_gate blocker-metadata tests.

The final-response gate consumes AgentLoopDecision rows and produces a
FinalResponseGateResult that the /develop next emission path reads. This
slice ensures the 6 typed BlockerSnapshot fields survive into the gate result
AND that ``repair_command_runnable=False`` causes the gate to refuse emitting
the unrunnable command as ``next_required_command``.
"""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.commands.development.final_response_gate import (
    FinalResponseGateResult,
    _repair_command_runnable_from_field,
    enforce_final_response_gate,
)
from dev.scripts.devctl.commands.development.orchestration_models import (
    DevelopmentAgentLoopInput,
    DevelopmentContinuationRequiredSignal,
)


def _continuation_required() -> DevelopmentContinuationRequiredSignal:
    """Minimal continuation signal that forces the gate into the agent-loop block."""
    return DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        final_response_allowed=False,
        reasons=("agent_loop_decision_present",),
        required_packet_kind="",
        required_packet_command="",
        next_required_command="",
        user_action="",
        continuation_goal="",
        why_not_done="agent loop in flight",
        stop_policy="stop_only_when_typed_controller_closed",
        required_final_response_action="run_next_command",
        user_continue_state="must_continue",
    )


def _orchestration_with_decision(decision: DevelopmentAgentLoopInput) -> SimpleNamespace:
    return SimpleNamespace(agent_loop_decisions=(decision,))


def _decision_with_blocker(**overrides) -> DevelopmentAgentLoopInput:
    """Build a DevelopmentAgentLoopInput row that flows into the final gate."""
    base = {
        "actor_id": "claude",
        "actor_role": "implementer",
        "session_id": "s1",
        "lifecycle_state": "blocked",
        "required_action": "repair_startup_authority",
        "loop_mode": "typed_event_wait",
        "should_continue_loop": True,
        "safe_to_continue": False,
        "may_mutate": False,
        "proof_state": "satisfied",
        "blocker_owner": "claude",
        "blocker_target": "dev/scripts/devctl/runtime/startup_authority.py",
        "blocker_reason": "startup_authority_failed",
        "repair_command": (
            "python3 dev/scripts/devctl.py session "
            "--role observer --include-review-status always --format json"
        ),
        "stop_anchor": "",
        "repair_command_runnable": True,
    }
    base.update(overrides)
    return DevelopmentAgentLoopInput(**base)


def test_runnable_blocker_threads_six_typed_fields_into_gate_result() -> None:
    """Phase 0.6.A v4.29: a runnable blocker propagates all 6 typed fields."""
    decision = _decision_with_blocker()
    result = enforce_final_response_gate(
        _continuation_required(),
        orchestration=_orchestration_with_decision(decision),
    )
    assert result.allow_final_response is False
    assert result.blocker_owner == "claude"
    assert result.blocker_target == "dev/scripts/devctl/runtime/startup_authority.py"
    assert result.blocker_reason == "startup_authority_failed"
    assert "devctl.py session" in result.repair_command
    assert result.stop_anchor == ""
    assert result.repair_command_runnable is True


def test_unrunnable_blocker_refuses_to_emit_command_as_next_required() -> None:
    """v4.29 (rev_pkt_4696) critical axis: repair_command_runnable=False MUST
    NOT emit the upstream command as ``next_required_command`` - the gate
    must route to stop_anchor or operator override instead.

    Codex's directive: "If repair_command_runnable=False, final-response gate
    must not emit that command as runnable next_required_command; it must
    surface the typed blocker owner/target/reason and stop anchor or typed
    blocked packet path."
    """
    decision = _decision_with_blocker(
        blocker_owner="operator",
        blocker_target="MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1",
        blocker_reason="manual_repair_required",
        repair_command="see operator runbook section 4.2",
        stop_anchor="stop_anchor:operator_action_required",
        repair_command_runnable=False,
    )
    result = enforce_final_response_gate(
        _continuation_required(),
        orchestration=_orchestration_with_decision(decision),
    )
    assert result.allow_final_response is False
    # Critical refusal: next_required_command MUST NOT carry the unrunnable command
    assert "see operator runbook" not in result.next_required_command
    # Typed handoff fields preserved so consumers can route to operator/stop
    assert result.blocker_owner == "operator"
    assert (
        result.blocker_target
        == "MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1"
    )
    assert result.blocker_reason == "manual_repair_required"
    assert result.repair_command == "see operator runbook section 4.2"
    assert result.stop_anchor == "stop_anchor:operator_action_required"
    assert result.repair_command_runnable is False


def test_unrunnable_blocker_clears_next_required_command_to_empty() -> None:
    """v4.29: when runnable=False, the gate sets next_required_command="" so
    the agent loop's run-next-command path is unambiguously blocked."""
    decision = _decision_with_blocker(
        repair_command="some unrunnable command",
        repair_command_runnable=False,
        stop_anchor="stop_anchor:operator_required",
    )
    result = enforce_final_response_gate(
        _continuation_required(),
        orchestration=_orchestration_with_decision(decision),
    )
    # next_required_command should be empty (not the unrunnable command)
    assert result.next_required_command == ""


def test_runnable_blocker_keeps_next_required_command_populated() -> None:
    """v4.29 positive case (refreshed by v4.45.3): when the actor CAN run
    (can_run_next_command=True) and has a real next_command, the gate
    preserves it so the agent can execute the typed step.

    Pre-v4.45.3 this test asserted non-empty next_required_command even
    when the actor was blocked (can_run_next_command=False) — relying on
    the fabricated ``develop next`` default the fallback synthesized.
    Codex's rev_pkt_4739 directive ("blocked decisions should return
    empty unless the explicit scoped plan-override branch applies") made
    that synthesis incorrect. The test now sets can_run_next_command=True
    + a real next_command so the positive path is unambiguous.
    """
    decision = _decision_with_blocker(
        repair_command_runnable=True,
        can_run_next_command=True,
        next_command=(
            "python3 dev/scripts/devctl.py session --role observer "
            "--include-review-status always --format json"
        ),
    )
    result = enforce_final_response_gate(
        _continuation_required(),
        orchestration=_orchestration_with_decision(decision),
    )
    # next_required_command should be populated (not refused) — the
    # actor's runnable next_command propagates through the gate.
    assert result.next_required_command != ""


def test_legacy_decision_without_runnable_field_keeps_true_default() -> None:
    """v4.29: an AgentLoopDecision row from before the field existed defaults
    to repair_command_runnable=True - the gate must NOT silently flip legacy
    decisions to unrunnable territory via _truthy(None) == False."""
    # Build a SimpleNamespace lacking repair_command_runnable entirely
    decision = SimpleNamespace(
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
        lifecycle_state="blocked",
        required_action="repair_startup_authority",
        loop_mode="typed_event_wait",
        should_continue_loop=True,
        safe_to_continue=False,
        may_mutate=False,
        proof_state="satisfied",
        # Intentionally NO blocker_* or repair_command_runnable fields
    )
    result = enforce_final_response_gate(
        _continuation_required(),
        orchestration=_orchestration_with_decision(decision),
    )
    # The gate's default for runnable when the field is absent must be True
    assert result.repair_command_runnable is True


def test_repair_command_runnable_from_field_helper_preserves_defaults() -> None:
    """v4.29: the helper that reads repair_command_runnable from a decision
    preserves True for missing/None, applies _truthy for explicit values."""
    # Missing / None falls back to True
    assert _repair_command_runnable_from_field(SimpleNamespace()) is True
    assert (
        _repair_command_runnable_from_field(
            SimpleNamespace(repair_command_runnable=None)
        )
        is True
    )
    # Explicit boolean values pass through
    assert (
        _repair_command_runnable_from_field(
            SimpleNamespace(repair_command_runnable=True)
        )
        is True
    )
    assert (
        _repair_command_runnable_from_field(
            SimpleNamespace(repair_command_runnable=False)
        )
        is False
    )
    # String projections coerce via _truthy semantics
    assert (
        _repair_command_runnable_from_field(
            SimpleNamespace(repair_command_runnable="false")
        )
        is False
    )
    assert (
        _repair_command_runnable_from_field(
            SimpleNamespace(repair_command_runnable="0")
        )
        is False
    )
    assert (
        _repair_command_runnable_from_field(
            SimpleNamespace(repair_command_runnable="true")
        )
        is True
    )


def test_stop_anchor_surfaces_when_unrunnable_command_refused() -> None:
    """v4.29: when the gate refuses to emit an unrunnable command, the
    upstream stop_anchor surfaces on the result so consumers know the typed
    pause point."""
    decision = _decision_with_blocker(
        repair_command="some unrunnable command",
        repair_command_runnable=False,
        stop_anchor="stop_anchor:self_referential_loop:operator_required",
    )
    result = enforce_final_response_gate(
        _continuation_required(),
        orchestration=_orchestration_with_decision(decision),
    )
    assert result.stop_anchor == "stop_anchor:self_referential_loop:operator_required"
    assert result.next_required_command == ""  # explicit refusal


def test_final_response_gate_result_to_dict_includes_six_typed_fields() -> None:
    """v4.29: FinalResponseGateResult.to_dict() serializes the 6 new fields
    so downstream JSON consumers see them."""
    result = FinalResponseGateResult(
        blocker_owner="claude",
        blocker_target="dev/foo.py",
        blocker_reason="test_reason",
        repair_command="python3 test.py",
        stop_anchor="",
        repair_command_runnable=True,
    )
    payload = result.to_dict()
    assert payload["blocker_owner"] == "claude"
    assert payload["blocker_target"] == "dev/foo.py"
    assert payload["blocker_reason"] == "test_reason"
    assert payload["repair_command"] == "python3 test.py"
    assert payload["stop_anchor"] == ""
    assert payload["repair_command_runnable"] is True


def test_final_response_gate_result_defaults_keep_runnable_true() -> None:
    """v4.29: an empty FinalResponseGateResult defaults to runnable=True so
    legacy callers that don't set the field don't accidentally signal
    unrunnable."""
    result = FinalResponseGateResult()
    assert result.repair_command_runnable is True
    assert result.blocker_owner == ""
    assert result.repair_command == ""
    assert result.stop_anchor == ""


# ---------------------------------------------------------------------------
# v4.45.2 (rev_pkt_4737 / rev_pkt_4738) — gate must not emit next_loop_command
# ---------------------------------------------------------------------------


def test_v4_45_2_blocked_decision_with_empty_next_command_does_not_emit_loop_command() -> None:
    """v4.45.2 (rev_pkt_4737 / rev_pkt_4738 codex-dispatched task):

    When the upstream AgentLoopDecision has next_command="" (because
    can_run_next_command=False after the v4.45 fix), the
    agent_loop_next_required_command helper must NOT fall back to
    next_loop_command. The previous fallback chain
    ``next_command or next_loop_command or continuation.next_required_command``
    re-emitted the same agent-loop invocation as next_required_command,
    producing the end-to-end read-only self-loop codex reproduced via
    ``develop next --actor codex``.
    """
    decision = _decision_with_blocker(
        # The v4.45 fix: next_command is empty because actor is blocked
        # and cannot execute anything. next_loop_command remains populated
        # so the supervisor can identify the loop driver.
        next_command="",
        next_loop_command=(
            "python3 dev/scripts/devctl.py agent-loop --format json "
            "--actor codex --role reviewer --session-id codex-session"
        ),
        repair_command="",  # Empty repair: normalize to runnable=False
        repair_command_runnable=False,
    )
    result = enforce_final_response_gate(
        _continuation_required(),
        orchestration=_orchestration_with_decision(decision),
    )
    # Critical invariant: next_required_command MUST NOT be the agent-loop
    # self-loop. With repair_command empty + runnable=False, the gate
    # already clears next_required_command to "" via the v4.29 unrunnable
    # branch — v4.45.2 ensures that even if runnable were True, the
    # fallback no longer reaches next_loop_command.
    assert decision.next_loop_command != ""  # sanity: loop command exists
    assert result.next_required_command == ""


def test_v4_45_2_blocked_decision_with_runnable_owner_blocker_does_not_self_loop() -> None:
    """v4.45.2: the codex reviewer scenario codex's rev_pkt_4737 reproduced.

    Decision shape:
    - actor_id=codex, blocker_owner=claude (cross-owner blocker)
    - can_run_next_command=False (codex can't mutate)
    - safe_to_continue=False, may_mutate=False
    - next_command="" (v4.45 fix in effect)
    - repair_command="python3 dev/scripts/checks/check_startup_authority_contract.py --format md"
    - repair_command_runnable=True (repair IS runnable, by claude)

    Pre-v4.45.2: agent_loop_next_required_command fell back to
    next_loop_command since next_command="", producing
    next_required_command=agent-loop self-loop.

    Post-v4.45.2: fallback drops next_loop_command. With repair_command
    runnable, the typed blocker carries the actor handoff through the
    blocker_* fields; next_required_command emits the repair command (the
    typed handoff), NOT the agent-loop self-loop.
    """
    decision = _decision_with_blocker(
        actor_id="codex",
        actor_role="reviewer",
        blocker_owner="claude",
        blocker_target="dev/state/import_index.jsonl",
        blocker_reason="import_index_atomicity_violation",
        repair_command=(
            "python3 dev/scripts/checks/check_startup_authority_contract.py "
            "--format md"
        ),
        repair_command_runnable=True,
        next_command="",
        next_loop_command=(
            "python3 dev/scripts/devctl.py agent-loop --format json "
            "--actor codex --role reviewer --session-id codex-session"
        ),
    )
    result = enforce_final_response_gate(
        _continuation_required(),
        orchestration=_orchestration_with_decision(decision),
    )
    # The typed blocker fields propagate to the gate result
    assert result.blocker_owner == "claude"
    assert result.blocker_target == "dev/state/import_index.jsonl"
    assert result.blocker_reason == "import_index_atomicity_violation"
    assert "check_startup_authority_contract.py" in result.repair_command
    assert result.repair_command_runnable is True
    # The critical invariant: next_required_command MUST NOT be the
    # agent-loop self-loop. It is either the repair_command (typed
    # handoff) or empty, but never the loop command.
    assert "agent-loop" not in result.next_required_command, (
        f"next_required_command must not re-emit agent-loop self-loop; "
        f"got: {result.next_required_command!r}"
    )
    assert result.next_required_command != decision.next_loop_command


# ---------------------------------------------------------------------------
# v4.45.4 (rev_pkt_4742) — final-gate consumer must coerce string-bool
# ---------------------------------------------------------------------------


def test_v4_45_4_agent_loop_next_required_command_handles_string_false() -> None:
    """v4.45.4 (rev_pkt_4742 verbatim Codex repro): when the consumer
    receives a projection-shaped AgentLoopDecision with
    ``can_run_next_command="false"`` plus empty ``next_command`` and a
    populated ``next_loop_command``, ``agent_loop_next_required_command``
    must return empty — not the fabricated ``develop next`` default.
    Pre-v4.45.4 the consumer used ``bool(_field(...))`` which treats
    ``"false"`` as True, re-enabling the fallback fabrication.
    """
    from dev.scripts.devctl.commands.development.final_response_gate_agent_loop import (
        agent_loop_next_required_command,
    )

    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        final_response_allowed=False,
        reasons=("agent_loop_decision_present",),
        required_packet_kind="",
        required_packet_command="",
        next_required_command="",
        user_action="",
        continuation_goal="",
        why_not_done="agent loop in flight",
        stop_policy="stop_only_when_typed_controller_closed",
        required_final_response_action="run_next_command",
        user_continue_state="must_continue",
    )

    for projected_value in ("false", "0"):
        decision = SimpleNamespace(
            actor_id="codex",
            actor_role="reviewer",
            session_id="codex-session",
            can_run_next_command=projected_value,  # projection-shaped boolean
            next_command="",
            next_loop_command=(
                "python3 dev/scripts/devctl.py agent-loop --format json "
                "--actor codex --role reviewer --session-id codex-session"
            ),
            operator_override=SimpleNamespace(
                requested=False, active=False, edit_allowed=False,
            ),
            requested_plan_ref="",
            requested_packet_id="",
        )
        result = agent_loop_next_required_command(
            decision,
            continuation=continuation,
            required_action="repair_startup_authority",
            next_slice_id="",
        )
        assert result == "", (
            f"agent_loop_next_required_command with projected "
            f"can_run_next_command={projected_value!r} must return empty; "
            f"got: {result!r}"
        )


def test_v4_45_6_agent_loop_final_response_block_string_false_should_continue() -> None:
    """v4.45.6 (rev_pkt_4747 verbatim repro): when ``required_action="wait"``
    (non-blocking) and ``should_continue_loop`` is the projection string
    ``"false"``, the final-gate block must NOT fire — the typed signal says
    the loop is not continuing, so the gate should allow final response
    instead of forcing a wait block.

    Pre-v4.45.6 used raw ``bool("false") == True``, producing a block with
    ``reason=agent_loop:wait, action=run_next_command, next=""``. Post-v4.45.6
    uses shared coerce_bool which correctly treats ``"false"`` as False.
    """
    from dev.scripts.devctl.commands.development.final_response_gate import (
        _agent_loop_final_response_block,
    )

    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        reasons=(),
        required_packet_kind="",
        required_packet_command="",
        next_required_command="",
        user_action="",
        continuation_goal="",
        why_not_done="",
        stop_policy="stop_only_when_typed_controller_closed",
        required_final_response_action="allow_final_response",
        user_continue_state="may_complete",
    )
    decision = SimpleNamespace(
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
        required_action="wait",  # non-blocking
        should_continue_loop="false",  # projection string
        loop_mode="observer_wait",
        safe_to_continue=False,
        may_mutate=False,
        can_run_next_command=False,
        next_command="",
        next_loop_command="",
        blocker_owner="",
        blocker_target="",
        blocker_reason="",
        repair_command="",
        stop_anchor="",
        repair_command_runnable=False,
        operator_override=SimpleNamespace(
            requested=False, active=False, edit_allowed=False,
            scope="", target_kind="", target_ref="",
        ),
    )
    orchestration = SimpleNamespace(agent_loop_decisions=(decision,))
    result = _agent_loop_final_response_block(
        continuation,
        orchestration=orchestration,
        next_slice_id="",
    )
    # Non-blocking action + should_continue=False (post coerce_bool) → no block.
    assert result is None, (
        f"Final-gate block must not fire when required_action is non-blocking "
        f"AND should_continue_loop coerces to False; got: {result!r}"
    )


def test_v4_45_4_agent_loop_next_required_command_native_false_still_empty() -> None:
    """v4.45.4 defensive: Python False + 0 still yield empty (the
    behavior already worked pre-v4.45.4; this test pins it under the
    new shared-coerce_bool path)."""
    from dev.scripts.devctl.commands.development.final_response_gate_agent_loop import (
        agent_loop_next_required_command,
    )

    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        final_response_allowed=False,
        reasons=("agent_loop_decision_present",),
        required_packet_kind="",
        required_packet_command="",
        next_required_command="",
        user_action="",
        continuation_goal="",
        why_not_done="agent loop in flight",
        stop_policy="stop_only_when_typed_controller_closed",
        required_final_response_action="run_next_command",
        user_continue_state="must_continue",
    )

    for native_value in (False, 0):
        decision = SimpleNamespace(
            actor_id="codex",
            actor_role="reviewer",
            session_id="codex-session",
            can_run_next_command=native_value,
            next_command="",
            next_loop_command=(
                "python3 dev/scripts/devctl.py agent-loop --format json"
            ),
            operator_override=SimpleNamespace(
                requested=False, active=False, edit_allowed=False,
            ),
            requested_plan_ref="",
            requested_packet_id="",
        )
        result = agent_loop_next_required_command(
            decision,
            continuation=continuation,
            required_action="repair_startup_authority",
            next_slice_id="",
        )
        assert result == "", f"native {native_value!r} should yield empty; got {result!r}"
