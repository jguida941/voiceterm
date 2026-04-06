"""Governed typed-action executor for the remote commit/push pipeline."""

from __future__ import annotations

import secrets
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...governance.push_state_support import is_expired
from ...repo_packs import active_path_config
from ...review_channel.event_reducer import load_or_refresh_event_bundle, refresh_event_bundle
from ...review_channel.event_store import resolve_artifact_paths
from ...review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
    persist_remote_commit_pipeline_contract,
)
from ...review_channel.state import refresh_status_snapshot
from ...runtime import ActionResult, TypedAction, review_state_from_payload
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from ...runtime.remote_commit_pipeline_models import (
    CommitIntentState,
    RemoteCommitPipelineContract,
)
from ...runtime.review_state_models import ReviewPacketState
from ...runtime.startup_context import build_startup_context
from ...runtime.vcs import run_git_capture
from .governed_executor_authorization import (
    approved_target_identity,
    build_push_authorization,
)
from .governed_executor_field_access import (
    bool_field,
    field,
    string_field,
    string_value,
)
from .governed_executor_packets import (
    approval_decision_packet,
    build_commit_approval_request,
    latest_matching_packet,
)
from .governed_executor_push_result import pipeline_push_result
from .governed_executor_support import (
    CommitBlock,
    commit_failed_pipeline,
    commit_recorded_pipeline,
    evaluate_commit_readiness,
)
from .push import build_push_args, run_push_action

STAGE_ACTION_ID = "vcs.stage"
COMMIT_ACTION_ID = "vcs.commit"
RECOVER_ACTION_ID = "vcs.pipeline.recover"
APPROVAL_PACKET_KIND = "commit_approval"

_ACTIVE_PIPELINE_STATES = frozenset(
    {
        "drafted",
        "staged",
        "guards_running",
        "guards_passed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
        "commit_recorded",
        "push_pending",
    }
)
_RECOVERABLE_PIPELINE_STATES = frozenset(
    {
        "",
        "guards_failed",
        "rejected",
        "push_blocked",
        "push_completed",
    }
)
_PUSHABLE_PIPELINE_STATES = frozenset(
    {
        "commit_recorded",
        "push_pending",
        "push_blocked",
    }
)


def build_stage_action(
    *,
    repo_pack_id: str,
    paths: Sequence[str] = (),
    commit_message_draft: str,
    push_requested: bool,
    guard_profile: str,
    work_intake_ref: str,
    remote: str = "origin",
    requested_by: str = "remote_commit_pipeline",
) -> TypedAction:
    """Build the canonical typed action for governed staging."""
    parameters: dict[str, object] = {}
    parameters["paths"] = [str(path) for path in paths if str(path).strip()]
    parameters["commit_message_draft"] = commit_message_draft
    parameters["push_requested"] = bool(push_requested)
    parameters["guard_profile"] = guard_profile
    parameters["work_intake_ref"] = work_intake_ref
    parameters["remote"] = remote
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=STAGE_ACTION_ID,
        repo_pack_id=repo_pack_id,
        parameters=parameters,
        requested_by=requested_by,
        dry_run=False,
    )


def build_commit_action(
    *,
    repo_pack_id: str,
    pipeline_id: str,
    requested_by: str = "remote_commit_pipeline",
) -> TypedAction:
    """Build the canonical typed action for governed commit execution."""
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=COMMIT_ACTION_ID,
        repo_pack_id=repo_pack_id,
        parameters={"pipeline_id": pipeline_id},
        requested_by=requested_by,
        dry_run=False,
    )


def build_recover_action(
    *,
    repo_pack_id: str,
    strategy: str = "clear",
    requested_by: str = "remote_commit_pipeline",
) -> TypedAction:
    """Build the canonical typed action for governed pipeline recovery."""
    return TypedAction(
        schema_version=1,
        contract_id="TypedAction",
        action_id=RECOVER_ACTION_ID,
        repo_pack_id=repo_pack_id,
        parameters={"strategy": strategy},
        requested_by=requested_by,
        dry_run=False,
    )


