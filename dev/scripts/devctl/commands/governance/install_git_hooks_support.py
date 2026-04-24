"""Support helpers for the `install-git-hooks` command."""

from __future__ import annotations

import re
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

from .common import emit_governance_command_output as _default_emit_governance_command_output

_MANAGED_HOOK_PYTHON_PLACEHOLDER = "@DEVCTL_PYTHON@"
_MANAGED_HOOK_PYTHON_ASSIGNMENT_RE = re.compile(
    r'^DEVCTL_PYTHON="[^"\n]*"$',
    re.MULTILINE,
)


@dataclass(frozen=True)
class InstallGitHooksContext:
    """Shared install/uninstall inputs for managed hook operations."""

    statuses: dict[str, str]
    hook_targets: dict[str, dict[str, Path]]
    target_display: dict[str, str]
    hooks_dir: Path | None = None
    repo_root: Path | None = None


def render_managed_hook_template(template_path: Path) -> str:
    """Render one managed hook template with the active Python executable."""
    content = template_path.read_text(encoding="utf-8")
    return content.replace(
        _MANAGED_HOOK_PYTHON_PLACEHOLDER,
        sys.executable or "python3",
    )


def normalize_managed_hook_content(content: str) -> str:
    """Collapse interpreter-specific hook lines back to the template placeholder."""
    return _MANAGED_HOOK_PYTHON_ASSIGNMENT_RE.sub(
        f'DEVCTL_PYTHON="{_MANAGED_HOOK_PYTHON_PLACEHOLDER}"',
        content,
        count=1,
    )


def run_install(
    args,
    *,
    context: InstallGitHooksContext,
    force: bool,
) -> int:
    repo_root = context.repo_root
    hooks_dir = context.hooks_dir
    if repo_root is None or hooks_dir is None:
        raise ValueError("install-git-hooks install context requires repo_root and hooks_dir")
    missing_templates = {
        hook_name: safe_relative(paths["template"], repo_root)
        for hook_name, paths in context.hook_targets.items()
        if not paths["template"].is_file()
    }
    if missing_templates:
        return emit_install_git_hooks_command(
            args,
            ok=False,
            summary={
                "hook_status": "template_missing",
                "hook_statuses": context.statuses,
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
        hook_name: context.target_display[hook_name]
        for hook_name, status in context.statuses.items()
        if status == "non_managed"
    }
    if non_managed and not force:
        return emit_install_git_hooks_command(
            args,
            ok=False,
            summary={
                "hook_status": "non_managed",
                "hook_statuses": context.statuses,
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
    for paths in context.hook_targets.values():
        target_path = paths["target"]
        target_path.write_text(
            render_managed_hook_template(paths["template"]),
            encoding="utf-8",
        )
        shutil.copystat(paths["template"], target_path)
        target_path.chmod(
            target_path.stat().st_mode
            | stat.S_IXUSR
            | stat.S_IXGRP
            | stat.S_IXOTH
        )
    return emit_install_git_hooks_command(
        args,
        ok=True,
        summary={
            "hook_status": "managed",
            "hook_statuses": {
                hook_name: "managed" for hook_name in context.hook_targets
            },
            "target_paths": context.target_display,
        },
        human_output=(
            f"# install-git-hooks\n\n"
            f"- status: installed\n"
            f"- targets: `{context.target_display}`\n\n"
            "Every `git commit` in this clone will now evaluate the typed "
            "`commit_permission` boundary before the commit is recorded. "
            "Allowed commits auto-refresh a ReviewSnapshot into the commit "
            "and then create a trailing snapshot-only receipt commit through "
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


def run_uninstall(
    args,
    *,
    context: InstallGitHooksContext,
    force: bool,
) -> int:
    removable = {
        hook_name: paths
        for hook_name, paths in context.hook_targets.items()
        if context.statuses[hook_name] in {"managed", "managed_drifted"}
        or (context.statuses[hook_name] == "non_managed" and force)
    }
    non_managed = {
        hook_name: context.target_display[hook_name]
        for hook_name, status in context.statuses.items()
        if status == "non_managed"
    }
    if non_managed and not force:
        return emit_install_git_hooks_command(
            args,
            ok=False,
            summary={
                "hook_status": "non_managed",
                "hook_statuses": context.statuses,
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
        return emit_install_git_hooks_command(
            args,
            ok=True,
            summary={"hook_status": "absent", "hook_statuses": context.statuses},
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
            removed[hook_name] = context.target_display[hook_name]
        except OSError as exc:
            return emit_install_git_hooks_command(
                args,
                ok=False,
                summary={
                    "hook_status": context.statuses[hook_name],
                    "hook_statuses": context.statuses,
                    "error": f"unlink_failed: {exc}",
                },
                human_output=(
                    f"# install-git-hooks\n\n"
                    f"- status: error\n"
                    f"- error: failed to remove `{context.target_display[hook_name]}`: {exc}\n"
                ),
            )
    return emit_install_git_hooks_command(
        args,
        ok=True,
        summary={"hook_status": "uninstalled", "removed": removed},
        human_output=(
            f"# install-git-hooks\n\n"
            f"- status: uninstalled\n"
            f"- note: removed managed hooks: `{removed}`.\n"
        ),
    )


def render_status_markdown(statuses: dict[str, str], target_display: dict[str, str]) -> str:
    rows = "\n".join(
        f"- {hook_name}: {statuses[hook_name]} at `{target_display[hook_name]}`"
        for hook_name in sorted(statuses)
    )
    notes: list[str] = []
    if any(status == "managed_drifted" for status in statuses.values()):
        notes.append(
            "- note: rerun `python3 dev/scripts/devctl.py install-git-hooks` "
            "to refresh drifted managed hooks."
        )
    notes_block = ""
    if notes:
        notes_block = "".join(f"{note}\n" for note in notes)
    return (
        "# install-git-hooks\n\n"
        f"{rows}\n"
        f"{notes_block}"
    )


def hook_targets(
    *,
    repo_root: Path,
    hooks_dir: Path,
    hook_template_relpaths: dict[str, str],
) -> dict[str, dict[str, Path]]:
    return {
        hook_name: {
            "template": repo_root / template_relpath,
            "target": hooks_dir / hook_name,
        }
        for hook_name, template_relpath in hook_template_relpaths.items()
    }


def safe_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def emit_install_git_hooks_command(
    args,
    *,
    ok: bool,
    summary: dict,
    human_output: str,
) -> int:
    payload = {"ok": ok, **summary}
    try:
        from . import install_git_hooks as install_git_hooks_command

        emitter = getattr(
            install_git_hooks_command,
            "emit_governance_command_output",
            _default_emit_governance_command_output,
        )
    except ImportError:
        emitter = _default_emit_governance_command_output
    return emitter(
        args,
        command="install-git-hooks",
        json_payload=payload,
        markdown_output=human_output,
        ok=ok,
        summary=summary,
    )


__all__ = [
    "InstallGitHooksContext",
    "emit_install_git_hooks_command",
    "hook_targets",
    "render_status_markdown",
    "run_install",
    "run_uninstall",
    "safe_relative",
]
