from __future__ import annotations

import unittest

from app.operator_console.theme import (
    DEFAULT_THEME_ID,
    available_theme_ids,
    build_operator_console_stylesheet,
    build_operator_console_stylesheet_from_colors,
    resolve_theme,
)
from app.operator_console.theme.runtime import theme_engine as theme_engine_module
from app.operator_console.theme.config.theme_components import default_component_settings
from app.operator_console.theme.config.theme_motion import default_motion_settings
from app.operator_console.theme.config.theme_tokens import default_theme_tokens


class ThemeRegistryTests(unittest.TestCase):
    def test_default_theme_exists(self) -> None:
        self.assertIn(DEFAULT_THEME_ID, available_theme_ids())

    def test_overlay_theme_ids_are_available(self) -> None:
        expected_prefix = (
            "coral",
            "claude",
            "codex",
            "chatgpt",
            "catppuccin",
            "dracula",
            "nord",
            "tokyonight",
            "gruvbox",
            "ansi",
            "none",
            "minimal",
        )
        available = available_theme_ids()
        self.assertGreaterEqual(len(available), len(expected_prefix))
        self.assertEqual(available[: len(expected_prefix)], expected_prefix)

    def test_resolve_theme_falls_back_to_default(self) -> None:
        self.assertEqual(resolve_theme("missing-theme").theme_id, DEFAULT_THEME_ID)

    def test_stylesheet_uses_selected_theme_colors(self) -> None:
        stylesheet = build_operator_console_stylesheet("coral")
        self.assertIn("#ff6b6b", stylesheet)
        self.assertIn("QSplitter::handle", stylesheet)
        self.assertIn(resolve_theme("coral").colors["hover_overlay"], stylesheet)
        self.assertIn(resolve_theme("coral").colors["scrollbar_track_bg"], stylesheet)
        self.assertIn(resolve_theme("coral").colors["menu_border_subtle"], stylesheet)

    def test_nav_tab_bar_has_transparent_background(self) -> None:
        stylesheet = build_operator_console_stylesheet("codex")
        self.assertIn("QTabBar#NavTabBar", stylesheet)
        self.assertIn("background: transparent", stylesheet)

    def test_nav_tabs_pane_is_transparent(self) -> None:
        stylesheet = build_operator_console_stylesheet("codex")
        self.assertIn("QTabWidget#NavTabs::pane", stylesheet)

    def test_monitor_tabs_have_document_style(self) -> None:
        stylesheet = build_operator_console_stylesheet("codex")
        self.assertIn("QTabWidget#MonitorTabs::pane", stylesheet)
        self.assertIn("QTabBar#MonitorTabBar::tab", stylesheet)

    def test_sidebar_nav_is_grouped_with_navigation_rules(self) -> None:
        stylesheet = build_operator_console_stylesheet("codex")
        self.assertIn("QFrame#SidebarNav", stylesheet)
        self.assertIn("QListWidget#SidebarNavList::item:selected", stylesheet)

    def test_summary_surfaces_have_explicit_qss_rules(self) -> None:
        stylesheet = build_operator_console_stylesheet("codex")
        self.assertIn("QFrame#AgentSummaryCard", stylesheet)
        self.assertIn("QLabel#RoleBadge", stylesheet)
        self.assertIn('QLabel#StatusIndicator[statusLevel="active"]', stylesheet)

    def test_tab_min_width_is_at_least_90px(self) -> None:
        stylesheet = build_operator_console_stylesheet("codex")
        self.assertIn("min-width: 90px", stylesheet)

    def test_buttons_use_subtle_styling(self) -> None:
        """Buttons should use muted text color and small padding."""
        stylesheet = build_operator_console_stylesheet("codex")
        self.assertIn("padding: 3px 8px", stylesheet)
        self.assertIn("font-size: 11px", stylesheet)

    def test_accent_buttons_use_tinted_backgrounds(self) -> None:
        """Accent-role buttons should use subtle tints, not saturated fills."""
        stylesheet = build_operator_console_stylesheet("codex")
        # Primary accent buttons should not use deep accent fill
        self.assertNotIn("accent_deep", stylesheet)

    def test_all_themes_produce_valid_stylesheet(self) -> None:
        """Every registered theme should generate a non-empty stylesheet."""
        for theme_id in available_theme_ids():
            stylesheet = build_operator_console_stylesheet(theme_id)
            self.assertIn("QMainWindow", stylesheet)
            self.assertIn("QPushButton", stylesheet)
            self.assertIn("QTabBar", stylesheet)

    def test_explicit_color_builder_matches_named_theme_builder(self) -> None:
        colors = resolve_theme("codex").colors
        self.assertEqual(
            build_operator_console_stylesheet_from_colors(colors),
            build_operator_console_stylesheet("codex"),
        )

    def test_explicit_tokens_change_the_generated_stylesheet(self) -> None:
        colors = resolve_theme("codex").colors
        tokens = default_theme_tokens()
        tokens.update({"font_size": "16", "border_radius_large": "18"})

        stylesheet = build_operator_console_stylesheet_from_colors(colors, tokens)

        self.assertIn("font-size: 16px", stylesheet)
        self.assertIn("border-radius: 18px", stylesheet)

    def test_component_styles_change_the_generated_stylesheet(self) -> None:
        colors = resolve_theme("codex").colors
        components = default_component_settings()
        components.update({"button_style": "outline", "nav_tab_style": "pill"})

        stylesheet = build_operator_console_stylesheet_from_colors(
            colors,
            default_theme_tokens(),
            components,
        )

        self.assertIn("background: transparent", stylesheet)
        self.assertIn("QTabBar#NavTabBar::tab:selected", stylesheet)

    def test_motion_settings_do_not_break_stylesheet_generation(self) -> None:
        colors = resolve_theme("codex").colors
        motion = default_motion_settings()
        motion.update({"page_transition": "none", "page_transition_ms": "0"})

        stylesheet = build_operator_console_stylesheet_from_colors(
            colors,
            default_theme_tokens(),
            default_component_settings(),
            motion,
        )

        self.assertIn("QPushButton#SmallActionButton", stylesheet)

    def test_stylesheet_no_longer_depends_on_shared_rgba_literals(self) -> None:
        stylesheet = build_operator_console_stylesheet("codex")

        self.assertNotIn("rgba(255, 255, 255, 0.06)", stylesheet)
        self.assertNotIn("rgba(9, 17, 22, 210)", stylesheet)

    @unittest.skipUnless(theme_engine_module._PYQT_AVAILABLE, "PyQt6 is not installed")
    def test_theme_engine_generate_stylesheet_uses_shared_builder(self) -> None:
        engine = theme_engine_module.ThemeEngine()
        self.assertEqual(
            engine.generate_stylesheet(),
            build_operator_console_stylesheet_from_colors(
                engine.get_colors(),
                engine.get_tokens(),
                engine.get_components(),
                engine.get_motion(),
            ),
        )


if __name__ == "__main__":
    unittest.main()
