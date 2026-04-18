"""Shared current-session helpers for review-channel projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from .ack_contract import extract_implementer_ack_revision
from .collaboration_provider import coding_provider_from_review_state
from .current_session_attention import (
    implementer_packet_attention_for,
    packet_attention_requires_clear,
)
from .current_session_authority import prefer_bridge_current_session
from .handoff_constants import _is_substantive_text
from .current_session_render import (
    append_current_session_markdown,
    current_focus_line,
)
from .current_session_support import (
    _canonicalize_instruction_state,
    compute_implementer_state_hash,
    current_session_authority_drift_warning,
    event_agent_status,
    event_claude_ack,
    event_current_instruction,
    event_implementer_ack,
    event_open_findings,
    instruction_revision_reuse_warning,
    prior_typed_current_session,
    resolve_instruction_revision as _resolve_instruction_revision,
)
from .handoff import BridgeSnapshot
from .session_state_hints import provider_session_state_hint
from .status_projection_helpers import clean_section
from ..runtime.review_packet_inbox import packet_inbox_from_review_state
from ..runtime.review_state_semantics import is_missing_instruction
from ..runtime.review_state_models import ReviewCurrentSessionState
from ..runtime.review_state_semantics import classify_implementer_ack_state


def bridge_implementer_state_hash(snapshot: BridgeSnapshot) -> str:
    """Return the implementer-state digest for one bridge snapshot."""
    return compute_implementer_state_hash(
        implementer_status=_section_text(snapshot, "Claude Status"),
        implementer_questions=_section_text(snapshot, "Claude Questions"),
        implementer_ack=_section_text(snapshot, "Claude Ack"),
    )


def build_bridge_current_session(
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
    *,
    prior_review_state: Mapping[str, object] | None = None,
) -> ReviewCurrentSessionState:
    """Build typed current-session state from bridge sections."""
    current_instruction = _section_text(snapshot, "Current Instruction For Claude")
    implementer_status = _section_text(snapshot, "Claude Status")
    implementer_questions = _section_text(snapshot, "Claude Questions")
    implementer_ack = _section_text(snapshot, "Claude Ack")
    current_instruction_revision = _resolve_instruction_revision(
        snapshot=snapshot,
        bridge_liveness=bridge_liveness,
        current_instruction=current_instruction,
        prior_review_state=prior_review_state,
    )
    current_instruction, current_instruction_revision = _canonicalize_instruction_state(
        current_instruction,
        current_instruction_revision,
    )
    instruction_missing = is_missing_instruction(current_instruction)
    if instruction_missing:
        implementer_ack = ""
    implementer_ack_revision = (
        ""
        if instruction_missing
        else extract_implementer_ack_revision(implementer_ack)
    )
    ack_current = (not instruction_missing) and _is_substantive_text(
        implementer_ack
    ) and (
        not current_instruction_revision
        or implementer_ack_revision == current_instruction_revision
    )
    implementer_provider = coding_provider_from_review_state(prior_review_state)
    implementer_hint = provider_session_state_hint(
        dict(bridge_liveness),
        provider=implementer_provider,
    )
    return ReviewCurrentSessionState(
        current_instruction=current_instruction,
        current_instruction_revision=current_instruction_revision,
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_revision=implementer_ack_revision,
        implementer_ack_state=(
            "missing"
            if instruction_missing
            else classify_implementer_ack_state(
                implementer_status=implementer_status,
                implementer_ack=implementer_ack,
                ack_current=ack_current,
                stale_label="stale",
                is_substantive_text=_is_substantive_text,
            )
        ),
        implementer_state_hash=compute_implementer_state_hash(
            implementer_status=implementer_status,
            implementer_questions=implementer_questions,
            implementer_ack=implementer_ack,
        ),
        implementer_session_state=str(implementer_hint.get("state") or ""),
        implementer_session_hint=str(implementer_hint.get("summary") or ""),
        open_findings=_section_text(snapshot, "Open Findings"),
        last_reviewed_scope=_section_text(snapshot, "Last Reviewed Scope"),
    )


def resolve_current_session_authority(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
    prior_review_state: Mapping[str, object] | None = None,
) -> ReviewCurrentSessionState:
    """Return the canonical current-session owner for bridge-backed status."""
    bridge_session = build_bridge_current_session(
        snapshot,
        bridge_liveness,
        prior_review_state=prior_review_state,
    )
    prior_session = prior_typed_current_session(prior_review_state)
    if prior_session is None:
        return bridge_session
    if prefer_bridge_current_session(
        prior_session=prior_session,
        bridge_session=bridge_session,
        bridge_liveness=bridge_liveness,
    ):
        return bridge_session
    return prior_session


def build_event_current_session(
    *,
    review_state: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    prior_review_state: Mapping[str, object] | None = None,
) -> ReviewCurrentSessionState:
    """Build typed current-session state from event-backed review state."""
    prior_session = prior_typed_current_session(prior_review_state)
    implementer_provider = coding_provider_from_review_state(review_state)
    current_instruction = event_current_instruction(review_state)
    packet_attention = implementer_packet_attention_for(review_state)
    clear_from_packet_truth = packet_attention_requires_clear(packet_attention)
    current_instruction_revision = str(
        bridge_liveness.get("current_instruction_revision") or ""
    )
    if (
        not current_instruction
        and prior_session is not None
        and not clear_from_packet_truth
    ):
        current_instruction = prior_session.current_instruction
        current_instruction_revision = (
            current_instruction_revision or prior_session.current_instruction_revision
        )
    current_instruction, current_instruction_revision = _canonicalize_instruction_state(
        current_instruction,
        current_instruction_revision,
    )
    if clear_from_packet_truth:
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
        open_findings=event_open_findings(review_state),
        last_reviewed_scope=str(
            _mapping(review_state.get("review")).get("plan_id") or ""
        ),
    )


def current_session_payload(
    state: ReviewCurrentSessionState,
) -> dict[str, object]:
    """Serialize typed current-session state for JSON projections."""
    return asdict(state)


def current_session_mapping(
    review_state: Mapping[str, object],
) -> Mapping[str, object]:
    """Return the projected current-session mapping when present."""
    return _mapping(review_state.get("current_session"))


def _section_text(snapshot: BridgeSnapshot, section: str) -> str:
    raw = snapshot.sections.get(section, "")
    return clean_section(raw)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
