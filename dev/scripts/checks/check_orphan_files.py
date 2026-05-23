#!/usr/bin/env python3
"""Fail when new guard/test files are born without runtime wiring."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, run_format_check, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        run_format_check,
        utc_timestamp,
    )

try:
    from feature_completion_support import FeatureCompletionSupport as _Support
except ModuleNotFoundError:
    from dev.scripts.checks.feature_completion_support import (
        FeatureCompletionSupport as _Support,
    )

# Backward-compatibility module-level aliases for the dedup-extracted helpers.
# Existing tests and external callers reach into ``guard._bundled_check_paths`` etc.;
# these aliases keep the surface stable while the bodies live in
# ``feature_completion_support.py``.
_registered_check_paths = _Support.registered_check_paths
_bundled_check_paths = _Support.bundled_check_paths
_quality_check_paths = _Support.quality_check_paths
_router_mapped_paths = _Support.router_mapped_paths
_git_status_output = _Support.git_status_output


if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

COMMAND = "check_orphan_files"
CONTRACT_ID = "OrphanFileProductionGuard"


@dataclass(frozen=True, slots=True)
class OrphanFileViolation:
    path: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    git_status_output: str | None = None,
    registered_check_paths: frozenset[str] | None = None,
    bundled_check_paths: frozenset[str] | None = None,
    quality_check_paths: frozenset[str] | None = None,
    router_mapped_paths: frozenset[str] | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    new_files = _new_files(
        git_status_output if git_status_output is not None else _Support.git_status_output(warnings)
    )
    registered = (
        registered_check_paths
        if registered_check_paths is not None
        else _Support.registered_check_paths()
    )
    bundled = bundled_check_paths if bundled_check_paths is not None else _Support.bundled_check_paths()
    quality = (
        quality_check_paths if quality_check_paths is not None else _Support.quality_check_paths()
    )
    router_mapped = (
        router_mapped_paths if router_mapped_paths is not None else _Support.router_mapped_paths()
    )

    violations: list[OrphanFileViolation] = []
    for path in new_files:
        if _is_check_entrypoint(path):
            violations.extend(
                _check_guard_file(
                    path=path,
                    registered=registered,
                    bundled=bundled,
                    quality=quality,
                    router_mapped=router_mapped,
                )
            )
        elif _is_devctl_test(path) and path not in router_mapped:
            violations.append(
                OrphanFileViolation(
                    path=path,
                    reason="orphan_test_not_mapped",
                    detail="New devctl test file is not mapped in router_python_tests.",
                    remediation=(
                        "Add a path mapping in "
                        "dev/scripts/devctl/commands/check/router_python_tests.py."
                    ),
                )
            )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "new_file_count": len(new_files),
        "new_files": list(new_files),
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def _check_guard_file(
    *,
    path: str,
    registered: frozenset[str],
    bundled: frozenset[str],
    quality: frozenset[str],
    router_mapped: frozenset[str],
) -> tuple[OrphanFileViolation, ...]:
    violations: list[OrphanFileViolation] = []
    if path not in registered:
        violations.append(
            OrphanFileViolation(
                path=path,
                reason="orphan_check_not_registered",
                detail="New check entrypoint is missing from script_catalog_registry.",
                remediation="Register the guard in script_catalog_registry.py.",
            )
        )
    if path not in bundled:
        violations.append(
            OrphanFileViolation(
                path=path,
                reason="orphan_check_not_bundled",
                detail="New check entrypoint is not reachable from any command bundle.",
                remediation="Add the guard to the appropriate bundle registry layer.",
            )
        )
    if path not in quality:
        violations.append(
            OrphanFileViolation(
                path=path,
                reason="orphan_check_not_quality_routed",
                detail="New check entrypoint has no QualityStepSpec.",
                remediation="Add a QualityStepSpec in quality_policy/defaults.py.",
            )
        )
    if path not in router_mapped:
        violations.append(
            OrphanFileViolation(
                path=path,
                reason="orphan_check_without_focused_test_mapping",
                detail="New check entrypoint has no focused router_python_tests mapping.",
                remediation="Map the guard to its focused test file in router_python_tests.py.",
            )
        )
    return tuple(violations)


def _new_files(status_output: str) -> tuple[str, ...]:
    files: list[str] = []
    for line in status_output.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        if status != "??" and "A" not in status:
            continue
        path = line[3:] if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip()
        if path:
            files.append(path)
    return tuple(files)


def _is_check_entrypoint(path: str) -> bool:
    name = Path(path).name
    return path.startswith("dev/scripts/checks/") and name.startswith("check_") and name.endswith(".py")


def _is_devctl_test(path: str) -> bool:
    name = Path(path).name
    return path.startswith("dev/scripts/devctl/tests/") and name.startswith("test_") and name.endswith(".py")


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- new_file_count: {report.get('new_file_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if isinstance(violation, Mapping):
                lines.append(
                    f"- {violation.get('path')}: {violation.get('reason')} "
                    f"({violation.get('detail')})"
                )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    return run_format_check(argv=argv, command=COMMAND, description=__doc__ or COMMAND, build_report=build_report, render_markdown=render_markdown)


if __name__ == "__main__":
    raise SystemExit(main())
