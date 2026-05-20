#!/usr/bin/env python3
"""Fail when controller decisions project actions that contradict authority."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

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

from dev.scripts.devctl.runtime.control_decision_consistency import (  # noqa: E402
    evaluate_control_decision_consistency,
    extract_control_decisions,
)
from dev.scripts.devctl.review_channel.agent_loop_decision_projection import (  # noqa: E402
    attach_agent_loop_decision_projections,
)


def build_report(
    *,
    report_override: Mapping[str, object] | Sequence[object] | None = None,
    input_path: Path | None = None,
    stdin_text: str = "",
    allow_empty: bool = False,
) -> dict[str, object]:
    payload: object
    source_path = input_path
    if report_override is not None:
        payload = report_override
    elif input_path is not None:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    elif stdin_text.strip():
        payload = json.loads(stdin_text)
    elif (REPO_ROOT / "dev/reports/review_channel/state/latest.json").exists():
        source_path = REPO_ROOT / "dev/reports/review_channel/state/latest.json"
        payload = json.loads(source_path.read_text(encoding="utf-8"))
    else:
        payload = {}
    payload = _fresh_control_decision_payload(payload)
    decisions = extract_control_decisions(payload)
    report = evaluate_control_decision_consistency(
        decisions,
        source=str(source_path or "report_override"),
        allow_empty=allow_empty,
    ).to_dict()
    report["command"] = "check_control_decision_consistency"
    report["timestamp"] = utc_timestamp()
    return report


def _fresh_control_decision_payload(payload: object) -> object:
    if not isinstance(payload, Mapping):
        return payload
    if not isinstance(payload.get("agent_work_board"), Mapping):
        return payload
    return attach_agent_loop_decision_projections(payload)


def render_markdown(report: Mapping[str, object]) -> str:
    lines = ["# check_control_decision_consistency", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- decision_count: {report.get('decision_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        if violations:
            lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('source')}: {violation.get('reason')} "
                f"({violation.get('detail', '')})"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON report to inspect")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read a JSON report from stdin.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow no-subject reports for diagnostics only.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        stdin_text = sys.stdin.read() if args.stdin else ""
        report = build_report(
            input_path=args.input,
            stdin_text=stdin_text,
            allow_empty=args.allow_empty,
        )
    except Exception as exc:  # broad-except: guard entrypoints must emit structured reports instead of tracebacks fallback=typed runtime error
        return emit_runtime_error(
            "check_control_decision_consistency",
            args.format,
            str(exc),
        )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
