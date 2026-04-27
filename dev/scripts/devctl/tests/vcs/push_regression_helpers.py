"""Shared fixtures for governed push regression tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.vcs import push
from dev.scripts.devctl.governance.push_policy import (
    PushBypassPolicy,
    PushCheckpointPolicy,
    PushPolicy,
    PushPostPushPolicy,
    PushPreflightPolicy,
    PushPublicationPolicy,
)
from dev.scripts.devctl.review_channel.service_identity import (
    worktree_identity_for_repo,
)


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "remote": None,
        "quality_policy": None,
        "execute": False,
        "skip_preflight": False,
        "skip_post_push": False,
        "approved_target_identity": None,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_policy(**overrides) -> PushPolicy:
    values = {
        "policy_path": "dev/config/devctl_repo_policy.json",
        "repo_pack_id": "voiceterm",
        "warnings": (),
        "default_remote": "origin",
        "development_branch": "main",
        "release_branch": "main",
        "protected_branches": ("main",),
        "allowed_branch_prefixes": ("feature/", "fix/"),
        "preflight": PushPreflightPolicy(),
        "post_push": PushPostPushPolicy(),
        "bypass": PushBypassPolicy(),
        "checkpoint": PushCheckpointPolicy(),
        "publication": PushPublicationPolicy(),
    }
    values.update(overrides)
    return PushPolicy(**values)


def run_git(repo_root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def create_repo_with_ahead_commit(tmp_root: Path, branch: str) -> tuple[Path, Path]:
    repo_root = tmp_root / "repo"
    remote_root = tmp_root / "remote.git"
    run_git(tmp_root, "init", "--bare", str(remote_root))
    run_git(tmp_root, "init", str(repo_root))
    run_git(repo_root, "config", "user.email", "test@example.com")
    run_git(repo_root, "config", "user.name", "Test User")
    run_git(repo_root, "checkout", "-b", branch)
    (repo_root / "tracked.txt").write_text("initial\n", encoding="utf-8")
    run_git(repo_root, "add", "tracked.txt")
    run_git(repo_root, "commit", "-m", "initial")
    run_git(repo_root, "remote", "add", "origin", str(remote_root))
    run_git(repo_root, "push", "-u", "origin", branch)
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    run_git(repo_root, "commit", "-am", "update tracked file")
    return repo_root, remote_root


def authorization_for_current_repo(
    repo_root: Path, identity: str = ""
) -> SimpleNamespace:
    head = push.current_head_commit_sha(repo_root=repo_root)
    approved_target_identity = identity or f"tree-receipt-29990101T000000Z:{head}"
    return SimpleNamespace(
        authorized=True,
        reason="push_authorization_current",
        summary="Publication is authorized for the current HEAD.",
        push_authorization=SimpleNamespace(
            approved_target_identity=approved_target_identity,
            authorization_id="push-auth-29990101T000000Z",
            approval_mode="commit_pipeline_approval",
            authorized_head_sha=head,
            approved_at_utc="2999-01-01T00:00:00Z",
            expires_at_utc="2999-01-01T00:30:00Z",
            worktree_identity=worktree_identity_for_repo(repo_root),
        ),
    )
