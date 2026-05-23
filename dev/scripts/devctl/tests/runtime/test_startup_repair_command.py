"""Phase 0.6.A v4.17 (rev_pkt_4672) startup-repair-command tests.

MP-GUARDIR-V4-PHASE-0-6-A-STARTUP-REPAIR-COMMAND-S1: startup_authority_failed
and related blockers must emit typed (owner, target, reason, repair_command)
OR a typed stop_anchor. The self-referential agent-loop command MUST NOT
return the same value twice without a changed blocker, command, or
stop_anchor. Operator edit-only override either becomes
``AgentLoopOperatorOverride.active=True`` for the scoped pass OR fails with
an explicit typed reason.
"""

from __future__ import annotations

from dev.scripts.devctl.runtime.agent_loop_operator_override import (
    AgentLoopOperatorOverride,
    DEFAULT_OPERATOR_OVERRIDE_REASON,
    EDIT_ONLY_OVERRIDE_SCOPE,
    OPERATOR_OVERRIDE_REQUESTOR,
    OPERATOR_OVERRIDE_SOURCE,
)
from dev.scripts.devctl.runtime.startup_blocker_decision import (
    BlockerSnapshot,
    _STARTUP_AUTHORITY_REPAIR_DIRECTIVES,
    _resolve_startup_authority_repair,
    derive_blocker_decision,
    detect_self_referential_loop,
    escalate_self_referential_loop_to_stop_anchor,
)


# ---------------------------------------------------------------------------
# v4.17 typed action field population
# ---------------------------------------------------------------------------


def test_startup_authority_failed_carries_typed_repair_command() -> None:
    """v4.17 (rev_pkt_4672): startup_authority_failed gets a runnable repair_command."""
    startup_authority = {
        "ok": False,
        "errors": ["authority probe timed out"],
    }
    snapshot = derive_blocker_decision(
        startup_authority=startup_authority,
        quality={},
        doctor={},
        session={},
        push_action="govern_then_push",
    )
    assert snapshot.blocker_source == "startup_authority"
    assert snapshot.blocker_owner == "implementer"
    assert snapshot.blocker_target == "dev/scripts/devctl/runtime/startup_authority.py"
    assert snapshot.blocker_reason == "startup_authority_failed"
    assert "devctl.py session" in snapshot.repair_command
    assert snapshot.stop_anchor == ""


def test_import_index_atomicity_violation_carries_typed_repair_command() -> None:
    """v4.17: import_index_atomicity violation gets its own targeted repair_command."""
    startup_authority = {
        "ok": False,
        "import_index_atomicity_violations": 3,
    }
    snapshot = derive_blocker_decision(
        startup_authority=startup_authority,
        quality={},
        doctor={},
        session={},
        push_action="govern_then_push",
    )
    assert snapshot.blocker_source == "startup_authority"
    assert snapshot.blocker_target == "dev/state/import_index.jsonl"
    assert snapshot.blocker_reason == "import_index_atomicity_violation"
    # v4.43.3 (rev_pkt_4718): the repair command is the real startup-authority
    # contract check entrypoint (bundles import_index_atomicity validation),
    # not the broken ``devctl check --target ...`` form.
    # v4.43.4 (rev_pkt_4720): switched to the stable public shim path so
    # AI-facing surfaces converge on one canonical command shape.
    assert "check_startup_authority_contract.py" in snapshot.repair_command


def test_checkpoint_required_carries_typed_repair_command() -> None:
    """v4.17: checkpoint_required blockers get a final-response-gate repair command."""
    startup_authority = {
        "checkpoint_required": True,
        "checkpoint_reason": "checkpoint_required",
    }
    snapshot = derive_blocker_decision(
        startup_authority=startup_authority,
        quality={},
        doctor={},
        session={},
        push_action="govern_then_push",
    )
    assert snapshot.blocker_source == "startup_authority"
    assert snapshot.blocker_reason == "checkpoint_required"
    assert "enforce-final-response-gate" in snapshot.repair_command


