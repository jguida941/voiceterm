"""Phase 0.6.A v4.23 link 7 (rev_pkt_4694) develop parser blocker-metadata tests.

The /develop parser converts AgentLoopDecision rows into DevelopmentAgentLoopInput.
This slice ensures the 6 typed BlockerSnapshot fields (blocker_owner,
blocker_target, blocker_reason, repair_command, stop_anchor,
repair_command_runnable) survive the conversion and that
``repair_command_runnable`` does NOT lose False values to Python's truthy-string
default (the ``bool("false") == True`` trap).
"""

from __future__ import annotations

from dev.scripts.devctl.commands.development.orchestration_agent_loop_parse import (
    _parse_repair_command_runnable,
    agent_loop_input,
)


def _base_row(**overrides) -> dict[str, object]:
    """Minimal valid AgentLoopDecision row for parser tests."""
    base = {
        "actor_id": "claude",
        "actor_role": "implementer",
        "session_id": "s1",
        "lifecycle_state": "idle",
        "required_action": "observe_typed_runtime",
        "loop_mode": "typed_event_wait",
        "should_continue_loop": True,
        "safe_to_continue": True,
        "may_mutate": False,
        "proof_state": "satisfied",
    }
    base.update(overrides)
    return base


def test_blocker_metadata_fields_default_when_absent() -> None:
    """Phase 0.6.A v4.23: missing fields fall back to typed dataclass defaults."""
    row = _base_row()
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.blocker_owner == ""
    assert parsed.blocker_target == ""
    assert parsed.blocker_reason == ""
    assert parsed.repair_command == ""
    assert parsed.stop_anchor == ""
    assert parsed.repair_command_runnable is True


def test_blocker_metadata_fields_thread_through_parser() -> None:
    """Phase 0.6.A v4.23: populated fields survive the parser into the contract."""
    row = _base_row(
        blocker_owner="claude",
        blocker_target="dev/scripts/devctl/runtime/startup_authority.py",
        blocker_reason="startup_authority_failed",
        repair_command=(
            "python3 dev/scripts/devctl.py session "
            "--role observer --include-review-status always --format json"
        ),
        stop_anchor="",
        repair_command_runnable=True,
    )
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.blocker_owner == "claude"
    assert (
        parsed.blocker_target
        == "dev/scripts/devctl/runtime/startup_authority.py"
    )
    assert parsed.blocker_reason == "startup_authority_failed"
    assert "devctl.py session" in parsed.repair_command
    assert parsed.stop_anchor == ""
    assert parsed.repair_command_runnable is True


def test_repair_command_runnable_false_survives_python_bool_value() -> None:
    """v4.23 rev_pkt_4694 critical axis: native False does NOT get coerced to True."""
    row = _base_row(repair_command_runnable=False)
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.repair_command_runnable is False


def test_repair_command_runnable_false_survives_string_false() -> None:
    """v4.23 rev_pkt_4694: string ``"false"`` from JSON projections must produce False.

    This is the exact trap codex called out: raw ``bool("false") == True`` in
    Python (non-empty string is truthy). coerce_bool treats "false" as False.
    """
    row = _base_row(repair_command_runnable="false")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.repair_command_runnable is False


def test_repair_command_runnable_false_survives_string_zero() -> None:
    """v4.23 rev_pkt_4694: string ``"0"`` from JSON projections must produce False."""
    row = _base_row(repair_command_runnable="0")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.repair_command_runnable is False


def test_repair_command_runnable_true_survives_string_true() -> None:
    """v4.23 rev_pkt_4694: string ``"true"`` produces True (positive case)."""
    for true_form in ("true", "True", "TRUE", "1", "yes", "on"):
        row = _base_row(repair_command_runnable=true_form)
        parsed = agent_loop_input(row)
        assert parsed is not None
        assert parsed.repair_command_runnable is True, (
            f"value={true_form!r} should produce True"
        )


def test_repair_command_runnable_missing_keeps_true_default() -> None:
    """v4.23 rev_pkt_4694: completely absent field falls back to the
    dataclass default (True), not False as raw ``bool(None)`` would give.
    """
    row = _base_row()  # no repair_command_runnable key at all
    assert "repair_command_runnable" not in row
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.repair_command_runnable is True


