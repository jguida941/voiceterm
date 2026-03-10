"""Tests for read-only overlay theme metadata imports."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.operator_console.theme.io.overlay_import import (
    import_overlay_theme_file,
    import_overlay_theme_text,
    render_overlay_import_summary,
)


class OverlayImportTests(unittest.TestCase):
    def test_style_pack_json_import_reads_base_theme(self) -> None:
        result = import_overlay_theme_text(
            """{
                "version": 4,
                "profile": "ops",
                "base_theme": "dracula",
                "components": {"overlay_border": "rounded"},
                "motion": {"page_transition": "fade"}
            }"""
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.theme_id, "dracula")
        self.assertEqual(result.source_kind, "style-pack-json")
        self.assertEqual(result.applied_fields, ("base_theme",))
        self.assertIn("components.overlay_border", result.ignored_fields)
        self.assertIn("motion.page_transition", result.ignored_fields)

    def test_style_pack_json_import_supports_legacy_theme_field(self) -> None:
        result = import_overlay_theme_text('{"version": 1, "theme": "nord"}')

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.theme_id, "nord")
        self.assertEqual(result.applied_fields, ("theme",))

    def test_theme_file_import_reads_meta_base_theme_and_ignored_sections(self) -> None:
        result = import_overlay_theme_text(
            """
            [meta]
            name = "Night Ops"
            version = 1
            base_theme = "claude"

            [colors]
            recording = "#ff0000"

            [borders]
            style = "rounded"
            """
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.theme_id, "claude")
        self.assertEqual(result.source_kind, "theme-file-toml")
        self.assertEqual(result.applied_fields, ("meta.base_theme",))
        self.assertIn("colors", result.ignored_fields)
        self.assertIn("borders", result.ignored_fields)

    def test_import_overlay_theme_file_reads_toml_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ops-theme.toml"
            path.write_text(
                """
                [meta]
                base_theme = "codex"
                """,
                encoding="utf-8",
            )

            result = import_overlay_theme_file(str(path))

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.theme_id, "codex")
        self.assertIn(("source", "ops-theme.toml"), result.provenance)

    def test_render_summary_mentions_unmapped_fields(self) -> None:
        result = import_overlay_theme_text(
            """{
                "version": 4,
                "base_theme": "codex",
                "overrides": {"glyphs": "ascii"}
            }"""
        )

        assert result is not None
        summary = render_overlay_import_summary(result)

        self.assertIn("Codex", summary)
        self.assertIn("Applied: base_theme.", summary)
        self.assertIn("Not yet mapped: overrides.glyphs.", summary)


if __name__ == "__main__":
    unittest.main()
