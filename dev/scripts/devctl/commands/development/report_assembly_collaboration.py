"""Collaboration profile phase for develop report assembly."""

from __future__ import annotations

from typing import Any

from ...config import REPO_ROOT
from ...runtime.development_collaboration_profiles import (
    build_agent_collaboration_profile,
)
from ...runtime.development_collaboration_modes import collaboration_mode_report
from . import report as development_report
from .report import (
    _effective_reviewer_mode_from_review_state,
    _mode_chain_errors_should_block,
    _profile_contract_refs,
    _profile_role_counts,
)


def build_collaboration_mode(
    args: Any,
    *,
    core: Any,
) -> tuple[dict[str, object], tuple[str, ...], tuple[str, ...]]:
    warnings = core.warnings
    blockers = core.blockers
    collaboration_mode = collaboration_mode_report(
        requested_mode=getattr(args, "collaboration_mode", ""),
        requested_role_preset=getattr(args, "role_preset", ""),
        max_workers=int(getattr(args, "max_workers", 0) or 0),
        chain_phases=tuple(getattr(args, "chain_phase", ()) or ()),
        dogfood=bool(getattr(args, "dogfood", False)),
        generic_agent_count=int(getattr(args, "generic_agents", 0) or 0),
        chain_scope=getattr(args, "chain_scope", ""),
        receipt_refs=tuple(getattr(args, "chain_receipt_ref", ()) or ()),
        role_counts=tuple(getattr(args, "role_count", ()) or ()),
        effective_reviewer_mode=_effective_reviewer_mode_from_review_state(
            core.review_state
        ),
    )
    selected_role_preset_id = str(
        collaboration_mode.get("selected_role_preset_id") or "dashboard"
    )
    profile = build_agent_collaboration_profile(
        profile_id=getattr(args, "profile", ""),
        selected_mode_id=str(collaboration_mode.get("selected_mode_id") or "solo"),
        selected_role_preset_id=selected_role_preset_id,
        providers=tuple(getattr(args, "provider", ()) or ()),
        role_bindings=tuple(getattr(args, "role_binding", ()) or ()),
        role_counts=_profile_role_counts(args, selected_role_preset_id),
        agent_mind_providers=tuple(getattr(args, "agent_mind_provider", ()) or ()),
        remote_provider=getattr(args, "remote_provider", ""),
        architecture_agent_count=int(getattr(args, "architecture_agents", 0) or 0),
        review_agent_count=int(getattr(args, "review_agents", 0) or 0),
        source_packet_id=getattr(args, "source_packet_id", ""),
        target_packet_id=getattr(args, "target_packet_id", ""),
        stop_at_packet_id=getattr(args, "stop_at_packet", ""),
        stop_at_mp_row_id=getattr(args, "stop_at_mp_row", ""),
        source_ref=getattr(args, "source_ref", ""),
        target_ref=getattr(args, "target_ref", ""),
        max_workers=int(getattr(args, "max_workers", 0) or 0),
        emit_template=bool(getattr(args, "emit_profile_template", False)),
        review_state=core.review_state,
        events=development_report._review_channel_events(REPO_ROOT),
        plan_rows=core.rows,
    )
    collaboration_mode["profile"] = profile.to_dict()
    collaboration_mode["profile_contract_refs"] = _profile_contract_refs(profile)
    warnings = (*warnings, *profile.validation_warnings)
    blockers = collaboration_blockers(
        args,
        core.action,
        blockers,
        collaboration_mode,
        profile,
    )
    return collaboration_mode, warnings, blockers


def collaboration_blockers(
    args: Any,
    action: str,
    blockers: tuple[str, ...],
    collaboration_mode: dict[str, object],
    profile: Any,
) -> tuple[str, ...]:
    if (
        action == "collaboration-profile"
        and bool(getattr(args, "validate_profile", False))
        and not profile.ok
    ):
        blockers = (*blockers, *profile.validation_errors)
    mode_chain = collaboration_mode.get("mode_chain")
    if (
        _mode_chain_errors_should_block(action, args)
        and isinstance(mode_chain, dict)
        and mode_chain.get("validation_errors")
    ):
        blockers = (
            *blockers,
            *tuple(str(item) for item in mode_chain.get("validation_errors") or ()),
        )
    return blockers
