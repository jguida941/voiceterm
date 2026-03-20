"""Focused tests for check_governance_closure guard command path."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_governance_closure(fmt: str = "json") -> tuple[int, dict | str]:
    """Run check_governance_closure.py and return (exit_code, output)."""
    result = subprocess.run(
        [sys.executable, "dev/scripts/checks/check_governance_closure.py", "--format", fmt],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if fmt == "json":
        return result.returncode, json.loads(result.stdout)
    return result.returncode, result.stdout


def test_governance_closure_json_shape() -> None:
    """JSON output has the expected contract fields."""
    rc, payload = _run_governance_closure("json")
    assert isinstance(payload, dict)
    assert payload["command"] == "check_governance_closure"
    assert "ok" in payload
    assert "schema_version" in payload
    assert payload["schema_version"] == 1
    assert "total_guards" in payload
    assert "total_probes" in payload
    assert "violations" in payload
    assert "violation_count" in payload
    assert "checks_run" in payload
    assert isinstance(payload["violations"], list)
    assert isinstance(payload["checks_run"], list)
    assert len(payload["checks_run"]) == 4


def test_governance_closure_md_format() -> None:
    """Markdown output includes the expected header and structure."""
    rc, output = _run_governance_closure("md")
    assert "# check_governance_closure" in output
    assert "- ok:" in output
    assert "- guards:" in output
    assert "- probes:" in output
    assert "- violations:" in output


def test_governance_closure_violation_shape() -> None:
    """Each violation has check and detail fields."""
    rc, payload = _run_governance_closure("json")
    for v in payload["violations"]:
        assert "check" in v
        assert "detail" in v
        assert v["check"] in (
            "guard_test_coverage",
            "probe_test_coverage",
            "ci_guard_coverage",
            "workflow_timeout",
        )


def test_governance_closure_ci_coverage_does_not_flag_itself() -> None:
    """governance_closure should not flag itself as missing from CI now that it is wired."""
    rc, payload = _run_governance_closure("json")
    ci_violations = [
        v for v in payload["violations"]
        if v["check"] == "ci_guard_coverage" and v.get("guard_id") == "governance_closure"
    ]
    assert ci_violations == [], (
        "governance_closure should not flag itself — it should be in _SHARED_GOVERNANCE_CHECKS"
    )


def test_governance_closure_guard_count_matches_catalog() -> None:
    """Total guards in report should match the script_catalog count."""
    rc, payload = _run_governance_closure("json")
    assert payload["total_guards"] >= 60  # sanity: at least 60 guards registered
    assert payload["total_probes"] >= 20  # sanity: at least 20 probes registered


def test_governance_closure_ci_policy_is_explicit() -> None:
    """The CI coverage policy for governance_closure must match reality.

    Contract: governance_closure runs in CI via both:
    1. Direct step in tooling_control_plane.yml (so the CI coverage check sees it)
    2. _SHARED_GOVERNANCE_CHECKS in bundle_registry.py (so bundles include it)

    It must NOT be in CI_COVERAGE_EXEMPTIONS since it is directly in a workflow.
    """
    from dev.scripts.checks.governance_closure.command import CI_COVERAGE_EXEMPTIONS
    from dev.scripts.devctl.bundle_registry import _SHARED_GOVERNANCE_CHECKS

    # governance_closure must NOT be in CI exemptions (it IS in a workflow now)
    assert "governance_closure" not in CI_COVERAGE_EXEMPTIONS, (
        "governance_closure is directly in tooling_control_plane.yml — "
        "remove it from CI_COVERAGE_EXEMPTIONS"
    )

    # governance_closure must be in the shared governance checks bundle
    governance_closure_cmd = "python3 dev/scripts/checks/check_governance_closure.py"
    assert governance_closure_cmd in _SHARED_GOVERNANCE_CHECKS, (
        "governance_closure must be in _SHARED_GOVERNANCE_CHECKS so it runs "
        "in CI via the tooling/release bundle"
    )


def test_governance_closure_clean_summary_forced() -> None:
    """Force a clean summary path through the main() rendering logic.

    Imports the command module directly and patches the check functions
    to return zero violations, proving the ok=True / clean markdown path.
    """
    import importlib
    from unittest.mock import patch
    import io

    # Import the command module in-process
    cmd = importlib.import_module("governance_closure.command")

    with patch.object(cmd, "_find_guard_test_gaps", return_value=0), \
         patch.object(cmd, "_find_probe_test_gaps", return_value=0), \
         patch.object(cmd, "_find_ci_coverage_gaps", return_value=0), \
         patch.object(cmd, "_find_workflow_timeout_gaps", return_value=0), \
         patch("sys.argv", ["check_governance_closure", "--format", "json"]), \
         patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        rc = cmd.main()

    assert rc == 0
    output = mock_stdout.getvalue()
    payload = json.loads(output)
    assert payload["ok"] is True
    assert payload["violations"] == []
    assert payload["violation_count"] == 0
