"""devctl governance-quality-feedback command implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...governance.quality_feedback.report_builder import (
    ReportBuilderConfig,
    build_quality_feedback_report,
    write_quality_feedback_artifact,
)
from ...governance.quality_feedback.report_render import (
    render_quality_feedback_markdown,
)
from .common import emit_governance_command_output, render_governance_value_error


def run(args) -> int:
    """Build and emit a composite quality feedback report."""
    try:
        repo_root = Path(getattr(args, "repo_path", None) or ".").resolve()
        repo_name = getattr(args, "repo_name", None) or repo_root.name

        previous_snapshot: dict[str, Any] | None = None
        prev_path = getattr(args, "previous_snapshot", None)
        if prev_path:
            prev_file = Path(prev_path).expanduser()
            if prev_file.exists():
                previous_snapshot = json.loads(
                    prev_file.read_text(encoding="utf-8")
                )

        snapshot = build_quality_feedback_report(
            repo_root=repo_root,
            repo_name=repo_name,
            config=ReportBuilderConfig(
                governance_review_log=_resolve_optional_path(
                    getattr(args, "governance_review_log", None)
                ),
                external_finding_log=_resolve_optional_path(
                    getattr(args, "external_finding_log", None)
                ),
                max_review_rows=int(getattr(args, "max_review_rows", 5000)),
                max_external_rows=int(getattr(args, "max_external_rows", 10000)),
                halstead_max_files=int(getattr(args, "halstead_max_files", 5000)),
                previous_snapshot=previous_snapshot,
            ),
        )

        artifact_paths = write_quality_feedback_artifact(
            snapshot, repo_root=repo_root
        )

        payload = snapshot.to_dict()
        payload["artifact_paths"] = artifact_paths

    except ValueError as exc:
        return render_governance_value_error(exc)

    return emit_governance_command_output(
        args,
        command="governance-quality-feedback",
        json_payload=payload,
        markdown_output=render_quality_feedback_markdown(snapshot),
        summary={
            "overall_score": snapshot.maintainability.overall,
            "grade": snapshot.maintainability.grade,
            "files_scanned": snapshot.halstead_summary.files_scanned,
            "fp_count": snapshot.false_positive_analysis.total_fp_count,
            "recommendation_count": len(snapshot.recommendations),
        },
    )


def _resolve_optional_path(raw: str | None) -> Path | None:
    """Resolve and expand a user-supplied path, or return None."""
    if not raw:
        return None
    return Path(raw).expanduser().resolve()
