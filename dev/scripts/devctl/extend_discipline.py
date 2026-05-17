"""Extension-vs-build verification for ``devctl guard-run``."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable, Iterable

from .config import REPO_ROOT
from .time_utils import utc_timestamp

EXTEND_DISCIPLINE_CHECK_ID = "extend-discipline"
EXTEND_DISCIPLINE_TOGGLE_ID = "ExtensionVsBuildVerificationAutomation"
EXTEND_DISCIPLINE_MODES = ("auto", "manual", "disabled")

_GitRunner = Callable[..., subprocess.CompletedProcess[str]]


def build_extend_discipline_report(
    *,
    mode: str = "manual",
    repo_root: Path = REPO_ROOT,
    git_runner: _GitRunner = subprocess.run,
) -> dict[str, Any]:
    """Return a report classifying dirty work as extending or building."""
    normalized_mode = str(mode or "manual").strip()
    errors: list[str] = []
    if normalized_mode not in EXTEND_DISCIPLINE_MODES:
        errors.append(
            f"Unknown extend-discipline mode `{normalized_mode}`. "
            f"Expected one of: {', '.join(EXTEND_DISCIPLINE_MODES)}."
        )
        normalized_mode = "manual"
    if normalized_mode == "disabled":
        report = _base_report(normalized_mode)
        report.update(
            {
                "ok": not errors,
                "status": "disabled" if not errors else "error",
                "verdict": "DISABLED",
                "extended": [],
                "built": [],
                "untracked_audit": {"count": 0, "paths": []},
                "diff_audit": _empty_diff_audit(),
                "warnings": ["Extension-vs-build verification is disabled."],
                "errors": errors,
                "attention_required": False,
            }
        )
        return report

    status_result = _run_git(
        ["git", "status", "--short", "--untracked-files=all"],
        repo_root=repo_root,
        git_runner=git_runner,
    )
    diff_result = _run_git(
        ["git", "diff", "--numstat", "HEAD", "--"],
        repo_root=repo_root,
        git_runner=git_runner,
    )
    if status_result.returncode != 0:
        errors.append(status_result.stderr.strip() or "git status failed")
    if diff_result.returncode != 0:
        errors.append(diff_result.stderr.strip() or "git diff --numstat failed")

    return classify_extend_discipline(
        status_lines=status_result.stdout.splitlines(),
        diff_lines=diff_result.stdout.splitlines(),
        mode=normalized_mode,
        errors=errors,
    )


def classify_extend_discipline(
    *,
    status_lines: Iterable[str],
    diff_lines: Iterable[str],
    mode: str = "manual",
    errors: Iterable[str] = (),
) -> dict[str, Any]:
    """Classify git status/numstat rows into extend/build buckets."""
    normalized_mode = str(mode or "manual").strip()
    parsed = [_parse_status_line(line) for line in status_lines]
    entries = [entry for entry in parsed if entry is not None]
    built = [entry for entry in entries if entry["classification"] == "built"]
    extended = [entry for entry in entries if entry["classification"] == "extended"]
    untracked_paths = [
        str(entry["path"]) for entry in built if entry.get("status") == "??"
    ]
    diff_audit = _parse_diff_numstat(diff_lines)
    verdict = _verdict(extended=extended, built=built)
    warnings: list[str] = []
    report_errors = [str(error) for error in errors if str(error).strip()]
    attention_required = verdict in {"BUILD", "MIXED"}
    if attention_required:
        message = (
            "New build paths detected; verify they extend existing authority or "
            "carry explicit new-surface wiring before committing."
        )
        if normalized_mode == "auto":
            report_errors.append(message)
        else:
            warnings.append(message)

    report = _base_report(normalized_mode)
    report.update(
        {
            "ok": not report_errors,
            "status": "error" if report_errors else ("attention" if warnings else "ok"),
            "verdict": verdict,
            "extended": extended,
            "built": built,
            "untracked_audit": {
                "count": len(untracked_paths),
                "paths": untracked_paths,
            },
            "diff_audit": diff_audit,
            "warnings": warnings,
            "errors": report_errors,
            "attention_required": attention_required,
        }
    )
    return report


def build_extend_discipline_markdown(report: dict[str, Any]) -> str:
    """Render the extension-vs-build report in markdown."""
    lines = ["# devctl guard-run", ""]
    lines.append(f"- check: {report.get('check')}")
    lines.append(f"- toggle_id: {report.get('toggle_id')}")
    lines.append(f"- mode: {report.get('mode')}")
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- status: {report.get('status')}")
    lines.append(f"- verdict: {report.get('verdict')}")
    lines.append(f"- extended_count: {len(report.get('extended') or [])}")
    lines.append(f"- built_count: {len(report.get('built') or [])}")
    lines.append(f"- untracked_count: {(report.get('untracked_audit') or {}).get('count', 0)}")
    diff_audit = report.get("diff_audit") or {}
    lines.append(f"- diff_churn: {diff_audit.get('diff_churn', 0)}")
    _append_entries(lines, "Extended Paths", report.get("extended") or [])
    _append_entries(lines, "Built Paths", report.get("built") or [])
    _append_messages(lines, "Warnings", report.get("warnings") or [])
    _append_messages(lines, "Errors", report.get("errors") or [])
    return "\n".join(lines)


def _base_report(mode: str) -> dict[str, Any]:
    return {
        "command": "guard-run",
        "check": EXTEND_DISCIPLINE_CHECK_ID,
        "toggle_id": EXTEND_DISCIPLINE_TOGGLE_ID,
        "mode": mode,
        "timestamp": utc_timestamp(),
    }


def _run_git(
    command: list[str],
    *,
    repo_root: Path,
    git_runner: _GitRunner,
) -> subprocess.CompletedProcess[str]:
    return git_runner(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )


def _parse_status_line(line: str) -> dict[str, str] | None:
    text = line.rstrip()
    if len(text) < 4:
        return None
    status = text[:2]
    path = text[3:]
    if not path:
        return None
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    if status == "??" or "A" in status:
        return {
            "path": path,
            "status": status,
            "classification": "built",
            "reason": "new_or_added_path",
        }
    if status.strip():
        return {
            "path": path,
            "status": status,
            "classification": "extended",
            "reason": "tracked_path_changed",
        }
    return None


def _parse_diff_numstat(lines: Iterable[str]) -> dict[str, Any]:
    paths: list[dict[str, Any]] = []
    total_added = 0
    total_removed = 0
    for line in lines:
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added = _parse_count(parts[0])
        removed = _parse_count(parts[1])
        path = parts[-1]
        if added is not None:
            total_added += added
        if removed is not None:
            total_removed += removed
        paths.append(
            {
                "path": path,
                "lines_added": added,
                "lines_removed": removed,
            }
        )
    return {
        "count": len(paths),
        "paths": paths,
        "lines_added": total_added,
        "lines_removed": total_removed,
        "diff_churn": total_added + total_removed,
    }


def _empty_diff_audit() -> dict[str, Any]:
    return {
        "count": 0,
        "paths": [],
        "lines_added": 0,
        "lines_removed": 0,
        "diff_churn": 0,
    }


def _parse_count(value: str) -> int | None:
    return int(value) if value.isdigit() else None


def _verdict(*, extended: list[dict[str, str]], built: list[dict[str, str]]) -> str:
    if extended and built:
        return "MIXED"
    if built:
        return "BUILD"
    if extended:
        return "EXTEND"
    return "CLEAN"


def _append_entries(
    lines: list[str],
    title: str,
    entries: list[dict[str, Any]],
) -> None:
    if not entries:
        return
    lines.extend(["", f"## {title}"])
    for entry in entries:
        lines.append(
            f"- {entry.get('path')} ({entry.get('status')}, {entry.get('reason')})"
        )


def _append_messages(lines: list[str], title: str, messages: list[str]) -> None:
    if not messages:
        return
    lines.extend(["", f"## {title}"])
    for message in messages:
        lines.append(f"- {message}")
