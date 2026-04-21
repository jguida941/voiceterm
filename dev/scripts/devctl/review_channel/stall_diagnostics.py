"""Typed stall diagnosis for codex review-channel conductors.

Surfaces two related conditions that operators and dashboards need to
distinguish from healthy idle:

1. Conductor wedge: a task-complete event was emitted but no caller-known
   replacement session has been spawned within a bounded budget.
2. Sandbox-escalation deadlock: the codex binary emitted an escalation
   event (`is_escalation: true`) and produced no further events after it;
   under headless `--terminal none` mode this prompt cannot be answered,
   so the session sits silently waiting forever.

Both conditions are returned as one typed dataclass so a single read
can drive a typed event emission, dashboard render, or operator alert.

Replacement-session detection is explicit: the caller passes a frozenset
of `replacement_session_ids` it expects to see if the conductor was
restarted. The function does NOT walk every rollout under the root and
guess by mtime — that approach mis-clears stalls when an unrelated lane
writes a newer rollout to the shared sessions root.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ConductorStallDiagnosis:
    """One typed stall reading for a given codex conductor session."""

    session_id: str
    latest_task_complete_utc: str
    latest_escalation_utc: str
    latest_escalation_summary: str
    latest_event_utc: str
    observation_utc: str
    elapsed_seconds_since_task_complete: float
    elapsed_seconds_since_latest_escalation: float
    new_session_since_task_complete: bool
    stall_budget_seconds: float
    stalled: bool
    reason: str


def _iter_rollout_events(rollout_path: Path):
    """Yield decoded JSON event dicts from a rollout JSONL file.

    Skips empty lines and lines that fail JSON decode rather than raising,
    because rollout files can be partially written while the codex binary
    is still appending to them.
    """
    try:
        handle = rollout_path.open("r", encoding="utf-8")
    except FileNotFoundError:
        return
    try:
        for raw in handle:
            text = raw.strip()
            if not text:
                continue
            try:
                yield json.loads(text)
            except json.JSONDecodeError:
                continue
    finally:
        handle.close()


def _read_rollout_signals(rollout_path: Path) -> dict[str, str]:
    """Return latest task-complete, latest escalation, and latest-event timestamps.

    The latest-event timestamp covers ANY event in the rollout — required so
    callers can distinguish "escalation was the last thing that happened"
    (deadlock candidate) from "escalation happened, then later activity
    resumed" (recovered).

    Real codex rollout JSONL nests typed payloads under a top-level
    `{"type": "event_msg" | "response_item", "payload": {...}}` envelope; the
    `task_complete` typed payload appears as `payload.type == "task_complete"`
    and sandbox-escalation events expose `is_escalation: true` either at the
    top level (legacy/test-fixture shape) or inside `payload`. Both shapes are
    accepted so the diagnostic stays correct against production rollouts and
    the synthetic events used by focused tests.
    """
    signals = {
        "latest_task_complete_utc": "",
        "latest_escalation_utc": "",
        "latest_escalation_summary": "",
        "latest_event_utc": "",
    }
    for event in _iter_rollout_events(rollout_path):
        ts = event.get("timestamp") or event.get("ts") or ""
        if not ts:
            continue
        if ts > signals["latest_event_utc"]:
            signals["latest_event_utc"] = ts
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        event_type = (
            event.get("type")
            or event.get("event_type")
            or (payload.get("type") if payload else "")
            or ""
        )
        payload_inner_type = payload.get("type") if payload else ""
        is_task_complete = (
            event_type == "task_complete" or payload_inner_type == "task_complete"
        )
        if is_task_complete and ts > signals["latest_task_complete_utc"]:
            signals["latest_task_complete_utc"] = ts
        is_escalation = bool(event.get("is_escalation")) or bool(
            payload.get("is_escalation") if payload else False
        )
        if is_escalation and ts > signals["latest_escalation_utc"]:
            signals["latest_escalation_utc"] = ts
            summary = event.get("summary") or (payload.get("summary") if payload else "") or ""
            if isinstance(summary, str):
                signals["latest_escalation_summary"] = summary
    return signals


def _replacement_session_observed(
    rollouts_root: Path, replacement_session_ids: frozenset[str]
) -> bool:
    """Return True when any replacement_session_ids has a rollout file on disk.

    Uses explicit caller-supplied session ids rather than mtime heuristic.
    The caller (dashboard, conductor supervisor) knows which session it
    expects after a relaunch; we only confirm that file exists.
    """
    if not replacement_session_ids or not rollouts_root.exists():
        return False
    for session_id in replacement_session_ids:
        for _ in rollouts_root.rglob(f"rollout-*-{session_id}.jsonl"):
            return True
    return False


def _iso_to_unix(iso_utc: str) -> float:
    """Parse a codex rollout ISO-8601 timestamp into unix seconds.

    Returns 0.0 when input is empty or not recognized as ISO-8601.
    """
    if not iso_utc:
        return 0.0
    text = iso_utc.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return 0.0


def diagnose_conductor_stall(
    *,
    session_id: str,
    rollout_path: Path,
    rollouts_root: Path,
    observation_utc: str,
    observation_unix_seconds: float,
    stall_budget_seconds: float = 300.0,
    replacement_session_ids: frozenset[str] = frozenset(),
) -> ConductorStallDiagnosis:
    """Return a typed stall diagnosis for the given codex session.

    The session is reported as stalled when either:
    - a `task_complete` event has been emitted, no caller-supplied
      replacement session has produced a rollout file on disk, and the
      elapsed time since the task-complete exceeds stall_budget_seconds; or
    - an escalation event was the latest event in the rollout, and the
      elapsed time since that escalation exceeds stall_budget_seconds
      (covers the sandbox-escalation deadlock observed in headless
      `--terminal none` launches where the operator-approval prompt
      cannot be rendered).

    Caller passes ``replacement_session_ids`` containing the session ids
    they expect to see if the conductor was restarted. Without this set,
    no rollout walk happens — the function does NOT guess based on mtime
    of unrelated rollout files in the shared sessions root.
    """
    signals = _read_rollout_signals(rollout_path)
    new_session_observed = _replacement_session_observed(
        rollouts_root, replacement_session_ids
    )

    task_complete_iso = signals["latest_task_complete_utc"]
    escalation_iso = signals["latest_escalation_utc"]
    latest_event_iso = signals["latest_event_utc"]

    elapsed_complete = (
        max(0.0, observation_unix_seconds - _iso_to_unix(task_complete_iso))
        if task_complete_iso
        else 0.0
    )
    elapsed_escalation = (
        max(0.0, observation_unix_seconds - _iso_to_unix(escalation_iso))
        if escalation_iso
        else 0.0
    )

    escalation_is_latest_event = (
        bool(escalation_iso)
        and bool(latest_event_iso)
        and escalation_iso == latest_event_iso
    )

    if (
        escalation_is_latest_event
        and elapsed_escalation > stall_budget_seconds
    ):
        # An escalation that is the latest event in the rollout AND has
        # exceeded the budget is the canonical headless sandbox-escalation
        # deadlock, regardless of whether the session previously emitted
        # one or more task_complete events. Gating this on "no prior
        # task_complete" (the v1 shape) masked deadlocks for any long-lived
        # conductor that completed earlier work and only later wedged on
        # an unanswerable approval prompt — exactly the scenario this
        # diagnostic exists to surface.
        stalled = True
        reason = "escalation_deadlock"
    elif task_complete_iso and new_session_observed:
        stalled = False
        reason = "new_session_spawned"
    elif task_complete_iso and elapsed_complete > stall_budget_seconds:
        stalled = True
        reason = "stalled_beyond_budget"
    elif task_complete_iso:
        stalled = False
        reason = "within_budget"
    elif escalation_iso:
        stalled = False
        reason = "escalation_recent"
    else:
        stalled = False
        reason = "no_task_complete_yet"

    return ConductorStallDiagnosis(
        session_id=session_id,
        latest_task_complete_utc=task_complete_iso,
        latest_escalation_utc=escalation_iso,
        latest_escalation_summary=signals["latest_escalation_summary"],
        latest_event_utc=latest_event_iso,
        observation_utc=observation_utc,
        elapsed_seconds_since_task_complete=elapsed_complete,
        elapsed_seconds_since_latest_escalation=elapsed_escalation,
        new_session_since_task_complete=new_session_observed,
        stall_budget_seconds=stall_budget_seconds,
        stalled=stalled,
        reason=reason,
    )
