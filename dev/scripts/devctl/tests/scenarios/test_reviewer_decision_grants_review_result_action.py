"""Scenario: a reviewer with an active attention packet for the current
plan-row must have at least one review-result-emitting action in its
allowed_actions list (post_finding, post_action_request, review_accepted,
review_failed, review.checkpoint, etc). Otherwise the reviewer has work
to act on but no way to record the result.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]

_REVIEW_RESULT_ACTIONS = frozenset({
    "review-channel.post_finding",
    "review-channel.post_action_request",
    "review-channel.post_task_progress",
    "review-channel.post_task_produced",
    "review-channel.post_evidence",
    "review-channel.post_continuation_anchor",
    "review-channel.post_stop_anchor",
    "review.checkpoint",
})


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


def test_reviewer_with_active_attention_can_emit_review_result():
    """For each agent_loop_decision whose actor_role is reviewer (or
    orchestrator) and which names an attention/active packet, the
    decision's allowed_actions must include at least one review-result
    posting action.
    """
    output = _run_sync_status()
    decisions = output.get("agent_loop_decisions") or []
    if not isinstance(decisions, list) or not decisions:
        pytest.skip("no agent_loop_decisions")

    in_scope = 0
    violations: list[dict] = []
    for d in decisions:
        if not isinstance(d, dict):
            continue
        role = str(d.get("actor_role") or "").strip().lower()
        if role not in {"reviewer", "orchestrator"}:
            continue
        attention = str(d.get("attention_packet_id") or "").strip()
        active = str(d.get("active_packet_id") or "").strip()
        if not (attention or active):
            continue
        in_scope += 1
        allowed = d.get("allowed_actions") or []
        if not isinstance(allowed, list):
            allowed = []
        if any(a in _REVIEW_RESULT_ACTIONS for a in allowed):
            continue
        violations.append({
            "actor_id": str(d.get("actor_id") or ""),
            "actor_role": role,
            "attention": attention,
            "active": active,
            "allowed_actions": list(allowed)[:6],
        })

    if in_scope == 0:
        pytest.skip("no reviewer/orchestrator decision currently has an attention packet")

    assert not violations, (
        "reviewer/orchestrator has work to act on but no way to record "
        "the result:\n"
        + "\n".join(
            f"  - actor={v['actor_id']!r}/{v['actor_role']!r} "
            f"attention={v['attention']!r} active={v['active']!r} "
            f"allowed_first6={v['allowed_actions']!r}"
            for v in violations[:5]
        )
    )
