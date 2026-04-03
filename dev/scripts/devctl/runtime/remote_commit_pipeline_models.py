"""Typed models for the remote-session commit/push pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .action_contracts import ActionResult, action_result_from_mapping
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)


REMOTE_COMMIT_PIPELINE_CONTRACT_ID = "RemoteCommitPipelineContract"
REMOTE_COMMIT_PIPELINE_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class CommitIntentState:
    """Immutable staged-work snapshot shared across pipeline steps."""

    staged_tree_hash: str = ""
    staged_path_count: int = 0
    staged_paths: tuple[str, ...] = ()
    diff_summary: str = ""
    commit_message_draft: str = ""
    push_requested: bool = False
    guard_profile: str = ""
    work_intake_ref: str = ""

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        payload["staged_tree_hash"] = self.staged_tree_hash
        payload["staged_path_count"] = self.staged_path_count
        payload["staged_paths"] = list(self.staged_paths)
        payload["diff_summary"] = self.diff_summary
        payload["commit_message_draft"] = self.commit_message_draft
        payload["push_requested"] = self.push_requested
        payload["guard_profile"] = self.guard_profile
        payload["work_intake_ref"] = self.work_intake_ref
        return payload


@dataclass(frozen=True, slots=True)
class RemoteCommitPipelineContract:
    """Canonical read-only owner for remote commit/push lifecycle state."""

    schema_version: int = REMOTE_COMMIT_PIPELINE_SCHEMA_VERSION
    contract_id: str = REMOTE_COMMIT_PIPELINE_CONTRACT_ID
    pipeline_id: str = ""
    state: str = "push_blocked"
    requested_by: str = ""
    branch: str = ""
    remote: str = ""
    intent: CommitIntentState = field(default_factory=CommitIntentState)
    guard_action_id: str = ""
    guard_result: ActionResult | None = None
    reviewer_runtime_generation: str = ""
    approval_packet_id: str = ""
    decision_packet_id: str = ""
    approval_state: str = "not_requested"
    commit_action_id: str = ""
    commit_result: ActionResult | None = None
    commit_sha: str = ""
    push_action_id: str = ""
    push_result: ActionResult | None = None
    push_report_path: str = ""
    blocked_reason: str = "pipeline_unavailable"
    recovery_action_allowed: str = ""
    generation_id: str = ""
    approval_expires_at_utc: str = ""
    approved_target_identity: str = ""
    snapshot_id: str = ""

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        payload["schema_version"] = self.schema_version
        payload["contract_id"] = self.contract_id
        payload["pipeline_id"] = self.pipeline_id
        payload["state"] = self.state
        payload["requested_by"] = self.requested_by
        payload["branch"] = self.branch
        payload["remote"] = self.remote
        payload["intent"] = self.intent.to_dict()
        payload["guard_action_id"] = self.guard_action_id
        payload["guard_result"] = (
            self.guard_result.to_dict() if self.guard_result is not None else None
        )
        payload["reviewer_runtime_generation"] = self.reviewer_runtime_generation
        payload["approval_packet_id"] = self.approval_packet_id
        payload["decision_packet_id"] = self.decision_packet_id
        payload["approval_state"] = self.approval_state
        payload["commit_action_id"] = self.commit_action_id
        payload["commit_result"] = (
            self.commit_result.to_dict() if self.commit_result is not None else None
        )
        payload["commit_sha"] = self.commit_sha
        payload["push_action_id"] = self.push_action_id
        payload["push_result"] = (
            self.push_result.to_dict() if self.push_result is not None else None
        )
        payload["push_report_path"] = self.push_report_path
        payload["blocked_reason"] = self.blocked_reason
        payload["recovery_action_allowed"] = self.recovery_action_allowed
        payload["generation_id"] = self.generation_id
        payload["approval_expires_at_utc"] = self.approval_expires_at_utc
        payload["approved_target_identity"] = self.approved_target_identity
        payload["snapshot_id"] = self.snapshot_id
        return payload


def commit_intent_state_from_mapping(payload: Mapping[str, object]) -> CommitIntentState:
    """Normalize one commit-intent mapping into the shared typed model."""
    mapping = coerce_mapping(payload)
    return CommitIntentState(
        staged_tree_hash=coerce_string(mapping.get("staged_tree_hash")),
        staged_path_count=coerce_int(mapping.get("staged_path_count")),
        staged_paths=coerce_string_items(mapping.get("staged_paths")),
        diff_summary=coerce_string(mapping.get("diff_summary")),
        commit_message_draft=coerce_string(mapping.get("commit_message_draft")),
        push_requested=coerce_bool(mapping.get("push_requested")),
        guard_profile=coerce_string(mapping.get("guard_profile")),
        work_intake_ref=coerce_string(mapping.get("work_intake_ref")),
    )


def remote_commit_pipeline_contract_from_mapping(
    payload: Mapping[str, object],
) -> RemoteCommitPipelineContract:
    """Normalize one pipeline mapping into the shared typed contract."""
    mapping = coerce_mapping(payload)
    if not mapping:
        return RemoteCommitPipelineContract()

    return RemoteCommitPipelineContract(
        schema_version=coerce_int(mapping.get("schema_version"))
        or REMOTE_COMMIT_PIPELINE_SCHEMA_VERSION,
        contract_id=coerce_string(mapping.get("contract_id"))
        or REMOTE_COMMIT_PIPELINE_CONTRACT_ID,
        pipeline_id=coerce_string(mapping.get("pipeline_id")),
        state=coerce_string(mapping.get("state")) or "push_blocked",
        requested_by=coerce_string(mapping.get("requested_by")),
        branch=coerce_string(mapping.get("branch")),
        remote=coerce_string(mapping.get("remote")),
        intent=commit_intent_state_from_mapping(coerce_mapping(mapping.get("intent"))),
        guard_action_id=coerce_string(mapping.get("guard_action_id")),
        guard_result=_action_result_from_object(mapping.get("guard_result")),
        reviewer_runtime_generation=coerce_string(
            mapping.get("reviewer_runtime_generation")
        ),
        approval_packet_id=coerce_string(mapping.get("approval_packet_id")),
        decision_packet_id=coerce_string(mapping.get("decision_packet_id")),
        approval_state=coerce_string(mapping.get("approval_state")) or "not_requested",
        commit_action_id=coerce_string(mapping.get("commit_action_id")),
        commit_result=_action_result_from_object(mapping.get("commit_result")),
        commit_sha=coerce_string(mapping.get("commit_sha")),
        push_action_id=coerce_string(mapping.get("push_action_id")),
        push_result=_action_result_from_object(mapping.get("push_result")),
        push_report_path=coerce_string(mapping.get("push_report_path")),
        blocked_reason=coerce_string(mapping.get("blocked_reason"))
        or "pipeline_unavailable",
        recovery_action_allowed=coerce_string(mapping.get("recovery_action_allowed")),
        generation_id=coerce_string(mapping.get("generation_id")),
        approval_expires_at_utc=coerce_string(mapping.get("approval_expires_at_utc")),
        approved_target_identity=coerce_string(
            mapping.get("approved_target_identity")
        ),
        snapshot_id=coerce_string(mapping.get("snapshot_id")),
    )


def _action_result_from_object(value: object) -> ActionResult | None:
    mapping = coerce_mapping(value)
    if not mapping:
        return None
    return action_result_from_mapping(mapping)
