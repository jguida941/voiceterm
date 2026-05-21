"""SLICE-X tests: bug-priority preemption in `select_next_slice`.

Per codex orchestrator directive rev_pkt_4494 / rev_pkt_4506 (Role-flip cycle 2):
unresolved critical/high `confirmed_issue` findings preempt ordinary leaf-row
selection in `develop next`. Tests verify the helper composes with existing
FindingBacklog + RankedFinding contracts and does NOT weaken VCS/edit gates.
"""

from __future__ import annotations

from dev.scripts.devctl.commands.development.next_slice import select_next_slice
from dev.scripts.devctl.runtime.master_plan_contract import PlanRow
from dev.scripts.devctl.triage.findings_priority_models import RankedFinding


def _row(*, row_id: str, target_ref: str = "", status: str = "queued") -> PlanRow:
    return PlanRow(
        row_id=row_id,
        title=f"row {row_id}",
        status=status,
        sdlc_stage="impl",
        target_ref=target_ref,
    )


def _finding(
    *,
    qid: str = "Q-1",
    severity: str = "critical",
    resolution_state: str = "open",
    primary_file: str = "",
) -> RankedFinding:
    return RankedFinding(
        rank=1,
        qid=qid,
        heading=f"finding {qid}",
        severity=severity,
        severity_rank=0 if severity == "critical" else 1,
        status="confirmed_issue",
        summary=f"open {severity} finding {qid}",
        resolution_state=resolution_state,
        primary_file=primary_file,
        file_refs=(primary_file,) if primary_file else (),
        matched_file_refs=(primary_file,) if primary_file else (),
        max_fan_out=5,
        fan_out_by_file=((primary_file, 5),) if primary_file else (),
    )


def test_critical_finding_with_active_target_ref_preempts_leaf_row() -> None:
    """Open critical finding whose primary_file matches an active row's target_ref preempts that row's leaf-row fallback selection."""
    rows = (
        _row(row_id="MP-LINKED", target_ref="pkg/buggy.py", status="queued"),
        _row(row_id="MP-OTHER", target_ref="pkg/other.py", status="queued"),
    )
    findings = (_finding(severity="critical", primary_file="pkg/buggy.py"),)

    result = select_next_slice(rows, ranked_findings=findings)

    assert result.slice_id == "MP-LINKED"
    assert "preempts" in result.reason
    assert "critical" in result.reason


def test_high_finding_without_linkage_does_not_preempt_current_plan() -> None:
    """Open high finding with no plan-row linkage stays in backlog while a plan row is executable."""
    rows = (
        _row(row_id="MP-A", target_ref="pkg/a.py", status="queued"),
    )
    findings = (_finding(severity="high", primary_file="pkg/orphan.py"),)

    result = select_next_slice(rows, ranked_findings=findings)

    assert result.slice_id == "MP-A"
    assert result.status == "queued"
    assert result.target_ref == "pkg/a.py"
    assert "current-plan authority" in result.reason


def test_high_finding_without_linkage_can_surface_when_no_plan_row_exists() -> None:
    """Unlinked critical/high findings remain visible if no plan graph row can run."""
    findings = (_finding(severity="high", primary_file="pkg/orphan.py"),)

    result = select_next_slice((), ranked_findings=findings)

    assert result.slice_id == "bug-priority-preemption"
    assert result.status == "attention_required"
    assert result.target_ref == "pkg/orphan.py"
    assert "No active plan-row linkage" in result.reason


def test_finding_linkage_ignores_packet_binding_rows() -> None:
    """PKT-BIND rows are packet evidence, not executable finding targets."""
    rows = (
        _row(
            row_id="PKT-BIND-REV-PKT-1",
            target_ref="pkg/buggy.py",
            status="queued",
        ),
        _row(row_id="MP-CURRENT", target_ref="pkg/current.py", status="queued"),
    )
    findings = (_finding(severity="critical", primary_file="pkg/buggy.py"),)

    result = select_next_slice(rows, ranked_findings=findings)

    assert result.slice_id == "MP-CURRENT"
    assert "current-plan authority" in result.reason


def test_medium_finding_does_not_preempt() -> None:
    """Medium severity findings do NOT preempt; falls through to active leaf row."""
    rows = (
        _row(row_id="MP-NORMAL", target_ref="pkg/normal.py", status="queued"),
    )
    findings = (_finding(severity="medium", primary_file="pkg/normal.py"),)

    result = select_next_slice(rows, ranked_findings=findings)

    assert result.slice_id == "MP-NORMAL"
    assert "preempts" not in result.reason


def test_resolved_finding_does_not_preempt() -> None:
    """Resolved/closed findings do NOT preempt; falls through to active leaf row."""
    rows = (
        _row(row_id="MP-CONT", target_ref="pkg/cont.py", status="queued"),
    )
    findings = (
        _finding(
            severity="critical",
            resolution_state="resolved",
            primary_file="pkg/cont.py",
        ),
    )

    result = select_next_slice(rows, ranked_findings=findings)

    assert result.slice_id == "MP-CONT"
    assert "preempts" not in result.reason


def test_no_findings_argument_preserves_pre_slice_x_behavior() -> None:
    """Backward compat: omitting `ranked_findings` keeps original leaf-row selection unchanged."""
    rows = (
        _row(row_id="MP-LEGACY", target_ref="pkg/legacy.py", status="queued"),
    )

    result = select_next_slice(rows)

    assert result.slice_id == "MP-LEGACY"
    assert "current-plan authority" in result.reason
