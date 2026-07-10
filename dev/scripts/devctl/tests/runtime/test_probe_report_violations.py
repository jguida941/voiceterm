"""Tests for the probe-report -> ViolationRecord adapter.

These tests lock the field-by-field mapping from an enriched probe-report
hint into a ``ViolationRecord`` so downstream consumers can render probe
findings through the shared ``CheckResult`` / ``ViolationRecord`` renderer
without relying on probe-report's own markdown/terminal output. The shape
of an enriched hint is the one produced by
``dev.scripts.checks.probe_report.contracts.enrich_probe_hint_contract``.
"""

from __future__ import annotations

from typing import Any

from dev.scripts.devctl.runtime.check_result_models import ViolationRecord
from dev.scripts.devctl.runtime.probe_report_violations import (
    probe_report_to_violations,
)


def _enriched_hint(**overrides: Any) -> dict[str, Any]:
    """Build a minimal enriched probe hint with sane defaults for testing."""
    base: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": "Finding",
        "finding_id": "probe:test@x:0",
        "signal_type": "probe",
        "check_id": "probe_magic_numbers",
        "rule_id": "probe_magic_numbers",
        "rule_version": "1",
        "repo_name": "codex-voice",
        "repo_path": "",
        "file_path": "dev/scripts/devctl/example.py",
        "symbol": "compute_threshold",
        "line": 42,
        "end_line": 0,
        "severity": "medium",
        "risk_type": "magic_number",
        "review_lens": "maintainability",
        "ai_instruction": (
            "Replace the literal 3600 with a named constant so the unit is "
            "visible at the call site.\nAvoid re-introducing the bare literal."
        ),
        "signals": (),
        "source_command": "probe-report",
        "source_artifact": "probe-report:risk_hints",
    }
    base.update(overrides)
    return base


def test_empty_report_returns_empty_tuple() -> None:
    """A report with no risk_hints key yields an empty tuple."""
    assert probe_report_to_violations({}) == ()


def test_empty_risk_hints_list_returns_empty_tuple() -> None:
    """An explicit empty risk_hints list yields an empty tuple."""
    assert probe_report_to_violations({"risk_hints": []}) == ()


def test_non_list_risk_hints_returns_empty_tuple() -> None:
    """A malformed risk_hints payload (not a list) fails closed to empty."""
    assert probe_report_to_violations({"risk_hints": "bogus"}) == ()


def test_non_dict_hint_entries_are_skipped() -> None:
    """List entries that are not dict-like are silently skipped."""
    report = {"risk_hints": [None, 42, "bogus", _enriched_hint()]}
    result = probe_report_to_violations(report)
    assert len(result) == 1
    assert result[0].step_name == "probe_magic_numbers"


def test_enriched_hint_maps_every_violation_field() -> None:
    """Every ViolationRecord field is populated from the matching hint key."""
    report = {"risk_hints": [_enriched_hint()]}
    (violation,) = probe_report_to_violations(report)

    assert isinstance(violation, ViolationRecord)
    assert violation.step_name == "probe_magic_numbers"
    assert violation.exit_code == 0
    assert violation.summary.startswith("Replace the literal 3600")
    assert len(violation.summary) <= 120
    assert violation.error == ""
    assert violation.failure_output == ""
    assert violation.file_path == "dev/scripts/devctl/example.py"
    assert violation.line == 42
    assert violation.policy == "maintainability"
    assert "named constant" in violation.fix
    assert violation.fix.count("\n") >= 1
    assert violation.source == "probe_magic_numbers"
    assert violation.severity == "medium"


def test_missing_file_and_line_default_to_empty_values() -> None:
    """A hint without file_path or line produces safe zero/empty defaults."""
    hint = _enriched_hint(file_path="", line=0)
    (violation,) = probe_report_to_violations({"risk_hints": [hint]})
    assert violation.file_path == ""
    assert violation.line == 0


def test_missing_ai_instruction_falls_back_to_risk_type_label() -> None:
    """When guidance is empty, summary falls back to check_id + risk_type."""
    hint = _enriched_hint(ai_instruction="", risk_type="clone_density")
    (violation,) = probe_report_to_violations({"risk_hints": [hint]})
    assert "probe_magic_numbers" in violation.summary
    assert "clone_density" in violation.summary
    assert violation.fix == ""


def test_missing_ai_instruction_and_risk_type_uses_review_lens() -> None:
    """When risk_type is absent too, summary falls back to review_lens."""
    hint = _enriched_hint(ai_instruction="", risk_type="", review_lens="concurrency")
    (violation,) = probe_report_to_violations({"risk_hints": [hint]})
    assert "concurrency" in violation.summary


def test_long_ai_instruction_first_line_is_truncated_to_120_chars() -> None:
    """The summary never exceeds 120 chars, matching the check-path bound."""
    long_first_line = "x" * 500
    hint = _enriched_hint(ai_instruction=f"{long_first_line}\nrest")
    (violation,) = probe_report_to_violations({"risk_hints": [hint]})
    assert len(violation.summary) == 120


def test_multiple_hints_preserve_order() -> None:
    """Hint order in risk_hints is preserved in the output tuple."""
    report = {
        "risk_hints": [
            _enriched_hint(check_id="probe_a", line=1),
            _enriched_hint(check_id="probe_b", line=2),
            _enriched_hint(check_id="probe_c", line=3),
        ]
    }
    violations = probe_report_to_violations(report)
    assert tuple(v.step_name for v in violations) == ("probe_a", "probe_b", "probe_c")
    assert tuple(v.line for v in violations) == (1, 2, 3)


def test_string_line_coerces_to_int() -> None:
    """A hint whose line arrives as a string (JSON round-trip) still maps."""
    hint = _enriched_hint(line="42")
    (violation,) = probe_report_to_violations({"risk_hints": [hint]})
    assert violation.line == 42


def test_non_integer_line_coerces_to_zero() -> None:
    """A malformed line value (non-int) is coerced safely to 0."""
    hint = _enriched_hint(line="not-a-number")
    (violation,) = probe_report_to_violations({"risk_hints": [hint]})
    assert violation.line == 0


def test_violation_record_is_hashable_and_frozen() -> None:
    """The adapter returns frozen dataclass instances that can be set members.

    ``ViolationRecord`` is declared frozen+slots in ``check_result_models``,
    so adapter output must be usable in set/dict keys without mutation risk.
    """
    (violation,) = probe_report_to_violations({"risk_hints": [_enriched_hint()]})
    bucket = {violation}
    assert violation in bucket
