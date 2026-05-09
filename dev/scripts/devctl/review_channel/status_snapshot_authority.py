"""Authority-building helpers for bridge-backed status refresh."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path

from ..runtime.agent_mind_projection_read import read_agent_mind_projection
from ..runtime.governance_scan import scan_repo_governance_safely
from ..runtime.remote_control_attachment_status import remote_attachment_active
from .current_session_attention import has_explicit_packet_truth
from .current_session_packet_normalize import (
    normalize_current_session_from_packet_truth as _normalize_current_session_from_packet_truth,
)
from .current_session_projection import (
    build_event_current_session,
    current_session_authority_drift_warning,
    instruction_revision_reuse_warning,
    resolve_current_session_authority,
)
from .current_session_support import compute_implementer_state_hash
from .handoff import BridgeSnapshot
from .recovery_assessment import (
    build_recovery_assessment,
    recovery_assessment_to_attention_payload,
)
from .reviewer_runtime_contract import (
    ReviewerRuntimeInputs,
    build_reviewer_runtime_contract,
)
from .status_projection_support import build_queue_state
from ..runtime.operator_context import derive_operator_interaction_mode
from ..runtime.review_state_semantics import (
    is_missing_instruction,
    is_pending_implementer_state,
)


@dataclass
class StatusAuthorityInputs:
    """Inputs required to build typed authority state for status refresh."""

    repo_root: Path
    output_root: Path
    bridge_snapshot: BridgeSnapshot
    bridge_text: str
    bridge_liveness: dict[str, object]
    prior_review_state: dict[str, object]
    merged_warnings: list[str]
    merged_errors: list[str]
    pending_packets: tuple[dict[str, object], ...] = ()
    stale_packet_count: int = 0
    reviewer_accepted_implementer_state_hash_override: str | None = None


def build_status_authority(
    inputs: StatusAuthorityInputs,
) -> tuple[object, dict[str, object], object, object]:
    """Build current-session, attention, recovery, and reviewer runtime state."""
    authority_review_state = _review_state_with_packet_truth(
        prior_review_state=inputs.prior_review_state,
        pending_packets=inputs.pending_packets,
        stale_packet_count=inputs.stale_packet_count,
    )
    current_session = resolve_current_session_authority(
        snapshot=inputs.bridge_snapshot,
        bridge_liveness=inputs.bridge_liveness,
        prior_review_state=authority_review_state,
    )
    current_session = _overlay_packet_current_session(
        current_session=current_session,
        bridge_liveness=inputs.bridge_liveness,
        review_state=authority_review_state,
    )
    current_session = _normalize_current_session_from_packet_truth(
        current_session=current_session,
        review_state=authority_review_state,
    )
    current_session = _preserve_pending_bridge_implementer_reset(
        current_session=current_session,
        snapshot=inputs.bridge_snapshot,
    )
    _append_status_warning(
        inputs.merged_warnings,
        current_session_authority_drift_warning(
            snapshot=inputs.bridge_snapshot,
            prior_review_state=authority_review_state,
            bridge_liveness=inputs.bridge_liveness,
        ),
    )
    _append_status_warning(
        inputs.merged_warnings,
        instruction_revision_reuse_warning(
            snapshot=inputs.bridge_snapshot,
            bridge_liveness=inputs.bridge_liveness,
            prior_review_state=authority_review_state,
        ),
    )
    _apply_current_session_fields(
        bridge_liveness=inputs.bridge_liveness,
        current_session=current_session,
    )
    operator_interaction_mode = _operator_interaction_mode(
        inputs.repo_root,
        review_state_payload=authority_review_state,
        bridge_liveness=inputs.bridge_liveness,
    )
    recovery_assessment = build_recovery_assessment(
        bridge_liveness=inputs.bridge_liveness,
        current_session=current_session,
        contract_errors=inputs.merged_errors,
        operator_interaction_mode=operator_interaction_mode,
    )
    attention = recovery_assessment_to_attention_payload(recovery_assessment)
    reviewer_runtime = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=inputs.bridge_snapshot,
            bridge_liveness=inputs.bridge_liveness,
            current_session=current_session,
            recovery_assessment=recovery_assessment,
            attention=attention,
            session_output_root=inputs.output_root,
            rollover_dir=inputs.output_root.parent / "rollovers",
            bridge_text=inputs.bridge_text,
            prior_review_state=authority_review_state,
            repo_root=inputs.repo_root,
            operator_interaction_mode=operator_interaction_mode,
            agent_mind=read_agent_mind_projection(inputs.repo_root, provider="codex"),
            reviewer_accepted_implementer_state_hash_override=(
                inputs.reviewer_accepted_implementer_state_hash_override
            ),
        )
    )
    return current_session, attention, recovery_assessment, reviewer_runtime


def _operator_interaction_mode(
    repo_root: Path,
    *,
    review_state_payload: dict[str, object] | None = None,
    bridge_liveness: dict[str, object] | None = None,
) -> str:
    governance = scan_repo_governance_safely(repo_root)
    bridge = bridge_liveness or {}
    if _bridge_has_remote_control_attachment(bridge):
        return "remote_control"
    reviewer_mode = str(
        bridge.get("effective_reviewer_mode") or bridge.get("reviewer_mode") or ""
    ).strip()
    return derive_operator_interaction_mode(
        governance=governance,
        review_state_payload=review_state_payload,
        receipt=None,
        reviewer_mode=reviewer_mode,
    )


def _bridge_has_remote_control_attachment(bridge_liveness: dict[str, object]) -> bool:
    """Return True when the bridge proves a live remote-control attachment.

    Per rev_pkt_2986 finding #4: this used to be a local
    ``status == "attached"`` check that ignored TTL and the typed
    ``unknown`` (active) status, so a stale or never-heartbeated remote
    attachment would still fail-open as live. Replaced with the shared
    ``remote_attachment_active`` helper which honors
    ``ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES`` AND
    ``remote_attachment_expired`` TTL semantics.
    """
    providers = bridge_liveness.get("remote_control_active_providers")
    if isinstance(providers, (list, tuple, set)):
        return any(str(provider or "").strip() for provider in providers)
    attachment = bridge_liveness.get("remote_control_attachment")
    if isinstance(attachment, dict):
        return remote_attachment_active(attachment)
    return False


def _append_status_warning(warnings: list[str], warning: str) -> None:
    if warning and warning not in warnings:
        warnings.append(warning)


def _review_state_with_packet_truth(
    *,
    prior_review_state: dict[str, object] | None,
    pending_packets: tuple[dict[str, object], ...],
    stale_packet_count: int,
) -> dict[str, object] | None:
    if not pending_packets:
        return prior_review_state
    resolved_review_state = prior_review_state
    if isinstance(resolved_review_state, dict) and isinstance(
        resolved_review_state.get("review_state"), dict
    ):
        resolved_review_state = resolved_review_state.get("review_state")
    review_state = dict(resolved_review_state or {})
    review_state["packets"] = _merge_pending_and_prior_packets(
        pending_packets,
        review_state.get("packets"),
    )
    review_state["queue"] = asdict(
        build_queue_state(
            None,
            pending_packets=pending_packets,
            stale_packet_count=stale_packet_count,
        )
    )
    return review_state


def _merge_pending_and_prior_packets(
    pending_packets: tuple[dict[str, object], ...],
    prior_packets: object,
) -> list[dict[str, object]]:
    merged: list[dict[str, object]] = []
    seen: set[str] = set()
    for packet in (*pending_packets, *_packet_rows(prior_packets)):
        packet_id = str(packet.get("packet_id") or "").strip()
        if packet_id and packet_id in seen:
            continue
        if packet_id:
            seen.add(packet_id)
        merged.append(dict(packet))
    return merged


def _packet_rows(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(dict(packet) for packet in value if isinstance(packet, dict))


def _overlay_packet_current_session(
    *,
    current_session,
    bridge_liveness: dict[str, object],
    review_state: dict[str, object] | None,
):
    if not isinstance(review_state, dict) or not has_explicit_packet_truth(review_state):
        return current_session
    packet_session = build_event_current_session(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        prior_review_state=review_state,
    )
    if is_missing_instruction(packet_session.current_instruction):
        return current_session
    return packet_session


def _preserve_pending_bridge_implementer_reset(*, current_session, snapshot):
    if str(current_session.implementer_ack_state or "").strip() == "current":
        return current_session
    status = str(snapshot.sections.get("Implementer Status") or "").strip()
    ack = str(snapshot.sections.get("Implementer Ack") or "").strip()
    if not is_pending_implementer_state(
        implementer_status=status,
        implementer_ack=ack,
        implementer_ack_state="",
    ):
        return current_session
    return replace(
        current_session,
        implementer_status=status,
        implementer_ack=ack,
        implementer_ack_revision="",
        implementer_ack_state="pending",
        implementer_state_hash=compute_implementer_state_hash(
            implementer_status=status,
            implementer_ack=ack,
        ),
    )


def _apply_current_session_fields(
    *,
    bridge_liveness: dict[str, object],
    current_session,
) -> None:
    bridge_liveness["current_instruction"] = current_session.current_instruction
    bridge_liveness["current_instruction_revision"] = (
        current_session.current_instruction_revision
    )
    bridge_liveness["implementer_status"] = current_session.implementer_status
    bridge_liveness["claude_status"] = current_session.implementer_status
    bridge_liveness["implementer_ack"] = current_session.implementer_ack
    bridge_liveness["claude_ack"] = current_session.implementer_ack
    bridge_liveness["implementer_ack_revision"] = current_session.implementer_ack_revision
    bridge_liveness["claude_ack_revision"] = current_session.implementer_ack_revision
    bridge_liveness["implementer_ack_current"] = (
        current_session.implementer_ack_state == "current"
    )
    bridge_liveness["claude_ack_current"] = (
        current_session.implementer_ack_state == "current"
    )
    bridge_liveness["implementer_state_hash"] = current_session.implementer_state_hash
    bridge_liveness["open_findings"] = current_session.open_findings
    bridge_liveness["last_reviewed_scope"] = current_session.last_reviewed_scope
