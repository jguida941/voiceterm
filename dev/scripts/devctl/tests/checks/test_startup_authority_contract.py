"""Tests for check_startup_authority_contract.py — startup authority guard."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from dev.scripts.checks.startup_authority_contract.command import _build_report
from dev.scripts.checks.startup_authority_contract.runtime_import_staged import (
    collect_staged_import_index_atomicity_findings,
)
from dev.scripts.checks.startup_authority_contract.runtime_checks import (
    collect_concurrent_writer_errors,
    collect_import_index_atomicity_findings,
    collect_post_checkpoint_dirty_worktree_errors,
    collect_reviewer_loop_block_errors,
)
from dev.scripts.devctl.runtime.review_state_parser import review_state_from_payload


def _fake_pipeline(
    *,
    pipeline_id: str = "pipeline-test",
    state: str = "guards_failed",
    staged_tree_hash: str = "deadbeefcafef00d",
    staged_path_count: int = 8,
):
    """Build a minimal pipeline namespace for the parked-at-checkpoint exemption.

    The shape matches the ``RemoteCommitPipelineContract`` attributes that the
    startup-authority check reads: ``pipeline_id``, ``state``, and
    ``intent.{staged_tree_hash, staged_path_count}``. Any looser shape must
    fall back to normal enforcement.
    """
    return SimpleNamespace(
        pipeline_id=pipeline_id,
        state=state,
        intent=SimpleNamespace(
            staged_tree_hash=staged_tree_hash,
            staged_path_count=staged_path_count,
        ),
    )


def _mock_subprocess_run(*_args, **_kwargs):
    """Return a fake CompletedProcess so git calls yield empty strings."""

    class _Fake:
        returncode = 1
        stdout = ""

    return _Fake()


def _setup_full_layout(root: Path) -> None:
    """Create the minimal repo layout that satisfies all startup-authority checks."""
    (root / "dev" / "active").mkdir(parents=True)
    (root / "dev" / "scripts").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (root / "dev" / "active" / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    (root / "dev" / "active" / "MASTER_PLAN.md").write_text(
        "# Master Plan\n", encoding="utf-8"
    )


def _init_git_repo(root: Path) -> None:
    subprocess.run(
        ["git", "init", "-q"],
        cwd=root,
        check=True,
    )


def _commit_repo_snapshot(root: Path, *, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Tests",
            "-c",
            "user.email=tests@example.com",
            "commit",
            "-q",
            "-m",
            message,
        ],
        cwd=root,
        check=True,
    )


def _write_policy(root: Path, payload: dict[str, object]) -> None:
    policy_path = root / "dev" / "config" / "devctl_repo_policy.json"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(json.dumps(payload), encoding="utf-8")


def _fake_governance(
    repo_root: Path,
    *,
    checkpoint_required: bool = False,
    safe_to_continue_editing: bool = True,
    checkpoint_reason: str = "clean_worktree",
    worktree_dirty: bool | None = None,
    worktree_clean: bool | None = None,
    ahead_of_upstream_commits: int | None = 1,
    dirty_path_count: int = 0,
    untracked_path_count: int = 0,
    recommended_action: str = "use_devctl_push",
):
    if worktree_clean is None:
        worktree_clean = safe_to_continue_editing and not checkpoint_required
    if worktree_dirty is None:
        worktree_dirty = not worktree_clean
    return SimpleNamespace(
        docs_authority="AGENTS.md",
        plan_registry=SimpleNamespace(
            registry_path="dev/active/INDEX.md",
            tracker_path="dev/active/MASTER_PLAN.md",
        ),
        path_roots=SimpleNamespace(
            active_docs="dev/active",
            scripts="dev/scripts",
        ),
        repo_identity=SimpleNamespace(repo_name=repo_root.name),
        startup_order=("AGENTS.md", "dev/active/INDEX.md", "dev/active/MASTER_PLAN.md"),
        push_enforcement=SimpleNamespace(
            checkpoint_required=checkpoint_required,
            safe_to_continue_editing=safe_to_continue_editing,
            checkpoint_reason=checkpoint_reason,
            worktree_clean=worktree_clean,
            worktree_dirty=worktree_dirty,
            upstream_ref="origin/main",
            ahead_of_upstream_commits=ahead_of_upstream_commits,
            dirty_path_count=dirty_path_count,
            untracked_path_count=untracked_path_count,
            recommended_action=recommended_action,
        ),
    )


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_all_green(tmp_path: Path) -> None:
    """All required files and dirs present -> ok=True, zero errors."""
    _setup_full_layout(tmp_path)

    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is True
    assert report["errors"] == []
    assert report["checks_passed"] == report["checks_run"]
    assert report["command"] == "check_startup_authority_contract"
    assert report["repo_name"] == tmp_path.name


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_missing_agents_md(tmp_path: Path) -> None:
    """Missing AGENTS.md -> ok=False with a startup-authority error."""
    _setup_full_layout(tmp_path)
    (tmp_path / "AGENTS.md").unlink()

    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    authority_errors = [e for e in report["errors"] if "AGENTS.md" in e]
    assert len(authority_errors) == 1


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_missing_tracker(tmp_path: Path) -> None:
    """Missing MASTER_PLAN.md -> ok=False with tracker errors."""
    _setup_full_layout(tmp_path)
    (tmp_path / "dev" / "active" / "MASTER_PLAN.md").unlink()

    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    tracker_errors = [e for e in report["errors"] if "tracker" in e.lower() or "MASTER_PLAN" in e]
    assert len(tracker_errors) >= 1


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_missing_path_roots(tmp_path: Path) -> None:
    """Empty tmp_path with no dirs -> errors about missing path roots."""
    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    path_root_errors = [
        e for e in report["errors"] if "path_roots" in e or "active_docs" in e or "scripts" in e
    ]
    assert len(path_root_errors) >= 2


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_empty_repo_name(tmp_path: Path) -> None:
    """Empty policy with no git -> repo_name falls back to directory name."""
    report = _build_report(repo_root=tmp_path)

    # Even without policy repo_name, scan_repo_governance falls back to dir name
    assert report["repo_name"] == tmp_path.name
    assert report["repo_name"] != ""


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_uses_policy_bootstrap_paths(tmp_path: Path) -> None:
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    (tmp_path / "tools").mkdir(parents=True)
    (tmp_path / "CONTRIBUTING.md").write_text("# Process\n", encoding="utf-8")
    (tmp_path / "docs" / "plans" / "INDEX.md").write_text(
        "# Index\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "plans" / "MASTER_PLAN.md").write_text(
        "# Master Plan\n", encoding="utf-8"
    )
    _write_policy(
        tmp_path,
        {
            "schema_version": 1,
            "repo_name": "PortableRepo",
            "repo_governance": {
                "surface_generation": {
                    "context": {
                        "process_doc": "CONTRIBUTING.md",
                        "execution_tracker_doc": "docs/plans/MASTER_PLAN.md",
                        "active_registry_doc": "docs/plans/INDEX.md",
                        "python_tooling": "tools/",
                    },
                },
            },
        },
    )

    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is True
    assert report["errors"] == []


def test_startup_authority_fails_when_checkpoint_budget_is_exceeded(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    fake_module = SimpleNamespace(
        scan_repo_governance=lambda _root: _fake_governance(
            tmp_path,
            checkpoint_required=True,
            safe_to_continue_editing=False,
            checkpoint_reason="dirty_path_budget_exceeded",
        )
    )

    with (
        patch(
            "dev.scripts.checks.startup_authority_contract.command.import_repo_module",
            return_value=fake_module,
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_import_index_atomicity_findings",
            return_value=([], []),
        ),
    ):
        report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert report["checkpoint_required"] is True
    assert report["safe_to_continue_editing"] is False
    assert any("over budget" in error for error in report["errors"])


def test_startup_authority_fails_when_local_checkpoint_leaves_dirty_worktree(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    fake_module = SimpleNamespace(
        scan_repo_governance=lambda _root: _fake_governance(
            tmp_path,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            checkpoint_reason="within_dirty_budget",
            worktree_clean=False,
            worktree_dirty=True,
            ahead_of_upstream_commits=1,
            dirty_path_count=2,
            untracked_path_count=1,
            recommended_action="commit_before_push",
        )
    )

    with (
        patch(
            "dev.scripts.checks.startup_authority_contract.command.import_repo_module",
            return_value=fake_module,
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_import_index_atomicity_findings",
            return_value=([], []),
        ),
    ):
        report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert any(
        "dirty worktree after a local checkpoint" in error for error in report["errors"]
    )


def test_startup_authority_allows_pre_checkpoint_dirty_worktree(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    fake_module = SimpleNamespace(
        scan_repo_governance=lambda _root: _fake_governance(
            tmp_path,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            checkpoint_reason="within_dirty_budget",
            worktree_clean=False,
            worktree_dirty=True,
            ahead_of_upstream_commits=0,
            dirty_path_count=2,
            untracked_path_count=1,
            recommended_action="commit_before_push",
        )
    )

    with (
        patch(
            "dev.scripts.checks.startup_authority_contract.command.import_repo_module",
            return_value=fake_module,
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_import_index_atomicity_findings",
            return_value=([], []),
        ),
    ):
        report = _build_report(repo_root=tmp_path)

    assert report["ok"] is True
    assert not any(
        "dirty worktree after a local checkpoint" in error for error in report["errors"]
    )


def test_startup_authority_reports_first_import_atomicity_violation(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    fake_module = SimpleNamespace(
        scan_repo_governance=lambda _root: _fake_governance(tmp_path)
    )
    violation = (
        "app/operator_console/state/snapshots/phone_status_snapshot.py: "
        "`from dev.scripts.devctl.phone_status_views import compact_view` "
        "resolves to module candidates `dev/scripts/devctl/phone_status_views.py`, "
        "`dev/scripts/devctl/phone_status_views/__init__.py` missing from git "
        "index (staged)."
    )

    with (
        patch(
            "dev.scripts.checks.startup_authority_contract.command.import_repo_module",
            return_value=fake_module,
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_import_index_atomicity_findings",
            return_value=([violation], []),
        ),
    ):
        report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert report["import_index_atomicity_violations"] == 1
    assert report["import_index_atomicity_findings"] == [violation]


def test_collect_concurrent_writer_errors_when_outside_scope_dirty_paths_overlap_live_agents(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    _init_git_repo(tmp_path)
    _commit_repo_snapshot(tmp_path, message="seed repo")
    review_root = tmp_path / "dev/reports/review_channel/latest"
    review_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "bridge": {
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
        },
        "review": {"plan_id": "MP-377"},
        "current_session": {
            "last_reviewed_scope": "MP-377",
            "current_instruction": (
                "Stay on `dev/scripts/devctl/runtime/work_intake.py` only."
            ),
            "implementer_ack_state": "current",
        },
        "collaboration": {
            "participants": [
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "live": True,
                    "status": "live",
                },
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "live": True,
                    "status": "live",
                },
            ]
        },
    }
    (review_root / "review_state.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    outside_scope_path = (
        tmp_path / "dev/scripts/devctl/review_channel/session_state_hints.py"
    )
    outside_scope_path.parent.mkdir(parents=True, exist_ok=True)
    outside_scope_path.write_text("# dirty\n", encoding="utf-8")

    errors = collect_concurrent_writer_errors(
        tmp_path,
        _fake_governance(
            tmp_path,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            worktree_clean=False,
            worktree_dirty=True,
            ahead_of_upstream_commits=0,
        ),
        review_state=review_state_from_payload(payload),
    )

    assert len(errors) == 1
    assert "concurrent writer activity" in errors[0].lower()
    assert "session_state_hints.py" in errors[0]


def test_collect_concurrent_writer_errors_when_live_workers_share_one_worktree(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    _init_git_repo(tmp_path)
    _commit_repo_snapshot(tmp_path, message="seed repo")
    review_root = tmp_path / "dev/reports/review_channel/latest"
    review_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "bridge": {
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
        },
        "review": {"plan_id": "MP-377"},
        "current_session": {
            "last_reviewed_scope": "MP-377",
            "current_instruction": (
                "Stay on `dev/scripts/devctl/runtime/work_intake.py` only."
            ),
            "implementer_ack_state": "current",
        },
        "collaboration": {
            "participants": [
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "live": True,
                    "status": "live",
                },
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "live": True,
                    "status": "live",
                },
            ],
            "delegated_work": [
                {
                    "receipt_id": "worker-1",
                    "agent_id": "codex-worker-1",
                    "provider": "codex",
                    "role": "implementer",
                    "owner_session": "codex",
                    "status": "live",
                    "live": True,
                    "lane": "AGENT-1",
                    "worktree": "../codex-voice-wt-a1",
                    "branch": "feature/a1",
                },
                {
                    "receipt_id": "worker-2",
                    "agent_id": "claude-worker-1",
                    "provider": "claude",
                    "role": "implementer",
                    "owner_session": "claude",
                    "status": "live",
                    "live": True,
                    "lane": "AGENT-2",
                    "worktree": "../codex-voice-wt-a1",
                    "branch": "feature/a2",
                },
            ],
        },
    }
    (review_root / "review_state.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    errors = collect_concurrent_writer_errors(
        tmp_path,
        _fake_governance(
            tmp_path,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            worktree_clean=True,
            worktree_dirty=False,
            ahead_of_upstream_commits=0,
        ),
        review_state=review_state_from_payload(payload),
    )

    assert len(errors) == 1
    assert "concurrent writer activity" in errors[0].lower()
    assert "duplicate_delegated_worktrees=../codex-voice-wt-a1" in errors[0]


def test_post_checkpoint_dirty_exempted_when_pipeline_parked_at_guards_failed() -> None:
    """Exact live failing shape: dirty worktree + pipeline parked at guards_failed.

    Router-19 was rejecting ``recommended_action=commit_before_push`` while a
    governed remote-commit pipeline was intentionally holding the frozen
    staged snapshot awaiting reviewer adjudication. The typed pipeline
    contract is the exemption proof, so the collector must return no errors.
    """
    gov = _fake_governance(
        Path("/tmp/repo"),
        worktree_dirty=True,
        worktree_clean=False,
        ahead_of_upstream_commits=1,
        dirty_path_count=11,
        untracked_path_count=0,
        recommended_action="commit_before_push",
    )

    errors = collect_post_checkpoint_dirty_worktree_errors(
        gov,
        pipeline=_fake_pipeline(state="guards_failed"),
        current_tree_hash="deadbeefcafef00d",
    )

    assert errors == []


def test_post_checkpoint_dirty_exempted_when_pipeline_parked_at_staged() -> None:
    """Pre-guard parking: dirty worktree + pipeline in state=staged must exempt.

    ``staged`` is the first parked state after the typed stage action records
    the frozen snapshot; the startup-authority check must not rediscover that
    parking as a contract violation.
    """
    gov = _fake_governance(
        Path("/tmp/repo"),
        worktree_dirty=True,
        worktree_clean=False,
        ahead_of_upstream_commits=1,
        dirty_path_count=8,
        untracked_path_count=0,
        recommended_action="commit_before_push",
    )

    errors = collect_post_checkpoint_dirty_worktree_errors(
        gov,
        pipeline=_fake_pipeline(state="staged"),
        current_tree_hash="deadbeefcafef00d",
    )

    assert errors == []


def test_post_checkpoint_dirty_still_fails_for_post_commit_pipeline_states() -> None:
    """Exemption must not widen into post-commit states where the snapshot is behind a commit.

    ``commit_recorded`` means the staged snapshot already landed as a git
    commit; any remaining dirt is new dirt and deserves the normal
    ``commit_before_push`` rejection. The same holds for ``push_pending``,
    ``push_blocked``, ``push_completed``, and ``rejected`` (the pipeline is
    dead). Checking ``commit_recorded`` is sufficient to prove the narrow
    exemption boundary holds.
    """
    gov = _fake_governance(
        Path("/tmp/repo"),
        worktree_dirty=True,
        worktree_clean=False,
        ahead_of_upstream_commits=1,
        dirty_path_count=3,
        untracked_path_count=0,
        recommended_action="commit_before_push",
    )

    errors = collect_post_checkpoint_dirty_worktree_errors(
        gov, pipeline=_fake_pipeline(state="commit_recorded")
    )

    assert len(errors) == 1
    assert "dirty worktree after a local checkpoint" in errors[0]


def test_post_checkpoint_dirty_still_fails_when_pipeline_id_is_empty() -> None:
    """A pipeline artifact with an empty pipeline_id must NOT trigger the exemption.

    An empty pipeline_id is how the typed artifact represents "no active
    pipeline" — exempting this case would silently disable the check for
    every dirty-after-checkpoint worktree on repos that happen to carry an
    empty pipeline file.
    """
    gov = _fake_governance(
        Path("/tmp/repo"),
        worktree_dirty=True,
        worktree_clean=False,
        ahead_of_upstream_commits=1,
        dirty_path_count=3,
        untracked_path_count=0,
        recommended_action="commit_before_push",
    )

    errors = collect_post_checkpoint_dirty_worktree_errors(
        gov, pipeline=_fake_pipeline(pipeline_id="", state="staged")
    )

    assert len(errors) == 1
    assert "dirty worktree after a local checkpoint" in errors[0]


def test_post_checkpoint_dirty_still_fails_when_staged_tree_hash_is_empty() -> None:
    """A parked-state pipeline with no staged_tree_hash must NOT trigger the exemption.

    The staged_tree_hash is the cross-check that the typed stage action
    actually ran and captured a real index. Without it, the "parking" claim
    is unsupported and the normal enforcement path must still fire.
    """
    gov = _fake_governance(
        Path("/tmp/repo"),
        worktree_dirty=True,
        worktree_clean=False,
        ahead_of_upstream_commits=1,
        dirty_path_count=3,
        untracked_path_count=0,
        recommended_action="commit_before_push",
    )

    errors = collect_post_checkpoint_dirty_worktree_errors(
        gov,
        pipeline=_fake_pipeline(
            state="guards_failed",
            staged_tree_hash="",
            staged_path_count=0,
        ),
    )

    assert len(errors) == 1
    assert "dirty worktree after a local checkpoint" in errors[0]


def test_startup_authority_integration_allows_dirty_when_live_pipeline_parked(
    tmp_path: Path,
) -> None:
    """End-to-end: real ``commit_pipeline.json`` on disk unsticks the live shape.

    Writes a minimal canonical artifact under the repo-local review-status
    dir, then runs ``_build_report`` with a dirty+ahead governance snapshot.
    Proves the loader path is wired correctly and that the exact router-19
    failing shape from the MP-381 live pipeline (state=guards_failed, staged
    snapshot frozen) no longer fails the startup-authority contract.
    """
    _setup_full_layout(tmp_path)
    status_dir = tmp_path / "dev" / "reports" / "review_channel" / "latest"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / "commit_pipeline.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "contract_id": "RemoteCommitPipelineContract",
                "pipeline_id": "pipeline-live-test",
                "state": "guards_failed",
                "intent": {
                    "staged_tree_hash": "93026842b5ba832eec5c72971df8b19c56a0cae8",
                    "staged_path_count": 8,
                },
                "approval_state": "not_requested",
                "blocked_reason": "bundle_failed",
            }
        ),
        encoding="utf-8",
    )
    fake_module = SimpleNamespace(
        scan_repo_governance=lambda _root: _fake_governance(
            tmp_path,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            checkpoint_reason="within_dirty_budget",
            worktree_clean=False,
            worktree_dirty=True,
            ahead_of_upstream_commits=1,
            dirty_path_count=11,
            untracked_path_count=0,
            recommended_action="commit_before_push",
        )
    )

    with (
        patch(
            "dev.scripts.checks.startup_authority_contract.command.import_repo_module",
            return_value=fake_module,
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_import_index_atomicity_findings",
            return_value=([], []),
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_push_decision_contract_errors",
            return_value=[],
        ),
        # F18: stub the live tree-hash so the parked-pipeline exemption can
        # bind against the artifact's staged_tree_hash without needing a
        # real git index in tmp_path.
        patch(
            "dev.scripts.checks.startup_authority_contract.runtime_checks._index_tree_hash",
            return_value="93026842b5ba832eec5c72971df8b19c56a0cae8",
        ),
    ):
        report = _build_report(repo_root=tmp_path)

    assert report["ok"] is True
    assert not any(
        "dirty worktree after a local checkpoint" in error for error in report["errors"]
    )


def test_post_checkpoint_dirty_rejects_when_current_tree_hash_drifts_from_pipeline() -> None:
    """F18: dirty worktree + parked pipeline + drifted current tree -> exemption denied.

    Codex finding F18: the parked-pipeline exemption must stay bound to
    the *current* git index tree hash. If new edits land after staging,
    the staged snapshot has drifted under the operator and ``vcs.commit``
    will later reject the same drift as ``staged_snapshot_changed``.
    The startup-authority check must mirror that contract by refusing
    the exemption whenever the current index hash diverges from
    ``pipeline.intent.staged_tree_hash``, so the dashboard and operator
    surfaces still see the dirty-after-checkpoint error in this case.
    """
    gov = _fake_governance(
        Path("/tmp/repo"),
        worktree_dirty=True,
        worktree_clean=False,
        ahead_of_upstream_commits=1,
        dirty_path_count=11,
        untracked_path_count=0,
        recommended_action="commit_before_push",
    )

    # The pipeline still claims a frozen snapshot at "deadbeefcafef00d",
    # but the worktree has drifted to a different tree ("driftedhash...").
    # The exemption MUST refuse and the normal error MUST fire.
    errors = collect_post_checkpoint_dirty_worktree_errors(
        gov,
        pipeline=_fake_pipeline(
            state="guards_failed",
            staged_tree_hash="deadbeefcafef00d",
        ),
        current_tree_hash="driftedhashfromnewedits",
    )

    assert len(errors) == 1
    assert "dirty worktree after a local checkpoint" in errors[0]


def test_post_checkpoint_dirty_rejects_when_current_tree_hash_is_empty() -> None:
    """A failed/empty current tree hash read must NOT exempt the dirty state.

    The fail-closed boundary: if the live ``index_tree_hash`` call returns
    an empty string (e.g. ``git write-tree`` failed), the bind-check has
    no proof that the worktree still matches the staged snapshot and the
    exemption must be refused.
    """
    gov = _fake_governance(
        Path("/tmp/repo"),
        worktree_dirty=True,
        worktree_clean=False,
        ahead_of_upstream_commits=1,
        dirty_path_count=11,
        untracked_path_count=0,
        recommended_action="commit_before_push",
    )

    errors = collect_post_checkpoint_dirty_worktree_errors(
        gov,
        pipeline=_fake_pipeline(state="guards_failed"),
        current_tree_hash="",
    )

    assert len(errors) == 1
    assert "dirty worktree after a local checkpoint" in errors[0]


def test_post_checkpoint_dirty_resolves_pipeline_via_governance_review_root(
    tmp_path: Path,
) -> None:
    """F19: non-default ``governance.artifact_roots.review_root`` resolves the artifact.

    Codex finding F19: the commit-pipeline artifact root must be resolved
    through ``ProjectGovernance.artifact_roots.review_root`` (with
    repo-pack override fallback) instead of the hardcoded VoiceTerm
    default ``dev/reports/review_channel/latest``. This test points
    governance at a non-default ``custom/review`` directory, writes the
    canonical ``commit_pipeline.json`` there, and proves the loader
    finds it through the typed resolver — without writing anything to
    the default `dev/reports/review_channel/latest` location.
    """
    custom_root_rel = "custom/review/state"
    pipeline_dir = tmp_path / custom_root_rel
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    (pipeline_dir / "commit_pipeline.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "contract_id": "RemoteCommitPipelineContract",
                "pipeline_id": "pipeline-non-default-root",
                "state": "guards_failed",
                "intent": {
                    "staged_tree_hash": "abc123nondefault",
                    "staged_path_count": 4,
                },
                "approval_state": "not_requested",
                "blocked_reason": "bundle_failed",
            }
        ),
        encoding="utf-8",
    )

    # Build a governance namespace with the non-default review_root.
    gov = SimpleNamespace(
        artifact_roots=SimpleNamespace(review_root=custom_root_rel),
        push_enforcement=SimpleNamespace(
            checkpoint_required=False,
            safe_to_continue_editing=True,
            checkpoint_reason="within_dirty_budget",
            worktree_clean=False,
            worktree_dirty=True,
            ahead_of_upstream_commits=1,
            dirty_path_count=4,
            untracked_path_count=0,
            recommended_action="commit_before_push",
        ),
    )

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks._index_tree_hash",
        return_value="abc123nondefault",
    ):
        errors = collect_post_checkpoint_dirty_worktree_errors(
            gov,
            repo_root=tmp_path,
        )

    assert errors == []


def test_post_checkpoint_dirty_governance_review_root_takes_priority(
    tmp_path: Path,
) -> None:
    """When `governance.artifact_roots.review_root` is set it MUST be preferred.

    Negative-side proof for F19: writing the artifact ONLY to the
    non-default location and never to `dev/reports/review_channel/latest`
    must still resolve the parked-pipeline exemption. If the typed
    resolver were ignored, this test would fall back to the hardcoded
    default and fail to find the pipeline file.
    """
    custom_root_rel = "alt/path/review"
    pipeline_dir = tmp_path / custom_root_rel
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    (pipeline_dir / "commit_pipeline.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "contract_id": "RemoteCommitPipelineContract",
                "pipeline_id": "pipeline-alt-path",
                "state": "staged",
                "intent": {
                    "staged_tree_hash": "alt123hash",
                    "staged_path_count": 2,
                },
            }
        ),
        encoding="utf-8",
    )
    # Confirm the default location is empty so any fallback would fail.
    default_dir = tmp_path / "dev" / "reports" / "review_channel" / "latest"
    assert not (default_dir / "commit_pipeline.json").exists()

    gov = SimpleNamespace(
        artifact_roots=SimpleNamespace(review_root=custom_root_rel),
        push_enforcement=SimpleNamespace(
            checkpoint_required=False,
            safe_to_continue_editing=True,
            checkpoint_reason="within_dirty_budget",
            worktree_clean=False,
            worktree_dirty=True,
            ahead_of_upstream_commits=1,
            dirty_path_count=2,
            untracked_path_count=0,
            recommended_action="commit_before_push",
        ),
    )

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks._index_tree_hash",
        return_value="alt123hash",
    ):
        errors = collect_post_checkpoint_dirty_worktree_errors(
            gov,
            repo_root=tmp_path,
        )

    assert errors == []


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_fails_when_reviewer_loop_blocks_implementation(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    state_dir = tmp_path / "dev" / "reports" / "review_channel" / "latest"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "review_state.json").write_text(
        json.dumps(
            {
                "bridge": {
                    "reviewer_mode": "active_dual_agent",
                    "claude_ack_current": False,
                    "review_accepted": False,
                },
                "attention": {
                    "status": "claude_ack_stale",
                },
                "current_session": {
                    "implementer_ack_state": "stale",
                },
            }
        ),
        encoding="utf-8",
    )

    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert report["reviewer_loop_blocked"] is True
    assert any("Reviewer loop blocks" in error for error in report["errors"])


def test_collect_reviewer_loop_block_errors_respects_commit_gate_bypass() -> None:
    governance = _fake_governance(Path("."))
    reviewer_gate = SimpleNamespace(
        implementation_blocked=True,
        review_gate_allows_push=False,
        implementation_block_reason="checkpoint_required",
        reviewer_mode="active_dual_agent",
        review_accepted=False,
    )

    with patch.dict(
        os.environ,
        {"DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY": "1"},
        clear=False,
    ):
        errors = collect_reviewer_loop_block_errors(
            Path("."),
            governance,
            reviewer_gate=reviewer_gate,
        )

    assert errors == []


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_allows_fresh_pending_implementer_state(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    state_dir = tmp_path / "dev" / "reports" / "review_channel" / "latest"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "review_state.json").write_text(
        json.dumps(
            {
                "bridge": {
                    "reviewer_mode": "active_dual_agent",
                    "claude_ack_current": False,
                    "review_accepted": False,
                },
                "attention": {
                    "status": "claude_ack_stale",
                },
                "current_session": {
                    "implementer_status": "- pending",
                    "implementer_ack": "- pending",
                    "implementer_ack_state": "pending",
                },
            }
        ),
        encoding="utf-8",
    )

    report = _build_report(repo_root=tmp_path)

    assert report["reviewer_loop_blocked"] is False
    assert not any("Reviewer loop blocks" in error for error in report["errors"])


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_bootstrap_intent_allows_reviewer_loop_only_block(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    state_dir = tmp_path / "dev" / "reports" / "review_channel" / "latest"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "review_state.json").write_text(
        json.dumps(
            {
                "bridge": {
                    "reviewer_mode": "active_dual_agent",
                    "claude_ack_current": False,
                    "review_accepted": False,
                },
                "attention": {
                    "status": "claude_ack_stale",
                },
                "current_session": {
                    "implementer_ack_state": "stale",
                },
            }
        ),
        encoding="utf-8",
    )

    report = _build_report(repo_root=tmp_path, intent="reviewer_bootstrap")

    assert report["ok"] is True
    assert report["reviewer_loop_blocked"] is True
    assert report["reviewer_loop_bootstrap_allowed"] is True
    assert not any("Reviewer loop blocks" in error for error in report["errors"])


def test_startup_authority_uses_preloaded_governance_and_reviewer_gate(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    governance = _fake_governance(tmp_path)
    reviewer_gate = SimpleNamespace(
        implementation_blocked=True,
        review_gate_allows_push=False,
        implementation_block_reason="reviewer_heartbeat_stale",
        reviewer_mode="active_dual_agent",
        review_accepted=False,
    )

    with (
        patch(
            "dev.scripts.checks.startup_authority_contract.command.import_repo_module",
        ) as import_repo_module,
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_import_index_atomicity_findings",
            return_value=([], []),
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_push_decision_contract_errors",
            return_value=[],
        ),
    ):
        report = _build_report(
            repo_root=tmp_path,
            intent="reviewer_bootstrap",
            governance=governance,
            reviewer_gate=reviewer_gate,
        )

    import_repo_module.assert_not_called()
    assert report["ok"] is True
    assert report["reviewer_loop_blocked"] is True
    assert report["reviewer_loop_bootstrap_allowed"] is True


def test_startup_authority_fails_when_push_contract_is_incoherent(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    fake_module = SimpleNamespace(
        scan_repo_governance=lambda _root: _fake_governance(tmp_path)
    )

    with (
        patch(
            "dev.scripts.checks.startup_authority_contract.command.import_repo_module",
            return_value=fake_module,
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_import_index_atomicity_findings",
            return_value=([], []),
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_push_decision_contract_errors",
            return_value=["Push decision contract must point to devctl push."],
        ),
    ):
        report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert any("Push decision contract" in error for error in report["errors"])


def test_startup_authority_guard_shim_executes_in_supported_script_mode(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    script_path = (
        Path(__file__).resolve().parents[5]
        / "dev"
        / "scripts"
        / "checks"
        / "check_startup_authority_contract.py"
    )

    result = subprocess.run(
        ["python3", str(script_path), "--format", "md"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "DEVCTL_REPO_ROOT": str(tmp_path)},
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "# check_startup_authority_contract" in result.stdout


def _git_commit(tmp_path: Path, message: str = "test") -> None:
    """Create a commit in the test repo so HEAD exists for ls-tree checks."""
    subprocess.run(
        ["git", "commit", "-m", message, "--allow-empty-message"],
        cwd=tmp_path, check=True, capture_output=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "test",
             "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "test",
             "GIT_COMMITTER_EMAIL": "t@t"},
    )


def test_import_index_atomicity_flags_repo_local_worktree_only_module(
    tmp_path: Path,
) -> None:
    """Importer is committed, target module only exists on disk -> error."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    importer = tmp_path / "dev" / "testpkg" / "importer.py"
    importer.parent.mkdir(parents=True)
    importer.write_text("from . import startup_signals\n", encoding="utf-8")
    # Commit only the importer — target module stays on disk only
    subprocess.run(
        ["git", "add", "dev/testpkg/importer.py"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    _git_commit(tmp_path, "add importer without target")
    # Now create the target on disk (not committed)
    (tmp_path / "dev" / "testpkg" / "startup_signals.py").write_text(
        "VALUE = 1\n", encoding="utf-8",
    )

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_import_staged.resolve_quality_scope_roots",
        return_value=(Path("dev"),),
    ):
        errors, warnings = collect_import_index_atomicity_findings(tmp_path)

    assert warnings == []
    assert any("startup_signals.py" in error for error in errors)


def test_import_index_atomicity_flags_committed_importer_with_broken_import(
    tmp_path: Path,
) -> None:
    """Committed importer with a missing target fails on the HEAD layer."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    importer = tmp_path / "dev" / "testpkg" / "importer.py"
    importer.parent.mkdir(parents=True)
    # Commit the importer WITH the import but WITHOUT the target
    importer.write_text("from . import startup_signals\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "dev/testpkg/importer.py"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    _git_commit(tmp_path, "commit importer referencing missing module")
    # Target exists on disk but not in HEAD
    (tmp_path / "dev" / "testpkg" / "startup_signals.py").write_text(
        "VALUE = 1\n", encoding="utf-8",
    )

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks.resolve_quality_scope_roots",
        return_value=(Path("dev"),),
    ):
        errors, warnings = collect_import_index_atomicity_findings(tmp_path)

    assert warnings == []
    assert any("startup_signals.py" in e and "committed" in e for e in errors)


def test_import_index_atomicity_allows_staged_atomic_split_with_existing_head(
    tmp_path: Path,
) -> None:
    """Existing committed importer modified + new target both staged -> no error.

    This is the false-positive Codex caught: if the committed layer scanned
    working-tree content against HEAD, a legitimate atomic stage would fail.
    With HEAD-content-vs-HEAD-paths, the committed layer only sees the old
    HEAD version (which doesn't have the new import), so no false positive.
    """
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    importer = tmp_path / "dev" / "testpkg" / "importer.py"
    importer.parent.mkdir(parents=True)
    # First commit: importer exists but does NOT import startup_signals
    importer.write_text("import os\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "dev/testpkg/importer.py"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    _git_commit(tmp_path, "initial importer without target import")
    # Now modify importer to add the import, create target, stage both
    importer.write_text("import os\nfrom . import startup_signals\n", encoding="utf-8")
    (tmp_path / "dev" / "testpkg" / "startup_signals.py").write_text(
        "VALUE = 1\n", encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "dev/testpkg/importer.py", "dev/testpkg/startup_signals.py"],
        cwd=tmp_path, check=True, capture_output=True,
    )

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks.resolve_quality_scope_roots",
        return_value=(Path("dev"),),
    ):
        errors, warnings = collect_import_index_atomicity_findings(tmp_path)

    # Staged layer: both in index -> passes
    # Committed layer: HEAD content has "import os" only, no startup_signals ref -> passes
    assert errors == []
    assert warnings == []


def test_staged_import_atomicity_ignores_unstaged_importer_dirt(
    tmp_path: Path,
) -> None:
    """Commit preflight validates the index snapshot, not dirty worktree imports."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    importer = tmp_path / "dev" / "testpkg" / "importer.py"
    importer.parent.mkdir(parents=True)
    importer.write_text("import os\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "dev/testpkg/importer.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    _git_commit(tmp_path, "initial importer without target import")

    importer.write_text("import os\nfrom . import startup_signals\n", encoding="utf-8")
    (tmp_path / "dev" / "testpkg" / "commit_snapshot.py").write_text(
        "VALUE = 1\n", encoding="utf-8"
    )
    subprocess.run(
        ["git", "add", "dev/testpkg/commit_snapshot.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks.resolve_quality_scope_roots",
        return_value=(Path("dev"),),
    ):
        errors, warnings = collect_staged_import_index_atomicity_findings(tmp_path)

    assert warnings == []
    assert errors == []


def test_import_index_atomicity_accepts_atomic_staged_split(
    tmp_path: Path,
) -> None:
    """Both importer and target staged atomically on a fresh repo (no HEAD yet).

    Before the first commit, ls-tree HEAD returns nothing, so the committed
    layer is skipped. The staged layer sees both files -> no error. This is
    the normal "stage everything then commit" workflow.
    """
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    importer = tmp_path / "dev" / "testpkg" / "importer.py"
    importer.parent.mkdir(parents=True)
    importer.write_text("from . import startup_signals\n", encoding="utf-8")
    (tmp_path / "dev" / "testpkg" / "startup_signals.py").write_text(
        "VALUE = 1\n", encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "dev/testpkg/importer.py", "dev/testpkg/startup_signals.py"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    # No commit yet — fresh repo, HEAD doesn't exist

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks.resolve_quality_scope_roots",
        return_value=(Path("dev"),),
    ):
        errors, warnings = collect_import_index_atomicity_findings(tmp_path)

    assert errors == []
    assert warnings == []


def test_import_index_atomicity_accepts_committed_module_split(tmp_path: Path) -> None:
    """Both importer and target are committed -> no error."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    importer = tmp_path / "dev" / "testpkg" / "importer.py"
    importer.parent.mkdir(parents=True)
    importer.write_text("from . import startup_signals\n", encoding="utf-8")
    (tmp_path / "dev" / "testpkg" / "startup_signals.py").write_text(
        "VALUE = 1\n", encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "dev/testpkg/importer.py", "dev/testpkg/startup_signals.py"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    _git_commit(tmp_path, "add both files atomically")

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks.resolve_quality_scope_roots",
        return_value=(Path("dev"),),
    ):
        errors, warnings = collect_import_index_atomicity_findings(tmp_path)

    assert errors == []
    assert warnings == []


def test_import_index_atomicity_limits_committed_scan_to_local_package_scope(
    tmp_path: Path,
) -> None:
    """Committed HEAD importers outside the local dirty package are ignored."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    for package in ("pkg_a", "pkg_b"):
        importer = tmp_path / "dev" / package / "importer.py"
        importer.parent.mkdir(parents=True, exist_ok=True)
        importer.write_text("from . import startup_signals\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "dev/pkg_a/importer.py", "dev/pkg_b/importer.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    _git_commit(tmp_path, "commit importers without targets")
    (tmp_path / "dev" / "pkg_b" / "startup_signals.py").write_text(
        "VALUE = 1\n", encoding="utf-8"
    )

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks.resolve_quality_scope_roots",
        return_value=(Path("dev"),),
    ):
        errors, warnings = collect_import_index_atomicity_findings(tmp_path)

    assert warnings == []
    assert any("dev/pkg_b/startup_signals.py" in error for error in errors)
    assert not any("dev/pkg_a/startup_signals.py" in error for error in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
