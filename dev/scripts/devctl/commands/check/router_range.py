"""Range-aware command normalization for check-router."""

from __future__ import annotations

import shlex

from ...common import inject_quality_policy_command, normalize_repo_python_shell_command
from ...governance.script_catalog_registry import (
    CHECK_SCRIPT_RELATIVE_PATHS,
    PROBE_SCRIPT_RELATIVE_PATHS,
)
from ...quality_policy import AI_GUARD_REGISTRY, REVIEW_PROBE_REGISTRY
from ...runtime.validation_scope import ValidationScope, ValidationScopeKind


def _range_aware_script_fragments() -> frozenset[str]:
    fragments: set[str] = {
        "dev/scripts/devctl.py docs-check",
    }
    fragments.update(
        CHECK_SCRIPT_RELATIVE_PATHS[script_id]
        for script_id, spec in AI_GUARD_REGISTRY.items()
        if spec.supports_commit_range and spec.script_id in CHECK_SCRIPT_RELATIVE_PATHS
    )
    fragments.update(
        PROBE_SCRIPT_RELATIVE_PATHS[script_id]
        for script_id, spec in REVIEW_PROBE_REGISTRY.items()
        if spec.supports_commit_range and spec.script_id in PROBE_SCRIPT_RELATIVE_PATHS
    )
    return frozenset(fragments)


ROUTER_RANGE_AWARE_SCRIPT_FRAGMENTS = _range_aware_script_fragments()

ROUTER_VALIDATION_SCOPE_AWARE_SCRIPT_FRAGMENTS = frozenset(
    {
        "dev/scripts/devctl.py docs-check",
        "dev/scripts/checks/check_system_picture_freshness.py",
        "dev/scripts/checks/check_review_channel_bridge.py",
        "dev/scripts/checks/check_startup_authority_contract.py",
        "dev/scripts/checks/check_review_surface_consistency.py",
        "dev/scripts/checks/check_tandem_consistency.py",
        "dev/scripts/checks/check_multi_agent_sync.py",
    }
)


def normalize_router_command(
    command: str,
    policy_path: str | None,
    *,
    since_ref: str | None = None,
    head_ref: str = "HEAD",
    validation_scope: ValidationScope | None = None,
) -> str:
    normalized = normalize_repo_python_shell_command(
        inject_quality_policy_command(command, policy_path)
    )
    ranged = append_router_range_args(
        normalized,
        since_ref=since_ref,
        head_ref=head_ref,
    )
    return append_router_validation_scope_arg(ranged, validation_scope=validation_scope)


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


def append_router_validation_scope_arg(
    command: str,
    *,
    validation_scope: ValidationScope | None,
) -> str:
    """Append typed validation scope to guards that understand it."""
    if validation_scope is None:
        return command
    if validation_scope.kind is ValidationScopeKind.LIVE_WORKTREE:
        return command
    if "--validation-scope" in command:
        return command
    if not any(
        fragment in command
        for fragment in ROUTER_VALIDATION_SCOPE_AWARE_SCRIPT_FRAGMENTS
    ):
        return command
    return command + " --validation-scope " + shlex.quote(validation_scope.kind.value)
