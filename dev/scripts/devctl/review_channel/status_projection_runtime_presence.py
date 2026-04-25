"""Typed runtime-presence helpers for bridge status projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..runtime.role_profile import TandemRole, default_provider_for_role
from . import collaboration_session_local_reviewer as _local_reviewer_activity
from .collaboration_session_local_reviewer import provider_packet_activity_is_fresh
from .peer_liveness import (
    CodexPollState,
    ReviewerFreshness,
    ReviewerMode,
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)
from .remote_control_attachment_artifact import load_remote_control_attachments
from .reviewer_activity_liveness import apply_reviewer_activity_liveness


@dataclass(frozen=True, slots=True)
class RuntimePresenceProjection:
    active_runtime_providers: list[str]
    remote_control_active_providers: list[str]
    packet_activity_active_providers: list[str]


def apply_reviewer_activity_runtime_liveness(
    *,
    bridge_liveness: dict[str, object],
    output_root: Path,
    reviewer_provider: str,
    capability_provider_fn,
) -> None:
    provider = (
        str(reviewer_provider or "").strip().lower()
        or capability_provider_fn(bridge_liveness, "reviewer_capability")
        or default_provider_for_role(TandemRole.REVIEWER)
    )
    apply_reviewer_activity_liveness(
        bridge_liveness=bridge_liveness,
        reviewer_provider=provider,
        session_output_root=output_root,
    )
    _mark_fresh_reviewer_heartbeat_activity(
        bridge_liveness=bridge_liveness,
        reviewer_provider=provider,
        output_root=output_root,
    )


def runtime_presence_projection(
    *,
    bridge_liveness: Mapping[str, object],
    active_providers: list[str],
    output_root: Path,
    capability_provider_fn,
) -> RuntimePresenceProjection:
    remote_control_providers = list(
        active_remote_control_providers(output_root=output_root)
    )
    packet_activity_providers = list(
        packet_activity_providers_for_bridge(
            bridge_liveness=bridge_liveness,
            output_root=output_root,
            capability_provider_fn=capability_provider_fn,
        )
    )
    runtime_providers = ordered_unique(
        [
            *active_providers,
            *remote_control_providers,
            *packet_activity_providers,
            *reviewer_activity_providers(bridge_liveness),
        ]
    )
    return RuntimePresenceProjection(
        active_runtime_providers=runtime_providers,
        remote_control_active_providers=remote_control_providers,
        packet_activity_active_providers=packet_activity_providers,
    )


def active_remote_control_providers(*, output_root: Path) -> tuple[str, ...]:
    providers: list[str] = []
    for attachment in load_remote_control_attachments(
        output_root=output_root,
        active_only=True,
    ):
        provider = str(attachment.provider or "").strip().lower()
        if provider and provider not in providers:
            providers.append(provider)
    return tuple(providers)


def packet_activity_providers_for_bridge(
    *,
    bridge_liveness: Mapping[str, object],
    output_root: Path,
    capability_provider_fn,
) -> tuple[str, ...]:
    providers: list[str] = []
    implementer_provider = capability_provider_fn(
        bridge_liveness, "implementer_capability"
    ) or default_provider_for_role(TandemRole.IMPLEMENTER)
    if implementer_provider and provider_packet_activity_is_fresh(
        provider=implementer_provider,
        session_output_root=output_root,
    ):
        providers.append(implementer_provider)
    return tuple(providers)


def reviewer_activity_providers(
    bridge_liveness: Mapping[str, object],
) -> tuple[str, ...]:
    if not bool(bridge_liveness.get("reviewer_activity_active")):
        return ()
    provider = str(bridge_liveness.get("reviewer_activity_provider") or "").strip()
    if not provider:
        return ()
    return (provider,)


def ordered_unique(providers: list[str]) -> list[str]:
    result: list[str] = []
    for provider in providers:
        normalized = str(provider or "").strip().lower()
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def sync_local_reviewer_activity_hooks() -> None:
    try:
        from . import collaboration_session as collaboration_session_mod
    except ImportError:
        return
    _local_reviewer_activity._utcnow = collaboration_session_mod._utcnow
    _local_reviewer_activity.discover_latest_session = (
        collaboration_session_mod.discover_latest_session
    )


def _mark_fresh_reviewer_heartbeat_activity(
    *,
    bridge_liveness: dict[str, object],
    reviewer_provider: str,
    output_root: Path,
) -> None:
    raw_reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "").strip()
    reviewer_mode = (
        normalize_reviewer_mode(raw_reviewer_mode).value
        if raw_reviewer_mode
        else ReviewerMode.TOOLS_ONLY.value
    )
    if (
        not reviewer_mode_is_active(reviewer_mode)
        and reviewer_mode != ReviewerMode.TOOLS_ONLY.value
    ):
        return
    if bool(
        bridge_liveness.get("poll_status_automation_only")
    ) and not _tools_only_remote_control_heartbeat_is_authoritative(
        bridge_liveness=bridge_liveness,
        reviewer_mode=reviewer_mode,
        output_root=output_root,
    ):
        return
    if str(bridge_liveness.get("reviewer_activity_provider") or "").strip():
        return
    freshness = str(bridge_liveness.get("reviewer_freshness") or "").strip()
    poll_state = str(
        bridge_liveness.get("reviewer_poll_state")
        or bridge_liveness.get("codex_poll_state")
        or ""
    ).strip()
    poll_timestamp = str(
        bridge_liveness.get("last_reviewer_poll_utc")
        or bridge_liveness.get("last_codex_poll_utc")
        or ""
    ).strip()
    if not poll_timestamp:
        return
    if freshness not in {
        ReviewerFreshness.FRESH.value,
        ReviewerFreshness.POLL_DUE.value,
    }:
        return
    if poll_state not in {CodexPollState.FRESH.value, CodexPollState.POLL_DUE.value}:
        return
    provider = str(reviewer_provider or "").strip().lower()
    if not provider:
        return
    bridge_liveness["reviewer_activity_source"] = "reviewer_heartbeat"
    bridge_liveness["reviewer_activity_provider"] = provider
    bridge_liveness["reviewer_activity_active"] = True


def _tools_only_remote_control_heartbeat_is_authoritative(
    *,
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    output_root: Path,
) -> bool:
    if reviewer_mode != ReviewerMode.TOOLS_ONLY.value:
        return False
    if str(bridge_liveness.get("reviewer_activity_provider") or "").strip():
        return False
    return bool(active_remote_control_providers(output_root=output_root))
