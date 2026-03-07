"""Shared bootstrap helpers for check scripts."""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
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
