"""devctl audit-scaffold command implementation."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

from ..common import confirm_or_abort, pipe_output, write_output
from ..config import REPO_ROOT
from ..script_catalog import check_script_cmd
from .audit_scaffold_render import (
    report_output,
    render_generated_doc,
)

ACTIVE_ROOT = (REPO_ROOT / "dev" / "active").resolve()
DEFAULT_OUTPUT = "dev/active/RUST_AUDIT_FINDINGS.md"
DEFAULT_TEMPLATE = "dev/config/templates/rust_audit_findings_template.md"

GUARD_SPECS = (
    {
        "name": "code-shape-guard",
        "script_id": "code_shape",
        "supports_range": True,
        "severity": "high",
        "focus": "modularity",
    },
    {
        "name": "rust-lint-debt-guard",
        "script_id": "rust_lint_debt",
        "supports_range": True,
        "severity": "high",
        "focus": "lint debt",
    },
    {
        "name": "rust-best-practices-guard",
        "script_id": "rust_best_practices",
        "supports_range": True,
        "severity": "high",
        "focus": "best practices",
    },
    {
        "name": "rust-audit-patterns-guard",
        "script_id": "rust_audit_patterns",
        "supports_range": False,
        "severity": "critical",
        "focus": "known audit regressions",
    },
    {
        "name": "rust-security-footguns-guard",
        "script_id": "rust_security_footguns",
        "supports_range": True,
        "severity": "critical",
        "focus": "security footguns",
    },
)


def _resolve_repo_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate.resolve()
    return (REPO_ROOT / candidate).resolve()


def _is_under_active_root(path: Path) -> bool:
    try:
        path.relative_to(ACTIVE_ROOT)
    except ValueError:
        return False
    return True


def _repo_relative(path: Path) -> str:
    repo_root = REPO_ROOT.resolve()
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root).as_posix()
    except ValueError:
        return resolved.as_posix()


def _guard_cmd(spec: dict, *, since_ref: str | None, head_ref: str) -> list[str]:
    cmd = check_script_cmd(spec["script_id"], "--format", "json")
    if spec["supports_range"] and since_ref:
        cmd.extend(["--since-ref", since_ref, "--head-ref", head_ref])
    return cmd


def _run_guard(spec: dict, *, since_ref: str | None, head_ref: str, dry_run: bool) -> dict:
    cmd = _guard_cmd(spec, since_ref=since_ref, head_ref=head_ref)
    if dry_run:
        return {
            "name": spec["name"],
            "script_id": spec["script_id"],
            "severity": spec["severity"],
            "focus": spec["focus"],
            "cmd": cmd,
            "returncode": 0,
            "ok": True,
            "skipped": True,
            "violations": [],
            "error": None,
            "report": {},
        }

    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout = proc.stdout.strip()
    report = {}
    parse_error = None
    if stdout:
        try:
            report = json.loads(stdout)
        except json.JSONDecodeError as exc:
            parse_error = f"failed to parse {spec['name']} json output: {exc}"
    elif proc.stderr.strip():
        parse_error = f"{spec['name']} emitted no JSON output"

    violations = report.get("violations", []) if isinstance(report, dict) else []
    return {
        "name": spec["name"],
        "script_id": spec["script_id"],
        "severity": spec["severity"],
        "focus": spec["focus"],
        "cmd": cmd,
        "returncode": proc.returncode,
        "ok": bool(report.get("ok", proc.returncode == 0)) if isinstance(report, dict) else False,
        "skipped": False,
        "violations": violations if isinstance(violations, list) else [],
        "error": parse_error,
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]) if proc.stderr else "",
        "report": report if isinstance(report, dict) else {},
    }


def run(args) -> int:
    """Generate an actionable audit scaffold from guard-script findings."""
    errors: list[str] = []

    output_path = _resolve_repo_path(args.output_path)
    template_path = _resolve_repo_path(args.template_path)

    if not _is_under_active_root(output_path):
        errors.append(
            f"output path must stay under dev/active/ (got: {output_path})"
        )

    if not template_path.exists():
        errors.append(f"template file does not exist: {template_path}")

    if output_path.exists() and not args.force:
        errors.append(
            "output file already exists; pass --force to overwrite"
        )

    if errors:
        report = {
            "command": "audit-scaffold",
            "timestamp": datetime.now().isoformat(),
            "ok": False,
            "output_path": output_path.as_posix(),
            "findings_detected": False,
            "trigger": args.trigger,
            "trigger_steps": args.trigger_steps or "n/a",
            "guards": [],
            "errors": errors,
        }
        output = report_output(report, args.format)
        write_output(output, args.output)
        return 1

    if output_path.exists():
        confirm_or_abort(
            f"Overwrite existing audit scaffold at {output_path.relative_to(REPO_ROOT)}?",
            args.yes or args.dry_run,
        )

    template_text = template_path.read_text(encoding="utf-8")
    since_ref = args.since_ref
    head_ref = args.head_ref
    range_label = f"{since_ref}..{head_ref}" if since_ref else "working-tree vs HEAD"

    guard_steps: list[dict] = []
    if args.source_guards:
        for spec in GUARD_SPECS:
            guard_steps.append(
                _run_guard(spec, since_ref=since_ref, head_ref=head_ref, dry_run=args.dry_run)
            )

    findings_detected = any(bool(step.get("violations")) for step in guard_steps)
    generated_at = datetime.now().isoformat()
    generated_doc = render_generated_doc(
        template_text=template_text,
        generated_at=generated_at,
        trigger=args.trigger,
        trigger_steps=args.trigger_steps or "n/a",
        range_label=range_label,
        guard_steps=guard_steps,
    )

    if not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(generated_doc, encoding="utf-8")

    report = {
        "command": "audit-scaffold",
        "timestamp": generated_at,
        "ok": True,
        "output_path": _repo_relative(output_path),
        "template_path": _repo_relative(template_path),
        "findings_detected": findings_detected,
        "trigger": args.trigger,
        "trigger_steps": args.trigger_steps or "n/a",
        "range": range_label,
        "guards": guard_steps,
        "errors": [],
    }

    output = report_output(report, args.format)
    write_output(output, args.output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc
    return 0
