"""Push preflight routing helpers."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..common_io import inject_quality_policy_command, normalize_repo_python_shell_command

if TYPE_CHECKING:
    from .push_policy import PushPolicy


@dataclass(frozen=True, slots=True)
class PushRefRoutingState:
    """Branch/upstream facts needed to resolve a push preflight base."""

    current_branch: str = ""
    upstream_ref: str = ""
    branch_has_remote: bool | None = None


def build_preflight_shell_command(
    policy: "PushPolicy",
    *,
    remote: str,
    route_state: PushRefRoutingState | None = None,
    quality_policy_path: str | None = None,
) -> str:
    """Build the non-mutating or execution-ready preflight shell command."""
    resolved_route = route_state or PushRefRoutingState()
    since_ref = resolve_preflight_since_ref(
        remote=remote,
        development_branch=policy.development_branch,
        release_branch=policy.release_branch,
        since_ref_template=policy.preflight.since_ref_template,
        route_state=resolved_route,
    )
    args = [
        "python3",
        "dev/scripts/devctl.py",
        policy.preflight.command,
        "--since-ref",
        since_ref,
    ]
    if policy.preflight.execute:
        args.append("--execute")
    command = shlex.join(args)
    return normalize_repo_python_shell_command(
        inject_quality_policy_command(command, quality_policy_path)
    )


def resolve_preflight_since_ref(
    *,
    remote: str,
    development_branch: str,
    release_branch: str,
    since_ref_template: str,
    route_state: PushRefRoutingState | None = None,
) -> str:
    """Resolve the diff base for push/check-router preflight commands."""
    resolved_route = route_state or PushRefRoutingState()
    branch = str(resolved_route.current_branch or "").strip()
    if resolved_route.branch_has_remote and branch:
        return f"{remote}/{branch}"

    upstream = str(resolved_route.upstream_ref or "").strip()
    if upstream:
        upstream_remote, _, _branch = upstream.partition("/")
        if upstream_remote == remote:
            return upstream

    return (since_ref_template or "{remote}/{development_branch}").format(
        remote=remote,
        development_branch=development_branch,
        release_branch=release_branch,
    )
