"""Tests for shared failure packet contracts and JUnit ingestion."""

from __future__ import annotations

import tempfile
from pathlib import Path

from dev.scripts.devctl.runtime.failure_packet import (
    FAILURE_PACKET_CONTRACT_ID,
    build_failure_packet,
    collect_failure_packet,
)


_JUNIT_XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="3" failures="1" errors="0" skipped="1">
  <testcase classname="pkg.test_mod" name="test_ok" file="pkg/test_mod.py" line="3" />
  <testcase classname="pkg.test_mod" name="test_fail" file="pkg/test_mod.py" line="7">
    <failure message="assert 1 == 2">Traceback line 1
Traceback line 2</failure>
    <system-err>stderr tail</system-err>
  </testcase>
  <testcase classname="pkg.test_mod" name="test_skip" file="pkg/test_mod.py" line="12">
    <skipped />
  </testcase>
</testsuite>
"""


def test_build_failure_packet_parses_junit_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        junit_path = Path(tmp_dir) / "devctl-tests.junit.xml"
        junit_path.write_text(_JUNIT_XML, encoding="utf-8")

        packet = build_failure_packet([junit_path], source="workspace")

    assert packet.contract_id == FAILURE_PACKET_CONTRACT_ID
    assert packet.runner == "pytest"
    assert packet.total_tests == 3
    assert packet.failed_tests == 1
    assert packet.skipped_tests == 1
    assert packet.primary_test_id == "pkg.test_mod::test_fail"
    assert packet.primary_message == "assert 1 == 2"
    assert packet.cases[0].file_path == "pkg/test_mod.py"
    assert packet.cases[0].stderr_excerpt == "stderr tail"


def test_collect_failure_packet_prefers_latest_failure_bundle() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        older = root / "dev" / "reports" / "failures" / "tooling" / "run-1-attempt-1"
        newer = root / "dev" / "reports" / "failures" / "tooling" / "run-2-attempt-1"
        (older / "source-artifacts").mkdir(parents=True)
        (newer / "source-artifacts").mkdir(parents=True)
        (older / "source-artifacts" / "old.junit.xml").write_text(
            _JUNIT_XML.replace("assert 1 == 2", "old failure"),
            encoding="utf-8",
        )
        (newer / "source-artifacts" / "new.junit.xml").write_text(
            _JUNIT_XML.replace("assert 1 == 2", "new failure"),
            encoding="utf-8",
        )

        packet = collect_failure_packet(root)

    assert packet is not None
    assert packet["source"] == "failure-bundle:run-2-attempt-1"
    assert packet["primary_message"] == "new failure"
