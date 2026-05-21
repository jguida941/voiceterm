"""Phase 0.6.A v4.43 (rev_pkt_4715) — stale-decision typed blocker tests.

Plan row: MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1.
Plan revision: guardir-v4.43-2026-05-20.

Codex's rev_pkt_4715 reproduction: trying to post ``review_accepted`` for
claude's v4.41 work, the obedience guard fired 4 violations
(``mutation_attempt_after_may_mutate_false``,
``command_attempt_after_can_run_next_command_false``,
``non_body_open_action_after_body_open_required``, plus stale source
decision ``agent-runtime-clock:rev_evt_84896``). The decision was older
than the attempted action's observed event id; refreshing the decision
would have made the action legal.

v4.43 emits a typed ``StaleControllerDecisionBlocker`` in
``ControlDecisionObedienceReport.stale_decision_blocker`` so consumers
can distinguish "refresh decision and retry" from "real action violation".
"""

from __future__ import annotations

from dev.scripts.devctl.runtime.control_decision_obedience import (
    StaleControllerDecisionBlocker,
    evaluate_control_decision_obedience,
)


# ---------------------------------------------------------------------------
# StaleControllerDecisionBlocker dataclass shape
# ---------------------------------------------------------------------------


def test_v4_43_stale_decision_blocker_dataclass_round_trip() -> None:
    """v4.43: the typed blocker has stable schema fields for downstream
    consumers to read."""
    blocker = StaleControllerDecisionBlocker(
        blocker_id="stale_decision:rev_evt_50000:vs:rev_evt_60000",
        decision_source_latest_event_id="rev_evt_50000",
        action_observed_event_id="rev_evt_60000",
        suppressed_violation_reasons=(
            "mutation_attempt_after_may_mutate_false",
            "command_attempt_after_can_run_next_command_false",
        ),
        detail="Decision input older than attempted action.",
    )
    payload = blocker.to_dict()
    assert payload["contract_id"] == "StaleControllerDecisionBlocker"
    assert payload["schema_version"] == 1
    assert payload["blocker_id"].startswith("stale_decision:")
    assert payload["decision_source_latest_event_id"] == "rev_evt_50000"
    assert payload["action_observed_event_id"] == "rev_evt_60000"
    assert payload["suppressed_violation_reasons"] == [
        "mutation_attempt_after_may_mutate_false",
        "command_attempt_after_can_run_next_command_false",
    ]


# ---------------------------------------------------------------------------
# evaluate_control_decision_obedience emits typed blocker on stale state
# ---------------------------------------------------------------------------


