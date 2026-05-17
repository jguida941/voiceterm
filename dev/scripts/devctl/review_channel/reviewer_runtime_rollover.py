"""Rollover-state helpers for the typed reviewer-runtime contract."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from ..runtime.reviewer_runtime_models import ReviewerRolloverState
from .handoff import observe_rollover_ack_state


def resolve_reviewer_rollover_state(
    *,
    rollover_dir: Path | None,
    bridge_text: str | None,
    attention: Mapping[str, object] | None,
    override: Mapping[str, object] | None,
) -> ReviewerRolloverState:
    """Resolve rollover metadata from override, persisted bundle, and bridge ACKs."""
    rollover_id = ""
    trigger = ""
    ack_pending = False
    override_mapping = override if isinstance(override, Mapping) else {}
    handoff_bundle = override_mapping.get("handoff_bundle")
    if isinstance(handoff_bundle, Mapping):
        rollover_id = str(handoff_bundle.get("rollover_id") or "").strip()
    handoff_ack = override_mapping.get("handoff_ack_observed")
    if isinstance(handoff_ack, Mapping) and handoff_ack:
        ack_pending = not all(bool(value) for value in handoff_ack.values())
    if not trigger:
        trigger = str(
            override_mapping.get("rollover_trigger")
            or override_mapping.get("attention_status")
            or ""
        ).strip()

    if not rollover_id or not trigger:
        persisted = _load_latest_rollover_payload(rollover_dir)
        if persisted:
            rollover_id = rollover_id or str(persisted.get("rollover_id") or "").strip()
            trigger = trigger or str(persisted.get("trigger") or "").strip()

    if rollover_id and not isinstance(handoff_ack, Mapping) and bridge_text:
        observed = observe_rollover_ack_state(
            bridge_text=bridge_text,
            rollover_id=rollover_id,
        )
        if observed:
            ack_pending = not all(bool(value) for value in observed.values())

    if not trigger:
        trigger = str((attention or {}).get("status") or "").strip()
    return ReviewerRolloverState(
        rollover_id=rollover_id,
        ack_pending=ack_pending,
        trigger=trigger,
    )


def _load_latest_rollover_payload(
    rollover_dir: Path | None,
) -> Mapping[str, object]:
    if not isinstance(rollover_dir, Path) or not rollover_dir.exists():
        return {}
    for handoff_path in sorted(rollover_dir.glob("*/handoff.json"), reverse=True):
        try:
            payload = json.loads(handoff_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return payload
    return {}
