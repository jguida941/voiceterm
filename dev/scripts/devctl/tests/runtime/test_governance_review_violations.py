"""Tests for the recent-governance-review -> ViolationRecord adapter.

These tests lock the field-by-field mapping from one adjudicated
governance-review row into a ``ViolationRecord`` so downstream
consumers can render the **recent governance-review window** through
the shared ``CheckResult`` / ``ViolationRecord`` renderer. The row
shape is the one produced by
``dev.scripts.devctl.governance_review_log.build_governance_review_row``
from ``dev.scripts.devctl.governance_review_models.GovernanceReviewInput``.

The adapter is explicitly scoped to the **recent** window emitted by
``build_governance_review_report``, not to the full set of live
governance findings. Rows older than the recent window are not in the
input payload and are never expected in the output. The default verdict
filter is ``("confirmed_issue",)``: only currently tracked findings
inside the recent window surface as violations, and
``fixed`` / ``waived`` / ``deferred`` / ``false_positive`` / ``unknown``
rows are skipped.
"""

from __future__ import annotations

from typing import Any

from dev.scripts.devctl.runtime.check_result_models import ViolationRecord
from dev.scripts.devctl.runtime.governance_review_violations import (
    DEFAULT_INCLUDE_VERDICTS,
    governance_review_recent_to_violations,
)


def _row(**overrides: Any) -> dict[str, Any]:
    """Build a minimal adjudicated governance-review row with sane defaults."""
    base: dict[str, Any] = {
        "finding_id": "probe:test@x:0",
        "timestamp_utc": "2026-04-06T06:00:00Z",
        "schema_version": 2,
        "contract_id": "FindingReview",
        "repo_name": "codex-voice",
        "repo_path": "",
        "signal_type": "probe",
        "check_id": "probe_magic_numbers",
        "verdict": "confirmed_issue",
        "file_path": "dev/scripts/devctl/example.py",
        "finding_class": "local_defect",
        "recurrence_risk": "localized",
        "prevention_surface": "probe",
        "symbol": "compute_threshold",
        "line": 42,
        "severity": "medium",
        "risk_type": "magic_number",
        "source_command": "probe-report",
        "scan_mode": "working-tree",
        "notes": (
            "Replace the literal 3600 with a named constant so the unit is "
            "visible at the call site.\nTracked under probe_magic_numbers."
        ),
    }
    base.update(overrides)
    return base


def _report(*rows: dict[str, Any]) -> dict[str, Any]:
    """Wrap rows into a governance-review recent-window report payload."""
    return {
        "command": "governance-review",
        "generated_at_utc": "2026-04-06T06:00:00Z",
        "log_path": "dev/reports/governance_review/log.jsonl",
        "stats": {},
        "recent_findings": list(rows),
    }


def test_default_include_set_is_confirmed_issue_only() -> None:
    """The module-level default filter is documented as confirmed_issue only."""
    assert DEFAULT_INCLUDE_VERDICTS == ("confirmed_issue",)


def test_empty_report_returns_empty_tuple() -> None:
    """A report with no recent_findings key yields an empty tuple."""
    assert governance_review_recent_to_violations({}) == ()


def test_empty_recent_findings_list_returns_empty_tuple() -> None:
    """An explicit empty recent_findings list yields an empty tuple."""
    assert governance_review_recent_to_violations(_report()) == ()


def test_non_list_recent_findings_returns_empty_tuple() -> None:
    """A malformed recent_findings payload (not a list) fails closed to empty."""
    assert governance_review_recent_to_violations({"recent_findings": "bogus"}) == ()


def test_non_dict_row_entries_are_skipped() -> None:
    """List entries that are not dict-like are silently skipped."""
    report = {"recent_findings": [None, 42, "bogus", _row()]}
    result = governance_review_recent_to_violations(report)
    assert len(result) == 1
    assert result[0].step_name == "probe_magic_numbers"


