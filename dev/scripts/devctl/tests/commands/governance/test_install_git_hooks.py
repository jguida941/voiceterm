"""Tests for the devctl install-git-hooks command."""

from __future__ import annotations

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
    assert "Governed path: python3 dev/scripts/devctl.py push --execute" in content