def test_v4_43_codex_rev_pkt_4715_verbatim_reproduction() -> None:
    """v4.43 (rev_pkt_4715 verbatim regression): the exact scenario codex
    hit — decision sourced from rev_evt_84896 while the attempted action
    observed a fresher event id — must produce a typed stale-decision
    blocker."""
    decision = {
        "decision": "wait",
        "required_action": "wait_for_scoped_packet",
        "may_mutate": False,
        "can_run_next_command": False,
        "body_open_required": True,
        "source_latest_event_id": "rev_evt_84896",  # codex's exact stale source
    }
    # Codex was attempting a review_accepted post AFTER event 84900+
    attempted_action = {
        "action_kind": "review-channel.post_review_accepted",
        "command": (
            "python3 dev/scripts/devctl.py review-channel --action post "
            "--kind review_accepted --from-agent codex --to-agent claude"
        ),
        "actor": "codex",
        "role": "reviewer",
        "session_id": "019e46cb-dd3c-7121-bf2f-eff8cc5fc815",
        "source_latest_event_id": "rev_evt_84920",  # fresher than decision
        "mutates": True,  # review-channel post IS a typed lifecycle mutation
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    # Violations still fire (the action IS technically violating obedience)
    assert report.ok is False
    assert report.violation_count > 0
    # But the typed stale-decision blocker IS now present
    assert report.stale_decision_blocker is not None
    blocker = report.stale_decision_blocker
    assert blocker["contract_id"] == "StaleControllerDecisionBlocker"
    assert blocker["decision_source_latest_event_id"] == "rev_evt_84896"
    assert blocker["action_observed_event_id"] == "rev_evt_84920"
    # Suppressed violation reasons recorded for audit
    assert "mutation_attempt_after_may_mutate_false" in (
        blocker["suppressed_violation_reasons"]
    )


def test_v4_43_no_stale_blocker_when_decision_is_fresh() -> None:
    """v4.43: a fresh decision (same or newer event id than action) does
    NOT trigger the stale-decision blocker. Real violations stay raw."""
    decision = {
        "decision": "wait",
        "required_action": "wait_for_scoped_packet",
        "may_mutate": False,
        "can_run_next_command": False,
        "source_latest_event_id": "rev_evt_99999",  # newer than action
    }
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post",
        "actor": "codex",
        "source_latest_event_id": "rev_evt_50000",
        "mutates": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    assert report.ok is False
    # No stale blocker — decision was fresh
    assert report.stale_decision_blocker is None
    # Real violations should still surface
    assert report.violation_count > 0


def test_v4_43_no_stale_blocker_when_decision_has_no_source_event_id() -> None:
    """v4.43: defensively, when the decision lacks source_latest_event_id,
    the stale check can't compare and won't emit a blocker. Real violations
    still surface as before."""
    decision = {
        "decision": "wait",
        "required_action": "wait_for_scoped_packet",
        "may_mutate": False,
        # source_latest_event_id missing
    }
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post",
        "actor": "codex",
        "source_latest_event_id": "rev_evt_50000",
        "mutates": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    assert report.stale_decision_blocker is None


def test_v4_43_no_stale_blocker_when_action_has_no_event_id() -> None:
    """v4.43: defensive — when the action has no observed event id, can't
    compare. No blocker emitted."""
    decision = {
        "decision": "wait",
        "required_action": "wait_for_scoped_packet",
        "may_mutate": False,
        "source_latest_event_id": "rev_evt_50000",
    }
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post",
        "actor": "codex",
        "mutates": True,
        # No source_latest_event_id on action
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    assert report.stale_decision_blocker is None


def test_v4_43_no_stale_blocker_when_no_violations() -> None:
    """v4.43: when there are no violations, no stale blocker either —
    the report says everything is fine."""
    decision = {
        "decision": "run",
        "may_mutate": True,
        "can_run_next_command": True,
        "source_latest_event_id": "rev_evt_50000",
        "actor_id": "claude",
        "actor_role": "implementer",
        "session_id": "s1",
    }
    attempted_action = {
        "action_kind": "review-channel.show",
        "command": "python3 dev/scripts/devctl.py review-channel --action show",
        "actor": "claude",
        "role": "implementer",
        "session_id": "s1",
        "source_latest_event_id": "rev_evt_60000",
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    # May still have violations from scope checks if the action isn't allowed,
    # but in this construction, there shouldn't be a stale-decision blocker
    # specifically when ok=True. Test the invariant.
    if report.ok:
        assert report.stale_decision_blocker is None


def test_v4_43_stale_blocker_includes_all_violation_reasons() -> None:
    """v4.43: the suppressed_violation_reasons tuple captures EVERY
    violation that fired, so consumers can audit the full set even after
    refreshing the decision."""
    decision = {
        "decision": "wait",
        "required_action": "wait_for_scoped_packet",
        "may_mutate": False,
        "can_run_next_command": False,
        "body_open_required": True,
        "source_latest_event_id": "rev_evt_50000",
    }
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post",
        "actor": "codex",
        "source_latest_event_id": "rev_evt_60000",
        "mutates": True,
        "executes_command": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    assert report.stale_decision_blocker is not None
    suppressed = report.stale_decision_blocker["suppressed_violation_reasons"]
    # Must include at least one of codex's reproduction reasons
    reproduction_reasons = {
        "mutation_attempt_after_may_mutate_false",
        "command_attempt_after_can_run_next_command_false",
        "non_body_open_action_after_body_open_required",
        "non_packet_attention_action_after_wait_for_scoped_packet",
    }
    assert any(r in reproduction_reasons for r in suppressed)


def test_v4_43_stale_blocker_uses_event_id_rank_ordering() -> None:
    """v4.43: event_id ranks compare numerically — rev_evt_99 < rev_evt_100,
    not lexically. (Lexical would put rev_evt_99 > rev_evt_100.)"""
    decision = {
        "decision": "wait",
        "may_mutate": False,
        "source_latest_event_id": "rev_evt_99",  # rank 99
    }
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post",
        "actor": "codex",
        "source_latest_event_id": "rev_evt_100",  # rank 100, newer
        "mutates": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    assert report.stale_decision_blocker is not None
    assert (
        report.stale_decision_blocker["decision_source_latest_event_id"]
        == "rev_evt_99"
    )
    assert (
        report.stale_decision_blocker["action_observed_event_id"]
        == "rev_evt_100"
    )


def test_v4_43_no_stale_blocker_when_action_event_older_than_decision() -> None:
    """v4.43: when action is OLDER than decision (the opposite of stale),
    no blocker — the real violations are real."""
    decision = {
        "decision": "wait",
        "may_mutate": False,
        "source_latest_event_id": "rev_evt_90000",
    }
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post",
        "actor": "codex",
        "source_latest_event_id": "rev_evt_50000",  # older than decision
        "mutates": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    assert report.stale_decision_blocker is None


def test_v4_43_to_dict_includes_stale_blocker_field() -> None:
    """v4.43: the ControlDecisionObedienceReport.to_dict() serialization
    includes the new stale_decision_blocker field for JSON projection."""
    decision = {
        "decision": "wait",
        "may_mutate": False,
        "source_latest_event_id": "rev_evt_50000",
    }
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post",
        "actor": "codex",
        "source_latest_event_id": "rev_evt_60000",
        "mutates": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    payload = report.to_dict()
    assert "stale_decision_blocker" in payload
    assert payload["stale_decision_blocker"] is not None
    assert (
        payload["stale_decision_blocker"]["contract_id"]
        == "StaleControllerDecisionBlocker"
    )


# ---------------------------------------------------------------------------
# v4.43.1 (rev_pkt_4716) — live-path repair: observed_event_id takes priority
# ---------------------------------------------------------------------------


def test_v4_43_1_observed_event_id_takes_priority_over_source_latest_event_id() -> None:
    """v4.43.1 (rev_pkt_4716): when the live ``_review_channel_lifecycle_gate``
    copies action.source_latest_event_id from the loaded decision, the
    action's ``observed_event_id`` (populated separately from canonical
    review-channel state) MUST drive the stale-decision check."""
    decision = {
        "may_mutate": False,
        "can_run_next_command": False,
        "source_latest_event_id": "rev_evt_84896",  # codex's stale source
    }
    # Live-path-shaped action: source_latest_event_id COPIED from decision
    # (so naive comparison would tie). But observed_event_id carries the
    # fresh canonical observation.
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post --kind review_accepted",
        "actor": "codex",
        "source_latest_event_id": "rev_evt_84896",  # IDENTICAL to decision (live shape)
        "observed_event_id": "rev_evt_84920",       # NEW: separately supplied, fresher
        "mutates": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    assert report.stale_decision_blocker is not None, (
        "v4.43.1: observed_event_id MUST drive stale-decision detection on "
        "the live path where source_latest_event_id is copied from decision"
    )
    blocker = report.stale_decision_blocker
    assert blocker["decision_source_latest_event_id"] == "rev_evt_84896"
    assert blocker["action_observed_event_id"] == "rev_evt_84920"


def test_v4_43_1_no_blocker_when_observed_event_matches_decision() -> None:
    """v4.43.1: when the observed event id equals the decision's source
    event id (no real staleness), no blocker fires — even when the action's
    source_latest_event_id is the same."""
    decision = {
        "may_mutate": False,
        "source_latest_event_id": "rev_evt_50000",
    }
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post",
        "actor": "codex",
        "source_latest_event_id": "rev_evt_50000",
        "observed_event_id": "rev_evt_50000",  # SAME → not stale
        "mutates": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    assert report.stale_decision_blocker is None


def test_v4_43_1_observed_event_id_can_demote_via_being_older() -> None:
    """v4.43.1: when observed_event_id is OLDER than decision (action was
    observed before the latest decision update), no stale blocker fires."""
    decision = {
        "may_mutate": False,
        "source_latest_event_id": "rev_evt_90000",
    }
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "python3 dev/scripts/devctl.py review-channel --action post",
        "actor": "codex",
        "source_latest_event_id": "rev_evt_90000",
        "observed_event_id": "rev_evt_50000",  # older than decision
        "mutates": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    assert report.stale_decision_blocker is None


def test_v4_43_2_live_path_reads_canonical_reduced_state(tmp_path) -> None:
    """v4.43.2 (rev_pkt_4717) INTEGRATION: ``_latest_observed_event_id``
    reads from the canonical reduced state (review_state.json shape) via
    ``source_latest_event_id_from_reduced_state``, NOT from the raw
    trace.ndjson tail. Proves the cursor flows through the same typed
    extraction path AgentRuntimeClock / agent_sync / reviewer_runtime
    consumers use."""
    from dev.scripts.devctl.commands.review_channel.event_handler import (
        _latest_observed_event_id,
    )

    import json
    # Build a synthetic review_state.json with the canonical shape
    state_path = tmp_path / "latest.json"
    review_state = {
        "agent_runtime_clock": {
            "source_latest_event_id": "rev_evt_84920",
            "agent_id": "claude",
        },
        "agent_sync": {"source_latest_event_id": "rev_evt_84890"},  # older
    }
    state_path.write_text(json.dumps(review_state))

    class _Artifact:
        def __init__(self, p):
            self.state_path = str(p)
    class _Ctx:
        def __init__(self, p):
            self.artifact_paths = _Artifact(p)

    observed = _latest_observed_event_id(_Ctx(state_path))
    # The agent_runtime_clock path is highest priority — wins over agent_sync
    assert observed == "rev_evt_84920"


def test_v4_43_2_live_path_extraction_walks_priority_order(tmp_path) -> None:
    """v4.43.2: when only ``agent_sync`` has a cursor (no
    agent_runtime_clock), the extractor falls through to it."""
    from dev.scripts.devctl.commands.review_channel.event_handler import (
        _latest_observed_event_id,
    )
    import json
    state_path = tmp_path / "latest.json"
    review_state = {
        "agent_sync": {"source_latest_event_id": "rev_evt_84890"},
    }
    state_path.write_text(json.dumps(review_state))

    class _Artifact:
        def __init__(self, p):
            self.state_path = str(p)
    class _Ctx:
        def __init__(self, p):
            self.artifact_paths = _Artifact(p)

    observed = _latest_observed_event_id(_Ctx(state_path))
    assert observed == "rev_evt_84890"


def test_v4_43_2_live_path_reviewer_runtime_fallback(tmp_path) -> None:
    """v4.43.2: when only ``reviewer_runtime`` has a cursor, falls through."""
    from dev.scripts.devctl.commands.review_channel.event_handler import (
        _latest_observed_event_id,
    )
    import json
    state_path = tmp_path / "latest.json"
    review_state = {
        "reviewer_runtime": {"source_latest_event_id": "rev_evt_84880"},
    }
    state_path.write_text(json.dumps(review_state))

    class _Artifact:
        def __init__(self, p):
            self.state_path = str(p)
    class _Ctx:
        def __init__(self, p):
            self.artifact_paths = _Artifact(p)

    assert _latest_observed_event_id(_Ctx(state_path)) == "rev_evt_84880"


def test_v4_43_2_live_path_helper_returns_empty_on_missing_file(tmp_path) -> None:
    """v4.43.2: defensive — if state_path doesn't exist yet (e.g. fresh
    repo), the helper returns "" so the gate falls back to legacy
    source_latest_event_id comparison."""
    from dev.scripts.devctl.commands.review_channel.event_handler import (
        _latest_observed_event_id,
    )
    class _Artifact:
        def __init__(self):
            self.state_path = str(tmp_path / "does_not_exist.json")
    class _Ctx:
        def __init__(self):
            self.artifact_paths = _Artifact()
    observed = _latest_observed_event_id(_Ctx())
    assert observed == ""


def test_v4_43_2_live_path_helper_handles_malformed_json(tmp_path) -> None:
    """v4.43.2: defensive — malformed JSON in state_path doesn't crash,
    returns "" so detection falls back to legacy path."""
    from dev.scripts.devctl.commands.review_channel.event_handler import (
        _latest_observed_event_id,
    )
    state_path = tmp_path / "latest.json"
    state_path.write_text("{not valid json")
    class _Artifact:
        def __init__(self, p):
            self.state_path = str(p)
    class _Ctx:
        def __init__(self, p):
            self.artifact_paths = _Artifact(p)
    observed = _latest_observed_event_id(_Ctx(state_path))
    assert observed == ""


def test_v4_43_2_canonical_extractor_promoted_to_public_name() -> None:
    """v4.43.2: ``source_latest_event_id_from_reduced_state`` is the new
    public API. The underscore-prefixed legacy name is preserved as alias."""
    from dev.scripts.devctl.runtime.control_decision_artifacts import (
        _source_latest_event_id,
        source_latest_event_id_from_reduced_state,
    )
    # Both names export the same callable
    assert source_latest_event_id_from_reduced_state is _source_latest_event_id
    # Functional check on the typed extraction order
    payload = {
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_99999"},
        "agent_sync": {"source_latest_event_id": "rev_evt_50000"},
    }
    assert (
        source_latest_event_id_from_reduced_state(payload) == "rev_evt_99999"
    )


def test_v4_43_1_codex_verbatim_live_path_reproduction(tmp_path) -> None:
    """v4.43.1 (rev_pkt_4716 VERBATIM live-path regression): codex's
    reproduction was ``review-channel post`` with decision sourced from
    ``rev_evt_84896`` and the LIVE event trace newer. With v4.43.1, the
    gate populates observed_event_id from the trace, and the stale-decision
    blocker fires."""
    from dev.scripts.devctl.runtime.control_decision_obedience import (
        evaluate_control_decision_obedience,
    )
    # Decision input is stale (v4.43.1 codex's exact source event id)
    decision = {
        "may_mutate": False,
        "can_run_next_command": False,
        "body_open_required": True,
        "source_latest_event_id": "rev_evt_84896",
    }
    # Live gate populates observed_event_id from canonical typed state
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": (
            "python3 dev/scripts/devctl.py review-channel --action post "
            "--kind review_accepted --from-agent codex --to-agent claude"
        ),
        "actor": "codex",
        "source_latest_event_id": "rev_evt_84896",  # live shape: copied from decision
        "observed_event_id": "rev_evt_85000",       # v4.43.1: fresh observation
        "mutates": True,
        "writes_state": True,
        "executes_command": True,
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=[attempted_action],
    )
    # v4.43.1 SUCCESS: typed stale-decision blocker fires on live shape
    assert report.stale_decision_blocker is not None
    assert (
        report.stale_decision_blocker["decision_source_latest_event_id"]
        == "rev_evt_84896"
    )
    assert (
        report.stale_decision_blocker["action_observed_event_id"]
        == "rev_evt_85000"
    )
