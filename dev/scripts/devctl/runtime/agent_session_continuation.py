"""Public facade for typed agent-session continuation contracts."""

from __future__ import annotations

from .agent_session_continuation_build import (
    build_agent_resume_receipt,
    build_agent_session_continuation,
)
from .agent_session_continuation_models import (
    AGENT_RESUME_RECEIPT_CONTRACT_ID,
    AGENT_RESUME_RECEIPT_SCHEMA_VERSION,
    AGENT_SESSION_CONTINUATION_CONTRACT_ID,
    AGENT_SESSION_CONTINUATION_SCHEMA_VERSION,
    AUTHORITY_RESULT_ALLOWED,
    AUTHORITY_RESULT_BLOCKED,
    CONTINUATION_MODE_RUNTIME_RESUME,
    CONTINUATION_MODE_TYPED_REHYDRATION,
    RESUME_RESULT_BLOCKED,
    RESUME_RESULT_FAILED,
    RESUME_RESULT_LOADED,
    AgentResumeReceiptState,
    AgentSessionContinuationState,
)
from .agent_session_continuation_parse import (
    agent_resume_receipt_from_mapping,
    agent_session_continuation_from_mapping,
    validate_agent_resume_receipt,
    validate_agent_session_continuation,
)

__all__ = [
    "AGENT_RESUME_RECEIPT_CONTRACT_ID",
    "AGENT_RESUME_RECEIPT_SCHEMA_VERSION",
    "AGENT_SESSION_CONTINUATION_CONTRACT_ID",
    "AGENT_SESSION_CONTINUATION_SCHEMA_VERSION",
    "AUTHORITY_RESULT_ALLOWED",
    "AUTHORITY_RESULT_BLOCKED",
    "CONTINUATION_MODE_RUNTIME_RESUME",
    "CONTINUATION_MODE_TYPED_REHYDRATION",
    "RESUME_RESULT_BLOCKED",
    "RESUME_RESULT_FAILED",
    "RESUME_RESULT_LOADED",
    "AgentResumeReceiptState",
    "AgentSessionContinuationState",
    "agent_resume_receipt_from_mapping",
    "agent_session_continuation_from_mapping",
    "build_agent_resume_receipt",
    "build_agent_session_continuation",
    "validate_agent_resume_receipt",
    "validate_agent_session_continuation",
]
