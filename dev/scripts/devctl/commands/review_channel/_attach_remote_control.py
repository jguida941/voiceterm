"""Persist external remote-control session attachment state."""

from __future__ import annotations

from pathlib import Path

from ...runtime.remote_control_attachment_builder import (
    RemoteControlAttachmentBuildInput,
    build_remote_control_attachment_state,
)
from ...runtime.remote_control_attachment_models import int_or_none
from ..remote_control._lifecycle_state_resolution import (
    has_remote_identity,
    resolve_lifecycle_attachment_status,
)
from ...review_channel.remote_control_attachment_artifact import (
    load_remote_control_attachment,
    persist_remote_control_attachment,
)
from ...review_channel.state import refresh_status_snapshot
from ...runtime.reviewer_runtime_models import RemoteControlAttachmentState
from ...time_utils import utc_timestamp
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths


def run_attach_remote_control_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | dict[str, object],
) -> tuple[dict[str, object], int]:
    """Write the remote-control attachment artifact and refresh typed status."""
    runtime_paths = _coerce_runtime_paths(paths)
    status_dir = runtime_paths.status_dir
    if not isinstance(status_dir, Path):
        raise ValueError(
            "review-channel attach-remote-control requires a resolved --status-dir."
        )

    # Per rev_pkt_2996 finding #6: load existing scoped to the requested
    # provider so a future non-Claude attach call doesn't inherit identity
    # from a Claude attachment artifact (or vice versa). Without this scope,
    # the artifact loader picks the most recent attachment of any provider,
    # which composes wrong with cross-provider identity guarding.
    requested_provider = str(
        getattr(args, "remote_provider", "claude") or "claude"
    )
    existing = load_remote_control_attachment(
        output_root=status_dir,
        provider=requested_provider,
    )
    attachment = _build_attachment(args=args, existing=existing)
    artifact_path = persist_remote_control_attachment(attachment, output_root=status_dir)
    refreshed = False
    refreshed_snapshot_id = ""
    bridge_path = runtime_paths.bridge_path
    review_channel_path = runtime_paths.review_channel_path
    if (
        isinstance(bridge_path, Path)
        and isinstance(review_channel_path, Path)
        and bridge_path.exists()
        and review_channel_path.exists()
    ):
        snapshot = refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=status_dir,
            promotion_plan_path=runtime_paths.promotion_plan_path,
            execution_mode=getattr(args, "execution_mode", "markdown-bridge"),
            warnings=[],
            errors=[],
        )
        refreshed = True
        review_state = snapshot.review_state
        if review_state is not None:
            refreshed_snapshot_id = str(review_state.snapshot_id or "").strip()
            reviewer_runtime = review_state.reviewer_runtime
            if reviewer_runtime.remote_control_attachment is not None:
                attachment = reviewer_runtime.remote_control_attachment

    report = _build_report(
        attachment=attachment,
        artifact_path=artifact_path,
        refreshed=refreshed,
        refreshed_snapshot_id=refreshed_snapshot_id,
    )
    return report, 0


def _build_attachment(
    *,
    args,
    existing: RemoteControlAttachmentState | None,
) -> RemoteControlAttachmentState:
    """Thin adapter: map review-channel argparse fields to the shared builder.

    Per rev_pkt_2986 finding #2: identity guard, ``session_url`` parsing,
    fallback merge order, and TTL handling now live in
    ``runtime.remote_control_attachment_models.build_remote_control_attachment_state``
    so this helper and ``commands/remote_control/command._persist_attachment``
    share one canonical body.
    """
    requested_status = str(
        getattr(args, "attachment_status", "attached") or "attached"
    ).strip()
    status = (
        resolve_lifecycle_attachment_status(
            args,
            current=existing,
        )
        if requested_status == "attached"
        else requested_status
    )
    refresh_existing_identity = (
        status == "attached"
        and not has_remote_identity(args)
        and existing is not None
        and bool(
            (existing.remote_session_id or "").strip()
            or (existing.session_url or "").strip()
        )
    )
    return build_remote_control_attachment_state(
        RemoteControlAttachmentBuildInput(
            now_utc=utc_timestamp(),
            provider=str(getattr(args, "remote_provider", "claude") or "claude"),
            role=str(getattr(args, "remote_role", "operator") or "operator"),
            status=status,
            session_name=str(getattr(args, "session_name", "") or ""),
            remote_session_id=str(getattr(args, "remote_session_id", "") or ""),
            session_url=str(getattr(args, "session_url", "") or ""),
            metadata_path=str(getattr(args, "metadata_path", "") or ""),
            launcher_source=str(getattr(args, "launcher_source", "") or ""),
            host_pid=int_or_none(getattr(args, "host_pid", None)),
            host_session_label=str(getattr(args, "host_session_label", "") or ""),
            heartbeat_ttl_seconds=getattr(args, "heartbeat_ttl_seconds", None),
            previous_operator_mode=str(
                getattr(args, "previous_operator_mode", "") or ""
            ),
            entrypoint=str(getattr(args, "entrypoint", "") or ""),
            existing=existing,
            refresh_existing_identity=refresh_existing_identity,
        ),
    )


def _build_report(
    *,
    attachment: RemoteControlAttachmentState,
    artifact_path: Path,
    refreshed: bool,
    refreshed_snapshot_id: str,
) -> dict[str, object]:
    report: dict[str, object] = {}
    report["command"] = "review-channel"
    report["action"] = "attach-remote-control"
    report["ok"] = True
    report["attachment"] = _attachment_payload(attachment)
    report["artifact_path"] = str(artifact_path)
    report["status_refreshed"] = refreshed
    report["snapshot_id"] = refreshed_snapshot_id
    return report


def _attachment_payload(
    attachment: RemoteControlAttachmentState,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["provider"] = attachment.provider
    payload["role"] = attachment.role
    payload["attachment_id"] = attachment.attachment_id
    payload["session_name"] = attachment.session_name
    payload["remote_session_id"] = attachment.remote_session_id
    payload["session_url"] = attachment.session_url
    payload["status"] = attachment.status
    payload["transport"] = attachment.transport
    payload["attached_at_utc"] = attachment.attached_at_utc
    payload["last_seen_utc"] = attachment.last_seen_utc
    payload["metadata_path"] = attachment.metadata_path
    payload["launcher_source"] = attachment.launcher_source
    payload["host_pid"] = attachment.host_pid
    payload["host_session_label"] = attachment.host_session_label
    payload["heartbeat_ttl_seconds"] = attachment.heartbeat_ttl_seconds
    payload["previous_operator_mode"] = attachment.previous_operator_mode
    payload["entrypoint"] = attachment.entrypoint
    return payload