def test_confirmed_issue_row_maps_every_violation_field() -> None:
    """Every ViolationRecord field is populated from the matching row key."""
    (violation,) = governance_review_recent_to_violations(_report(_row()))

    assert isinstance(violation, ViolationRecord)
    assert violation.step_name == "probe_magic_numbers"
    assert violation.exit_code == 0
    assert violation.summary.startswith("Replace the literal 3600")
    assert len(violation.summary) <= 120
    assert violation.error == ""
    assert violation.failure_output == ""
    assert violation.file_path == "dev/scripts/devctl/example.py"
    assert violation.line == 42
    assert violation.policy == "probe"
    assert "named constant" in violation.fix
    assert violation.fix.count("\n") >= 1
    assert violation.source == "probe-report"
    assert violation.severity == "medium"


def test_non_live_verdicts_are_filtered_out_by_default() -> None:
    """``fixed`` / ``waived`` / ``deferred`` / ``false_positive`` rows are skipped.

    The default include set is ``("confirmed_issue",)``, so any row with
    a resolved verdict must not surface as a current violation in any
    shared-renderer consumer.
    """
    report = _report(
        _row(verdict="fixed", check_id="probe_fixed"),
        _row(verdict="waived", check_id="probe_waived"),
        _row(verdict="deferred", check_id="probe_deferred"),
        _row(verdict="false_positive", check_id="probe_fp"),
        _row(verdict="unknown", check_id="probe_unknown"),
        _row(verdict="confirmed_issue", check_id="probe_live"),
    )
    violations = governance_review_recent_to_violations(report)
    assert len(violations) == 1
    assert violations[0].step_name == "probe_live"


def test_adapter_only_reads_recent_window_from_report() -> None:
    """The adapter reads ``recent_findings`` and nothing outside it.

    Regression lock for F3: ``build_governance_review_report`` slices
    ``recent_findings`` to a bounded window. Rows that exist in the
    underlying review log but NOT in the report's recent window must
    never appear in the adapter output. This test synthesizes a report
    whose ``recent_findings`` is only a subset of a hypothetical
    broader log and asserts the adapter respects the report payload
    exactly instead of reaching into other keys.
    """
    report: dict[str, Any] = {
        "command": "governance-review",
        "recent_findings": [
            _row(check_id="probe_recent_a"),
            _row(check_id="probe_recent_b"),
        ],
        # These keys exist on the report envelope but are NOT the
        # source of truth for this adapter; the adapter must ignore
        # them and read only ``recent_findings``.
        "stats": {
            "by_check_id": [
                {"bucket": "probe_older_unwindowed"},
            ],
        },
        "log_path": "dev/reports/governance_review/log.jsonl",
    }
    violations = governance_review_recent_to_violations(report)
    assert tuple(v.step_name for v in violations) == (
        "probe_recent_a",
        "probe_recent_b",
    )


def test_adapter_scales_with_upstream_recent_limit_beyond_default() -> None:
    """Regression lock for the recent-only semantic across the 10-row boundary.

    ``build_governance_review_report(recent_limit=...)`` defaults to 10 rows
    but callers may pass a larger value. The adapter must process every
    row the caller placed in ``recent_findings`` without internally
    re-trimming to 10, so a widened upstream window flows through to
    downstream shared-renderer consumers.

    This test synthesizes a report with 12 ``confirmed_issue`` rows plus
    1 ``fixed`` row (13 total, > default recent_limit=10) and asserts:

    1. All 12 ``confirmed_issue`` rows appear in the output, preserving
       order. A naive implementation that re-sliced to the first 10
       would silently drop rows 11-12.
    2. The ``fixed`` row is filtered out by the default verdict set,
       independent of window size.
    3. Row order is preserved exactly, proving the adapter is not
       re-sorting or deduplicating the recent window.
    """
    rows = [
        _row(check_id=f"probe_confirmed_{i:02d}", line=i)
        for i in range(1, 13)  # 12 confirmed_issue rows
    ]
    rows.append(_row(check_id="probe_fixed", verdict="fixed", line=99))

    violations = governance_review_recent_to_violations(_report(*rows))

    assert len(violations) == 12
    assert tuple(v.step_name for v in violations) == tuple(
        f"probe_confirmed_{i:02d}" for i in range(1, 13)
    )
    assert tuple(v.line for v in violations) == tuple(range(1, 13))
    assert "probe_fixed" not in {v.step_name for v in violations}


