"""Session-end guard that turns Codex task completion into a typed handoff."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from ..commands.rollout_tail.discovery import discover_latest_session
from ..commands.rollout_tail.parser import parse_rollout_file
from ..repo_packs import active_path_config
from ..runtime.rollout_event import RolloutEvent
from .event_store import load_events, resolve_artifact_paths
from .event_reducer import reduce_events
from .events import post_packet
from .launch_authority import current_head_sha
from .packet_contract import (
    PacketGuardBundleEvidenceFields,
    PacketPostRequest,
    PacketTargetFields,
)
from ..runtime.session_termination_policy import (
    session_termination_policy_from_review_state,
    task_complete_decision,
)


@dataclass(frozen=True, slots=True)
class TaskCompleteHandoffRequest:
    """Inputs for the task_complete-to-stage-packet guard."""

    repo_root: Path
    provider: str = "codex"
    to_agent: str = "claude"
    sessions_root: Path | None = None
    target_revision: str = ""
    target_ref: str = ""
    actor_role: str = ""
    guard_evidence: str = "--profile ci"
    conductor_exit_code: str = ""


@dataclass(frozen=True, slots=True)
class TaskCompleteHandoffResult:
    """Outcome from one handoff guard pass."""

    status: str
    reason: str
    packet_id: str = ""
    target_revision: str = ""
    target_ref: str = ""
    rollout_path: str = ""
    task_complete_at_utc: str = ""


def emit_handoff_for_latest_task_complete(
    request: TaskCompleteHandoffRequest,
) -> TaskCompleteHandoffResult:
    """Post a stage_commit_pipeline packet when a completed Codex slice lacks one."""
    provider = _clean(request.provider).lower()
    if provider != "codex":
        return _skipped("unsupported_provider")

    rollout_path = discover_latest_session(provider, root=request.sessions_root)
    if rollout_path is None:
        return _skipped("missing_rollout")
    task_complete = _latest_task_complete(rollout_path, provider=provider)
    if task_complete is None:
        return _skipped("missing_task_complete", rollout_path=rollout_path)

    repo_root = request.repo_root.resolve()
    target_revision = _clean(request.target_revision) or current_head_sha(repo_root)
    if not target_revision:
        return _skipped("missing_target_revision", rollout_path=rollout_path)
    target_ref = _clean(request.target_ref) or f"devctl_commit:{target_revision}"
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    existing_events = load_events(Path(artifact_paths.event_log_path))
    review_channel_path = repo_root / active_path_config().review_channel_rel
    if not review_channel_path.exists():
        return _skipped("missing_review_channel", rollout_path=rollout_path)

    review_state, _ = reduce_events(
        events=existing_events,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
    )
    decision = task_complete_decision(
        session_id=task_complete.session_id,
        packets=review_state.get("packets", ()),
        policy=session_termination_policy_from_review_state(review_state),
        actor=provider,
        actor_role=request.actor_role,
        target_ref=target_ref,
    )
    if not decision.terminate:
        return TaskCompleteHandoffResult(
            status="blocked",
            reason=f"task_complete_rejected_by_policy:{decision.reason}",
            target_revision=target_revision,
            target_ref=target_ref,
            rollout_path=str(rollout_path),
            task_complete_at_utc=task_complete.timestamp,
        )

    if _has_matching_stage_handoff(
        existing_events,
        from_agent=provider,
        target_ref=target_ref,
        target_revision=target_revision,
    ):
        return TaskCompleteHandoffResult(
            status="skipped",
            reason="matching_stage_handoff_exists",
            target_revision=target_revision,
            target_ref=target_ref,
            rollout_path=str(rollout_path),
            task_complete_at_utc=task_complete.timestamp,
        )

    _, event = post_packet(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent=provider,
            to_agent=_clean(request.to_agent) or "claude",
            kind="action_request",
            summary="Stage verified commit pipeline",
            body=_handoff_body(
                task_complete,
                rollout_path=rollout_path,
                conductor_exit_code=request.conductor_exit_code,
            ),
            requested_action="stage_commit_pipeline",
            policy_hint="review_only",
            approval_required=False,
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref=target_ref,
                target_revision=target_revision,
            ),
            guard_bundle_evidence=PacketGuardBundleEvidenceFields.from_values(
                full_guard_bundle_evidence=request.guard_evidence,
            ),
        ),
    )
    return TaskCompleteHandoffResult(
        status="posted",
        reason="task_complete_without_stage_handoff",
        packet_id=_clean(event.get("packet_id")),
        target_revision=target_revision,
        target_ref=target_ref,
        rollout_path=str(rollout_path),
        task_complete_at_utc=task_complete.timestamp,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default=os.environ.get("REVIEW_CHANNEL_PROVIDER", "codex"))
    parser.add_argument("--to-agent", default=os.environ.get("REVIEW_CHANNEL_HANDOFF_TARGET_AGENT", "claude"))
    parser.add_argument("--repo-root", default=os.environ.get("REVIEW_CHANNEL_CONTROL_ROOT", "."))
    parser.add_argument("--sessions-root", default=os.environ.get("REVIEW_CHANNEL_CODEX_SESSIONS_ROOT", ""))
    parser.add_argument("--target-revision", default=os.environ.get("REVIEW_CHANNEL_HANDOFF_TARGET_REVISION", ""))
    parser.add_argument("--target-ref", default=os.environ.get("REVIEW_CHANNEL_HANDOFF_TARGET_REF", ""))
    parser.add_argument("--actor-role", default=os.environ.get("REVIEW_CHANNEL_HANDOFF_ACTOR_ROLE", ""))
    parser.add_argument("--guard-evidence", default=os.environ.get("REVIEW_CHANNEL_HANDOFF_GUARD_EVIDENCE", "--profile ci"))
    parser.add_argument("--conductor-exit-code", default="")
    args = parser.parse_args(argv)

    result = emit_handoff_for_latest_task_complete(
        TaskCompleteHandoffRequest(
            repo_root=Path(args.repo_root),
            provider=args.provider,
            to_agent=args.to_agent,
            sessions_root=Path(args.sessions_root) if args.sessions_root else None,
            target_revision=args.target_revision,
            target_ref=args.target_ref,
            actor_role=args.actor_role,
            guard_evidence=args.guard_evidence,
            conductor_exit_code=args.conductor_exit_code,
        )
    )
    print(json.dumps(asdict(result), sort_keys=True))
    return 0 if result.status in {"posted", "skipped"} else 1


def _latest_task_complete(rollout_path: Path, *, provider: str) -> RolloutEvent | None:
    task_events = [
        event
        for event in parse_rollout_file(rollout_path, provider=provider, limit=None)
        if event.event_type == "event_msg:task_complete"
    ]
    if not task_events:
        return None
    return max(task_events, key=lambda event: event.timestamp or "")


def _has_matching_stage_handoff(
    events: list[dict[str, object]],
    *,
    from_agent: str,
    target_ref: str,
    target_revision: str,
) -> bool:
    for event in events:
        if _clean(event.get("event_type")) != "packet_posted":
            continue
        if _clean(event.get("kind")) != "action_request":
            continue
        if _clean(event.get("requested_action")) != "stage_commit_pipeline":
            continue
        if _clean(event.get("from_agent")).lower() != from_agent:
            continue
        if _clean(event.get("target_ref")) != target_ref:
            continue
        if _clean(event.get("target_revision")) == target_revision:
            return True
    return False


def _handoff_body(
    task_complete: RolloutEvent,
    *,
    rollout_path: Path,
    conductor_exit_code: str,
) -> str:
    message = _task_complete_message(task_complete)
    lines = [
        "Codex emitted task_complete without a typed stage_commit_pipeline packet.",
        f"task_complete_at_utc: {task_complete.timestamp}",
        f"rollout_path: {rollout_path}",
    ]
    exit_code = _clean(conductor_exit_code)
    if exit_code:
        lines.append(f"conductor_exit_code: {exit_code}")
    if message:
        lines.extend(["", message])
    return "\n".join(lines)


def _task_complete_message(event: RolloutEvent) -> str:
    payload = event.raw_payload.get("payload")
    if isinstance(payload, dict):
        for key in ("last_agent_message", "message"):
            value = _clean(payload.get(key))
            if value:
                return value
    return _clean(event.summary)


def _skipped(
    reason: str,
    *,
    rollout_path: Path | None = None,
) -> TaskCompleteHandoffResult:
    return TaskCompleteHandoffResult(
        status="skipped",
        reason=reason,
        rollout_path=str(rollout_path) if rollout_path is not None else "",
    )


def _clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


if __name__ == "__main__":
    raise SystemExit(main())