@dataclass(slots=True)
class GovernedVcsExecutor:
    """Repo-owned executor for the remote commit/push pipeline typed actions."""

    repo_root: Path = REPO_ROOT
    bridge_path: Path | None = None
    review_channel_path: Path | None = None
    startup_context_fn: Any = None
    push_policy: object | None = None
    build_post_push_commands_fn: Any = None
    refresh_projections: bool = True

    def __post_init__(self) -> None:
        config = active_path_config()
        if self.bridge_path is None:
            self.bridge_path = self.repo_root / config.bridge_rel
        if self.review_channel_path is None:
            self.review_channel_path = self.repo_root / config.review_channel_rel
        if self.startup_context_fn is None:
            self.startup_context_fn = build_startup_context

    @property
    def projections_root(self) -> Path:
        return Path(resolve_artifact_paths(repo_root=self.repo_root).projections_root)

    def load_pipeline(self) -> RemoteCommitPipelineContract:
        return load_remote_commit_pipeline_contract(output_root=self.projections_root)

    def execute(self, action: TypedAction) -> ActionResult:
        if action.action_id == STAGE_ACTION_ID:
            return self._execute_stage(action)
        if action.action_id == COMMIT_ACTION_ID:
            return self._execute_commit(action)
        if action.action_id == RECOVER_ACTION_ID:
            return self._execute_recover(action)
        if action.action_id == "vcs.push":
            return self._execute_push(action)
        return self._result(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason="unsupported_vcs_action",
            operator_guidance=(
                "Use one of `vcs.stage`, `vcs.commit`, `vcs.push`, or "
                "`vcs.pipeline.recover`."
            ),
        )

    def record_guard_result(
        self,
        guard_result: ActionResult,
        *,
        guard_action_id: str = "quality.guard_bundle",
    ) -> RemoteCommitPipelineContract:
        """Record the existing guard-bundle result on the current pipeline."""
        pipeline = self.load_pipeline()
        if not pipeline.pipeline_id:
            raise ValueError("Cannot record guard result without an active pipeline.")

        next_state = "guards_passed"
        blocked_reason = ""
        approval_state = pipeline.approval_state
        if guard_result.status != ActionOutcome.PASS or not guard_result.ok:
            next_state = "guards_failed"
            blocked_reason = guard_result.reason or f"guard_{guard_result.status}"
            approval_state = "not_requested"

        updated = replace(
            pipeline,
            state=next_state,
            guard_action_id=guard_action_id,
            guard_result=guard_result,
            approval_state=approval_state,
            blocked_reason=blocked_reason,
        )
        self._persist_pipeline(updated)
        return updated

    def _execute_stage(self, action: TypedAction) -> ActionResult:
        startup_context = self.startup_context_fn(repo_root=self.repo_root)
        if bool_field(field(startup_context, "reviewer_gate"), "implementation_blocked"):
            reason = string_field(
                field(startup_context, "reviewer_gate"),
                "implementation_block_reason",
            ) or "reviewer_gate_blocked"
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason=reason,
                operator_guidance=(
                    "Repair the review/startup state before staging a remote "
                    "commit pipeline."
                ),
            )

        current = self.load_pipeline()
        if current.pipeline_id and current.state in _ACTIVE_PIPELINE_STATES:
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="active_pipeline_exists",
                operator_guidance=(
                    "Recover or complete the current remote commit pipeline "
                    "before staging another one."
                ),
                warnings=(f"active_pipeline_id={current.pipeline_id}",),
                artifact_paths=(self._pipeline_artifact_relpath(),),
            )

        dirty_paths = self._dirty_paths()
        selected_paths = _normalize_paths(action.parameters.get("paths"))
        if not dirty_paths:
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="no_changes_to_stage",
                operator_guidance="Create or modify repo files before running `vcs.stage`.",
            )

        if selected_paths:
            outside_scope = sorted(set(dirty_paths) - set(selected_paths))
            if outside_scope:
                return self._result(
                    action_id=action.action_id,
                    ok=False,
                    status=ActionOutcome.FAIL,
                    reason="dirty_paths_outside_scope",
                    operator_guidance=(
                        "Either expand the selected stage scope or clean the "
                        "other dirty paths before retrying."
                    ),
                    warnings=tuple(outside_scope),
                )
        else:
            selected_paths = dirty_paths

        stage_code, _, stage_error = run_git_capture(
            ["add", "-A", "--", *selected_paths],
            repo_root=self.repo_root,
        )
        if stage_code != 0:
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="git_add_failed",
                operator_guidance="Repair the git index error and rerun `vcs.stage`.",
                warnings=((stage_error,) if stage_error else ()),
            )

        staged_paths = self._staged_paths()
        if not staged_paths:
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="no_staged_changes",
                operator_guidance=(
                    "The selected scope did not produce a staged snapshot. "
                    "Adjust the path list or make a real change first."
                ),
            )

        tree_hash = self._index_tree_hash()
        if not tree_hash:
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="staged_tree_hash_unavailable",
                operator_guidance="Repair the git index state and rerun `vcs.stage`.",
            )

        pipeline_id = f"pipeline-{secrets.token_hex(6)}"
        generation_id = f"gen-{secrets.token_hex(6)}"
        remote = string_value(action.parameters.get("remote")) or "origin"
        intent = CommitIntentState(
            staged_tree_hash=tree_hash,
            staged_path_count=len(staged_paths),
            staged_paths=tuple(staged_paths),
            diff_summary=self._staged_diff_summary(),
            commit_message_draft=string_value(
                action.parameters.get("commit_message_draft")
            ),
            push_requested=bool(action.parameters.get("push_requested")),
            guard_profile=string_value(action.parameters.get("guard_profile")),
            work_intake_ref=string_value(action.parameters.get("work_intake_ref")),
        )
        pipeline = RemoteCommitPipelineContract(
            pipeline_id=pipeline_id,
            state="staged",
            requested_by=action.requested_by,
            branch=self._current_branch(),
            remote=remote,
            intent=intent,
            blocked_reason="",
            recovery_action_allowed=RECOVER_ACTION_ID,
            generation_id=generation_id,
        )
        warnings = self._persist_pipeline(pipeline)
        return self._result(
            action_id=action.action_id,
            ok=True,
            status=ActionOutcome.PASS,
            reason="pipeline_staged",
            operator_guidance=(
                "Run the routed guard bundle, then post the operator approval "
                "packet before `vcs.commit`."
            ),
            warnings=tuple(warnings),
            artifact_paths=(self._pipeline_artifact_relpath(),),
        )

    def _execute_commit(self, action: TypedAction) -> ActionResult:
        artifact_relpath = self._pipeline_artifact_relpath()

        pipeline = self.load_pipeline()
        requested_pipeline_id = string_value(action.parameters.get("pipeline_id"))
        if not pipeline.pipeline_id or (
            requested_pipeline_id and requested_pipeline_id != pipeline.pipeline_id
        ):
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="pipeline_not_found",
                operator_guidance="Stage a pipeline first, then rerun `vcs.commit`.",
            )

        pipeline = self._sync_pipeline_approval(pipeline)
        readiness = evaluate_commit_readiness(
            pipeline=pipeline,
            current_tree_hash=self._index_tree_hash(),
            requested_commit_message=string_value(
                action.parameters.get("commit_message_draft")
            ),
        )
        if isinstance(readiness, CommitBlock):
            return self._commit_blocked_result(
                action_id=action.action_id,
                pipeline=readiness.pipeline,
                reason=readiness.reason,
                guidance=readiness.guidance,
            )
        pipeline = readiness.pipeline
        commit_message = readiness.commit_message

        commit_pending = replace(
            pipeline,
            state="commit_pending",
            commit_action_id=action.action_id,
            blocked_reason="",
        )
        self._persist_pipeline(commit_pending)
        commit_code, _, commit_error = run_git_capture(
            ["commit", "-m", commit_message],
            repo_root=self.repo_root,
        )
        if commit_code != 0:
            failed = commit_failed_pipeline(
                pending_pipeline=commit_pending,
                action_id=action.action_id,
                commit_error=commit_error,
                artifact_relpath=artifact_relpath,
                result_builder=self._result,
            )
            warnings = self._persist_pipeline(failed)
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="commit_failed",
                operator_guidance=(
                    "Inspect the git commit failure, repair the repo state, "
                    "then recover the pipeline."
                ),
                warnings=tuple(warnings + ([commit_error] if commit_error else [])),
                artifact_paths=(artifact_relpath,),
            )

        commit_sha = self._head_commit()
        completed = commit_recorded_pipeline(
            pending_pipeline=commit_pending,
            action_id=action.action_id,
            commit_sha=commit_sha,
            push_authorization=build_push_authorization(
                pipeline=commit_pending,
                commit_sha=commit_sha,
                decision_packet=self._approval_decision_packet(commit_pending),
                approval_mode="commit_pipeline_approval",
                request_packet_id=commit_pending.approval_packet_id,
            ),
            artifact_relpath=artifact_relpath,
            result_builder=self._result,
        )
        warnings = self._persist_pipeline(completed)
        return self._result(
            action_id=action.action_id,
            ok=True,
            status=ActionOutcome.PASS,
            reason="commit_recorded",
            operator_guidance=(
                "Run the existing governed `vcs.push` action to publish the "
                "new commit."
            ),
            warnings=tuple(warnings),
            artifact_paths=(artifact_relpath,),
        )

    def _execute_push(self, action: TypedAction) -> ActionResult:
        pipeline = self._sync_pipeline_push_authorization(self.load_pipeline())
        if pipeline.state not in _PUSHABLE_PIPELINE_STATES or not pipeline.commit_sha:
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="commit_not_ready_for_push",
                operator_guidance=(
                    "Record the governed commit before requesting the existing "
                    "`vcs.push` action."
                ),
            )

        push_args = build_push_args(
            remote=string_value(action.parameters.get("remote")) or pipeline.remote,
            quality_policy=(
                string_value(action.parameters.get("quality_policy")) or None
            ),
            execute=bool(action.parameters.get("execute", not action.dry_run)),
            skip_preflight=bool(action.parameters.get("skip_preflight")),
            skip_post_push=bool(action.parameters.get("skip_post_push")),
            approved_target_identity=pipeline.approved_target_identity or None,
            format="json",
        )
        pending = replace(
            pipeline,
            state="push_pending",
            push_action_id=action.action_id,
            blocked_reason="",
        )
        self._persist_pipeline(pending)
        _, report = run_push_action(
            push_args,
            repo_root=self.repo_root,
            policy=self.push_policy,
            emit_output_report=False,
            build_post_push_commands_fn=self.build_post_push_commands_fn,
        )
        push_result = pipeline_push_result(
            action_id=action.action_id,
            report=report,
        )
        push_report_path = string_value(
            field(report, "artifacts", {}) if isinstance(report, dict) else {}
        )
        artifacts = ()
        if isinstance(report, dict):
            artifacts_dict = report.get("artifacts")
            if isinstance(artifacts_dict, dict):
                latest_json = string_value(artifacts_dict.get("latest_json"))
                if latest_json:
                    artifacts = (latest_json,)
                    push_report_path = latest_json

        stages = report.get("push_stages", {}) if isinstance(report, dict) else {}
        push_completed = bool(
            isinstance(stages, dict)
            and stages.get("published_remote")
            and stages.get("post_push_green")
        )
        next_state = "push_completed" if push_completed else "push_blocked"
        blocked_reason = "" if push_completed else string_value(report.get("reason"))
        updated = replace(
            pending,
            state=next_state,
            push_result=push_result,
            push_report_path=push_report_path,
            blocked_reason=blocked_reason,
        )
        warnings = self._persist_pipeline(updated)
        return self._result(
            action_id=action.action_id,
            ok=push_result.ok,
            status=push_result.status,
            reason=push_result.reason,
            retryable=push_result.retryable,
            partial_progress=push_result.partial_progress,
            operator_guidance=push_result.operator_guidance,
            warnings=tuple(warnings + list(push_result.warnings)),
            artifact_paths=tuple(
                list(artifacts or ()) + [self._pipeline_artifact_relpath()]
            ),
        )

    def _execute_recover(self, action: TypedAction) -> ActionResult:
        pipeline = self.load_pipeline()
        strategy = string_value(action.parameters.get("strategy")) or "clear"
        force = bool(action.parameters.get("force"))
        if not force and pipeline.pipeline_id and pipeline.state not in _RECOVERABLE_PIPELINE_STATES:
            return self._result(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="pipeline_not_recoverable",
                operator_guidance=(
                    "Only blocked, rejected, completed, or empty pipelines may "
                    "be recovered without `force=true`."
                ),
            )

        if strategy == "restage":
            if not pipeline.intent.staged_paths:
                return self._result(
                    action_id=action.action_id,
                    ok=False,
                    status=ActionOutcome.FAIL,
                    reason="no_restage_intent",
                    operator_guidance=(
                        "The current pipeline does not carry a reusable staged "
                        "scope. Clear it or stage a new pipeline instead."
                    ),
                )
            stage_action = build_stage_action(
                repo_pack_id=action.repo_pack_id,
                paths=pipeline.intent.staged_paths,
                commit_message_draft=pipeline.intent.commit_message_draft,
                push_requested=pipeline.intent.push_requested,
                guard_profile=pipeline.intent.guard_profile,
                work_intake_ref=pipeline.intent.work_intake_ref,
                remote=pipeline.remote or "origin",
                requested_by=action.requested_by,
            )
            return self._execute_stage(stage_action)

        warnings = self._persist_pipeline(RemoteCommitPipelineContract())
        return self._result(
            action_id=action.action_id,
            ok=True,
            status=ActionOutcome.PASS,
            reason="pipeline_cleared",
            operator_guidance=(
                "The current remote commit pipeline has been cleared. Stage a "
                "fresh snapshot when ready."
            ),
            warnings=tuple(warnings),
            artifact_paths=(self._pipeline_artifact_relpath(),),
        )

    def _commit_blocked_result(
        self,
        *,
        action_id: str,
        pipeline: RemoteCommitPipelineContract,
        reason: str,
        guidance: str,
    ) -> ActionResult:
        warnings = self._persist_pipeline(pipeline)
        return self._result(
            action_id=action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason=reason,
            operator_guidance=guidance,
            warnings=tuple(warnings),
            artifact_paths=(self._pipeline_artifact_relpath(),),
        )

    def _sync_pipeline_approval(
        self,
        pipeline: RemoteCommitPipelineContract,
    ) -> RemoteCommitPipelineContract:
        packets = self._event_packets()
        request_packet = latest_matching_packet(
            packets,
            pipeline,
            require_apply=False,
            request_kind="request",
            approval_packet_kind=APPROVAL_PACKET_KIND,
        )
        decision_packet = latest_matching_packet(
            packets,
            pipeline,
            require_apply=True,
            request_kind="decision",
            approval_packet_kind=APPROVAL_PACKET_KIND,
        )
        approval_state = "not_requested"
        next_state = pipeline.state
        blocked_reason = pipeline.blocked_reason
        approval_expires_at_utc = ""
        approved_identity = ""

        if request_packet is not None:
            approval_state = "pending"
            next_state = "operator_approval_pending"
            blocked_reason = ""
            approval_expires_at_utc = request_packet.expires_at_utc

        if decision_packet is not None:
            approval_expires_at_utc = (
                decision_packet.expires_at_utc or approval_expires_at_utc
            )
            if is_expired(decision_packet.expires_at_utc):
                approval_state = "expired"
                next_state = "push_blocked"
                blocked_reason = "approval_expired"
            elif decision_packet.requested_action == "reject_commit_pipeline":
                approval_state = "rejected"
                next_state = "rejected"
                blocked_reason = "approval_rejected"
            else:
                approval_state = "approved"
                next_state = "approved"
                blocked_reason = ""
                approved_identity = approved_target_identity(
                    staged_tree_hash=pipeline.intent.staged_tree_hash,
                    decision_packet=decision_packet,
                    fallback_generation=pipeline.generation_id,
                )

        return replace(
            pipeline,
            state=next_state,
            approval_packet_id=(
                request_packet.packet_id if request_packet is not None else ""
            ),
            decision_packet_id=(
                decision_packet.packet_id if decision_packet is not None else ""
            ),
            approval_state=approval_state,
            approval_expires_at_utc=approval_expires_at_utc,
            approved_target_identity=approved_identity,
            blocked_reason=blocked_reason,
        )

    def _approval_decision_packet(
        self,
        pipeline: RemoteCommitPipelineContract,
    ) -> ReviewPacketState:
        return approval_decision_packet(
            self._event_packets(),
            pipeline,
            approval_packet_kind=APPROVAL_PACKET_KIND,
        )

    def _sync_pipeline_push_authorization(
        self,
        pipeline: RemoteCommitPipelineContract,
    ) -> RemoteCommitPipelineContract:
        if not pipeline.commit_sha:
            return pipeline
        override_packet = latest_matching_packet(
            self._event_packets(),
            pipeline,
            require_apply=True,
            request_kind="override_decision",
            approval_packet_kind=APPROVAL_PACKET_KIND,
            allowed_target_revisions=(pipeline.approved_target_identity,),
        )
        if override_packet is None or is_expired(override_packet.expires_at_utc):
            return pipeline
        authorization = build_push_authorization(
            pipeline=pipeline,
            commit_sha=pipeline.commit_sha,
            decision_packet=override_packet,
            approval_mode="override_push",
            override_reason=string_value(override_packet.summary)
            or string_value(override_packet.body),
        )
        if pipeline.push_authorization == authorization:
            return pipeline
        updated = replace(
            pipeline,
            push_authorization=authorization,
        )
        self._persist_pipeline(updated)
        return updated

    def _persist_pipeline(self, pipeline: RemoteCommitPipelineContract) -> list[str]:
        persist_remote_commit_pipeline_contract(pipeline, output_root=self.projections_root)
        legacy_root = self.repo_root / active_path_config().review_status_dir_rel
        if legacy_root.resolve() != self.projections_root.resolve():
            persist_remote_commit_pipeline_contract(pipeline, output_root=legacy_root)
        return self._refresh_review_projections()

    def _refresh_review_projections(self) -> list[str]:
        if not self.refresh_projections or self.review_channel_path is None:
            return []
        warnings: list[str] = []
        try:
            artifact_paths = resolve_artifact_paths(repo_root=self.repo_root)
            event_log = Path(artifact_paths.event_log_path)
            state_path = Path(artifact_paths.state_path)
            if event_log.exists() or state_path.exists():
                refresh_event_bundle(
                    repo_root=self.repo_root,
                    review_channel_path=self.review_channel_path,
                    artifact_paths=artifact_paths,
                )
            elif self.bridge_path is not None and self.bridge_path.exists():
                refresh_status_snapshot(
                    repo_root=self.repo_root,
                    bridge_path=self.bridge_path,
                    review_channel_path=self.review_channel_path,
                    output_root=self.projections_root,
                )
        except (OSError, ValueError) as exc:
            warnings.append(f"projection_refresh_failed: {exc}")
        return warnings

    def _event_packets(self) -> tuple[ReviewPacketState, ...]:
        if self.review_channel_path is None or not self.review_channel_path.exists():
            return ()
        artifact_paths = resolve_artifact_paths(repo_root=self.repo_root)
        event_log = Path(artifact_paths.event_log_path)
        state_path = Path(artifact_paths.state_path)
        if not event_log.exists() and not state_path.exists():
            return ()
        try:
            bundle = load_or_refresh_event_bundle(
                repo_root=self.repo_root,
                review_channel_path=self.review_channel_path,
                artifact_paths=artifact_paths,
            )
        except ValueError:
            return ()
        return review_state_from_payload(bundle.review_state).packets

    def _dirty_paths(self) -> list[str]:
        code, output, error = run_git_capture(
            ["status", "--porcelain", "--untracked-files=all"],
            repo_root=self.repo_root,
        )
        if code != 0:
            raise ValueError(error or "git status failed")
        dirty_paths: list[str] = []
        ignored_prefixes = _ignored_prefixes()
        for line in output.splitlines():
            if not line:
                continue
            parts = line.split(maxsplit=1)
            path = parts[1] if len(parts) == 2 else ""
            if "->" in path:
                path = path.split("->")[-1].strip()
            normalized = path.strip()
            if not normalized or _path_is_ignored(normalized, ignored_prefixes):
                continue
            dirty_paths.append(normalized)
        return dirty_paths

    def _staged_paths(self) -> list[str]:
        code, output, error = run_git_capture(
            ["diff", "--cached", "--name-only", "--diff-filter=ACDMRTUXB"],
            repo_root=self.repo_root,
        )
        if code != 0:
            raise ValueError(error or "git diff --cached failed")
        return [line.strip() for line in output.splitlines() if line.strip()]

    def _staged_diff_summary(self) -> str:
        code, output, error = run_git_capture(
            ["diff", "--cached", "--stat"],
            repo_root=self.repo_root,
        )
        if code != 0:
            raise ValueError(error or "git diff --cached --stat failed")
        return output

    def _index_tree_hash(self) -> str:
        code, output, _ = run_git_capture(["write-tree"], repo_root=self.repo_root)
        return output if code == 0 else ""

    def _current_branch(self) -> str:
        code, output, _ = run_git_capture(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            repo_root=self.repo_root,
        )
        return output if code == 0 else ""

    def _head_commit(self) -> str:
        code, output, _ = run_git_capture(["rev-parse", "HEAD"], repo_root=self.repo_root)
        return output if code == 0 else ""

    def _pipeline_artifact_relpath(self) -> str:
        return _repo_relpath(
            self.projections_root / "commit_pipeline.json",
            repo_root=self.repo_root,
        )

    def _result(
        self,
        *,
        action_id: str,
        ok: bool,
        status: str,
        reason: str,
        retryable: bool = False,
        partial_progress: bool = False,
        operator_guidance: str = "",
        warnings: Sequence[str] = (),
        artifact_paths: Sequence[str] = (),
    ) -> ActionResult:
        return ActionResult(
            schema_version=ACTION_RESULT_SCHEMA_VERSION,
            contract_id=ACTION_RESULT_CONTRACT_ID,
            action_id=action_id,
            ok=ok,
            status=status,
            reason=reason,
            retryable=retryable,
            partial_progress=partial_progress,
            operator_guidance=operator_guidance,
            warnings=tuple(warnings),
            artifact_paths=tuple(artifact_paths),
        )


def _ignored_prefixes() -> tuple[str, ...]:
    config = active_path_config()
    prefixes = [
        config.review_status_dir_rel.strip("/"),
        config.review_artifact_root_rel.strip("/"),
        config.push_report_rel.strip("/"),
        config.bridge_rel.strip("/"),
        "convo.md",
    ]
    return tuple(prefix for prefix in prefixes if prefix)


def _path_is_ignored(path: str, prefixes: Sequence[str]) -> bool:
    for prefix in prefixes:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def _normalize_paths(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    paths: list[str] = []
    for item in value:
        text = string_value(item)
        if text:
            paths.append(text)
    return paths




def _repo_relpath(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())
