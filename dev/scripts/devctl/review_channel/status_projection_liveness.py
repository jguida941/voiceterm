"""Liveness helpers for bridge-backed status projections."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..runtime.role_profile import (
    TandemRole,
    default_provider_for_role,
    normalize_tandem_role,
)
from ..runtime.session_liveness_builder import (
    build_session_liveness_signals,
    session_liveness_rows,
)
from .collaboration_session_local_reviewer import local_reviewer_activity_is_fresh
from .launch_truth import (
    LaunchTruthState,
    capability_provider,
    classify_launch_truth,
    effective_reviewer_mode,
)
from .peer_liveness import (
    CodexPollState,
    OverallLivenessState,
    ReviewerFreshness,
    reviewer_mode_is_active,
)
from .remote_control_attachment_artifact import load_remote_control_attachments
from .session_state_hints import provider_session_state_hint
from .single_agent_authority import single_agent_lane_has_live_typed_authority
from .status_projection_runtime_presence import sync_local_reviewer_activity_hooks


def bridge_liveness_warnings(bridge_liveness: dict[str, object]) -> list[str]:
    warnings: list[str] = []
    codex_poll_state = str(bridge_liveness.get("codex_poll_state") or "unknown")
    reviewer_freshness = str(bridge_liveness.get("reviewer_freshness") or "")
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    if not reviewer_mode_is_active(reviewer_mode):
        effective_mode = str(
            bridge_liveness.get("effective_reviewer_mode") or reviewer_mode
        ).strip()
        if effective_mode == "active_dual_agent":
            warnings.append(
                "Bridge reviewer mode is inactive, but typed reviewer activity "
                "plus live remote-control runtime promote the effective mode to "
                "`active_dual_agent`; keep mutation authority on typed "
                "ActorAuthority grants."
            )
        elif activity_provider := str(
            bridge_liveness.get("reviewer_activity_provider") or ""
        ).strip():
            warnings.append(
                "Bridge reviewer mode is inactive, but typed reviewer packet "
                f"activity from `{activity_provider}` is fresh enough to prove "
                "the reviewer is present; keep mutation authority on typed "
                "ActorAuthority grants."
            )
        elif effective_mode == "single_agent":
            if single_agent_lane_has_live_typed_authority(bridge_liveness):
                warnings.append(
                    "Bridge reviewer mode is `single_agent`; dual-agent "
                    "heartbeat freshness is intentionally suspended, but "
                    "typed status/packet surfaces remain authoritative for "
                    "this local-review or remote-dashboard lane."
                )
            else:
                warnings.append(
                    "Bridge reviewer mode is `single_agent`; dual-agent "
                    "heartbeat freshness is intentionally suspended until the "
                    "workflow explicitly returns to `active_dual_agent`."
                )
        else:
            warnings.append(
                "Bridge reviewer mode is inactive; live heartbeat freshness is not enforced until the reviewer resumes active_dual_agent mode."
            )
    elif overall_state == OverallLivenessState.RUNTIME_MISSING:
        warnings.append(
            "Reviewer runtime is missing while `active_dual_agent` is still declared. The daemon is treated as missing runtime, not as authority to pause the loop."
        )
    elif (
        reviewer_freshness == ReviewerFreshness.MISSING
        or codex_poll_state == CodexPollState.MISSING
    ):
        warnings.append(
            "Bridge liveness is missing: the reviewer heartbeat compatibility field does not expose a usable poll timestamp yet."
        )
    elif reviewer_freshness == ReviewerFreshness.OVERDUE:
        warnings.append(
            "Bridge liveness is overdue: the latest reviewer poll timestamp has exceeded the controller escalation threshold."
        )
    elif (
        reviewer_freshness == ReviewerFreshness.STALE
        or codex_poll_state == CodexPollState.STALE
    ):
        warnings.append(
            "Bridge liveness is stale: the latest reviewer poll timestamp is older than the five-minute heartbeat contract."
        )
    elif (
        reviewer_freshness == ReviewerFreshness.POLL_DUE
        or codex_poll_state == CodexPollState.POLL_DUE
    ):
        warnings.append(
            "Bridge liveness is due for refresh: the latest reviewer poll timestamp is older than the 2-3 minute reviewer cadence but still within the five-minute heartbeat window."
        )
    elif overall_state == OverallLivenessState.WAITING_ON_PEER:
        warnings.append(
            "Bridge liveness is waiting_on_peer: the current bridge state still needs a fresh reviewer poll or complete implementer status/ACK state before the next cycle."
        )
    if bridge_liveness.get("reviewed_hash_current") is False:
        warnings.append(
            "Bridge review content is stale: the worktree has changed since the last reviewed hash. Current Verdict, Open Findings, and Current Instruction may not reflect the current tree state."
        )
    claude_hint = provider_session_state_hint(bridge_liveness, provider="claude")
    if claude_hint:
        warnings.append(
            str(claude_hint.get("summary") or "Implementer session hint detected.")
        )
    return warnings


def _degrade_active_dual_agent_freshness(
    bridge_liveness: dict[str, object],
) -> None:
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "").strip()
    if not reviewer_mode_is_active(reviewer_mode):
        return

    launch_truth = str(
        bridge_liveness.get("launch_truth")
        or classify_launch_truth(bridge_liveness).value
    ).strip()
    if launch_truth == LaunchTruthState.LIVE.value:
        return

    if launch_truth == LaunchTruthState.RUNTIME_MISSING.value:
        bridge_liveness["overall_state"] = OverallLivenessState.RUNTIME_MISSING
    elif (
        str(bridge_liveness.get("overall_state") or "").strip()
        == OverallLivenessState.FRESH.value
    ):
        bridge_liveness["overall_state"] = OverallLivenessState.STALE

    if bool(bridge_liveness.get("codex_conductor_active")):
        return

    poll_state = str(bridge_liveness.get("codex_poll_state") or "").strip()
    if poll_state in {CodexPollState.FRESH.value, CodexPollState.POLL_DUE.value}:
        bridge_liveness["codex_poll_state"] = CodexPollState.STALE

    reviewer_freshness = str(bridge_liveness.get("reviewer_freshness") or "").strip()
    if reviewer_freshness in {
        ReviewerFreshness.FRESH.value,
        ReviewerFreshness.POLL_DUE.value,
        "unknown",
    }:
        bridge_liveness["reviewer_freshness"] = ReviewerFreshness.STALE


def hybrid_loop_errors(bridge_liveness: dict[str, object]) -> list[str]:
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    if not reviewer_mode_is_active(reviewer_mode):
        return []
    launch_truth = str(
        bridge_liveness.get("launch_truth")
        or classify_launch_truth(bridge_liveness).value
    )
    if launch_truth == LaunchTruthState.DETACHED_RUNTIME_ONLY.value:
        return [
            "Reviewer mode is `active_dual_agent` but no live repo-owned Codex or "
            "Claude conductor sessions are present. Do not trust detached "
            "publisher/supervisor heartbeats as proof the review loop is live; "
            "relaunch with `review-channel --action launch` or "
            "`review-channel --action rollover` before continuing."
        ]
    if launch_truth == LaunchTruthState.AUTOMATION_ONLY.value:
        reason = str(bridge_liveness.get("poll_status_reason") or "unknown")
        return [
            "Repo-owned Codex conductor sessions are present, but the latest "
            "reviewer poll still comes from automation-only heartbeat refresh "
            f"(`{reason}`) rather than a reviewer-owned turn. Do not treat the "
            "live loop as started until `Poll Status` advances through a real "
            "Codex reviewer action."
        ]
    if launch_truth == LaunchTruthState.HYBRID_CLAUDE_ONLY.value:
        return [
            "Repo-owned Claude conductor is active but no live repo-owned Codex conductor session is present. Hybrid chat/terminal review loops are not trusted; relaunch with `review-channel --action launch` or `review-channel --action rollover` instead of relying on Claude-only recover."
        ]
    return []


def _single_agent_local_reviewer_provider(
    *,
    bridge_liveness: Mapping[str, object],
    output_root: Path,
) -> str | None:
    reviewer_mode = str(
        bridge_liveness.get("effective_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or ""
    ).strip()
    if reviewer_mode != "single_agent":
        return None
    reviewer_provider = (
        capability_provider(bridge_liveness, "reviewer_capability")
        or str(bridge_liveness.get("review_agent") or "").strip().lower()
        or default_provider_for_role(TandemRole.REVIEWER)
    )
    if not reviewer_provider:
        return None
    sync_local_reviewer_activity_hooks()
    if not local_reviewer_activity_is_fresh(
        reviewer_provider=reviewer_provider,
        session_output_root=output_root,
    ):
        return None
    return reviewer_provider


def _single_agent_remote_control_providers(
    *,
    bridge_liveness: Mapping[str, object],
    output_root: Path,
) -> tuple[str, ...]:
    reviewer_mode = str(
        bridge_liveness.get("effective_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or ""
    ).strip()
    if reviewer_mode != "single_agent":
        return ()
    providers: list[str] = []
    for attachment in load_remote_control_attachments(
        output_root=output_root,
        active_only=True,
    ):
        if (
            normalize_tandem_role(getattr(attachment, "role", ""))
            == TandemRole.OPERATOR
        ):
            continue
        provider = str(attachment.provider or "").strip().lower()
        if provider and provider not in providers:
            providers.append(provider)
    return tuple(providers)


def _build_participant_liveness(
    bridge_liveness: dict[str, object],
    active_providers: list[str],
) -> list[dict[str, object]]:
    """Emit runtime-owned SessionLivenessSignal rows for each provider."""
    return session_liveness_rows(
        build_session_liveness_signals(
            bridge_liveness=bridge_liveness,
            active_providers=active_providers,
        )
    )
