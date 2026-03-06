#!/usr/bin/env python3
"""Guard bundle registry DRY compliance: flag copy-paste command sharing."""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Final

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH: Final[str] = "dev/scripts/devctl/bundle_registry.py"
DEFAULT_MAX_SHARED: Final[int] = 5


def _load_registry():
    module_path = REPO_ROOT / REGISTRY_PATH
    spec = importlib.util.spec_from_file_location("bundle_registry", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_shared_constants(module) -> bool:
    for name, obj in inspect.getmembers(module):
        if name.startswith("_") and isinstance(obj, tuple) and all(isinstance(s, str) for s in obj):
            return True
    return False


def build_report(max_shared: int = DEFAULT_MAX_SHARED) -> dict:
    registry = _load_registry()
    bundles: dict[str, tuple[str, ...]] = registry.BUNDLE_REGISTRY
    uses_composition = _has_shared_constants(registry)

    cmd_counts: Counter[str] = Counter()
    for commands in bundles.values():
        for cmd in commands:
            cmd_counts[cmd] += 1

    widely_shared = [cmd for cmd, count in cmd_counts.items() if count > 2]

    violations: list[dict[str, object]] = []
    if widely_shared and not uses_composition:
        for cmd in widely_shared:
            violations.append({
                "rule": "dry-violation",
                "command_text": cmd,
                "bundle_count": cmd_counts[cmd],
                "hint": "Extract shared commands into a composition tuple in bundle_registry.py.",
            })

    if len(widely_shared) > max_shared and not uses_composition:
        pass  # violations already collected above

    return {
        "command": "check_bundle_registry_dry",
        "timestamp": datetime.now().isoformat(),
        "ok": not violations,
        "bundle_count": len(bundles),
        "widely_shared_count": len(widely_shared),
        "uses_composition": uses_composition,
        "violations": violations,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# check_bundle_registry_dry",
        "",
        f"- ok: {report['ok']}",
        f"- bundle_count: {report['bundle_count']}",
        f"- widely_shared_count: {report['widely_shared_count']}",
        f"- uses_composition: {report['uses_composition']}",
        f"- violations: {len(report['violations'])}",
    ]
    violations = report.get("violations", [])
    if violations:
        lines.extend(["", "## Violations"])
        for v in violations:
            lines.append(
                "- [{rule}] `{command_text}` appears in {bundle_count} bundles -> {hint}".format(
                    rule=v["rule"],
                    command_text=v["command_text"],
                    bundle_count=v["bundle_count"],
                    hint=v["hint"],
                )
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--max-shared",
        type=int,
        default=DEFAULT_MAX_SHARED,
        help="Max commands allowed in >2 bundles without composition (default: 5).",
    )
    args = parser.parse_args()
    report = build_report(max_shared=args.max_shared)
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
