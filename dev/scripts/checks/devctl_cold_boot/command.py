#!/usr/bin/env python3
"""Cold-boot smoke guard for the devctl CLI import graph."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _run_probe(repo_root: Path) -> dict[str, object]:
    command = [
        sys.executable,
        "-c",
        (
            "import sys; "
            "sys.path.insert(0, 'dev/scripts'); "
            "from devctl.cli import main"
        ),
    ]
    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return {
        "command": "check_devctl_cold_boot",
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "probe": "from devctl.cli import main",
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _render_md(report: dict[str, object]) -> str:
    lines = ["# check_devctl_cold_boot", ""]
    lines.append(f"- ok: {bool(report.get('ok', False))}")
    lines.append(f"- probe: `{report.get('probe')}`")
    if report.get("stderr"):
        lines.extend(["", "## stderr", "", "```text", str(report["stderr"]), "```"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "md"), default="json")
    args = parser.parse_args(argv)

    report = _run_probe(_repo_root())
    if args.format == "md":
        sys.stdout.write(_render_md(report))
    else:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if bool(report["ok"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
