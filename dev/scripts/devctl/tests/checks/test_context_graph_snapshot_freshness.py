from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.context_graph_snapshot_freshness.command import (
    evaluate_context_graph_snapshot_freshness,
)


def test_context_graph_snapshot_freshness_reports_missing_snapshot(
    tmp_path: Path,
) -> None:
    report = evaluate_context_graph_snapshot_freshness(repo_root=tmp_path)

    assert report.ok is True
    assert report.report_only is True
    assert report.would_fail is True
    assert report.snapshot_count == 0
    assert report.drift is True
    assert "no ContextGraphSnapshot" in report.detail

