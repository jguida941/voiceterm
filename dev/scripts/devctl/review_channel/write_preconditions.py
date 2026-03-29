"""Preconditions for instruction-mutating markdown bridge writes."""

from __future__ import annotations

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
    raise ValueError(
        f"{action} refused stale bridge write: expected current instruction "
        f"revision `{expected}`, but live bridge revision is "
        f"`{live_revision or 'missing'}`."
    )
