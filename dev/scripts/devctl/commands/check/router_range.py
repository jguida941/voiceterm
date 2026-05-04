"""Range-aware command normalization for check-router."""

from __future__ import annotations

import shlex

from ...common import inject_quality_policy_command, normalize_repo_python_shell_command

ROUTER_RANGE_AWARE_SCRIPT_FRAGMENTS = frozenset(
    {
        "dev/scripts/checks/check_python_broad_except.py",
        "dev/scripts/checks/check_command_source_validation.py",
        "dev/scripts/checks/check_structural_complexity.py",
        "dev/scripts/checks/check_duplicate_types.py",
    }
)


def normalize_router_command(
    command: str,
    policy_path: str | None,
    *,
    since_ref: str | None = None,
    head_ref: str = "HEAD",
) -> str:
    normalized = normalize_repo_python_shell_command(
        inject_quality_policy_command(command, policy_path)
    )
    return append_router_range_args(
        normalized,
        since_ref=since_ref,
        head_ref=head_ref,
    )


def append_router_range_args(
    command: str,
    *,
    since_ref: str | None,
    head_ref: str,
) -> str:
    if not since_ref or "--since-ref" in command:
        return command
    if not any(fragment in command for fragment in ROUTER_RANGE_AWARE_SCRIPT_FRAGMENTS):
        return command
    return (
        command
        + " --since-ref "
        + shlex.quote(str(since_ref))
        + " --head-ref "
        + shlex.quote(str(head_ref or "HEAD"))
    )
