"""Dashboard-backed control-decision fallback for review-channel writes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from ...runtime.review_channel_post_actions import required_review_channel_post_action
from ...runtime.value_coercion import coerce_mapping, coerce_string


def dashboard_backed_control_decision_payload(
    *,
    args,
    repo_root: Path,
    review_state: Mapping[str, object],
    actor: str,
    role: str,
    session_id: str,
    attempted_argv: Sequence[str],
) -> dict[str, object]:
    required_action = required_post_allowed_action(args, attempted_argv)
    if not required_action:
        return {}
    try:
        from ...runtime.agent_loop_decision import build_agent_loop_decision
        from ...runtime.dashboard_snapshot_authority import build_dashboard_snapshot
        from ..reporting.claude_loop_state import load_master_plan_authority

        dashboard = build_dashboard_snapshot(
            repo_root=repo_root,
            view="overview",
            role=role,
            include_review_state=True,
        )
        dashboard_review_state = dict(coerce_mapping(dashboard.get("_review_state")))
        decision = build_agent_loop_decision(
            review_state=dashboard_review_state or dict(review_state),
            dashboard=dashboard,
            actor_id=actor,
            actor_role=role,
            session_id=session_id,
            loop_intent="",
            requested_plan_ref="",
            requested_packet_id="",
            master_plan=load_master_plan_authority(repo_root),
            operator_override_requested=getattr(args, "operator_override", False),
            operator_override_reason=getattr(args, "override_reason", ""),
            operator_override_scope=getattr(args, "override_scope", "edit-only"),
            operator_override_by=getattr(args, "override_by", "operator"),
        )
    except (ImportError, OSError, TypeError, ValueError, KeyError):
        return {}
    payload = decision.to_dict()
    return payload if decision_allows_action(payload, required_action) else {}


def should_prefer_dashboard_control_decision(
    *,
    args,
    projected_decision: Mapping[str, object],
    dashboard_decision: Mapping[str, object],
    attempted_argv: Sequence[str],
) -> bool:
    required_action = required_post_allowed_action(args, attempted_argv)
    if not required_action or not dashboard_decision:
        return False
    if decision_allows_action(projected_decision, required_action):
        return False
    return decision_allows_action(dashboard_decision, required_action)


def required_post_allowed_action(args, attempted_argv: Sequence[str]) -> str:
    if coerce_string(getattr(args, "action", "")).strip().lower() != "post":
        return ""
    kind = coerce_string(getattr(args, "kind", "")).strip().lower()
    if not kind:
        return ""
    return required_review_channel_post_action(attempted_argv, kind=kind)


def decision_allows_action(
    decision: Mapping[str, object],
    required_action: str,
) -> bool:
    allowed_actions = decision.get("allowed_actions")
    if not isinstance(allowed_actions, (list, tuple, set, frozenset)):
        return False
    normalized = {coerce_string(item).strip().lower() for item in allowed_actions}
    return required_action.strip().lower() in normalized