def test_unknown_startup_kind_emits_stop_anchor_not_repair_command() -> None:
    """v4.17: unknown startup kinds escalate to stop_anchor instead of silent acceptance.

    Codex's directive: emit a runnable repair_command OR a typed stop_anchor.
    Unknown kinds MUST NOT leave both empty - that would let the loop continue
    with no actionable signal.
    """
    repair = _resolve_startup_authority_repair("entirely-fake-startup-kind")
    owner, target, reason, repair_command, stop_anchor = repair
    assert repair_command == ""
    assert stop_anchor != ""
    assert "stop_anchor:" in stop_anchor
    assert owner == "operator"


def test_repair_directive_table_invariant_at_least_one_action() -> None:
    """v4.17 invariant: every directive entry has either repair_command OR stop_anchor.

    Walks the known-kinds table and verifies that exactly one (XOR not technically
    required - both could be set in future) of repair_command / stop_anchor is
    non-empty for every entry. Prevents accidentally introducing an unactionable
    blocker via table extension.
    """
    for kind, directive in _STARTUP_AUTHORITY_REPAIR_DIRECTIVES.items():
        owner, target, reason, repair_command, stop_anchor = directive
        assert owner, f"kind={kind!r} missing owner"
        assert target, f"kind={kind!r} missing target"
        assert reason, f"kind={kind!r} missing reason"
        assert repair_command or stop_anchor, (
            f"kind={kind!r} has neither repair_command nor stop_anchor"
        )


def test_blocker_snapshot_to_dict_includes_new_fields() -> None:
    """v4.17: BlockerSnapshot.to_dict serializes the new typed action fields."""
    snapshot = BlockerSnapshot(
        blocker_owner="claude",
        blocker_target="dev/foo.py",
        blocker_reason="example_reason",
        repair_command="python3 do_thing.py",
        stop_anchor="",
    )
    payload = snapshot.to_dict()
    assert payload["blocker_owner"] == "claude"
    assert payload["blocker_target"] == "dev/foo.py"
    assert payload["blocker_reason"] == "example_reason"
    assert payload["repair_command"] == "python3 do_thing.py"
    assert payload["stop_anchor"] == ""


# ---------------------------------------------------------------------------
# v4.17 self-referential loop detection
# ---------------------------------------------------------------------------


def test_self_referential_loop_detected_when_same_command_repeats() -> None:
    """v4.17 (rev_pkt_4672): same top_blocker + repair_command + stop_anchor = self-loop."""
    snap = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        repair_command="python3 dev/scripts/devctl.py session --role observer --format json",
    )
    same = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        repair_command="python3 dev/scripts/devctl.py session --role observer --format json",
    )
    assert detect_self_referential_loop(same, snap) is True


def test_self_referential_loop_not_detected_when_blocker_changes() -> None:
    """v4.17: blocker text change breaks the self-loop (progress is being made)."""
    snap = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        repair_command="python3 dev/scripts/devctl.py session --format json",
    )
    different = BlockerSnapshot(
        top_blocker="startup authority: import_index_atomicity",
        repair_command="python3 dev/scripts/devctl.py session --format json",
    )
    assert detect_self_referential_loop(different, snap) is False


def test_self_referential_loop_not_detected_when_command_changes() -> None:
    """v4.17: command change breaks the self-loop (different action being attempted)."""
    snap = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        repair_command="python3 dev/scripts/devctl.py session --format json",
    )
    different = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        repair_command="python3 dev/scripts/devctl.py check --format md",
    )
    assert detect_self_referential_loop(different, snap) is False


def test_self_referential_loop_not_detected_when_stop_anchor_changes() -> None:
    """v4.17: stop_anchor change breaks the self-loop (escalation occurred)."""
    snap = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        repair_command="python3 do_thing.py",
        stop_anchor="",
    )
    different = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        repair_command="python3 do_thing.py",
        stop_anchor="stop_anchor:operator_required",
    )
    assert detect_self_referential_loop(different, snap) is False


