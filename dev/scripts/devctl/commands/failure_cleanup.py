"""devctl failure-cleanup command implementation."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from ..collect import collect_ci_runs
from ..common import confirm_or_abort, pipe_output, write_output
from ..config import REPO_ROOT

GREEN_CI_CONCLUSIONS = {"success", "neutral", "skipped"}
MAX_BLOCKING_RUNS = 15
FAILURE_ROOT_RELATIVE = Path("dev/reports/failures")
OUTSIDE_OVERRIDE_ROOT_RELATIVE = Path("dev/reports")


def _resolve_target_dir(
    directory_arg: str,
    *,
    allow_outside_failure_root: bool,
) -> tuple[Path | None, Path, str | None]:
    root = REPO_ROOT.resolve()
    failure_root = (root / FAILURE_ROOT_RELATIVE).resolve()
    override_root = (root / OUTSIDE_OVERRIDE_ROOT_RELATIVE).resolve()
    raw = Path(directory_arg).expanduser()
    target = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None, failure_root, f"target directory is outside repository root: {target}"
    if target == root:
        return None, failure_root, "refusing to delete repository root"
    if target == (root / ".git"):
        return None, failure_root, "refusing to delete .git directory"
    if not allow_outside_failure_root:
        try:
            target.relative_to(failure_root)
        except ValueError:
            return (
                None,
                failure_root,
                (
                    "target directory is outside default failure root "
                    f"({failure_root}); rerun with --allow-outside-failure-root if intentional"
                ),
            )
    else:
        try:
            target.relative_to(override_root)
        except ValueError:
            return (
                None,
                failure_root,
                (
                    "target directory is outside allowed override root "
                    f"({override_root}); override mode only permits paths under dev/reports"
                ),
            )
    return target, failure_root, None


def _count_tree_entries(root: Path) -> tuple[int, int]:
    file_count = 0
    dir_count = 0
    for path in root.rglob("*"):
        if path.is_file():
            file_count += 1
        elif path.is_dir():
            dir_count += 1
    return file_count, dir_count


def _summarize_blocking_runs(runs: list[dict]) -> list[dict]:
    summaries = []
    for run in runs[:MAX_BLOCKING_RUNS]:
        summaries.append(
            {
                "databaseId": run.get("databaseId"),
                "displayTitle": run.get("displayTitle", "unknown"),
                "name": run.get("name", "unknown"),
                "event": run.get("event", "unknown"),
                "headBranch": run.get("headBranch", "unknown"),
                "status": run.get("status", "unknown"),
                "conclusion": run.get("conclusion") or "pending",
                "updatedAt": run.get("updatedAt"),
                "headSha": run.get("headSha"),
                "url": run.get("url"),
            }
        )
    return summaries


def _normalize_ci_filters(args) -> dict[str, str]:
    return {
        "branch": str(getattr(args, "ci_branch", "") or "").strip(),
        "workflow": str(getattr(args, "ci_workflow", "") or "").strip(),
        "event": str(getattr(args, "ci_event", "") or "").strip().lower(),
        "sha": str(getattr(args, "ci_sha", "") or "").strip().lower(),
    }


def _run_matches_filters(run: dict, filters: dict[str, str]) -> bool:
    branch = filters.get("branch", "")
    if branch and str(run.get("headBranch") or "").strip() != branch:
        return False

    workflow = filters.get("workflow", "").lower()
    if workflow:
        display = str(run.get("displayTitle") or "").strip().lower()
        name = str(run.get("name") or "").strip().lower()
        if workflow not in display and workflow not in name:
            return False

    event = filters.get("event", "")
    if event and str(run.get("event") or "").strip().lower() != event:
        return False

    sha = filters.get("sha", "")
    if sha and not str(run.get("headSha") or "").strip().lower().startswith(sha):
        return False

    return True


def _evaluate_ci_gate(
    ci_limit: int,
    *,
    filters: dict[str, str],
) -> tuple[bool, dict, list[dict], int, str | None]:
    ci_report = collect_ci_runs(ci_limit)
    if "error" in ci_report:
        return False, ci_report, [], 0, str(ci_report.get("error") or "ci gate error")
    runs = ci_report.get("runs", [])
    if not isinstance(runs, list):
        return False, {"error": "invalid gh run list payload"}, [], 0, "invalid gh run list payload"

    matched_runs = [run for run in runs if isinstance(run, dict) and _run_matches_filters(run, filters)]
    if not matched_runs:
        return False, ci_report, [], 0, "No CI runs matched the selected cleanup filters."

    blocking_runs: list[dict] = []
    for run in matched_runs:
        status = str(run.get("status") or "").lower()
        conclusion = str(run.get("conclusion") or "").lower()
        if status != "completed":
            blocking_runs.append(run)
            continue
        if conclusion not in GREEN_CI_CONCLUSIONS:
            blocking_runs.append(run)

    return (
        not blocking_runs,
        ci_report,
        _summarize_blocking_runs(blocking_runs),
        len(matched_runs),
        None,
    )


def _render_md(report: dict) -> str:
    lines = ["# devctl failure-cleanup", ""]
    lines.append(f"- directory: {report['directory']}")
    lines.append(f"- directory_exists: {report['directory_exists']}")
    lines.append(f"- files_found: {report['files_found']}")
    lines.append(f"- directories_found: {report['directories_found']}")
    lines.append(f"- failure_root: {report['failure_root']}")
    lines.append(f"- allow_outside_failure_root: {report['allow_outside_failure_root']}")
    lines.append(f"- require_green_ci: {report['require_green_ci']}")
    lines.append(f"- ci_limit: {report['ci_limit']}")
    lines.append(f"- ci_filters: {report['ci_filters']}")
    if report["require_green_ci"]:
        lines.append(f"- ci_gate_ok: {report['ci_gate_ok']}")
        lines.append(f"- ci_matched_runs: {report['ci_matched_runs']}")
    if report.get("ci_error"):
        lines.append(f"- ci_error: {report['ci_error']}")
    lines.append(f"- dry_run: {report['dry_run']}")
    lines.append(f"- deleted: {report['deleted']}")

    if report.get("blocking_ci_runs"):
        lines.append("")
        lines.append("## Blocking CI runs")
        for run in report["blocking_ci_runs"]:
            lines.append(
                "- {title} [{event} {branch}]: {status}/{conclusion} (updated={updated})".format(
                    title=run["displayTitle"],
                    event=run.get("event") or "unknown",
                    branch=run.get("headBranch") or "unknown",
                    status=run["status"],
                    conclusion=run["conclusion"],
                    updated=run.get("updatedAt") or "unknown",
                )
            )

    if report.get("errors"):
        lines.append("")
        lines.append("## Errors")
        for error in report["errors"]:
            lines.append(f"- {error}")

    lines.append(f"- ok: {report['ok']}")
    return "\n".join(lines)


def run(args) -> int:
    """Delete failure triage artifacts once safeguards pass."""
    ci_filters = _normalize_ci_filters(args)
    target, failure_root, target_error = _resolve_target_dir(
        args.directory,
        allow_outside_failure_root=bool(getattr(args, "allow_outside_failure_root", False)),
    )
    errors: list[str] = []
    if target_error:
        errors.append(target_error)

    ci_gate_ok = True
    ci_report = None
    blocking_ci_runs: list[dict] = []
    ci_matched_runs = 0
    ci_error = None
    if args.require_green_ci:
        ci_gate_ok, ci_report, blocking_ci_runs, ci_matched_runs, gate_error = _evaluate_ci_gate(
            args.ci_limit,
            filters=ci_filters,
        )
        if gate_error:
            ci_error = gate_error
        if not ci_gate_ok and not ci_error:
            errors.append(
                "Recent CI runs are not fully green; resolve failures/cancellations before cleanup."
            )
        if ci_error:
            errors.append(f"Unable to evaluate CI gate: {ci_error}")

    directory_exists = bool(target and target.exists())
    files_found = 0
    directories_found = 0
    if directory_exists and target is not None:
        files_found, directories_found = _count_tree_entries(target)

    deleted = False
    ok = not errors
    if ok and directory_exists and target is not None:
        if args.dry_run:
            deleted = False
        else:
            try:
                confirm_or_abort(
                    f"Delete failure artifact directory `{target}`?",
                    args.yes,
                )
                shutil.rmtree(target)
                deleted = True
                directory_exists = False
                files_found = 0
                directories_found = 0
            except OSError as exc:
                ok = False
                errors.append(f"failed to delete directory: {exc}")
            except SystemExit:
                ok = False
                errors.append("cleanup aborted by user")

    report = {
        "command": "failure-cleanup",
        "timestamp": datetime.now().isoformat(),
        "directory": str(target) if target is not None else args.directory,
        "directory_exists": directory_exists,
        "files_found": files_found,
        "directories_found": directories_found,
        "failure_root": str(failure_root),
        "allow_outside_failure_root": bool(getattr(args, "allow_outside_failure_root", False)),
        "require_green_ci": bool(args.require_green_ci),
        "ci_limit": int(args.ci_limit),
        "ci_filters": ci_filters,
        "ci_gate_ok": ci_gate_ok,
        "ci_matched_runs": ci_matched_runs,
        "ci_error": ci_error,
        "blocking_ci_runs": blocking_ci_runs,
        "dry_run": bool(args.dry_run),
        "deleted": deleted,
        "errors": errors,
        "ok": ok,
    }
    if ci_report is not None:
        report["ci"] = ci_report

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)

    write_output(output, args.output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc
    return 0 if ok else 1
