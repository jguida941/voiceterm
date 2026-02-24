"""Helpers for running policy scripts that emit JSON reports."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .config import REPO_ROOT


def run_json_policy_gate(script_path: Path, gate_label: str) -> dict:
    """Run a policy script with `--format json` and parse its report."""
    if not script_path.exists():
        return {
            "ok": False,
            "error": f"Missing {gate_label} script: {script_path.relative_to(REPO_ROOT)}",
        }

    try:
        completed = subprocess.run(
            ["python3", str(script_path), "--format", "json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {"ok": False, "error": f"Failed to run {gate_label}: {exc}"}

    output = completed.stdout.strip()
    if not output:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        return {"ok": False, "error": f"{gate_label} produced no JSON output ({detail})."}

    try:
        report = json.loads(output)
    except json.JSONDecodeError as exc:
        snippet = output[:200].strip().replace("\n", " ")
        return {
            "ok": False,
            "error": f"{gate_label} returned invalid JSON ({exc}): {snippet}",
        }

    if completed.returncode not in (0, 1):
        stderr = completed.stderr.strip()
        report.setdefault(
            "error",
            f"{gate_label} exited with code {completed.returncode}"
            + (f": {stderr}" if stderr else ""),
        )
        report["ok"] = False
    return report
