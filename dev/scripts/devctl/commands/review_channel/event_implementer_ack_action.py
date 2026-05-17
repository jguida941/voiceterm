"""Implementer ACK action for the event-backed review-channel command path."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.event_store import append_event
from ...review_channel.events import refresh_event_bundle
from ...review_channel.implementer_ack_events import (
    ImplementerAckEventInput,
    build_implementer_ack_event,
    find_matching_implementer_ack_event,
)
from ...review_channel.packet_agents import packet_agent_ids_from_review_state
from ...runtime.role_profile import TandemRole, role_for_provider
from .event_action_support import EventActionContext


def run_implementer_ack_action(
    *,
    context: EventActionContext,
) -> tuple[dict, int, dict[str, object]]:
    """Append or reuse one typed implementer ACK event."""
    bundle = refresh_event_bundle(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=context.artifact_paths,
    )
    ack_input = _ack_input(context, bundle.events)
    _validate_implementer_ack_actor(bundle.review_state, ack_input.actor)
    _validate_current_revision(bundle.review_state, ack_input.revision)

    existing_event = find_matching_implementer_ack_event(
        bundle.events,
        actor=ack_input.actor,
        session_id=ack_input.session_id,
        revision=ack_input.revision,
        target_session_id=ack_input.target_session_id,
    )
    if existing_event:
        return _idempotent_ack_result(context, existing_event)

    event = build_implementer_ack_event(ack_input)
    written_event = append_event(
        Path(context.artifact_paths.event_log_path),
        event,
        existing_events=bundle.events,
    )
    refreshed = _refresh(context)
    report, exit_code = context.build_event_report_fn(
        args=context.args,
        bundle=refreshed,
        event=written_event,
    )
    report["idempotent"] = False
    return report, exit_code, refreshed.review_state


def _ack_input(
    context: EventActionContext,
    existing_events: list[dict[str, object]],
) -> ImplementerAckEventInput:
    args = context.args
    return ImplementerAckEventInput(
        repo_root=context.repo_root,
        existing_events=existing_events,
        actor=str(getattr(args, "actor", "") or "").strip(),
        revision=str(getattr(args, "revision", "") or "").strip(),
        notes=str(getattr(args, "notes", "") or "").strip(),
        session_id=str(getattr(args, "session_id", "") or ""),
        plan_id=str(getattr(args, "plan_id", "") or ""),
        controller_run_id=getattr(args, "controller_run_id", None),
        target_session_id=str(
            getattr(args, "target_session_id", "") or ""
        ).strip(),
    )


def _idempotent_ack_result(
    context: EventActionContext,
    existing_event: object,
) -> tuple[dict, int, dict[str, object]]:
    refreshed = _refresh(context)
    report, exit_code = context.build_event_report_fn(
        args=context.args,
        bundle=refreshed,
        event=dict(existing_event),
    )
    report["idempotent"] = True
    return report, exit_code, refreshed.review_state


def _refresh(context: EventActionContext):
    return refresh_event_bundle(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=context.artifact_paths,
    )


def _validate_current_revision(
    review_state: dict[str, object],
    revision: str,
) -> None:
    current_session = review_state.get("current_session")
    if not isinstance(current_session, dict):
        raise ValueError("review-channel implementer-ack requires typed current_session.")
    current_revision = str(
        current_session.get("current_instruction_revision") or ""
    ).strip()
    if not current_revision:
        raise ValueError(
            "review-channel implementer-ack requires a live current instruction revision."
        )
    if revision != current_revision:
        raise ValueError(
            "review-channel implementer-ack revision mismatch: "
            f"expected {current_revision}, got {revision}."
        )


def _validate_implementer_ack_actor(
    review_state: dict[str, object],
    actor: str,
) -> None:
    if not actor:
        raise ValueError("--actor is required for review-channel implementer-ack.")
    valid_agent_ids = set(packet_agent_ids_from_review_state(review_state))
    if actor not in valid_agent_ids:
        raise ValueError(f"Unsupported review-channel actor: {actor}")
    if _actor_is_assigned_implementer(review_state, actor):
        return
    if role_for_provider(actor) == TandemRole.IMPLEMENTER:
        return
    raise ValueError(
        "review-channel implementer-ack requires an actor with the typed "
        "implementer role."
    )


def _actor_is_assigned_implementer(
    review_state: dict[str, object],
    actor: str,
) -> bool:
    collaboration = review_state.get("collaboration")
    if not isinstance(collaboration, dict):
        return False
    assignments = collaboration.get("role_assignments")
    if not isinstance(assignments, list):
        return False
    return any(_assignment_matches_actor(row, actor) for row in assignments)


def _assignment_matches_actor(row: object, actor: str) -> bool:
    if not isinstance(row, dict):
        return False
    role_id = str(row.get("role_id") or "").strip()
    provider = str(row.get("provider") or "").strip()
    role = str(row.get("role") or "").strip()
    if provider != actor:
        return False
    if role_id == "coding_agent":
        return True
    return role_for_provider(actor) == TandemRole.IMPLEMENTER and role in {
        "",
        TandemRole.IMPLEMENTER.value,
        "coding_agent",
    }
