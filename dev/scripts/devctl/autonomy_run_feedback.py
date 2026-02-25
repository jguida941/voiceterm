"""Closed-loop feedback sizing helpers for `devctl swarm_run`."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .numeric import to_int

NO_SIGNAL_TRIAGE_REASONS = {"gh_unreachable_local_non_blocking", "dry-run"}


def _normalized_reason(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text or "unknown"


def _load_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, str(exc)
    except json.JSONDecodeError as exc:
        return None, f"invalid json ({exc})"
    if not isinstance(payload, dict):
        return None, "expected object json"
    return payload, None


def _downshift_target(*, current: int, minimum: int, factor: float) -> int:
    candidate = int(math.floor(float(current) * factor))
    if candidate >= current:
        candidate = current - 1
    return max(minimum, candidate)


def _upshift_target(*, current: int, maximum: int, factor: float) -> int:
    candidate = int(math.ceil(float(current) * factor))
    if candidate <= current:
        candidate = current + 1
    return min(maximum, candidate)


def _worker_rows(swarm_payload: dict[str, Any]) -> list[dict[str, Any]]:
    agents = swarm_payload.get("agents")
    if not isinstance(agents, list):
        return []
    rows: list[dict[str, Any]] = []
    for row in agents:
        if not isinstance(row, dict):
            continue
        if str(row.get("agent") or "").strip().upper() == "AGENT-REVIEW":
            continue
        rows.append(row)
    return rows


def _worker_metrics(worker_row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    fallback_reason = _normalized_reason(worker_row.get("reason"))
    resolved = bool(worker_row.get("resolved"))
    unresolved = 0
    triage_reasons: list[str] = []

    report_json_raw = str(worker_row.get("report_json") or "").strip()
    if report_json_raw:
        report_path = Path(report_json_raw)
        if report_path.exists():
            payload, error = _load_json_object(report_path)
            if error:
                warnings.append(f"{report_path}: {error}")
            elif payload is not None:
                resolved = bool(payload.get("resolved", resolved))
                rounds = payload.get("rounds")
                if isinstance(rounds, list):
                    for round_row in rounds:
                        if not isinstance(round_row, dict):
                            continue
                        triage_reasons.append(
                            _normalized_reason(round_row.get("triage_reason"))
                        )
                        unresolved = to_int(
                            round_row.get("unresolved_count"), default=unresolved
                        )
                if not triage_reasons:
                    triage_reasons.append(_normalized_reason(payload.get("reason")))
        else:
            warnings.append(f"{report_path}: report json missing")

    if not triage_reasons:
        triage_reasons = [fallback_reason]

    last_reason = triage_reasons[-1]
    has_signal = any(
        reason not in NO_SIGNAL_TRIAGE_REASONS for reason in triage_reasons
    )
    return {
        "resolved": resolved,
        "unresolved_count": unresolved,
        "last_reason": last_reason,
        "has_signal": has_signal,
    }, warnings


def _cycle_feedback_metrics(swarm_payload: dict[str, Any]) -> dict[str, Any]:
    summary = swarm_payload.get("summary")
    summary = summary if isinstance(summary, dict) else {}

    selected_agents = to_int(summary.get("selected_agents"), default=0)
    worker_rows = _worker_rows(swarm_payload)
    worker_agents = len(worker_rows)
    if worker_agents <= 0:
        worker_agents = to_int(summary.get("worker_agents"), default=0)

    signal_workers = 0
    resolved_workers = 0
    unresolved_total = 0
    reason_counts: dict[str, int] = {}
    warnings: list[str] = []

    for row in worker_rows:
        metrics, row_warnings = _worker_metrics(row)
        warnings.extend(row_warnings)
        if bool(metrics.get("has_signal")):
            signal_workers += 1
        if bool(metrics.get("resolved")):
            resolved_workers += 1
        unresolved_total += to_int(metrics.get("unresolved_count"), default=0)
        reason = _normalized_reason(metrics.get("last_reason"))
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    no_signal_workers = max(worker_agents - signal_workers, 0)
    no_signal_cycle = worker_agents > 0 and signal_workers == 0
    avg_unresolved = (
        round(float(unresolved_total) / float(worker_agents), 3)
        if worker_agents > 0
        else 0.0
    )

    return {
        "selected_agents": selected_agents,
        "worker_agents": worker_agents,
        "signal_workers": signal_workers,
        "no_signal_workers": no_signal_workers,
        "no_signal_cycle": no_signal_cycle,
        "resolved_workers": resolved_workers,
        "unresolved_total": unresolved_total,
        "avg_unresolved_per_worker": avg_unresolved,
        "triage_reason_counts": reason_counts,
        "warnings": warnings,
    }


def build_feedback_state(
    args, *, continuous_enabled: bool
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Build mutable sizing state from CLI args."""
    warnings: list[str] = []
    errors: list[str] = []

    feedback_requested = bool(getattr(args, "feedback_sizing", False))
    enabled = feedback_requested and continuous_enabled

    stall_rounds = to_int(getattr(args, "feedback_stall_rounds", 2), default=2)
    no_signal_rounds = to_int(
        getattr(args, "feedback_no_signal_rounds", 2), default=2
    )
    downshift_factor = float(getattr(args, "feedback_downshift_factor", 0.5))
    upshift_rounds = to_int(getattr(args, "feedback_upshift_rounds", 2), default=2)
    upshift_factor = float(getattr(args, "feedback_upshift_factor", 1.25))

    if feedback_requested and not continuous_enabled:
        warnings.append("feedback sizing ignored because --continuous is disabled")

    if feedback_requested:
        if stall_rounds < 1:
            errors.append("--feedback-stall-rounds must be >= 1")
        if no_signal_rounds < 1:
            errors.append("--feedback-no-signal-rounds must be >= 1")
        if upshift_rounds < 1:
            errors.append("--feedback-upshift-rounds must be >= 1")
        if downshift_factor <= 0.0 or downshift_factor >= 1.0:
            errors.append("--feedback-downshift-factor must be > 0 and < 1")
        if upshift_factor <= 1.0:
            errors.append("--feedback-upshift-factor must be > 1")

    min_agents = max(1, to_int(getattr(args, "min_agents", 1), default=1))
    max_agents = max(min_agents, to_int(getattr(args, "max_agents", 20), default=20))
    configured_agents = getattr(args, "agents", None)
    next_agents: int | None = None
    if configured_agents is not None:
        configured_count = max(1, to_int(configured_agents, default=1))
        min_agents = min(min_agents, configured_count)
        max_agents = max(max_agents, configured_count)
        if enabled:
            next_agents = configured_count

    state = {
        "enabled": enabled,
        "settings": {
            "stall_rounds": stall_rounds,
            "no_signal_rounds": no_signal_rounds,
            "downshift_factor": downshift_factor,
            "upshift_rounds": upshift_rounds,
            "upshift_factor": upshift_factor,
        },
        "min_agents": min_agents,
        "max_agents": max_agents,
        "next_agents": next_agents,
        "no_signal_streak": 0,
        "stall_streak": 0,
        "improve_streak": 0,
        "last_unresolved_total": None,
        "history": [],
    }
    return state, warnings, errors


