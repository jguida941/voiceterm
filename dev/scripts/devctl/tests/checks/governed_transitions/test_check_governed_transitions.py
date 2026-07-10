"""Tests for the governed transition verifier."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.governed_transitions.command import build_report
from dev.scripts.devctl.context_graph.models import (
    EDGE_KIND_PRODUCES_STATE,
    EDGE_KIND_REQUIRES_STATE,
    EDGE_KIND_TRANSITIONS_TO,
)
from dev.scripts.devctl.runtime.governed_transitions import TransitionContract


def test_transition_report_accepts_graph_walkable_metadata(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        transitions=(
            TransitionContract(
                transition_id="test.lifecycle.approve",
                requires=("Request:pending",),
                produces=("Lifecycle:active",),
                emits=("ApprovalReceipt",),
                graph_path=("Request", "ApprovalReceipt", "Lifecycle"),
                owner_module="tests.transitions",
                function_name="approve",
            ),
        ),
        manifest_modules=("tests.transitions",),
    )

    assert report.ok
    assert report.transition_count == 1
    assert report.checked_path_count == 2
    assert report.failure_count == 0
    assert report.edge_kind_counts[EDGE_KIND_REQUIRES_STATE] == 1
    assert report.edge_kind_counts[EDGE_KIND_PRODUCES_STATE] == 1
    assert report.edge_kind_counts[EDGE_KIND_TRANSITIONS_TO] == 2


def test_transition_report_rejects_missing_declared_graph_path(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        transitions=(
            TransitionContract(
                transition_id="test.lifecycle.missing_path",
                requires=("Request:pending",),
                produces=("Lifecycle:active",),
                emits=("ApprovalReceipt",),
                graph_path=(),
                owner_module="tests.transitions",
                function_name="approve",
            ),
        ),
        manifest_modules=("tests.transitions",),
    )

    assert not report.ok
    assert report.failure_count == 1
    assert report.path_checks[0].check_kind == "metadata_shape"
    assert "graph_path" in report.path_checks[0].reason


def test_real_manifest_has_walkable_bypass_transitions() -> None:
    report = build_report(repo_root=Path.cwd())

    assert report.ok
    assert report.transition_count >= 3
    assert "dev.scripts.devctl.runtime.bypass_lifecycle_evaluation" in (
        report.manifest_modules
    )
