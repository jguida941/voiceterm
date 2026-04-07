"""Prepared-launch authority helpers for review-channel conductor scripts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .handoff import extract_bridge_snapshot

NON_RESTARTABLE_LAUNCH_AUTHORITY_EXIT_CODE = 82


@dataclass(frozen=True, slots=True)
class PreparedLaunchAuthority:
    """Authority snapshot embedded into one prepared conductor launch."""

    head_sha: str = ""
    instruction_revision: str = ""
    session_token: str = ""
    review_state_path: Path | None = None


def build_prepared_launch_authority(
    *,
    repo_root: Path,
    bridge_path: Path,
    bridge_liveness: Mapping[str, object] | None = None,
    review_state_path: Path | None = None,
) -> PreparedLaunchAuthority:
    """Build the typed authority snapshot a launch script must re-check."""
    review_state = _load_review_state(review_state_path)
    bridge = _mapping(review_state.get("bridge")) if review_state else {}
    review = _mapping(review_state.get("review")) if review_state else {}
    current_session = (
        _mapping(review_state.get("current_session")) if review_state else {}
    )
    bridge_snapshot = _bridge_snapshot(bridge_path)
    bridge_liveness = bridge_liveness or {}

    instruction_revision = _first_text(
        current_session.get("current_instruction_revision"),
        bridge.get("current_instruction_revision"),
        bridge_liveness.get("current_instruction_revision"),
        bridge_snapshot.metadata.get("current_instruction_revision"),
    )
    last_codex_poll = _first_text(
        bridge.get("last_codex_poll_utc"),
        bridge_liveness.get("last_codex_poll_utc"),
        bridge_snapshot.metadata.get("last_codex_poll_utc"),
    )
    session_id = _first_text(review.get("session_id"), "markdown-bridge")

    return PreparedLaunchAuthority(
        head_sha=current_head_sha(repo_root),
        instruction_revision=instruction_revision,
        session_token=launch_session_token(
            session_id=session_id,
            instruction_revision=instruction_revision,
            last_codex_poll_utc=last_codex_poll,
        ),
        review_state_path=review_state_path,
    )


def launch_session_token(
    *,
    session_id: str,
    instruction_revision: str,
    last_codex_poll_utc: str,
) -> str:
    """Return the stable typed turn/session token used by launch scripts."""
    payload = "\0".join(
        part.strip()
        for part in (session_id, instruction_revision, last_codex_poll_utc)
        if part.strip()
    )
    if not payload:
        return ""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def current_head_sha(repo_root: Path) -> str:
    """Return the current git HEAD SHA, or empty string when unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _load_review_state(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _bridge_snapshot(bridge_path: Path):
    try:
        return extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    except OSError:
        return extract_bridge_snapshot("")


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""