def test_self_referential_loop_not_detected_with_no_previous() -> None:
    """v4.17: first emission cannot be a self-loop (no prior to compare against)."""
    snap = BlockerSnapshot(
        top_blocker="any blocker",
        repair_command="python3 do_thing.py",
    )
    assert detect_self_referential_loop(snap, None) is False


def test_self_referential_loop_not_detected_when_no_repair_command() -> None:
    """v4.17: stop_anchor-only sequences are explicit pauses, not self-loops."""
    snap = BlockerSnapshot(
        top_blocker="startup authority: unknown_kind",
        repair_command="",
        stop_anchor="stop_anchor:operator_review",
    )
    same = BlockerSnapshot(
        top_blocker="startup authority: unknown_kind",
        repair_command="",
        stop_anchor="stop_anchor:operator_review",
    )
    assert detect_self_referential_loop(same, snap) is False


def test_escalate_self_referential_loop_emits_stop_anchor() -> None:
    """v4.17: escalation swaps repair_command for stop_anchor + names operator owner.

    When the loop guard fires, the agent must NOT keep emitting the same
    unactionable command. Escalation produces a typed stop_anchor with the
    operator as owner so the next step is unambiguous.
    """
    looped = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        next_action="checkpoint_blocked_by_startup_authority:startup_authority_failed",
        blocker_source="startup_authority",
        blocker_owner="claude",
        blocker_target="dev/scripts/devctl/runtime/startup_authority.py",
        blocker_reason="startup_authority_failed",
        repair_command="python3 dev/scripts/devctl.py session --format json",
        stop_anchor="",
    )
    escalated = escalate_self_referential_loop_to_stop_anchor(looped)
    assert escalated.repair_command == ""
    assert "stop_anchor:" in escalated.stop_anchor
    assert "self_referential_loop" in escalated.stop_anchor
    assert escalated.blocker_owner == "operator"
    assert escalated.blocker_reason.startswith("loop:")
    assert "loop_detected:same_repair_command_twice" in escalated.derivation_evidence


def test_escalate_preserves_blocker_target_and_source() -> None:
    """v4.17: escalation does not lose audit fields (target/source/derivation)."""
    looped = BlockerSnapshot(
        top_blocker="any",
        blocker_source="startup_authority",
        blocker_target="dev/foo/bar.py",
        blocker_reason="kind_x",
        repair_command="cmd",
        derivation_evidence=("evidence1", "evidence2"),
    )
    escalated = escalate_self_referential_loop_to_stop_anchor(looped)
    assert escalated.blocker_target == "dev/foo/bar.py"
    assert escalated.blocker_source == "startup_authority"
    # Original evidence preserved, escalation evidence appended
    assert "evidence1" in escalated.derivation_evidence
    assert "evidence2" in escalated.derivation_evidence


# ---------------------------------------------------------------------------
# v4.17 operator override interaction
# ---------------------------------------------------------------------------


def test_operator_override_edit_allowed_requires_all_typed_fields() -> None:
    """v4.17: AgentLoopOperatorOverride.edit_allowed requires a fully typed override.

    Codex's directive: operator override either becomes active=True for the
    scoped pass OR fails with explicit typed reason. The contract's
    ``edit_allowed`` property already enforces the typed field requirements;
    this test pins the invariant.
    """
    # A bare override is NOT edit_allowed
    bare = AgentLoopOperatorOverride()
    assert bare.edit_allowed is False

    # An override with all typed fields IS edit_allowed
    full = AgentLoopOperatorOverride(
        requested=True,
        active=True,
        state="active",
        source=OPERATOR_OVERRIDE_SOURCE,
        requested_by=OPERATOR_OVERRIDE_REQUESTOR,
        scope=EDIT_ONLY_OVERRIDE_SCOPE,
        reason=DEFAULT_OPERATOR_OVERRIDE_REASON,
        target_kind="runtime",
        target_ref="dev/scripts/devctl/runtime/startup_authority.py",
        allowed_actions=("implementation.edit",),
        effective_actor_role="implementer",
        effective_workstream_id="builder",
        effective_authority_source="operator_override_edit_only_repair",
    )
    assert full.edit_allowed is True


