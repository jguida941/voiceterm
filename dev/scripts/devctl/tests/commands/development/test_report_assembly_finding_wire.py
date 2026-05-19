"""SLICE-Y tests: report_assembly wires FindingBacklog -> select_next_slice preemption.

Per codex orchestrator directive rev_pkt_4495 / rev_pkt_4511 (Role-flip cycle 2 SLICE-Y):
wire ranked critical/high open findings from the canonical FindingBacklog source
into ``select_next_slice`` so ``develop next --actor agent`` surfaces
bug-priority preemption instead of silently selecting ordinary plan rows.

Composes with SLICE-X helper (commit 0ea70c7d); does NOT create a parallel bug queue.
"""

from __future__ import annotations

from dev.scripts.devctl.commands.development.report_assembly import (
    _ranked_findings_for_develop_next,
)
from dev.scripts.devctl.triage.findings_priority_models import RankedFinding


def test_ranked_findings_for_develop_next_returns_tuple_of_ranked_findings() -> None:
    """Wire returns a tuple of RankedFinding rows projected from FindingBacklog."""
    result = _ranked_findings_for_develop_next()

    assert isinstance(result, tuple)
    for finding in result:
        assert isinstance(finding, RankedFinding)


def test_ranked_findings_for_develop_next_orders_by_severity() -> None:
    """Critical findings rank ahead of high/medium/low when source has them."""
    findings = _ranked_findings_for_develop_next()
    severity_order = ("critical", "high", "medium", "low")
    last_seen_rank = -1
    for finding in findings:
        current_rank = severity_order.index(finding.severity) if finding.severity in severity_order else 99
        assert current_rank >= last_seen_rank, (
            f"Findings should be ordered by severity rank "
            f"but found {finding.severity} after rank {last_seen_rank}"
        )
        last_seen_rank = current_rank


def test_ranked_findings_for_develop_next_marks_open_resolution_state() -> None:
    """All projected findings come from FindingBacklog.open_findings so resolution_state=open."""
    findings = _ranked_findings_for_develop_next()
    for finding in findings:
        assert finding.resolution_state == "open"
        assert finding.status == "confirmed_issue"
