"""Scenario: when an agent-loop decision says "run this next command" and
that next command is a sanctioned review-channel packet-attention call
(body-open, semantic-ingest, absorb), the decision's allowed_actions
list MUST include a matching ``review-channel.*`` entry.

Otherwise the actor is told "do this" while every action is denied --
the agent has work to do but no permission to do it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]

# Map a packet-attention next_command to the review-channel.* action that
# should appear in allowed_actions when the decision says run_next_command.
_NEXT_COMMAND_TO_REVIEW_ACTION: tuple[tuple[str, str], ...] = (
    ("review-channel --action show", "review-channel.show"),
    ("review-channel --action ingest", "review-channel.ingest"),
    ("review-channel --action absorb", "review-channel.absorb"),
)


def _expected_review_action(next_command: str) -> str:
    for needle, action in _NEXT_COMMAND_TO_REVIEW_ACTION:
        if needle in next_command:
            return action
    return ""


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
    assert result.returncode == 0, (
        f"sync-status exit {result.returncode}; stderr: {result.stderr[:300]}"
    )
    return json.loads(result.stdout)


def test_run_next_command_decision_must_grant_matching_review_channel_action():
    """For every agent_loop_decision where:
        decision == 'run_next_command'
        advance_allowed is True
        next_command targets a sanctioned review-channel.* packet action
      the decision's allowed_actions list MUST contain the matching
      review-channel.* action. Empty allowed_actions in that state is
      a contradiction: the controller is naming a required action while
      denying every action.
    """
    output = _run_sync_status()
    decisions = output.get("agent_loop_decisions") or []
    if not isinstance(decisions, list) or not decisions:
        pytest.skip("no agent_loop_decisions in sync-status output")

    violations: list[dict] = []
    for d in decisions:
        if not isinstance(d, dict):
            continue
        if str(d.get("decision") or "").strip().lower() != "run_next_command":
            continue
        if not bool(d.get("advance_allowed")):
            continue
        next_command = str(d.get("next_command") or "")
        expected = _expected_review_action(next_command)
        if not expected:
            continue
        allowed = d.get("allowed_actions") or []
        if not isinstance(allowed, list):
            allowed = []
        if expected in allowed:
            continue
        violations.append({
            "actor_id": str(d.get("actor_id") or ""),
            "actor_role": str(d.get("actor_role") or ""),
            "expected_action": expected,
            "allowed_actions": list(allowed),
            "next_command": next_command[:120],
        })

    assert not violations, (
        "agent_loop_decision says run_next_command but allowed_actions "
        "does not include the matching review-channel.* action -- the "
        "actor is being told to run a command they have no permission "
        "to run.\n"
        + "\n".join(
            f"  - actor={v['actor_id']!r}/{v['actor_role']!r} "
            f"expected={v['expected_action']!r} "
            f"allowed_actions={v['allowed_actions']!r} "
            f"next_command={v['next_command']!r}"
            for v in violations[:5]
        )
    )
