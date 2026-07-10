"""Agent-session continuation builders for session-resume packets."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import TYPE_CHECKING

from ...runtime.agent_session_continuation_build import (
    build_agent_session_continuation,
)
from ...runtime.agent_session_continuation_models import (
    CONTINUATION_MODE_TYPED_REHYDRATION,
    AgentSessionContinuationState,
)
from ...time_utils import utc_timestamp
from .session_resume_continuation_identity import (
    agent_id_for_role as _agent_id_for_role,
    authority_text as _authority_text,
    resume_receipt_command as _resume_receipt_command,
)
from .session_resume_continuation_packets import (
    last_acknowledged_packet_id as _last_acknowledged_packet_id,
    last_seen_packet_id as _last_seen_packet_id,
)
from .session_resume_continuation_sessions import (
    session_ref_for_agent as _session_ref_for_agent,
)
from .session_resume_context_values import replace_context_values

if TYPE_CHECKING:
    from ...runtime.authority_snapshot import AuthoritySnapshot
    from ...runtime.review_state_models import PacketInboxState, ReviewState


@dataclass(frozen=True)
class SessionResumeContinuationContext:
    repo_root: Path
    role: str
    branch: str
    authority_snapshot: "AuthoritySnapshot | None"
    packet_inbox: "PacketInboxState | None"
    typed_review_state: "ReviewState | None"
    current_instruction: str
    blockers: str
    changed_paths: Sequence[str] | None = None


def build_agent_session_continuation_for_resume(
    context: SessionResumeContinuationContext | None = None,
    **values: object,
) -> AgentSessionContinuationState:
    """Build the typed rehydration state embedded in SessionCachePacket.

    When both ``context`` and keyword values are supplied, keyword values
    override the context. Unknown keyword fields fail closed before any
    authority state is emitted.
    """
    context = replace_context_values(
        context,
        values,
        context_type=SessionResumeContinuationContext,
        label="session continuation",
    )
    agent_id = _agent_id_for_role(
        role=context.role,
        authority_snapshot=context.authority_snapshot,
    )
    session_ref = _session_ref_for_agent(
        typed_review_state=context.typed_review_state,
        agent_id=agent_id,
        role=context.role,
    )
    dirty_paths_count, dirty_paths_status = _dirty_paths_state(
        context.repo_root,
        changed_paths=context.changed_paths,
    )
    current_blockers = _blockers_with_dirty_state(
        context.blockers,
        dirty_paths_status=dirty_paths_status,
    )
    return build_agent_session_continuation(
        agent_id=agent_id,
        provider=agent_id,
        role=context.role,
        working_tree=str(context.repo_root),
        branch=context.branch,
        session_id_or_transcript_path=session_ref,
        last_seen_packet_id=_last_seen_packet_id(
            packet_inbox=context.packet_inbox,
            agent_id=agent_id,
        ),
        last_acknowledged_packet_id=_last_acknowledged_packet_id(
            typed_review_state=context.typed_review_state,
            agent_id=agent_id,
        ),
        current_assignment=(
            context.current_instruction
            or _authority_text(context.authority_snapshot, "current_slice")
            or _coordination_current_slice(context.typed_review_state)
        ),
        dirty_paths_count=dirty_paths_count,
        dirty_paths_status=dirty_paths_status,
        current_blockers=current_blockers,
        resume_command=_resume_receipt_command(role=context.role, provider=agent_id),
        continuation_mode=CONTINUATION_MODE_TYPED_REHYDRATION,
        generated_at_utc=utc_timestamp(),
        result="expected",
    )


def _coordination_current_slice(typed_review_state: "ReviewState | None") -> str:
    if typed_review_state is None:
        return ""
    coordination = getattr(typed_review_state, "coordination", None)
    return str(getattr(coordination, "current_slice", "") or "").strip()


def _dirty_paths_state(
    repo_root: Path,
    *,
    changed_paths: Sequence[str] | None,
) -> tuple[int, str]:
    if changed_paths is not None:
        return len(tuple(path for path in changed_paths if str(path).strip())), "known"
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return -1, "unknown"
    if result.returncode != 0:
        return -1, "unknown"
    return len([line for line in result.stdout.splitlines() if line.strip()]), "known"


def _blockers_with_dirty_state(
    blockers: str,
    *,
    dirty_paths_status: str,
) -> str:
    parts = [
        token.strip()
        for token in str(blockers or "none").split(",")
        if token.strip() and token.strip() != "none"
    ]
    if dirty_paths_status == "unknown" and "dirty_paths_unknown" not in parts:
        parts.append("dirty_paths_unknown")
    return ",".join(parts) if parts else "none"


__all__ = [
    "SessionResumeContinuationContext",
    "build_agent_session_continuation_for_resume",
]
