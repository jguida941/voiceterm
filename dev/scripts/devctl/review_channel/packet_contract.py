"""Shared review-packet contract helpers for event-backed review-channel flows."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from ..runtime.master_plan_contract import PlanProposal
from .event_store import (
    DEFAULT_PACKET_TTL_MINUTES,
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
)
from .packet_agents import default_packet_agent_ids
from .pending_packet_models import (
    PacketGuardBundleEvidenceFields,
    PacketRuntimeApprovalFields,
)
from .packet_attestation import PacketGuardAttestation
from .packet_plan_proposal import (
    PLANNING_PACKET_KINDS,
    PROPOSAL_PACKET_KINDS,
    PlanProposalPacketFields,
    carrier_packet_kinds,
    plan_proposal_for_fields,
    validate_plan_proposal_contract,
)
from .packet_route_scope import (
    normalize_packet_route_role,
    packet_route_matches_scope,
)
from .packet_target_validation import (
    STAGE_PIPELINE_ACTION_REQUEST_ACTIONS,
    VALID_PLAN_MUTATION_OPS,
    VALID_TARGET_KINDS,
    validate_target_fields,
)
from .packet_text_fields import (
    clean_optional_text as _clean_optional_text,
    normalize_anchor_ref_rows as _normalize_anchor_ref_rows,
)

VALID_AGENT_IDS = frozenset(default_packet_agent_ids())
COMMIT_APPROVAL_PACKET_KIND = "commit_approval"
ACTION_REQUEST_PACKET_KIND = "action_request"
VALID_PACKET_KINDS = {
    "finding",
    "question",
    "draft",
    "instruction",
    ACTION_REQUEST_PACKET_KIND,
    "approval_request",
    "decision",
    "system_notice",
    "plan_gap_review",
    "plan_patch_review",
    "plan_ready_gate",
    COMMIT_APPROVAL_PACKET_KIND,
}
CARRIER_PACKET_KINDS = carrier_packet_kinds(VALID_PACKET_KINDS)
VALID_POLICY_HINTS = {
    "review_only",
    "stage_draft",
    "operator_approval_required",
    "safe_auto_apply",
}


@dataclass(frozen=True, slots=True)
class PacketKindSchema:
    """Per-kind packet validation contract used by CLI and runtime callers."""

    kind: str
    summary_required: bool = True
    body_required: bool = True


PACKET_KIND_SCHEMAS = {
    kind: PacketKindSchema(kind=kind)
    for kind in VALID_PACKET_KINDS
}


@dataclass(frozen=True, slots=True)
class PacketTargetFields:
    """Typed plan/runtime target metadata carried by review packets.

    ``target_role`` and ``target_session_id`` are actor-route discriminators:
    they distinguish reviewer, implementer, architect, dashboard, watcher, and
    other role sessions that may run on any provider adapter. The legacy
    ``to_agent`` provider field remains delivery compatibility only; authority
    consumers fail closed unless scoped actor/session fields and capability
    grants match the intended route.
    """

    target_kind: str = ""
    target_ref: str = ""
    target_revision: str = ""
    anchor_refs: tuple[str, ...] = ()
    intake_ref: str = ""
    mutation_op: str = ""
    target_role: str = ""
    target_session_id: str = ""
    requested_session_visibility: str = ""

    @classmethod
    def from_values(
        cls,
        *,
        target_kind: object = None,
        target_ref: object = None,
        target_revision: object = None,
        anchor_refs: object = None,
        intake_ref: object = None,
        mutation_op: object = None,
        target_role: object = None,
        target_session_id: object = None,
        requested_session_visibility: object = None,
    ) -> "PacketTargetFields":
        return cls(
            target_kind=_clean_optional_text(target_kind) or "",
            target_ref=_clean_optional_text(target_ref) or "",
            target_revision=_clean_optional_text(target_revision) or "",
            anchor_refs=tuple(_normalize_anchor_ref_rows(anchor_refs)),
            intake_ref=_clean_optional_text(intake_ref) or "",
            mutation_op=_clean_optional_text(mutation_op) or "",
            target_role=_clean_optional_text(target_role) or "",
            target_session_id=_clean_optional_text(target_session_id) or "",
            requested_session_visibility=(
                _clean_optional_text(requested_session_visibility) or ""
            ),
        )

    def to_event_fields(self) -> dict[str, object]:
        fields: dict[str, object] = {}
        fields["target_kind"] = self.target_kind or None
        fields["target_ref"] = self.target_ref or None
        fields["target_revision"] = self.target_revision or None
        fields["anchor_refs"] = list(self.anchor_refs)
        fields["intake_ref"] = self.intake_ref or None
        fields["mutation_op"] = self.mutation_op or None
        fields["target_role"] = self.target_role or None
        fields["target_session_id"] = self.target_session_id or None
        fields["requested_session_visibility"] = (
            self.requested_session_visibility or None
        )
        return fields

    def has_values(self) -> bool:
        return any(
            (
                self.target_kind,
                self.target_ref,
                self.target_revision,
                self.anchor_refs,
                self.intake_ref,
                self.mutation_op,
                self.target_role,
                self.target_session_id,
                self.requested_session_visibility,
            )
        )


@dataclass(frozen=True, slots=True)
class PacketPostRequest:
    """Validated review-packet post request."""

    from_agent: str
    to_agent: str
    kind: str
    summary: str
    body: str
    evidence_refs: tuple[str, ...] = ()
    guidance_refs: tuple[str, ...] = ()
    context_pack_refs: tuple[dict[str, object], ...] = ()
    confidence: float = 1.0
    requested_action: str = "review_only"
    policy_hint: str = "review_only"
    approval_required: bool = False
    packet_id: str | None = None
    trace_id: str | None = None
    session_id: str = DEFAULT_REVIEW_CHANNEL_SESSION_ID
    plan_id: str = DEFAULT_REVIEW_CHANNEL_PLAN_ID
    controller_run_id: str | None = None
    expires_in_minutes: int = DEFAULT_PACKET_TTL_MINUTES
    target: PacketTargetFields = field(default_factory=PacketTargetFields)
    runtime_approval: PacketRuntimeApprovalFields = field(
        default_factory=PacketRuntimeApprovalFields
    )
    guard_bundle_evidence: PacketGuardBundleEvidenceFields = field(
        default_factory=PacketGuardBundleEvidenceFields
    )
    plan_proposal: PlanProposal = field(default_factory=PlanProposal)


@dataclass(frozen=True, slots=True)
class PacketTransitionRequest:
    """Validated review-packet transition request."""

    action: str
    packet_id: str
    actor: str
    session_id: str = DEFAULT_REVIEW_CHANNEL_SESSION_ID
    plan_id: str = DEFAULT_REVIEW_CHANNEL_PLAN_ID
    controller_run_id: str | None = None
    guard_attestation: PacketGuardAttestation | None = None


def validate_post_request(
    request: PacketPostRequest,
    *,
    valid_agent_ids: Iterable[str] | None = None,
    existing_packets: Iterable[Mapping[str, object]] | None = None,
) -> None:
    """Fail closed when one packet post request violates the contract."""
    allowed_agent_ids = _resolve_valid_agent_ids(valid_agent_ids)
    if request.from_agent not in allowed_agent_ids:
        raise ValueError(
            f"Unsupported review-channel from-agent: {request.from_agent}"
        )
    if request.to_agent not in allowed_agent_ids:
        raise ValueError(f"Unsupported review-channel to-agent: {request.to_agent}")
    if request.kind not in VALID_PACKET_KINDS:
        raise ValueError(f"Unsupported review-channel packet kind: {request.kind}")
    schema = packet_kind_schema(request.kind)
    if schema.summary_required and not request.summary.strip():
        raise ValueError("--summary is required for review-channel post.")
    if schema.body_required and not request.body.strip():
        raise ValueError("Review-channel post body is required.")
    if not 0.0 <= request.confidence <= 1.0:
        raise ValueError("--confidence must be between 0.0 and 1.0.")
    if request.policy_hint not in VALID_POLICY_HINTS:
        raise ValueError(
            f"Unsupported review-channel policy hint: {request.policy_hint}"
        )
    if request.expires_in_minutes <= 0:
        raise ValueError("--expires-in-minutes must be greater than zero.")
    validate_target_fields(
        kind=request.kind,
        requested_action=request.requested_action,
        target=request.target,
        runtime_approval=request.runtime_approval,
        guard_bundle_evidence=request.guard_bundle_evidence,
    )
    _validate_plan_proposal_fields(
        request=request,
        existing_packets=existing_packets,
    )


def packet_kind_schema(kind: str) -> PacketKindSchema:
    """Return the typed validation schema for one packet kind."""
    return PACKET_KIND_SCHEMAS[kind]


def plan_proposal_for_request(request: PacketPostRequest) -> PlanProposal:
    """Return explicit or compatibility-derived plan proposal metadata."""
    return plan_proposal_for_fields(
        PlanProposalPacketFields(
            kind=request.kind,
            requested_action=request.requested_action,
            target_kind=request.target.target_kind,
            target_ref=request.target.target_ref,
            target_revision=request.target.target_revision,
            anchor_refs=request.target.anchor_refs,
            mutation_op=request.target.mutation_op,
            explicit_proposal=request.plan_proposal,
        )
    )


def _validate_plan_proposal_fields(
    *,
    request: PacketPostRequest,
    existing_packets: Iterable[Mapping[str, object]] | None,
) -> None:
    proposal = plan_proposal_for_request(request)
    validate_plan_proposal_contract(
        kind=request.kind,
        proposal=proposal,
        carrier_kinds=CARRIER_PACKET_KINDS,
        existing_packets=existing_packets,
    )


def _resolve_valid_agent_ids(
    valid_agent_ids: Iterable[str] | None,
) -> set[str]:
    if valid_agent_ids is None:
        return set(VALID_AGENT_IDS)
    normalized = {
        str(agent_id).strip()
        for agent_id in valid_agent_ids
        if str(agent_id).strip()
    }
    return normalized or set(VALID_AGENT_IDS)
