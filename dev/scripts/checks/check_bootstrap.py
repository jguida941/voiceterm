"""Shared bootstrap helpers for check scripts."""

from __future__ import annotations

import argparse
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def import_attr(module_name: str, attr_name: str) -> Any:
    """Import an attribute from local-script or package execution contexts."""
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        module = importlib.import_module(f"dev.scripts.checks.{module_name}")
    return getattr(module, attr_name)


def utc_timestamp() -> str:
    """Return a stable UTC ISO-8601 timestamp for JSON/markdown reports."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_since_ref_format_parser(description: str) -> argparse.ArgumentParser:
    """Build the standard since-ref/head-ref/format parser shared by guards."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def is_under_target_roots(
    path: Path, *, repo_root: Path, target_roots: tuple[Path, ...]
) -> bool:
    """Return whether a repo path falls within one of the configured roots."""
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        relative = path
    return any(relative == root or root in relative.parents for root in target_roots)


def emit_runtime_error(command: str, output_format: str, error: str) -> int:
    """Emit a consistent error report for guard script runtime failures."""
    report = {
        "command": command,
        "timestamp": utc_timestamp(),
        "ok": False,
        "error": error,
    }
    if output_format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"# {command}\n")
        print(f"- ok: False\n- error: {report['error']}")
    return 2
