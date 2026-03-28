"""Repo-governance push policy resolution helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..bundle_registry import get_bundle_commands
from ..common_io import inject_quality_policy_command, normalize_repo_python_shell_command
from ..config import REPO_ROOT
from .push_policy_parse import (
    _coerce_mapping,
    _coerce_positive_int,
    _coerce_text,
    _coerce_text_items,
    _dedupe,
    _parse_bypass_policy,
    _parse_checkpoint_policy,
    _parse_post_push_policy,
    _parse_preflight_policy,
    _resolve_repo_pack_id,
)
from .push_routing import build_preflight_shell_command, resolve_preflight_since_ref
from .repo_policy import load_repo_policy_payload

DEFAULT_ALLOWED_BRANCH_PREFIXES = ("feature/", "fix/")


@dataclass(frozen=True, slots=True)
class PushPreflightPolicy:
    """Structured preflight command configuration."""

    command: str = "check-router"
    since_ref_template: str = "{remote}/{development_branch}"
    execute: bool = True


@dataclass(frozen=True, slots=True)
class PushPostPushPolicy:
    """Structured post-push command configuration."""

    bundle: str = "bundle.post-push"


@dataclass(frozen=True, slots=True)
class PushBypassPolicy:
    """Policy-gated bypass controls for the canonical push flow."""

    allow_skip_preflight: bool = False
    allow_skip_post_push: bool = False


@dataclass(frozen=True, slots=True)
class PushCheckpointPolicy:
    """Deterministic checkpoint budget for local editing before push."""

    max_dirty_paths_before_checkpoint: int = 12
    max_untracked_paths_before_checkpoint: int = 6
    compatibility_projection_paths: tuple[str, ...] = ()
    """Paths of generated compatibility projections (e.g., bridge.md) that
    should be excluded from dirty-path counting for push/checkpoint decisions.
    These files are live-modified by the review loop, not authored code."""
    advisory_context_paths: tuple[str, ...] = ()
    """Repo-local scratch/reference paths (e.g., convo.md) that should not
    block governed push/checkpoint decisions for authored code."""


@dataclass(frozen=True, slots=True)
class PushPolicy:
    """Resolved repo-owned push governance policy."""

    policy_path: str
    repo_pack_id: str
    warnings: tuple[str, ...]
    default_remote: str
    development_branch: str
    release_branch: str
    protected_branches: tuple[str, ...]
    allowed_branch_prefixes: tuple[str, ...]
    preflight: PushPreflightPolicy
    post_push: PushPostPushPolicy
    bypass: PushBypassPolicy
    checkpoint: PushCheckpointPolicy


def load_push_policy(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> PushPolicy:
    """Load the resolved repo-governance push policy."""
    payload, warnings, resolved_policy_path = load_repo_policy_payload(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    return push_policy_from_payload(
        payload,
        repo_root=repo_root,
        resolved_policy_path=str(resolved_policy_path),
        warnings=warnings,
    )


def push_policy_from_payload(
    payload: dict[str, object],
    *,
    repo_root: Path = REPO_ROOT,
    resolved_policy_path: str = "",
    warnings: tuple[str, ...] = (),
) -> PushPolicy:
    """Parse PushPolicy from a resolved repo-policy payload."""
    governance_payload = payload.get("repo_governance")
    push_payload = {}
    if isinstance(governance_payload, dict):
        maybe_push = governance_payload.get("push")
        if isinstance(maybe_push, dict):
            push_payload = maybe_push
    warning_list = list(warnings)
    default_remote = _coerce_text(push_payload.get("default_remote"), "origin")
    development_branch = _coerce_text(
        push_payload.get("development_branch"),
        "main",
    )
    release_branch = _coerce_text(
        push_payload.get("release_branch"),
        development_branch,
    )
    protected = _coerce_text_items(
        push_payload.get("protected_branches"),
        fallback=(development_branch, release_branch),
    )
    allowed_prefixes = _coerce_text_items(
        push_payload.get("allowed_branch_prefixes"),
        fallback=DEFAULT_ALLOWED_BRANCH_PREFIXES,
    )
    preflight = _parse_preflight_policy(
        push_payload.get("preflight"),
        warning_list,
    )
    post_push = _parse_post_push_policy(
        push_payload.get("post_push"),
        warning_list,
    )
    bypass = _parse_bypass_policy(push_payload.get("bypass"))
    checkpoint = _parse_checkpoint_policy(
        push_payload.get("checkpoint"),
        warning_list,
    )
    repo_pack_id = _resolve_repo_pack_id(payload, repo_root=repo_root)
    return PushPolicy(
        policy_path=resolved_policy_path,
        repo_pack_id=repo_pack_id,
        warnings=tuple(warning_list),
        default_remote=default_remote,
        development_branch=development_branch,
        release_branch=release_branch,
        protected_branches=_dedupe(protected),
        allowed_branch_prefixes=_dedupe(allowed_prefixes),
        preflight=preflight,
        post_push=post_push,
        bypass=bypass,
        checkpoint=checkpoint,
    )


def build_push_command_routing_defaults(policy: PushPolicy) -> dict[str, object]:
    """Render the push-routing subset for ProjectGovernance payloads."""
    push_defaults: dict[str, object] = {}
    push_defaults["default_remote"] = policy.default_remote
    push_defaults["development_branch"] = policy.development_branch
    push_defaults["release_branch"] = policy.release_branch
    push_defaults["protected_branches"] = list(policy.protected_branches)
    push_defaults["allowed_branch_prefixes"] = list(policy.allowed_branch_prefixes)
    push_defaults["preflight"] = {
        "command": policy.preflight.command,
        "since_ref_template": policy.preflight.since_ref_template,
        "execute": policy.preflight.execute,
    }
    push_defaults["post_push"] = {"bundle": policy.post_push.bundle}
    push_defaults["bypass"] = {
        "allow_skip_preflight": policy.bypass.allow_skip_preflight,
        "allow_skip_post_push": policy.bypass.allow_skip_post_push,
    }
    push_defaults["checkpoint"] = {
        "max_dirty_paths_before_checkpoint": (
            policy.checkpoint.max_dirty_paths_before_checkpoint
        ),
        "max_untracked_paths_before_checkpoint": (
            policy.checkpoint.max_untracked_paths_before_checkpoint
        ),
        "compatibility_projection_paths": list(
            policy.checkpoint.compatibility_projection_paths
        ),
        "advisory_context_paths": list(policy.checkpoint.advisory_context_paths),
    }
    return {"push": push_defaults}


def detect_push_enforcement_state(
    policy: PushPolicy,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, object]:
    """Compatibility wrapper for the runtime push/checkpoint detector."""
    from .push_state import detect_push_enforcement_state as _detect

    return _detect(policy, repo_root=repo_root)


def resolve_sync_branches(policy: PushPolicy) -> tuple[str, ...]:
    """Return the canonical development/release sync branches."""
    return _dedupe((policy.development_branch, policy.release_branch))


def build_post_push_commands(
    policy: PushPolicy,
    *,
    quality_policy_path: str | None = None,
) -> list[str]:
    """Return normalized post-push bundle commands for the active policy."""
    commands = get_bundle_commands(policy.post_push.bundle)
    return [
        normalize_repo_python_shell_command(
            inject_quality_policy_command(command, quality_policy_path)
        )
        for command in commands
    ]


