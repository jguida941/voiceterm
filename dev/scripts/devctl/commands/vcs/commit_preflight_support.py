"""Shared command strings and guidance for governed commit preflight."""

from __future__ import annotations

from dataclasses import dataclass

from ...runtime.operator_context import (
    OperatorInteractionMode,
    operator_mode_allows_commit_self_approval,
    resolve_operator_interaction_mode,
)
from ...runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    has_active_remote_control_attachment,
)
from ...runtime.role_profile import TandemRole, normalize_tandem_role

COMMIT_START_COMMAND = 'python3 dev/scripts/devctl.py commit -m "<descriptive message>"'
APPROVE_PENDING_COMMAND = (
    "python3 dev/scripts/devctl.py commit --approve-pending --format json"
)
OPERATOR_INBOX_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action operator-inbox "
    "--status pending --terminal none --format json"
)
OPERATOR_HISTORY_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action history "
    "--target operator --limit 5 --terminal none --format json"
)


@dataclass(frozen=True, slots=True)
class CommitApprovalAuthority:
    """Typed approval decision for one governed commit attempt."""

    interaction_mode: str = OperatorInteractionMode.UNRESOLVED.value
    approval_actor: str = "operator"
    auto_approve: bool = False
    authority_reason: str = ""


def next_command_guidance(next_command: str) -> str:
    """Render operator guidance directly from a typed next command."""
    if not next_command:
        return ""
    return f"Run `{next_command}` next."


def build_commit_approval_authority(
    *,
    interaction_mode: str,
    remote_control_attachment: RemoteControlAttachmentState | None = None,
) -> CommitApprovalAuthority:
    """Return the typed approval authority for one governed commit attempt."""
    mode = resolve_operator_interaction_mode(str(interaction_mode or "").strip()).value
    if operator_mode_allows_commit_self_approval(mode):
        return CommitApprovalAuthority(
            interaction_mode=mode,
            approval_actor="operator",
            auto_approve=True,
            authority_reason=f"{mode}_self_approval",
        )

    if mode == OperatorInteractionMode.REMOTE_CONTROL.value:
        attachment = remote_control_attachment
        attachment_provider = str(
            getattr(attachment, "provider", "") or ""
        ).strip().lower()
        attachment_role = normalize_tandem_role(
            getattr(attachment, "role", "") or ""
        )
        if (
            has_active_remote_control_attachment(attachment)
            and attachment_role == TandemRole.OPERATOR
            and attachment_provider
        ):
            return CommitApprovalAuthority(
                interaction_mode=mode,
                approval_actor=attachment_provider,
                auto_approve=True,
                authority_reason="remote_control_operator_delegate",
            )

    return CommitApprovalAuthority(
        interaction_mode=mode,
        approval_actor="operator",
        auto_approve=False,
        authority_reason=f"{mode}_explicit_approval_required",
    )


def should_auto_approve(authority: CommitApprovalAuthority) -> bool:
    """Return True when typed approval authority already exists for this mode."""
    return authority.auto_approve
