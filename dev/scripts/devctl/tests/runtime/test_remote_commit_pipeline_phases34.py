"""Phase 3/4 regression tests for remote commit pipeline surface convergence."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.commands.vcs.governed_executor import (
    APPROVAL_PACKET_KIND,
    build_commit_action,
    build_commit_approval_request,
    build_stage_action,
)
from dev.scripts.devctl.commands.vcs.push import build_push_action
from dev.scripts.devctl.review_channel.events import (
    post_packet,
    resolve_artifact_paths,
    transition_packet,
)
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketPostRequest,
    PacketRuntimeApprovalFields,
    PacketTargetFields,
    PacketTransitionRequest,
)
from dev.scripts.devctl.review_channel.state import refresh_status_snapshot
from dev.scripts.devctl.runtime.review_state_parser import review_state_from_payload
from dev.scripts.devctl.runtime.startup_context import build_startup_context
from dev.scripts.devctl.tests.review_channel.test_review_channel import (
    _build_bridge_text,
    _build_review_channel_text,
    _write_active_conductor_session,
    _write_live_runtime,
)
from dev.scripts.devctl.tests.runtime.test_startup_context import _minimal_governance
from dev.scripts.devctl.tests.vcs.test_governed_executor import (
    _executor,
    _init_repo,
    _passing_guard_result,
    _run_git,
)


def test_phase4_clean_path_surface_snapshot_alignment(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    remote_root = tmp_path / "remote.git"
    _run_git(remote_root.parent, "init", "--bare", str(remote_root))
    _run_git(repo_root, "remote", "add", "origin", str(remote_root))
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: phase4 clean path",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()
    _approve_pipeline(repo_root=repo_root, pipeline=pipeline)

    commit_result = executor.execute(
        build_commit_action(repo_pack_id="test-pack", pipeline_id=pipeline.pipeline_id)
    )
    assert commit_result.ok is True

    push_result = executor.execute(
        build_push_action(
            repo_pack_id="test-pack",
            branch="feature/pipeline-e2e",
            remote="origin",
            execute=True,
            skip_preflight=True,
            skip_post_push=False,
            requested_by="remote_commit_pipeline",
        )
    )
    assert push_result.ok is True

    review_state, compact, commit_pipeline = _load_review_surfaces(repo_root)
    expected = review_state["snapshot_id"]
    assert expected
    assert compact["snapshot_id"] == expected
    assert compact["doctor"]["snapshot_id"] == expected
    assert review_state["_compat"]["doctor"]["snapshot_id"] == expected
    assert review_state["commit_pipeline"]["snapshot_id"] == expected
    assert commit_pipeline["snapshot_id"] == expected


def test_phase4_rescue_path_recovers_doctor_health_and_snapshot(tmp_path: Path) -> None:
    root = tmp_path / "rescue"
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_build_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(
        _build_bridge_text(
            current_verdict="- Reviewer-accepted.",
            open_findings="- none",
        ),
        encoding="utf-8",
    )
    status_dir = root / "dev/reports/review_channel/latest"

    with (
        patch(
            "dev.scripts.devctl.review_channel.state.compute_non_audit_worktree_hash",
            return_value="a" * 64,
        ),
        patch(
            "dev.scripts.devctl.review_channel.reviewer_worker.compute_non_audit_worktree_hash",
            return_value="a" * 64,
        ),
    ):
        first = refresh_status_snapshot(
            repo_root=root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=status_dir,
        )
    first_review_state, first_compact, _ = _load_snapshot_surfaces(first)
    assert first_compact["doctor"]["status"] == "runtime_missing"

    _write_live_runtime(status_dir)
    _write_active_conductor_session(status_dir, provider="codex")
    _write_active_conductor_session(status_dir, provider="claude")
    with (
        patch(
            "dev.scripts.devctl.review_channel.state.compute_non_audit_worktree_hash",
            return_value="a" * 64,
        ),
        patch(
            "dev.scripts.devctl.review_channel.reviewer_worker.compute_non_audit_worktree_hash",
            return_value="a" * 64,
        ),
        ):
            second = refresh_status_snapshot(
                repo_root=root,
                bridge_path=bridge_path,
                review_channel_path=review_channel_path,
                output_root=status_dir,
            )
    second_review_state, second_compact, second_pipeline = _load_snapshot_surfaces(second)
    assert second_compact["doctor"]["status"] == "reviewer_completion_unrecorded"
    assert second_review_state["snapshot_id"] != first_review_state["snapshot_id"]
    assert second_compact["snapshot_id"] == second_review_state["snapshot_id"]
    assert second_compact["doctor"]["snapshot_id"] == second_review_state["snapshot_id"]
    assert second_pipeline["snapshot_id"] == second_review_state["snapshot_id"]


def test_phase4_surface_convergence_across_startup_push_doctor_and_bridge_projection(
    tmp_path: Path,
) -> None:
    root = tmp_path / "startup"
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_build_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(
        _build_bridge_text(
            current_verdict="- Reviewer-accepted.",
            open_findings="- none",
        ),
        encoding="utf-8",
    )
    status_dir = root / "dev/reports/review_channel/latest"
    _write_live_runtime(status_dir)
    snapshot = refresh_status_snapshot(
        repo_root=root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir,
    )
    review_state_payload, compact_payload, _ = _load_snapshot_surfaces(snapshot)
    review_state = review_state_from_payload(review_state_payload)
    assert review_state is not None

    with (
        patch(
            "dev.scripts.devctl.governance.draft.scan_repo_governance",
            return_value=_minimal_governance(),
        ),
        patch(
            "dev.scripts.devctl.runtime.startup_context.load_current_review_state",
            return_value=review_state,
        ),
        patch(
            "dev.scripts.devctl.runtime.startup_context._load_startup_review_state",
            return_value=review_state,
        ),
        patch(
            "dev.scripts.devctl.runtime.startup_context.build_work_intake_packet",
            return_value=None,
        ),
        patch(
            "dev.scripts.devctl.runtime.startup_context._load_startup_coordination_snapshot",
            return_value=None,
        ),
        patch(
            "dev.scripts.devctl.runtime.startup_context.load_startup_quality_signals",
            return_value={},
        ),
    ):
        startup = build_startup_context(repo_root=root)

    expected = review_state_payload["snapshot_id"]
    assert startup.snapshot_id == expected
    assert startup.push_decision.snapshot_id == expected
    assert review_state_payload["_compat"]["doctor"]["snapshot_id"] == expected
    assert (
        review_state_payload["_compat"]["bridge_projection"]["metadata"]["snapshot_id"]
        == expected
    )
    assert compact_payload["push_decision"]["snapshot_id"] == expected
    assert "snapshot_id" in startup.contract_ownership_map["ReviewState"]["startup_surface_tokens"]
    assert (
        "snapshot_id"
        in startup.contract_ownership_map["RemoteCommitPipelineContract"]["startup_surface_tokens"]
    )


def test_phase4_remote_session_commit_approval_stays_generation_bound(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: phase4 remote session",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()
    approval_request = build_commit_approval_request(pipeline)
    assert approval_request.target.target_revision == pipeline.generation_id
    assert approval_request.runtime_approval.pipeline_generation == pipeline.generation_id
    assert (
        approval_request.runtime_approval.staged_snapshot_hash
        == pipeline.intent.staged_tree_hash
    )

    decision_event = _approve_pipeline(repo_root=repo_root, pipeline=pipeline)
    commit_result = executor.execute(
        build_commit_action(repo_pack_id="test-pack", pipeline_id=pipeline.pipeline_id)
    )
    assert commit_result.ok is True

    updated_pipeline = executor.load_pipeline()
    assert updated_pipeline.approval_state == "approved"
    assert updated_pipeline.commit_sha
    assert updated_pipeline.intent.staged_tree_hash in updated_pipeline.approved_target_identity
    assert decision_event["pipeline_generation"] == pipeline.generation_id
    assert decision_event["target_revision"] == pipeline.generation_id


def _approve_pipeline(
    *,
    repo_root: Path,
    pipeline,
) -> dict[str, object]:
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(pipeline),
    )
    _, decision_event = post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="operator",
            to_agent="system",
            kind=APPROVAL_PACKET_KIND,
            summary="Approve governed commit pipeline",
            body="Operator approved the guarded staged snapshot.",
            requested_action="approve_commit_pipeline",
            policy_hint="operator_approval_required",
            approval_required=False,
            trace_id=pipeline.pipeline_id,
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref=f"remote_commit_pipeline:{pipeline.pipeline_id}",
                target_revision=pipeline.generation_id,
            ),
            runtime_approval=PacketRuntimeApprovalFields.from_values(
                pipeline_generation=pipeline.generation_id,
                staged_snapshot_hash=pipeline.intent.staged_tree_hash,
                guard_results_summary='{"action_id": "quality.guard_bundle", "reason": "", "status": "pass"}',
            ),
        ),
    )
    transition_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event["packet_id"]),
            actor="operator",
        ),
    )
    return decision_event


def _load_review_surfaces(repo_root: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    output_root = repo_root / "dev/reports/review_channel/latest"
    return (
        json.loads((output_root / "review_state.json").read_text(encoding="utf-8")),
        json.loads((output_root / "compact.json").read_text(encoding="utf-8")),
        json.loads((output_root / "commit_pipeline.json").read_text(encoding="utf-8")),
    )


def _load_snapshot_surfaces(snapshot) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    paths = snapshot.projection_paths
    return (
        json.loads(Path(paths.review_state_path).read_text(encoding="utf-8")),
        json.loads(Path(paths.compact_path).read_text(encoding="utf-8")),
        json.loads(Path(paths.commit_pipeline_path).read_text(encoding="utf-8")),
    )
