"""Shared failure-evidence packet contracts and JUnit ingestion helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

from .value_coercion import coerce_int, coerce_string, coerce_string_items

FAILURE_PACKET_CONTRACT_ID = "FailurePacket"
FAILURE_PACKET_SCHEMA_VERSION = 1

_JUNIT_PATTERNS = ("*.junit.xml", "*junit*.xml", "TEST-*.xml")


@dataclass(frozen=True, slots=True)
class FailureCase:
    test_id: str
    test_name: str
    file_path: str = ""
    line: int = 0
    outcome: str = "failed"
    message: str = ""
    traceback_excerpt: str = ""
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FailurePacket:
    schema_version: int
    contract_id: str
    source: str
    runner: str
    generated_at: str
    status: str
    total_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    passed_tests: int
    primary_test_id: str = ""
    primary_message: str = ""
    cases: tuple[FailureCase, ...] = ()
    artifact_paths: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def failure_packet_from_mapping(payload: dict[str, object]) -> FailurePacket:
    raw_cases = payload.get("cases")
    cases: list[FailureCase] = []
    if isinstance(raw_cases, list):
        for raw_case in raw_cases:
            if not isinstance(raw_case, dict):
                continue
            cases.append(
                FailureCase(
                    test_id=coerce_string(raw_case.get("test_id")),
                    test_name=coerce_string(raw_case.get("test_name")),
                    file_path=coerce_string(raw_case.get("file_path")),
                    line=coerce_int(raw_case.get("line")),
                    outcome=coerce_string(raw_case.get("outcome")) or "failed",
                    message=coerce_string(raw_case.get("message")),
                    traceback_excerpt=coerce_string(raw_case.get("traceback_excerpt")),
                    stdout_excerpt=coerce_string(raw_case.get("stdout_excerpt")),
                    stderr_excerpt=coerce_string(raw_case.get("stderr_excerpt")),
                )
            )
    return FailurePacket(
        schema_version=coerce_int(payload.get("schema_version"))
        or FAILURE_PACKET_SCHEMA_VERSION,
        contract_id=coerce_string(payload.get("contract_id"))
        or FAILURE_PACKET_CONTRACT_ID,
        source=coerce_string(payload.get("source")),
        runner=coerce_string(payload.get("runner")) or "pytest",
        generated_at=coerce_string(payload.get("generated_at")),
        status=coerce_string(payload.get("status")) or "unknown",
        total_tests=coerce_int(payload.get("total_tests")),
        failed_tests=coerce_int(payload.get("failed_tests")),
        error_tests=coerce_int(payload.get("error_tests")),
        skipped_tests=coerce_int(payload.get("skipped_tests")),
        passed_tests=coerce_int(payload.get("passed_tests")),
        primary_test_id=coerce_string(payload.get("primary_test_id")),
        primary_message=coerce_string(payload.get("primary_message")),
        cases=tuple(cases),
        artifact_paths=coerce_string_items(payload.get("artifact_paths")),
        warnings=coerce_string_items(payload.get("warnings")),
    )


def collect_failure_packet(repo_root: Path) -> dict[str, object] | None:
    """Collect the latest available pytest failure packet from local artifacts.

    Coverage scope (reflected in the ``source`` field of the returned packet):

    - ``failure-bundle:<name>``: JUnit XML found under
      ``dev/reports/failures/**/source-artifacts/``.  This path is populated by
      the ``failure_triage.yml`` CI workflow (which downloads upstream artifacts
      via ``gh run download``) or by a manual ``gh run download`` into the same
      tree.  The bundle is CI-grade evidence.
    - ``workspace``: JUnit XML found at the repo root from a local ``pytest
      --junitxml`` run.  This is development-grade evidence only.

    CI artifacts uploaded by ``tooling_control_plane.yml`` are NOT automatically
    available locally.  To ingest CI failure evidence on a developer machine,
    download the artifacts into ``dev/reports/failures/`` first.
    """
    artifact_paths, source = _discover_junit_artifacts(repo_root)
    if not artifact_paths:
        return None
    packet = build_failure_packet(artifact_paths, source=source)
    return packet.to_dict()


def build_failure_packet(
    junit_paths: Iterable[Path],
    *,
    source: str,
) -> FailurePacket:
    """Aggregate one or more JUnit XML files into a shared failure packet."""
    cases: list[FailureCase] = []
    warnings: list[str] = []
    total_tests = 0
    failed_tests = 0
    error_tests = 0
    skipped_tests = 0
    artifact_list: list[str] = []

    for junit_path in sorted({path.resolve() for path in junit_paths}):
        artifact_list.append(str(junit_path))
        try:
            tree = ElementTree.parse(junit_path)
        except (ElementTree.ParseError, OSError) as exc:
            warnings.append(f"{junit_path}: {exc}")
            continue
        root = tree.getroot()
        for suite in _iter_test_suites(root):
            total_tests += _int_attr(suite, "tests")
            failed_tests += _int_attr(suite, "failures")
            error_tests += _int_attr(suite, "errors")
            skipped_tests += _int_attr(suite, "skipped")
            suite_out = _child_text(suite, "system-out")
            suite_err = _child_text(suite, "system-err")
            for testcase in suite.findall("testcase"):
                case = _failure_case_from_testcase(
                    testcase,
                    suite_stdout=suite_out,
                    suite_stderr=suite_err,
                )
                if case is not None:
                    cases.append(case)

    passed_tests = max(0, total_tests - failed_tests - error_tests - skipped_tests)
    primary = cases[0] if cases else None
    status = "failed" if (failed_tests or error_tests or cases) else "passed"
    return FailurePacket(
        schema_version=FAILURE_PACKET_SCHEMA_VERSION,
        contract_id=FAILURE_PACKET_CONTRACT_ID,
        source=source,
        runner="pytest",
        generated_at=datetime.now(timezone.utc).isoformat(),
        status=status,
        total_tests=total_tests,
        failed_tests=failed_tests,
        error_tests=error_tests,
        skipped_tests=skipped_tests,
        passed_tests=passed_tests,
        primary_test_id=primary.test_id if primary is not None else "",
        primary_message=primary.message if primary is not None else "",
        cases=tuple(cases),
        artifact_paths=tuple(artifact_list),
        warnings=tuple(warnings),
    )


def _discover_junit_artifacts(repo_root: Path) -> tuple[list[Path], str]:
    """Discover JUnit XML, preferring CI failure bundles over workspace files."""
    latest_bundle = _latest_failure_bundle(repo_root)
    if latest_bundle is not None:
        bundle_paths = _find_junit_paths(latest_bundle)
        if bundle_paths:
            return bundle_paths, f"failure-bundle:{latest_bundle.name}"
    workspace_paths = _find_junit_paths(repo_root)
    if workspace_paths:
        return workspace_paths, "workspace"
    return [], ""


def _latest_failure_bundle(repo_root: Path) -> Path | None:
    failure_root = repo_root / "dev" / "reports" / "failures"
    if not failure_root.is_dir():
        return None
    candidates = [
        path
        for path in failure_root.rglob("*")
        if path.is_dir() and (path / "source-artifacts").exists()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _find_junit_paths(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in _JUNIT_PATTERNS:
        for path in root.rglob(pattern):
            if path.is_file():
                paths.add(path)
    return sorted(paths)


def _iter_test_suites(root: ElementTree.Element) -> Iterable[ElementTree.Element]:
    if root.tag == "testsuite":
        yield root
        return
    if root.tag == "testsuites":
        yield from root.findall("testsuite")


def _failure_case_from_testcase(
    testcase: ElementTree.Element,
    *,
    suite_stdout: str,
    suite_stderr: str,
) -> FailureCase | None:
    failure = testcase.find("failure")
    error = testcase.find("error")
    node = failure if failure is not None else error
    if node is None:
        return None
    classname = testcase.attrib.get("classname", "").strip()
    name = testcase.attrib.get("name", "").strip()
    test_id = f"{classname}::{name}".strip(":")
    return FailureCase(
        test_id=test_id or name,
        test_name=name or test_id,
        file_path=testcase.attrib.get("file", "").strip(),
        line=_coerce_positive_int(testcase.attrib.get("line")),
        outcome="error" if error is not None else "failed",
        message=(node.attrib.get("message", "") or _first_line(node.text)).strip(),
        traceback_excerpt=_excerpt(node.text),
        stdout_excerpt=_excerpt(_child_text(testcase, "system-out") or suite_stdout),
        stderr_excerpt=_excerpt(_child_text(testcase, "system-err") or suite_stderr),
    )


def _excerpt(text: str | None, *, max_lines: int = 12, max_chars: int = 2000) -> str:
    normalized = (text or "").strip()
    if not normalized:
        return ""
    lines = normalized.splitlines()[:max_lines]
    collapsed = "\n".join(lines)
    return collapsed[:max_chars].rstrip()


def _child_text(node: ElementTree.Element, tag: str) -> str:
    child = node.find(tag)
    return (child.text or "").strip() if child is not None and child.text else ""


def _first_line(text: str | None) -> str:
    lines = (text or "").strip().splitlines()
    return lines[0].strip() if lines else ""


def _int_attr(node: ElementTree.Element, name: str) -> int:
    return _coerce_positive_int(node.attrib.get(name))


def _coerce_positive_int(raw: object) -> int:
    try:
        value = int(str(raw or "0"))
    except (TypeError, ValueError):
        return 0
    return value if value > 0 else 0
