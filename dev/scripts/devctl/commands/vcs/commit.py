"""Governed commit command — wraps git commit with mandatory guard checks.

Runs ``devctl check --profile quick`` before every commit. If guards fail,
the commit is blocked and violations are reported. This is the programmatic
counterpart to the pre-commit hook in
``dev/config/templates/portable_governance_pre_commit_hook.sh``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from ...common import emit_output, write_output
from ...config import REPO_ROOT
from ...time_utils import utc_timestamp

GUARD_PROFILE = "quick"
DEVCTL_SCRIPT = "dev/scripts/devctl.py"


def _run_guard_bundle(
    *,
    repo_root: Path = REPO_ROOT,
    runner: Any = None,
) -> int:
    """Run the quick guard profile and return the exit code."""
    cmd = [
        sys.executable,
        str(repo_root / DEVCTL_SCRIPT),
        "check",
        "--profile",
        GUARD_PROFILE,
        "--format",
        "json",
    ]
    run_fn = runner or subprocess.run
    result = run_fn(cmd, cwd=str(repo_root), capture_output=True, text=True)
    if result.returncode != 0:
        # Show guard output on stderr so the operator sees what failed
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    return result.returncode


def _build_git_commit_cmd(args) -> list[str]:
    """Build the git commit command from parsed arguments."""
    cmd = ["git", "commit"]
    if getattr(args, "message", None):
        cmd.extend(["-m", args.message])
    if getattr(args, "amend", False):
        cmd.append("--amend")
    extra = getattr(args, "passthrough", None) or []
    cmd.extend(extra)
    return cmd


def _run_git_commit(
    args,
    *,
    repo_root: Path = REPO_ROOT,
    runner: Any = None,
) -> int:
    """Execute git commit and return the exit code."""
    cmd = _build_git_commit_cmd(args)
    run_fn = runner or subprocess.run
    result = run_fn(cmd, cwd=str(repo_root))
    return result.returncode


def run_commit(
    args,
    *,
    repo_root: Path = REPO_ROOT,
    guard_runner: Any = None,
    git_runner: Any = None,
) -> int:
    """Run governed commit: guards first, then git commit on success.

    Parameters
    ----------
    args:
        Parsed CLI arguments (must have ``message``, ``amend``,
        ``passthrough``, ``format``, ``output``).
    repo_root:
        Repository root path.
    guard_runner:
        Optional subprocess.run replacement for the guard check (testing).
    git_runner:
        Optional subprocess.run replacement for git commit (testing).

    Returns
    -------
    int
        0 on success, non-zero on guard failure or commit failure.
    """
    # Step 1: Run guard bundle
    guard_rc = _run_guard_bundle(repo_root=repo_root, runner=guard_runner)
    if guard_rc != 0:
        report = _build_report(
            status="blocked",
            reason="guard_bundle_failed",
            guard_exit_code=guard_rc,
        )
        _emit_report(args, report)
        return 1

    # Step 2: Run git commit
    commit_rc = _run_git_commit(
        args,
        repo_root=repo_root,
        runner=git_runner,
    )
    if commit_rc != 0:
        report = _build_report(status="failed", reason="git_commit_failed", git_exit_code=commit_rc)
        _emit_report(args, report)
        return commit_rc

    report = _build_report(status="committed")
    _emit_report(args, report)
    return 0


def _build_report(*, status: str, reason: str = "", **extra: object) -> dict[str, object]:
    """Build a commit-gate report dict."""
    r: dict[str, object] = {"command": "commit", "timestamp": utc_timestamp(), "status": status}
    if reason:
        r["reason"] = reason
    r.update(extra)
    return r


def _emit_report(args, report: dict[str, Any]) -> None:
    """Emit the commit report in the requested format."""
    import json

    fmt = getattr(args, "format", "md")
    if fmt == "json":
        output = json.dumps(report, indent=2)
    else:
        lines = [f"# devctl commit — {report['status']}"]
        for key, value in report.items():
            if key in {"command", "status"}:
                continue
            lines.append(f"- **{key}**: {value}")
        output = "\n".join(lines)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )


def run(args) -> int:
    """Entry point for ``devctl commit``."""
    return run_commit(args)
