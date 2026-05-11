"""Event-backed current-session builders."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .collaboration_provider import coding_provider_from_review_state
from .current_session_attention import (
    has_explicit_packet_truth,
    implementer_packet_attention_for,
    packet_attention_requires_clear,
)
from .current_session_checkpoint import reviewer_checkpoint_instruction_preservation
from .current_session_queue import queue_instruction_preserves_packet_truth_clear
from .current_session_support import (
    _canonicalize_instruction_state,
    compute_implementer_state_hash,
    event_agent_status,
    event_current_instruction,
    event_implementer_ack,
    event_open_findings,
    prior_typed_current_session,
)
from .handoff_constants import _is_substantive_text
from .session_state_hints import provider_session_state_hint
from .status_projection_helpers import clean_section
from ..runtime.review_state_models import ReviewCurrentSessionState
from ..runtime.review_state_semantics import (
    classify_implementer_ack_state,
    is_missing_instruction,
)


def event_current_session_candidate(
    *,
    review_state: Mapping[str, object] | None,
    bridge_liveness: Mapping[str, object],
) -> ReviewCurrentSessionState | None:
    resolved_review_state = _mapping(review_state)
    resolved_review_state = (
        _mapping(resolved_review_state.get("review_state")) or resolved_review_state
    )
    if not resolved_review_state:
        return None

    event_session = build_event_current_session(
        review_state=resolved_review_state,
        bridge_liveness=bridge_liveness,
        prior_review_state=resolved_review_state,
    )
    if not any(
        (
            clean_section(event_session.current_instruction),
            clean_section(event_session.implementer_status),
            clean_section(event_session.open_findings),
        )
    ):
        return None
    return event_session


def event_session_has_active_instruction(
    event_session: ReviewCurrentSessionState | None,
) -> bool:
    if event_session is None:
        return False
    return not is_missing_instruction(event_session.current_instruction) and bool(
        event_session.current_instruction_revision
    )


def event_session_clears_packet_truth(
    *,
    review_state: Mapping[str, object] | None,
    event_session: ReviewCurrentSessionState | None,
) -> bool:
    if event_session is None or event_session_has_active_instruction(event_session):
        return False
    resolved_review_state = _mapping(review_state)
    resolved_review_state = (
        _mapping(resolved_review_state.get("review_state")) or resolved_review_state
    )
    if not has_explicit_packet_truth(resolved_review_state):
        return False
    return packet_attention_requires_clear(
        implementer_packet_attention_for(resolved_review_state)
    )


def build_event_current_session(
    *,
    review_state: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    prior_review_state: Mapping[str, object] | None = None,
) -> ReviewCurrentSessionState:
    """Build typed current-session state from event-backed review state."""
    prior_session = prior_typed_current_session(prior_review_state)
    implementer_provider = coding_provider_from_review_state(review_state)
    checkpoint_instruction = reviewer_checkpoint_instruction_preservation(review_state)
    current_instruction = event_current_instruction(review_state)
    packet_attention = implementer_packet_attention_for(review_state)
    clear_from_packet_truth = (
        packet_attention_requires_clear(packet_attention)
        and not queue_instruction_preserves_packet_truth_clear(
            review_state,
            current_instruction=current_instruction,
        )
    )
    current_instruction_revision = str(
        bridge_liveness.get("current_instruction_revision") or ""
    )
    reused_prior_instruction = False
    if (
        not current_instruction
        and prior_session is not None
        and not clear_from_packet_truth
    ):
        current_instruction = prior_session.current_instruction
        reused_prior_instruction = True
        current_instruction_revision = (
            prior_session.current_instruction_revision or current_instruction_revision
        )
    current_instruction, current_instruction_revision = _canonicalize_instruction_state(
        current_instruction,
        current_instruction_revision,
    )
    if clear_from_packet_truth and not queue_instruction_preserves_packet_truth_clear(
        review_state,
        current_instruction=current_instruction,
    ):
        preserved = reviewer_checkpoint_instruction_preservation(review_state)
        if preserved is not None:
            current_instruction, current_instruction_revision = preserved
        else:
            current_instruction = ""
            current_instruction_revision = ""
    instruction_missing = is_missing_instruction(current_instruction)
    if (
        instruction_missing
        and current_instruction == "(missing)"
        and (
            prior_session is None
            or packet_attention_requires_clear(packet_attention)
        )
    ):
        current_instruction = ""
        current_instruction_revision = ""
    live_instruction_present = (
        not is_missing_instruction(current_instruction)
        and bool(current_instruction_revision)
    )
    implementer_ack = (
        event_implementer_ack(review_state) if live_instruction_present else ""
    )
    implementer_ack_revision = (
        str(
            bridge_liveness.get("implementer_ack_revision")
            or bridge_liveness.get("claude_ack_revision")
            or ""
        )
        if live_instruction_present
        else ""
    )
    ack_current = (
        bool(
            bridge_liveness.get("implementer_ack_current")
            or bridge_liveness.get("claude_ack_current")
        )
        if live_instruction_present
        else False
    )
    implementer_status = event_agent_status(review_state, implementer_provider)
    implementer_hint = provider_session_state_hint(
        dict(bridge_liveness),
        provider=implementer_provider,
    )
    open_findings = event_open_findings(review_state)
    last_reviewed_scope = str(
        _mapping(review_state.get("review")).get("plan_id") or ""
    )
    if reused_prior_instruction and prior_session is not None:
        if not str(implementer_status or "").strip():
            implementer_status = prior_session.implementer_status
        if open_findings == "none" and prior_session.open_findings:
            open_findings = prior_session.open_findings
        last_reviewed_scope = last_reviewed_scope or prior_session.last_reviewed_scope
    if checkpoint_instruction is not None and current_instruction == checkpoint_instruction[0]:
        if not str(implementer_status or "").strip():
            implementer_status = "- pending"
        if not str(implementer_ack or "").strip():
            bridge_ack = _bridge_liveness_implementer_ack(bridge_liveness)
            if ack_current and bridge_ack:
                implementer_ack = bridge_ack
            else:
                implementer_ack = "- pending"
                implementer_ack_revision = ""
                ack_current = False
    return ReviewCurrentSessionState(
        current_instruction=current_instruction,
        current_instruction_revision=current_instruction_revision,
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_revision=implementer_ack_revision,
        implementer_ack_state=classify_implementer_ack_state(
            implementer_status=implementer_status,
            implementer_ack=implementer_ack,
            ack_current=ack_current,
            stale_label="stale",
            is_substantive_text=_is_substantive_text,
        ),
        implementer_state_hash=compute_implementer_state_hash(
            implementer_status=implementer_status,
            implementer_ack=implementer_ack,
        ),
        implementer_session_state=str(implementer_hint.get("state") or ""),
        implementer_session_hint=str(implementer_hint.get("summary") or ""),
        open_findings=open_findings,
        last_reviewed_scope=last_reviewed_scope,
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _bridge_liveness_implementer_ack(
    bridge_liveness: Mapping[str, object],
) -> str:
    for field in ("implementer_ack", "claude_ack"):
        raw = bridge_liveness.get(field)
        value = clean_section(str(raw or ""))
        if value and _is_substantive_text(value):
            return value
    return ""
