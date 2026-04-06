"""Tests for the dashboard-side ViolationRecord adapter consumers.

These tests prove the MP-381 contract family is *consumed* end-to-end by
the dashboard data layer:

- ``violations_to_dashboard_cells`` flattens ViolationRecord-shaped dicts
  into the dashboard "cell" shape used by ``recent_violations`` lists.
- ``audit_recent_violations`` projects governance-review recent rows
  through the shared adapter into dashboard cells.
- ``probes_recent_violations`` projects probe-report risk hints through
  the shared adapter into dashboard cells.
- ``_build_audit_section`` and ``_build_probes_section`` populate the
  new ``recent_violations`` field unconditionally so renderers can read
  it without branching.

The test fixtures mirror the real artifact shape:
``recent_findings`` for governance-review, ``risk_hints`` for
probe-report, with the same field names the production adapters
already exercise.
"""

from __future__ import annotations

from typing import Any

from dev.scripts.devctl.commands.dashboard_data import (
    _build_audit_section,
    _build_probes_section,
)
from dev.scripts.devctl.commands.dashboard_violations import (
    MAX_DASHBOARD_VIOLATION_ROWS,
    audit_recent_violations,
    probes_recent_violations,
    violations_to_dashboard_cells,
)


# -------------------------------------------------------
# violations_to_dashboard_cells
# -------------------------------------------------------


def test_violations_to_dashboard_cells_empty_input_returns_empty_list() -> None:
    """No violations input must produce no cells (renderers iterate unconditionally)."""
    assert violations_to_dashboard_cells([]) == []
    assert violations_to_dashboard_cells(()) == []


def test_violations_to_dashboard_cells_minimal_record_maps_required_fields() -> None:
    """Required fields (step_name/summary) project into the cell required keys."""
    cells = violations_to_dashboard_cells([
        {"step_name": "fmt", "exit_code": 1, "summary": "bad format"},
    ])

    assert len(cells) == 1
    cell = cells[0]
    assert cell["check"] == "fmt"
    assert cell["status"] == "FAIL"
    assert cell["violation"] == "bad format"
    assert "file_path" not in cell
    assert "line" not in cell


def test_violations_to_dashboard_cells_full_record_preserves_optional_fields() -> None:
    """Optional fields (file/line/policy/fix/source/severity) round-trip when present."""
    cells = violations_to_dashboard_cells([
        {
            "step_name": "code_shape",
            "exit_code": 1,
            "summary": "function too long",
            "file_path": "dev/scripts/example.py",
            "line": 42,
            "policy": "function_length",
            "fix": "split into helpers",
            "source": "code_shape",
            "severity": "high",
        },
    ])

    cell = cells[0]
    assert cell["file_path"] == "dev/scripts/example.py"
    assert cell["line"] == "42"
    assert cell["policy"] == "function_length"
    assert cell["fix"] == "split into helpers"
    assert cell["source"] == "code_shape"
    assert cell["severity"] == "high"


def test_violations_to_dashboard_cells_prepends_location_when_missing() -> None:
    """A summary without an embedded location gets prefixed with ``file:line``."""
    cells = violations_to_dashboard_cells([
        {
            "step_name": "lint",
            "exit_code": 1,
            "summary": "trailing whitespace",
            "file_path": "src/foo.py",
            "line": 7,
        },
    ])
    assert cells[0]["violation"].startswith("src/foo.py:7")


def test_violations_to_dashboard_cells_does_not_double_prepend_location() -> None:
    """If the summary already mentions the location, it must not be re-added."""
    cells = violations_to_dashboard_cells([
        {
            "step_name": "lint",
            "exit_code": 1,
            "summary": "src/foo.py:7 trailing whitespace",
            "file_path": "src/foo.py",
            "line": 7,
        },
    ])
    assert cells[0]["violation"].count("src/foo.py:7") == 1


def test_violations_to_dashboard_cells_caps_at_max_dashboard_rows() -> None:
    """The cap keeps the dashboard snapshot compact regardless of source size."""
    records = [
        {"step_name": f"check-{i}", "exit_code": 1, "summary": f"violation {i}"}
        for i in range(MAX_DASHBOARD_VIOLATION_ROWS + 5)
    ]
    cells = violations_to_dashboard_cells(records)
    assert len(cells) == MAX_DASHBOARD_VIOLATION_ROWS


# -------------------------------------------------------
# audit_recent_violations
# -------------------------------------------------------


