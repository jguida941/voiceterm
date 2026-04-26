"""Bridge-drift detection and sync helpers for review-channel status."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from ...review_channel.bridge_file import rewrite_bridge_markdown
from ...review_channel.bridge_projection import render_bridge_projection
from ...review_channel.current_session_projection import (
    current_session_authority_drift_warning,
)
from ...review_channel.handoff import extract_bridge_snapshot
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
from ...review_channel.peer_liveness import (
    resolve_reported_reviewer_mode,
    reviewer_mode_is_active,
)


def bridge_current_session_drifted(
    warnings: list[str],
    *,
    bridge_path: Path | None = None,
    review_state_path: Path | None = None,
    bridge_liveness: dict[str, object] | None = None,
) -> bool:
    warning_reported_drift = any(
        "typed `current_session` authority" in str(warning) for warning in warnings
    )
    if bridge_path is None or review_state_path is None:
        return warning_reported_drift
    if not bridge_path.is_file() or not review_state_path.is_file():
        return warning_reported_drift
    try:
        prior_review_state = json.loads(review_state_path.read_text(encoding="utf-8"))
        if not isinstance(prior_review_state, dict):
            return warning_reported_drift
        snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return warning_reported_drift
    if reviewer_mode_projection_drifted(
        snapshot_metadata=snapshot.metadata,
        review_state_payload=prior_review_state,
    ):
        return True
    return bool(
        current_session_authority_drift_warning(
            snapshot=snapshot,
            prior_review_state=prior_review_state,
            bridge_liveness=bridge_liveness,
        )
    )


def reviewer_mode_projection_drifted(
    *,
    snapshot_metadata: Mapping[str, object],
    review_state_payload: Mapping[str, object],
) -> bool:
    expected = _typed_effective_reviewer_mode(review_state_payload)
    if not expected:
        return False
    current = resolve_reported_reviewer_mode(
        {"reviewer_mode": snapshot_metadata.get("reviewer_mode")}
    )
    if reviewer_mode_is_active(current) and not reviewer_mode_is_active(expected):
        return False
    return current != expected


def without_bridge_current_session_drift(warnings: object) -> list[str]:
    if not isinstance(warnings, list):
        return []
    return [
        str(warning)
        for warning in warnings
        if "typed `current_session` authority" not in str(warning)
    ]


def sync_bridge_from_typed_projection_if_needed(
    *,
    repo_root: Path,
    bridge_path: Path,
    snapshot,
) -> tuple[bool, str]:
    review_state_path = Path(snapshot.projection_paths.review_state_path)
    if not review_state_path.is_file():
        return (
            False,
            "Skipped `bridge.md` sync during status refresh because the typed "
            "review-state projection is missing.",
        )
    try:
        review_state_payload = json.loads(review_state_path.read_text(encoding="utf-8"))
        if not isinstance(review_state_payload, dict):
            raise ValueError("Typed review-state projection must be a JSON object.")
        current_bridge_text = bridge_path.read_text(encoding="utf-8")
        if reviewer_owned_bridge_state_is_newer(
            bridge_text=current_bridge_text,
            review_state_payload=review_state_payload,
        ):
            return (
                False,
                "Skipped `bridge.md` sync during status refresh because the "
                "reviewer-owned bridge heartbeat is newer than the typed "
                "review-state projection.",
            )
        bridge_rel = str(bridge_path.relative_to(repo_root))
        worktree_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=(bridge_rel,),
        )

        def transform(_bridge_text: str) -> str:
            rendered, _ = render_bridge_projection(
                review_state=review_state_payload,
                last_worktree_hash=worktree_hash,
            )
            return rendered

        rewrite_bridge_markdown(bridge_path, transform=transform)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return (
            False,
            "Failed to synchronize `bridge.md` from typed review-state during "
            f"status refresh: {exc}",
        )
    return (True, "")


def reviewer_owned_bridge_state_is_newer(
    *,
    bridge_text: str,
    review_state_payload: Mapping[str, object],
) -> bool:
    """Return True when a fresh reviewer-owned bridge row must not be reversed."""
    snapshot = extract_bridge_snapshot(bridge_text)
    if not reviewer_mode_is_active(snapshot.metadata.get("reviewer_mode")):
        return False
    bridge_poll = _parse_timestamp(snapshot.metadata.get("last_codex_poll_utc"))
    typed_poll = _parse_timestamp(_typed_last_codex_poll_utc(review_state_payload))
    if bridge_poll is None or typed_poll is None:
        return False
    return bridge_poll > typed_poll


def _typed_last_codex_poll_utc(payload: Mapping[str, object]) -> str:
    bridge = _mapping(payload.get("bridge"))
    if bridge:
        value = str(
            bridge.get("last_reviewer_poll_utc")
            or bridge.get("last_codex_poll_utc")
            or ""
        ).strip()
        if value:
            return value
    compat = _mapping(payload.get("_compat"))
    projection = _mapping(compat.get("bridge_projection"))
    metadata = _mapping(projection.get("metadata"))
    return str(metadata.get("last_codex_poll_utc") or "").strip()


def _typed_effective_reviewer_mode(payload: Mapping[str, object]) -> str:
    bridge = _mapping(payload.get("bridge"))
    if bridge:
        mode = resolve_reported_reviewer_mode(
            {
                "reviewer_mode": (
                    bridge.get("effective_reviewer_mode") or bridge.get("reviewer_mode")
                )
            }
        )
        if mode:
            return mode
    authority = _mapping(payload.get("authority_snapshot"))
    if authority:
        mode = resolve_reported_reviewer_mode(
            {"reviewer_mode": authority.get("reviewer_mode")}
        )
        if mode:
            return mode
    return ""


def _parse_timestamp(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
