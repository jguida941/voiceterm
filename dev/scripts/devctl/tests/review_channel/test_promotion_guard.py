"""Focused promotion-readiness regressions for reviewer prose collisions."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.handoff import BridgeSnapshot
from dev.scripts.devctl.review_channel.promotion import validate_promotion_ready
from dev.scripts.devctl.review_channel.promotion_support import (
    instruction_needs_plan_promotion,
)


def _snapshot(
    *,
    verdict: str,
    open_findings: str,
    instruction: str,
) -> BridgeSnapshot:
    return BridgeSnapshot(
        metadata={},
        sections={
            "Current Verdict": verdict,
            "Open Findings": open_findings,
            "Current Instruction For Claude": instruction,
        },
    )


def test_validate_promotion_ready_rejects_changes_requested_with_accepted_detail() -> None:
    """A later `Accepted:` detail line must not make the whole verdict promotable."""
    errors = validate_promotion_ready(
        _snapshot(
            verdict="\n".join(
                [
                    "- changes_requested",
                    "- Accepted: `e35c4e3` fixed F18/F19.",
                ]
            ),
            open_findings="- none",
            instruction="- hold steady",
        )
    )

    assert any("Current Verdict" in error for error in errors)


def test_validate_promotion_ready_rejects_real_findings_with_terminal_none_text() -> None:
    """`--terminal none` and `unresolved` must not look like idle findings."""
    errors = validate_promotion_ready(
        _snapshot(
            verdict="- accepted",
            open_findings=(
                "- F21: `--terminal none` still reaches the live launch path "
                "in local or unresolved interaction mode."
            ),
            instruction="- hold steady",
        )
    )

    assert any("Open Findings" in error for error in errors)


def test_validate_promotion_ready_rejects_active_instruction_with_terminal_none_detail() -> None:
    """An active instruction that mentions `--terminal none` must stay live."""
    errors = validate_promotion_ready(
        _snapshot(
            verdict="- accepted",
            open_findings="- none",
            instruction="\n".join(
                [
                    "- Start a bounded launch-authority fix.",
                    "- Keep `--terminal none` fail-closed in local mode.",
                ]
            ),
        )
    )

    assert any("Current Instruction For Claude" in error for error in errors)


def test_instruction_needs_plan_promotion_ignores_generic_words_in_later_context() -> None:
    """Only the primary instruction item may drive generic next-step promotion."""
    instruction = "\n".join(
        [
            "- Start a bounded launch-authority fix.",
            "- Do not continue next item until reviewer approval lands.",
        ]
    )

    assert instruction_needs_plan_promotion(instruction) is False


def test_validate_promotion_ready_accepts_explicit_idle_state_markers() -> None:
    """Promotion still works when the primary markers are explicitly idle/resolved."""
    errors = validate_promotion_ready(
        _snapshot(
            verdict="- accepted",
            open_findings="- none",
            instruction="- hold steady",
        )
    )

    assert errors == []
