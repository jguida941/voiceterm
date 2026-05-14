from __future__ import annotations

from dev.scripts.devctl.runtime.agent_loop_bilateral_protocol import (
    PROPERTY_CHAT_NOT_AUTHORITY,
    PROPERTY_COMMANDS_CONSUME_EVIDENCE,
    PROPERTY_COMPOSABILITY_ANCHORS,
    PROPERTY_PROJECTION_DISPLAY_ONLY,
    PROPERTY_RECEIPT_BINDING,
    PROPERTY_TYPED_ACTION_STATE,
    PROPERTY_TYPED_RESUMABILITY,
    PROPERTY_TYPED_STOP_HANDOFF,
    AgentLoopBilateralProtocol,
    BilateralProtocolPropertyResult,
    build_agent_loop_bilateral_protocol,
)


def test_bilateral_protocol_satisfies_all_properties() -> None:
    protocol = _valid_protocol()

    assert protocol.ok is True
    assert protocol.status == "satisfied"
    assert protocol.failing_property_ids == ()
    assert {result.property_id for result in protocol.property_results} == {
        PROPERTY_COMPOSABILITY_ANCHORS,
        PROPERTY_CHAT_NOT_AUTHORITY,
        PROPERTY_TYPED_ACTION_STATE,
        PROPERTY_TYPED_STOP_HANDOFF,
        PROPERTY_TYPED_RESUMABILITY,
        PROPERTY_PROJECTION_DISPLAY_ONLY,
        PROPERTY_COMMANDS_CONSUME_EVIDENCE,
        PROPERTY_RECEIPT_BINDING,
    }


def test_bilateral_protocol_rejects_chat_or_memory_authority_property_1() -> None:
    protocol = _valid_protocol(authority_refs=("chat:operator-paste",))

    result = _property(protocol, PROPERTY_CHAT_NOT_AUTHORITY)

    assert protocol.ok is False
    assert result.satisfied is False
    assert result.violation_code == "chat_or_memory_authority"


def test_bilateral_protocol_requires_typed_action_state_property_2() -> None:
    protocol = _valid_protocol(typed_action_refs=())

    result = _property(protocol, PROPERTY_TYPED_ACTION_STATE)

    assert result.satisfied is False
    assert result.violation_code == "missing_typed_action_state"


def test_bilateral_protocol_requires_typed_handoff_property_3() -> None:
    protocol = _valid_protocol(handoff_refs=())

    result = _property(protocol, PROPERTY_TYPED_STOP_HANDOFF)

    assert result.satisfied is False
    assert result.violation_code == "missing_typed_handoff"


def test_bilateral_protocol_requires_packet_and_lane_resumption_property_4() -> None:
    protocol = _valid_protocol(lane_resumption_refs=())

    result = _property(protocol, PROPERTY_TYPED_RESUMABILITY)

    assert result.satisfied is False
    assert result.violation_code == "missing_resumption_evidence"


def test_bilateral_protocol_rejects_projection_authority_property_5() -> None:
    protocol = _valid_protocol(authority_refs=("projection:bridge.md",))

    result = _property(protocol, PROPERTY_PROJECTION_DISPLAY_ONLY)

    assert result.satisfied is False
    assert result.violation_code == "projection_used_as_authority"


def test_bilateral_protocol_requires_command_evidence_property_6() -> None:
    protocol = _valid_protocol(command_evidence_refs=())

    result = _property(protocol, PROPERTY_COMMANDS_CONSUME_EVIDENCE)

    assert result.satisfied is False
    assert result.violation_code == "missing_command_evidence"


def test_bilateral_protocol_requires_complete_receipt_binding_property_7() -> None:
    protocol = _valid_protocol(guard_result_ref="")

    result = _property(protocol, PROPERTY_RECEIPT_BINDING)

    assert result.satisfied is False
    assert result.violation_code == "incomplete_receipt_binding"


def test_bilateral_protocol_requires_three_composability_contracts() -> None:
    protocol = _valid_protocol(composability_contracts=("AgentLoopDecision",))

    result = _property(protocol, PROPERTY_COMPOSABILITY_ANCHORS)

    assert result.satisfied is False
    assert result.violation_code == "missing_composability_anchors"


def _valid_protocol(
    *,
    authority_refs: tuple[str, ...] = ("contract:AgentLoopDecision",),
    typed_action_refs: tuple[str, ...] = ("typed_action:plan-work",),
    handoff_refs: tuple[str, ...] = ("packet:rev_pkt_stop_anchor",),
    resume_packet_refs: tuple[str, ...] = ("packet:rev_pkt_continuation_anchor",),
    lane_resumption_refs: tuple[str, ...] = (
        "contract:PeerSessionHandshakeEvidence",
        "contract:PeerHeartbeatEvidence",
    ),
    projection_refs: tuple[str, ...] = ("projection:AGENTS.md",),
    command_evidence_refs: tuple[str, ...] = ("run_record:check-router",),
    receipt_refs: tuple[str, ...] = ("validation_receipt:guard-bundle",),
    composability_contracts: tuple[str, ...] = (
        "AgentLoopDecision",
        "SessionTerminationPolicy",
        "PeerSessionHandshakeEvidence",
    ),
    repo_state_ref: str = "repo_state:HEAD",
    actor_ref: str = "actor:codex",
    guard_result_ref: str = "guard:docs-check",
    command_ref: str = "command:devctl check-router",
    proof_ref: str = "proof:review-channel",
) -> AgentLoopBilateralProtocol:
    return build_agent_loop_bilateral_protocol(
        actor_id="codex",
        peer_actor_id="claude",
        plan_row_id="MP377-AGENT-LOOP-BILATERAL-PROTOCOL-S1",
        authority_refs=authority_refs,
        typed_action_refs=typed_action_refs,
        handoff_refs=handoff_refs,
        resume_packet_refs=resume_packet_refs,
        lane_resumption_refs=lane_resumption_refs,
        projection_refs=projection_refs,
        command_evidence_refs=command_evidence_refs,
        receipt_refs=receipt_refs,
        composability_contracts=composability_contracts,
        repo_state_ref=repo_state_ref,
        actor_ref=actor_ref,
        guard_result_ref=guard_result_ref,
        command_ref=command_ref,
        proof_ref=proof_ref,
    )


def _property(
    protocol: AgentLoopBilateralProtocol,
    property_id: str,
) -> BilateralProtocolPropertyResult:
    return next(
        result
        for result in protocol.property_results
        if result.property_id == property_id
    )
