"""Builders for typed agent-session continuation contracts."""

from __future__ import annotations

from typing import Any

from .agent_session_continuation_models import (
    CONTINUATION_MODE_TYPED_REHYDRATION,
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
from .value_coercion import coerce_string


_CONTINUATION_DRAFT_DEFAULTS: tuple[tuple[str, object], ...] = (
    ("agent_id", ""),
    ("provider", ""),
    ("role", ""),
    ("working_tree", ""),
    ("branch", ""),
    ("session_id_or_transcript_path", ""),
    ("last_seen_packet_id", ""),
    ("last_acknowledged_packet_id", ""),
    ("current_assignment", ""),
    ("dirty_paths_count", 0),
    ("dirty_paths_status", ""),
    ("current_blockers", "none"),
    ("resume_command", ""),
    ("bootstrap_hash", ""),
    ("continuation_mode", CONTINUATION_MODE_TYPED_REHYDRATION),
    ("generated_at_utc", ""),
    ("authority_result", ""),
    ("result", CONTINUATION_RESULT_EXPECTED),
)

_RESUME_RECEIPT_DRAFT_DEFAULTS: tuple[tuple[str, object], ...] = (
    ("provider", ""),
    ("agent_id", ""),
    ("session_id_or_transcript_path", ""),
    ("started_at_utc", ""),
    ("observed_at_utc", ""),
    ("result", RESUME_RESULT_LOADED),
    ("authority_result", ""),
    ("source", "session-resume"),
)


class _DraftValues:
    """Construction-only input holder; never a runtime authority contract."""

    _defaults: tuple[tuple[str, object], ...] = ()

    def __init__(self, **values: object) -> None:
        defaults = dict(self._defaults)
        unknown = sorted(set(values) - set(defaults))
        if unknown:
            joined = ", ".join(unknown)
            raise TypeError(f"unknown agent-session continuation field(s): {joined}")
        for name, default in defaults.items():
            setattr(self, name, values.get(name, default))

    def with_values(self, values: dict[str, object]) -> "_DraftValues":
        if not values:
            return self
        names = tuple(name for name, _default in self._defaults)
        current = {name: getattr(self, name) for name in names}
        current.update(values)
        return self.__class__(**current)


class AgentSessionContinuationDraft(_DraftValues):
    """Construction helper for AgentSessionContinuationState."""

    __slots__ = tuple(name for name, _default in _CONTINUATION_DRAFT_DEFAULTS)
    _defaults = _CONTINUATION_DRAFT_DEFAULTS


class AgentResumeReceiptDraft(_DraftValues):
    """Construction helper for AgentResumeReceiptState."""

    __slots__ = tuple(name for name, _default in _RESUME_RECEIPT_DRAFT_DEFAULTS)
    _defaults = _RESUME_RECEIPT_DRAFT_DEFAULTS


def build_agent_session_continuation(
    draft: AgentSessionContinuationDraft | None = None,
    **values: object,
) -> AgentSessionContinuationState:
    """Build a continuation state and bind it to a stable state hash.

    When both ``draft`` and keyword values are supplied, keyword values
    deliberately override the draft before the final authority state is built.
    Unknown keyword fields fail closed.
    """
    draft = _continuation_draft(draft, values)
    dirty_count = int(draft.dirty_paths_count or 0)
    dirty_status = _dirty_paths_status(draft.dirty_paths_status, dirty_count)
    blockers = coerce_string(draft.current_blockers) or "none"
    state = AgentSessionContinuationState(
        agent_id=coerce_string(draft.agent_id),
        provider=coerce_string(draft.provider) or coerce_string(draft.agent_id),
        role=coerce_string(draft.role),
        working_tree=coerce_string(draft.working_tree),
        branch=coerce_string(draft.branch),
        session_id_or_transcript_path=coerce_string(
            draft.session_id_or_transcript_path
        ),
        last_seen_packet_id=coerce_string(draft.last_seen_packet_id),
        last_acknowledged_packet_id=coerce_string(
            draft.last_acknowledged_packet_id
        ),
        current_assignment=coerce_string(draft.current_assignment),
        dirty_paths_count=dirty_count,
        dirty_paths_status=dirty_status,
        current_blockers=blockers,
        resume_command=coerce_string(draft.resume_command),
        bootstrap_hash=coerce_string(draft.bootstrap_hash),
        continuation_mode=_continuation_mode(draft.continuation_mode),
        generated_at_utc=coerce_string(draft.generated_at_utc),
        authority_result=_authority_result(
            draft.authority_result,
            current_blockers=blockers,
            dirty_paths_status_value=dirty_status,
        ),
        result=resume_result(draft.result, default=CONTINUATION_RESULT_EXPECTED),
    )
    state_hash = continuation_hash(state.to_dict())
    return AgentSessionContinuationState(
        **{
            **state.to_dict(),
            "continuation_id": f"agent_continuation:{state_hash[:16]}",
            "continuation_hash": state_hash,
        }
    )


def build_agent_resume_receipt(
    continuation: AgentSessionContinuationState,
    draft: AgentResumeReceiptDraft | None = None,
    **values: object,
) -> AgentResumeReceiptState:
    """Build the event/log row proving one continuation was loaded.

    When both ``draft`` and keyword values are supplied, keyword values
    deliberately override the draft before the final receipt is built.
    Unknown keyword fields fail closed.
    """
    draft = _resume_receipt_draft(draft, values)
    provider_text = coerce_string(draft.provider) or continuation.provider
    agent_text = coerce_string(draft.agent_id) or continuation.agent_id or provider_text
    session_ref = (
        coerce_string(draft.session_id_or_transcript_path)
        or continuation.session_id_or_transcript_path
    )
    receipt = AgentResumeReceiptState(
        continuation_id=continuation.continuation_id,
        agent_id=agent_text,
        provider=provider_text or agent_text,
        role=continuation.role,
        working_tree=continuation.working_tree,
        branch=continuation.branch,
        session_id_or_transcript_path=session_ref,
        last_seen_packet_id=continuation.last_seen_packet_id,
        last_acknowledged_packet_id=continuation.last_acknowledged_packet_id,
        current_assignment=continuation.current_assignment,
        dirty_paths_count=continuation.dirty_paths_count,
        dirty_paths_status=continuation.dirty_paths_status,
        current_blockers=continuation.current_blockers,
        resume_command=continuation.resume_command,
        continuation_hash=continuation.continuation_hash,
        bootstrap_hash=continuation.bootstrap_hash,
        continuation_mode=continuation.continuation_mode,
        started_at_utc=coerce_string(draft.started_at_utc)
        or continuation.generated_at_utc,
        observed_at_utc=coerce_string(draft.observed_at_utc),
        load_result=resume_result(draft.result, default=RESUME_RESULT_LOADED),
        authority_result=_authority_result(
            draft.authority_result or continuation.authority_result,
            current_blockers=continuation.current_blockers,
            dirty_paths_status_value=continuation.dirty_paths_status,
        ),
        result=resume_result(draft.result, default=RESUME_RESULT_LOADED),
        source=coerce_string(draft.source) or "session-resume",
    )
    receipt_hash = resume_receipt_hash(receipt.to_dict())
    return AgentResumeReceiptState(
        **{
            **receipt.to_dict(),
            "receipt_id": f"agent_resume:{receipt_hash[:16]}",
        }
    )


def _continuation_draft(
    draft: AgentSessionContinuationDraft | None,
    values: dict[str, object],
) -> AgentSessionContinuationDraft:
    return _replace_known_fields(draft or AgentSessionContinuationDraft(), values)


def _resume_receipt_draft(
    draft: AgentResumeReceiptDraft | None,
    values: dict[str, object],
) -> AgentResumeReceiptDraft:
    return _replace_known_fields(draft or AgentResumeReceiptDraft(), values)


def _replace_known_fields(draft: Any, values: dict[str, object]) -> Any:
    return draft.with_values(values)


__all__ = [
    "AgentResumeReceiptDraft",
    "AgentSessionContinuationDraft",
    "build_agent_resume_receipt",
    "build_agent_session_continuation",
]
