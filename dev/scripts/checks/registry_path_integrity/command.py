#!/usr/bin/env python3
"""Guard that script catalog and quality-policy entries point at real files."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path

_BOOT_ROOT = str(Path(__file__).resolve().parents[4])
if _BOOT_ROOT not in sys.path:
    sys.path.insert(0, _BOOT_ROOT)

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - package-style fallback for tests
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

from dev.scripts.devctl.governance.script_catalog_registry import (
    CHECK_SCRIPT_RELATIVE_PATHS,
    PROBE_SCRIPT_RELATIVE_PATHS,
)
from dev.scripts.devctl.quality_policy.defaults import (
    DEFAULT_AI_GUARD_SPECS,
    DEFAULT_REVIEW_PROBE_SPECS,
)

_TOP_LEVEL_PROBE_EXEMPTIONS = {
    "probe_bootstrap": "shared probe bootstrap compatibility shim",
    "probe_path_filters": "shared path-filter helper for probes",
    "probe_report_render": "shared probe-report rendering helper",
}


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    check_paths: Mapping[str, str] | None = None,
    probe_paths: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Return registry/file-system drift for checks and probes."""
    checks = dict(check_paths or CHECK_SCRIPT_RELATIVE_PATHS)
    probes = dict(probe_paths or PROBE_SCRIPT_RELATIVE_PATHS)
    violations: list[dict[str, str]] = []
    violations.extend(_missing_registered_paths(repo_root, "check", checks))
    violations.extend(_missing_registered_paths(repo_root, "probe", probes))
    violations.extend(_missing_quality_policy_refs("check", checks))
    violations.extend(_missing_quality_policy_refs("probe", probes))
    violations.extend(_unregistered_top_level_checks(repo_root, checks))
    violations.extend(_unregistered_top_level_probes(repo_root, probes))
    return {
        "command": "check_registry_path_integrity",
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "registered_checks": len(checks),
        "registered_probes": len(probes),
        "violations": violations,
    }


def _missing_registered_paths(
    repo_root: Path,
    kind: str,
    paths: Mapping[str, str],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for script_id, relative in sorted(paths.items()):
        if not (repo_root / relative).is_file():
            violations.append(
                {
                    "check": "registered_path_exists",
                    "kind": kind,
                    "script_id": script_id,
                    "path": relative,
                    "detail": f"Registered {kind} path does not exist: {relative}",
                }
            )
    return violations


def _missing_quality_policy_refs(
    kind: str,
    paths: Mapping[str, str],
) -> list[dict[str, str]]:
    specs = DEFAULT_AI_GUARD_SPECS if kind == "check" else DEFAULT_REVIEW_PROBE_SPECS
    violations: list[dict[str, str]] = []
    for spec in specs:
        if spec.script_id not in paths:
            violations.append(
                {
                    "check": "quality_policy_script_registered",
                    "kind": kind,
                    "script_id": spec.script_id,
                    "path": "",
                    "detail": (
                        f"Quality policy references unregistered {kind}: "
                        f"{spec.script_id}"
                    ),
                }
            )
    return violations


def _unregistered_top_level_checks(
    repo_root: Path,
    check_paths: Mapping[str, str],
) -> list[dict[str, str]]:
    checks_dir = repo_root / "dev/scripts/checks"
    registered_ids = set(check_paths)
    violations: list[dict[str, str]] = []
    for path in sorted(checks_dir.glob("check_*.py")):
        script_id = path.stem.removeprefix("check_")
        if script_id not in registered_ids:
            violations.append(
                _unregistered_entrypoint_violation("check", script_id, path, repo_root)
            )
    return violations


def _unregistered_top_level_probes(
    repo_root: Path,
    probe_paths: Mapping[str, str],
) -> list[dict[str, str]]:
    checks_dir = repo_root / "dev/scripts/checks"
    registered_ids = set(probe_paths)
    violations: list[dict[str, str]] = []
    for path in sorted(checks_dir.glob("probe_*.py")):
        script_id = path.stem
        if script_id in _TOP_LEVEL_PROBE_EXEMPTIONS:
            continue
        if script_id not in registered_ids:
            violations.append(
                _unregistered_entrypoint_violation("probe", script_id, path, repo_root)
            )
    return violations


def _unregistered_entrypoint_violation(
    kind: str,
    script_id: str,
    path: Path,
    repo_root: Path,
) -> dict[str, str]:
    relative = path.relative_to(repo_root).as_posix()
    return {
        "check": "top_level_entrypoint_registered",
        "kind": kind,
        "script_id": script_id,
        "path": relative,
        "detail": f"Top-level {kind} entrypoint is not registered: {relative}",
    }


def _render_md(report: Mapping[str, object]) -> str:
    lines = ["# check_registry_path_integrity", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- registered_checks: {report['registered_checks']}")
    lines.append(f"- registered_probes: {report['registered_probes']}")
    violations = report.get("violations")
    violations = violations if isinstance(violations, list) else []
    lines.append(f"- violations: {len(violations)}")
    if violations:
        lines.append("")
        lines.append("## Violations")
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                "- "
                + str(violation.get("script_id") or "unknown")
                + ": "
                + str(violation.get("detail") or "")
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check script catalog and quality policy path integrity."
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
