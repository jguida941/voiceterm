"""Governed typed-action executor for the remote commit/push pipeline."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...repo_packs import active_path_config
from ...review_channel.event_store import resolve_artifact_paths
from ...review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
)
from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.startup_context import build_startup_context
from .governed_executor_actions import (
    APPROVAL_PACKET_KIND,
    COMMIT_ACTION_ID,
    RECOVER_ACTION_ID,
    STAGE_ACTION_ID,
    _PUSHABLE_PIPELINE_STATES,
    _RECOVERABLE_PIPELINE_STATES,
    build_commit_action,
    build_recover_action,
    build_stage_action,
)
from .governed_executor_field_access import string_value
from .governed_executor_git import repo_relpath
from .governed_executor_commit_phase import CommitPipelineContext, execute_commit
from .governed_executor_packets import build_commit_approval_request
from .governed_executor_phases import execute_stage
from .governed_executor_push_result import (
    apply_push_report_projection,
    project_push_report,
)
from .governed_executor_validation import build_validation_receipt
from .governed_executor_sync import (
    load_event_packets,
    persist_pipeline,
    persist_pipeline_contract_only,
    sync_pipeline_push_authorization,
)
from .push import build_push_args, run_push_action


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
            validation_receipt=build_validation_receipt(
                pipeline=pipeline,
                guard_result=guard_result,
                guard_action_id=guard_action_id,
            ),
            approval_state=approval_state,
            blocked_reason=blocked_reason,
        )
        self._persist_pipeline(updated)
        return updated

    def _execute_stage(self, action: TypedAction) -> ActionResult:
        return execute_stage(
            action,
            repo_root=self.repo_root,
            startup_context_fn=self.startup_context_fn,
            load_pipeline=self.load_pipeline,
            persist_pipeline=self._persist_pipeline,
            pipeline_artifact_relpath=self._pipeline_artifact_relpath(),
            result_builder=self._result,
        )

    def _execute_commit(self, action: TypedAction) -> ActionResult:
        # The ReviewSnapshot refresh is wired before approval/staging in
        # `devctl commit` so the approved tree already contains the latest
        # projection. The raw-git hook installer still ships a post-commit
        # receipt hook that delegates to `review-snapshot --receipt-commit`;
        # keep that as the explicit trailing snapshot-only publication path
        # instead of adding an uncommitted post-commit write here.
        return execute_commit(
            action,
            context=CommitPipelineContext(
                repo_root=self.repo_root,
                review_channel_path=self.review_channel_path,
                load_pipeline=self.load_pipeline,
                persist_pipeline=self._persist_pipeline,
                persist_pipeline_contract_only=lambda pipeline: persist_pipeline_contract_only(
                    pipeline,
                    projections_root=self.projections_root,
                    repo_root=self.repo_root,
                )
                or [],
                event_packets_loader=self._event_packets,
                pipeline_artifact_relpath=self._pipeline_artifact_relpath(),
                result_builder=self._result,
            ),
        )

    def _execute_push(self, action: TypedAction) -> ActionResult:
        pipeline = sync_pipeline_push_authorization(
            self.load_pipeline(),
            self._event_packets(),
            approval_packet_kind=APPROVAL_PACKET_KIND,
            persist_fn=self._persist_pipeline,
        )
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
        projection = project_push_report(
            action_id=action.action_id,
            report=report,
            pipeline_artifact_relpath=self._pipeline_artifact_relpath(),
        )
        updated = apply_push_report_projection(pending, projection)
        warnings = self._persist_pipeline(updated)
        return self._result(
            action_id=action.action_id,
            ok=projection.push_result.ok,
            status=projection.push_result.status,
            reason=projection.push_result.reason,
            retryable=projection.push_result.retryable,
            partial_progress=projection.push_result.partial_progress,
            operator_guidance=projection.push_result.operator_guidance,
            warnings=tuple(warnings + list(projection.push_result.warnings)),
            artifact_paths=projection.artifact_paths,
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
                risk_addons=(
                    ()
                    if pipeline.intent.validation_plan is None
                    else pipeline.intent.validation_plan.risk_addons
                ),
                proof_level=(
                    ""
                    if pipeline.intent.validation_plan is None
                    else pipeline.intent.validation_plan.proof_level
                ),
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

    def _persist_pipeline(self, pipeline: RemoteCommitPipelineContract) -> list[str]:
        return persist_pipeline(
            pipeline,
            projections_root=self.projections_root,
            repo_root=self.repo_root,
            refresh_projections=self.refresh_projections,
            review_channel_path=self.review_channel_path,
            bridge_path=self.bridge_path,
        )

    def _event_packets(self) -> tuple:
        return load_event_packets(
            repo_root=self.repo_root,
            review_channel_path=self.review_channel_path,
        )

    def _pipeline_artifact_relpath(self) -> str:
        return repo_relpath(
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
