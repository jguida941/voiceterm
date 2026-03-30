"""Reset implementer-owned bridge sections to the canonical pending state."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from ...review_channel.bridge_file import rewrite_bridge_markdown
from ...review_channel.instruction_reset import reset_implementer_sections
from ...review_channel.reviewer_state import _refresh_projections_after_checkpoint
from ...review_channel.reviewer_state_support import (
    current_instruction_revision_from_bridge_text,
)
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths


def run_reset_implementer_state_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    run_status_action_fn: Callable[..., tuple[dict[str, object], int]],
) -> tuple[dict[str, object], int]:
    """Rewrite Claude-owned bridge sections to the canonical pending state."""
    runtime_paths = _coerce_runtime_paths(paths)
    bridge_path = runtime_paths.bridge_path
    if bridge_path is None:
        raise ValueError(
            "review-channel reset-implementer-state requires a resolved bridge path."
        )

    changed = False
    current_instruction_revision = ""

    def transform(bridge_text: str) -> str:
        nonlocal changed, current_instruction_revision
        current_instruction_revision = current_instruction_revision_from_bridge_text(
            bridge_text
        )
        updated_text = reset_implementer_sections(bridge_text)
        changed = updated_text != bridge_text
        return updated_text

    rewrite_bridge_markdown(bridge_path, transform=transform)
    _refresh_projections_after_checkpoint(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )

    report, _ = run_status_action_fn(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
    )
    report["action"] = getattr(args, "action", "reset-implementer-state")
    report["ok"] = True
    report["exit_ok"] = True
    report["exit_code"] = 0
    report["implementer_state_reset"] = {
        "changed": changed,
        "current_instruction_revision": current_instruction_revision,
        "reason": str(getattr(args, "reason", "") or ""),
    }
    return report, 0
