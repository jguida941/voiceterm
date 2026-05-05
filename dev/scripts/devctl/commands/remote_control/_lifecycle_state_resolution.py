"""Lifecycle status + before-state resolution helpers for remote-control.

Per rev_pkt_2996 + rev_pkt_3003 the ``remote-control`` lifecycle action
must (a) fail closed when no current session identity is provable and
(b) carry a typed before-state into every receipt so a reader can prove
whether the call mutated the typed attachment. Extracted from
``command.py`` to keep that module under the shape budget.
"""

from __future__ import annotations

from typing import Any

from ...runtime.remote_control_attachment_status import (
    SYNTHETIC_REMOTE_SESSION_ID_PREFIXES,
    remote_attachment_active,
    remote_attachment_has_physical_identity,
)
from ...runtime.reviewer_runtime_models import RemoteControlAttachmentState
from ._invocation_logging import LifecycleBeforeState

EVIDENCE_MISSING_STATUS = "evidence_missing"
TRUSTED_REFRESH_SOURCE_KINDS = frozenset(
    {"claude_builtin_slash", "claude_project_slash"}
)
TRUSTED_REFRESH_PROOF_CHANNELS = frozenset(
    {
        "claude_agent_mind_attribution",
        "claude_agent_mind_remote_control_bridge_status",
        "claude_hook",
        "claude_session_state",
    }
)


def has_remote_identity(args: Any) -> bool:
    """True when the caller passed --remote-session-id or --session-url."""
    session_url = str(getattr(args, "session_url", "") or "").strip()
    if session_url:
        return True
    remote_session_id = str(getattr(args, "remote_session_id", "") or "").strip()
    if remote_session_id and not remote_session_id.startswith(
        SYNTHETIC_REMOTE_SESSION_ID_PREFIXES
    ):
        return True
    return False


def has_proven_refresh_source(args: Any) -> bool:
    """True when a lifecycle call proves physical remote-control transport."""
    source_kind = str(getattr(args, "proven_source_kind", "") or "").strip()
    if source_kind not in TRUSTED_REFRESH_SOURCE_KINDS:
        return False
    provider_session_id = str(
        getattr(args, "provider_session_id", "") or ""
    ).strip()
    if not provider_session_id.startswith("claude-code:"):
        return False
    proof_channel = str(getattr(args, "source_proof_channel", "") or "").strip()
    return proof_channel in TRUSTED_REFRESH_PROOF_CHANNELS


def resolve_lifecycle_attachment_status(
    args: Any,
    *,
    current: RemoteControlAttachmentState | None,
) -> str:
    """Decide the attachment ``status`` to upsert for one lifecycle call.

    Per rev_pkt_2996 finding #1: a slash invocation with no remote-session
    identity must NOT promote ``operator_interaction_mode=remote_control``
    by writing ``status="unknown"`` (which the runtime treats as active).
    Resolution order:

    1. Caller passes ``--remote-session-id`` or ``--session-url`` -> the
       caller is proving a current remote session ``-> attached``.
    2. Else, an existing identity-bound attachment is still active AND this
       lifecycle call has non-flag proof of a provider-owned refresh source
       ``-> attached`` (identity is inherited from the existing record by the
       shared builder under ``refresh_existing_identity=True``).
    3. Otherwise the call has no identity evidence ``-> evidence_missing``,
       which is NOT in ``ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES`` so
       mode derivation fails closed to ``local_terminal``.
    """
    if has_remote_identity(args):
        return "attached"
    if (
        current is not None
        and has_proven_refresh_source(args)
        and remote_attachment_active(current)
        and (
            remote_attachment_has_physical_identity(current)
        )
    ):
        return "attached"
    return EVIDENCE_MISSING_STATUS


def before_state_from_report(report: dict[str, Any]) -> LifecycleBeforeState:
    """Snapshot pre-invocation state from a fresh ``_status_report`` payload."""
    attachment = report.get("attachment") if isinstance(report, dict) else None
    if not isinstance(attachment, dict):
        attachment = {}
    return LifecycleBeforeState(
        attachment_status=str(attachment.get("status") or "").strip(),
        attachment_id=str(attachment.get("attachment_id") or "").strip(),
        operator_interaction_mode=str(
            report.get("operator_interaction_mode") or ""
        ).strip(),
    )


def before_state_from_attachment(
    attachment: RemoteControlAttachmentState | None,
) -> LifecycleBeforeState:
    """Snapshot pre-invocation state directly from a typed attachment."""
    if attachment is None:
        return LifecycleBeforeState()
    return LifecycleBeforeState(
        attachment_status=(attachment.status or "").strip(),
        attachment_id=(attachment.attachment_id or "").strip(),
        operator_interaction_mode=(
            "remote_control" if remote_attachment_active(attachment) else "local_terminal"
        ),
    )


__all__ = [
    "EVIDENCE_MISSING_STATUS",
    "before_state_from_attachment",
    "before_state_from_report",
    "has_remote_identity",
    "has_proven_refresh_source",
    "resolve_lifecycle_attachment_status",
]
