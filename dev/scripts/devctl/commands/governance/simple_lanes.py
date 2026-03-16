"""Simple policy-backed lane aliases for vibecoder-facing devctl flows."""

from __future__ import annotations

import json
from typing import Any

from ...common import emit_output, pipe_output, run_cmd, write_output
from ...config import REPO_ROOT
from ...time_utils import utc_timestamp
from .simple_lanes_support import (
    TandemValidateExecution,
    build_tandem_validate_plan,
    build_tandem_validate_report,
    render_tandem_validate_markdown,
)

LAUNCHER_POLICY_PATH = "dev/config/devctl_policies/launcher.json"


def _append_output_args(argv: list[str], args: Any) -> None:
    if getattr(args, "format", None):
        argv.extend(["--format", args.format])
    if getattr(args, "output", None):
        argv.extend(["--output", args.output])
    if getattr(args, "pipe_command", None):
        argv.extend(["--pipe-command", args.pipe_command])
    if getattr(args, "pipe_args", None):
        argv.extend(["--pipe-args", *args.pipe_args])


def _dispatch(argv: list[str]) -> int:
    from ... import cli as devctl_cli

    parsed = devctl_cli.build_parser().parse_args(argv)
    handler = devctl_cli.COMMAND_HANDLERS.get(parsed.command)
    if handler is None:
        raise ValueError(f"unknown delegated devctl command: {parsed.command}")
    return handler(parsed)


def run_tandem_validate(args) -> int:
    """Run the canonical live tandem validation lane."""
    plan = build_tandem_validate_plan(
        quality_policy_path=getattr(args, "quality_policy", None),
        since_ref=getattr(args, "since_ref", None),
        head_ref=getattr(args, "head_ref", "HEAD"),
    )
    steps: list[dict[str, object]] = []
    ok = bool(plan["ok"])
    if ok:
        for index, row in enumerate(plan["planned_commands"], start=1):
            command = str(row["command"])
            result = run_cmd(
                f"tandem-{index:02d}",
                ["bash", "-lc", command],
                cwd=REPO_ROOT,
                dry_run=bool(getattr(args, "dry_run", False)),
            )
            step = dict(result)
            step["command"] = command
            step["source"] = row["source"]
            steps.append(step)
            if result["returncode"] != 0:
                ok = False
                if not getattr(args, "keep_going", False):
                    break
    report = build_tandem_validate_report(
        plan=plan,
        execution=TandemValidateExecution(
            ok=ok,
            dry_run=bool(getattr(args, "dry_run", False)),
            keep_going=bool(getattr(args, "keep_going", False)),
            quality_policy=getattr(args, "quality_policy", None),
            steps=steps,
            timestamp=utc_timestamp(),
        ),
    )
    output = (
        json.dumps(report, indent=2)
        if getattr(args, "format", "md") == "json"
        else render_tandem_validate_markdown(report)
    )
    pipe_rc = emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if ok else 1


def run_launcher_check(args) -> int:
    """Run a focused AI-guard lane for launcher/package Python entrypoints."""
    argv = [
        "check",
        "--with-ai-guard",
        "--skip-fmt",
        "--skip-clippy",
        "--skip-tests",
        "--skip-build",
        "--quality-policy",
        LAUNCHER_POLICY_PATH,
    ]
    if getattr(args, "since_ref", None):
        argv.extend(["--since-ref", args.since_ref, "--head-ref", args.head_ref])
    if getattr(args, "adoption_scan", False):
        argv.append("--adoption-scan")
    if getattr(args, "dry_run", False):
        argv.append("--dry-run")
    if getattr(args, "keep_going", False):
        argv.append("--keep-going")
    if getattr(args, "no_parallel", False):
        argv.append("--no-parallel")
    _append_output_args(argv, args)
    return _dispatch(argv)


def run_launcher_probes(args) -> int:
    """Run focused review probes for launcher/package Python entrypoints."""
    argv = [
        "probe-report",
        "--quality-policy",
        LAUNCHER_POLICY_PATH,
        "--output-root",
        args.output_root,
    ]
    if getattr(args, "since_ref", None):
        argv.extend(["--since-ref", args.since_ref, "--head-ref", args.head_ref])
    if getattr(args, "adoption_scan", False):
        argv.append("--adoption-scan")
    if getattr(args, "emit_artifacts", True):
        argv.append("--emit-artifacts")
    else:
        argv.append("--no-emit-artifacts")
    if getattr(args, "json_output", None):
        argv.extend(["--json-output", args.json_output])
    _append_output_args(argv, args)
    return _dispatch(argv)


def run_launcher_policy(args) -> int:
    """Render the focused launcher/package quality policy."""
    argv = [
        "quality-policy",
        "--quality-policy",
        LAUNCHER_POLICY_PATH,
    ]
    _append_output_args(argv, args)
    return _dispatch(argv)
