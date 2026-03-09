"""Read the latest repo-visible phone/control snapshot for the Operator Console."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from dev.scripts.devctl.mobile_status_views import compact_view as mobile_compact_view
from dev.scripts.devctl.phone_status_views import compact_view
from dev.scripts.devctl.review_channel import DEFAULT_BRIDGE_REL, DEFAULT_REVIEW_CHANNEL_REL
from dev.scripts.devctl.review_channel_state import (
    DEFAULT_REVIEW_STATUS_DIR_REL,
    refresh_status_snapshot,
)
from .value_coercion import safe_int, safe_text

DEFAULT_MOBILE_STATUS_REL = "dev/reports/mobile/latest/full.json"
DEFAULT_PHONE_STATUS_REL = "dev/reports/autonomy/queue/phone/latest.json"
_CACHE_LOCK = Lock()
_CACHE: dict[
    str,
    tuple[tuple[int | None, int | None, int | None, int | None], "PhoneControlSnapshot"],
] = {}


@dataclass(frozen=True)
class PhoneControlSnapshot:
    """Compact phone/control state derived from the latest phone-status payload."""

    available: bool
    phase: str
    reason: str
    mode_effective: str
    unresolved_count: int
    risk: str
    latest_working_branch: str | None
    next_actions: tuple[str, ...]
    warnings_count: int
    errors_count: int
    age_minutes: float | None
    source_run_url: str | None
    review_bridge_state: str | None = None
    current_instruction: str | None = None
    last_worktree_hash: str | None = None
    note: str | None = None


def load_phone_control_snapshot(repo_root: Path) -> PhoneControlSnapshot:
    """Return a compact read-only phone/control snapshot for the current repo."""
    if not repo_root.exists():
        return _unavailable("repo root is unavailable")

    signature = _signature(repo_root)
    cache_key = str(repo_root.resolve())
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None and cached[0] == signature:
            return cached[1]

    mobile_projection_path = repo_root / DEFAULT_MOBILE_STATUS_REL
    mobile_projection_note: str | None = None
    if mobile_projection_path.exists():
        snapshot = _load_snapshot_from_mobile_projection(mobile_projection_path)
        if snapshot.available:
            with _CACHE_LOCK:
                _CACHE[cache_key] = (signature, snapshot)
            return snapshot
        mobile_projection_note = snapshot.note

    payload_path = repo_root / DEFAULT_PHONE_STATUS_REL
    if not payload_path.exists():
        snapshot = _unavailable("no phone-status artifact has been written yet")
        with _CACHE_LOCK:
            _CACHE[cache_key] = (signature, snapshot)
        return snapshot

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        snapshot = _unavailable("phone-status JSON is invalid")
        with _CACHE_LOCK:
            _CACHE[cache_key] = (signature, snapshot)
        return snapshot
    except OSError as exc:
        snapshot = _unavailable(f"phone-status could not be read: {exc}")
        with _CACHE_LOCK:
            _CACHE[cache_key] = (signature, snapshot)
        return snapshot

    if not isinstance(payload, dict):
        snapshot = _unavailable("phone-status payload is not a JSON object")
        with _CACHE_LOCK:
            _CACHE[cache_key] = (signature, snapshot)
        return snapshot

    try:
        compact = compact_view(payload)
    except Exception as exc:  # pragma: no cover - broad-except: allow reason=projection failures must degrade to unavailable snapshot data
        snapshot = _unavailable(f"phone-status projection failed: {exc}")
        with _CACHE_LOCK:
            _CACHE[cache_key] = (signature, snapshot)
        return snapshot

    mobile_compact, mobile_note = _load_mobile_compact(repo_root, payload)
    combined_note = mobile_note or mobile_projection_note
    if mobile_note and mobile_projection_note and mobile_note != mobile_projection_note:
        combined_note = f"{mobile_projection_note} {mobile_note}"

    next_actions = compact.get("next_actions")
    if not isinstance(next_actions, list):
        next_actions = []
    age_minutes = None
    try:
        age_seconds = max(0.0, time.time() - payload_path.stat().st_mtime)
        age_minutes = age_seconds / 60.0
    except OSError:
        age_minutes = None

    snapshot = _build_snapshot(
        compact=compact,
        mobile_compact=mobile_compact,
        age_minutes=age_minutes,
        note=combined_note,
    )
    with _CACHE_LOCK:
        _CACHE[cache_key] = (signature, snapshot)
    return snapshot


def _load_snapshot_from_mobile_projection(mobile_projection_path: Path) -> PhoneControlSnapshot:
    try:
        payload = json.loads(mobile_projection_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _unavailable("mobile-status projection JSON is invalid")
    except OSError as exc:
        return _unavailable(f"mobile-status projection could not be read: {exc}")

    if not isinstance(payload, dict):
        return _unavailable("mobile-status projection is not a JSON object")

    controller_payload = payload.get("controller_payload")
    if not isinstance(controller_payload, dict):
        return _unavailable("mobile-status projection is missing controller_payload")

    try:
        compact = compact_view(controller_payload)
        mobile_compact = mobile_compact_view(payload)
    except Exception as exc:  # pragma: no cover - broad-except: allow reason=projection helper failures must surface as unavailable mobile status
        return _unavailable(f"mobile-status projection failed: {exc}")

    try:
        age_seconds = max(0.0, time.time() - mobile_projection_path.stat().st_mtime)
        age_minutes = age_seconds / 60.0
    except OSError:
        age_minutes = None

    return _build_snapshot(
        compact=compact,
        mobile_compact=mobile_compact,
        age_minutes=age_minutes,
        note="Using repo-owned mobile-status projection bundle.",
    )


def _build_snapshot(
    *,
    compact: dict[str, object],
    mobile_compact: dict[str, object],
    age_minutes: float | None,
    note: str | None,
) -> PhoneControlSnapshot:
    next_actions = compact.get("next_actions")
    if not isinstance(next_actions, list):
        next_actions = []
    return PhoneControlSnapshot(
        available=True,
        phase=safe_text(compact.get("phase")) or "unknown",
        reason=safe_text(compact.get("reason")) or "unknown",
        mode_effective=safe_text(compact.get("mode_effective")) or "unknown",
        unresolved_count=safe_int(compact.get("unresolved_count")),
        risk=safe_text(compact.get("risk")) or "unknown",
        latest_working_branch=safe_text(compact.get("latest_working_branch")),
        next_actions=tuple(
            text for text in (safe_text(row) for row in next_actions) if text
        ),
        warnings_count=safe_int(compact.get("warnings_count")),
        errors_count=safe_int(compact.get("errors_count")),
        age_minutes=age_minutes,
        source_run_url=safe_text(compact.get("source_run_url")),
        review_bridge_state=safe_text(mobile_compact.get("review_bridge_state")),
        current_instruction=safe_text(mobile_compact.get("current_instruction")),
        last_worktree_hash=safe_text(mobile_compact.get("last_worktree_hash")),
        note=note,
    )


def _unavailable(note: str) -> PhoneControlSnapshot:
    return PhoneControlSnapshot(
        available=False,
        phase="offline",
        reason="unavailable",
        mode_effective="unknown",
        unresolved_count=0,
        risk="unknown",
        latest_working_branch=None,
        next_actions=(),
        warnings_count=0,
        errors_count=0,
        age_minutes=None,
        source_run_url=None,
        review_bridge_state=None,
        current_instruction=None,
        last_worktree_hash=None,
        note=note,
    )


def _load_mobile_compact(
    repo_root: Path,
    phone_payload: dict[str, object],
) -> tuple[dict[str, object], str | None]:
    review_channel_path = repo_root / DEFAULT_REVIEW_CHANNEL_REL
    bridge_path = repo_root / DEFAULT_BRIDGE_REL
    status_root = repo_root / DEFAULT_REVIEW_STATUS_DIR_REL
    if not review_channel_path.exists() or not bridge_path.exists():
        return {}, "Review bridge not available; showing phone-status fallback."
    try:
        status_snapshot = refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=status_root,
        )
        review_payload = json.loads(
            Path(status_snapshot.projection_paths.full_path).read_text(encoding="utf-8")
        )
        compact_payload = mobile_compact_view(
            {
                "controller_payload": phone_payload,
                "review_payload": review_payload,
            }
        )
    except Exception as exc:  # pragma: no cover - broad-except: allow reason=relay fallback must return an explanatory warning instead of crashing UI
        return {}, f"Mobile relay fallback active: {exc}"
    warning_note = None
    if status_snapshot.warnings:
        warning_note = "; ".join(status_snapshot.warnings[:2])
    return compact_payload, warning_note


def _signature(repo_root: Path) -> tuple[int | None, int | None, int | None, int | None]:
    return (
        _mtime_ns(repo_root / DEFAULT_MOBILE_STATUS_REL),
        _mtime_ns(repo_root / DEFAULT_PHONE_STATUS_REL),
        _mtime_ns(repo_root / DEFAULT_REVIEW_CHANNEL_REL),
        _mtime_ns(repo_root / DEFAULT_BRIDGE_REL),
    )


def _mtime_ns(path: Path) -> int | None:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None
