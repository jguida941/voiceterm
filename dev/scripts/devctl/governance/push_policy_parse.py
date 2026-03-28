"""Parse/coerce helpers extracted from push_policy."""

from __future__ import annotations

from pathlib import Path

from ..bundle_registry import get_bundle_commands


def _coerce_text(value: object, fallback: str) -> str:
    return str(value or "").strip() or fallback


def _coerce_text_items(
    value: object,
    *,
    fallback: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, list):
        return fallback
    items = tuple(
        _coerce_text(entry, "") for entry in value if _coerce_text(entry, "")
    )
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
) -> "PushPreflightPolicy":
    from .push_policy import PushPreflightPolicy

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
) -> "PushPostPushPolicy":
    from .push_policy import PushPostPushPolicy

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


def _parse_bypass_policy(payload: object) -> "PushBypassPolicy":
    from .push_policy import PushBypassPolicy

    if not isinstance(payload, dict):
        return PushBypassPolicy()
    return PushBypassPolicy(
        allow_skip_preflight=bool(payload.get("allow_skip_preflight", False)),
        allow_skip_post_push=bool(payload.get("allow_skip_post_push", False)),
    )


def _parse_checkpoint_policy(
    payload: object,
    warnings: list[str],
) -> "PushCheckpointPolicy":
    from .push_policy import PushCheckpointPolicy

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
    pack_id = _coerce_text(metadata.get("pack_id"), "")
    if pack_id:
        return pack_id
    repo_name = _coerce_text(payload.get("repo_name"), "")
    if repo_name:
        return repo_name.lower().replace(" ", "_")
    return repo_root.name