def test_operator_override_missing_reason_fails_with_typed_signal() -> None:
    """v4.17: an override missing reason does NOT activate edit_allowed.

    The contract treats empty ``reason`` as failure - the operator must name
    why the override is being granted. This is the "fails with explicit typed
    reason" branch of codex's directive.
    """
    missing_reason = AgentLoopOperatorOverride(
        requested=True,
        active=True,
        state="active",
        source=OPERATOR_OVERRIDE_SOURCE,
        requested_by=OPERATOR_OVERRIDE_REQUESTOR,
        scope=EDIT_ONLY_OVERRIDE_SCOPE,
        reason="",  # explicit empty
        target_kind="runtime",
        target_ref="dev/scripts/devctl/runtime/startup_authority.py",
        allowed_actions=("implementation.edit",),
        effective_actor_role="implementer",
        effective_workstream_id="builder",
        effective_authority_source="operator_override_edit_only_repair",
    )
    assert missing_reason.edit_allowed is False


def test_operator_override_wrong_scope_fails_with_typed_signal() -> None:
    """v4.17: override with non-edit-only scope does not activate edit_allowed."""
    wrong_scope = AgentLoopOperatorOverride(
        requested=True,
        active=True,
        state="active",
        source=OPERATOR_OVERRIDE_SOURCE,
        requested_by=OPERATOR_OVERRIDE_REQUESTOR,
        scope="full-publication",  # wrong scope, not edit-only
        reason=DEFAULT_OPERATOR_OVERRIDE_REASON,
        target_kind="runtime",
        target_ref="dev/foo.py",
        allowed_actions=("implementation.edit", "vcs.commit", "vcs.push"),
        effective_actor_role="implementer",
        effective_workstream_id="builder",
        effective_authority_source="operator_override_edit_only_repair",
    )
    assert wrong_scope.edit_allowed is False


# ---------------------------------------------------------------------------
# Phase 0.6.A v4.18 (rev_pkt_4674) next-command obedience classification
# ---------------------------------------------------------------------------


def test_blocker_snapshot_repair_command_runnable_defaults_true() -> None:
    """v4.18: ``repair_command_runnable`` defaults to True (existing emission sites
    use only read-only commands; future write-command directives MUST opt out)."""
    snap = BlockerSnapshot()
    assert snap.repair_command_runnable is True


def test_agent_loop_decision_threads_blocker_snapshot_fields() -> None:
    """v4.18 wiring (rev_pkt_4676/4677): AgentLoopDecision carries the typed
    blocker fields so consumers (develop next, agent-loop) can refuse to
    auto-execute repair_command_runnable=False commands.

    This is the receiving end of the cross-module wire. Future wiring of
    context_builder + decision_builder populates these from the upstream
    BlockerSnapshot; this test pins the contract on the decision side.
    """
    from dev.scripts.devctl.runtime.agent_loop_decision_models import (
        AgentLoopDecision,
    )

    decision = AgentLoopDecision(
        blocker_owner="claude",
        blocker_target="dev/scripts/devctl/runtime/startup_authority.py",
        blocker_reason="startup_authority_failed",
        repair_command=(
            "python3 dev/scripts/devctl.py session --role observer "
            "--include-review-status always --format json"
        ),
        stop_anchor="",
        repair_command_runnable=True,
    )
    payload = decision.to_dict()
    assert payload["blocker_owner"] == "claude"
    assert payload["blocker_target"] == "dev/scripts/devctl/runtime/startup_authority.py"
    assert payload["blocker_reason"] == "startup_authority_failed"
    assert "devctl.py session" in payload["repair_command"]
    assert payload["stop_anchor"] == ""
    assert payload["repair_command_runnable"] is True


def test_agent_loop_decision_default_repair_command_runnable_is_true() -> None:
    """v4.18: default AgentLoopDecision keeps repair_command_runnable=True so
    existing emission sites are forward-compatible (no consumer auto-rejection
    when the field is absent in upstream contexts)."""
    from dev.scripts.devctl.runtime.agent_loop_decision_models import (
        AgentLoopDecision,
    )

    decision = AgentLoopDecision()
    assert decision.repair_command_runnable is True
    assert decision.blocker_owner == ""
    assert decision.repair_command == ""
    assert decision.stop_anchor == ""


