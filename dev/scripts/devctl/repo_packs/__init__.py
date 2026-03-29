"""Repo-pack owned metadata, path resolution, and thin read-only helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .review_helpers import MobileReviewStateResult, load_mobile_review_state
from .voiceterm import (
    DEFAULT_BRIDGE_REL,
    DEFAULT_MOBILE_STATUS_REL,
    DEFAULT_PHONE_STATUS_REL,
    DEFAULT_REVIEW_CHANNEL_REL,
    DEFAULT_REVIEW_STATUS_DIR_REL,
    VOICETERM_PATH_CONFIG,
    RepoPathConfig,
    WorkflowPresetDefinition,
    collect_devctl_ci_runs,
    collect_devctl_git_status,
    collect_devctl_mutation_summary,
    collect_devctl_quality_backlog,
    load_review_payload_from_bridge,
    voiceterm_repo_root,
    workflow_preset_definitions,
)


@dataclass(slots=True)
class _ActivePathConfigState:
    """Tiny state holder for the active repo-pack override."""

    config: RepoPathConfig | None = None


@lru_cache(maxsize=1)
def _active_path_config_state() -> _ActivePathConfigState:
    """Return the repo-local override state for the active path config."""
    return _ActivePathConfigState()


def active_path_config() -> RepoPathConfig:
    """Return the active repo-pack path configuration.

    Defaults to the VoiceTerm config. Other repos override by calling
    ``set_active_path_config()`` during bootstrap.
    """
    override = _active_path_config_state().config
    if override is not None:
        return override
    return VOICETERM_PATH_CONFIG


def configured_path_config() -> RepoPathConfig | None:
    """Return the explicitly activated repo-pack path config, if any."""
    return _active_path_config_state().config


def active_path_config_is_overridden() -> bool:
    """Return whether the repo-pack path config was explicitly overridden."""
    return configured_path_config() is not None


def require_active_path_config() -> RepoPathConfig:
    """Return the activated repo-pack path config or fail closed."""
    config = configured_path_config()
    if config is None:
        raise RuntimeError(
            "Repo-pack path config is not activated; use ProjectGovernance or "
            "call set_active_path_config() explicitly."
        )
    return config


def set_active_path_config(config: RepoPathConfig) -> None:
    """Override the active repo-pack path configuration."""
    _active_path_config_state().config = config


__all__ = [
    "active_path_config",
    "active_path_config_is_overridden",
    "configured_path_config",
    "require_active_path_config",
    "set_active_path_config",
    "DEFAULT_BRIDGE_REL",
    "DEFAULT_MOBILE_STATUS_REL",
    "DEFAULT_PHONE_STATUS_REL",
    "DEFAULT_REVIEW_CHANNEL_REL",
    "DEFAULT_REVIEW_STATUS_DIR_REL",
    "MobileReviewStateResult",
    "RepoPathConfig",
    "VOICETERM_PATH_CONFIG",
    "WorkflowPresetDefinition",
    "collect_devctl_ci_runs",
    "collect_devctl_git_status",
    "collect_devctl_mutation_summary",
    "collect_devctl_quality_backlog",
    "load_mobile_review_state",
    "load_review_payload_from_bridge",
    "voiceterm_repo_root",
    "workflow_preset_definitions",
]
