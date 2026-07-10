#!/usr/bin/env python3
"""Fail when `/develop` orchestration signals lack closure instructions."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_REQUIRED_SIGNAL_FIELDS = (
    "source_surface",
    "severity",
    "recommended_action",
    "closure_check_command",
)


def build_report(
    *,
    report_override: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return a typed report for `/develop` orchestration signal closure."""
    payload = report_override if report_override is not None else _develop_report()
    signals = _orchestration_signals(payload)
    violations = _signal_violations(signals)
    return {
        "command": "check_orchestration_recommendation_closure",
        "timestamp": utc_timestamp(),
        "ok": len(violations) == 0,
        "signal_count": len(signals),
        "required_signal_fields": _REQUIRED_SIGNAL_FIELDS,
        "violations": violations,
    }


def _develop_report() -> Mapping[str, object]:
    from dev.scripts.devctl.commands.development.report import (
        build_report as build_develop_report,
    )

    args = SimpleNamespace(
        action_flag="status",
        action="status",
        actor="auto",
        fleet="default",
        max_cycles=1,
        max_workers=0,
        dry_run=False,
        drain_packets=False,
    )
    report = build_develop_report(args)
    payload = report.to_dict()
    return payload if isinstance(payload, Mapping) else {}


def _orchestration_signals(
    payload: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    orchestration = payload.get("orchestration")
    if not isinstance(orchestration, Mapping):
        return ()
    signals = orchestration.get("signals")
    if not isinstance(signals, Sequence) or isinstance(signals, (str, bytes)):
        return ()
    return tuple(signal for signal in signals if isinstance(signal, Mapping))


def _signal_violations(
    signals: tuple[Mapping[str, object], ...],
) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for signal in signals:
        signal_id = _signal_id(signal)
        missing = tuple(
            field for field in _REQUIRED_SIGNAL_FIELDS if not _text(signal.get(field))
        )
        if missing:
            violations.append(
                {
                    "signal_id": signal_id,
                    "reason": "missing_required_signal_fields",
                    "missing_fields": missing,
                }
            )
        if _text(signal.get("recommended_action")) and not _text(
            signal.get("closure_check_command")
        ):
            violations.append(
                {
                    "signal_id": signal_id,
                    "reason": "recommendation_without_closure_check",
                }
            )
    return violations


def _signal_id(signal: Mapping[str, object]) -> str:
    source = _text(signal.get("source")) or "source"
    signal_id = _text(signal.get("signal_id")) or "signal"
    return f"{source}:{signal_id}"


def _text(value: object) -> str:
    return str(value or "").strip()


def _render_md(report: Mapping[str, object]) -> str:
    lines = ["# check_orchestration_recommendation_closure", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- signal_count: {report.get('signal_count')}")
    lines.append(
        "- required_signal_fields: "
        + ", ".join(str(item) for item in report.get("required_signal_fields", ()))
    )
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        lines.append(f"- violations: {len(violations)}")
        if violations:
            _append_violation_lines(lines, violations)
    return "\n".join(lines)


def _append_violation_lines(lines: list[str], violations: Sequence[object]) -> None:
    lines.extend(("", "## Violations", ""))
    for violation in violations:
        if not isinstance(violation, Mapping):
            continue
        lines.append(f"- {violation.get('signal_id')}: {violation.get('reason')}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        report = build_report()
    except Exception as exc:  # broad-except: allow reason=guard entrypoints must emit structured reports instead of tracebacks fallback=typed runtime error
        return emit_runtime_error(
            "check_orchestration_recommendation_closure",
            args.format,
            str(exc),
        )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
