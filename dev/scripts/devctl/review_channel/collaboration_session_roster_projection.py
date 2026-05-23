"""Participant-projection helpers for collaboration-session roster."""

from __future__ import annotations

from ..runtime.review_state_models import CollaborationParticipantState
from ..runtime.reviewer_runtime_models import RemoteControlAttachmentState
from ..runtime.role_profile import normalize_role_id
from .session_probe import ConductorSessionRecord
from .collaboration_session_roster_lookup import text


def primary_lane_fields(record: ConductorSessionRecord) -> tuple[str, str, str, str]:
    if not record.planned_lanes:
        return "", "", "", ""
    lane = record.planned_lanes[0]
    return (
        text(lane.get("lane")),
        text(lane.get("mp_scope")),
        text(lane.get("worktree")),
        text(lane.get("branch")),
    )


def participant_from_record(
    record: ConductorSessionRecord,
    *,
    attachment: RemoteControlAttachmentState | None,
) -> CollaborationParticipantState:
    lane_title, mp_scope, worktree, branch = primary_lane_fields(record)
    workspace_root = record.workspace_root or record.repo_root
    worktree_identity = worktree or workspace_root
    branch_name = branch or record.current_branch
    if attachment is None:
        return CollaborationParticipantState(
            agent_id=record.provider,
            provider=record.provider,
            display_name=record.provider_name,
            role=normalize_role_id(record.role),
            session_name=record.session_name,
            live=record.live,
            status="live" if record.live else "configured",
            capture_mode=record.capture_mode,
            approval_mode=record.approval_mode,
            supervision_mode=record.supervision_mode,
            prepared_at=record.prepared_at,
            metadata_path=record.metadata_path,
            log_path=record.log_path,
            launch_command=record.launch_command,
            requested_worker_budget=record.requested_worker_budget,
            planned_lane_count=record.planned_lane_count,
            lane=lane_title,
            mp_scope=mp_scope,
            worktree=worktree_identity,
            branch=branch_name,
            workspace_root=workspace_root,
        )
    return CollaborationParticipantState(
        agent_id=record.provider,
        provider=record.provider,
        display_name=record.provider_name,
        role=normalize_role_id(attachment.role or record.role),
        session_name=attachment.session_name or record.session_name or f"{record.provider}-remote-control",
        live=True,
        status="live",
        capture_mode="remote-control",
        approval_mode=record.approval_mode,
        supervision_mode="remote-control",
        prepared_at=attachment.attached_at_utc or record.prepared_at,
        metadata_path=attachment.metadata_path or record.metadata_path,
        log_path=record.log_path,
        launch_command=attachment.session_url or record.launch_command,
        requested_worker_budget=record.requested_worker_budget,
        planned_lane_count=record.planned_lane_count,
        lane=lane_title,
        mp_scope=mp_scope,
        worktree=worktree_identity,
        branch=branch_name,
        workspace_root=workspace_root,
    )


def participant_from_attachment(
    attachment: RemoteControlAttachmentState,
) -> CollaborationParticipantState:
    provider = attachment.provider or "remote"
    return CollaborationParticipantState(
        agent_id=provider,
        provider=provider,
        display_name=provider.title(),
        role=normalize_role_id(attachment.role),
        session_name=attachment.session_name or f"{provider}-remote-control",
        live=True,
        status="live",
        capture_mode="remote-control",
        approval_mode="balanced",
        supervision_mode="remote-control",
        prepared_at=attachment.attached_at_utc,
        metadata_path=attachment.metadata_path,
        log_path="",
        launch_command=attachment.session_url,
        requested_worker_budget=0,
        planned_lane_count=0,
        workspace_root="",
    )


def planned_lane_role(lane: dict[str, object], *, provider: str) -> str:
    return normalize_role_id(
        lane.get("role")
        or lane.get("role_id")
        or lane.get("role_preset")
        or lane.get("target_role")
    )
