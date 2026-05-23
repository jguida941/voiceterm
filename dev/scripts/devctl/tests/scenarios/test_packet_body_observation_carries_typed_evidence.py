"""Scenario: when a packet's body_observed_at_utc is set, the same
packet must also carry the typed observation evidence -- who observed
it, the body digest, and the typed observation event ids. A
``body_observed_at_utc`` timestamp without the supporting fields means
the observation is being claimed without a verifiable route.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


def _run_inbox(actor: str = "claude") -> dict:
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


def test_body_observed_packets_carry_typed_observation_evidence():
    """For each packet where body_observed_at_utc is set, the same packet
    row must also have non-empty body_observed_by, body_digest, and
    body_observation_events. Otherwise the observation is a claim with
    no supporting evidence.
    """
    output = _run_inbox()
    packets = output.get("packets") or []
    if not packets:
        pytest.skip("inbox returned zero packets")

    violations: list[dict] = []
    for p in packets:
        if not isinstance(p, dict):
            continue
        observed_at = str(p.get("body_observed_at_utc") or "").strip()
        if not observed_at:
            continue
        observed_by = str(p.get("body_observed_by") or "").strip()
        digest = str(p.get("body_digest") or "").strip()
        events = p.get("body_observation_events") or []
        if observed_by and digest and isinstance(events, list) and events:
            continue
        violations.append({
            "packet_id": str(p.get("packet_id") or "?"),
            "body_observed_at_utc": observed_at,
            "body_observed_by": observed_by,
            "body_digest_present": bool(digest),
            "body_observation_events_count": (
                len(events) if isinstance(events, list) else "n/a"
            ),
        })

    assert not violations, (
        "packet claims body_observed_at_utc but lacks typed observation "
        "evidence:\n"
        + "\n".join(
            f"  - {v['packet_id']} observed_at={v['body_observed_at_utc']!r} "
            f"observed_by={v['body_observed_by']!r} "
            f"digest={v['body_digest_present']} "
            f"events={v['body_observation_events_count']}"
            for v in violations[:5]
        )
    )
