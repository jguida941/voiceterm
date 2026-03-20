"""Tests for shared JSONL parsing warnings."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.jsonl_support import parse_json_line_dict


class JsonlSupportTests(unittest.TestCase):
    def test_invalid_json_row_emits_warning_with_source_context(self) -> None:
        warnings: list[str] = []

        payload = parse_json_line_dict(
            "{not-json}",
            source="events.jsonl",
            line_number=7,
            warning_sink=warnings.append,
        )

        self.assertIsNone(payload)
        self.assertEqual(len(warnings), 1)
        self.assertIn("events.jsonl:7", warnings[0])
        self.assertIn("invalid JSON object", warnings[0])

    def test_non_object_row_emits_warning_with_source_context(self) -> None:
        warnings: list[str] = []

        payload = parse_json_line_dict(
            '["not", "an", "object"]',
            source="events.jsonl",
            line_number=9,
            warning_sink=warnings.append,
        )

        self.assertIsNone(payload)
        self.assertEqual(len(warnings), 1)
        self.assertIn("events.jsonl:9", warnings[0])
        self.assertIn("expected top-level JSON object", warnings[0])


if __name__ == "__main__":
    unittest.main()
