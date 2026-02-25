"""Summary extractors for autonomy report source artifacts."""

from __future__ import annotations

from typing import Any

from .numeric import to_int, to_optional_float


def _summarize_triage(payload: dict[str, Any]) -> dict[str, Any]:
    attempts = payload.get("attempts")
    attempt_count = len(attempts) if isinstance(attempts, list) else 0
    return {
        "reason": str(payload.get("reason") or "unknown"),
        "unresolved_count": to_int(payload.get("unresolved_count"), default=0),
        "attempt_count": attempt_count,
        "mode": str(payload.get("mode") or "unknown"),
        "ok": bool(payload.get("ok", False)),
    }


def _summarize_mutation(payload: dict[str, Any]) -> dict[str, Any]:
    score = to_optional_float(payload.get("last_score"), default=None)
    threshold = to_optional_float(payload.get("threshold"), default=None)
    gap = None
    if score is not None and threshold is not None:
        gap = round((score - threshold) * 100.0, 3)
    return {
        "reason": str(payload.get("reason") or "unknown"),
        "last_score_pct": None if score is None else round(score * 100.0, 3),
        "threshold_pct": None if threshold is None else round(threshold * 100.0, 3),
        "score_gap_pct": gap,
        "ok": bool(payload.get("ok", False)),
    }


def _summarize_autonomy(payload: dict[str, Any]) -> dict[str, Any]:
    rounds = payload.get("rounds")
    unresolved_by_round: list[int] = []
    if isinstance(rounds, list):
        for row in rounds:
            if isinstance(row, dict):
                unresolved_by_round.append(
                    to_int(row.get("unresolved_count"), default=0)
                )
    return {
        "reason": str(payload.get("reason") or "unknown"),
        "resolved": bool(payload.get("resolved", False)),
        "rounds_completed": to_int(
            payload.get("rounds_completed"), default=len(unresolved_by_round)
        ),
        "tasks_completed": to_int(payload.get("tasks_completed"), default=0),
        "unresolved_by_round": unresolved_by_round,
        "ok": bool(payload.get("ok", False)),
    }


def _summarize_orchestrate(payload: dict[str, Any]) -> dict[str, Any]:
    errors = payload.get("errors")
    warnings = payload.get("warnings")
    return {
        "ok": bool(payload.get("ok", False)),
        "errors_count": len(errors) if isinstance(errors, list) else 0,
        "warnings_count": len(warnings) if isinstance(warnings, list) else 0,
        "stale_agent_count": to_int(payload.get("stale_agent_count"), default=0),
        "overdue_instruction_ack_count": to_int(
            payload.get("overdue_instruction_ack_count"), default=0
        ),
    }


def _summarize_phone(payload: dict[str, Any]) -> dict[str, Any]:
    controller = (
        payload.get("controller") if isinstance(payload.get("controller"), dict) else {}
    )
    terminal = (
        payload.get("terminal") if isinstance(payload.get("terminal"), dict) else {}
    )
    return {
        "reason": str(payload.get("reason") or "unknown"),
        "mode": str(controller.get("mode_effective") or "unknown"),
        "rounds_completed": to_int(controller.get("rounds_completed"), default=0),
        "tasks_completed": to_int(controller.get("tasks_completed"), default=0),
        "trace_lines": (
            len(terminal.get("trace") or [])
            if isinstance(terminal.get("trace"), list)
            else 0
        ),
    }


def summarize_source(key: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Return the summary payload for one source type."""
    if key == "triage_loop":
        return _summarize_triage(payload)
    if key == "mutation_loop":
        return _summarize_mutation(payload)
    if key == "autonomy_loop":
        return _summarize_autonomy(payload)
    if key in {"orchestrate_status", "orchestrate_watch"}:
        return _summarize_orchestrate(payload)
    return _summarize_phone(payload)
