"""Preconditions for instruction-mutating markdown bridge writes."""

from __future__ import annotations

from .current_session_projection import bridge_implementer_state_hash
from .handoff import extract_bridge_snapshot
from .reviewer_state_normalize import (
    instruction_revision as _normalized_instruction_revision,
    normalize_instruction_body as _normalize_instruction_body,
)
from .reviewer_state_support import current_instruction_revision_from_bridge_text


def assert_expected_instruction_revision(
    *,
    bridge_text: str,
    expected_instruction_revision: str | None,
    action: str,
) -> None:
    """Fail closed when a caller tries to mutate stale live instruction state."""
    expected = (expected_instruction_revision or "").strip()
    if not expected:
        return
    live_revision = current_instruction_revision_from_bridge_text(bridge_text)
    if live_revision == expected:
        return
    snapshot = extract_bridge_snapshot(bridge_text)
    effective_revision = _normalized_instruction_revision(
        _normalize_instruction_body(
            snapshot.sections.get("Current Instruction For Claude", "")
        )
    )
    if effective_revision == expected:
        return
    raise ValueError(
        f"{action} refused stale bridge write: expected current instruction "
        f"revision `{expected}`, but live bridge revision is "
        f"`{live_revision or 'missing'}`"
        + (
            f" (effective typed revision `{effective_revision}`)."
            if effective_revision and effective_revision != live_revision
            else "."
        )
    )


def assert_expected_implementer_state_hash(
    *,
    bridge_text: str,
    expected_implementer_state_hash: str | None,
    action: str,
) -> None:
    """Fail closed when a reviewer write depends on stale Claude-owned state."""
    expected = (expected_implementer_state_hash or "").strip()
    if not expected:
        return
    live_hash = bridge_implementer_state_hash(extract_bridge_snapshot(bridge_text))
    if live_hash == expected:
        return
    raise ValueError(
        f"{action} refused stale bridge write: expected implementer state hash "
        f"`{expected}`, but live implementer state hash is "
        f"`{live_hash or 'missing'}`."
    )
