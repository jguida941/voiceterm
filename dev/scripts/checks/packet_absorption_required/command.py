#!/usr/bin/env python3
"""Fail when actionable packets are acknowledged without absorption receipts."""

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

from dev.scripts.devctl.runtime.packet_absorption import (  # noqa: E402
    evaluate_packet_absorption_required,
)


def build_report(
    *,
    report_override: Mapping[str, object] | Sequence[object] | None = None,
    input_path: Path | None = None,
    stdin_text: str = "",
    allow_empty: bool = False,
    observation_without_ingestion_limit: int | None = 1,
) -> dict[str, object]:
    if report_override is not None:
        payload: object = report_override
    elif input_path is not None:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    elif stdin_text.strip():
        payload = json.loads(stdin_text)
    else:
        payload = _load_default_review_state_payload()
    report = evaluate_packet_absorption_required(
        payload,
        allow_empty=allow_empty,
        observation_without_ingestion_limit=observation_without_ingestion_limit,
    ).to_dict()
    report["command"] = "check_packet_absorption_required"
    report["timestamp"] = utc_timestamp()
    return report


def _load_default_review_state_payload() -> object:
    for relpath in (
        "dev/reports/review_channel/state/latest.json",
        "dev/reports/review_channel/projections/latest/review_state.json",
    ):
        path = REPO_ROOT / relpath
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, Mapping):
            return payload
    return {}


def render_markdown(report: Mapping[str, object]) -> str:
    lines = ["# check_packet_absorption_required", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- actionable_packet_count: {report.get('actionable_packet_count')}")
    lines.append(f"- absorption_receipt_count: {report.get('absorption_receipt_count')}")
    lines.append(
        "- semantic_ingestion_receipt_count: "
        f"{report.get('semantic_ingestion_receipt_count')}"
    )
    lines.append(
        "- body_observed_without_ingestion_count: "
        f"{report.get('body_observed_without_ingestion_count')}"
    )
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        if violations:
            lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('packet_id')}: {violation.get('reason')}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON review-state payload")
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
    parser.add_argument(
        "--observation-without-ingestion-limit",
        type=int,
        default=1,
        help=(
            "Fail with packet_observation_without_semantic_ingestion after this "
            "many observed actionable packets lack semantic ingestion."
        ),
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
            observation_without_ingestion_limit=(
                args.observation_without_ingestion_limit
            ),
        )
    except Exception as exc:  # broad-except: guard entrypoints must emit structured reports instead of tracebacks fallback=typed runtime error
        return emit_runtime_error(
            "check_packet_absorption_required",
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
