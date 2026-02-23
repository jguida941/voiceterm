"""`devctl security` command.

Why this exists:
- local runs should catch serious security issues before CI does
- RustSec policy checks are our baseline dependency security gate
- optional scanners (like `zizmor`) can be enabled for stricter workflow checks
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

from ..common import build_env, pipe_output, run_cmd, write_output
from ..config import REPO_ROOT, SRC_DIR
from ..steps import format_steps_md

DEFAULT_FAIL_ON_KINDS = ("yanked", "unsound")
DEFAULT_RUSTSEC_OUTPUT = "rustsec-audit.json"


def _make_internal_step(
    *,
    name: str,
    cmd: list[str],
    returncode: int,
    duration_s: float,
    skipped: bool = False,
    error: str | None = None,
    details: dict | None = None,
) -> dict:
    step = {
        "name": name,
        "cmd": cmd,
        "cwd": str(REPO_ROOT),
        "returncode": returncode,
        "duration_s": round(duration_s, 2),
        "skipped": skipped,
    }
    if error:
        step["error"] = error
    if details:
        step["details"] = details
    return step


def _resolve_rustsec_output(path_value: str | None) -> Path:
    if not path_value:
        return REPO_ROOT / DEFAULT_RUSTSEC_OUTPUT
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _run_rustsec_audit_step(
    report_path: Path,
    *,
    dry_run: bool,
    env: dict,
) -> tuple[dict, list[str]]:
    """Run `cargo audit --json` and write the raw report to disk."""
    cmd = ["cargo", "audit", "--json"]
    if dry_run:
        return (
            _make_internal_step(
                name="rustsec-audit",
                cmd=cmd,
                returncode=0,
                duration_s=0.0,
                skipped=True,
                details={"report_path": str(report_path), "reason": "dry-run"},
            ),
            [],
        )

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=SRC_DIR,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        step = _make_internal_step(
            name="rustsec-audit",
            cmd=cmd,
            returncode=127,
            duration_s=time.time() - start,
            error=str(exc),
        )
        return step, []

    stdout = result.stdout or ""
    if not stdout.strip():
        stderr = (result.stderr or "").strip()
        message = "cargo audit produced no JSON output"
        if stderr:
            message = f"{message}: {stderr}"
        step = _make_internal_step(
            name="rustsec-audit",
            cmd=cmd,
            returncode=result.returncode or 1,
            duration_s=time.time() - start,
            error=message,
        )
        return step, []

    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(stdout, encoding="utf-8")
    except OSError as exc:
        step = _make_internal_step(
            name="rustsec-audit",
            cmd=cmd,
            returncode=2,
            duration_s=time.time() - start,
            error=f"failed to write RustSec report: {exc}",
        )
        return step, []

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            "cargo audit returned non-zero; continuing because policy check decides pass/fail."
        )

    step = _make_internal_step(
        name="rustsec-audit",
        cmd=cmd,
        returncode=0,
        duration_s=time.time() - start,
        details={
            "report_path": str(report_path),
            "cargo_audit_exit_code": result.returncode,
        },
    )
    return step, warnings


def _build_rustsec_policy_cmd(args, report_path: Path) -> list[str]:
    fail_on_kind = args.fail_on_kind or list(DEFAULT_FAIL_ON_KINDS)
    cmd = [
        "python3",
        "dev/scripts/check_rustsec_policy.py",
        "--input",
        str(report_path),
        "--min-cvss",
        str(args.min_cvss),
    ]
    if args.allowlist_file:
        cmd.extend(["--allowlist-file", args.allowlist_file])
    for warning_kind in fail_on_kind:
        cmd.extend(["--fail-on-kind", warning_kind])
    if args.allow_unknown_severity:
        cmd.append("--allow-unknown-severity")
    return cmd


def _run_optional_tool_step(
    *,
    name: str,
    cmd: list[str],
    required: bool,
    dry_run: bool,
    env: dict,
) -> tuple[dict, list[str]]:
    """Run an optional scanner with CI-Hub-style missing-tool behavior."""
    if dry_run:
        return run_cmd(name, cmd, cwd=REPO_ROOT, env=env, dry_run=True), []

    tool = cmd[0]
    if shutil.which(tool) is None:
        message = f"{tool} is not installed. Install it to run this check."
        if required:
            step = _make_internal_step(
                name=name,
                cmd=cmd,
                returncode=127,
                duration_s=0.0,
                error=message,
            )
            return step, []

        step = _make_internal_step(
            name=name,
            cmd=cmd,
            returncode=0,
            duration_s=0.0,
            skipped=True,
            details={"reason": message},
        )
        return step, [message]

    return run_cmd(name, cmd, cwd=REPO_ROOT, env=env, dry_run=False), []


def run(args) -> int:
    """Run local security checks and return a non-zero code on failures."""
    steps: list[dict] = []
    warnings: list[str] = []
    env = build_env(args)

    rustsec_output = _resolve_rustsec_output(args.rustsec_output)
    rustsec_step, rustsec_warnings = _run_rustsec_audit_step(
        rustsec_output,
        dry_run=args.dry_run,
        env=env,
    )
    steps.append(rustsec_step)
    warnings.extend(rustsec_warnings)

    rustsec_policy_cmd = _build_rustsec_policy_cmd(args, rustsec_output)
    if rustsec_step["returncode"] == 0:
        policy_step = run_cmd(
            "rustsec-policy",
            rustsec_policy_cmd,
            cwd=REPO_ROOT,
            env=env,
            dry_run=args.dry_run,
        )
    else:
        policy_step = _make_internal_step(
            name="rustsec-policy",
            cmd=rustsec_policy_cmd,
            returncode=0,
            duration_s=0.0,
            skipped=True,
            details={"reason": "rustsec-audit step failed"},
        )
    steps.append(policy_step)

    if args.with_zizmor:
        zizmor_step, zizmor_warnings = _run_optional_tool_step(
            name="zizmor",
            cmd=["zizmor", ".github/workflows", "--min-severity", "high"],
            required=args.require_optional_tools,
            dry_run=args.dry_run,
            env=env,
        )
        steps.append(zizmor_step)
        warnings.extend(zizmor_warnings)

    success = all(step["returncode"] == 0 for step in steps)
    report = {
        "command": "security",
        "timestamp": datetime.now().isoformat(),
        "ok": success,
        "rustsec_output": str(rustsec_output),
        "warnings": warnings,
        "steps": steps,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    elif args.format == "md":
        lines = ["# devctl security", ""]
        lines.append(f"- ok: {success}")
        lines.append(f"- rustsec_output: {rustsec_output}")
        if warnings:
            lines.append("- warnings:")
            lines.extend(f"  - {warning}" for warning in warnings)
        lines.append("")
        lines.append(format_steps_md(steps))
        output = "\n".join(lines)
    else:
        lines = [
            f"devctl security rustsec_output={rustsec_output}",
            "",
        ]
        for step in steps:
            status = "SKIP" if step.get("skipped") else ("OK" if step["returncode"] == 0 else "FAIL")
            lines.append(f"[{status}] {step['name']} (exit={step['returncode']})")
            if step.get("error"):
                lines.append(f"  reason: {step['error']}")
        if warnings:
            lines.append("")
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")
        lines.append(f"overall={success} exit_code={0 if success else 1}")
        output = "\n".join(lines)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if success else 1
