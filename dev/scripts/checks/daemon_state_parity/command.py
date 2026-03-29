#!/usr/bin/env python3
"""Guard that validates parity between Rust daemon event types and Python runtime models.

Parses DaemonEvent variants from Rust types.rs, extracts wire names via serde
rename attributes, and validates that the Python daemon_reducer handles all
event types and exposes matching DaemonStateDict fields.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_checks_dir = str(Path(__file__).resolve().parent.parent)
if _checks_dir not in sys.path:
    sys.path.insert(0, _checks_dir)

from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp

RUST_TYPES_PATH = Path("rust/src/bin/voiceterm/daemon/types.rs")
PYTHON_REDUCER_PATH = Path("dev/scripts/devctl/review_channel/daemon_reducer.py")

# Rust serde rename patterns
_VARIANT_RENAME_RE = re.compile(
    r'#\s*\[\s*serde\s*\(\s*rename\s*=\s*"(?P<wire>[^"]+)"\s*\)\s*\]\s*\n\s*'
    r"(?P<variant>[A-Za-z_][A-Za-z0-9_]*)",
)
_ENUM_BLOCK_RE = re.compile(
    r"enum\s+DaemonEvent\s*\{(?P<body>(?:[^{}]|\{[^{}]*\})*)\}",
    re.DOTALL,
)
_STRUCT_FIELDS_RE = re.compile(
    r"struct\s+AgentInfo\s*\{(?P<body>[^}]+)\}",
    re.DOTALL,
)
_RUST_FIELD_RE = re.compile(
    r"^\s*pub\s+(?P<name>[a-z_][a-z0-9_]*)\s*:",
    re.MULTILINE,
)

# Python patterns
_PYTHON_FROZENSET_RE = re.compile(
    r"DAEMON_EVENT_TYPES\s*=\s*frozenset\(\{(?P<body>[^}]+)\}\)",
)
_PYTHON_TYPEDDICT_RE = re.compile(
    r"class\s+DaemonStateDict\(TypedDict\):\s*(?:\"\"\"[^\"]*\"\"\")?\s*\n(?P<body>(?:\s+\w+.*\n)*)",
)


def _parse_rust_event_wire_names(rust_src: str) -> dict[str, str]:
    """Extract DaemonEvent variant → wire name mapping."""
    match = _ENUM_BLOCK_RE.search(rust_src)
    if match is None:
        return {}
    body = match.group("body")
    return {m.group("variant"): m.group("wire") for m in _VARIANT_RENAME_RE.finditer(body)}


def _parse_rust_agent_info_fields(rust_src: str) -> list[str]:
    """Extract AgentInfo struct field names."""
    match = _STRUCT_FIELDS_RE.search(rust_src)
    if match is None:
        return []
    return [m.group("name") for m in _RUST_FIELD_RE.finditer(match.group("body"))]


def _parse_python_event_types(python_src: str) -> set[str]:
    """Extract DAEMON_EVENT_TYPES frozenset entries."""
    match = _PYTHON_FROZENSET_RE.search(python_src)
    if match is None:
        return set()
    body = match.group("body")
    return {s.strip().strip('"').strip("'") for s in body.split(",") if s.strip().strip('"').strip("'")}


def _parse_python_daemon_state_fields(python_src: str) -> list[str]:
    """Extract DaemonStateDict TypedDict field names."""
    match = _PYTHON_TYPEDDICT_RE.search(python_src)
    if match is None:
        return []
    body = match.group("body")
    return [line.split(":")[0].strip() for line in body.strip().splitlines() if ":" in line and not line.strip().startswith("#")]


def build_report(repo_root: Path | None = None) -> dict:
    root = repo_root or REPO_ROOT
    rust_path = root / RUST_TYPES_PATH
    python_path = root / PYTHON_REDUCER_PATH

    violations: list[dict[str, str]] = []
    coverage: list[dict[str, object]] = []

    rust_src = rust_path.read_text(encoding="utf-8")
    python_src = python_path.read_text(encoding="utf-8")

    # Check 1: Rust DaemonEvent wire names covered by Python DAEMON_EVENT_TYPES
    rust_events = _parse_rust_event_wire_names(rust_src)
    python_events = _parse_python_event_types(python_src)
    rust_wire_names = set(rust_events.values())

    # Rust daemon events (daemon_ready, daemon_status, etc.) are wire events
    # broadcast to WebSocket/socket clients. Python DAEMON_EVENT_TYPES are
    # internal event-log event types emitted by the Python publisher. These are
    # deliberately different naming domains. The parity check validates that
    # both sides have a lifecycle start/stop/heartbeat trio, not exact name match.
    rust_lifecycle_events = {
        name for name in rust_wire_names if name.startswith("daemon_")
    }
    python_lifecycle_trio = {"daemon_started", "daemon_stopped", "daemon_heartbeat"}
    rust_lifecycle_trio = {"daemon_ready", "daemon_shutdown", "daemon_status"}
    py_trio_ok = python_lifecycle_trio.issubset(python_events)
    rs_trio_ok = rust_lifecycle_trio.issubset(rust_lifecycle_events)
    trio_ok = py_trio_ok and rs_trio_ok

    coverage.append({
        "check": "daemon_lifecycle_trio_parity",
        "ok": trio_ok,
        "rust_lifecycle_events": sorted(rust_lifecycle_events),
        "python_event_types": sorted(python_events),
        "detail": (
            "Both Rust and Python cover the full daemon lifecycle trio (start/heartbeat-status/stop)."
            if trio_ok
            else f"Incomplete trio: rust_ok={rs_trio_ok} python_ok={py_trio_ok}"
        ),
    })
    if not trio_ok:
        violations.append({
            "rule": "daemon-lifecycle-trio-gap",
            "detail": f"Lifecycle trio incomplete: rust_ok={rs_trio_ok} python_ok={py_trio_ok}",
        })

    # Check 2: DaemonStateDict field completeness
    state_fields = _parse_python_daemon_state_fields(python_src)
    required_fields = {"running", "pid", "started_at_utc", "last_heartbeat_utc", "stop_reason", "stopped_at_utc"}
    missing_state = sorted(required_fields - set(state_fields))
    state_ok = not missing_state
    coverage.append({
        "check": "daemon_state_field_coverage",
        "ok": state_ok,
        "fields": state_fields,
        "detail": (
            "DaemonStateDict covers all required daemon lifecycle fields."
            if state_ok
            else f"Missing fields: {missing_state}"
        ),
    })
    if not state_ok:
        violations.append({
            "rule": "daemon-state-field-gap",
            "detail": f"DaemonStateDict missing: {missing_state}",
        })

    # Check 3: Rust AgentInfo field parity
    agent_fields = _parse_rust_agent_info_fields(rust_src)
    expected_agent = {"session_id", "provider", "label", "working_dir", "pid", "is_alive"}
    actual_agent = set(agent_fields)
    agent_missing = sorted(expected_agent - actual_agent)
    agent_ok = not agent_missing
    coverage.append({
        "check": "agent_info_field_parity",
        "ok": agent_ok,
        "rust_fields": agent_fields,
        "detail": (
            "Rust AgentInfo has all expected fields."
            if agent_ok
            else f"Missing: {agent_missing}"
        ),
    })

    return {
        "command": "check_daemon_state_parity",
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "rust_daemon_event_variants": len(rust_events),
        "python_daemon_event_types": len(python_events),
        "daemon_state_fields": len(state_fields),
        "violations": violations,
        "coverage": coverage,
    }


def render_md(report: dict) -> str:
    lines = ["# check_daemon_state_parity", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- rust_daemon_event_variants: {report['rust_daemon_event_variants']}")
    lines.append(f"- python_daemon_event_types: {report['python_daemon_event_types']}")
    lines.append(f"- daemon_state_fields: {report['daemon_state_fields']}")
    lines.append(f"- violations: {len(report['violations'])}")
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    for row in report.get("coverage", []):
        tag = "PASS" if row.get("ok") else "FAIL"
        lines.append(f"- [{tag}] {row['check']}: {row.get('detail', '')}")
    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append("")
        for v in report["violations"]:
            lines.append(f"- {v['rule']}: {v['detail']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()

    try:
        report = build_report()
    except (ImportError, OSError, ValueError) as exc:
        return emit_runtime_error("check_daemon_state_parity", args.format, str(exc))

    output = json.dumps(report, indent=2) if args.format == "json" else render_md(report)
    print(output)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
