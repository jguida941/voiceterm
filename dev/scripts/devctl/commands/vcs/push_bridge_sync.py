"""Review bridge projection refresh before governed push preflight."""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from ...repo_packs import active_path_config
from ...review_channel.core import bridge_is_active
from ...review_channel.state import refresh_status_snapshot
from ..review_channel.status_bridge_sync import (
    sync_bridge_from_typed_projection_if_needed as _sync_bridge_from_typed_projection_if_needed,
)
from .push_review_snapshot_receipt_guard import (
    current_head_is_managed_review_snapshot_receipt,
)


def sync_bridge_projection_before_preflight(
    state,
    *,
    repo_root: Path = REPO_ROOT,
) -> None:
    """Refresh `bridge.md` from typed review state before routed preflight runs."""
    if current_head_is_managed_review_snapshot_receipt(repo_root=repo_root):
        return
    config = active_path_config()
    bridge_path = repo_root / config.bridge_rel
    review_channel_path = repo_root / config.review_channel_rel
    status_dir = repo_root / config.review_status_dir_rel
    if not bridge_path.is_file() or not review_channel_path.is_file():
        return
    try:
        review_channel_text = review_channel_path.read_text(encoding="utf-8")
    except OSError as exc:
        state.warnings.append(
            "push preflight skipped bridge sync because review-channel state "
            f"could not be read: {exc}"
        )
        return

    if not bridge_is_active(review_channel_text):
        return

    try:
        snapshot = refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=status_dir,
            execution_mode="markdown-bridge",
            warnings=[],
            errors=[],
        )
        bridge_synced, sync_warning = _sync_bridge_from_typed_projection_if_needed(
            repo_root=repo_root,
            bridge_path=bridge_path,
            snapshot=snapshot,
        )
    except (OSError, ValueError) as exc:
        state.warnings.append(
            "push preflight skipped bridge sync because the typed review "
            f"projection could not be refreshed: {exc}"
        )
        return

    if sync_warning:
        state.warnings.append(sync_warning)
    if bridge_synced:
        state.warnings.append(
            "Synchronized `bridge.md` from typed review-state before push preflight."
        )


__all__ = ["sync_bridge_projection_before_preflight"]
