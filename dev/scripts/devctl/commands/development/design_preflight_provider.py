"""Provider session-state probe for develop design-preflight."""

from __future__ import annotations

from pathlib import Path

from ...time_utils import utc_timestamp
from .design_preflight_probe import ground_truth_probe
from .models import DevelopmentGroundTruthProbe


def provider_session_state_probe(
    *,
    repo_root: Path,
    topic: str,
) -> DevelopmentGroundTruthProbe:
    if "remote" not in topic.lower() and "claude" not in topic.lower():
        return ground_truth_probe(
            "provider_session_state",
            "not_applicable",
            "No provider-native state keyword in the topic.",
            "",
            (),
        )
    try:
        from ..remote_control._session_state_proof import (
            resolve_latest_live_session_state_bridge_proof,
        )
    except ImportError:
        return ground_truth_probe(
            "provider_session_state",
            "missing",
            "Claude session-state reader is unavailable.",
            "",
            (),
        )
    proof = resolve_latest_live_session_state_bridge_proof(
        now_utc=utc_timestamp(),
        expected_cwd=repo_root,
        max_age_seconds=900,
    )
    if proof is None:
        return ground_truth_probe(
            "provider_session_state",
            "absent",
            "Claude session-state was checked; no fresh bridgeSessionId proof is active for this repo.",
            "~/.claude/sessions/*.json",
            ("bridgeSessionId", "updatedAt", "pid", "cwd"),
        )
    return ground_truth_probe(
        "provider_session_state",
        "present",
        "Fresh Claude bridgeSessionId proof found.",
        str(proof.path),
        ("bridgeSessionId", "updatedAt", "pid", "cwd"),
    )
