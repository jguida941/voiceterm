"""Focused fail-closed tests for implementation admissibility."""

from __future__ import annotations

from dev.scripts.devctl.runtime.implementation_admissibility import (
    derive_implementation_admissibility,
)


def test_derive_implementation_admissibility_blocks_on_none_permission() -> None:
    result = derive_implementation_admissibility(implementation_permission=None)

    assert result.status == "blocked"
    assert "implementation_permission_missing" in result.reasons


def test_derive_implementation_admissibility_blocks_on_empty_permission() -> None:
    result = derive_implementation_admissibility(implementation_permission="")

    assert result.status == "blocked"
    assert "implementation_permission_missing" in result.reasons


def test_derive_implementation_admissibility_keeps_checkpoint_required_when_permission_present(
) -> None:
    result = derive_implementation_admissibility(
        implementation_permission="active",
        checkpoint_required=True,
        safe_to_continue_editing=False,
    )

    assert result.status == "checkpoint_required"
    assert "checkpoint_required" in result.reasons
    assert "safe_to_continue_editing_false" in result.reasons
