"""Parsers and authority validators for agent-session continuation contracts."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_session_continuation_models import (
    AGENT_RESUME_RECEIPT_CONTRACT_ID,
    AGENT_RESUME_RECEIPT_SCHEMA_VERSION,
    AGENT_SESSION_CONTINUATION_CONTRACT_ID,
    AGENT_SESSION_CONTINUATION_SCHEMA_VERSION,
    CONTINUATION_RESULT_EXPECTED,
    RESUME_RESULT_LOADED,
    AgentResumeReceiptState,
    AgentSessionContinuationState,
)
from .agent_session_continuation_values import (
    authority_result as _authority_result,
    continuation_hash,
    continuation_mode as _continuation_mode,
    dirty_paths_status as _dirty_paths_status,
    resume_receipt_hash,
    resume_result,
)
from .value_coercion import coerce_int, coerce_mapping, coerce_string


def agent_session_continuation_from_mapping(
    value: object,
) -> AgentSessionContinuationState | None:
    payload = coerce_mapping(value)
    if not payload:
        return None
    agent_id = coerce_string(payload.get("agent_id"))
    role = coerce_string(payload.get("role"))
    state_hash = coerce_string(payload.get("continuation_hash"))
    bootstrap_hash = coerce_string(payload.get("bootstrap_hash"))
    if not (agent_id or role or state_hash or bootstrap_hash):
        return None
    dirty_count = coerce_int(payload.get("dirty_paths_count"))
    dirty_status = _dirty_paths_status(payload.get("dirty_paths_status"), dirty_count)
    return AgentSessionContinuationState(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=(
            coerce_string(payload.get("contract_id"))
            or AGENT_SESSION_CONTINUATION_CONTRACT_ID
        ),
        continuation_id=coerce_string(payload.get("continuation_id")),
        agent_id=agent_id,
        provider=coerce_string(payload.get("provider")) or agent_id,
        role=role,
        working_tree=coerce_string(payload.get("working_tree")),
        branch=coerce_string(payload.get("branch")),
        session_id_or_transcript_path=coerce_string(
            payload.get("session_id_or_transcript_path")
        ),
        last_seen_packet_id=coerce_string(payload.get("last_seen_packet_id")),
        last_acknowledged_packet_id=coerce_string(
            payload.get("last_acknowledged_packet_id")
        ),
        current_assignment=coerce_string(payload.get("current_assignment")),
        dirty_paths_count=dirty_count,
        dirty_paths_status=dirty_status,
        current_blockers=coerce_string(payload.get("current_blockers")) or "none",
        resume_command=coerce_string(payload.get("resume_command")),
        continuation_hash=state_hash or bootstrap_hash,
        bootstrap_hash=bootstrap_hash,
        continuation_mode=_continuation_mode(payload.get("continuation_mode")),
        generated_at_utc=coerce_string(payload.get("generated_at_utc")),
        authority_result=_authority_result(
            payload.get("authority_result"),
            current_blockers=payload.get("current_blockers"),
            dirty_paths_status_value=dirty_status,
        ),
        result=resume_result(
            payload.get("result"),
            default=CONTINUATION_RESULT_EXPECTED,
        ),
    )


def agent_resume_receipt_from_mapping(value: object) -> AgentResumeReceiptState | None:
    payload = coerce_mapping(value)
    if not payload:
        return None
    continuation_id = coerce_string(payload.get("continuation_id"))
    state_hash = coerce_string(payload.get("continuation_hash"))
    bootstrap_hash = coerce_string(payload.get("bootstrap_hash"))
    if not (continuation_id or state_hash or bootstrap_hash):
        return None
    agent_id = coerce_string(payload.get("agent_id"))
    dirty_count = coerce_int(payload.get("dirty_paths_count"))
    dirty_status = _dirty_paths_status(payload.get("dirty_paths_status"), dirty_count)
    return AgentResumeReceiptState(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=(
            coerce_string(payload.get("contract_id"))
            or AGENT_RESUME_RECEIPT_CONTRACT_ID
        ),
        receipt_id=coerce_string(payload.get("receipt_id")),
        continuation_id=continuation_id,
        agent_id=agent_id,
        provider=coerce_string(payload.get("provider")) or agent_id,
        role=coerce_string(payload.get("role")),
        working_tree=coerce_string(payload.get("working_tree")),
        branch=coerce_string(payload.get("branch")),
        session_id_or_transcript_path=coerce_string(
            payload.get("session_id_or_transcript_path")
        ),
        last_seen_packet_id=coerce_string(payload.get("last_seen_packet_id")),
        last_acknowledged_packet_id=coerce_string(
            payload.get("last_acknowledged_packet_id")
        ),
        current_assignment=coerce_string(payload.get("current_assignment")),
        dirty_paths_count=dirty_count,
        dirty_paths_status=dirty_status,
        current_blockers=coerce_string(payload.get("current_blockers")) or "none",
        resume_command=coerce_string(payload.get("resume_command")),
        continuation_hash=state_hash or bootstrap_hash,
        bootstrap_hash=bootstrap_hash,
        continuation_mode=_continuation_mode(payload.get("continuation_mode")),
        started_at_utc=coerce_string(payload.get("started_at_utc")),
        observed_at_utc=coerce_string(payload.get("observed_at_utc")),
        load_result=resume_result(
            payload.get("load_result") or payload.get("result"),
            default=RESUME_RESULT_LOADED,
        ),
        authority_result=_authority_result(
            payload.get("authority_result"),
            current_blockers=payload.get("current_blockers"),
            dirty_paths_status_value=dirty_status,
        ),
        result=resume_result(payload.get("result"), default=RESUME_RESULT_LOADED),
        source=coerce_string(payload.get("source")) or "session-resume",
        source_event_id=coerce_string(payload.get("source_event_id")),
    )


def validate_agent_session_continuation(
    value: object,
) -> AgentSessionContinuationState:
    """Strict authority parser for continuation state."""
    payload = coerce_mapping(value)
    required = (
        "contract_id",
        "schema_version",
        "continuation_id",
        "agent_id",
        "provider",
        "role",
        "working_tree",
        "branch",
        "continuation_hash",
        "generated_at_utc",
    )
    _require_authority_fields(
        payload,
        required=required,
        contract_id=AGENT_SESSION_CONTINUATION_CONTRACT_ID,
        schema_version=AGENT_SESSION_CONTINUATION_SCHEMA_VERSION,
    )
    parsed = agent_session_continuation_from_mapping(payload)
    if parsed is None:
        raise ValueError("Invalid AgentSessionContinuation payload.")
    expected_hash = continuation_hash(parsed.to_dict())
    if parsed.continuation_hash != expected_hash:
        raise ValueError("AgentSessionContinuation continuation_hash mismatch.")
    expected_id = f"agent_continuation:{expected_hash[:16]}"
    if parsed.continuation_id != expected_id:
        raise ValueError("AgentSessionContinuation continuation_id mismatch.")
    return parsed


def validate_agent_resume_receipt(value: object) -> AgentResumeReceiptState:
    """Strict authority parser for resume receipts."""
    payload = coerce_mapping(value)
    required = (
        "contract_id",
        "schema_version",
        "receipt_id",
        "continuation_id",
        "agent_id",
        "provider",
        "role",
        "working_tree",
        "branch",
        "continuation_hash",
        "observed_at_utc",
        "load_result",
        "authority_result",
    )
    _require_authority_fields(
        payload,
        required=required,
        contract_id=AGENT_RESUME_RECEIPT_CONTRACT_ID,
        schema_version=AGENT_RESUME_RECEIPT_SCHEMA_VERSION,
    )
    parsed = agent_resume_receipt_from_mapping(payload)
    if parsed is None:
        raise ValueError("Invalid AgentResumeReceipt payload.")
    expected_id = f"agent_resume:{resume_receipt_hash(parsed.to_dict())[:16]}"
    if parsed.receipt_id != expected_id:
        raise ValueError("AgentResumeReceipt receipt_id mismatch.")
    return parsed


def _require_authority_fields(
    payload: Mapping[str, object],
    *,
    required: tuple[str, ...],
    contract_id: str,
    schema_version: int,
) -> None:
    if coerce_string(payload.get("contract_id")) != contract_id:
        raise ValueError(f"Expected contract_id={contract_id}.")
    if coerce_int(payload.get("schema_version")) != schema_version:
        raise ValueError(f"Expected schema_version={schema_version}.")
    missing = [field for field in required if not coerce_string(payload.get(field))]
    if missing:
        raise ValueError(
            f"{contract_id} missing required authority field(s): "
            + ", ".join(missing)
        )


__all__ = [
    "agent_resume_receipt_from_mapping",
    "agent_session_continuation_from_mapping",
    "validate_agent_resume_receipt",
    "validate_agent_session_continuation",
]
