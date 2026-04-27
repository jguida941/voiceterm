#!/usr/bin/env python3
"""Detect typed enum members that are declared but never consumed by decisions."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path

from .models import EnumConnectivityReport
from .scanner import DEFAULT_SCAN_ROOTS, scan_enum_connectivity


def build_report(
    *,
    repo_root: Path,
    scan_roots: Iterable[str] = DEFAULT_SCAN_ROOTS,
    fail_on_disconnected: bool = False,
    include_tests: bool = False,
) -> EnumConnectivityReport:
    """Build a warning-first enum connectivity report."""
    roots = tuple(scan_roots)
    members, consumers = scan_enum_connectivity(
        repo_root=repo_root,
        scan_roots=roots,
        include_tests=include_tests,
    )
    enum_count = len({member.enum_name for member in members})
    connected = {consumer.member_key for consumer in consumers}
    disconnected = tuple(member for member in members if member.key not in connected)
    blocking_failure = fail_on_disconnected and bool(disconnected)
    return EnumConnectivityReport(
        ok=not blocking_failure,
        mode="blocking" if fail_on_disconnected else "warning_only",
        enum_count=enum_count,
        member_count=len(members),
        connected_count=len(
            {member.key for member in members if member.key in connected}
        ),
        disconnected_members=disconnected,
        consumers=consumers,
        scan_roots=roots,
    )


def render_md(report: EnumConnectivityReport) -> str:
    status = "OK" if report.ok else "FAIL"
    if report.mode == "warning_only" and report.disconnected_count:
        status = "WARN"
    lines = [
        "# check_typed_enum_connectivity",
        "",
        f"Status: {status}",
        f"Mode: {report.mode}",
        f"Enum classes scanned: {report.enum_count}",
        (
            "Members: "
            f"{report.member_count} total, {report.connected_count} connected, "
            f"{report.disconnected_count} disconnected"
        ),
        "",
    ]
    if not report.disconnected_members:
        lines.append(
            "All discovered string enum members have at least one decision consumer."
        )
        return "\n".join(lines)

    lines.extend(
        [
            "## Disconnected enum members",
            "",
            "| enum | member | value | definition |",
            "|---|---|---|---|",
        ]
    )
    for member in report.disconnected_members[:50]:
        lines.append(
            "| "
            f"{member.enum_name} | {member.member_name} | `{member.value}` | "
            f"{member.path}:{member.line} |"
        )
    if report.disconnected_count > 50:
        lines.append("")
        lines.append(
            f"... {report.disconnected_count - 50} additional disconnected members omitted."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    checks_dir = Path(__file__).resolve().parent.parent
    if str(checks_dir) not in sys.path:
        sys.path.insert(0, str(checks_dir))

    from check_bootstrap import REPO_ROOT, emit_runtime_error

    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--fail-on-disconnected",
        action="store_true",
        help="Hard-fail when any enum member has no decision consumer.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Count test-only enum references as consumers.",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(
            repo_root=REPO_ROOT,
            fail_on_disconnected=bool(args.fail_on_disconnected),
            include_tests=bool(args.include_tests),
        )
    except (ImportError, RuntimeError, TypeError, ValueError) as exc:
        return emit_runtime_error(
            "check_typed_enum_connectivity",
            args.format,
            str(exc),
        )

    output = (
        json.dumps(report.to_dict(), indent=2)
        if args.format == "json"
        else render_md(report)
    )
    print(output)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
