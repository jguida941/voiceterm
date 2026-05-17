"""Shared attach/auth policy builder for the review-channel backend."""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass

from ..platform.surface_definitions import caller_authority as platform_caller_authority

_DEVCTL_INTERPRETER = os.path.basename(sys.executable)

REVIEW_CHANNEL_ATTACH_ENTRYPOINTS = (
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action status --terminal none --format json",
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action ensure --terminal none --format json",
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action reviewer-heartbeat --terminal none --format json",
)
REVIEW_CHANNEL_HEALTH_SIGNALS = (
    "ok",
    "bridge.reviewer_mode",
    "bridge.last_codex_poll_age_seconds",
    "bridge.reviewed_hash_current",
    "attention.status",
    "runtime.daemons.publisher.running",
    "runtime.daemons.reviewer_supervisor.running",
)
REVIEW_CHANNEL_SHUTDOWN_ENTRYPOINTS = (
    "stop the repo-owned ensure/reviewer-heartbeat follow process",
    "persist final publisher/reviewer-supervisor heartbeat stop state",
)


@dataclass(frozen=True)
class ServiceEndpointPolicy:
    """Machine-readable attach surface for the current review-channel backend."""

    service_id: str
    launch_entrypoints: tuple[str, ...]
    discovery_fields: tuple[str, ...]
    health_signals: tuple[str, ...]
    shutdown_entrypoints: tuple[str, ...]


@dataclass(frozen=True)
class AttachCallerAuthority:
    """Allowed/staged/approval/forbidden action buckets for one caller class."""

    caller_id: str
    allowed_actions: tuple[str, ...]
    stage_only_actions: tuple[str, ...]
    approval_required_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]


@dataclass(frozen=True)
class AttachAuthPolicy:
    """Repo/worktree-scoped attach/auth contract for review-channel consumers."""

    attach_scope: str
    local_only: bool
    off_lan_allowed: bool
    transport: str
    auth_mode: str
    token_required: bool
    key_required: bool
    approval_boundary: str
    attach_entrypoints: tuple[str, ...]
    service_endpoint: ServiceEndpointPolicy
    caller_authority: tuple[AttachCallerAuthority, ...]


def build_attach_auth_policy(*, service_identity: dict[str, object]) -> dict[str, object]:
    """Build the repo/worktree attach/auth contract for bridge consumers."""
    discovery_fields = tuple(
        str(field)
        for field in list(service_identity.get("discovery_fields") or [])
        if str(field)
    )
    return asdict(
        AttachAuthPolicy(
            attach_scope="repo_worktree_local",
            local_only=True,
            off_lan_allowed=False,
            transport="filesystem_markdown_bridge",
            auth_mode="repo_worktree_identity",
            token_required=False,
            key_required=False,
            approval_boundary="caller_authority_policy",
            attach_entrypoints=REVIEW_CHANNEL_ATTACH_ENTRYPOINTS,
            service_endpoint=ServiceEndpointPolicy(
                service_id=str(service_identity.get("service_id") or ""),
                launch_entrypoints=REVIEW_CHANNEL_ATTACH_ENTRYPOINTS,
                discovery_fields=discovery_fields,
                health_signals=REVIEW_CHANNEL_HEALTH_SIGNALS,
                shutdown_entrypoints=REVIEW_CHANNEL_SHUTDOWN_ENTRYPOINTS,
            ),
            caller_authority=_build_attach_caller_authority(),
        )
    )


def _build_attach_caller_authority() -> tuple[AttachCallerAuthority, ...]:
    """Return caller authority rows from the platform surface source of truth."""
    return tuple(
        AttachCallerAuthority(
            caller_id=spec.caller_id,
            allowed_actions=spec.allowed_actions,
            stage_only_actions=spec.stage_only_actions,
            approval_required_actions=spec.approval_required_actions,
            forbidden_actions=spec.forbidden_actions,
        )
        for spec in platform_caller_authority()
    )
