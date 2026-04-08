"""Shared current-session support helpers for review-channel projections."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256

from .ack_contract import extract_implementer_ack_revision
from .handoff import BridgeSnapshot
from .handoff_constants import _is_substantive_text
from .reviewer_state_normalize import (
    instruction_revision as _normalized_instruction_revision,
    normalize_instruction_body as _normalize_instruction_body,
)
from .status_projection_helpers import clean_section
from ..runtime.review_state_models import ReviewCurrentSessionState
from ..runtime.review_state_semantics import classify_implementer_ack_state


def compute_implementer_state_hash(
    *,
    implementer_status: str,
    implementer_questions: str = "",
    implementer_ack: str,
) -> str:
    """Return a stable digest for Claude-owned live bridge state."""
    normalized = (
        clean_section(implementer_status),
        clean_section(implementer_questions),
        clean_section(implementer_ack),
    )
    if not any(normalized):
        return ""
    return sha256("\0".join(normalized).encode("utf-8")).hexdigest()


def prior_typed_current_session(
    prior_review_state: Mapping[str, object] | None,
) -> ReviewCurrentSessionState | None:
    """Read the persisted typed current-session payload when present."""
    prior_payload = _mapping(prior_review_state)
    review_state = _mapping(prior_payload.get("review_state")) or prior_payload
    current_session = _mapping(review_state.get("current_session"))
    if not current_session:
        return None

    current_instruction = clean_section(
        str(current_session.get("current_instruction") or "")
    )
    current_instruction_revision = str(
        current_session.get("current_instruction_revision") or ""
    ).strip()
    implementer_status = clean_section(
        str(current_session.get("implementer_status") or "")
    )
    implementer_ack = clean_section(str(current_session.get("implementer_ack") or ""))
    implementer_ack_revision = str(
        current_session.get("implementer_ack_revision") or ""
    ).strip() or extract_implementer_ack_revision(implementer_ack)
    implementer_ack_state = str(
        current_session.get("implementer_ack_state") or ""
    ).strip()
    if not implementer_ack_state:
        ack_current = _is_substantive_text(implementer_ack) and (
            not current_instruction_revision
            or implementer_ack_revision == current_instruction_revision
        )
        implementer_ack_state = classify_implementer_ack_state(
            implementer_status=implementer_status,
            implementer_ack=implementer_ack,
            ack_current=ack_current,
            stale_label="stale",
            is_substantive_text=_is_substantive_text,
        )
    implementer_state_hash = str(
        current_session.get("implementer_state_hash") or ""
    ).strip() or compute_implementer_state_hash(
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
    )
    implementer_session_state = str(
        current_session.get("implementer_session_state") or ""
    ).strip()
    implementer_session_hint = str(
        current_session.get("implementer_session_hint") or ""
    ).strip()
    open_findings = clean_section(str(current_session.get("open_findings") or ""))
    last_reviewed_scope = clean_section(
        str(current_session.get("last_reviewed_scope") or "")
    )

    if not any(
        (
            current_instruction,
            current_instruction_revision,
            implementer_status,
            implementer_ack,
            implementer_ack_revision,
            implementer_state_hash,
            open_findings,
            last_reviewed_scope,
        )
    ):
        return None

    return ReviewCurrentSessionState(
        current_instruction=current_instruction,
        current_instruction_revision=current_instruction_revision,
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_revision=implementer_ack_revision,
        implementer_ack_state=implementer_ack_state or "unknown",
        implementer_state_hash=implementer_state_hash,
        implementer_session_state=implementer_session_state,
        implementer_session_hint=implementer_session_hint,
        open_findings=open_findings,
        last_reviewed_scope=last_reviewed_scope,
    )


def resolve_instruction_revision(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
    current_instruction: str,
    prior_review_state: Mapping[str, object] | None,
) -> str:
    """Return the current instruction revision for bridge-backed status."""
    revision = str(bridge_liveness.get("current_instruction_revision") or "").strip()
    if revision and _instruction_revision_reused_for_changed_instruction(
        revision=revision,
        current_instruction=current_instruction,
        prior_review_state=prior_review_state,
    ):
        return _derived_instruction_revision(current_instruction)
    if revision:
        return revision

    revision = str(snapshot.metadata.get("current_instruction_revision") or "").strip()
    if revision and _instruction_revision_reused_for_changed_instruction(
        revision=revision,
        current_instruction=current_instruction,
        prior_review_state=prior_review_state,
    ):
        return _derived_instruction_revision(current_instruction)
    if revision:
        return revision
    return _derived_instruction_revision(current_instruction)


def current_session_authority_drift_warning(
    *,
    snapshot: BridgeSnapshot,
    prior_review_state: Mapping[str, object] | None,
) -> str:
    """Warn when the compatibility bridge drifts from typed current-session state."""
    prior_session = prior_typed_current_session(prior_review_state)
    if prior_session is None:
        return ""

    drifted: list[str] = []
    section_pairs = (
        ("Current Instruction For Claude", prior_session.current_instruction),
        ("Claude Status", prior_session.implementer_status),
        ("Claude Ack", prior_session.implementer_ack),
        ("Open Findings", prior_session.open_findings),
        ("Last Reviewed Scope", prior_session.last_reviewed_scope),
    )
    for heading, typed_value in section_pairs:
        live_value = _section_text(snapshot, heading)
        normalized_typed = (
            _normalize_instruction_body(typed_value)
            if heading == "Current Instruction For Claude"
            else clean_section(typed_value)
        )
        if normalized_typed != live_value:
            drifted.append(heading)
    if not drifted:
        return ""

    joined = ", ".join(drifted[:3])
    if len(drifted) > 3:
        joined += ", ..."
    return (
        "Live bridge sections drift from typed `current_session` authority "
        f"({joined}). Status is projecting the persisted typed session until a "
        "repo-owned writer refreshes the bridge compatibility projection."
    )


def instruction_revision_reuse_warning(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
    prior_review_state: Mapping[str, object] | None,
) -> str:
    """Return a warning when reviewer instruction text changed under one revision."""
    current_instruction = _section_text(snapshot, "Current Instruction For Claude")
    explicit_revision = str(
        snapshot.metadata.get("current_instruction_revision")
        or bridge_liveness.get("current_instruction_revision")
        or ""
    ).strip()
    if not explicit_revision:
        return ""
    if not _instruction_revision_reused_for_changed_instruction(
        revision=explicit_revision,
        current_instruction=current_instruction,
        prior_review_state=prior_review_state,
    ):
        return ""
    derived_revision = _derived_instruction_revision(current_instruction)
    if not derived_revision:
        return ""
    return (
        "Current reviewer instruction text changed while `Current instruction "
        f"revision` stayed at `{explicit_revision}`. Typed state re-derived the "
        f"live revision as `{derived_revision}`; refresh reviewer-owned bridge "
        "metadata so the markdown header matches the current instruction body."
    )


def event_current_instruction(review_state: Mapping[str, object]) -> str:
    """Derive the event-backed current instruction from queue or packets."""
    queue = _mapping(review_state.get("queue"))
    derived = str(queue.get("derived_next_instruction") or "").strip()
    if derived:
        return derived
    packets = review_state.get("packets")
    if isinstance(packets, list):
        for packet in packets:
            if not isinstance(packet, dict) or packet.get("status") != "pending":
                continue
            summary = str(packet.get("summary") or "").strip()
            if summary:
                return summary
    return ""


def event_open_findings(queue: Mapping[str, object]) -> str:
    """Summarize pending event-backed findings for the current session."""
    pending_total = int(queue.get("pending_total") or 0)
    if pending_total <= 0:
        return "none"
    return f"{pending_total} pending review packet(s)"


def event_claude_ack(queue: Mapping[str, object]) -> str:
    """Derive the implementer ACK state from event-backed queue counts."""
    pending_claude = int(queue.get("pending_claude") or 0)
    return "pending" if pending_claude else "acknowledged"


def event_agent_status(
    review_state: Mapping[str, object],
    agent_id: str,
) -> str:
    """Read one agent status from typed registry rows before compatibility fallbacks."""
    registry = _mapping(review_state.get("registry"))
    registry_agents = registry.get("agents")
    compat = review_state.get("_compat")
    compat_agents = compat.get("agents") if isinstance(compat, dict) else None
    agents = registry_agents or compat_agents or review_state.get("agents")
    if not isinstance(agents, list):
        return ""
    for agent in agents:
        if not isinstance(agent, dict) or agent.get("agent_id") != agent_id:
            continue
        return str(
            agent.get("job_state")
            or agent.get("job_status")
            or agent.get("status")
            or ""
        )
    return ""


def _instruction_revision_reused_for_changed_instruction(
    *,
    revision: str,
    current_instruction: str,
    prior_review_state: Mapping[str, object] | None,
) -> bool:
    if not revision:
        return False
    prior_session = _mapping(_mapping(prior_review_state).get("current_session"))
    prior_revision = str(prior_session.get("current_instruction_revision") or "").strip()
    if prior_revision != revision:
        return False
    prior_instruction = _normalize_instruction_body(
        str(prior_session.get("current_instruction") or "")
    )
    current_normalized = _normalize_instruction_body(current_instruction)
    if not prior_instruction or not current_normalized:
        return False
    return prior_instruction != current_normalized


def _derived_instruction_revision(current_instruction: str) -> str:
    normalized_instruction = _normalize_instruction_body(current_instruction)
    if normalized_instruction == "(missing)":
        return ""
    if not normalized_instruction:
        return ""
    return _normalized_instruction_revision(normalized_instruction)


def _section_text(snapshot: BridgeSnapshot, section: str) -> str:
    return clean_section(snapshot.sections.get(section, ""))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
