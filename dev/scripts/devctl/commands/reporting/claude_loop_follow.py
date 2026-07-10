"""Follow-loop timing for agent-loop reporting commands."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ...runtime.value_coercion import coerce_mapping


SnapshotBuilder = Callable[[Any], dict[str, Any]]
SnapshotRenderer = Callable[[Any, dict[str, Any]], str]


def run_follow(
    args: Any,
    *,
    build_snapshot: SnapshotBuilder,
    render_snapshot: SnapshotRenderer,
) -> int:
    interval_arg = getattr(args, "interval", "typed")
    typed_interval = uses_typed_interval(interval_arg)
    interval_seconds = parse_interval_seconds(interval_arg)
    max_snapshots = getattr(args, "max_follow_snapshots", None)
    count = 0
    try:
        while True:
            count += 1
            payload = build_snapshot(args)
            if typed_interval:
                interval_seconds = payload_loop_interval_seconds(payload)
            payload["follow"] = dict(
                enabled=True,
                snapshot_seq=count,
                interval_seconds=interval_seconds,
                interval_source="agent_loop_decision"
                if typed_interval
                else "cli_argument",
            )
            print(render_snapshot(args, payload))
            print("", flush=True)
            if max_snapshots is not None and count >= int(max_snapshots):
                return 0
            if payload_loop_should_stop(payload):
                return 0
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        return 0


def parse_interval_seconds(raw: object) -> float:
    text = str(raw or "5").strip().lower()
    if text == "typed":
        return 5.0
    multiplier = 1.0
    if text.endswith("ms"):
        multiplier = 0.001
        text = text[:-2]
    elif text.endswith("s"):
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 60.0
        text = text[:-1]
    try:
        value = float(text)
    except ValueError:
        value = 5.0
    return max(0.1, value * multiplier)


def uses_typed_interval(raw: object) -> bool:
    return str(raw or "").strip().lower() in {"", "typed", "auto"}


def payload_loop_interval_seconds(payload: dict[str, Any]) -> float:
    decision = coerce_mapping(payload.get("agent_loop_decision"))
    value = decision.get("recommended_cadence_seconds")
    try:
        seconds = float(value or 0)
    except (TypeError, ValueError):
        seconds = 0.0
    if seconds <= 0:
        return 5.0
    return max(0.1, seconds)


def payload_loop_should_stop(payload: dict[str, Any]) -> bool:
    decision = coerce_mapping(payload.get("agent_loop_decision"))
    return str(decision.get("loop_mode") or "") == "stopped"


__all__ = ["run_follow"]
