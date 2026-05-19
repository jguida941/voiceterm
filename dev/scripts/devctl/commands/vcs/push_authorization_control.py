"""AgentLoopDecision-compatible projection over push authorization records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ...governance.push_state import current_head_commit_sha
from ...review_channel.remote_commit_pipeline_artifact import (
    load_canonical_remote_commit_pipeline_contract,
)
from ...runtime.push_authorization import publication_authorization_decision


@dataclass(frozen=True, slots=True)
class PushAuthorizationControllerDecision:
    """AgentLoopDecision-compatible projection over one push authorization."""

    receipt_id: str
    source_decision_id: str
    source_snapshot_id: str
    source_latest_event_id: str
    source_head_sha: str
    push_authorization_id: str
    push_authorization_reason: str
    push_authorization_summary: str
    actor_id: str = ""
    actor_role: str = ""
    session_id: str = ""
    contract_id: str = "AgentLoopDecision"
    decision: str = "allow"
    required_action: str = "publish_authorized_head"
    may_mutate: bool = True
    can_run_next_command: bool = True
    allowed_actions: tuple[str, ...] = ("devctl.push.execute", "vcs.push")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["allowed_actions"] = list(self.allowed_actions)
        return payload


def push_authorization_control_decision(
    args: Any,
    *,
    repo_root: Path,
    commit_pipeline: Any = None,
    publication_authorization_fn: Any = None,
) -> dict[str, object]:
    """Derive push obedience authority from the governed commit pipeline."""
    pipeline = (
        commit_pipeline
        if commit_pipeline is not None
        else load_canonical_remote_commit_pipeline_contract(repo_root=repo_root)
    )
    authorization_decision = (
        publication_authorization_fn or publication_authorization_decision
    )(repo_root=repo_root, pipeline=pipeline)
    if not bool(getattr(authorization_decision, "authorized", False)):
        return {}
    authorization = getattr(authorization_decision, "push_authorization", None)
    authorization_id = str(getattr(authorization, "authorization_id", "") or "").strip()
    if not authorization_id:
        return {}
    return PushAuthorizationControllerDecision(
        receipt_id=authorization_id,
        source_decision_id=authorization_id,
        source_snapshot_id=_source_snapshot_id(pipeline, authorization_id),
        source_latest_event_id=_source_latest_event_id(pipeline, authorization),
        source_head_sha=current_head_commit_sha(repo_root=repo_root),
        push_authorization_id=authorization_id,
        push_authorization_reason=str(
            getattr(authorization_decision, "reason", "") or ""
        ),
        push_authorization_summary=str(
            getattr(authorization_decision, "summary", "") or ""
        ),
        actor_id=str(getattr(args, "actor", "") or ""),
        actor_role=str(getattr(args, "role", "") or ""),
        session_id=str(getattr(args, "session_id", "") or ""),
    ).to_dict()


def _source_snapshot_id(pipeline: Any, authorization_id: str) -> str:
    return (
        str(getattr(pipeline, "snapshot_id", "") or "").strip()
        or str(getattr(pipeline, "zref", "") or "").strip()
        or authorization_id
    )


def _source_latest_event_id(pipeline: Any, authorization: Any) -> str:
    return (
        str(getattr(authorization, "decision_packet_id", "") or "").strip()
        or str(getattr(authorization, "request_packet_id", "") or "").strip()
        or str(getattr(pipeline, "decision_packet_id", "") or "").strip()
        or str(getattr(pipeline, "approval_packet_id", "") or "").strip()
    )


__all__ = ["push_authorization_control_decision"]
