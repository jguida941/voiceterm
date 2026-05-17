"""Push preflight routing helpers."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

from ..common_io import inject_quality_policy_command, normalize_repo_python_shell_command

if TYPE_CHECKING:
    from .push_policy import PushPolicy


@dataclass(frozen=True, slots=True)
class PushRefRoutingState:
    """Branch/upstream facts needed to resolve a push preflight base."""

    current_branch: str = ""
    upstream_ref: str = ""
    branch_has_remote: bool | None = None


class PushValidationRouting(NamedTuple):
    """Validation refs used by push preflight routing."""

    head_ref: str = "HEAD"
    range_scope_only: bool = False
    validation_scope: str = ""


class PushPreflightReportRouting(NamedTuple):
    """Optional check-router report artifact routing for push preflight."""

    output_path: str = ""
    format: str = "json"


def build_preflight_shell_command(
    policy: "PushPolicy",
    *,
    remote: str,
    route_state: PushRefRoutingState | None = None,
    quality_policy_path: str | None = None,
    validation_routing: PushValidationRouting | None = None,
    report_routing: PushPreflightReportRouting | None = None,
) -> str:
    """Build the non-mutating or execution-ready preflight shell command."""
    resolved_route = route_state or PushRefRoutingState()
    resolved_validation = validation_routing or PushValidationRouting()
    resolved_report = report_routing or PushPreflightReportRouting()
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
    if resolved_validation.head_ref and resolved_validation.head_ref != "HEAD":
        args.extend(["--head-ref", resolved_validation.head_ref])
    if resolved_validation.range_scope_only:
        args.append("--range-scope-only")
    if resolved_validation.validation_scope:
        args.extend(["--validation-scope", resolved_validation.validation_scope])
    if resolved_report.output_path:
        args.extend(
            ["--format", resolved_report.format, "--output", resolved_report.output_path]
        )
    if policy.preflight.execute:
        args.append("--execute")
        args.extend(["--parallel-workers", str(max(1, policy.preflight.parallel_workers))])
        if not bool(getattr(policy.preflight, "fail_fast_on_blocker", True)):
            args.append("--keep-going")
    command = shlex.join(args)
    check_router_command = normalize_repo_python_shell_command(
        inject_quality_policy_command(command, quality_policy_path)
    )
    publication_scope_command = normalize_repo_python_shell_command(
        shlex.join(
            [
                "python3",
                "dev/scripts/checks/check_publication_scope_integrity.py",
                "--format",
                "md",
            ]
        )
    )
    return f"{publication_scope_command} && {check_router_command}"


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