def test_repair_command_runnable_none_keeps_true_default() -> None:
    """v4.23: explicit None (e.g. JSON null) also falls back to default True."""
    row = _base_row(repair_command_runnable=None)
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.repair_command_runnable is True


def test_parse_repair_command_runnable_direct_unit_cases() -> None:
    """v4.23: direct unit tests on the helper for projection edge cases."""
    assert _parse_repair_command_runnable({}) is True
    assert _parse_repair_command_runnable({"repair_command_runnable": None}) is True
    assert _parse_repair_command_runnable({"repair_command_runnable": False}) is False
    assert _parse_repair_command_runnable({"repair_command_runnable": True}) is True
    assert _parse_repair_command_runnable({"repair_command_runnable": "false"}) is False
    assert _parse_repair_command_runnable({"repair_command_runnable": "0"}) is False
    assert _parse_repair_command_runnable({"repair_command_runnable": "no"}) is False
    assert _parse_repair_command_runnable({"repair_command_runnable": "off"}) is False
    assert _parse_repair_command_runnable({"repair_command_runnable": "FALSE"}) is False
    assert _parse_repair_command_runnable({"repair_command_runnable": "true"}) is True
    assert _parse_repair_command_runnable({"repair_command_runnable": "1"}) is True
    assert _parse_repair_command_runnable({"repair_command_runnable": "yes"}) is True
    assert _parse_repair_command_runnable({"repair_command_runnable": 0}) is False
    assert _parse_repair_command_runnable({"repair_command_runnable": 1}) is True


def test_unrunnable_blocker_round_trip_through_parser() -> None:
    """v4.23 integration: a complete unrunnable-blocker shape preserves all 6 fields
    with repair_command_runnable=False through the parser into the typed contract.

    This is codex's critical regression axis: the /develop next path must NOT
    silently drop the unrunnable classification when it pulls AgentLoopDecision
    rows from the dashboard projection.
    """
    row = _base_row(
        blocker_owner="operator",
        blocker_target="MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1",
        blocker_reason="manual_repair_required",
        repair_command="see operator runbook section 4.2",
        stop_anchor="stop_anchor:operator_action_required",
        repair_command_runnable="false",  # JSON-projection form
    )
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.blocker_owner == "operator"
    assert (
        parsed.blocker_target
        == "MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1"
    )
    assert parsed.blocker_reason == "manual_repair_required"
    assert parsed.repair_command == "see operator runbook section 4.2"
    assert parsed.stop_anchor == "stop_anchor:operator_action_required"
    assert parsed.repair_command_runnable is False


# ---------------------------------------------------------------------------
# v4.45.3 (rev_pkt_4739) — can_run_next_command must use coerce_bool
# ---------------------------------------------------------------------------


def test_v4_45_3_can_run_next_command_python_false_stays_false() -> None:
    """v4.45.3 (rev_pkt_4739): direct Python False passes through."""
    row = _base_row(can_run_next_command=False)
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.can_run_next_command is False


def test_v4_45_3_can_run_next_command_string_false_stays_false() -> None:
    """v4.45.3 (rev_pkt_4739 verbatim): projection ``"false"`` MUST parse as
    False. Codex's direct repro showed pre-v4.45.3 returned True because
    ``bool("false")`` is True in Python.
    """
    row = _base_row(can_run_next_command="false")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.can_run_next_command is False


def test_v4_45_3_can_run_next_command_string_zero_stays_false() -> None:
    """v4.45.3: projection ``"0"`` MUST parse as False."""
    row = _base_row(can_run_next_command="0")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.can_run_next_command is False


def test_v4_45_3_can_run_next_command_int_zero_stays_false() -> None:
    """v4.45.3: integer 0 MUST parse as False."""
    row = _base_row(can_run_next_command=0)
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.can_run_next_command is False


def test_v4_45_3_can_run_next_command_python_true_stays_true() -> None:
    """v4.45.3: direct Python True passes through (defensive)."""
    row = _base_row(can_run_next_command=True)
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.can_run_next_command is True


def test_v4_45_3_can_run_next_command_string_true_stays_true() -> None:
    """v4.45.3 defensive: projection ``"true"`` MUST parse as True."""
    row = _base_row(can_run_next_command="true")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.can_run_next_command is True


# ---------------------------------------------------------------------------
# v4.45.5 (rev_pkt_4743) — other boolean fields also use coerce_bool
# ---------------------------------------------------------------------------


