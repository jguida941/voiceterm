"""devctl sync command implementation.

Synchronize selected branches against a remote with explicit safety guards:
- clean worktree required unless --allow-dirty
- fast-forward-only pulls (`git pull --ff-only`)
- optional push for local-ahead branches
- restore the starting branch at the end
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import Dict, List

from ..collect import collect_git_status
from ..common import pipe_output, run_cmd, write_output
from ..config import REPO_ROOT

DEFAULT_SYNC_BRANCHES = ("develop", "master")
MAX_DIRTY_PATHS = 12


def _unique_preserve_order(values: List[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _run_git_capture(args: List[str]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, (completed.stdout or "").strip(), (completed.stderr or "").strip()


def _remote_exists(remote: str) -> bool:
    code, _, _ = _run_git_capture(["remote", "get-url", remote])
    return code == 0


def _branch_exists(branch: str) -> bool:
    code, _, _ = _run_git_capture(["rev-parse", "--verify", "--quiet", branch])
    return code == 0


def _remote_branch_exists(remote: str, branch: str) -> bool:
    code, _, _ = _run_git_capture(
        ["show-ref", "--verify", "--quiet", f"refs/remotes/{remote}/{branch}"]
    )
    return code == 0


def _branch_divergence(remote: str, branch: str) -> Dict:
    code, output, error = _run_git_capture(
        ["rev-list", "--left-right", "--count", f"{remote}/{branch}...{branch}"]
    )
    if code != 0:
        message = error or output or f"git rev-list exited with code {code}"
        return {"behind": None, "ahead": None, "error": message}

    parts = output.split()
    if len(parts) != 2:
        return {"behind": None, "ahead": None, "error": f"Unexpected divergence output: {output!r}"}

    try:
        behind = int(parts[0])
        ahead = int(parts[1])
    except ValueError:
        return {"behind": None, "ahead": None, "error": f"Unable to parse divergence output: {output!r}"}
    return {"behind": behind, "ahead": ahead, "error": None}


def _summarize_dirty_paths(changes: list[dict]) -> list[str]:
    paths = [str(change.get("path", "")).strip() for change in changes]
    filtered = [path for path in paths if path]
    if len(filtered) <= MAX_DIRTY_PATHS:
        return filtered
    hidden = len(filtered) - MAX_DIRTY_PATHS
    return filtered[:MAX_DIRTY_PATHS] + [f"... (+{hidden} more)"]


def _render_md(report: Dict) -> str:
    lines = ["# devctl sync", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- remote: {report['remote']}")
    lines.append(f"- start_branch: {report['start_branch']}")
    lines.append(f"- target_branches: {', '.join(report['target_branches']) or 'none'}")
    lines.append(f"- allow_dirty: {report['allow_dirty']}")
    lines.append(f"- push: {report['push']}")
    lines.append(f"- errors: {len(report['errors'])}")
    lines.append(f"- warnings: {len(report['warnings'])}")
    lines.append("")
    lines.append("| Branch | Status | Behind | Ahead | Notes |")
    lines.append("|---|---|---:|---:|---|")
    for branch in report["branches"]:
        behind = "-" if branch["behind"] is None else str(branch["behind"])
        ahead = "-" if branch["ahead"] is None else str(branch["ahead"])
        notes = "; ".join(branch["notes"]) if branch["notes"] else "-"
        lines.append(
            f"| `{branch['branch']}` | {branch['status']} | {behind} | {ahead} | {notes} |"
        )
    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {message}" for message in report["errors"])
    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        lines.extend(f"- {message}" for message in report["warnings"])
    return "\n".join(lines)


def run(args) -> int:
    """Sync selected branches with guardrails and optional push behavior."""
    git = collect_git_status()
    errors: List[str] = []
    warnings: List[str] = []
    branches_report: List[Dict] = []

    if "error" in git:
        errors.append(git["error"])
        start_branch = ""
        dirty_paths: List[str] = []
    else:
        start_branch = str(git.get("branch", "")).strip()
        dirty_paths = _summarize_dirty_paths(git.get("changes", []))

    requested = list(args.branches) if args.branches else list(DEFAULT_SYNC_BRANCHES)
    if start_branch and start_branch != "HEAD" and not args.no_current:
        requested.append(start_branch)
    target_branches = _unique_preserve_order(requested)

    if not target_branches:
        errors.append("No branches selected. Use --branches and/or remove --no-current.")
    if start_branch == "HEAD":
        errors.append("Detached HEAD is not supported. Check out a branch first.")
    if dirty_paths and not args.allow_dirty:
        errors.append(
            "Working tree has uncommitted changes. Commit/stash first or re-run with --allow-dirty."
        )
    if not _remote_exists(args.remote):
        errors.append(f"Remote '{args.remote}' is not configured.")

    fetch_step = None
    restore_step = None
    active_branch = start_branch

    if not errors:
        fetch_step = run_cmd("git-fetch", ["git", "fetch", args.remote], cwd=REPO_ROOT)
        if fetch_step["returncode"] != 0:
            errors.append(f"git fetch failed for remote '{args.remote}'.")

    for branch in target_branches:
        branch_row: Dict = {
            "branch": branch,
            "status": "pending",
            "behind": None,
            "ahead": None,
            "notes": [],
            "steps": [],
        }

        if errors and fetch_step is None:
            branch_row["status"] = "skipped"
            branch_row["notes"].append("Skipped due to preflight guard failure.")
            branches_report.append(branch_row)
            continue

        if not _branch_exists(branch):
            message = f"Local branch '{branch}' is missing."
            branch_row["status"] = "missing-local"
            branch_row["notes"].append(message)
            errors.append(message)
            branches_report.append(branch_row)
            continue

        if not _remote_branch_exists(args.remote, branch):
            message = f"Remote ref '{args.remote}/{branch}' is missing."
            branch_row["status"] = "missing-remote"
            branch_row["notes"].append(message)
            errors.append(message)
            branches_report.append(branch_row)
            continue

        if active_branch != branch:
            checkout = run_cmd(
                f"git-checkout-{branch}",
                ["git", "checkout", branch],
                cwd=REPO_ROOT,
            )
            branch_row["steps"].append(checkout)
            if checkout["returncode"] != 0:
                message = f"Checkout failed for branch '{branch}'."
                branch_row["status"] = "checkout-failed"
                branch_row["notes"].append(message)
                errors.append(message)
                branches_report.append(branch_row)
                continue
            active_branch = branch

        pull = run_cmd(
            f"git-pull-{branch}",
            ["git", "pull", "--ff-only", args.remote, branch],
            cwd=REPO_ROOT,
        )
        branch_row["steps"].append(pull)
        if pull["returncode"] != 0:
            message = f"Fast-forward pull failed for '{branch}'."
            branch_row["status"] = "pull-failed"
            branch_row["notes"].append(message)
            errors.append(message)
            branches_report.append(branch_row)
            continue

        divergence = _branch_divergence(args.remote, branch)
        if divergence["error"]:
            message = f"Unable to compute divergence for '{branch}': {divergence['error']}"
            branch_row["status"] = "divergence-error"
            branch_row["notes"].append(message)
            errors.append(message)
            branches_report.append(branch_row)
            continue

        branch_row["behind"] = divergence["behind"]
        branch_row["ahead"] = divergence["ahead"]

        if args.push and (branch_row["ahead"] or 0) > 0:
            push = run_cmd(
                f"git-push-{branch}",
                ["git", "push", args.remote, branch],
                cwd=REPO_ROOT,
            )
            branch_row["steps"].append(push)
            if push["returncode"] != 0:
                message = f"Push failed for '{branch}'."
                branch_row["status"] = "push-failed"
                branch_row["notes"].append(message)
                errors.append(message)
                branches_report.append(branch_row)
                continue
            divergence = _branch_divergence(args.remote, branch)
            if divergence["error"]:
                message = f"Unable to recompute divergence for '{branch}': {divergence['error']}"
                branch_row["status"] = "divergence-error"
                branch_row["notes"].append(message)
                errors.append(message)
                branches_report.append(branch_row)
                continue
            branch_row["behind"] = divergence["behind"]
            branch_row["ahead"] = divergence["ahead"]

        behind = int(branch_row["behind"] or 0)
        ahead = int(branch_row["ahead"] or 0)
        if behind == 0 and ahead == 0:
            branch_row["status"] = "synced"
        elif behind > 0 and ahead > 0:
            message = f"Branch '{branch}' diverged from {args.remote}/{branch}."
            branch_row["status"] = "diverged"
            branch_row["notes"].append(message)
            errors.append(message)
        elif behind > 0:
            message = f"Branch '{branch}' is behind {args.remote}/{branch} after pull."
            branch_row["status"] = "behind"
            branch_row["notes"].append(message)
            errors.append(message)
        else:
            branch_row["status"] = "ahead"
            if args.push:
                message = f"Branch '{branch}' is still ahead after push attempt."
                branch_row["notes"].append(message)
                errors.append(message)
            else:
                message = (
                    f"Branch '{branch}' is ahead of {args.remote}/{branch}; "
                    "re-run with --push to fully sync."
                )
                branch_row["notes"].append(message)
                errors.append(message)
        branches_report.append(branch_row)

    if start_branch and active_branch and active_branch != start_branch:
        restore_step = run_cmd(
            "git-restore-start-branch",
            ["git", "checkout", start_branch],
            cwd=REPO_ROOT,
        )
        if restore_step["returncode"] != 0:
            errors.append(f"Failed to restore starting branch '{start_branch}'.")
        else:
            active_branch = start_branch

    report = {
        "command": "sync",
        "timestamp": datetime.now().isoformat(),
        "ok": len(errors) == 0,
        "remote": args.remote,
        "start_branch": start_branch,
        "active_branch": active_branch,
        "target_branches": target_branches,
        "allow_dirty": bool(args.allow_dirty),
        "push": bool(args.push),
        "dirty_paths": dirty_paths,
        "fetch_step": fetch_step,
        "restore_step": restore_step,
        "branches": branches_report,
        "errors": errors,
        "warnings": warnings,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)
    write_output(output, args.output)

    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 0 if report["ok"] else 1
