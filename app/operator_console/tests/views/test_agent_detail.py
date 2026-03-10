"""Tests for agent detail diff detection behavior."""

from __future__ import annotations

import unittest

from app.operator_console.theme.runtime.theme_state import BUILTIN_PRESETS
from app.operator_console.views import agent_detail as agent_detail_module
from app.operator_console.views.agent_detail import DiffHighlighter, looks_like_unified_diff

try:
    from PyQt6.QtWidgets import QApplication, QPlainTextEdit
except ImportError:
    QApplication = None
    QPlainTextEdit = None


class UnifiedDiffDetectionTests(unittest.TestCase):
    def test_markdown_bullets_are_not_treated_as_diff(self) -> None:
        text = "- Status: active\n- Phase: coding\n- Questions: none"
        self.assertFalse(looks_like_unified_diff(text))

    def test_unified_diff_is_detected(self) -> None:
        text = "\n".join(
            (
                "diff --git a/file.py b/file.py",
                "--- a/file.py",
                "+++ b/file.py",
                "@@ -1,2 +1,2 @@",
                "-old",
                "+new",
            )
        )
        self.assertTrue(looks_like_unified_diff(text))


@unittest.skipUnless(agent_detail_module._PYQT_AVAILABLE, "PyQt6 is not installed")
class DiffHighlighterThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_diff_highlighter_uses_theme_tints_for_added_and_removed_lines(self) -> None:
        view = QPlainTextEdit()
        view.setPlainText(
            "\n".join(
                (
                    "diff --git a/file.py b/file.py",
                    "--- a/file.py",
                    "+++ b/file.py",
                    "@@ -1 +1 @@",
                    "-old",
                    "+new",
                )
            )
        )

        highlighter = DiffHighlighter(
            view.document(),
            {
                "status_active": "#102030",
                "danger": "#405060",
                "accent": "#708090",
                "text": "#a0b0c0",
            },
        )

        added_bg = highlighter._added.background().color()
        removed_bg = highlighter._removed.background().color()

        self.assertTrue(highlighter.is_diff_document)
        self.assertEqual(added_bg.name(), "#102030")
        self.assertEqual(added_bg.alpha(), 25)
        self.assertEqual(removed_bg.name(), "#405060")
        self.assertEqual(removed_bg.alpha(), 25)

    def test_diff_highlighter_falls_back_to_builtin_theme_colors(self) -> None:
        view = QPlainTextEdit()
        view.setPlainText(
            "\n".join(
                (
                    "diff --git a/file.py b/file.py",
                    "--- a/file.py",
                    "+++ b/file.py",
                    "@@ -1 +1 @@",
                    "-old",
                    "+new",
                )
            )
        )

        highlighter = DiffHighlighter(view.document(), {})

        added_bg = highlighter._added.background().color()
        removed_bg = highlighter._removed.background().color()
        hunk_fg = highlighter._hunk.foreground().color()
        header_fg = highlighter._header.foreground().color()

        self.assertEqual(
            added_bg.name(),
            BUILTIN_PRESETS["Codex"].colors["status_active"],
        )
        self.assertEqual(
            removed_bg.name(),
            BUILTIN_PRESETS["Codex"].colors["danger"],
        )
        self.assertEqual(
            hunk_fg.name(),
            BUILTIN_PRESETS["Codex"].colors["accent"],
        )
        self.assertEqual(
            header_fg.name(),
            BUILTIN_PRESETS["Codex"].colors["text"],
        )

    def test_invalid_theme_color_falls_back_to_builtin_semantic_text(self) -> None:
        color = agent_detail_module._theme_qcolor({"text": "not-a-color"}, "text")

        self.assertEqual(
            color.name(),
            BUILTIN_PRESETS["Codex"].colors["text"],
        )


if __name__ == "__main__":
    unittest.main()
