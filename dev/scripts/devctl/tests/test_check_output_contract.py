"""Tests for the typed CheckResult / ViolationRecord output contract."""

from __future__ import annotations

import json

from dev.scripts.devctl.runtime.check_result_models import (
    CHECK_RESULT_CONTRACT_ID,
    CHECK_RESULT_SCHEMA_VERSION,
    CheckResult,
    ViolationRecord,
    build_check_result,
    render_check_result_md,
    render_check_result_text,
)


def _make_step(
    name: str,
    returncode: int = 0,
    *,
    skipped: bool = False,
    error: str = "",
    failure_output: str = "",
    duration_s: float = 1.0,
) -> dict:
    step: dict = {
        "name": name,
        "cmd": ["test", name],
        "cwd": "/repo",
        "returncode": returncode,
        "duration_s": duration_s,
        "skipped": skipped,
    }
    if error:
        step["error"] = error
    if failure_output:
        step["failure_output"] = failure_output
    return step


# -------------------------------------------------------
# ViolationRecord
# -------------------------------------------------------


def test_violation_record_to_dict_minimal() -> None:
    vr = ViolationRecord(step_name="fmt", exit_code=1, summary="bad format")
    payload = vr.to_dict()
    assert payload["step_name"] == "fmt"
    assert payload["exit_code"] == 1
    assert payload["summary"] == "bad format"
    assert "error" not in payload
    assert "failure_output" not in payload


def test_violation_record_to_dict_with_details() -> None:
    vr = ViolationRecord(
        step_name="clippy",
        exit_code=2,
        summary="lint failure",
        error="clippy error",
        failure_output="warning: unused variable",
    )
    payload = vr.to_dict()
    assert payload["error"] == "clippy error"
    assert payload["failure_output"] == "warning: unused variable"


# -------------------------------------------------------
# CheckResult
# -------------------------------------------------------


def test_check_result_to_dict_round_trip() -> None:
    result = build_check_result(
        steps=[_make_step("fmt"), _make_step("clippy", 1, error="lint error")],
        timestamp="2026-04-04T00:00:00Z",
    )
    payload = result.to_dict()
    assert payload["schema_version"] == CHECK_RESULT_SCHEMA_VERSION
    assert payload["contract_id"] == CHECK_RESULT_CONTRACT_ID
    assert payload["success"] is False
    assert payload["total"] == 2
    assert payload["passed"] == 1
    assert payload["failed"] == 1
    assert payload["skipped"] == 0
    assert len(payload["violations"]) == 1
    assert payload["violations"][0]["step_name"] == "clippy"
    # Verify JSON-serializable
    json.dumps(payload)


def test_check_result_all_pass() -> None:
    result = build_check_result(
        steps=[_make_step("fmt"), _make_step("test")],
        timestamp="2026-04-04T00:00:00Z",
    )
    assert result.success is True
    assert result.failed == 0
    assert result.passed == 2
    assert result.violations == ()


def test_check_result_skipped_steps() -> None:
    result = build_check_result(
        steps=[
            _make_step("fmt"),
            _make_step("clippy", skipped=True),
        ],
        timestamp="2026-04-04T00:00:00Z",
    )
    assert result.skipped == 1
    assert result.passed == 1
    assert result.total == 2


def test_check_result_empty_steps() -> None:
    result = build_check_result(steps=[], timestamp="2026-04-04T00:00:00Z")
    assert result.success is True
    assert result.total == 0


# -------------------------------------------------------
# Enriched steps carry status + violation_summary
# -------------------------------------------------------


def test_enriched_steps_carry_status() -> None:
    result = build_check_result(
        steps=[
            _make_step("fmt"),
            _make_step("clippy", 1, error="lint"),
            _make_step("test", skipped=True),
        ],
        timestamp="2026-04-04T00:00:00Z",
    )
    statuses = [s["status"] for s in result.steps]
    assert statuses == ["PASS", "FAIL", "SKIP"]


def test_enriched_steps_violation_summary_present_on_fail() -> None:
    result = build_check_result(
        steps=[_make_step("clippy", 1, error="lint err")],
        timestamp="2026-04-04T00:00:00Z",
    )
    assert result.steps[0]["violation_summary"] == "lint err"


def test_enriched_steps_violation_summary_empty_on_pass() -> None:
    result = build_check_result(
        steps=[_make_step("fmt")],
        timestamp="2026-04-04T00:00:00Z",
    )
    assert result.steps[0]["violation_summary"] == ""


# -------------------------------------------------------
# Text renderer
# -------------------------------------------------------


def test_render_text_empty() -> None:
    result = build_check_result(steps=[], timestamp="2026-04-04T00:00:00Z")
    assert render_check_result_text(result) == "no check steps ran"


def test_render_text_includes_failure_detail() -> None:
    result = build_check_result(
        steps=[
            _make_step("fmt"),
            _make_step("clippy", 1, error="bad lint"),
        ],
        timestamp="2026-04-04T00:00:00Z",
    )
    text = render_check_result_text(result)
    assert "1/2 passed" in text
    assert "1 failed" in text
    assert "PASS" in text
    assert "FAIL" in text
    assert "bad lint" in text


# -------------------------------------------------------
# Markdown renderer
# -------------------------------------------------------


def test_render_md_table_header() -> None:
    result = build_check_result(
        steps=[_make_step("fmt")],
        timestamp="2026-04-04T00:00:00Z",
    )
    md = render_check_result_md(result)
    assert "| Step | Status |" in md
    assert "| fmt |" in md


def test_render_md_failure_output_section() -> None:
    result = build_check_result(
        steps=[_make_step("clippy", 1, failure_output="warning: unused")],
        timestamp="2026-04-04T00:00:00Z",
    )
    md = render_check_result_md(result)
    assert "## Failure Output" in md
    assert "warning: unused" in md


# -------------------------------------------------------
# Violation summary extraction edge cases
# -------------------------------------------------------


def test_violation_summary_from_failure_output_last_line() -> None:
    result = build_check_result(
        steps=[
            _make_step(
                "test",
                1,
                failure_output="line1\nline2\nactual error",
            ),
        ],
        timestamp="2026-04-04T00:00:00Z",
    )
    assert result.violations[0].summary == "actual error"


def test_violation_summary_fallback_exit_code() -> None:
    result = build_check_result(
        steps=[_make_step("test", 42)],
        timestamp="2026-04-04T00:00:00Z",
    )
    assert result.violations[0].summary == "exit 42"


def test_violation_summary_truncation() -> None:
    long_error = "x" * 200
    result = build_check_result(
        steps=[_make_step("test", 1, error=long_error)],
        timestamp="2026-04-04T00:00:00Z",
    )
    assert len(result.violations[0].summary) == 120
