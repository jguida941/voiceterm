"""CLI entrypoint for the tandem-consistency guard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    # Bootstrap checks dir and repo root onto sys.path before any devctl import
    checks_dir = Path(__file__).resolve().parent.parent
    if str(checks_dir) not in sys.path:
        sys.path.insert(0, str(checks_dir))

    from check_bootstrap import REPO_ROOT

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from tandem_consistency.report import build_report, render_md

    parser = argparse.ArgumentParser(description="Tandem-consistency guard.")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--ci-bundle", action="store_true", help="Relax hash enforcement for bundled CI runs")
    args = parser.parse_args()

    bridge_path = REPO_ROOT / "code_audit.md"
    bridge_text = bridge_path.read_text(encoding="utf-8") if bridge_path.exists() else None
    report = build_report(bridge_text=bridge_text, repo_root=REPO_ROOT, ci_bundle=args.ci_bundle)
    output = json.dumps(report, indent=2) if args.format == "json" else render_md(report)
    print(output)
    return 0 if report.get("ok", False) else 1
