"""Dataclasses for typed agent-session continuation contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass

AGENT_SESSION_CONTINUATION_CONTRACT_ID = "AgentSessionContinuation"
AGENT_SESSION_CONTINUATION_SCHEMA_VERSION = 1
AGENT_RESUME_RECEIPT_CONTRACT_ID = "AgentResumeReceipt"
AGENT_RESUME_RECEIPT_SCHEMA_VERSION = 1

CONTINUATION_MODE_TYPED_REHYDRATION = "typed_rehydration"
CONTINUATION_MODE_RUNTIME_RESUME = "runtime_resume"

CONTINUATION_RESULT_EXPECTED = "expected"
RESUME_RESULT_LOADED = "loaded"
RESUME_RESULT_BLOCKED = "blocked"
RESUME_RESULT_FAILED = "failed"
AUTHORITY_RESULT_ALLOWED = "allowed"
AUTHORITY_RESULT_BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AgentSessionContinuationState:
    """Expected typed state a newly started agent process must rehydrate from."""

    schema_version: int = AGENT_SESSION_CONTINUATION_SCHEMA_VERSION
    contract_id: str = AGENT_SESSION_CONTINUATION_CONTRACT_ID
    continuation_id: str = ""
    agent_id: str = ""
    provider: str = ""
    role: str = ""
    working_tree: str = ""
    branch: str = ""
    session_id_or_transcript_path: str = ""
    last_seen_packet_id: str = ""
    last_acknowledged_packet_id: str = ""
    current_assignment: str = ""
    dirty_paths_count: int = 0
    dirty_paths_status: str = "known"
    current_blockers: str = "none"
    resume_command: str = ""
    continuation_hash: str = ""
    bootstrap_hash: str = ""
    continuation_mode: str = CONTINUATION_MODE_TYPED_REHYDRATION
    generated_at_utc: str = ""
    authority_result: str = AUTHORITY_RESULT_ALLOWED
    result: str = CONTINUATION_RESULT_EXPECTED

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AgentResumeReceiptState:
    """Proof that an agent process loaded one typed continuation state."""

    schema_version: int = AGENT_RESUME_RECEIPT_SCHEMA_VERSION
    contract_id: str = AGENT_RESUME_RECEIPT_CONTRACT_ID
    receipt_id: str = ""
    continuation_id: str = ""
    agent_id: str = ""
    provider: str = ""
    role: str = ""
    working_tree: str = ""
    branch: str = ""
    session_id_or_transcript_path: str = ""
    last_seen_packet_id: str = ""
    last_acknowledged_packet_id: str = ""
    current_assignment: str = ""
    dirty_paths_count: int = 0
    dirty_paths_status: str = "known"
    current_blockers: str = "none"
    resume_command: str = ""
    continuation_hash: str = ""
    bootstrap_hash: str = ""
    continuation_mode: str = CONTINUATION_MODE_TYPED_REHYDRATION
    started_at_utc: str = ""
    observed_at_utc: str = ""
    load_result: str = RESUME_RESULT_LOADED
    authority_result: str = AUTHORITY_RESULT_ALLOWED
    result: str = RESUME_RESULT_LOADED
    source: str = "session-resume"
    source_event_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


__all__ = [
    "AGENT_RESUME_RECEIPT_CONTRACT_ID",
    "AGENT_RESUME_RECEIPT_SCHEMA_VERSION",
    "AGENT_SESSION_CONTINUATION_CONTRACT_ID",
    "AGENT_SESSION_CONTINUATION_SCHEMA_VERSION",
    "AUTHORITY_RESULT_ALLOWED",
    "AUTHORITY_RESULT_BLOCKED",
    "CONTINUATION_MODE_RUNTIME_RESUME",
    "CONTINUATION_MODE_TYPED_REHYDRATION",
    "CONTINUATION_RESULT_EXPECTED",
    "RESUME_RESULT_BLOCKED",
    "RESUME_RESULT_FAILED",
    "RESUME_RESULT_LOADED",
    "AgentResumeReceiptState",
    "AgentSessionContinuationState",
]
