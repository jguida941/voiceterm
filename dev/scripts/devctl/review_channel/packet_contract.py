"""Shared review-packet contract helpers for event-backed review-channel flows."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .event_store import (
    DEFAULT_PACKET_TTL_MINUTES,
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
)

VALID_AGENT_IDS = {"codex", "claude", "cursor", "operator", "system"}
VALID_PACKET_KINDS = {
    "finding",
    "question",
    "draft",
    "instruction",
    "action_request",
    "approval_request",
    "decision",
    "system_notice",
    "plan_gap_review",
    "plan_patch_review",
    "plan_ready_gate",
}
PLANNING_PACKET_KINDS = {
    "plan_gap_review",
    "plan_patch_review",
    "plan_ready_gate",
}
VALID_POLICY_HINTS = {
    "review_only",
    "stage_draft",
    "operator_approval_required",
    "safe_auto_apply",
}
VALID_TARGET_KINDS = {
    "artifact",
    "code",
    "plan",
    "policy",
    "runbook",
    "runtime",
}
VALID_PLAN_MUTATION_OPS = {
    "append_audit_evidence",
    "append_progress_log",
    "rewrite_section_note",
    "rewrite_session_resume",
    "set_checklist_state",
}
ANCHOR_REF_RE = re.compile(
    r"^(checklist|section|session_resume|progress|audit):[A-Za-z0-9][A-Za-z0-9._-]*$"
)


@dataclass(frozen=True, slots=True)
class PacketTargetFields:
    """Typed plan/policy/artifact target metadata carried by review packets."""

    target_kind: str = ""
    target_ref: str = ""
    target_revision: str = ""
    anchor_refs: tuple[str, ...] = ()
    intake_ref: str = ""
    mutation_op: str = ""

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
    ) -> "PacketTargetFields":
        return cls(
            target_kind=_clean_optional_text(target_kind) or "",
            target_ref=_clean_optional_text(target_ref) or "",
            target_revision=_clean_optional_text(target_revision) or "",
            anchor_refs=tuple(_normalize_string_rows(anchor_refs)),
            intake_ref=_clean_optional_text(intake_ref) or "",
            mutation_op=_clean_optional_text(mutation_op) or "",
        )

    def to_event_fields(self) -> dict[str, object]:
        fields: dict[str, object] = {}
        fields["target_kind"] = self.target_kind or None
        fields["target_ref"] = self.target_ref or None
        fields["target_revision"] = self.target_revision or None
        fields["anchor_refs"] = list(self.anchor_refs)
        fields["intake_ref"] = self.intake_ref or None
        fields["mutation_op"] = self.mutation_op or None
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


@dataclass(frozen=True, slots=True)
class PacketTransitionRequest:
    """Validated review-packet transition request."""

    action: str
    packet_id: str
    actor: str
    session_id: str = DEFAULT_REVIEW_CHANNEL_SESSION_ID
    plan_id: str = DEFAULT_REVIEW_CHANNEL_PLAN_ID
    controller_run_id: str | None = None


def validate_post_request(request: PacketPostRequest) -> None:
    """Fail closed when one packet post request violates the contract."""
    if request.from_agent not in VALID_AGENT_IDS:
        raise ValueError(
            f"Unsupported review-channel from-agent: {request.from_agent}"
        )
    if request.to_agent not in VALID_AGENT_IDS:
        raise ValueError(f"Unsupported review-channel to-agent: {request.to_agent}")
    if request.kind not in VALID_PACKET_KINDS:
        raise ValueError(f"Unsupported review-channel packet kind: {request.kind}")
    if not request.summary.strip():
        raise ValueError("--summary is required for review-channel post.")
    if not request.body.strip():
        raise ValueError("Review-channel post body is required.")
    if not 0.0 <= request.confidence <= 1.0:
        raise ValueError("--confidence must be between 0.0 and 1.0.")
    if request.policy_hint not in VALID_POLICY_HINTS:
        raise ValueError(
            f"Unsupported review-channel policy hint: {request.policy_hint}"
        )
    if request.expires_in_minutes <= 0:
        raise ValueError("--expires-in-minutes must be greater than zero.")
    _validate_target_fields(kind=request.kind, target=request.target)


def _validate_target_fields(
    *,
    kind: str,
    target: PacketTargetFields,
) -> None:
    if target.target_kind and target.target_kind not in VALID_TARGET_KINDS:
        raise ValueError(
            f"Unsupported review-channel target kind: {target.target_kind}"
        )
    planning_kind = kind in PLANNING_PACKET_KINDS
    if not planning_kind:
        if target.has_values():
            raise ValueError(
                "Planning packet fields are only allowed on plan review packet kinds."
            )
        return
    if target.target_kind != "plan":
        raise ValueError("Plan review packets must set --target-kind plan.")
    if not target.target_ref:
        raise ValueError("Plan review packets require --target-ref.")
    if not target.target_revision:
        raise ValueError("Plan review packets require --target-revision.")
    if not target.anchor_refs:
        raise ValueError("Plan review packets require at least one --anchor-ref.")
    invalid_anchor_refs = [
        anchor_ref
        for anchor_ref in target.anchor_refs
        if ANCHOR_REF_RE.fullmatch(anchor_ref) is None
    ]
    if invalid_anchor_refs:
        raise ValueError(
            "Invalid --anchor-ref value(s): " + ", ".join(invalid_anchor_refs)
        )
    if not target.intake_ref:
        raise ValueError("Plan review packets require --intake-ref.")
    if kind == "plan_patch_review":
        if target.mutation_op not in VALID_PLAN_MUTATION_OPS:
            raise ValueError(
                "Plan patch review packets require a valid --mutation-op."
            )
        return
    if target.mutation_op:
        raise ValueError("--mutation-op is only valid on `plan_patch_review` packets.")


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_string_rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    rows: list[str] = []
    for entry in value:
        text = str(entry).strip()
        if text:
            rows.append(text)
    return rows
