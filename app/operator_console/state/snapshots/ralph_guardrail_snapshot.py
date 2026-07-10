"""Read the latest Ralph guardrail loop snapshot for the Operator Console."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from dev.scripts.devctl.repo_packs import VOICETERM_PATH_CONFIG

from ..core.value_coercion import safe_int, safe_text

# Backward-compat alias — canonical value lives in VOICETERM_PATH_CONFIG.
DEFAULT_RALPH_REPORT_REL = VOICETERM_PATH_CONFIG.ralph_report_rel
_CACHE_LOCK = Lock()
_CACHE: dict[str, tuple[int | None, "RalphGuardrailSnapshot"]] = {}


@dataclass(frozen=True)
class RalphGuardrailSnapshot:
    """Compact Ralph guardrail loop state derived from the latest report."""

    available: bool
    phase: str  # "idle", "running", "complete", "escalated"
    attempt: int
    max_attempts: int
    total_findings: int
    fixed_count: int
    false_positive_count: int
    pending_count: int
    fix_rate_pct: float
    by_architecture: tuple[tuple[str, int, int], ...]  # (arch, total, fixed)
    by_severity: tuple[tuple[str, int, int], ...]  # (severity, total, fixed)
    last_run_timestamp: str | None
    branch: str | None
    approval_mode: str | None
    note: str | None = None


def load_ralph_guardrail_snapshot(repo_root: Path) -> RalphGuardrailSnapshot:
    """Return a compact read-only Ralph guardrail snapshot for the current repo."""
    if not repo_root.exists():
        return _unavailable("repo root is unavailable")

    report_path = repo_root / DEFAULT_RALPH_REPORT_REL
    signature = _mtime_ns(report_path)
    cache_key = str(repo_root.resolve())
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None and cached[0] == signature:
            return cached[1]

    if not report_path.exists():
        snapshot = _unavailable("no Ralph report has been written yet")
        with _CACHE_LOCK:
            _CACHE[cache_key] = (signature, snapshot)
        return snapshot

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        snapshot = _unavailable("Ralph report JSON is invalid")
        with _CACHE_LOCK:
            _CACHE[cache_key] = (signature, snapshot)
        return snapshot
    except OSError as exc:
        snapshot = _unavailable(f"Ralph report could not be read: {exc}")
        with _CACHE_LOCK:
            _CACHE[cache_key] = (signature, snapshot)
        return snapshot

    if not isinstance(payload, dict):
        snapshot = _unavailable("Ralph report payload is not a JSON object")
        with _CACHE_LOCK:
            _CACHE[cache_key] = (signature, snapshot)
        return snapshot

    snapshot = _project_snapshot(payload)
    with _CACHE_LOCK:
        _CACHE[cache_key] = (signature, snapshot)
    return snapshot


def _project_snapshot(payload: dict[str, object]) -> RalphGuardrailSnapshot:
    """Project a Ralph report JSON payload into a frozen snapshot."""
    total = safe_int(payload.get("total_findings"))
    fixed = safe_int(payload.get("fixed_count"))
    false_pos = safe_int(payload.get("false_positive_count"))
    pending = safe_int(payload.get("pending_count"))

    fix_rate = 0.0
    if total > 0:
        fix_rate = round((fixed / total) * 100.0, 1)

    by_arch = _parse_breakdown(payload.get("by_architecture"))
    by_sev = _parse_breakdown(payload.get("by_severity"))

    return RalphGuardrailSnapshot(
        available=True,
        phase=safe_text(payload.get("phase")) or "idle",
        attempt=safe_int(payload.get("attempt")),
        max_attempts=safe_int(payload.get("max_attempts")),
        total_findings=total,
        fixed_count=fixed,
        false_positive_count=false_pos,
        pending_count=pending,
        fix_rate_pct=fix_rate,
        by_architecture=by_arch,
        by_severity=by_sev,
        last_run_timestamp=safe_text(payload.get("last_run_timestamp")),
        branch=safe_text(payload.get("branch")),
        approval_mode=safe_text(payload.get("approval_mode")),
        note=safe_text(payload.get("note")),
    )


def _parse_breakdown(
    raw: object,
) -> tuple[tuple[str, int, int], ...]:
    """Parse a list of {name, total, fixed} dicts into a tuple of triples."""
    if not isinstance(raw, list):
        return ()
    result: list[tuple[str, int, int]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        name = safe_text(entry.get("name")) or "unknown"
        total = safe_int(entry.get("total"))
        fixed = safe_int(entry.get("fixed"))
        result.append((name, total, fixed))
    return tuple(result)


def _unavailable(note: str) -> RalphGuardrailSnapshot:
    return RalphGuardrailSnapshot(
        available=False,
        phase="idle",
        attempt=0,
        max_attempts=0,
        total_findings=0,
        fixed_count=0,
        false_positive_count=0,
        pending_count=0,
        fix_rate_pct=0.0,
        by_architecture=(),
        by_severity=(),
        last_run_timestamp=None,
        branch=None,
        approval_mode=None,
        note=note,
    )


def _mtime_ns(path: Path) -> int | None:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None
