"""devctl install-git-hooks command.

Installs the repo-owned git hooks that honor commit permission checks,
refresh ReviewSnapshot state, and keep publication on the governed
``devctl push`` path.
"""

from __future__ import annotations

from pathlib import Path

from ...common import add_standard_output_arguments
from ...config import REPO_ROOT
from .common import emit_governance_command_output
from .install_git_hooks_support import (
    InstallGitHooksContext,
    emit_install_git_hooks_command as _emit,
    hook_targets as _hook_targets,
    normalize_managed_hook_content as _normalize_managed_hook_content,
    render_status_markdown as _render_status_markdown,
    run_install as _run_install,
    run_uninstall as _run_uninstall,
    safe_relative as _safe_relative,
)

_MANAGED_MARKER = (
    "devctl-install-git-hooks: managed hook for review-snapshot refresh"
)
_HOOK_TEMPLATE_RELPATHS = {
    "pre-commit": "dev/config/git_hooks/pre-commit-review-snapshot.sh",
    "post-commit": "dev/config/git_hooks/post-commit-review-snapshot.sh",
    "pre-push": "dev/config/git_hooks/pre-push-governed-push.sh",
}


def add_parser(subparsers) -> None:
    cmd = subparsers.add_parser(
        "install-git-hooks",
        help=(
            "Install repo-owned git hooks so raw `git commit` first checks "
            "`commit_permission`, auto-refreshes the ReviewSnapshot file, "
            "receipt commits stay automated, and "
            "raw `git push` is forced back through `devctl push`."
        ),
    )
    cmd.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Report hook install status without writing anything.",
    )
    cmd.add_argument(
        "--uninstall",
        action="store_true",
        default=False,
        help="Remove the managed git hooks installed by this command.",
    )
    cmd.add_argument(
        "--force",
        action="store_true",
        default=False,
        help=(
            "Overwrite existing non-managed git hooks. Use only when you have "
            "verified the existing hooks are safe to replace."
        ),
    )
    add_standard_output_arguments(cmd, format_choices=("md", "json"))


def run(args) -> int:
    repo_root = REPO_ROOT
    hooks_dir = resolve_hooks_dir(repo_root)

    check_mode = bool(getattr(args, "check", False))
    uninstall_mode = bool(getattr(args, "uninstall", False))
    force = bool(getattr(args, "force", False))

    hook_targets = _hook_targets(
        repo_root=repo_root,
        hooks_dir=hooks_dir,
        hook_template_relpaths=_HOOK_TEMPLATE_RELPATHS,
    )
    statuses = {
        hook_name: current_install_status(
            paths["target"],
            template_path=paths["template"],
        )
        for hook_name, paths in hook_targets.items()
    }
    target_display = {
        hook_name: _safe_relative(paths["target"], repo_root)
        for hook_name, paths in hook_targets.items()
    }
    context = InstallGitHooksContext(
        statuses=statuses,
        hook_targets=hook_targets,
        target_display=target_display,
        hooks_dir=hooks_dir,
        repo_root=repo_root,
    )

    if check_mode:
        ok = all(status == "managed" for status in statuses.values())
        return _emit(
            args,
            ok=ok,
            summary={
                "hook_status": _overall_hook_status(statuses),
                "hook_statuses": statuses,
                "target_paths": target_display,
            },
            human_output=_render_status_markdown(statuses, target_display),
        )

    if uninstall_mode:
        return _run_uninstall(
            args,
            context=context,
            force=force,
        )

    return _run_install(
        args,
        context=context,
        force=force,
    )


def resolve_hooks_dir(repo_root: Path) -> Path:
    """Return the git hooks dir for the current worktree (main or linked)."""
    git_dir_marker = repo_root / ".git"
    if git_dir_marker.is_dir():
        return git_dir_marker / "hooks"
    if git_dir_marker.is_file():
        try:
            content = git_dir_marker.read_text(encoding="utf-8").strip()
        except OSError:
            content = ""
        if content.startswith("gitdir:"):
            gitdir = Path(content.split(":", 1)[1].strip())
            if not gitdir.is_absolute():
                gitdir = (repo_root / gitdir).resolve()
            return gitdir / "hooks"
    return repo_root / ".git" / "hooks"


def current_install_status(
    target_path: Path,
    *,
    template_path: Path | None = None,
) -> str:
    """Return the current managed/non-managed/drifted install state."""
    if not target_path.exists():
        return "absent"
    try:
        content = target_path.read_text(encoding="utf-8")
    except OSError:
        return "non_managed"
    if _MANAGED_MARKER not in content:
        return "non_managed"
    if template_path is None:
        return "managed"
    try:
        template_content = template_path.read_text(encoding="utf-8")
    except OSError:
        return "managed"
    if _normalize_managed_hook_content(content) != _normalize_managed_hook_content(
        template_content
    ):
        return "managed_drifted"
    return "managed"


def _overall_hook_status(statuses: dict[str, str]) -> str:
    if statuses and all(status == "managed" for status in statuses.values()):
        return "managed"
    if any(status == "managed_drifted" for status in statuses.values()):
        return "drifted"
    if any(status == "non_managed" for status in statuses.values()):
        return "non_managed"
    if any(status == "absent" for status in statuses.values()):
        return "absent"
    return "non_managed"


__all__ = ["add_parser", "current_install_status", "resolve_hooks_dir", "run"]
