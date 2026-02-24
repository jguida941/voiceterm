"""Shared helpers for emitting devctl audit metric events."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import REPO_ROOT

POLICY_PATH = REPO_ROOT / "dev/config/control_plane_policy.json"
POLICY_KEY = "audit_metrics"
DEFAULT_EVENT_LOG = Path("dev/reports/audits/devctl_events.jsonl")
SOURCE_BUCKETS = {"script_only", "ai_assisted", "human_manual", "other"}
AREA_BY_COMMAND = {
    "triage-loop": "loops",
    "mutation-loop": "loops",
    "loop-packet": "loops",
    "autonomy-loop": "loops",
    "integrations-sync": "federation",
    "integrations-import": "federation",
    "orchestrate-status": "orchestration",
    "orchestrate-watch": "orchestration",
    "status": "reporting",
    "report": "reporting",
    "triage": "reporting",
    "check": "governance",
    "docs-check": "governance",
    "hygiene": "governance",
    "security": "security",
    "ship": "release",
    "release": "release",
    "homebrew": "release",
    "pypi": "release",
    "release-notes": "release",
}


def _load_policy_section() -> dict[str, Any]:
    """Read audit-metrics policy section, returning an empty dict on failure."""
    try:
        payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(payload, dict):
        return {}
    section = payload.get(POLICY_KEY)
    return section if isinstance(section, dict) else {}


def _normalize_path(path_text: str) -> Path:
    """Resolve path text relative to repo root when not absolute."""
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def resolve_event_log_path() -> Path:
    """Resolve JSONL event log destination from env/policy/default."""
    env_override = str(os.environ.get("DEVCTL_AUDIT_EVENT_LOG") or "").strip()
    if env_override:
        return _normalize_path(env_override)
    policy = _load_policy_section()
    policy_path = str(policy.get("event_log_path") or "").strip()
    if policy_path:
        return _normalize_path(policy_path)
    return (REPO_ROOT / DEFAULT_EVENT_LOG).resolve()


def _bool_env(name: str, *, default: bool) -> bool:
    raw = str(os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _normalize_source_bucket(raw: str) -> str:
    value = raw.strip().lower()
    return value if value in SOURCE_BUCKETS else "script_only"


def _infer_area(command: str) -> str:
    return AREA_BY_COMMAND.get(command, "misc")


def _normalized_returncode(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1


def _default_step(command: str, args: Any) -> str:
    profile = getattr(args, "profile", None)
    if command == "check" and isinstance(profile, str) and profile.strip():
        return f"devctl:{command}:{profile.strip()}"
    return f"devctl:{command}"


def build_audit_event_payload(
    *,
    command: str,
    args: Any,
    returncode: Any,
    duration_seconds: float,
    argv: list[str] | None = None,
) -> dict[str, Any]:
    """Build one normalized audit event payload."""
    normalized_rc = _normalized_returncode(returncode)
    source_bucket = _normalize_source_bucket(
        str(os.environ.get("DEVCTL_EXECUTION_SOURCE") or "script_only")
    )
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "cycle_id": str(os.environ.get("DEVCTL_AUDIT_CYCLE_ID") or "local"),
        "area": str(os.environ.get("DEVCTL_AUDIT_AREA") or _infer_area(command)),
        "step": str(os.environ.get("DEVCTL_AUDIT_STEP") or _default_step(command, args)),
        "command": command,
        "execution_source": source_bucket,
        "actor": str(os.environ.get("DEVCTL_EXECUTION_ACTOR") or "script"),
        "automated": _bool_env("DEVCTL_AUDIT_AUTOMATED", default=True),
        "success": normalized_rc == 0,
        "returncode": normalized_rc,
        "duration_seconds": round(max(float(duration_seconds), 0.0), 2),
        "retries": int(os.environ.get("DEVCTL_AUDIT_RETRIES") or "0"),
        "manual_reason": (
            str(os.environ.get("DEVCTL_MANUAL_REASON")).strip()
            if os.environ.get("DEVCTL_MANUAL_REASON")
            else None
        ),
        "repeated_workaround": _bool_env("DEVCTL_REPEATED_WORKAROUND", default=False),
    }
    if argv:
        payload["argv"] = argv
    return payload


def emit_devctl_audit_event(
    *,
    command: str,
    args: Any,
    returncode: Any,
    duration_seconds: float,
    argv: list[str] | None = None,
) -> None:
    """Append one audit event unless disabled."""
    if _bool_env("DEVCTL_AUDIT_DISABLE", default=False):
        return
    payload = build_audit_event_payload(
        command=command,
        args=args,
        returncode=returncode,
        duration_seconds=duration_seconds,
        argv=argv,
    )
    output_path = resolve_event_log_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")
