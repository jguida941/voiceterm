"""Scenario: the packet the controller selects as the active piece of
work for a given actor must be the newest pending packet for that
actor in the same plan-row. Otherwise an older stale action_request
hides a newer same-row finding from the inbox.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


def _run_inbox(actor: str) -> dict:
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "review-channel",
            "--action", "inbox",
            "--target", actor,
            "--actor", actor,
            "--terminal", "none",
            "--limit", "200",
            "--include-stale",
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


def _packet_rank(packet: dict) -> int:
    """Numeric rank derived from packet_id (rev_pkt_NNNN) for ordering."""
    pid = str(packet.get("packet_id") or "")
    if "_" not in pid:
        return -1
    tail = pid.rsplit("_", 1)[-1]
    try:
        return int(tail)
    except ValueError:
        return -1


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


def test_selected_attention_packet_is_the_newest_same_row_pending():
    """For each actor that has a selected attention/active packet, the
    selection must be the newest pending packet in the same plan_row.
    A stale older packet selection that hides a newer same-row packet
    is the contradiction.
    """
    sync = _run_sync_status()
    decisions = sync.get("agent_loop_decisions") or []
    if not isinstance(decisions, list) or not decisions:
        pytest.skip("no agent_loop_decisions")

    violations: list[dict] = []
    for d in decisions:
        if not isinstance(d, dict):
            continue
        actor = str(d.get("actor_id") or "").strip()
        if not actor:
            continue
        selected = str(d.get("attention_packet_id") or "").strip()
        if not selected:
            continue
        plan_row = str(d.get("plan_target_ref") or "").strip()
        inbox = _run_inbox(actor)
        packets = inbox.get("packets") or []
        selected_packet = next(
            (
                p
                for p in packets
                if isinstance(p, dict)
                and str(p.get("packet_id") or "") == selected
            ),
            None,
        )
        if selected_packet is None:
            # selection points at something not in actor's inbox -- skip
            continue
        selected_row = str(selected_packet.get("plan_target_ref") or "").strip()
        target_row = plan_row or selected_row
        if not target_row:
            continue
        same_row_pending = [
            p
            for p in packets
            if isinstance(p, dict)
            and str(p.get("status") or "") == "pending"
            and str(p.get("plan_target_ref") or "") == target_row
        ]
        if not same_row_pending:
            continue
        newest_rank = max(_packet_rank(p) for p in same_row_pending)
        selected_rank = _packet_rank(selected_packet)
        if selected_rank >= newest_rank:
            continue
        newest_packet = max(same_row_pending, key=_packet_rank)
        violations.append({
            "actor": actor,
            "plan_row": target_row,
            "selected": selected,
            "selected_rank": selected_rank,
            "newest_same_row": str(newest_packet.get("packet_id") or "?"),
            "newest_rank": newest_rank,
        })

    assert not violations, (
        "selected attention packet is older than another pending packet "
        "in the same plan-row -- stale selection is hiding newer work:\n"
        + "\n".join(
            f"  - actor={v['actor']!r} row={v['plan_row']!r} "
            f"selected={v['selected']!r}(#{v['selected_rank']}) "
            f"newer_same_row={v['newest_same_row']!r}(#{v['newest_rank']})"
            for v in violations[:5]
        )
    )
