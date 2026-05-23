"""Tests for the thin ``ground-truth-probe`` CLI surface.

Covers the 7 contract cases the live-state semantic TDD plan's
acceptance criteria require:

  1. pytest green                → verdict satisfied, exit 0
  2. pytest red                  → verdict unsatisfied, exit 0 (default)
  3. pytest red + --strict       → verdict unsatisfied, exit 1
  4. missing target              → verdict unsatisfied, exit 0 (default)
  5. missing target + --strict   → exit 1
  6. --skip-pytest               → verdict missing, exit 0
  7. pytest node id with ``::``  → path portion validated correctly

These tests construct synthetic pytest files under ``tmp_path`` (no
real GuardIR state is mutated) and exercise the command's `run()`
function directly. ``DEVCTL_NO_ARTIFACT_WRITES=1`` is set so the
real receipt ledger is never touched by tests.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import pytest

from dev.scripts.devctl.commands import ground_truth_probe


GREEN_TEST_BODY = """
def test_green():
    assert True
"""

RED_TEST_BODY = """
def test_red():
    assert False, "intentional red"
"""


def _make_args(
    *,
    pytest_target: str,
    record: bool = False,
    skip_pytest: bool = False,
    strict: bool = False,
    output_format: str = "json",
) -> argparse.Namespace:
    """Build an argparse.Namespace matching ground_truth_probe's parser."""
    return argparse.Namespace(
        pytest_target=pytest_target,
        skip_pytest=skip_pytest,
        record=record,
        strict=strict,
        base_ref="",
        head_ref="HEAD",
        probe_id="live_state_invariants_v1",
        format=output_format,
        output=None,
        pipe_command=None,
        pipe_args=None,
    )


@pytest.fixture(autouse=True)
def _suppress_real_artifact_writes(monkeypatch):
    """Tests must never write to dev/state/ or dev/reports/."""
    monkeypatch.setenv("DEVCTL_NO_ARTIFACT_WRITES", "1")


def _run_capture(args, capsys) -> tuple[int, dict[str, Any]]:
    """Invoke run() and return (exit_code, parsed JSON payload)."""
    exit_code = ground_truth_probe.run(args)
    out = capsys.readouterr().out
    payload = json.loads(out)
    return exit_code, payload


# ---------------------------------------------------------------------------
# 1. pytest green → verdict satisfied, exit 0
# ---------------------------------------------------------------------------

def test_pytest_green_yields_verdict_satisfied_exit_zero(tmp_path, capsys, monkeypatch):
    target_path = _create_synthetic_test(tmp_path, GREEN_TEST_BODY, "test_green.py")
    monkeypatch.chdir(target_path.parent)
    monkeypatch.setattr(
        ground_truth_probe, "_REPO_ROOT", target_path.parent.resolve()
    )
    args = _make_args(pytest_target="test_green.py")

    exit_code, payload = _run_capture(args, capsys)

    assert exit_code == 0, "default mode must exit 0 on pytest green"
    assert payload["receipt"]["verdict"] == "satisfied"
    assert payload["pytest_exit_code"] == 0


# ---------------------------------------------------------------------------
# 2. pytest red → verdict unsatisfied, exit 0 (default)
# ---------------------------------------------------------------------------

def test_pytest_red_default_mode_yields_unsatisfied_exit_zero(tmp_path, capsys, monkeypatch):
    target_path = _create_synthetic_test(tmp_path, RED_TEST_BODY, "test_red.py")
    monkeypatch.chdir(target_path.parent)
    monkeypatch.setattr(
        ground_truth_probe, "_REPO_ROOT", target_path.parent.resolve()
    )
    args = _make_args(pytest_target="test_red.py")

    exit_code, payload = _run_capture(args, capsys)

    assert exit_code == 0, "default mode must keep exit 0 so the receipt is read"
    assert payload["receipt"]["verdict"] == "unsatisfied"
    assert payload["pytest_exit_code"] != 0


# ---------------------------------------------------------------------------
# 3. pytest red + --strict → verdict unsatisfied, exit 1
# ---------------------------------------------------------------------------

