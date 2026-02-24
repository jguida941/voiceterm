"""Security step builders for `devctl security`.

Shared helpers for building RustSec audit steps, policy commands, and
optional-tool runner steps. Extracted from security.py to keep the
command module under code-shape budgets.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from ..common import run_cmd
from ..config import REPO_ROOT, SRC_DIR
from ..script_catalog import check_script_cmd
from ..security_tiers import annotate_step_metadata

DEFAULT_FAIL_ON_KINDS = ("yanked", "unsound")
DEFAULT_RUSTSEC_OUTPUT = "rustsec-audit.json"


def make_internal_step(
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


def resolve_rustsec_output(path_value: str | None) -> Path:
    if not path_value:
        return REPO_ROOT / DEFAULT_RUSTSEC_OUTPUT
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def run_rustsec_audit_step(
    report_path: Path,
    *,
    dry_run: bool,
    env: dict,
) -> tuple[dict, list[str]]:
    """Run `cargo audit --json` and write the raw report to disk."""
    cmd = ["cargo", "audit", "--json"]
    if dry_run:
        step = make_internal_step(
            name="rustsec-audit",
            cmd=cmd,
            returncode=0,
            duration_s=0.0,
            skipped=True,
            details={"report_path": str(report_path), "reason": "dry-run"},
        )
        return annotate_step_metadata(step, tier="core", blocking=True), []
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
        step = make_internal_step(
            name="rustsec-audit",
            cmd=cmd,
            returncode=127,
            duration_s=time.time() - start,
            error=str(exc),
        )
        return annotate_step_metadata(step, tier="core", blocking=True), []
    stdout = result.stdout or ""
    if not stdout.strip():
        stderr = (result.stderr or "").strip()
        message = "cargo audit produced no JSON output"
        if stderr:
            message = f"{message}: {stderr}"
        step = make_internal_step(
            name="rustsec-audit",
            cmd=cmd,
            returncode=result.returncode or 1,
            duration_s=time.time() - start,
            error=message,
        )
        return annotate_step_metadata(step, tier="core", blocking=True), []
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(stdout, encoding="utf-8")
    except OSError as exc:
        step = make_internal_step(
            name="rustsec-audit",
            cmd=cmd,
            returncode=2,
            duration_s=time.time() - start,
            error=f"failed to write RustSec report: {exc}",
        )
        return annotate_step_metadata(step, tier="core", blocking=True), []
    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            "cargo audit returned non-zero; continuing because policy check decides pass/fail."
        )

    step = make_internal_step(
        name="rustsec-audit",
        cmd=cmd,
        returncode=0,
        duration_s=time.time() - start,
        details={
            "report_path": str(report_path),
            "cargo_audit_exit_code": result.returncode,
        },
    )
    return annotate_step_metadata(step, tier="core", blocking=True), warnings


def build_rustsec_policy_cmd(args, report_path: Path) -> list[str]:
    fail_on_kind = args.fail_on_kind or list(DEFAULT_FAIL_ON_KINDS)
    cmd = check_script_cmd(
        "rustsec_policy",
        "--input",
        str(report_path),
        "--min-cvss",
        str(args.min_cvss),
    )
    if args.allowlist_file:
        cmd.extend(["--allowlist-file", args.allowlist_file])
    for warning_kind in fail_on_kind:
        cmd.extend(["--fail-on-kind", warning_kind])
    if args.allow_unknown_severity:
        cmd.append("--allow-unknown-severity")
    return cmd


def run_optional_tool_step(
    *,
    name: str,
    cmd: list[str],
    required: bool,
    dry_run: bool,
    env: dict,
    cwd: Path | None = None,
    tier: str = "core",
    blocking: bool = True,
) -> tuple[dict, list[str]]:
    """Run an optional scanner with CI-Hub-style missing-tool behavior."""
    run_cwd = cwd or REPO_ROOT
    if dry_run:
        step = run_cmd(name, cmd, cwd=run_cwd, env=env, dry_run=True)
        return annotate_step_metadata(step, tier=tier, blocking=blocking), []
    tool = cmd[0]
    if shutil.which(tool) is None:
        message = f"{tool} is not installed. Install it to run this check."
        if required:
            step = make_internal_step(
                name=name,
                cmd=cmd,
                returncode=127,
                duration_s=0.0,
                error=message,
            )
            return annotate_step_metadata(step, tier=tier, blocking=True), []
        step = make_internal_step(
            name=name,
            cmd=cmd,
            returncode=0,
            duration_s=0.0,
            skipped=True,
            details={"reason": message},
        )
        return annotate_step_metadata(step, tier=tier, blocking=blocking), [message]
    step = run_cmd(name, cmd, cwd=run_cwd, env=env, dry_run=False)
    return annotate_step_metadata(step, tier=tier, blocking=blocking), []
