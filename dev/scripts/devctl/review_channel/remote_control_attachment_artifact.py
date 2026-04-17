"""Helpers for the external remote-control attachment artifact."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

from ..runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    has_active_remote_control_attachment,
    remote_control_attachment_from_mapping,
)
from ..time_utils import utc_timestamp


# Default provider preserves the legacy "claude-remote-control.json" filename so
# existing artifacts continue to load without migration.
DEFAULT_REMOTE_CONTROL_PROVIDER = "claude"
REMOTE_CONTROL_ATTACHMENT_FILENAME_SUFFIX = "-remote-control.json"
# Retained for backwards-compat consumers that reference the legacy filename.
REMOTE_CONTROL_ATTACHMENT_FILENAME = (
    f"{DEFAULT_REMOTE_CONTROL_PROVIDER}{REMOTE_CONTROL_ATTACHMENT_FILENAME_SUFFIX}"
)


def _normalize_provider(provider: str | None) -> str:
    """Return a non-empty provider slug, falling back to the default."""
    value = str(provider or "").strip().lower()
    return value or DEFAULT_REMOTE_CONTROL_PROVIDER


def remote_control_attachment_filename(provider: str | None) -> str:
    """Return the provider-scoped artifact filename."""
    return f"{_normalize_provider(provider)}{REMOTE_CONTROL_ATTACHMENT_FILENAME_SUFFIX}"


def remote_control_attachment_path(
    *,
    output_root: Path,
    provider: str | None = DEFAULT_REMOTE_CONTROL_PROVIDER,
) -> Path:
    """Return the canonical sidecar path for a provider's remote session."""
    return output_root / "sessions" / remote_control_attachment_filename(provider)


def _read_attachment_file(artifact_path: Path) -> RemoteControlAttachmentState | None:
    if not artifact_path.exists():
        return None
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    attachment = remote_control_attachment_from_mapping(payload)
    if attachment is None:
        return None
    return replace(attachment, metadata_path=str(artifact_path))


def _scan_provider_attachments(
    sessions_dir: Path,
) -> list[RemoteControlAttachmentState]:
    if not sessions_dir.is_dir():
        return []
    attachments: list[RemoteControlAttachmentState] = []
    for path in sorted(sessions_dir.glob(f"*{REMOTE_CONTROL_ATTACHMENT_FILENAME_SUFFIX}")):
        loaded = _read_attachment_file(path)
        if loaded is not None:
            attachments.append(loaded)
    return attachments


def _select_preferred_attachment(
    attachments: list[RemoteControlAttachmentState],
) -> RemoteControlAttachmentState | None:
    if not attachments:
        return None
    active = [a for a in attachments if has_active_remote_control_attachment(a)]
    pool = active or attachments
    # Prefer the most recently seen record so the newest live session wins when
    # multiple providers share the same status_dir.
    pool_sorted = sorted(
        pool,
        key=lambda a: (a.last_seen_utc or "", a.attached_at_utc or ""),
        reverse=True,
    )
    return pool_sorted[0]


def load_remote_control_attachment(
    *,
    output_root: Path,
    provider: str | None = None,
) -> RemoteControlAttachmentState | None:
    """Load a remote-control attachment artifact when present.

    When ``provider`` is supplied, only that provider's file is considered.
    Otherwise the sessions directory is scanned for any provider file and the
    most recently active attachment wins so legacy single-provider callers
    keep working and multi-provider callers see every attachment.
    """
    if provider is not None:
        return _read_attachment_file(
            remote_control_attachment_path(output_root=output_root, provider=provider)
        )
    return _select_preferred_attachment(
        _scan_provider_attachments(output_root / "sessions")
    )


def load_remote_control_attachments(
    *,
    output_root: Path,
    active_only: bool = False,
) -> tuple[RemoteControlAttachmentState, ...]:
    """Return every provider-scoped remote-control attachment under sessions/."""
    attachments = _scan_provider_attachments(output_root / "sessions")
    if active_only:
        attachments = [
            attachment
            for attachment in attachments
            if has_active_remote_control_attachment(attachment)
        ]
    return tuple(attachments)


def persist_remote_control_attachment(
    attachment: RemoteControlAttachmentState,
    *,
    output_root: Path,
) -> Path:
    """Write the provider-scoped remote-control attachment artifact."""
    artifact_path = remote_control_attachment_path(
        output_root=output_root, provider=attachment.provider
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = replace(attachment, metadata_path=str(artifact_path))
    artifact_path.write_text(
        json.dumps(asdict(payload), indent=2) + "\n",
        encoding="utf-8",
    )
    return artifact_path


def heartbeat_repo_remote_control_attachment(
    *,
    repo_root: Path,
    provider: str | None,
    seen_at_utc: str | None = None,
) -> Path | None:
    """Refresh `last_seen_utc` for an active repo-owned remote attachment."""
    from ..repo_packs import active_path_config

    normalized_provider = _normalize_provider(provider)
    output_root = repo_root / active_path_config().review_status_dir_rel
    attachment = load_remote_control_attachment(
        output_root=output_root,
        provider=normalized_provider,
    )
    if attachment is None or not has_active_remote_control_attachment(attachment):
        return None
    timestamp = str(seen_at_utc or "").strip() or utc_timestamp()
    return persist_remote_control_attachment(
        replace(attachment, last_seen_utc=timestamp),
        output_root=output_root,
    )


def deactivate_remote_control_attachments(
    *,
    output_root: Path,
    status: str = "detached",
) -> tuple[Path, ...]:
    """Downgrade persisted attachments so they no longer drive runtime mode."""
    normalized_status = str(status or "detached").strip().lower() or "detached"
    updated_paths: list[Path] = []
    for attachment in _scan_provider_attachments(output_root / "sessions"):
        current_status = str(attachment.status or "").strip().lower()
        if current_status == normalized_status:
            continue
        updated_paths.append(
            persist_remote_control_attachment(
                replace(attachment, status=normalized_status),
                output_root=output_root,
            )
        )
    return tuple(updated_paths)


def deactivate_repo_remote_control_attachments(
    *,
    repo_root: Path,
    status: str = "detached",
) -> tuple[Path, ...]:
    """Downgrade attachment artifacts under the governed review status root."""
    from ..repo_packs import active_path_config

    config = active_path_config()
    output_root = repo_root / config.review_status_dir_rel
    if not output_root.exists():
        return ()
    return deactivate_remote_control_attachments(
        output_root=output_root,
        status=status,
    )
