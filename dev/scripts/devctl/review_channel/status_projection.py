"""Helpers for bridge-backed review-state projection payloads.

Builds the canonical ``ReviewState`` shape from bridge markdown snapshots so
the bridge-backed and event-backed paths emit the same top-level contract.
Bridge-specific extras (``runtime``, ``service_identity``,
``attach_auth_policy``, ``project_id``) are nested under a
``_compat`` key so they do not masquerade as canonical contract fields.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ..common import display_path
from ..runtime.review_state_models import (
    AgentRegistryEntryState,
    AgentRegistryState,
    ReviewAttentionState,
    ReviewBridgeState,
    ReviewQueueState,
    ReviewSessionState,
    ReviewState,
)
from ..runtime.role_profile import TandemRole
from .current_session_projection import build_bridge_current_session
from .handoff import BridgeSnapshot
from .peer_liveness import OverallLivenessState
from .promotion import PromotionCandidate, promotion_candidate_to_dict
from .status_projection_compat import (
    CompatProjectionInputs,
    build_bridge_compat_projection,
)


@dataclass(frozen=True)
class ReviewStateContext:
    """Grouped path/identity context for review-state projection."""

    repo_root: Path
    bridge_path: Path
    review_channel_path: Path
    bridge_text: str
    project_id: str
    timestamp: str
    service_identity: dict[str, object]
    attach_auth_policy: dict[str, object]
    plan_id: str = ""
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def build_bridge_review_state(
    *,
    context: ReviewStateContext,
    snapshot: BridgeSnapshot,
    bridge_liveness: dict[str, object],
    attention: dict[str, object],
    promotion_candidate: PromotionCandidate | None,
    reduced_runtime: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a canonical ReviewState dict from bridge markdown state."""
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")

    review_state = ReviewState(
        schema_version=1,
        contract_id="ReviewState",
        command="review-channel",
        action="status",
        timestamp=context.timestamp,
        ok=_projection_ok(overall_state, context.errors),
        review=_build_review_session(context),
        queue=_build_queue_state(promotion_candidate),
        current_session=build_bridge_current_session(snapshot, bridge_liveness),
        bridge=_build_bridge_state(snapshot, bridge_liveness, overall_state),
        attention=_build_attention(attention),
        packets=(),
        registry=_build_agent_registry(
            overall_state=overall_state,
            bridge_liveness=bridge_liveness,
            timestamp=context.timestamp,
            plan_id=context.plan_id,
        ),
        warnings=context.warnings,
        errors=context.errors,
    )

    result: dict[str, object] = asdict(review_state)

    # Bridge-specific extras live under _compat so the canonical ReviewState
    # payload stays exact.  Consumers should migrate to _compat access; once
    # all callers are migrated the _compat key can be removed entirely.
    registry_dict = result.get("registry")
    raw_agents = registry_dict.get("agents", []) if isinstance(registry_dict, dict) else []
    legacy_agents = []
    for agent in raw_agents:
        entry = dict(agent) if isinstance(agent, dict) else {}
        entry["status"] = entry.get("job_state", "")
        entry["role"] = entry.get("current_job", "")
        entry["capabilities"] = []
        legacy_agents.append(entry)

    result["_compat"] = _build_compat_projection(
        context=context,
        bridge_liveness=bridge_liveness,
        reduced_runtime=reduced_runtime,
        legacy_agents=legacy_agents,
    )

    return result

def _projection_ok(overall_state: str, errors: tuple[str, ...]) -> bool:
    if errors:
        return False
    return overall_state in (
        OverallLivenessState.FRESH,
        OverallLivenessState.INACTIVE,
    )

def _build_compat_projection(
    *,
    context: ReviewStateContext,
    bridge_liveness: dict[str, object],
    reduced_runtime: dict[str, object] | None,
    legacy_agents: list[dict[str, object]],
) -> dict[str, object]:
    return build_bridge_compat_projection(
        inputs=CompatProjectionInputs(
            project_id=context.project_id,
            bridge_text=context.bridge_text,
            bridge_liveness=bridge_liveness,
            reduced_runtime=reduced_runtime,
            service_identity=context.service_identity,
            attach_auth_policy=context.attach_auth_policy,
            legacy_agents=legacy_agents,
        ),
    )

def _build_review_session(context: ReviewStateContext) -> ReviewSessionState:
    return ReviewSessionState(
        plan_id=context.plan_id,
        controller_run_id="",
        session_id="markdown-bridge",
        surface_mode="markdown-bridge",
        active_lane="review",
        refresh_seq=1,
        bridge_path=display_path(context.bridge_path, repo_root=context.repo_root),
        review_channel_path=display_path(
            context.review_channel_path,
            repo_root=context.repo_root,
        ),
    )


