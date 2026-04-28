"""Completed-handoff gating for governed push recovery-loop repair."""

from __future__ import annotations

from pathlib import Path

from ...governance.push_state import current_head_commit_sha
from ...review_channel.event_store import resolve_artifact_paths
from ...runtime.agent_session_outcome import AgentSessionOutcomeState
from ...runtime.review_snapshot_refresh import receipt_commit_parent_sha
from ...runtime.vcs import run_git_capture
from ...review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
)
from ...review_channel.agent_session_outcome_events import (
    latest_current_completed_handoff_outcome,
)
from .push_recovery_loop_payload import (
    field_value,
    payload_allows_bounded_recovery,
)

_BLOCKED_IMPLEMENTATION_PERMISSIONS = frozenset({"blocked", "suspended"})


def completed_handoff_outcome_for_startup_payload(
    *,
    repo_root: Path,
    payload: dict[str, object],
) -> AgentSessionOutcomeState | None:
    if not payload_is_completed_handoff_repair(payload):
        return None

    try:
        return latest_current_completed_handoff_outcome(
            repo_root=repo_root,
            expected_target_revisions=_handoff_target_revisions(repo_root),
        )
    except (OSError, ValueError):
        return None


def payload_is_completed_handoff_repair(payload: dict[str, object]) -> bool:
    if not payload_allows_bounded_recovery(payload):
        return False

    action = field_value(payload, "advisory_action") or field_value(payload, "action")
    if action != "repair_reviewer_loop":
        return False

    if field_value(payload, "attention_status") != "runtime_missing":
        return False

    permission = field_value(payload, "implementation_permission")
    if permission and permission not in _BLOCKED_IMPLEMENTATION_PERMISSIONS:
        return False

    topology = field_value(payload, "observed_control_topology")
    recovery_basis = field_value(payload, "recovery_basis")
    if topology:
        return topology == "no_live_agents"

    return recovery_basis in {"process_dead", "runtime_missing"}


def _handoff_target_revisions(repo_root: Path) -> tuple[str, ...]:
    current_head = current_head_commit_sha(repo_root=repo_root)
    if not current_head:
        return ()

    revisions: list[str] = [current_head]
    content_head = receipt_commit_parent_sha(
        repo_root=repo_root,
        current_head=current_head,
    ) or current_head
    _append_unique(revisions, content_head)

    pipeline_commit = _current_pipeline_commit_sha(repo_root)
    if pipeline_commit and pipeline_commit == content_head:
        _append_unique(revisions, _commit_parent_sha(repo_root, content_head))
    return tuple(revisions)


def _current_pipeline_commit_sha(repo_root: Path) -> str:
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    pipeline = load_remote_commit_pipeline_contract(
        output_root=Path(artifact_paths.projections_root)
    )
    result = pipeline.commit_result
    if not (result is not None and result.ok and result.action_id == "vcs.commit"):
        return ""
    return str(pipeline.commit_sha or "").strip()


def _commit_parent_sha(repo_root: Path, commit_sha: str) -> str:
    target = str(commit_sha or "").strip()
    if not target:
        return ""
    code, stdout, _ = run_git_capture(
        ["rev-parse", f"{target}^"],
        repo_root=repo_root,
    )
    if code != 0:
        return ""
    return stdout.strip()


def _append_unique(values: list[str], value: str) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)


__all__ = [
    "completed_handoff_outcome_for_startup_payload",
    "payload_is_completed_handoff_repair",
]
