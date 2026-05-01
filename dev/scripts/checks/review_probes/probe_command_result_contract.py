#!/usr/bin/env python3
"""Review probe: flag devctl JSON commands without a common result envelope."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )
except ModuleNotFoundError:  # pragma: no cover - package-style fallback
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
    from dev.scripts.checks.probe_support.bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )


PROBE_NAME = "command_result_contract"
REVIEW_LENS = "runtime_command_contract"
REQUIRED_FIELDS = ("command", "ok", "exit_ok", "exit_code", "status", "errors")
DEFAULT_COMMAND_SPECS = (
    (
        "review-channel sync-status",
        (
            "python3",
            "dev/scripts/devctl.py",
            "review-channel",
            "--action",
            "sync-status",
            "--terminal",
            "none",
            "--format",
            "json",
            "--for-agent",
            "codex",
        ),
    ),
    (
        "path-audit",
        ("python3", "dev/scripts/devctl.py", "path-audit", "--format", "json"),
    ),
    (
        "review-channel operator-inbox",
        (
            "python3",
            "dev/scripts/devctl.py",
            "review-channel",
            "--action",
            "operator-inbox",
            "--terminal",
            "none",
            "--format",
            "json",
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class CommandJsonObservation:
    """Observed JSON output for one command-result contract sample."""

    label: str
    argv: tuple[str, ...]
    exit_code: int
    payload: object
    parse_error: str = ""
    stderr: str = ""


def main(argv: list[str] | None = None) -> int:
    parser = build_probe_parser(PROBE_NAME)
    parser.add_argument(
        "--skip-live",
        action="store_true",
        help="Only emit an empty report; intended for parser/import smoke tests.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    observations: list[CommandJsonObservation] = []
    if not args.skip_live:
        observations = collect_command_observations(REPO_ROOT)
    hints = command_result_contract_hints(observations)
    report = ProbeReport(
        command=PROBE_NAME,
        risk_hints=hints,
        files_scanned=len(observations),
        files_with_hints=len({hint.symbol for hint in hints}),
        mode="live-command-sample",
        since_ref=args.since_ref,
        head_ref=args.head_ref,
    )
    return emit_probe_report(report, output_format=args.format)


def collect_command_observations(
    repo_root: Path,
    *,
    command_specs: Sequence[tuple[str, Sequence[str]]] = DEFAULT_COMMAND_SPECS,
    timeout_seconds: int = 60,
) -> list[CommandJsonObservation]:
    """Run a bounded read-only command sample and parse JSON output."""
    observations: list[CommandJsonObservation] = []
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    for label, argv in command_specs:
        try:
            completed = subprocess.run(
                tuple(argv),
                cwd=repo_root,
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            observations.append(
                CommandJsonObservation(
                    label=label,
                    argv=tuple(argv),
                    exit_code=124 if isinstance(exc, subprocess.TimeoutExpired) else 127,
                    payload={},
                    parse_error=type(exc).__name__,
                    stderr=str(exc),
                )
            )
            continue

        payload, parse_error = _decode_json_object(completed.stdout)
        observations.append(
            CommandJsonObservation(
                label=label,
                argv=tuple(argv),
                exit_code=completed.returncode,
                payload=payload,
                parse_error=parse_error,
                stderr=completed.stderr.strip(),
            )
        )
    return observations


def command_result_contract_hints(
    observations: Sequence[CommandJsonObservation],
) -> list[RiskHint]:
    """Return risk hints for commands missing the shared JSON envelope."""
    hints: list[RiskHint] = []
    for observation in observations:
        signals = _contract_signals(observation)
        if not signals:
            continue
        hints.append(
            RiskHint(
                file="dev/scripts/devctl.py",
                symbol=observation.label,
                risk_type="devctl_command_result_contract_gap",
                severity="high",
                signals=signals,
                ai_instruction=(
                    "Normalize this command's JSON output through the shared "
                    "command-result envelope: command, ok, exit_ok, exit_code, "
                    "status, and errors. Operators and tandem agents should not "
                    "need command-specific parsing to decide whether a command "
                    "succeeded, failed, or returned partial advisory state."
                ),
                review_lens=REVIEW_LENS,
                attach_docs=[
                    "dev/scripts/README.md",
                    "dev/active/ai_governance_platform.md",
                ],
            )
        )
    return hints


def _contract_signals(observation: CommandJsonObservation) -> list[str]:
    payload = observation.payload
    signals: list[str] = []
    if observation.exit_code != 0:
        signals.append(f"process_exit_code={observation.exit_code}")
    if observation.parse_error:
        signals.append(f"json_parse_error={observation.parse_error}")
    if not isinstance(payload, dict):
        signals.append(f"json_payload_type={type(payload).__name__}")
        return signals

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        signals.append("missing_fields=" + ",".join(missing))

    wrong_types = _wrong_type_fields(payload)
    if wrong_types:
        signals.append("wrong_field_types=" + ",".join(wrong_types))
    return signals


def _wrong_type_fields(payload: dict[str, object]) -> list[str]:
    wrong: list[str] = []
    if "command" in payload and not isinstance(payload["command"], str):
        wrong.append("command")
    if "ok" in payload and not isinstance(payload["ok"], bool):
        wrong.append("ok")
    if "exit_ok" in payload and not isinstance(payload["exit_ok"], bool):
        wrong.append("exit_ok")
    if "exit_code" in payload and not _is_plain_int(payload["exit_code"]):
        wrong.append("exit_code")
    if "status" in payload and not isinstance(payload["status"], str):
        wrong.append("status")
    if "errors" in payload and not isinstance(payload["errors"], list):
        wrong.append("errors")
    return wrong


def _decode_json_object(stdout: str) -> tuple[object, str]:
    text = stdout.strip()
    if not text:
        return {}, "empty_stdout"
    try:
        return json.loads(text), ""
    except json.JSONDecodeError as exc:
        return {}, f"{exc.msg} at line {exc.lineno} column {exc.colno}"


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


if __name__ == "__main__":
    raise SystemExit(main())