def _build_agent_registry(
    *,
    overall_state: str,
    bridge_liveness: dict[str, object],
    timestamp: str,
    plan_id: str = "",
) -> AgentRegistryState:
    claude_status = _claude_agent_status(bridge_liveness)
    operator_status = _operator_status(overall_state)
    agents = (
        AgentRegistryEntryState(
            agent_id="codex",
            provider="codex",
            display_name="Codex",
            lane="codex",
            lane_title="Reviewer",
            current_job=TandemRole.REVIEWER,
            job_state=overall_state,
            waiting_on="",
            last_packet_seen="",
            last_packet_applied="",
            script_profile="markdown-bridge-conductor",
            mp_scope=plan_id,
            worktree="",
            branch="",
            updated_at=timestamp,
        ),
        AgentRegistryEntryState(
            agent_id="claude",
            provider="claude",
            display_name="Claude",
            lane="claude",
            lane_title="Implementer",
            current_job=TandemRole.IMPLEMENTER,
            job_state=claude_status,
            waiting_on="",
            last_packet_seen="",
            last_packet_applied="",
            script_profile="markdown-bridge-conductor",
            mp_scope=plan_id,
            worktree="",
            branch="",
            updated_at=timestamp,
        ),
        AgentRegistryEntryState(
            agent_id="cursor",
            provider="cursor",
            display_name="Cursor",
            lane="cursor",
            lane_title="Implementer",
            current_job=TandemRole.IMPLEMENTER,
            job_state="idle",
            waiting_on="",
            last_packet_seen="",
            last_packet_applied="",
            script_profile="",
            mp_scope="",
            worktree="",
            branch="",
            updated_at=timestamp,
        ),
        AgentRegistryEntryState(
            agent_id="operator",
            provider="operator",
            display_name="Operator",
            lane="operator",
            lane_title="Approver",
            current_job="approver",
            job_state=operator_status,
            waiting_on="",
            last_packet_seen="",
            last_packet_applied="",
            script_profile="",
            mp_scope="",
            worktree="",
            branch="",
            updated_at=timestamp,
        ),
    )
    return AgentRegistryState(timestamp=timestamp, agents=agents)


def _claude_agent_status(bridge_liveness: dict[str, object]) -> str:
    if (
        bool(bridge_liveness.get("claude_status_present"))
        and bool(bridge_liveness.get("claude_ack_present"))
        and bool(bridge_liveness.get("claude_ack_current"))
    ):
        return "active"
    return "waiting"


def _operator_status(overall_state: str) -> str:
    if overall_state == OverallLivenessState.WAITING_ON_PEER:
        return "waiting"
    if overall_state in {
        OverallLivenessState.STALE,
        OverallLivenessState.RUNTIME_MISSING,
    }:
        return "warning"
    if overall_state == OverallLivenessState.INACTIVE:
        return "idle"
    return "active"


def _build_queue_state(
    promotion_candidate: PromotionCandidate | None,
) -> ReviewQueueState:
    return ReviewQueueState(
        pending_total=0,
        pending_codex=0,
        pending_claude=0,
        pending_cursor=0,
        pending_operator=0,
        stale_packet_count=0,
        derived_next_instruction=(
            promotion_candidate.instruction if promotion_candidate is not None else ""
        ),
        derived_next_instruction_source=(
            promotion_candidate_to_dict(promotion_candidate)
            if promotion_candidate is not None
            else {}
        ),
    )


def _build_bridge_state(
    snapshot: BridgeSnapshot,
    bridge_liveness: dict[str, object],
    overall_state: str,
) -> ReviewBridgeState:
    current_session = build_bridge_current_session(snapshot, bridge_liveness)
    return ReviewBridgeState(
        overall_state=overall_state,
        codex_poll_state=str(bridge_liveness.get("codex_poll_state") or "unknown"),
        reviewer_freshness=str(
            bridge_liveness.get("reviewer_freshness") or "unknown"
        ),
        reviewer_mode=str(
            bridge_liveness.get("reviewer_mode") or "active_dual_agent"
        ),
        last_codex_poll_utc=str(
            snapshot.metadata.get("last_codex_poll_utc") or ""
        ),
        last_codex_poll_age_seconds=int(
            bridge_liveness.get("last_codex_poll_age_seconds") or 0
        ),
        last_worktree_hash=str(
            snapshot.metadata.get("last_non_audit_worktree_hash") or ""
        ),
        current_instruction=current_session.current_instruction,
        open_findings=current_session.open_findings,
        claude_status=current_session.implementer_status,
        claude_ack=current_session.implementer_ack,
        claude_ack_current=bool(bridge_liveness.get("claude_ack_current")),
        current_instruction_revision=current_session.current_instruction_revision,
        claude_ack_revision=current_session.implementer_ack_revision,
        last_reviewed_scope=current_session.last_reviewed_scope,
        review_accepted=_compute_review_accepted(snapshot),
        implementer_completion_stall=bool(
            bridge_liveness.get("implementer_completion_stall")
        ),
        publisher_running=bool(bridge_liveness.get("publisher_running")),
    )


def _compute_review_accepted(snapshot: BridgeSnapshot) -> bool:
    """Compute reviewer-owned acceptance using canonical bridge_review_accepted."""
    try:
        from .bridge_validation import bridge_review_accepted

        return bridge_review_accepted(snapshot)
    except (ImportError, ValueError):
        return False
def _build_attention(attention: dict[str, object]) -> ReviewAttentionState | None:
    if not attention:
        return None
    return ReviewAttentionState(
        status=str(attention.get("status") or ""),
        owner=str(attention.get("owner") or ""),
        summary=str(attention.get("summary") or ""),
        recommended_action=str(attention.get("recommended_action") or ""),
        recommended_command=str(attention.get("recommended_command") or ""),
    )


from .status_projection_helpers import build_bridge_runtime as _build_bridge_runtime
