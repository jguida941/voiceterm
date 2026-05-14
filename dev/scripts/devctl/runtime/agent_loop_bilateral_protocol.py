"""Seven-property bilateral protocol contract for agent-loop handoffs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final


CONTRACT_ID: Final = "AgentLoopBilateralProtocol"
SCHEMA_VERSION: Final = 1
MINIMUM_COMPOSABILITY_CONTRACTS: Final = 3

PROPERTY_CHAT_NOT_AUTHORITY: Final = "P1_CHAT_NOT_AUTHORITY"
PROPERTY_TYPED_ACTION_STATE: Final = "P2_TYPED_ACTION_STATE"
PROPERTY_TYPED_STOP_HANDOFF: Final = "P3_TYPED_STOP_HANDOFF"
PROPERTY_TYPED_RESUMABILITY: Final = "P4_TYPED_RESUMABILITY"
PROPERTY_PROJECTION_DISPLAY_ONLY: Final = "P5_PROJECTION_DISPLAY_ONLY"
PROPERTY_COMMANDS_CONSUME_EVIDENCE: Final = "P6_COMMANDS_CONSUME_EVIDENCE"
PROPERTY_RECEIPT_BINDING: Final = "P7_RECEIPT_BINDING"
PROPERTY_COMPOSABILITY_ANCHORS: Final = "P0_COMPOSABILITY_ANCHORS"

_CHAT_AUTHORITY_PREFIXES: Final = ("chat:", "memory:")
_PROJECTION_AUTHORITY_PREFIXES: Final = (
    "bridge:",
    "dashboard:",
    "generated-markdown:",
    "projection:",
)
_RECEIPT_BINDING_FIELDS: Final = (
    "repo_state_ref",
    "actor_ref",
    "guard_result_ref",
    "command_ref",
    "proof_ref",
)


@dataclass(frozen=True, slots=True)
class BilateralProtocolPropertyResult:
    property_id: str
    property_name: str
    satisfied: bool
    evidence_refs: tuple[str, ...] = ()
    violation_code: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AgentLoopBilateralProtocol:
    contract_id: str = CONTRACT_ID
    schema_version: int = SCHEMA_VERSION
    actor_id: str = ""
    peer_actor_id: str = ""
    plan_row_id: str = ""
    status: str = "violated"
    property_results: tuple[BilateralProtocolPropertyResult, ...] = ()
    failing_property_ids: tuple[str, ...] = ()
    composability_contracts: tuple[str, ...] = ()
    authority_refs: tuple[str, ...] = ()
    typed_action_refs: tuple[str, ...] = ()
    handoff_refs: tuple[str, ...] = ()
    resume_packet_refs: tuple[str, ...] = ()
    lane_resumption_refs: tuple[str, ...] = ()
    projection_refs: tuple[str, ...] = ()
    command_evidence_refs: tuple[str, ...] = ()
    receipt_refs: tuple[str, ...] = ()
    repo_state_ref: str = ""
    actor_ref: str = ""
    guard_result_ref: str = ""
    command_ref: str = ""
    proof_ref: str = ""
    summary: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "satisfied"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["ok"] = self.ok
        return payload


def build_agent_loop_bilateral_protocol(
    *,
    actor_id: str,
    peer_actor_id: str,
    plan_row_id: str,
    authority_refs: tuple[str, ...] = (),
    typed_action_refs: tuple[str, ...] = (),
    handoff_refs: tuple[str, ...] = (),
    resume_packet_refs: tuple[str, ...] = (),
    lane_resumption_refs: tuple[str, ...] = (),
    projection_refs: tuple[str, ...] = (),
    command_evidence_refs: tuple[str, ...] = (),
    receipt_refs: tuple[str, ...] = (),
    composability_contracts: tuple[str, ...] = (),
    repo_state_ref: str = "",
    actor_ref: str = "",
    guard_result_ref: str = "",
    command_ref: str = "",
    proof_ref: str = "",
) -> AgentLoopBilateralProtocol:
    """Build a protocol verdict over the seven operator-defined properties."""
    authority = _refs(authority_refs)
    typed_actions = _refs(typed_action_refs)
    handoffs = _refs(handoff_refs)
    resume_packets = _refs(resume_packet_refs)
    lane_refs = _refs(lane_resumption_refs)
    projections = _refs(projection_refs)
    command_evidence = _refs(command_evidence_refs)
    receipts = _refs(receipt_refs)
    contracts = _refs(composability_contracts)
    binding_refs = {
        "repo_state_ref": repo_state_ref.strip(),
        "actor_ref": actor_ref.strip(),
        "guard_result_ref": guard_result_ref.strip(),
        "command_ref": command_ref.strip(),
        "proof_ref": proof_ref.strip(),
    }

    results = (
        _property_result(
            property_id=PROPERTY_COMPOSABILITY_ANCHORS,
            property_name="composes with existing typed contracts",
            satisfied=len(contracts) >= MINIMUM_COMPOSABILITY_CONTRACTS,
            evidence_refs=contracts,
            violation_code="missing_composability_anchors",
            summary=(
                "bilateral protocol composes with at least three existing typed contracts"
            ),
        ),
        _property_result(
            property_id=PROPERTY_CHAT_NOT_AUTHORITY,
            property_name="agents cannot rely on chat as authority",
            satisfied=bool(authority)
            and not _contains_prefixed_ref(authority, _CHAT_AUTHORITY_PREFIXES),
            evidence_refs=authority,
            violation_code="chat_or_memory_authority",
            summary="authority refs are typed state, contracts, packets, or receipts",
        ),
        _property_result(
            property_id=PROPERTY_TYPED_ACTION_STATE,
            property_name="every serious action enters typed state",
            satisfied=bool(typed_actions),
            evidence_refs=typed_actions,
            violation_code="missing_typed_action_state",
            summary="serious action is backed by typed action or packet refs",
        ),
        _property_result(
            property_id=PROPERTY_TYPED_STOP_HANDOFF,
            property_name="every stop or handoff exits through typed state",
            satisfied=bool(handoffs),
            evidence_refs=handoffs,
            violation_code="missing_typed_handoff",
            summary="stop or handoff has continuation, stop, or lifecycle refs",
        ),
        _property_result(
            property_id=PROPERTY_TYPED_RESUMABILITY,
            property_name="later agents resume from typed packet state",
            satisfied=bool(resume_packets) and bool(lane_refs),
            evidence_refs=resume_packets + lane_refs,
            violation_code="missing_resumption_evidence",
            summary=(
                "resume packet evidence is paired with provider-neutral lane evidence"
            ),
        ),
        _property_result(
            property_id=PROPERTY_PROJECTION_DISPLAY_ONLY,
            property_name="generated projections are display-only",
            satisfied=not _contains_prefixed_ref(
                authority,
                _PROJECTION_AUTHORITY_PREFIXES,
            ),
            evidence_refs=authority + projections,
            violation_code="projection_used_as_authority",
            summary="projection refs are allowed only outside authority refs",
        ),
        _property_result(
            property_id=PROPERTY_COMMANDS_CONSUME_EVIDENCE,
            property_name="commands consume typed evidence before mutation",
            satisfied=bool(command_evidence),
            evidence_refs=command_evidence,
            violation_code="missing_command_evidence",
            summary="mutation command has typed evidence refs",
        ),
        _property_result(
            property_id=PROPERTY_RECEIPT_BINDING,
            property_name=(
                "receipts bind action to repo state, actor, guard result, "
                "command, and proof"
            ),
            satisfied=bool(receipts)
            and all(binding_refs[field] for field in _RECEIPT_BINDING_FIELDS),
            evidence_refs=receipts + tuple(binding_refs.values()),
            violation_code="incomplete_receipt_binding",
            summary="receipt evidence contains all required binding refs",
        ),
    )
    failing = tuple(result.property_id for result in results if not result.satisfied)
    status = "satisfied" if not failing else "violated"
    return AgentLoopBilateralProtocol(
        actor_id=actor_id.strip(),
        peer_actor_id=peer_actor_id.strip(),
        plan_row_id=plan_row_id.strip(),
        status=status,
        property_results=results,
        failing_property_ids=failing,
        composability_contracts=contracts,
        authority_refs=authority,
        typed_action_refs=typed_actions,
        handoff_refs=handoffs,
        resume_packet_refs=resume_packets,
        lane_resumption_refs=lane_refs,
        projection_refs=projections,
        command_evidence_refs=command_evidence,
        receipt_refs=receipts,
        repo_state_ref=binding_refs["repo_state_ref"],
        actor_ref=binding_refs["actor_ref"],
        guard_result_ref=binding_refs["guard_result_ref"],
        command_ref=binding_refs["command_ref"],
        proof_ref=binding_refs["proof_ref"],
        summary=(
            "all bilateral protocol properties satisfied"
            if not failing
            else "bilateral protocol properties violated: " + ", ".join(failing)
        ),
    )


def _property_result(
    *,
    property_id: str,
    property_name: str,
    satisfied: bool,
    evidence_refs: tuple[str, ...],
    violation_code: str,
    summary: str,
) -> BilateralProtocolPropertyResult:
    return BilateralProtocolPropertyResult(
        property_id=property_id,
        property_name=property_name,
        satisfied=satisfied,
        evidence_refs=evidence_refs,
        violation_code="" if satisfied else violation_code,
        summary=summary,
    )


def _refs(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(value.strip() for value in values if value.strip())


def _contains_prefixed_ref(refs: tuple[str, ...], prefixes: tuple[str, ...]) -> bool:
    return any(ref.startswith(prefix) for ref in refs for prefix in prefixes)


__all__ = [
    "AgentLoopBilateralProtocol",
    "BilateralProtocolPropertyResult",
    "CONTRACT_ID",
    "MINIMUM_COMPOSABILITY_CONTRACTS",
    "PROPERTY_CHAT_NOT_AUTHORITY",
    "PROPERTY_COMMANDS_CONSUME_EVIDENCE",
    "PROPERTY_COMPOSABILITY_ANCHORS",
    "PROPERTY_PROJECTION_DISPLAY_ONLY",
    "PROPERTY_RECEIPT_BINDING",
    "PROPERTY_TYPED_ACTION_STATE",
    "PROPERTY_TYPED_RESUMABILITY",
    "PROPERTY_TYPED_STOP_HANDOFF",
    "build_agent_loop_bilateral_protocol",
]
