"""Tests for the devctl install-git-hooks command."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

from devctl.commands.governance.install_git_hooks import (
    current_install_status,
    resolve_hooks_dir,
    run,
)


_MANAGED_HOOK_BODY = """\
#!/usr/bin/env bash
# devctl-install-git-hooks: managed hook for review-snapshot refresh
#
# Auto-refreshes the configured ReviewSnapshot file before every git commit.
set -eu
exit 0
"""


def _make_main_worktree(tmp_path: Path) -> Path:
    """Build a minimal main-worktree layout: .git dir + dev/config/git_hooks."""
    repo_root = tmp_path / "repo"
    (repo_root / ".git" / "hooks").mkdir(parents=True)
    (repo_root / "dev" / "config" / "git_hooks").mkdir(parents=True)
    _write_hook_templates(repo_root)
    return repo_root


def _make_linked_worktree(tmp_path: Path) -> tuple[Path, Path]:
    """Build a minimal linked-worktree layout: .git is a file pointing at a gitdir."""
    main_repo = tmp_path / "main"
    main_repo.mkdir()
    gitdir = main_repo / ".git" / "worktrees" / "linked"
    (gitdir / "hooks").mkdir(parents=True)

    linked_repo = tmp_path / "linked"
    linked_repo.mkdir()
    (linked_repo / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    (linked_repo / "dev" / "config" / "git_hooks").mkdir(parents=True)
    _write_hook_templates(linked_repo)
    return linked_repo, gitdir / "hooks"


def _write_hook_templates(repo_root: Path) -> None:
    hook_root = repo_root / "dev" / "config" / "git_hooks"
    for filename in (
        "pre-commit-review-snapshot.sh",
        "post-commit-review-snapshot.sh",
        "pre-push-governed-push.sh",
    ):
        (hook_root / filename).write_text(_MANAGED_HOOK_BODY, encoding="utf-8")


# ---------------------------------------------------------------------------
# Hooks dir resolution — the portability half
# ---------------------------------------------------------------------------


def test_resolve_hooks_dir_returns_dot_git_hooks_for_main_worktree(tmp_path: Path) -> None:
    repo_root = _make_main_worktree(tmp_path)
    resolved = resolve_hooks_dir(repo_root)
    assert resolved == repo_root / ".git" / "hooks"


def test_resolve_hooks_dir_follows_gitdir_pointer_for_linked_worktree(
    tmp_path: Path,
) -> None:
    linked_repo, expected_hooks_dir = _make_linked_worktree(tmp_path)
    resolved = resolve_hooks_dir(linked_repo)
    assert resolved == expected_hooks_dir


def test_resolve_hooks_dir_falls_back_when_dot_git_absent(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    resolved = resolve_hooks_dir(repo_root)
    assert resolved == repo_root / ".git" / "hooks"


# ---------------------------------------------------------------------------
# Install status detection
# ---------------------------------------------------------------------------


def test_current_install_status_reports_absent_when_hook_missing(tmp_path: Path) -> None:
    assert current_install_status(tmp_path / "pre-commit") == "absent"


def test_current_install_status_reports_managed_when_marker_present(
    tmp_path: Path,
) -> None:
    hook = tmp_path / "pre-commit"
    hook.write_text(_MANAGED_HOOK_BODY, encoding="utf-8")
    assert current_install_status(hook) == "managed"


def test_current_install_status_reports_managed_drifted_when_template_differs(
    tmp_path: Path,
) -> None:
    hook = tmp_path / "pre-commit"
    template = tmp_path / "template.sh"
    template.write_text(_MANAGED_HOOK_BODY, encoding="utf-8")
    hook.write_text(
        _MANAGED_HOOK_BODY + "\n# drifted managed copy\n",
        encoding="utf-8",
    )
    assert (
        current_install_status(hook, template_path=template) == "managed_drifted"
    )


def test_current_install_status_reports_non_managed_when_marker_absent(
    tmp_path: Path,
) -> None:
    hook = tmp_path / "pre-commit"
    hook.write_text("#!/usr/bin/env bash\n# developer's custom hook\nexit 0\n", encoding="utf-8")
    assert current_install_status(hook) == "non_managed"


# ---------------------------------------------------------------------------
# End-to-end run() behaviour
# ---------------------------------------------------------------------------


def test_run_install_copies_template_into_hooks_dir(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = _make_main_worktree(tmp_path)
    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.REPO_ROOT", repo_root
    )
    args = Namespace(
        check=False, uninstall=False, force=False, format="json", output=None,
        pipe_command=None, pipe_args=None,
    )
    exit_code = run(args)
    assert exit_code == 0
    for hook_name in ("pre-commit", "post-commit", "pre-push"):
        installed = repo_root / ".git" / "hooks" / hook_name
        assert installed.is_file()
        assert "devctl-install-git-hooks: managed hook" in installed.read_text(
            encoding="utf-8"
        )
        # Hook must be executable after install.
        assert installed.stat().st_mode & 0o111 != 0


def test_current_install_status_treats_rendered_interpreter_as_managed(
    tmp_path: Path,
) -> None:
    template = tmp_path / "template.sh"
    installed = tmp_path / "pre-commit"
    template.write_text(
        _MANAGED_HOOK_BODY + 'DEVCTL_PYTHON="@DEVCTL_PYTHON@"\n',
        encoding="utf-8",
    )
    installed.write_text(
        _MANAGED_HOOK_BODY + 'DEVCTL_PYTHON="/opt/homebrew/bin/python3.11"\n',
        encoding="utf-8",
    )

    assert current_install_status(installed, template_path=template) == "managed"


def test_run_install_renders_active_python_into_managed_hooks(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = _make_main_worktree(tmp_path)
    template = repo_root / "dev" / "config" / "git_hooks" / "pre-commit-review-snapshot.sh"
    template.write_text(
        _MANAGED_HOOK_BODY + 'DEVCTL_PYTHON="@DEVCTL_PYTHON@"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.REPO_ROOT", repo_root
    )
    args = Namespace(
        check=False, uninstall=False, force=False, format="json", output=None,
        pipe_command=None, pipe_args=None,
    )

    exit_code = run(args)

    assert exit_code == 0
    installed = repo_root / ".git" / "hooks" / "pre-commit"
    assert f'DEVCTL_PYTHON="{sys.executable}"' in installed.read_text(encoding="utf-8")


def test_run_install_refuses_to_overwrite_non_managed_hook_without_force(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = _make_main_worktree(tmp_path)
    hook = repo_root / ".git" / "hooks" / "pre-commit"
    hook.write_text(
        "#!/usr/bin/env bash\n# developer's custom hook\nexit 0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.REPO_ROOT", repo_root
    )
    args = Namespace(
        check=False, uninstall=False, force=False, format="json", output=None,
        pipe_command=None, pipe_args=None,
    )
    exit_code = run(args)
    assert exit_code != 0
    # Custom hook preserved.
    assert "developer's custom hook" in hook.read_text(encoding="utf-8")


def test_run_install_force_replaces_non_managed_hook(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = _make_main_worktree(tmp_path)
    hook = repo_root / ".git" / "hooks" / "pre-commit"
    hook.write_text(
        "#!/usr/bin/env bash\n# developer's custom hook\nexit 0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.REPO_ROOT", repo_root
    )
    args = Namespace(
        check=False, uninstall=False, force=True, format="json", output=None,
        pipe_command=None, pipe_args=None,
    )
    exit_code = run(args)
    assert exit_code == 0
    assert "devctl-install-git-hooks: managed hook" in hook.read_text(encoding="utf-8")


def test_run_install_refreshes_drifted_managed_hook_without_force(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = _make_main_worktree(tmp_path)
    hook = repo_root / ".git" / "hooks" / "pre-commit"
    hook.write_text(
        _MANAGED_HOOK_BODY + "\n# drifted managed copy\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.REPO_ROOT", repo_root
    )
    args = Namespace(
        check=False, uninstall=False, force=False, format="json", output=None,
        pipe_command=None, pipe_args=None,
    )
    exit_code = run(args)
    assert exit_code == 0
    assert hook.read_text(encoding="utf-8") == _MANAGED_HOOK_BODY


def test_run_uninstall_removes_managed_hook(tmp_path: Path, monkeypatch) -> None:
    repo_root = _make_main_worktree(tmp_path)
    hook = repo_root / ".git" / "hooks" / "pre-commit"
    hook.write_text(_MANAGED_HOOK_BODY, encoding="utf-8")
    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.REPO_ROOT", repo_root
    )
    args = Namespace(
        check=False, uninstall=True, force=False, format="json", output=None,
        pipe_command=None, pipe_args=None,
    )
    exit_code = run(args)
    assert exit_code == 0
    assert not hook.exists()


def test_run_uninstall_refuses_to_remove_non_managed_hook_without_force(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = _make_main_worktree(tmp_path)
    hook = repo_root / ".git" / "hooks" / "pre-commit"
    hook.write_text(
        "#!/usr/bin/env bash\n# developer's custom hook\nexit 0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.REPO_ROOT", repo_root
    )
    args = Namespace(
        check=False, uninstall=True, force=False, format="json", output=None,
        pipe_command=None, pipe_args=None,
    )
    exit_code = run(args)
    assert exit_code != 0
    assert "developer's custom hook" in hook.read_text(encoding="utf-8")


def test_run_check_mode_reports_status_without_writing(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = _make_main_worktree(tmp_path)
    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.REPO_ROOT", repo_root
    )
    args = Namespace(
        check=True, uninstall=False, force=False, format="json", output=None,
        pipe_command=None, pipe_args=None,
    )
    exit_code = run(args)
    # absent → exit non-zero in check mode
    assert exit_code != 0
    # And nothing was written.
    assert not (repo_root / ".git" / "hooks" / "pre-commit").exists()


def test_run_check_mode_flags_drifted_managed_hook(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = _make_main_worktree(tmp_path)
    hook = repo_root / ".git" / "hooks" / "pre-commit"
    hook.write_text(
        _MANAGED_HOOK_BODY + "\n# drifted managed copy\n",
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    def _capture_emit(
        args,
        *,
        command: str,
        json_payload,
        markdown_output: str,
        ok: bool = True,
        summary=None,
    ) -> int:
        del args, command, markdown_output, summary
        captured.update(json_payload)
        return 0 if ok else 1

    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.REPO_ROOT", repo_root
    )
    monkeypatch.setattr(
        "devctl.commands.governance.install_git_hooks.emit_governance_command_output",
        _capture_emit,
    )
    args = Namespace(
        check=True, uninstall=False, force=False, format="json", output=None,
        pipe_command=None, pipe_args=None,
    )
    exit_code = run(args)
    assert exit_code != 0
    assert captured["hook_status"] == "drifted"
    hook_statuses = captured["hook_statuses"]
    assert isinstance(hook_statuses, dict)
    assert hook_statuses["pre-commit"] == "managed_drifted"


def test_repo_pre_push_template_uses_typed_runtime_guidance() -> None:
    template_path = (
        Path(__file__).resolve().parents[6]
        / "dev"
        / "config"
        / "git_hooks"
        / "pre-push-governed-push.sh"
    )
    content = template_path.read_text(encoding="utf-8")
    assert "startup-context --format summary" in content
    assert "Next typed step:" in content
    assert 'Governed path: $(basename "$DEVCTL_PYTHON") dev/scripts/devctl.py push --execute' in content


def test_repo_pre_commit_template_checks_commit_permission_before_refresh() -> None:
    template_path = (
        Path(__file__).resolve().parents[6]
        / "dev"
        / "config"
        / "git_hooks"
        / "pre-commit-review-snapshot.sh"
    )
    content = template_path.read_text(encoding="utf-8")
    assert "commit_permission_hook" in content
    assert "raw git commits must not bypass" in content
    assert "DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT" in content


def test_repo_pre_commit_template_does_not_write_projection_artifacts() -> None:
    template_path = (
        Path(__file__).resolve().parents[6]
        / "dev"
        / "config"
        / "git_hooks"
        / "pre-commit-review-snapshot.sh"
    )
    content = template_path.read_text(encoding="utf-8")
    assert "commit_permission_hook" in content
    assert "Projection refreshes deliberately" in content
    assert "review-snapshot --write" not in content
    assert "review-channel --action status" not in content
    assert "git add" not in content


def test_repo_post_commit_template_times_out_receipt_refresh() -> None:
    template_path = (
        Path(__file__).resolve().parents[6]
        / "dev"
        / "config"
        / "git_hooks"
        / "post-commit-review-snapshot.sh"
    )
    content = template_path.read_text(encoding="utf-8")
    assert "DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS" in content
    assert "run_review_snapshot_receipt" in content
    assert "return 124" in content
    assert "continuing commit" in content
