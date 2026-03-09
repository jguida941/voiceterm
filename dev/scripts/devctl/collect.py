"""Collect git/CI/mutation status for reports."""

import json
import shutil
import subprocess
from typing import Any, Dict

from .clippy_pedantic import build_snapshot as build_clippy_pedantic_snapshot
from .collect_dev_logs import (
    DevLogSessionRow,
    DevLogSummary,
    collect_dev_log_summary,
)
from .config import REPO_ROOT

CI_RUN_FIELDS_EXTENDED = (
    "status,conclusion,displayTitle,name,event,headBranch,headSha,"
    "createdAt,updatedAt,url,databaseId"
)
CI_RUN_FIELDS_FALLBACK = "status,conclusion,displayTitle,headSha,createdAt,updatedAt"


def collect_git_status(since_ref: str | None = None, head_ref: str = "HEAD") -> Dict:
    """Return branch and dirty state info from git."""
    if not shutil.which("git"):
        return {"error": "git not found"}
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
        if since_ref:
            status_raw = subprocess.check_output(
                ["git", "diff", "--name-status", f"{since_ref}...{head_ref}"],
                cwd=REPO_ROOT,
                text=True,
            )
        else:
            status_raw = subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=REPO_ROOT,
                text=True,
            )
    except subprocess.CalledProcessError as exc:
        return {"error": f"git failed: {exc}"}

    changes = []
    if since_ref:
        for line in status_raw.splitlines():
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            status = parts[0].strip()
            path = parts[-1].strip()
            changes.append({"status": status, "path": path})
    else:
        for line in status_raw.splitlines():
            if not line:
                continue
            status = line[:2].strip()
            path = line[3:]
            if "->" in path:
                path = path.split("->")[-1].strip()
            changes.append({"status": status, "path": path})

    changed_paths = {change["path"] for change in changes}
    return {
        "branch": branch,
        "changes": changes,
        "changelog_updated": "dev/CHANGELOG.md" in changed_paths,
        "master_plan_updated": "dev/active/MASTER_PLAN.md" in changed_paths,
        "since_ref": since_ref,
        "head_ref": head_ref,
    }


def collect_ci_runs(limit: int) -> Dict:
    """Return recent GitHub Actions runs via gh, if available."""
    if not shutil.which("gh"):
        return {"error": "gh not found"}
    last_error: Exception | None = None
    for fields in (CI_RUN_FIELDS_EXTENDED, CI_RUN_FIELDS_FALLBACK):
        try:
            output = subprocess.check_output(
                [
                    "gh",
                    "run",
                    "list",
                    "--limit",
                    str(limit),
                    "--json",
                    fields,
                ],
                cwd=REPO_ROOT,
                text=True,
                stderr=subprocess.STDOUT,
            )
            runs = json.loads(output)
            if not isinstance(runs, list):
                return {"error": "gh run list returned non-list payload"}
            normalized_runs = _normalize_ci_runs(runs)
            result: Dict[str, Any] = {"runs": normalized_runs}
            if fields != CI_RUN_FIELDS_EXTENDED:
                result["warning"] = (
                    "gh run list fallback mode: extended fields unavailable; "
                    "upgrade gh for full CI run metadata."
                )
            return result
        except subprocess.CalledProcessError as exc:
            last_error = exc
            if (
                fields == CI_RUN_FIELDS_EXTENDED
                and _should_retry_ci_runs_with_fallback(exc)
            ):
                continue
            return {"error": _format_collect_ci_error(exc)}
        except Exception as exc:
            last_error = exc
            return {"error": f"gh run list failed: {exc}"}
    return {"error": f"gh run list failed: {last_error}"}


def _normalize_ci_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        row = dict(run)
        # Legacy `gh` versions can omit these fields; populate stable keys for callers.
        row.setdefault("name", row.get("displayTitle"))
        row.setdefault("event", None)
        row.setdefault("headBranch", None)
        row.setdefault("url", None)
        row.setdefault("databaseId", None)
        normalized.append(row)
    return normalized


def _should_retry_ci_runs_with_fallback(exc: subprocess.CalledProcessError) -> bool:
    output = (exc.output or "").lower()
    fallback_markers = (
        "unknown json field",
        "accepts the following fields",
        "invalid value for --json",
    )
    return any(marker in output for marker in fallback_markers)


def _format_collect_ci_error(exc: subprocess.CalledProcessError) -> str:
    output = (exc.output or "").strip()
    if output:
        return f"gh run list failed: {output}"
    return f"gh run list failed: {exc}"


def collect_mutation_summary() -> Dict:
    """Return the latest mutation summary via mutants.py."""
    if not shutil.which("python3"):
        return {"error": "python3 not found"}

    unavailable_result = {
        "results": {
            "score": None,
            "outcomes_path": str(REPO_ROOT / "rust" / "mutants.out" / "outcomes.json"),
            "outcomes_updated_at": "unknown",
            "outcomes_age_hours": None,
        },
    }
    try:
        output = subprocess.check_output(
            ["python3", "dev/scripts/mutants.py", "--results-only", "--json"],
            cwd=REPO_ROOT,
            text=True,
        )
        payload = output.strip()
        if not payload:
            result = dict(unavailable_result)
            result["warning"] = (
                "mutation outcomes are unavailable (empty results payload)"
            )
            return result
        if payload.lower().startswith("no results found under"):
            result = dict(unavailable_result)
            result["warning"] = payload
            return result
        return {"results": json.loads(payload)}
    except subprocess.CalledProcessError as exc:
        output = (exc.output or "").strip()
        if output.lower().startswith("no results found under"):
            result = dict(unavailable_result)
            result["warning"] = output
            return result
        if output:
            return {"error": f"mutants summary failed: {output}"}
        return {"error": f"mutants summary failed: {exc}"}
    except json.JSONDecodeError:
        result = dict(unavailable_result)
        result["warning"] = "mutation outcomes are unavailable (invalid JSON payload)"
        return result
    except Exception as exc:
        return {"error": f"mutants summary failed: {exc}"}


def collect_clippy_pedantic_summary(
    summary_path: str | None = None,
    lints_path: str | None = None,
    policy_path: str | None = None,
) -> Dict[str, Any]:
    """Return advisory `clippy::pedantic` summary from existing artifacts."""
    return build_clippy_pedantic_snapshot(
        summary_path=summary_path,
        lints_path=lints_path,
        policy_path=policy_path,
    )
