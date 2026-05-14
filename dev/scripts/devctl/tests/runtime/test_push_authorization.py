"""Tests for persisted publication authorization decisions."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.governance.push_state_authorization import (
    push_authorization_state_from_pipeline,
)
from dev.scripts.devctl.runtime.action_contracts import ActionOutcome
from dev.scripts.devctl.runtime.push_authorization import (
    _snapshot_only_receipt_parent_sha,
    publication_authorization_decision,
)
from dev.scripts.devctl.review_channel.remote_commit_pipeline_artifact import (
    persist_remote_commit_pipeline_contract,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)
from dev.scripts.devctl.runtime.review_snapshot_refresh import (
    GENERATED_SURFACE_RECEIPT_SUBJECT_PREFIX,
)


def _review_state() -> SimpleNamespace:
    return SimpleNamespace(
        bridge=SimpleNamespace(
            session_liveness_signals=(
                {
                    "provider": "codex",
                    "role": "reviewer",
                    "state": "alive",
                },
                {
                    "provider": "claude",
                    "role": "implementer",
                    "state": "alive",
                },
            )
        ),
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="active_dual_agent",
            reviewer_freshness="stale",
            stale_reason="reviewer_missing",
        )
    )


def _single_agent_review_state() -> SimpleNamespace:
    return SimpleNamespace(
        bridge=SimpleNamespace(session_liveness_signals=()),
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
            reviewer_freshness="overdue",
            stale_reason="inactive",
        )
    )


def _tools_only_review_state() -> SimpleNamespace:
    return SimpleNamespace(
        bridge=SimpleNamespace(session_liveness_signals=()),
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="tools_only",
            reviewer_freshness="overdue",
            stale_reason="inactive",
        )
    )


def _pipeline(
    *,
    authorized_head_sha: str,
    worktree_identity: str = "",
) -> RemoteCommitPipelineContract:
    return RemoteCommitPipelineContract(
        pipeline_id="pipeline-123",
        state="commit_recorded",
        commit_sha=authorized_head_sha,
        worktree_identity=worktree_identity,
        approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
        push_authorization=PushAuthorizationRecord(
            authorization_id="push-auth-20260403T010000Z",
            pipeline_id="pipeline-123",
            generation_id="gen-123",
            authorized_head_sha=authorized_head_sha,
            approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
            approval_mode="commit_pipeline_approval",
            guard_action_id="quality.guard_bundle",
            guard_status=ActionOutcome.PASS,
            approved_by="operator",
            approved_at_utc="2026-04-05T12:00:00Z",
            worktree_identity=worktree_identity,
        ),
    )


@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_allows_current_head_with_stale_reviewer_runtime(
    load_pipeline_mock,
    current_head_mock,
    load_review_state_mock,
    _scan_governance_mock,
) -> None:
    load_review_state_mock.return_value = _review_state()
    current_head_mock.return_value = "head-123"
    load_pipeline_mock.return_value = _pipeline(authorized_head_sha="head-123")

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is True
    assert decision.reason == "push_authorization_current"
    assert decision.push_authorization is not None
    assert decision.push_authorization.approval_mode == "commit_pipeline_approval"


def test_publication_authorization_reads_event_backed_pipeline_projection(
    tmp_path: Path,
) -> None:
    projections_root = tmp_path / "dev/reports/review_channel/projections/latest"
    legacy_status_root = tmp_path / "dev/reports/review_channel/latest"
    persist_remote_commit_pipeline_contract(
        RemoteCommitPipelineContract(),
        output_root=legacy_status_root,
    )
    persist_remote_commit_pipeline_contract(
        _pipeline(authorized_head_sha="head-123"),
        output_root=projections_root,
    )

    with (
        patch(
            "dev.scripts.devctl.runtime.push_authorization.scan_repo_governance",
            return_value=None,
        ),
        patch(
            "dev.scripts.devctl.runtime.push_authorization.load_review_state",
            return_value=_review_state(),
        ),
        patch(
            "dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha",
            return_value="head-123",
        ),
        patch(
            "dev.scripts.devctl.runtime.push_authorization.worktree_identity_for_repo",
            return_value="",
        ),
        patch(
            "dev.scripts.devctl.runtime.push_authorization"
            "._snapshot_only_receipt_parent_sha",
            return_value="",
        ),
        patch(
            "dev.scripts.devctl.runtime.push_authorization"
            ".receipt_commit_ancestor_shas",
            return_value=(),
        ),
    ):
        decision = publication_authorization_decision(repo_root=tmp_path)

    assert decision.authorized is True
    assert decision.reason == "push_authorization_current"
    assert decision.push_authorization is not None
    assert decision.push_authorization.authorization_id == "push-auth-20260403T010000Z"


@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch(
    "dev.scripts.devctl.runtime.push_authorization._snapshot_only_receipt_parent_sha"
)
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_blocks_when_head_changes_after_authorization(
    load_pipeline_mock,
    current_head_mock,
    snapshot_parent_mock,
    load_review_state_mock,
    _scan_governance_mock,
) -> None:
    load_review_state_mock.return_value = _review_state()
    current_head_mock.return_value = "head-new"
    snapshot_parent_mock.return_value = ""
    load_pipeline_mock.return_value = _pipeline(authorized_head_sha="head-old")

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is False
    assert decision.reason == "head_changed_after_authorization"
    assert decision.push_authorization is not None


@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch(
    "dev.scripts.devctl.runtime.push_authorization._snapshot_only_receipt_parent_sha"
)
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_allows_snapshot_only_receipt_head(
    load_pipeline_mock,
    current_head_mock,
    snapshot_parent_mock,
    load_review_state_mock,
    _scan_governance_mock,
) -> None:
    load_review_state_mock.return_value = _review_state()
    current_head_mock.return_value = "head-receipt"
    snapshot_parent_mock.return_value = "head-old"
    load_pipeline_mock.return_value = _pipeline(authorized_head_sha="head-old")

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is True
    assert decision.reason == "push_authorization_snapshot_receipt_current"
    assert decision.push_authorization is not None


@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch("dev.scripts.devctl.runtime.push_authorization.receipt_commit_ancestor_shas")
@patch(
    "dev.scripts.devctl.runtime.push_authorization._snapshot_only_receipt_parent_sha"
)
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_allows_managed_receipt_chain(
    load_pipeline_mock,
    current_head_mock,
    snapshot_parent_mock,
    snapshot_ancestors_mock,
    load_review_state_mock,
    _scan_governance_mock,
) -> None:
    load_review_state_mock.return_value = _review_state()
    current_head_mock.return_value = "head-receipt-2"
    snapshot_parent_mock.return_value = "head-old"
    snapshot_ancestors_mock.return_value = ("head-receipt-1", "head-old")
    load_pipeline_mock.return_value = _pipeline(authorized_head_sha="head-old")

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is True
    assert decision.reason == "push_authorization_snapshot_receipt_current"
    assert decision.push_authorization is not None


def test_push_authorization_state_matches_receipt_chain_ancestor() -> None:
    state = push_authorization_state_from_pipeline(
        pipeline=_pipeline(authorized_head_sha="head-old"),
        current_head_commit="head-receipt-2",
        current_approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
        current_worktree_identity="",
        managed_receipt_ancestor_commits=("head-receipt-1", "head-old"),
    )

    assert state[6] is True


def test_snapshot_only_receipt_parent_sha_accepts_bridge_receipt(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("# Seed snapshot\n", encoding="utf-8")
    (repo_root / "bridge.md").write_text("seed bridge\n", encoding="utf-8")
    _git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md", "bridge.md")
    _git(repo_root, "commit", "-m", "Seed receipt artifacts")

    (repo_root / "code.py").write_text("print('governed')\n", encoding="utf-8")
    _git(repo_root, "add", "code.py")
    _git(repo_root, "commit", "-m", "Code change")

    parent_head = _git_output(repo_root, "rev-parse", "HEAD")
    parent_short = _git_output(repo_root, "rev-parse", "--short", "HEAD")
    snapshot_path.write_text("# Receipt snapshot\n", encoding="utf-8")
    (repo_root / "bridge.md").write_text("receipt bridge refresh\n", encoding="utf-8")
    _git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md", "bridge.md")
    _git(
        repo_root,
        "commit",
        "-m",
        f"Refresh external review snapshot for {parent_short}",
    )

    parent = _snapshot_only_receipt_parent_sha(
        repo_root=repo_root,
        current_head=_git_output(repo_root, "rev-parse", "HEAD"),
        governance=SimpleNamespace(
            artifact_roots=SimpleNamespace(
                review_snapshot_path="dev/audits/REVIEW_SNAPSHOT.md"
            )
        ),
    )

    assert parent.startswith(parent_head)


def test_snapshot_receipt_parent_sha_accepts_bridge_only_receipt(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("# Seed snapshot\n", encoding="utf-8")
    (repo_root / "bridge.md").write_text("seed bridge\n", encoding="utf-8")
    _git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md", "bridge.md")
    _git(repo_root, "commit", "-m", "Seed receipt artifacts")

    parent_head = _git_output(repo_root, "rev-parse", "HEAD")
    parent_short = _git_output(repo_root, "rev-parse", "--short", "HEAD")
    (repo_root / "bridge.md").write_text("receipt bridge refresh\n", encoding="utf-8")
    _git(repo_root, "add", "bridge.md")
    _git(
        repo_root,
        "commit",
        "-m",
        f"Refresh external review snapshot for {parent_short}",
    )

    parent = _snapshot_only_receipt_parent_sha(
        repo_root=repo_root,
        current_head=_git_output(repo_root, "rev-parse", "HEAD"),
        governance=SimpleNamespace(
            artifact_roots=SimpleNamespace(
                review_snapshot_path="dev/audits/REVIEW_SNAPSHOT.md"
            )
        ),
    )

    assert parent.startswith(parent_head)


def test_snapshot_receipt_parent_sha_walks_managed_receipt_chain(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("# Seed snapshot\n", encoding="utf-8")
    (repo_root / "bridge.md").write_text("seed bridge\n", encoding="utf-8")
    _git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md", "bridge.md")
    _git(repo_root, "commit", "-m", "Seed receipt artifacts")

    (repo_root / "code.py").write_text("print('governed')\n", encoding="utf-8")
    _git(repo_root, "add", "code.py")
    _git(repo_root, "commit", "-m", "Code change")

    content_head = _git_output(repo_root, "rev-parse", "HEAD")
    content_short = _git_output(repo_root, "rev-parse", "--short", "HEAD")
    snapshot_path.write_text("# Receipt snapshot 1\n", encoding="utf-8")
    _git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md")
    _git(
        repo_root,
        "commit",
        "-m",
        f"Refresh external review snapshot for {content_short}",
    )

    first_receipt_short = _git_output(repo_root, "rev-parse", "--short", "HEAD")
    (repo_root / "bridge.md").write_text("receipt bridge refresh 2\n", encoding="utf-8")
    _git(repo_root, "add", "bridge.md")
    _git(
        repo_root,
        "commit",
        "-m",
        f"Refresh external review snapshot for {first_receipt_short}",
    )

    parent = _snapshot_only_receipt_parent_sha(
        repo_root=repo_root,
        current_head=_git_output(repo_root, "rev-parse", "HEAD"),
        governance=SimpleNamespace(
            artifact_roots=SimpleNamespace(
                review_snapshot_path="dev/audits/REVIEW_SNAPSHOT.md"
            )
        ),
    )

    assert parent.startswith(content_head)


def test_snapshot_receipt_parent_sha_accepts_generated_surface_receipt(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    policy_path = repo_root / "dev/config/devctl_repo_policy.json"
    system_map_path = repo_root / "dev/guides/SYSTEM_MAP.md"
    snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    system_map_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(
        '{"repo_governance":{"surface_generation":{"surfaces":['
        '{"output_path":"dev/guides/SYSTEM_MAP.md",'
        '"tracked":true,"local_only":false}]}}}',
        encoding="utf-8",
    )
    system_map_path.write_text("# SYSTEM_MAP\n\nseed\n", encoding="utf-8")
    snapshot_path.write_text("# Seed snapshot\n", encoding="utf-8")
    _git(
        repo_root,
        "add",
        "dev/config/devctl_repo_policy.json",
        "dev/guides/SYSTEM_MAP.md",
        "dev/audits/REVIEW_SNAPSHOT.md",
    )
    _git(repo_root, "commit", "-m", "Seed generated surface policy")

    content_head = _git_output(repo_root, "rev-parse", "HEAD")
    content_short = _git_output(repo_root, "rev-parse", "--short", "HEAD")
    system_map_path.write_text("# SYSTEM_MAP\n\nrefreshed\n", encoding="utf-8")
    _git(repo_root, "add", "dev/guides/SYSTEM_MAP.md")
    _git(
        repo_root,
        "commit",
        "-m",
        f"{GENERATED_SURFACE_RECEIPT_SUBJECT_PREFIX}{content_short}",
    )

    parent = _snapshot_only_receipt_parent_sha(
        repo_root=repo_root,
        current_head=_git_output(repo_root, "rev-parse", "HEAD"),
        governance=SimpleNamespace(
            artifact_roots=SimpleNamespace(
                review_snapshot_path="dev/audits/REVIEW_SNAPSHOT.md"
            )
        ),
    )

    assert parent.startswith(content_head)


@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch(
    "dev.scripts.devctl.runtime.push_authorization._snapshot_only_receipt_parent_sha"
)
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_ignores_stale_pipeline_in_single_agent_mode(
    load_pipeline_mock,
    current_head_mock,
    snapshot_parent_mock,
    load_review_state_mock,
    _scan_governance_mock,
) -> None:
    load_review_state_mock.return_value = _single_agent_review_state()
    current_head_mock.return_value = "head-new"
    snapshot_parent_mock.return_value = ""
    load_pipeline_mock.return_value = _pipeline(authorized_head_sha="head-old")

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is True
    assert decision.authorization_required is False
    assert decision.reason == "authorization_not_required"


@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_ignores_declared_dual_agent_when_effective_mode_is_tools_only(
    load_pipeline_mock,
    current_head_mock,
    load_review_state_mock,
    _scan_governance_mock,
) -> None:
    load_review_state_mock.return_value = _tools_only_review_state()
    current_head_mock.return_value = "head-new"
    load_pipeline_mock.return_value = RemoteCommitPipelineContract()

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is True
    assert decision.authorization_required is False
    assert decision.reason == "authorization_not_required"


@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_allows_tools_only_runtime_when_exact_head_is_already_authorized(
    load_pipeline_mock,
    current_head_mock,
    load_review_state_mock,
    _scan_governance_mock,
) -> None:
    load_review_state_mock.return_value = _tools_only_review_state()
    current_head_mock.return_value = "head-123"
    load_pipeline_mock.return_value = _pipeline(authorized_head_sha="head-123")

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is True
    assert decision.authorization_required is True
    assert decision.reason == "push_authorization_current"


@patch("dev.scripts.devctl.runtime.push_authorization.worktree_identity_for_repo")
@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_blocks_when_worktree_identity_mismatches(
    load_pipeline_mock,
    current_head_mock,
    load_review_state_mock,
    _scan_governance_mock,
    worktree_identity_mock,
) -> None:
    load_review_state_mock.return_value = _review_state()
    current_head_mock.return_value = "head-123"
    worktree_identity_mock.return_value = "worktree:sha256:primary-lane"
    load_pipeline_mock.return_value = _pipeline(
        authorized_head_sha="head-123",
        worktree_identity="worktree:sha256:worker-lane",
    )

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is False
    assert decision.reason == "push_authorization_worktree_drift"


def _init_git_repo(repo_root: Path) -> None:
    _git(repo_root, "init")
    _git(repo_root, "config", "user.name", "Test User")
    _git(repo_root, "config", "user.email", "test@example.com")


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _git_output(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()