def _gov_data(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a minimal governance-review report with the given recent rows."""
    return {
        "stats": {
            "total_findings": len(rows),
            "fixed_count": 0,
            "open_finding_count": len(rows),
            "cleanup_rate_pct": 0.0,
        },
        "recent_findings": rows,
    }


def test_audit_recent_violations_empty_for_none_input() -> None:
    """A missing governance report must yield an empty list."""
    assert audit_recent_violations(None) == []


def test_audit_recent_violations_empty_when_no_recent_findings() -> None:
    """A report with no recent findings yields an empty list."""
    assert audit_recent_violations(_gov_data([])) == []


def test_audit_recent_violations_projects_confirmed_issue_rows() -> None:
    """Each ``confirmed_issue`` row in the recent window becomes one cell."""
    cells = audit_recent_violations(_gov_data([
        {
            "verdict": "confirmed_issue",
            "check_id": "probe_unwrap_chains",
            "file_path": "dev/scripts/example.py",
            "line": 41,
            "notes": "Replace .unwrap() chain with proper error propagation",
            "prevention_surface": "probe",
            "signal_type": "probe",
            "severity": "high",
        },
    ]))

    assert len(cells) == 1
    cell = cells[0]
    assert cell["check"] == "probe_unwrap_chains"
    assert cell["status"] == "FAIL"
    assert "Replace .unwrap()" in cell["violation"]
    assert cell["file_path"] == "dev/scripts/example.py"
    assert cell["line"] == "41"
    assert cell["policy"] == "probe"
    assert cell["severity"] == "high"


def test_audit_recent_violations_skips_non_confirmed_verdicts() -> None:
    """Fixed/false-positive/waived rows must NOT appear in the dashboard list."""
    cells = audit_recent_violations(_gov_data([
        {"verdict": "fixed", "check_id": "x", "notes": "n"},
        {"verdict": "false_positive", "check_id": "y", "notes": "n"},
        {"verdict": "waived", "check_id": "z", "notes": "n"},
    ]))
    assert cells == []


# -------------------------------------------------------
# probes_recent_violations
# -------------------------------------------------------


def _probe_data(hints: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a minimal probe-report aggregate with the given risk hints."""
    return {
        "summary": {
            "risk_hints": len(hints),
            "probe_count": 13,
            "files_scanned": 100,
            "hints_by_severity": {"high": 1, "medium": 0, "low": 0},
        },
        "risk_hints": hints,
    }


def test_probes_recent_violations_empty_for_none_input() -> None:
    """A missing probe report must yield an empty list."""
    assert probes_recent_violations(None) == []


def test_probes_recent_violations_empty_when_no_hints() -> None:
    """A report with no risk hints yields an empty list."""
    assert probes_recent_violations(_probe_data([])) == []


def test_probes_recent_violations_projects_each_hint() -> None:
    """Each risk hint becomes one dashboard cell with location and policy."""
    cells = probes_recent_violations(_probe_data([
        {
            "check_id": "probe_blank_line_frequency",
            "file_path": "dev/scripts/devctl/review_channel/prompt.py",
            "line": 12,
            "ai_instruction": (
                "Add blank lines between logical sections — separate setup "
                "from computation from output."
            ),
            "review_lens": "readability",
            "risk_type": "readability",
            "severity": "high",
        },
    ]))

    assert len(cells) == 1
    cell = cells[0]
    assert cell["check"] == "probe_blank_line_frequency"
    assert cell["status"] == "FAIL"
    assert "Add blank lines" in cell["violation"]
    assert cell["file_path"] == "dev/scripts/devctl/review_channel/prompt.py"
    assert cell["line"] == "12"
    assert cell["policy"] == "readability"
    assert cell["severity"] == "high"


# -------------------------------------------------------
# Section integration: _build_audit_section / _build_probes_section
# -------------------------------------------------------


def test_build_audit_section_includes_recent_violations_when_data_present() -> None:
    """The audit section must populate ``recent_violations`` from gov data."""
    section = _build_audit_section(_gov_data([
        {
            "verdict": "confirmed_issue",
            "check_id": "code_shape",
            "file_path": "dev/scripts/example.py",
            "line": 80,
            "notes": "function too long",
            "prevention_surface": "guard",
            "signal_type": "guard",
            "severity": "medium",
        },
    ]))

    assert "recent_violations" in section
    assert len(section["recent_violations"]) == 1
    assert section["recent_violations"][0]["check"] == "code_shape"
    # Existing fields still present (backward compat)
    assert section["total_findings"] == 1
    assert section["open_finding_count"] == 1


def test_build_audit_section_empty_recent_violations_when_no_gov_data() -> None:
    """Even with no gov_data, ``recent_violations`` must be present and empty."""
    section = _build_audit_section(None)
    assert section["recent_violations"] == []
    assert section["total_findings"] == "n/a"


def test_build_probes_section_includes_recent_violations_when_data_present() -> None:
    """The probes section must populate ``recent_violations`` from probe data."""
    section = _build_probes_section(_probe_data([
        {
            "check_id": "probe_unwrap_chains",
            "file_path": "src/foo.rs",
            "line": 100,
            "ai_instruction": "Replace unwrap with proper error handling",
            "review_lens": "safety",
            "severity": "high",
        },
    ]))

    assert "recent_violations" in section
    assert len(section["recent_violations"]) == 1
    assert section["recent_violations"][0]["check"] == "probe_unwrap_chains"
    # Existing fields still present (backward compat)
    assert section["risk_hints"] == 1
    assert section["high"] == 1


def test_build_probes_section_empty_recent_violations_when_no_probe_data() -> None:
    """Even with no probe_data, ``recent_violations`` must be present and empty."""
    section = _build_probes_section(None)
    assert section["recent_violations"] == []
    assert section["risk_hints"] == "n/a"
