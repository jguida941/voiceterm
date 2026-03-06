"""devctl compat-matrix command implementation."""

from __future__ import annotations

import json
from datetime import datetime

from ..common import pipe_output, write_output
from ..policy_gate import run_json_policy_gate
from ..script_catalog import check_script_path

COMPAT_MATRIX_SCRIPT = check_script_path("compat_matrix")
COMPAT_MATRIX_SMOKE_SCRIPT = check_script_path("compat_matrix_smoke")


def _render_md(report: dict) -> str:
    lines = ["# devctl compat-matrix", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- validation_ok: {report['validation_ok']}")
    lines.append(f"- smoke_ok: {report['smoke_ok']}")
    lines.append(f"- run_smoke: {report['run_smoke']}")
    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        for item in report["errors"]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def run(args) -> int:
    """Run compatibility matrix validation (+ optional smoke checks)."""
    validation_report = run_json_policy_gate(
        COMPAT_MATRIX_SCRIPT, "compatibility matrix validation gate"
    )
    validation_ok = bool(validation_report.get("ok", False))

    smoke_report = None
    smoke_ok = True
    run_smoke = not getattr(args, "no_smoke", False)
    if run_smoke:
        smoke_report = run_json_policy_gate(
            COMPAT_MATRIX_SMOKE_SCRIPT, "compatibility matrix smoke gate"
        )
        smoke_ok = bool(smoke_report.get("ok", False))

    errors: list[str] = []
    if not validation_ok:
        errors.append(
            validation_report.get("error")
            or "compatibility matrix validation gate failed"
        )
    if run_smoke and not smoke_ok:
        errors.append(smoke_report.get("error") or "compatibility matrix smoke gate failed")

    report = {
        "command": "compat-matrix",
        "timestamp": datetime.now().isoformat(),
        "ok": validation_ok and smoke_ok,
        "run_smoke": run_smoke,
        "validation_ok": validation_ok,
        "smoke_ok": smoke_ok,
        "validation_report": validation_report,
        "smoke_report": smoke_report,
        "errors": errors,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if report["ok"] else 1