def test_custom_include_verdicts_broadens_the_filter() -> None:
    """Passing a custom include set lets callers see historical verdicts.

    Still only within the recent window: a broader include tuple does
    not reach older rows outside ``recent_findings``, only relaxes the
    verdict filter on the rows that are already in the window.
    """
    report = _report(
        _row(verdict="fixed", check_id="probe_fixed"),
        _row(verdict="confirmed_issue", check_id="probe_live"),
    )
    violations = governance_review_recent_to_violations(
        report, include_verdicts=("confirmed_issue", "fixed"),
    )
    assert tuple(v.step_name for v in violations) == ("probe_fixed", "probe_live")


def test_missing_notes_falls_back_to_finding_class_label() -> None:
    """When notes are empty, summary falls back to check_id + finding_class."""
    (violation,) = governance_review_recent_to_violations(
        _report(_row(notes="", finding_class="rule_quality")),
    )
    assert "probe_magic_numbers" in violation.summary
    assert "rule_quality" in violation.summary
    assert violation.fix == ""


def test_missing_notes_and_finding_class_uses_signal_type() -> None:
    """When both notes and finding_class are empty, fall back to signal_type."""
    (violation,) = governance_review_recent_to_violations(
        _report(_row(notes="", finding_class="", signal_type="guard")),
    )
    assert "guard" in violation.summary


def test_missing_source_command_falls_back_to_signal_type() -> None:
    """When source_command is absent, ``source`` uses signal_type."""
    (violation,) = governance_review_recent_to_violations(
        _report(_row(source_command="", signal_type="guard")),
    )
    assert violation.source == "guard"


def test_missing_source_command_and_signal_type_uses_literal_fallback() -> None:
    """When both source_command and signal_type are empty, fall back to literal."""
    (violation,) = governance_review_recent_to_violations(
        _report(_row(source_command="", signal_type="")),
    )
    assert violation.source == "governance-review"


def test_missing_file_and_line_default_to_empty_values() -> None:
    """A row without file_path or line produces safe zero/empty defaults."""
    (violation,) = governance_review_recent_to_violations(
        _report(_row(file_path="", line=0)),
    )
    assert violation.file_path == ""
    assert violation.line == 0


def test_long_notes_first_line_is_truncated_to_120_chars() -> None:
    """The summary never exceeds 120 chars, matching the check-path bound."""
    long_first_line = "x" * 500
    (violation,) = governance_review_recent_to_violations(
        _report(_row(notes=f"{long_first_line}\nrest")),
    )
    assert len(violation.summary) == 120


def test_multiple_confirmed_issue_rows_preserve_order() -> None:
    """Row order in recent_findings is preserved in the output tuple."""
    report = _report(
        _row(check_id="probe_a", line=1),
        _row(check_id="probe_b", line=2),
        _row(check_id="probe_c", line=3),
    )
    violations = governance_review_recent_to_violations(report)
    assert tuple(v.step_name for v in violations) == ("probe_a", "probe_b", "probe_c")
    assert tuple(v.line for v in violations) == (1, 2, 3)


def test_string_line_coerces_to_int() -> None:
    """A row whose line arrives as a string (JSON round-trip) still maps."""
    (violation,) = governance_review_recent_to_violations(
        _report(_row(line="42")),
    )
    assert violation.line == 42


def test_non_integer_line_coerces_to_zero() -> None:
    """A malformed line value (non-int) is coerced safely to 0."""
    (violation,) = governance_review_recent_to_violations(
        _report(_row(line="not-a-number")),
    )
    assert violation.line == 0


def test_violation_record_is_hashable_and_frozen() -> None:
    """The adapter returns frozen dataclass instances that can be set members."""
    (violation,) = governance_review_recent_to_violations(_report(_row()))
    bucket = {violation}
    assert violation in bucket
