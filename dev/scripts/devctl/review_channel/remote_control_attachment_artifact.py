"""Helpers for the external remote-control attachment artifact."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

from ..runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    remote_control_attachment_from_mapping,
)


REMOTE_CONTROL_ATTACHMENT_FILENAME = "claude-remote-control.json"


def remote_control_attachment_path(*, output_root: Path) -> Path:
    """Return the canonical sidecar path for the external remote session."""
    return output_root / "sessions" / REMOTE_CONTROL_ATTACHMENT_FILENAME


def load_remote_control_attachment(
    *,
    output_root: Path,
) -> RemoteControlAttachmentState | None:
    """Load the canonical remote-control attachment artifact when present."""
    artifact_path = remote_control_attachment_path(output_root=output_root)
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


def persist_remote_control_attachment(
    attachment: RemoteControlAttachmentState,
    *,
    output_root: Path,
) -> Path:
    """Write the canonical remote-control attachment artifact and return its path."""
    artifact_path = remote_control_attachment_path(output_root=output_root)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = replace(attachment, metadata_path=str(artifact_path))
    artifact_path.write_text(
        json.dumps(asdict(payload), indent=2) + "\n",
        encoding="utf-8",
    )
    return artifact_path
