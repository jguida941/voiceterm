"""Authority-building helpers for bridge-backed status refresh."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .collaboration_provider import (
    coding_provider_from_review_state,
    reviewer_provider_from_review_state,
)
from ..runtime.governance_scan import scan_repo_governance_safely
from ..runtime.review_packet_inbox import (
    packet_inbox_from_review_state,
    summarize_packet_attention_open_findings,
)
from .current_session_attention import has_explicit_packet_truth
from .current_session_projection import (
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
from ..runtime.review_state_semantics import is_missing_instruction


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
    reviewer_accepted_implementer_state_hash_override: str | None = None


def build_status_authority(
    inputs: StatusAuthorityInputs,
) -> tuple[object, dict[str, object], object, object]:
    """Build current-session, attention, recovery, and reviewer runtime state."""
    current_session = resolve_current_session_authority(
        snapshot=inputs.bridge_snapshot,
        bridge_liveness=inputs.bridge_liveness,
        prior_review_state=inputs.prior_review_state,
    )
    current_session = _normalize_current_session_from_packet_truth(
        current_session=current_session,
        review_state=inputs.prior_review_state,
    )
    _append_status_warning(
        inputs.merged_warnings,
        current_session_authority_drift_warning(
            snapshot=inputs.bridge_snapshot,
            prior_review_state=inputs.prior_review_state,
        ),
    )
    _append_status_warning(
        inputs.merged_warnings,
        instruction_revision_reuse_warning(
            snapshot=inputs.bridge_snapshot,
            bridge_liveness=inputs.bridge_liveness,
            prior_review_state=inputs.prior_review_state,
        ),
    )
    _apply_current_session_fields(
        bridge_liveness=inputs.bridge_liveness,
        current_session=current_session,
    )
    recovery_assessment = build_recovery_assessment(
        bridge_liveness=inputs.bridge_liveness,
        current_session=current_session,
        contract_errors=inputs.merged_errors,
        operator_interaction_mode=_operator_interaction_mode(inputs.repo_root),
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
            prior_review_state=inputs.prior_review_state,
            reviewer_accepted_implementer_state_hash_override=(
                inputs.reviewer_accepted_implementer_state_hash_override
            ),
        )
    )
    return current_session, attention, recovery_assessment, reviewer_runtime


def _operator_interaction_mode(repo_root: Path) -> str:
    governance = scan_repo_governance_safely(repo_root)
    if governance is None:
        return ""
    return str(governance.bridge_config.operator_interaction_mode or "").strip()


def _append_status_warning(warnings: list[str], warning: str) -> None:
    if warning and warning not in warnings:
        warnings.append(warning)


def _normalize_current_session_from_packet_truth(
    *,
    current_session,
    review_state: dict[str, object] | None,
):
    if current_session is None:
        return current_session
    resolved_review_state = review_state
    if isinstance(resolved_review_state, dict) and isinstance(
        resolved_review_state.get("review_state"), dict
    ):
        resolved_review_state = resolved_review_state.get("review_state")
    packet_truth_present = bool(
        isinstance(resolved_review_state, dict)
        and has_explicit_packet_truth(resolved_review_state)
    )
    packet_inbox = (
        packet_inbox_from_review_state(resolved_review_state)
        if packet_truth_present
        else None
    )
    implementer_provider = coding_provider_from_review_state(resolved_review_state)
    reviewer_provider = reviewer_provider_from_review_state(resolved_review_state)
    record = (
        packet_inbox.for_agent(implementer_provider)
        if packet_inbox is not None
        else None
    )
    clear_instruction = bool(
        record is not None
        and not str(record.current_instruction_packet_id or "").strip()
    )
    packet_attention_present = record is not None
    missing_instruction = is_missing_instruction(current_session.current_instruction)
    clear_current_instruction = clear_instruction or missing_instruction
    cleared_ack = "" if clear_current_instruction else current_session.implementer_ack
    return replace(
        current_session,
        current_instruction=(
            "" if clear_current_instruction else current_session.current_instruction
        ),
        current_instruction_revision=(
            ""
            if clear_current_instruction
            else current_session.current_instruction_revision
        ),
        implementer_ack=cleared_ack,
        implementer_ack_revision=(
            ""
            if clear_current_instruction
            else current_session.implementer_ack_revision
        ),
        implementer_ack_state=(
            "missing"
            if clear_current_instruction
            else current_session.implementer_ack_state
        ),
        implementer_state_hash=compute_implementer_state_hash(
            implementer_status=current_session.implementer_status,
            implementer_ack=cleared_ack,
        ),
        open_findings=summarize_packet_attention_open_findings(
            resolved_review_state,
            fallback="" if packet_attention_present else current_session.open_findings,
            agent=reviewer_provider,
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
