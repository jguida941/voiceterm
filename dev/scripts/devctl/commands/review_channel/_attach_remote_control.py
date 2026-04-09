"""Persist external remote-control session attachment state."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

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

    existing = load_remote_control_attachment(output_root=status_dir)
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
    now = utc_timestamp()
    provider = str(getattr(args, "remote_provider", "claude") or "claude").strip()
    role = str(getattr(args, "remote_role", "implementer") or "implementer").strip()
    status = str(getattr(args, "attachment_status", "attached") or "attached").strip()
    session_name = str(getattr(args, "session_name", "") or "").strip()
    remote_session_id = str(getattr(args, "remote_session_id", "") or "").strip()
    session_url = str(getattr(args, "session_url", "") or "").strip()
    if not remote_session_id:
        remote_session_id = _session_id_from_url(session_url)
    metadata_path = str(getattr(args, "metadata_path", "") or "").strip()

    if existing is not None:
        if not session_name:
            session_name = existing.session_name
        if not remote_session_id:
            remote_session_id = existing.remote_session_id
        if not session_url:
            session_url = existing.session_url
        if not metadata_path:
            metadata_path = existing.metadata_path

    attached_at_utc = now
    attachment_id = f"remote-attach-{_slugify_timestamp(now)}"
    if existing is not None:
        # Identity matches on remote_session_id or session_url only. session_name
        # is a human display label and must never conflate distinct sessions
        # that happen to share the same bridge loop label.
        same_attachment = existing.provider == provider and (
            (remote_session_id and existing.remote_session_id == remote_session_id)
            or (session_url and existing.session_url == session_url)
        )
        if same_attachment:
            attachment_id = existing.attachment_id or attachment_id
            attached_at_utc = existing.attached_at_utc or now

    return RemoteControlAttachmentState(
        provider=provider,
        role=role,
        attachment_id=attachment_id,
        session_name=session_name,
        remote_session_id=remote_session_id,
        session_url=session_url,
        status=status,
        transport="review_channel_artifact",
        attached_at_utc=attached_at_utc,
        last_seen_utc=now,
        metadata_path=metadata_path,
    )


def _session_id_from_url(session_url: str) -> str:
    """Extract the trailing session_<id> segment from a remote session URL.

    Query strings and fragments are stripped before tail extraction so URLs
    like ``https://claude.ai/code/session_abc?foo=1`` resolve correctly.
    """
    trimmed = str(session_url or "").strip()
    if not trimmed:
        return ""
    path = urlparse(trimmed).path.rstrip("/")
    if not path:
        return ""
    tail = path.rsplit("/", 1)[-1]
    return tail if tail.startswith("session_") else ""


def _slugify_timestamp(value: str) -> str:
    """Collapse an ISO-8601 timestamp into a filesystem-safe slug.

    Keeps the ``T`` and ``Z`` anchors so the resulting id is still readable
    (e.g. ``20260409T131415Z``) while stripping separators that are awkward
    in filenames and attachment ids.
    """
    return (
        str(value or "")
        .replace("-", "")
        .replace(":", "")
        .replace(".", "")
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
    return payload
