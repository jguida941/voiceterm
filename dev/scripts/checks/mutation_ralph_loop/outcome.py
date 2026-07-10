"""Outcome/fix helpers for the bounded mutation remediation loop."""

from __future__ import annotations

from dataclasses import dataclass
import tempfile
from pathlib import Path
from typing import Any, Callable

try:
    from dev.scripts.checks.mutation_outcome_parse import aggregate_outcomes
except ModuleNotFoundError:  # pragma: no cover
    from checks.mutation_outcome_parse import aggregate_outcomes

try:
    from dev.scripts.checks.workflow_loop_utils import download_run_artifacts
except ModuleNotFoundError:  # pragma: no cover
    from checks.workflow_loop_utils import download_run_artifacts


@dataclass(frozen=True)
class FixCommandContext:
    attempt: int
    repo: str
    branch: str
    run_id: int
    run_sha: str
    threshold: float


@dataclass
class AttemptScoreContext:
    report: dict[str, Any]
    attempt_row: dict[str, Any]
    score: float
    threshold: float
    mode: str
    fix_command: str | None
    fix_block_reason: str | None
    missed: int
    fix_context: FixCommandContext
    run_fix_command_fn: Callable[[str, FixCommandContext], tuple[int, str | None]]


def record_attempt_result(
    *,
    report: dict[str, Any],
    attempt_row: dict[str, Any],
    status: str,
    message: str,
    reason: str,
) -> None:
    attempt_row["status"] = status
    attempt_row["message"] = message
    report["attempts"].append(attempt_row)
    report["reason"] = reason


def record_outcome_summary(
    *,
    report: dict[str, Any],
    attempt_row: dict[str, Any],
    attempt: int,
    outcome_report: dict[str, Any],
) -> tuple[float, dict[str, Any], int]:
    score = float(outcome_report.get("score") or 0.0)
    counts = outcome_report.get("counts", {})
    missed = int(counts.get("missed", 0)) if isinstance(counts, dict) else 0
    attempt_row["score"] = round(score, 6)
    attempt_row["counts"] = counts
    attempt_row["hotspots"] = outcome_report.get("hotspots", [])[:10]
    attempt_row["freshness"] = outcome_report.get("freshness", [])
    report["completed_attempts"] = attempt
    report["last_score"] = round(score, 6)
    report["last_counts"] = counts
    report["last_hotspots"] = outcome_report.get("hotspots", [])[:10]
    report["last_freshness"] = outcome_report.get("freshness", [])
    return score, counts, missed


def load_attempt_outcome(
    *,
    repo: str,
    run_id: int,
    attempt: int,
) -> tuple[dict[str, Any] | None, str | None, str | None]:
    with tempfile.TemporaryDirectory(prefix="mutation-loop-") as temp_dir:
        download_root = Path(temp_dir) / f"attempt-{attempt}"
        download_error = download_run_artifacts(repo, run_id, download_root)
        if download_error:
            return None, f"artifact download failed: {download_error}", "artifact download failed"

        outcome_report, outcome_error = aggregate_outcomes(download_root)
        if outcome_error:
            return None, f"outcome parse failed: {outcome_error}", "outcome parse failed"
        return outcome_report, None, None


def handle_attempt_score(context: AttemptScoreContext) -> tuple[bool, str]:
    if context.score >= context.threshold:
        context.report["attempts"].append(
            {
                **context.attempt_row,
                "status": "resolved",
                "message": (
                    f"mutation score {context.score:.2%} meets threshold "
                    f"{context.threshold:.2%}"
                ),
            }
        )
        context.report["ok"] = True
        context.report["reason"] = "threshold_met"
        return False, ""

    if context.mode == "report-only":
        record_attempt_result(
            report=context.report,
            attempt_row=context.attempt_row,
            status="reported",
            message=(
                f"mutation score {context.score:.2%} below threshold "
                f"{context.threshold:.2%}; report-only mode"
            ),
            reason="report_only_below_threshold",
        )
        return False, ""

    if not context.fix_command:
        record_attempt_result(
            report=context.report,
            attempt_row=context.attempt_row,
            status="blocked",
            message=(
                f"mutation score {context.score:.2%} below threshold with no "
                "--fix-command configured"
            ),
            reason="no_fix_command_configured",
        )
        return False, ""

    if context.fix_block_reason:
        context.attempt_row["status"] = "blocked"
        context.attempt_row["message"] = context.fix_block_reason
        context.attempt_row["missed_survivors"] = context.missed
        context.report["attempts"].append(context.attempt_row)
        context.report["reason"] = "fix_command_policy_blocked"
        return False, ""

    fix_rc, fix_error = context.run_fix_command_fn(
        context.fix_command,
        context.fix_context,
    )
    context.attempt_row["fix_exit_code"] = fix_rc
    if fix_error:
        record_attempt_result(
            report=context.report,
            attempt_row=context.attempt_row,
            status="failed",
            message=f"fix command error: {fix_error}",
            reason="fix_command_error",
        )
        return False, ""
    if fix_rc != 0:
        record_attempt_result(
            report=context.report,
            attempt_row=context.attempt_row,
            status="failed",
            message="fix command returned non-zero exit code",
            reason="fix_command_failed",
        )
        return False, ""

    context.report["attempts"].append(
        {
            **context.attempt_row,
            "status": "waiting-for-new-run",
            "message": (
                f"mutation score {context.score:.2%} below threshold; "
                "fix command applied"
            ),
        }
    )
    return True, context.fix_context.run_sha
