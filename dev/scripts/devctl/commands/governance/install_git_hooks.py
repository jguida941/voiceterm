"""devctl install-git-hooks command.

Installs the repo-owned git hooks that make raw ``git commit`` auto-refresh
the ReviewSnapshot projection, create a trailing snapshot-only receipt
commit, and block raw ``git push`` so publication stays on the governed
``devctl push`` path.

Portability:

- Hook templates live under ``dev/config/git_hooks/`` and are shipped with
  the governance platform. Adopter repos get them for free.
- Target hooks directory is resolved through git plumbing so the command
  works in main worktrees (where ``.git`` is a directory) AND in linked
  worktrees (where ``.git`` is a file pointing at ``.git/worktrees/<name>/``).
- The snapshot path the hook refreshes is resolved at hook-run time
  through ``ProjectGovernance.artifact_roots.review_snapshot_path``, so
  adopter repos override it via ``devctl_repo_policy.json`` without
  touching the hook template.

Safety:

- Idempotent: reinstalling overwrites the managed hook.
- Non-managed hook detection: refuses to overwrite existing hooks unless
  ``--force`` is passed, so developers with their own hooks don't silently
  lose them.
- Uninstall: ``--uninstall`` removes only managed hooks, never touches
  non-managed ones unless ``--force`` is passed.
- Check: ``--check`` reports install status without writing anything.
"""

from __future__ import annotations

import shutil
import stat
from pathlib import Path

from ...common import add_standard_output_arguments
from ...config import REPO_ROOT
from .common import emit_governance_command_output

_MANAGED_MARKER = (
    "devctl-install-git-hooks: managed hook for review-snapshot refresh"
)
_HOOK_TEMPLATE_RELPATHS = {
    "pre-commit": "dev/config/git_hooks/pre-commit-review-snapshot.sh",
    "post-commit": "dev/config/git_hooks/post-commit-review-snapshot.sh",
    "pre-push": "dev/config/git_hooks/pre-push-governed-push.sh",
}


