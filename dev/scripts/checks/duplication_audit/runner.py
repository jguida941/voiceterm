"""Tool-execution helpers for the duplication-audit script."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if __package__:
    from .report import _path_for_report
else:  # pragma: no cover - standalone script fallback
    from report import _path_for_report


def _missing_tool_message(jscpd_bin: str, report_path: Path) -> str:
    return (
        f"jscpd binary not found: {jscpd_bin}; install via `npm install -g jscpd` "
        f"or provide report evidence at {_path_for_report(report_path)}. "
        "For constrained environments, rerun with --run-jscpd --allow-missing-tool."
    )


def _run_jscpd(
    *,
    source_root: Path,
    report_dir: Path,
    report_path: Path,
    jscpd_bin: str,
    min_lines: int,
    min_tokens: int,
) -> tuple[bool, str | None, str | None]:
    resolved_bin = shutil.which(jscpd_bin)
    if resolved_bin is None:
        return False, _missing_tool_message(jscpd_bin, report_path), "missing_tool"

    report_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        resolved_bin,
        source_root.as_posix(),
        "--min-lines",
        str(min_lines),
        "--min-tokens",
        str(min_tokens),
        "--format",
        "rust",
        "--reporters",
        "json",
        "--output",
        report_dir.as_posix(),
    ]
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).splitlines()[-10:])
        return (
            False,
            f"jscpd failed (exit {proc.returncode}): {tail}",
            "execution_failed",
        )
    if not report_path.exists():
        return (
            False,
            f"jscpd completed but report file missing: {_path_for_report(report_path)}",
            "missing_report",
        )
    return True, None, "ok"
