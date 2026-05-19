"""SLICE-Y tests: report_assembly wires FindingBacklog -> select_next_slice preemption.

Per codex orchestrator directive rev_pkt_4495 / rev_pkt_4511 (Role-flip cycle 2 SLICE-Y):
wire ranked critical/high open findings from the canonical FindingBacklog source
into ``select_next_slice`` so ``develop next --actor agent`` surfaces
bug-priority preemption instead of silently selecting ordinary plan rows.

Composes with SLICE-X helper (commit 0ea70c7d); does NOT create a parallel bug queue.
"""

from __future__ import annotations

import pytest

from dev.scripts.devctl.commands.development import report_assembly
from dev.scripts.devctl.commands.development.report_assembly import (
    _ranked_findings_for_develop_next,
)
from dev.scripts.devctl.triage.findings_priority_models import RankedFinding


def test_ranked_findings_for_develop_next_returns_tuple_of_ranked_findings() -> None:
    """Wire returns (ranked_findings_tuple, None) when source is available."""
    findings, blocker = _ranked_findings_for_develop_next()

    assert isinstance(findings, tuple)
    assert blocker is None
    for finding in findings:
        assert isinstance(finding, RankedFinding)


def test_ranked_findings_for_develop_next_orders_by_severity() -> None:
    """Critical findings rank ahead of high/medium/low when source has them."""
    findings, _blocker = _ranked_findings_for_develop_next()
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
    findings, _blocker = _ranked_findings_for_develop_next()
    for finding in findings:
        assert finding.resolution_state == "open"
        assert finding.status == "confirmed_issue"


def test_ranked_findings_for_develop_next_returns_typed_blocker_on_load_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SLICE-Y repair per rev_pkt_4513: fail-loud typed blocker when FindingBacklog source unavailable.

    Soft-fall to plan rows silently was the original bug; this test pins the typed-blocker
    behavior so develop next NEVER silently selects ordinary plan rows when finding source
    cannot be loaded.
    """

    def _raising_loader(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError("synthetic finding_reviews missing")

    monkeypatch.setattr(report_assembly, "load_finding_backlog", _raising_loader)

    findings, blocker = _ranked_findings_for_develop_next()

    assert findings == ()
    assert blocker is not None
    assert blocker.slice_id == "finding-source-stale-blocker"
    assert blocker.status == "attention_required"
    assert "FindingBacklog source unavailable" in blocker.reason
    # NOT silently selecting plan rows - that is the regression this test pins.
