"""devctl cihub-setup command implementation."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime

from ..common import confirm_or_abort, pipe_output, run_cmd, write_output
from ..config import REPO_ROOT

ALLOWED_SETUP_STEPS = ("detect", "init", "update", "validate")
ALLOWED_STEP_FLAGS = ("--repo",)


def _build_step_cmd(args, step: str) -> list[str]:
    cmd = [args.cihub_bin, step]
    if args.repo:
        cmd.extend(["--repo", args.repo])
    return cmd


def _parse_help_commands(help_text: str) -> tuple[set[str], str]:
    match = re.search(r"\{([^}]+)\}", help_text)
    if match:
        commands = {part.strip() for part in match.group(1).split(",") if part.strip()}
        return commands, "parsed-braces"

    commands = {
        command
        for command in ALLOWED_SETUP_STEPS
        if re.search(rf"\b{re.escape(command)}\b", help_text)
    }
    return commands, "fallback-text-search"


def _probe_capabilities(cihub_bin: str) -> dict:
    if shutil.which(cihub_bin) is None:
        return {
            "available": False,
            "probe": "which",
            "error": f"{cihub_bin} binary not found.",
            "commands": [],
        }

    try:
        result = subprocess.run(
            [cihub_bin, "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {
            "available": False,
            "probe": "help",
            "error": str(exc),
            "commands": [],
        }

    help_text = "\n".join([result.stdout or "", result.stderr or ""])
    commands, probe_source = _parse_help_commands(help_text)

    available = result.returncode == 0 and bool(commands)
    error = None
    if result.returncode != 0:
        error = (result.stderr or result.stdout).strip() or "cihub --help failed"
    elif not commands:
        error = "Unable to detect CIHub setup capabilities from help output."

    return {
        "available": available,
        "probe": probe_source,
        "error": error,
        "commands": sorted(commands),
    }


def _render_md(report: dict) -> str:
    lines = ["# devctl cihub-setup", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- cihub_bin: {report['cihub_bin']}")
    lines.append(f"- strict_capabilities: {report['strict_capabilities']}")
    lines.append(f"- capability_probe: {report['capability_probe'].get('probe')}")
    lines.append(f"- available_commands: {', '.join(report['capability_probe'].get('commands', [])) or 'none'}")
    lines.append(f"- warnings: {len(report['warnings'])}")
    lines.append(f"- errors: {len(report['errors'])}")

    lines.append("")
    lines.append("| Step | Supported | Status | Exit | Command |")
    lines.append("|---|---|---|---:|---|")
    for step in report["steps"]:
        exit_code = "-" if step.get("returncode") is None else str(step["returncode"])
        lines.append(
            f"| `{step['step']}` | {step['supported']} | {step['status']} | {exit_code} | `{ ' '.join(step['cmd']) }` |"
        )

    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        lines.extend(f"- {warning}" for warning in report["warnings"])
    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in report["errors"])

    return "\n".join(lines)


def run(args) -> int:
    """Preview/apply allowlisted CIHub setup steps with capability guards."""
    warnings: list[str] = []
    errors: list[str] = []

    capability_probe = _probe_capabilities(args.cihub_bin)
    available_commands = set(capability_probe.get("commands", []))
    if capability_probe.get("error"):
        warnings.append(capability_probe["error"])

    requested_steps = []
    for step in args.steps:
        if step not in requested_steps:
            requested_steps.append(step)

    step_rows: list[dict] = []
    unsupported_steps: list[str] = []
    for step in requested_steps:
        cmd = _build_step_cmd(args, step)
        supported = capability_probe.get("available", False) and step in available_commands
        row = {
            "step": step,
            "cmd": cmd,
            "supported": supported,
            "status": "preview" if not args.apply else "pending",
            "returncode": None,
        }
        if not supported:
            row["status"] = "unsupported"
            unsupported_steps.append(step)
        step_rows.append(row)

    if unsupported_steps and args.strict_capabilities:
        errors.append(
            "Requested CIHub setup steps are unsupported for this binary: "
            + ", ".join(unsupported_steps)
        )

    if args.apply and not errors:
        runnable = [step for step in step_rows if step["supported"]]
        if not runnable:
            warning = "No runnable setup steps were detected; nothing was applied."
            warnings.append(warning)
            if args.strict_capabilities:
                errors.append(warning)
        else:
            confirm_or_abort(
                "Run allowlisted CIHub setup steps " + ", ".join(step["step"] for step in runnable) + "?",
                args.yes or args.dry_run,
            )

            for row in step_rows:
                if not row["supported"]:
                    continue
                step_result = run_cmd(
                    f"cihub-{row['step']}",
                    row["cmd"],
                    cwd=REPO_ROOT,
                    dry_run=args.dry_run,
                )
                row.update(
                    {
                        "status": "applied"
                        if step_result.get("returncode") == 0
                        else "failed",
                        "returncode": step_result.get("returncode"),
                        "skipped": step_result.get("skipped", False),
                    }
                )
                if step_result.get("error"):
                    row["error"] = step_result["error"]
                if row["status"] == "failed":
                    errors.append(
                        f"{row['step']} failed with exit code {step_result.get('returncode')}."
                    )

    report = {
        "command": "cihub-setup",
        "timestamp": datetime.now().isoformat(),
        "ok": len(errors) == 0,
        "mode": "apply" if args.apply else "preview",
        "cihub_bin": args.cihub_bin,
        "strict_capabilities": bool(args.strict_capabilities),
        "allowlist": {
            "steps": list(ALLOWED_SETUP_STEPS),
            "flags": list(ALLOWED_STEP_FLAGS),
        },
        "capability_probe": capability_probe,
        "requested_steps": requested_steps,
        "steps": step_rows,
        "warnings": warnings,
        "errors": errors,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    elif args.format == "md":
        output = _render_md(report)
    else:
        output = json.dumps(report, indent=2)

    write_output(output, args.output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc

    return 0 if report["ok"] else 1
