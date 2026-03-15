"""Simple policy-backed lane aliases for vibecoder-facing devctl flows."""

from __future__ import annotations

from typing import Any

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