def update_feedback_state(
    state: dict[str, Any], swarm_payload: dict[str, Any]
) -> dict[str, Any]:
    """Update feedback state from one completed swarm payload."""
    metrics = _cycle_feedback_metrics(swarm_payload)
    selected_agents = to_int(metrics.get("selected_agents"), default=0)
    if selected_agents <= 0:
        selected_agents = to_int(state.get("next_agents"), default=0)
    if selected_agents <= 0:
        selected_agents = to_int(state.get("min_agents"), default=1)

    enabled = bool(state.get("enabled"))
    next_agents: int | None = state.get("next_agents")
    decision = "disabled"
    trigger: str | None = None
    delta_unresolved: int | None = None

    unresolved_total = to_int(metrics.get("unresolved_total"), default=0)
    previous_unresolved = state.get("last_unresolved_total")
    if isinstance(previous_unresolved, int):
        delta_unresolved = unresolved_total - previous_unresolved

    if bool(metrics.get("no_signal_cycle")):
        state["no_signal_streak"] = to_int(state.get("no_signal_streak"), default=0) + 1
    else:
        state["no_signal_streak"] = 0

    if isinstance(previous_unresolved, int):
        if unresolved_total < previous_unresolved:
            state["improve_streak"] = to_int(state.get("improve_streak"), default=0) + 1
            state["stall_streak"] = 0
        else:
            state["stall_streak"] = to_int(state.get("stall_streak"), default=0) + 1
            state["improve_streak"] = 0
    else:
        state["stall_streak"] = 0
        state["improve_streak"] = 0
    state["last_unresolved_total"] = unresolved_total

    if enabled:
        settings = state.get("settings") if isinstance(state.get("settings"), dict) else {}
        min_agents = to_int(state.get("min_agents"), default=1)
        max_agents = max(min_agents, to_int(state.get("max_agents"), default=min_agents))
        current_agents = max(min_agents, min(max_agents, selected_agents))
        no_signal_rounds = to_int(settings.get("no_signal_rounds"), default=2)
        stall_rounds = to_int(settings.get("stall_rounds"), default=2)
        upshift_rounds = to_int(settings.get("upshift_rounds"), default=2)
        downshift_factor = float(settings.get("downshift_factor") or 0.5)
        upshift_factor = float(settings.get("upshift_factor") or 1.25)

        next_agents = current_agents
        decision = "hold"
        no_signal_streak = to_int(state.get("no_signal_streak"), default=0)
        stall_streak = to_int(state.get("stall_streak"), default=0)
        improve_streak = to_int(state.get("improve_streak"), default=0)

        if no_signal_streak >= no_signal_rounds:
            trigger = "no_signal_streak"
            next_agents = _downshift_target(
                current=current_agents, minimum=min_agents, factor=downshift_factor
            )
            if next_agents < current_agents:
                decision = "downshift"
                state["no_signal_streak"] = 0
        elif stall_streak >= stall_rounds:
            trigger = "stall_streak"
            next_agents = _downshift_target(
                current=current_agents, minimum=min_agents, factor=downshift_factor
            )
            if next_agents < current_agents:
                decision = "downshift"
                state["stall_streak"] = 0
        elif (
            improve_streak >= upshift_rounds
            and to_int(metrics.get("signal_workers"), default=0) > 0
            and unresolved_total > 0
        ):
            trigger = "improve_streak"
            next_agents = _upshift_target(
                current=current_agents, maximum=max_agents, factor=upshift_factor
            )
            if next_agents > current_agents:
                decision = "upshift"
                state["improve_streak"] = 0

        state["next_agents"] = int(next_agents)

    row = {
        "enabled": enabled,
        "selected_agents": selected_agents,
        "worker_agents": to_int(metrics.get("worker_agents"), default=0),
        "signal_workers": to_int(metrics.get("signal_workers"), default=0),
        "no_signal_workers": to_int(metrics.get("no_signal_workers"), default=0),
        "no_signal_cycle": bool(metrics.get("no_signal_cycle")),
        "resolved_workers": to_int(metrics.get("resolved_workers"), default=0),
        "unresolved_total": unresolved_total,
        "delta_unresolved": delta_unresolved,
        "avg_unresolved_per_worker": metrics.get("avg_unresolved_per_worker"),
        "triage_reason_counts": metrics.get("triage_reason_counts", {}),
        "decision": decision,
        "trigger": trigger,
        "next_agents": next_agents,
        "no_signal_streak": to_int(state.get("no_signal_streak"), default=0),
        "stall_streak": to_int(state.get("stall_streak"), default=0),
        "improve_streak": to_int(state.get("improve_streak"), default=0),
        "warnings": metrics.get("warnings", []),
    }
    history = state.get("history")
    if isinstance(history, list):
        history.append(row)
    return row


def summarize_feedback_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return report-safe summary from mutable feedback state."""
    history = state.get("history") if isinstance(state.get("history"), list) else []
    return {
        "enabled": bool(state.get("enabled")),
        "min_agents": to_int(state.get("min_agents"), default=1),
        "max_agents": to_int(state.get("max_agents"), default=1),
        "next_agents": state.get("next_agents"),
        "settings": state.get("settings", {}),
        "history": history,
    }
