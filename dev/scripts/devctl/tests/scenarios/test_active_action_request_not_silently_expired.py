"""Scenario: an action-request packet that the controller has selected
as the active piece of work for some actor must not be sitting past
its expires_at_utc. If a selected packet has expired, the controller
must stop selecting it (or surface a typed blocker that names the
expiry), not just keep pointing the actor at expired work.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


def _run_sync_status() -> dict:
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "review-channel",
            "--action", "sync-status",
            "--terminal", "none",
            "--format", "json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[:300]
    return json.loads(result.stdout)


def _packet_by_id(packets: list, packet_id: str) -> dict | None:
    for p in packets:
        if isinstance(p, dict) and str(p.get("packet_id") or "") == packet_id:
            return p
    return None


def _parse_utc(text: str) -> datetime | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def test_selected_active_packet_must_not_be_expired():
    """Walk the controller-selected active packet pointers (per-actor
    attention_packet_id and canonical_active_packets) and assert that
    each named packet is either not yet past its expires_at_utc or
    has no expiry at all. A selected expired packet means the system
    keeps directing an actor at work that has already aged out.
    """
    output = _run_sync_status()
    packets = output.get("packets") or []
    now = datetime.now(tz=timezone.utc)

    selected_ids: list[tuple[str, str]] = []  # (source, packet_id)
    canonical = output.get("canonical_active_packets") or {}
    if isinstance(canonical, dict):
        for actor, pid in canonical.items():
            if isinstance(pid, str) and pid.strip():
                selected_ids.append((f"canonical_active_packets[{actor}]", pid.strip()))
    agents = output.get("agents") or {}
    for actor, row in agents.items():
        if not isinstance(row, dict):
            continue
        attn = str(row.get("attention_packet_id") or "").strip()
        if attn:
            selected_ids.append((f"agents[{actor}].attention_packet_id", attn))
    decisions = output.get("agent_loop_decisions") or []
    for d in decisions:
        if not isinstance(d, dict):
            continue
        actor = str(d.get("actor_id") or "?")
        for field in ("attention_packet_id", "active_packet_id", "body_open_packet_id"):
            value = str(d.get(field) or "").strip()
            if value:
                selected_ids.append(
                    (f"agent_loop_decisions[{actor}].{field}", value)
                )

    if not selected_ids:
        pytest.skip("no active packet is currently selected for any actor")

    violations: list[dict] = []
    for source, pid in selected_ids:
        packet = _packet_by_id(packets, pid)
        if packet is None:
            continue
        expires = _parse_utc(str(packet.get("expires_at_utc") or ""))
        if expires is None:
            continue
        if expires > now:
            continue
        violations.append({
            "source": source,
            "packet_id": pid,
            "expires_at_utc": str(packet.get("expires_at_utc") or ""),
            "age_minutes_past_expiry": int((now - expires).total_seconds() / 60),
            "status": str(packet.get("status") or ""),
        })

    assert not violations, (
        "controller is selecting packets that are past their expires_at_utc:\n"
        + "\n".join(
            f"  - {v['source']} -> {v['packet_id']} "
            f"expired_at={v['expires_at_utc']!r} "
            f"({v['age_minutes_past_expiry']} min past) status={v['status']!r}"
            for v in violations[:5]
        )
    )
