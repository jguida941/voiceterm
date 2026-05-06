"""Shared current-session support helpers for review-channel projections."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256

from .ack_contract import extract_implementer_ack_revision
from .collaboration_provider import (
    coding_provider_from_review_state,
    reviewer_provider_from_review_state,
)
from .handoff import BridgeSnapshot
from .handoff_constants import _is_substantive_text
from .current_session_queue import (
    queue_current_instruction,
    queue_instruction_is_priority_action_request,
)
from .current_session_attention import reviewer_checkpoint_instruction_preservation
from .current_session_instruction_support import (
    canonicalize_instruction_state as _canonicalize_instruction_state,
    instruction_revision_reuse_warning,
    _normalize_instruction_body,
    resolve_instruction_revision,
)
from .status_projection_helpers import clean_section
from .current_session_authority import prefer_bridge_current_session
from ..runtime.review_packet_inbox import summarize_packet_attention_open_findings
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

    raw_current_instruction = clean_section(
        str(current_session.get("current_instruction") or "")
    )
    current_instruction, current_instruction_revision = _canonicalize_instruction_state(
        raw_current_instruction,
        str(current_session.get("current_instruction_revision") or "").strip(),
    )
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


def current_session_authority_drift_warning(
    *,
    snapshot: BridgeSnapshot,
    prior_review_state: Mapping[str, object] | None,
    bridge_liveness: Mapping[str, object] | None = None,
) -> str:
    """Warn when the compatibility bridge drifts from typed current-session state."""
    prior_session = prior_typed_current_session(prior_review_state)
    if prior_session is None:
        return ""
    bridge_session = _bridge_current_session_from_snapshot(
        snapshot,
        bridge_liveness=bridge_liveness,
    )
    if prefer_bridge_current_session(
        prior_session=prior_session,
        bridge_session=bridge_session,
        bridge_liveness=bridge_liveness,
    ):
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
        if _bridge_placeholder_matches_missing_typed_value(
            heading=heading,
            typed_value=normalized_typed,
            live_value=live_value,
        ):
            continue
        if normalized_typed != live_value:
            drifted.append(heading)
    if not drifted:
        return ""

    joined = ", ".join(drifted[:3])
    if len(drifted) > 3:
        joined += ", ..."
    return (
        "Live bridge sections drift from persisted typed `current_session` "
        f"authority ({joined}). This refresh is reprojecting the live bridge "
        "state so the next typed snapshot converges on the reviewer-owned "
        "checkpoint."
    )


def _bridge_placeholder_matches_missing_typed_value(
    *,
    heading: str,
    typed_value: str,
    live_value: str,
) -> bool:
    typed = clean_section(typed_value).lower()
    live = _normalize_placeholder_text(live_value)
    typed_missing = typed in {"", "(missing)", "missing", "none"}
    if not typed_missing:
        return False
    if heading == "Current Instruction For Claude":
        return live in {
            "await reviewer instruction refresh",
            "stop at a safe boundary",
            "relaunch before compaction",
        }
    if heading == "Claude Status":
        return live in {"status unavailable", "missing"}
    if heading == "Claude Ack":
        return live in {"missing"}
    return False


def _normalize_placeholder_text(value: str) -> str:
    text = clean_section(value).lower().rstrip(".").strip()
    if text.startswith("- "):
        text = text[2:].strip()
    return text


def _bridge_current_session_from_snapshot(
    snapshot: BridgeSnapshot,
    *,
    bridge_liveness: Mapping[str, object] | None = None,
) -> ReviewCurrentSessionState:
    current_instruction = _section_text(snapshot, "Current Instruction For Claude")
    implementer_status = _section_text(snapshot, "Claude Status")
    implementer_ack = _section_text(snapshot, "Claude Ack")
    implementer_ack_revision = (
        str((bridge_liveness or {}).get("implementer_ack_revision") or "").strip()
        or extract_implementer_ack_revision(implementer_ack)
    )
    return ReviewCurrentSessionState(
        current_instruction=current_instruction,
        current_instruction_revision=str(
            snapshot.metadata.get("current_instruction_revision")
            or (bridge_liveness or {}).get("current_instruction_revision")
            or ""
        ).strip(),
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_revision=implementer_ack_revision,
        implementer_ack_state=str(
            (bridge_liveness or {}).get("implementer_ack_state") or "unknown"
        ).strip(),
        implementer_state_hash=compute_implementer_state_hash(
            implementer_status=implementer_status,
            implementer_ack=implementer_ack,
        ),
        implementer_session_state=str(
            (bridge_liveness or {}).get("implementer_session_state") or ""
        ).strip(),
        implementer_session_hint=str(
            (bridge_liveness or {}).get("implementer_session_hint") or ""
        ).strip(),
        open_findings=_section_text(snapshot, "Open Findings"),
        last_reviewed_scope=_section_text(snapshot, "Last Reviewed Scope"),
    )


def event_current_instruction(review_state: Mapping[str, object]) -> str:
    """Derive the event-backed current instruction from the typed queue only.

    Typed queue instructions are the live route. A reviewer checkpoint is a
    preserved fallback only when no queue instruction is currently selected.
    """
    queue_instruction = queue_current_instruction(review_state)
    if queue_instruction:
        return queue_instruction

    checkpoint = _mapping(review_state.get("latest_reviewer_checkpoint"))
    preserved = reviewer_checkpoint_instruction_preservation(review_state)
    if preserved is not None:
        return preserved[0]
    return queue_instruction


def event_open_findings(review_state: Mapping[str, object]) -> str:
    """Summarize pending event-backed findings for the current session."""
    return summarize_packet_attention_open_findings(
        review_state,
        fallback="",
        agent=reviewer_provider_from_review_state(review_state),
    )


def event_claude_ack(queue: Mapping[str, object]) -> str:
    """Return a pending marker for event-backed queue pressure.

    Packet delivery/ack/apply lifecycle is not the implementer ACK contract.
    The event queue may show that an implementer still needs to act, but an
    empty queue must not synthesize `Claude Ack` or mark the current instruction
    acknowledged.
    """
    pending_claude = int(queue.get("pending_claude") or 0)
    return "pending" if pending_claude else ""


def event_implementer_ack(review_state: Mapping[str, object]) -> str:
    """Return a pending marker for the active coding-agent queue slot."""
    queue = _mapping(review_state.get("queue"))
    pending_total = int(
        queue.get(f"pending_{coding_provider_from_review_state(review_state)}") or 0
    )
    return "pending" if pending_total else ""


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


def _section_text(snapshot: BridgeSnapshot, section: str) -> str:
    return clean_section(snapshot.sections.get(section, ""))
def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
