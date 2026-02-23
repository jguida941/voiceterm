"""Collect git/CI/mutation status for reports."""

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .config import REPO_ROOT


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
                ["git", "status", "--porcelain"],
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
    try:
        output = subprocess.check_output(
            [
                "gh",
                "run",
                "list",
                "--limit",
                str(limit),
                "--json",
                "status,conclusion,displayTitle,headSha,createdAt,updatedAt",
            ],
            cwd=REPO_ROOT,
            text=True,
        )
        return {"runs": json.loads(output)}
    except Exception as exc:
        return {"error": f"gh run list failed: {exc}"}


def collect_mutation_summary() -> Dict:
    """Return the latest mutation summary via mutants.py."""
    if not shutil.which("python3"):
        return {"error": "python3 not found"}
    try:
        output = subprocess.check_output(
            ["python3", "dev/scripts/mutants.py", "--results-only", "--json"],
            cwd=REPO_ROOT,
            text=True,
        )
        return {"results": json.loads(output)}
    except Exception as exc:
        return {"error": f"mutants summary failed: {exc}"}


def collect_dev_log_summary(dev_root: str | None = None, session_limit: int = 5) -> Dict[str, Any]:
    """Return aggregate summary for guarded Dev Mode JSONL sessions."""
    root = _resolve_dev_root(dev_root)
    sessions_dir = root / "sessions"
    limit = max(1, int(session_limit))

    summary: Dict[str, Any] = {
        "dev_root": str(root),
        "sessions_dir": str(sessions_dir),
        "sessions_dir_exists": sessions_dir.is_dir(),
        "session_files_total": 0,
        "sessions_scanned": 0,
        "events_scanned": 0,
        "transcript_events": 0,
        "empty_events": 0,
        "error_events": 0,
        "total_words": 0,
        "latency_samples": 0,
        "avg_latency_ms": None,
        "parse_errors": 0,
        "latest_event_unix_ms": None,
        "recent_sessions": [],
    }
    if not sessions_dir.is_dir():
        return summary

    files = _session_files_sorted(sessions_dir)
    summary["session_files_total"] = len(files)
    scanned = files[:limit]
    summary["sessions_scanned"] = len(scanned)

    latency_sum = 0
    for path in scanned:
        session_row: Dict[str, Any] = {
            "file": path.name,
            "events": 0,
            "transcript_events": 0,
            "empty_events": 0,
            "error_events": 0,
            "latency_samples": 0,
            "avg_latency_ms": None,
            "parse_errors": 0,
        }
        session_latency_sum = 0
        try:
            with path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    session_row["events"] += 1
                    summary["events_scanned"] += 1
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        session_row["parse_errors"] += 1
                        summary["parse_errors"] += 1
                        continue
                    if not isinstance(event, dict):
                        session_row["parse_errors"] += 1
                        summary["parse_errors"] += 1
                        continue

                    kind = str(event.get("kind", "")).strip().lower()
                    if kind == "transcript":
                        session_row["transcript_events"] += 1
                        summary["transcript_events"] += 1
                    elif kind == "empty":
                        session_row["empty_events"] += 1
                        summary["empty_events"] += 1
                    elif kind == "error":
                        session_row["error_events"] += 1
                        summary["error_events"] += 1

                    words = _coerce_nonnegative_int(event.get("transcript_words"))
                    summary["total_words"] += words

                    latency = _coerce_nonnegative_int_or_none(event.get("latency_ms"))
                    if latency is not None:
                        session_row["latency_samples"] += 1
                        summary["latency_samples"] += 1
                        session_latency_sum += latency
                        latency_sum += latency

                    timestamp = _coerce_nonnegative_int_or_none(event.get("timestamp_unix_ms"))
                    if timestamp is not None and (
                        summary["latest_event_unix_ms"] is None
                        or timestamp > summary["latest_event_unix_ms"]
                    ):
                        summary["latest_event_unix_ms"] = timestamp
        except OSError as exc:
            session_row["error"] = str(exc)

        if session_row["latency_samples"] > 0:
            session_row["avg_latency_ms"] = int(
                session_latency_sum / session_row["latency_samples"]
            )
        summary["recent_sessions"].append(session_row)

    if summary["latency_samples"] > 0:
        summary["avg_latency_ms"] = int(latency_sum / summary["latency_samples"])
    latest_ts = summary["latest_event_unix_ms"]
    if isinstance(latest_ts, int):
        summary["latest_event_iso"] = _unix_ms_to_iso(latest_ts)
    else:
        summary["latest_event_iso"] = None
    return summary


def _resolve_dev_root(dev_root: str | None) -> Path:
    if dev_root:
        return Path(dev_root).expanduser()
    home = os.environ.get("HOME", "").strip()
    if home:
        return Path(home).expanduser() / ".voiceterm" / "dev"
    return REPO_ROOT / ".voiceterm" / "dev"


def _session_files_sorted(sessions_dir: Path) -> list[Path]:
    files = [path for path in sessions_dir.glob("session-*.jsonl") if path.is_file()]
    files.sort(
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )
    return files


def _coerce_nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    return 0


def _coerce_nonnegative_int_or_none(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    return None


def _unix_ms_to_iso(unix_ms: int) -> str:
    return datetime.fromtimestamp(unix_ms / 1000.0, tz=timezone.utc).isoformat()