def test_v4_45_5_may_mutate_string_false_stays_false() -> None:
    """v4.45.5: ``may_mutate="false"`` projection MUST parse as False.
    Codex's read-only audit caught this still raw-coerced after v4.45.3.
    """
    row = _base_row(may_mutate="false")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.may_mutate is False


def test_v4_45_5_safe_to_continue_string_false_stays_false() -> None:
    row = _base_row(safe_to_continue="false")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.safe_to_continue is False


def test_v4_45_5_advance_allowed_string_false_stays_false() -> None:
    row = _base_row(advance_allowed="false")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.advance_allowed is False


def test_v4_45_5_operator_override_active_string_false_stays_false() -> None:
    """v4.45.5: operator_override.active="false" projection MUST parse as False."""
    row = _base_row(operator_override={"active": "false"})
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.operator_override_active is False


def test_v4_45_5_should_continue_loop_string_false_stays_false() -> None:
    row = _base_row(should_continue_loop="false")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.should_continue_loop is False


def test_v4_45_5_new_peer_input_string_false_stays_false() -> None:
    row = _base_row(new_peer_input="false")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.new_peer_input is False


def test_v4_45_5_switch_to_packet_goal_string_false_stays_false() -> None:
    row = _base_row(switch_to_packet_goal="false")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.switch_to_packet_goal is False


def test_v4_45_5_continue_before_final_string_false_stays_false() -> None:
    row = _base_row(continue_before_final="false")
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.continue_before_final is False


def test_v4_45_6_operator_override_edit_allowed_string_false_active() -> None:
    """v4.45.6 (rev_pkt_4747 verbatim repro): when ``operator_override.active``
    is the projection string ``"false"``, ``_operator_override_edit_allowed``
    MUST return False. The helper previously used raw ``bool()`` which
    truthified ``"false"``, producing the contradictory shape
    ``operator_override_active=False`` (parsed correctly via coerce_bool at
    the top-level field) and ``operator_override_edit_allowed=True`` (wrong).
    """
    row = _base_row(operator_override={
        "active": "false",
        "scope": "edit-only",
        "allowed_actions": ["implementation.edit"],
        "blocked_actions": ["vcs.stage", "vcs.commit", "vcs.push"],
    })
    parsed = agent_loop_input(row)
    assert parsed is not None
    # Critical invariant: both fields agree the override is inactive.
    assert parsed.operator_override_active is False
    assert parsed.operator_override_edit_allowed is False


def test_v4_45_6_operator_override_edit_allowed_true_when_active_true() -> None:
    """v4.45.6 defensive: when ``active=True`` and all gate conditions
    are met, ``_operator_override_edit_allowed`` still returns True."""
    row = _base_row(operator_override={
        "active": True,
        "scope": "edit-only",
        "allowed_actions": ["implementation.edit"],
        "blocked_actions": ["vcs.stage", "vcs.commit", "vcs.push"],
    })
    parsed = agent_loop_input(row)
    assert parsed is not None
    assert parsed.operator_override_active is True
    assert parsed.operator_override_edit_allowed is True


def test_v4_45_5_agent_loop_signals_blocked_string_false_suppresses_all_commands() -> None:
    """v4.45.5 (rev_pkt_4743 #4 direct test): when can_run_next_command is
    the string ``"false"``, agent_loop_signals() must set
    closure_check_command, source_command, AND suggested_command to empty.
    """
    from dev.scripts.devctl.commands.development.orchestration_agent_loop import (
        agent_loop_signals,
    )

    row = agent_loop_input(_base_row(
        can_run_next_command="false",
        lifecycle_state="blocked",
        required_action="repair_startup_authority",
        next_command="",
        next_loop_command=(
            "python3 dev/scripts/devctl.py agent-loop --format json "
            "--actor codex --role reviewer --session-id codex-session"
        ),
    ))
    assert row is not None
    signals = agent_loop_signals((row,))
    assert len(signals) == 1
    signal = signals[0]
    assert signal.closure_check_command == "", (
        f"closure_check_command must be empty when blocked; "
        f"got: {signal.closure_check_command!r}"
    )
    assert signal.source_command == "", (
        f"source_command must be empty when blocked; "
        f"got: {signal.source_command!r}"
    )
    assert signal.suggested_command == "", (
        f"suggested_command must be empty when blocked; "
        f"got: {signal.suggested_command!r}"
    )