def add_parser(subparsers) -> None:
    """Register the ``install-git-hooks`` CLI parser."""
    cmd = subparsers.add_parser(
        "install-git-hooks",
        help=(
            "Install repo-owned git hooks so raw `git commit` auto-refreshes "
            "the ReviewSnapshot file, receipt commits stay automated, and "
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
    """Install, verify, or remove the managed ReviewSnapshot hooks."""
    repo_root = REPO_ROOT
    hooks_dir = resolve_hooks_dir(repo_root)

    check_mode = bool(getattr(args, "check", False))
    uninstall_mode = bool(getattr(args, "uninstall", False))
    force = bool(getattr(args, "force", False))

    hook_targets = _hook_targets(repo_root=repo_root, hooks_dir=hooks_dir)
    statuses = {
        hook_name: current_install_status(paths["target"])
        for hook_name, paths in hook_targets.items()
    }
    target_display = {
        hook_name: _safe_relative(paths["target"], repo_root)
        for hook_name, paths in hook_targets.items()
    }

    if check_mode:
        ok = all(status == "managed" for status in statuses.values())
        return _emit(
            args,
            ok=ok,
            summary={
                "hook_status": "managed" if ok else "incomplete",
                "hook_statuses": statuses,
                "target_paths": target_display,
            },
            human_output=_render_status_markdown(statuses, target_display),
        )

    if uninstall_mode:
        return _run_uninstall(
            args,
            statuses=statuses,
            hook_targets=hook_targets,
            target_display=target_display,
            force=force,
        )

    return _run_install(
        args,
        statuses=statuses,
        hook_targets=hook_targets,
        target_display=target_display,
        hooks_dir=hooks_dir,
        force=force,
        repo_root=repo_root,
    )


def resolve_hooks_dir(repo_root: Path) -> Path:
    """Return the git hooks dir for the current worktree (main or linked).

    Handles both shapes:
    - Main worktree: ``.git`` is a directory, hooks live at ``.git/hooks``.
    - Linked worktree: ``.git`` is a file whose contents are
      ``gitdir: <path>``, and hooks live at that gitdir path.
    """
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


def current_install_status(target_path: Path) -> str:
    """Return ``"managed"``, ``"non_managed"``, or ``"absent"``."""
    if not target_path.exists():
        return "absent"
    try:
        content = target_path.read_text(encoding="utf-8")
    except OSError:
        return "non_managed"
    if _MANAGED_MARKER in content:
        return "managed"
    return "non_managed"


def _run_install(
    args,
    *,
    statuses: dict[str, str],
    hook_targets: dict[str, dict[str, Path]],
    target_display: dict[str, str],
    hooks_dir: Path,
    force: bool,
    repo_root: Path,
) -> int:
    missing_templates = {
        hook_name: _safe_relative(paths["template"], repo_root)
        for hook_name, paths in hook_targets.items()
        if not paths["template"].is_file()
    }
    if missing_templates:
        return _emit(
            args,
            ok=False,
            summary={
                "hook_status": "template_missing",
                "hook_statuses": statuses,
                "error": "template_missing",
                "template_paths": missing_templates,
            },
            human_output=(
                f"# install-git-hooks\n\n"
                f"- status: error\n"
                f"- error: hook templates missing: `{missing_templates}`\n"
                "- fix: restore the template from the governance platform "
                "shipping bundle and rerun `devctl install-git-hooks`.\n"
            ),
        )

    non_managed = {
        hook_name: target_display[hook_name]
        for hook_name, status in statuses.items()
        if status == "non_managed"
    }
    if non_managed and not force:
        return _emit(
            args,
            ok=False,
            summary={
                "hook_status": "non_managed",
                "hook_statuses": statuses,
                "target_paths": non_managed,
            },
            human_output=(
                f"# install-git-hooks\n\n"
                f"- status: refused\n"
                f"- targets: `{non_managed}`\n"
                f"- reason: existing non-managed git hooks were "
                f"found. Inspect the file, then rerun with `--force` to "
                "replace them.\n"
            ),
        )

    hooks_dir.mkdir(parents=True, exist_ok=True)
    for paths in hook_targets.values():
        target_path = paths["target"]
        shutil.copy2(paths["template"], target_path)
        target_path.chmod(
            target_path.stat().st_mode
            | stat.S_IXUSR
            | stat.S_IXGRP
            | stat.S_IXOTH
        )
    return _emit(
        args,
        ok=True,
        summary={
            "hook_status": "managed",
            "hook_statuses": {hook_name: "managed" for hook_name in hook_targets},
            "target_paths": target_display,
        },
        human_output=(
            f"# install-git-hooks\n\n"
            f"- status: installed\n"
            f"- targets: `{target_display}`\n\n"
            "Every `git commit` in this clone will now auto-refresh a "
            "ReviewSnapshot into the commit and then create a trailing "
            "snapshot-only receipt commit through "
            "`devctl review-snapshot --write --receipt-commit`, regardless "
            "of whether the commit is made via the CLI, an IDE plugin, an "
            "editor git tool, or an AI assistant. The CI freshness guard "
            "(`check_review_snapshot_freshness.py`) remains the CI-side "
            "backstop. Raw `git push` is now blocked by the managed "
            "`pre-push` hook unless the push originated from the governed "
            "`python3 dev/scripts/devctl.py push --execute` path.\n\n"
            "To opt out temporarily: set `DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH=1` "
            "in the environment for a single commit.\n"
        ),
    )


def _run_uninstall(
    args,
    *,
    statuses: dict[str, str],
    hook_targets: dict[str, dict[str, Path]],
    target_display: dict[str, str],
    force: bool,
) -> int:
    removable = {
        hook_name: paths
        for hook_name, paths in hook_targets.items()
        if statuses[hook_name] == "managed"
        or (statuses[hook_name] == "non_managed" and force)
    }
    non_managed = {
        hook_name: target_display[hook_name]
        for hook_name, status in statuses.items()
        if status == "non_managed"
    }
    if non_managed and not force:
        return _emit(
            args,
            ok=False,
            summary={
                "hook_status": "non_managed",
                "hook_statuses": statuses,
                "target_paths": non_managed,
            },
            human_output=(
                f"# install-git-hooks\n\n"
                f"- status: refused\n"
                f"- targets: `{non_managed}`\n"
                f"- reason: refusing to remove non-managed git hooks. "
                f"Rerun with `--force` if the removal is intentional.\n"
            ),
        )
    if not removable:
        return _emit(
            args,
            ok=True,
            summary={"hook_status": "absent", "hook_statuses": statuses},
            human_output=(
                "# install-git-hooks\n\n"
                "- status: absent\n"
                "- note: no managed hooks to remove.\n"
            ),
        )
    removed: dict[str, str] = {}
    for hook_name, paths in removable.items():
        try:
            paths["target"].unlink()
            removed[hook_name] = target_display[hook_name]
        except OSError as exc:
            return _emit(
                args,
                ok=False,
                summary={
                    "hook_status": statuses[hook_name],
                    "hook_statuses": statuses,
                    "error": f"unlink_failed: {exc}",
                },
                human_output=(
                    f"# install-git-hooks\n\n"
                    f"- status: error\n"
                    f"- error: failed to remove `{target_display[hook_name]}`: {exc}\n"
                ),
            )
    return _emit(
        args,
        ok=True,
        summary={"hook_status": "uninstalled", "removed": removed},
        human_output=(
            f"# install-git-hooks\n\n"
            f"- status: uninstalled\n"
            f"- note: removed managed hooks: `{removed}`.\n"
        ),
    )


def _render_status_markdown(statuses: dict[str, str], target_display: dict[str, str]) -> str:
    rows = "\n".join(
        f"- {hook_name}: {statuses[hook_name]} at `{target_display[hook_name]}`"
        for hook_name in sorted(statuses)
    )
    return (
        "# install-git-hooks\n\n"
        f"{rows}\n"
    )


def _hook_targets(*, repo_root: Path, hooks_dir: Path) -> dict[str, dict[str, Path]]:
    return {
        hook_name: {
            "template": repo_root / template_relpath,
            "target": hooks_dir / hook_name,
        }
        for hook_name, template_relpath in _HOOK_TEMPLATE_RELPATHS.items()
    }


def _safe_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _emit(args, *, ok: bool, summary: dict, human_output: str) -> int:
    payload = {"ok": ok, **summary}
    return emit_governance_command_output(
        args,
        command="install-git-hooks",
        json_payload=payload,
        markdown_output=human_output,
        ok=ok,
        summary=summary,
    )


__all__ = [
    "add_parser",
    "current_install_status",
    "resolve_hooks_dir",
    "run",
]