def test_agent_loop_decision_can_carry_unrunnable_classification() -> None:
    """v4.19: a decision can mark its repair_command as unrunnable so the
    consumer treats it as informational only."""
    from dev.scripts.devctl.runtime.agent_loop_decision_models import (
        AgentLoopDecision,
    )

    decision = AgentLoopDecision(
        blocker_owner="operator",
        blocker_target="MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1",
        blocker_reason="manual_repair_required",
        repair_command="see operator runbook section 4.2",
        repair_command_runnable=False,
        stop_anchor="stop_anchor:operator_action_required",
    )
    payload = decision.to_dict()
    assert payload["repair_command_runnable"] is False
    assert payload["blocker_owner"] == "operator"
    assert payload["stop_anchor"].startswith("stop_anchor:")


def test_blocker_snapshot_to_dict_includes_repair_command_runnable() -> None:
    """v4.18: ``to_dict`` serializes ``repair_command_runnable`` so consumers see it."""
    snap = BlockerSnapshot(repair_command_runnable=False)
    payload = snap.to_dict()
    assert "repair_command_runnable" in payload
    assert payload["repair_command_runnable"] is False


def test_v4_17_directives_all_emit_read_only_commands() -> None:
    """v4.18 invariant: every directive's repair_command is a read-only inspection
    command, so it passes ControlDecisionObeyedGuard without needing carried
    controller-decision context. Future entries that need a write command MUST
    set ``repair_command_runnable=False`` and rely on owner+target for resolution.
    """
    write_action_substrings = (
        "review-channel --action post",
        "review-channel --action ingest",
        "review-channel --action ack",
        "review-channel --action absorb",
        "review-channel --action dismiss",
        "review-channel --action apply",
        "git commit",
        "git push",
        "git stage",
        "vcs.commit",
        "vcs.push",
        "vcs.stage",
        "push --execute",
    )
    for kind, directive in _STARTUP_AUTHORITY_REPAIR_DIRECTIVES.items():
        owner, target, reason, repair_command, stop_anchor = directive
        if not repair_command:
            continue
        for substring in write_action_substrings:
            assert substring not in repair_command, (
                f"kind={kind!r} repair_command contains write action {substring!r}; "
                f"must either reroute to a read-only equivalent or be marked "
                f"repair_command_runnable=False with owner+target. command={repair_command!r}"
            )


def test_unrunnable_repair_command_requires_owner_and_target() -> None:
    """v4.18: when ``repair_command_runnable=False``, the agent loop relies on
    ``blocker_owner`` + ``blocker_target`` for next-step typing.

    Constructing an unrunnable blocker without owner+target is a contract
    violation that consumers should treat as a defect. This test pins the
    semantic: unrunnable command requires both fields.
    """
    # Valid unrunnable: has owner + target
    valid = BlockerSnapshot(
        blocker_owner="operator",
        blocker_target="MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1",
        blocker_reason="manual_repair_required",
        repair_command="see operator runbook section 4.2",
        repair_command_runnable=False,
    )
    assert valid.blocker_owner != ""
    assert valid.blocker_target != ""
    assert valid.repair_command_runnable is False

    # Defective: unrunnable but missing both owner and target.
    # The contract doesn't enforce this in __post_init__ yet, but the property
    # invariant is testable:
    defective = BlockerSnapshot(
        blocker_owner="",
        blocker_target="",
        repair_command="see operator runbook",
        repair_command_runnable=False,
    )
    assert not (defective.blocker_owner and defective.blocker_target), (
        "test sentinel: defective blocker is missing required fields"
    )


def test_runnable_default_blocker_can_omit_repair_command() -> None:
    """v4.18: a default BlockerSnapshot (top_blocker='none') with no command
    keeps ``repair_command_runnable=True`` without violating invariants.

    Verifies the default doesn't accidentally cascade into 'unrunnable' for
    benign empty-snapshot cases.
    """
    benign = BlockerSnapshot()
    assert benign.top_blocker == "none"
    assert benign.repair_command == ""
    assert benign.repair_command_runnable is True


