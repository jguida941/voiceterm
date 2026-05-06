"""Bridge-backed current-session builders."""

from __future__ import annotations

from collections.abc import Mapping

from .ack_contract import extract_implementer_ack_revision
from .collaboration_provider import coding_provider_from_review_state
from .current_session_support import (
    _canonicalize_instruction_state,
    compute_implementer_state_hash,
    resolve_instruction_revision as _resolve_instruction_revision,
)
from .handoff import BridgeSnapshot
from .handoff_constants import _is_substantive_text
from .session_state_hints import provider_session_state_hint
from .status_projection_helpers import clean_section
from ..runtime.review_state_models import ReviewCurrentSessionState
from ..runtime.review_state_semantics import (
    classify_implementer_ack_state,
    is_missing_instruction,
)


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


def _section_text(snapshot: BridgeSnapshot, section: str) -> str:
    raw = snapshot.sections.get(section, "")
    return clean_section(raw)
