"""Push-governance scan helpers for governance draft generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..runtime.project_governance import PushEnforcement
from .push_policy import (
    build_push_command_routing_defaults,
    detect_push_enforcement_state,
    push_policy_from_payload,
)


def scan_command_routing_defaults(
    policy: dict[str, Any],
    *,
    repo_root: Path,
    resolved_policy_path: str | Path | None,
) -> dict[str, object] | None:
    """Render repo-owned command routing defaults for ProjectGovernance."""
    push_policy = push_policy_from_payload(
        policy,
        repo_root=repo_root,
        resolved_policy_path=str(resolved_policy_path or ""),
    )
    return build_push_command_routing_defaults(push_policy)


def scan_push_enforcement(
    policy: dict[str, Any],
    *,
    repo_root: Path,
    resolved_policy_path: str | Path | None,
) -> PushEnforcement:
    """Render repo-owned push/checkpoint state for ProjectGovernance."""
    push_policy = push_policy_from_payload(
        policy,
        repo_root=repo_root,
        resolved_policy_path=str(resolved_policy_path or ""),
    )
    return PushEnforcement(
        **detect_push_enforcement_state(push_policy, repo_root=repo_root)
    )