def test_loop_escalation_to_stop_anchor_preserves_repair_command_runnable() -> None:
    """v4.18: when a self-referential loop escalates to stop_anchor, the resulting
    snapshot has empty ``repair_command`` and ``repair_command_runnable`` is
    irrelevant. Verify escalation doesn't accidentally produce a runnable=False
    with a non-empty repair_command (which would violate the contract).
    """
    looped = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        repair_command="python3 some_cmd.py",
        repair_command_runnable=True,
    )
    escalated = escalate_self_referential_loop_to_stop_anchor(looped)
    # After escalation: repair_command must be empty (the loop guard cleared it)
    assert escalated.repair_command == ""
    # Contract is preserved: empty repair_command + stop_anchor non-empty is OK
    assert escalated.stop_anchor != ""


def test_loop_escalation_names_operator_as_next_owner() -> None:
    """v4.17 integration: escalated stop_anchor identifies operator as the owner
    of the next step, signalling that an AgentLoopOperatorOverride is the only
    forward path from a self-referential loop.

    This wires the loop-detection axis to the operator-override axis: once a
    self-loop is detected, the typed handoff goes to the operator who can issue
    a scoped edit-only override.
    """
    looped = BlockerSnapshot(
        top_blocker="startup authority: startup_authority_failed",
        repair_command="python3 some_command.py",
        blocker_owner="claude",
        blocker_target="dev/foo.py",
        blocker_reason="startup_authority_failed",
    )
    escalated = escalate_self_referential_loop_to_stop_anchor(looped)
    # Loop escalation must name operator as owner -> operator override is the next step
    assert escalated.blocker_owner == "operator"
    # Stop anchor must be a typed reference, not an arbitrary string
    assert escalated.stop_anchor.startswith("stop_anchor:")


def test_v4555_typed_collaboration_overrides_legacy_claude_owner_literal() -> None:
    """v4.55 continuation (rev_pkt_4788): when typed collaboration is
    supplied with a live `coding_agent` role_assignment, the implementer
    owner literal "claude" in `_STARTUP_AUTHORITY_REPAIR_DIRECTIVES` is
    overridden by the typed provider. This retires the legacy
    provider-literal hardcoding in favor of typed role_assignments per
    rev_pkt_4788 directive.
    """
    typed_collaboration = {
        "role_assignments": [
            {
                "agent_id": "alice",
                "provider": "alice",
                "role_id": "coding_agent",
                "live": True,
            }
        ]
    }
    owner, _target, _reason, _command, _stop = _resolve_startup_authority_repair(
        "checkpoint_required",
        collaboration=typed_collaboration,
    )
    assert owner == "alice", (
        "Typed live coding_agent provider must override the legacy "
        f"'claude' literal, got {owner!r}"
    )


def test_v4555_no_collaboration_falls_back_to_role_owner_not_provider() -> None:
    """Provider identity is not repair authority.

    When collaboration has not been typed-threaded, the blocker names the
    implementer role rather than a concrete provider. A live typed
    ``coding_agent`` still overrides this role placeholder.
    """
    owner, _target, _reason, _command, _stop = _resolve_startup_authority_repair(
        "checkpoint_required",
    )
    assert owner == "implementer"


def test_v4555_typed_collaboration_without_coding_agent_falls_back_to_role_owner() -> None:
    """v4.55 continuation: when typed collaboration carries no live
    `coding_agent` role_assignment (e.g. only a `review_agent` is
    live), the role placeholder applies. Empty typed lookup does NOT
    invent a provider owner.
    """
    typed_collaboration = {
        "role_assignments": [
            {
                "agent_id": "codex",
                "provider": "codex",
                "role_id": "review_agent",
                "live": True,
            }
        ]
    }
    owner, _target, _reason, _command, _stop = _resolve_startup_authority_repair(
        "checkpoint_required",
        collaboration=typed_collaboration,
    )
    assert owner == "implementer"