def test_pytest_red_strict_mode_yields_unsatisfied_exit_one(tmp_path, capsys, monkeypatch):
    target_path = _create_synthetic_test(tmp_path, RED_TEST_BODY, "test_red_strict.py")
    monkeypatch.setattr(
        ground_truth_probe, "_REPO_ROOT", target_path.parent.resolve()
    )
    args = _make_args(pytest_target="test_red_strict.py", strict=True)

    exit_code, payload = _run_capture(args, capsys)

    assert exit_code == 1, "--strict must propagate pytest failure to exit 1"
    assert payload["receipt"]["verdict"] == "unsatisfied"


# ---------------------------------------------------------------------------
# 4. missing target → verdict unsatisfied, exit 0 (default)
# ---------------------------------------------------------------------------

def test_missing_target_default_mode_yields_unsatisfied_exit_zero(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(ground_truth_probe, "_REPO_ROOT", tmp_path.resolve())
    args = _make_args(pytest_target="does_not_exist.py")

    exit_code, payload = _run_capture(args, capsys)

    assert exit_code == 0
    assert payload["receipt"]["verdict"] == "unsatisfied"
    assert payload["pytest_exit_code"] == 127
    assert "not found" in payload["pytest_summary"]


# ---------------------------------------------------------------------------
# 5. missing target + --strict → exit 1
# ---------------------------------------------------------------------------

def test_missing_target_strict_mode_yields_exit_one(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(ground_truth_probe, "_REPO_ROOT", tmp_path.resolve())
    args = _make_args(pytest_target="missing_strict.py", strict=True)

    exit_code, payload = _run_capture(args, capsys)

    assert exit_code == 1
    assert payload["receipt"]["verdict"] == "unsatisfied"


# ---------------------------------------------------------------------------
# 6. --skip-pytest → verdict missing, exit 0
# ---------------------------------------------------------------------------

def test_skip_pytest_yields_verdict_missing_exit_zero(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(ground_truth_probe, "_REPO_ROOT", tmp_path.resolve())
    args = _make_args(
        pytest_target="ignored_when_skip.py",
        skip_pytest=True,
    )

    exit_code, payload = _run_capture(args, capsys)

    assert exit_code == 0
    assert payload["pytest_exit_code"] is None, (
        "--skip-pytest must NOT invoke pytest at all"
    )
    assert payload["receipt"]["verdict"] == "missing", (
        "--skip-pytest must produce a non-satisfying receipt that cannot "
        "unblock the final-response gate"
    )


# ---------------------------------------------------------------------------
# 7. pytest node id with :: validates path portion only
# ---------------------------------------------------------------------------

def test_pytest_node_id_target_validates_path_portion(tmp_path, capsys, monkeypatch):
    target_path = _create_synthetic_test(tmp_path, GREEN_TEST_BODY, "test_nodeid.py")
    monkeypatch.setattr(
        ground_truth_probe, "_REPO_ROOT", target_path.parent.resolve()
    )
    # Use the pytest node-id syntax: <path>::<test_name>
    args = _make_args(pytest_target="test_nodeid.py::test_green")

    exit_code, payload = _run_capture(args, capsys)

    assert exit_code == 0, (
        "Node-id syntax (path.py::test_name) must pass path validation; "
        "got exit_code=%s summary=%r" % (
            payload.get("pytest_exit_code"), payload.get("pytest_summary")
        )
    )
    assert payload["receipt"]["verdict"] == "satisfied"


# ---------------------------------------------------------------------------
# 8. Writer-correctness guard — empty suite must NOT be satisfied
# ---------------------------------------------------------------------------
#
# Critique surfaced 2026-05-23: "The invariant trusts its own ledger. If a
# buggy probe writes a wrong verdict, the invariant happily certifies a lie."
#
# The hidden assumption the writer relies on is: pytest exit 0 == real proof.
# But pytest exit 0 ALSO happens when 0 tests are collected (exit 5 in
# pytest>=6 normally, but conftest-shadowed or empty-suite runs can produce
# exit 0). An empty suite proves nothing; the writer MUST NOT emit
# verdict=satisfied for it.
#
# This test pins that contract.

def test_pytest_target_with_zero_tests_collected_must_not_be_satisfied(tmp_path, capsys, monkeypatch):
    # File exists but contains NO test_* functions → pytest collects 0 tests.
    target_path = _create_synthetic_test(
        tmp_path,
        "# No test functions in this file.\n_not_a_test = 1\n",
        "test_empty.py",
    )
    monkeypatch.setattr(
        ground_truth_probe, "_REPO_ROOT", target_path.parent.resolve()
    )
    args = _make_args(pytest_target="test_empty.py")

    exit_code, payload = _run_capture(args, capsys)
    verdict = payload["receipt"]["verdict"]
    pytest_exit = payload["pytest_exit_code"]

    # Either pytest's exit code is non-zero (collection failure → unsatisfied)
    # OR if pytest treats this as exit 0, the writer MUST still refuse to
    # call it satisfied. Both branches: verdict != "satisfied".
    assert verdict != "satisfied", (
        "WRITER-CORRECTNESS VIOLATED: empty pytest suite must NOT produce "
        "verdict=satisfied. An empty suite is not proof.\n"
        f"  pytest_exit_code: {pytest_exit}\n"
        f"  emitted verdict: {verdict!r}\n"
        f"  pytest_summary: {payload['pytest_summary']!r}\n"
        "  Fix: the writer must require at least 1 real PASS (not just "
        "exit code 0) before stamping verdict=satisfied."
    )


# ---------------------------------------------------------------------------
# 9. Writer-correctness guard — all-xfail suite must NOT be satisfied
# ---------------------------------------------------------------------------
#
# pytest exits 0 when the only outcomes are xfail/skipped. The writer must
# refuse to call that satisfied — xfail is debt acknowledgement, not proof.

def test_pytest_target_with_only_xfail_must_not_be_satisfied(tmp_path, capsys, monkeypatch):
    body = (
        "import pytest\n\n"
        "@pytest.mark.xfail(strict=True, reason='debt only')\n"
        "def test_only_xfail():\n"
        "    assert False\n"
    )
    target_path = _create_synthetic_test(tmp_path, body, "test_xfail_only.py")
    monkeypatch.setattr(
        ground_truth_probe, "_REPO_ROOT", target_path.parent.resolve()
    )
    args = _make_args(pytest_target="test_xfail_only.py")

    exit_code, payload = _run_capture(args, capsys)

    assert payload["pytest_exit_code"] == 0, (
        "Sanity check: pytest should return 0 for an all-xfail-strict suite."
    )
    assert payload["receipt"]["verdict"] != "satisfied", (
        "WRITER-CORRECTNESS VIOLATED: an all-xfail suite produced "
        f"verdict={payload['receipt']['verdict']!r}. xfail is debt "
        "acknowledgement, NOT proof. The writer must require at least "
        "one real pass."
    )
    # Verify the warning trail names the rule, not just the symptom.
    warnings_blob = " ".join(payload["receipt"]["warnings"])
    assert "no_real_passes" in warnings_blob or "xfail" in warnings_blob.lower(), (
        f"Expected warning to name the downgrade reason; got {payload['receipt']['warnings']!r}"
    )


# ---------------------------------------------------------------------------
# 10. Writer-correctness guard — real pass count of zero downgrades to unsatisfied
# ---------------------------------------------------------------------------
#
# Same rule, expressed via a suite with all-skipped tests. exit 0, but
# no real passes → unsatisfied.

def test_pytest_target_with_only_skipped_must_not_be_satisfied(tmp_path, capsys, monkeypatch):
    body = (
        "import pytest\n\n"
        "@pytest.mark.skip(reason='intentionally skipped')\n"
        "def test_skipped():\n"
        "    assert True\n"
    )
    target_path = _create_synthetic_test(tmp_path, body, "test_skip_only.py")
    monkeypatch.setattr(
        ground_truth_probe, "_REPO_ROOT", target_path.parent.resolve()
    )
    args = _make_args(pytest_target="test_skip_only.py")

    exit_code, payload = _run_capture(args, capsys)

    assert payload["pytest_exit_code"] == 0
    assert payload["receipt"]["verdict"] != "satisfied", (
        "WRITER-CORRECTNESS VIOLATED: an all-skipped suite produced "
        f"verdict={payload['receipt']['verdict']!r}. Skipped tests "
        "execute zero real assertions. The writer must reject this."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_synthetic_test(tmp_path: Path, body: str, filename: str) -> Path:
    """Write a tiny pytest file and an empty conftest into tmp_path."""
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    test_file = tmp_path / filename
    test_file.write_text(body, encoding="utf-8")
    return test_file
