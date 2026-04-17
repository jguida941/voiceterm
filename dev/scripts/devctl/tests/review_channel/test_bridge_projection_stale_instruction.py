"""Regression: explicit typed clear must not fall back to stale bridge instruction."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.review_channel.bridge_projection_sections import (
    with_fallback_sections,
)


class TestExplicitClearNoStaleFallback(unittest.TestCase):

    def test_explicit_empty_instruction_does_not_fallback_to_bridge_state(self) -> None:
        review_state = {
            "current_session": {"current_instruction": ""},
            "bridge": {"current_instruction": "- stale bridge instruction"},
            "reviewer_runtime": {},
        }
        result = with_fallback_sections(review_state, {})
        instruction = result.get("Current Instruction For Claude", "")
        self.assertNotIn(
            "stale bridge instruction",
            instruction,
            "Explicit typed clear of current_instruction must not fall back to stale bridge state",
        )

    def test_missing_instruction_key_falls_back_to_bridge_state(self) -> None:
        review_state = {
            "current_session": {},
            "bridge": {"current_instruction": "- do the next task"},
            "reviewer_runtime": {},
        }
        result = with_fallback_sections(review_state, {})
        instruction = result.get("Current Instruction For Claude", "")
        self.assertNotIn("do the next task", instruction)
        self.assertIn("Await reviewer instruction refresh", instruction)

    def test_missing_placeholder_instruction_uses_refresh_placeholder(self) -> None:
        review_state = {
            "current_session": {"current_instruction": "(missing)"},
            "bridge": {"current_instruction": "- stale bridge instruction"},
            "reviewer_runtime": {},
        }
        result = with_fallback_sections(review_state, {})
        instruction = result.get("Current Instruction For Claude", "")
        self.assertNotIn("stale bridge instruction", instruction)
        self.assertNotIn("(missing)", instruction)
        self.assertIn("Await reviewer instruction refresh", instruction)

    def test_missing_last_reviewed_scope_does_not_fallback_to_bridge_state(self) -> None:
        review_state = {
            "current_session": {},
            "bridge": {"last_reviewed_scope": "MP-355"},
            "reviewer_runtime": {},
        }
        result = with_fallback_sections(review_state, {})
        last_reviewed_scope = result.get("Last Reviewed Scope", "")
        self.assertNotIn("MP-355", last_reviewed_scope)
        self.assertIn("(missing)", last_reviewed_scope)


if __name__ == "__main__":
    unittest.main()
