"""Scenario: a review-channel post by an actor whose control-decision
artifact already exists on disk must succeed without the caller passing
an explicit ``--control-decision-input``.

The artifact path pattern is:
    dev/reports/review_channel/control_decisions/<event_dir>/<actor>-<role>-<session>.json

Today the post route returns the generic ``no_control_decision_input``
error in this case. That makes a reviewer/implementer unable to post
without manually wiring the path through, defeating the typed route.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
CONTROL_DECISION_ROOT = REPO_ROOT / "dev" / "reports" / "review_channel" / "control_decisions"


def _newest_codex_reviewer_artifact() -> tuple[str, Path] | None:
    """Return ``(session_id, path)`` for the newest on-disk codex/reviewer
    control-decision artifact, or ``None`` if none exists.
    """
    if not CONTROL_DECISION_ROOT.is_dir():
        return None
    candidates: list[tuple[int, Path]] = []
    for event_dir in CONTROL_DECISION_ROOT.iterdir():
        if not event_dir.is_dir() or not event_dir.name.startswith("rev_evt_"):
            continue
        try:
            rank = int(event_dir.name.split("_")[-1])
        except ValueError:
            continue
        for path in event_dir.glob("codex-reviewer-*.json"):
            candidates.append((rank, path))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, picked = candidates[0]
    session_id = picked.stem[len("codex-reviewer-"):]
    return session_id, picked


def test_post_auto_loads_control_decision_when_artifact_exists_on_disk():
    """Post a packet as codex/reviewer without ``--control-decision-input``.
    Since a matching control-decision artifact exists on disk, the route
    should find it and either succeed or fail for a different, more
    specific reason -- never with the generic ``no_control_decision_input``.
    """
    artifact = _newest_codex_reviewer_artifact()
    if artifact is None:
        pytest.skip("no codex/reviewer control-decision artifact on disk")
    session_id, artifact_path = artifact

    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "review-channel",
            "--action", "post",
            "--from-agent", "codex",
            "--to-agent", "claude",
            "--actor", "codex",
            "--actor-role", "reviewer",
            "--session-id", session_id,
            "--kind", "task_progress",
            "--summary", "auto-discovery probe",
            "--body", "auto-discovery probe",
            "--terminal", "none",
            "--format", "json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"_raw_stdout": result.stdout[:400], "_returncode": result.returncode}

    payload_text = json.dumps(payload).lower()
    assert "no_control_decision_input" not in payload_text, (
        "post returned no_control_decision_input while a matching "
        "control-decision artifact already exists on disk.\n"
        f"  artifact: {artifact_path}\n"
        f"  session:  {session_id}\n"
        f"  exit:     {result.returncode}\n"
        f"  stdout:   {result.stdout[:300]!r}"
    )
    packet = payload.get("packet") or {}
    assert payload.get("ok") and packet.get("packet_id", "").startswith("rev_pkt_"), (
        "post completed but did not materialize a typed packet.\n"
        f"  ok:        {payload.get('ok')}\n"
        f"  errors:    {payload.get('errors')}\n"
        f"  rejected:  {payload.get('rejected_reason')}\n"
        f"  artifact:  {artifact_path}"
    )
