"""Repo-governance push policy resolution helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..bundle_registry import get_bundle_commands
from ..common_io import inject_quality_policy_command, normalize_repo_python_shell_command
from ..config import REPO_ROOT
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


def _coerce_text(value: object, fallback: str) -> str:
    return str(value or "").strip() or fallback


def _coerce_text_items(
    value: object,
    *,
    fallback: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, list):
        return fallback
    items = tuple(str(entry or "").strip() for entry in value if str(entry or "").strip())
    return items or fallback


def _coerce_positive_int(value: object, *, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def _coerce_mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


def _parse_preflight_policy(
    payload: object,
    warnings: list[str],
) -> PushPreflightPolicy:
    if not isinstance(payload, dict):
        return PushPreflightPolicy()
    command = _coerce_text(payload.get("command"), "check-router")
    if command != "check-router":
        warnings.append(
            f"repo_governance.push.preflight.command `{command}` is unsupported; defaulted to `check-router`."
        )
        command = "check-router"
    since_ref_template = _coerce_text(
        payload.get("since_ref_template"),
        "{remote}/{development_branch}",
    )
    execute = bool(payload.get("execute", True))
    return PushPreflightPolicy(
        command=command,
        since_ref_template=since_ref_template,
        execute=execute,
    )


def _parse_post_push_policy(
    payload: object,
    warnings: list[str],
) -> PushPostPushPolicy:
    if not isinstance(payload, dict):
        return PushPostPushPolicy()
    bundle = _coerce_text(payload.get("bundle"), "bundle.post-push")
    try:
        get_bundle_commands(bundle)
    except KeyError:
        warnings.append(
            f"repo_governance.push.post_push.bundle `{bundle}` is unknown; defaulted to `bundle.post-push`."
        )
        bundle = "bundle.post-push"
    return PushPostPushPolicy(bundle=bundle)


def _parse_bypass_policy(payload: object) -> PushBypassPolicy:
    if not isinstance(payload, dict):
        return PushBypassPolicy()
    return PushBypassPolicy(
        allow_skip_preflight=bool(payload.get("allow_skip_preflight", False)),
        allow_skip_post_push=bool(payload.get("allow_skip_post_push", False)),
    )


def _parse_checkpoint_policy(
    payload: object,
    warnings: list[str],
) -> PushCheckpointPolicy:
    if payload is None:
        return PushCheckpointPolicy()
    if not isinstance(payload, dict):
        warnings.append(
            "repo_governance.push.checkpoint must be an object; using defaults."
        )
        return PushCheckpointPolicy()
    compat_paths = _coerce_text_items(
        payload.get("compatibility_projection_paths"),
        fallback=(),
    )
    advisory_paths = _coerce_text_items(
        payload.get("advisory_context_paths"),
        fallback=(),
    )
    return PushCheckpointPolicy(
        max_dirty_paths_before_checkpoint=_coerce_positive_int(
            payload.get("max_dirty_paths_before_checkpoint"),
            fallback=12,
        ),
        max_untracked_paths_before_checkpoint=_coerce_positive_int(
            payload.get("max_untracked_paths_before_checkpoint"),
            fallback=6,
        ),
        compatibility_projection_paths=compat_paths,
        advisory_context_paths=advisory_paths,
    )


def _resolve_repo_pack_id(payload: dict[str, object], *, repo_root: Path) -> str:
    repo_governance = _coerce_mapping(payload.get("repo_governance"))
    surface_generation = _coerce_mapping(repo_governance.get("surface_generation"))
    metadata = _coerce_mapping(surface_generation.get("repo_pack_metadata"))
    pack_id = str(metadata.get("pack_id") or "").strip()
    if pack_id:
        return pack_id
    repo_name = str(payload.get("repo_name") or "").strip()
    if repo_name:
        return repo_name.lower().replace(" ", "_")
    return repo_root.name
