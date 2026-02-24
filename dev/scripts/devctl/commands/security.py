"""`devctl security` command.

Why this exists:
- local runs should catch serious security issues before CI does
- RustSec policy checks are our baseline dependency security gate
- scanner tiers split core checks from expensive optional scanners
"""

from __future__ import annotations

import json
from datetime import datetime

from ..common import build_env, pipe_output, run_cmd, write_output
from ..config import REPO_ROOT
from ..security_tiers import (
    CORE_SCANNER_IDS,
    EXPENSIVE_SCANNER_IDS,
    annotate_step_metadata,
    run_codeql_core_step,
    run_expensive_steps,
    run_python_core_steps,
    step_is_blocking_failure,
)
from ..steps import format_steps_md
from .security_steps import (
    build_rustsec_policy_cmd,
    make_internal_step,
    resolve_rustsec_output,
    run_optional_tool_step,
    run_rustsec_audit_step,
)


def run(args) -> int:
    """Run local security checks and return a non-zero code on failures."""
    steps: list[dict] = []
    warnings: list[str] = []
    env = build_env(args)
    rustsec_output = resolve_rustsec_output(args.rustsec_output)
    rustsec_step, rustsec_warnings = run_rustsec_audit_step(
        rustsec_output,
        dry_run=args.dry_run,
        env=env,
    )
    steps.append(rustsec_step)
    warnings.extend(rustsec_warnings)
    rustsec_policy_cmd = build_rustsec_policy_cmd(args, rustsec_output)
    if rustsec_step["returncode"] == 0:
        policy_step = run_cmd(
            "rustsec-policy",
            rustsec_policy_cmd,
            cwd=REPO_ROOT,
            env=env,
            dry_run=args.dry_run,
        )
        policy_step = annotate_step_metadata(policy_step, tier="core", blocking=True)
    else:
        policy_step = make_internal_step(
            name="rustsec-policy",
            cmd=rustsec_policy_cmd,
            returncode=0,
            duration_s=0.0,
            skipped=True,
            details={"reason": "rustsec-audit step failed"},
        )
        policy_step = annotate_step_metadata(policy_step, tier="core", blocking=True)
    steps.append(policy_step)
    core_enabled = args.scanner_tier in ("core", "all")
    run_zizmor = bool(args.with_zizmor)
    run_codeql_alerts = bool(args.with_codeql_alerts)
    if run_zizmor:
        zizmor_step, zizmor_warnings = run_optional_tool_step(
            name="zizmor",
            cmd=["zizmor", ".github/workflows", "--min-severity", "high"],
            required=args.require_optional_tools,
            dry_run=args.dry_run,
            env=env,
            tier="core",
            blocking=True,
        )
        steps.append(zizmor_step)
        warnings.extend(zizmor_warnings)
    if run_codeql_alerts:
        codeql_step, codeql_warnings = run_codeql_core_step(
            args=args,
            repo_root=REPO_ROOT,
            env=env,
            make_internal_step=make_internal_step,
        )
        steps.append(codeql_step)
        warnings.extend(codeql_warnings)
    if core_enabled:
        python_steps, python_warnings = run_python_core_steps(
            args=args,
            repo_root=REPO_ROOT,
            env=env,
            run_optional_tool_step=run_optional_tool_step,
            make_internal_step=make_internal_step,
        )
        steps.extend(python_steps)
        warnings.extend(python_warnings)
    if args.scanner_tier == "all":
        expensive_steps, expensive_warnings = run_expensive_steps(
            args=args,
            repo_root=REPO_ROOT,
            src_dir=REPO_ROOT / "src",
            env=env,
            run_optional_tool_step=run_optional_tool_step,
        )
        steps.extend(expensive_steps)
        warnings.extend(expensive_warnings)
    success = not any(step_is_blocking_failure(step) for step in steps)
    report = {
        "command": "security",
        "timestamp": datetime.now().isoformat(),
        "ok": success,
        "rustsec_output": str(rustsec_output),
        "scanner_tier": args.scanner_tier,
        "python_scope": getattr(args, "python_scope", "auto"),
        "since_ref": getattr(args, "since_ref", None),
        "head_ref": getattr(args, "head_ref", "HEAD"),
        "expensive_policy": args.expensive_policy,
        "core_scanners": list(CORE_SCANNER_IDS),
        "expensive_scanners": list(EXPENSIVE_SCANNER_IDS),
        "warnings": warnings,
        "steps": steps,
    }
    if args.format == "json":
        output = json.dumps(report, indent=2)
    elif args.format == "md":
        lines = ["# devctl security", ""]
        lines.append(f"- ok: {success}")
        lines.append(f"- rustsec_output: {rustsec_output}")
        lines.append(f"- scanner_tier: {args.scanner_tier}")
        lines.append(f"- python_scope: {getattr(args, 'python_scope', 'auto')}")
        lines.append(f"- expensive_policy: {args.expensive_policy}")
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
            (
                f"scanner_tier={args.scanner_tier} "
                f"python_scope={getattr(args, 'python_scope', 'auto')} "
                f"expensive_policy={args.expensive_policy}"
            ),
        ]
        for step in steps:
            blocking_failure = step_is_blocking_failure(step)
            if step.get("skipped"):
                status = "SKIP"
            elif step["returncode"] == 0:
                status = "OK"
            elif blocking_failure:
                status = "FAIL"
            else:
                status = "WARN"
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
