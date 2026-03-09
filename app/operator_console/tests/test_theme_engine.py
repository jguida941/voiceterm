"""Tests for the theme engine: ThemeState, presets, QSS parsing, and persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.operator_console.theme import theme_engine as theme_engine_module
from app.operator_console.theme.stylesheet import (
    build_operator_console_stylesheet_from_colors,
)
from app.operator_console.theme.theme_engine import (
    ActiveThemeSelection,
    BUILTIN_PRESETS,
    BUILTIN_PRESETS_BY_ID,
    COLOR_CATEGORIES,
    TOKEN_CATEGORIES,
    ThemeState,
    _builtin_presets,
    _load_custom_presets,
    _save_custom_preset,
    _delete_custom_preset_file,
    parse_qss_to_colors,
)
from app.operator_console.theme.theme_tokens import default_theme_tokens


class ThemeStateTests(unittest.TestCase):
    """ThemeState dataclass serialization and copy."""

    def test_to_dict_roundtrip(self) -> None:
        state = ThemeState(name="Test", colors={"accent": "#ff0000", "bg_top": "#111"})
        data = state.to_dict()
        restored = ThemeState.from_dict(data)
        self.assertEqual(restored.name, "Test")
        self.assertEqual(restored.colors["accent"], state.colors["accent"])
        self.assertEqual(restored.colors["bg_top"], state.colors["bg_top"])
        self.assertIn("toolbar_bg", restored.colors)

    def test_from_dict_defaults(self) -> None:
        state = ThemeState.from_dict({})
        self.assertEqual(state.name, "Custom")
        self.assertEqual(state.colors, {})
        self.assertEqual(state.tokens, default_theme_tokens())

    def test_copy_is_independent(self) -> None:
        original = ThemeState(name="A", colors={"accent": "#ff0000"})
        copied = original.copy()
        copied.colors["accent"] = "#00ff00"
        copied.name = "B"
        copied.tokens["font_size"] = "18"
        self.assertEqual(original.colors["accent"], "#ff0000")
        self.assertEqual(original.name, "A")
        self.assertEqual(original.tokens["font_size"], default_theme_tokens()["font_size"])

    def test_from_dict_accepts_legacy_metrics_key(self) -> None:
        state = ThemeState.from_dict(
            {
                "name": "Legacy",
                "colors": {"accent": "#123456"},
                "metrics": {"font_size": 18},
            }
        )

        self.assertEqual(state.colors["accent"], "#123456")
        self.assertEqual(state.tokens["font_size"], "18")

    def test_from_dict_infers_builtin_theme_id_for_legacy_saved_builtin(self) -> None:
        data = BUILTIN_PRESETS["Codex"].to_dict()
        data.pop("theme_id", None)

        state = ThemeState.from_dict(data)

        self.assertEqual(state.theme_id, "codex")

    def test_from_dict_does_not_infer_builtin_theme_id_for_modified_builtin_name(self) -> None:
        data = BUILTIN_PRESETS["Codex"].to_dict()
        data.pop("theme_id", None)
        data["colors"] = dict(data["colors"])
        data["colors"]["accent"] = "#123456"

        state = ThemeState.from_dict(data)

        self.assertIsNone(state.theme_id)

    def test_from_dict_hydrates_legacy_builtin_colors(self) -> None:
        state = ThemeState.from_dict(
            {
                "name": "Claude",
                "colors": {
                    "accent": BUILTIN_PRESETS["Claude"].colors["accent"],
                    "bg_top": BUILTIN_PRESETS["Claude"].colors["bg_top"],
                },
            }
        )

        self.assertEqual(state.theme_id, "claude")
        self.assertEqual(
            state.colors["toolbar_bg"],
            BUILTIN_PRESETS["Claude"].colors["toolbar_bg"],
        )

    def test_from_dict_hydrates_legacy_custom_colors_from_codex_base(self) -> None:
        state = ThemeState.from_dict(
            {
                "name": "Night Shift",
                "colors": {"accent": "#123456"},
            }
        )

        self.assertIsNone(state.theme_id)
        self.assertEqual(state.colors["accent"], "#123456")
        self.assertEqual(
            state.colors["toolbar_bg"],
            BUILTIN_PRESETS["Codex"].colors["toolbar_bg"],
        )

    def test_hydrated_legacy_state_builds_stylesheet(self) -> None:
        state = ThemeState.from_dict(
            {
                "name": "Codex",
                "colors": {"accent": BUILTIN_PRESETS["Codex"].colors["accent"]},
            }
        )

        stylesheet = build_operator_console_stylesheet_from_colors(
            state.colors,
            state.tokens,
        )

        self.assertIn("QFrame#Toolbar", stylesheet)
        self.assertIn(BUILTIN_PRESETS["Codex"].colors["toolbar_bg"], stylesheet)


class BuiltinPresetsTests(unittest.TestCase):
    """Built-in presets match the THEME_SEEDS registry."""

    def test_builtin_presets_are_populated(self) -> None:
        self.assertGreater(len(BUILTIN_PRESETS), 0)

    def test_each_preset_has_colors(self) -> None:
        for name, state in BUILTIN_PRESETS.items():
            self.assertIsInstance(state, ThemeState)
            self.assertEqual(state.name, name)
            self.assertGreater(len(state.colors), 0, f"Preset '{name}' has no colors")

    def test_codex_preset_exists(self) -> None:
        self.assertIn("Codex", BUILTIN_PRESETS)

    def test_presets_contain_all_category_keys(self) -> None:
        """Every color key listed in COLOR_CATEGORIES should exist in presets."""
        all_keys = set()
        for keys in COLOR_CATEGORIES.values():
            all_keys.update(keys)

        codex = BUILTIN_PRESETS["Codex"]
        for key in all_keys:
            self.assertIn(
                key, codex.colors,
                f"Key '{key}' from COLOR_CATEGORIES missing in Codex preset",
            )

    def test_presets_contain_all_token_keys(self) -> None:
        all_keys = set()
        for keys in TOKEN_CATEGORIES.values():
            all_keys.update(keys)

        codex = BUILTIN_PRESETS["Codex"]
        for key in all_keys:
            self.assertIn(key, codex.tokens)


class ColorCategoriesTests(unittest.TestCase):
    """Validate the category groupings are consistent."""

    def test_no_duplicate_keys_across_categories(self) -> None:
        seen: set[str] = set()
        for cat, keys in COLOR_CATEGORIES.items():
            for k in keys:
                self.assertNotIn(k, seen, f"Duplicate key '{k}' in category '{cat}'")
                seen.add(k)

    def test_all_categories_are_non_empty(self) -> None:
        for cat, keys in COLOR_CATEGORIES.items():
            self.assertGreater(len(keys), 0, f"Category '{cat}' is empty")


class CustomPresetPersistenceTests(unittest.TestCase):
    """Save/load/delete custom presets to a temp directory."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_save_and_load(self) -> None:
        state = ThemeState(name="MyPreset", colors={"accent": "#abcdef"})
        with mock.patch(
            "app.operator_console.theme.theme_engine.CUSTOM_THEMES_DIR", self._dir
        ):
            _save_custom_preset(state)
            loaded = _load_custom_presets()
        self.assertIn("MyPreset", loaded)
        self.assertEqual(loaded["MyPreset"].colors["accent"], "#abcdef")

    def test_delete_returns_true_on_success(self) -> None:
        state = ThemeState(name="ToDelete", colors={"bg_top": "#000"})
        with mock.patch(
            "app.operator_console.theme.theme_engine.CUSTOM_THEMES_DIR", self._dir
        ):
            _save_custom_preset(state)
            result = _delete_custom_preset_file("ToDelete")
        self.assertTrue(result)

    def test_delete_returns_false_when_missing(self) -> None:
        with mock.patch(
            "app.operator_console.theme.theme_engine.CUSTOM_THEMES_DIR", self._dir
        ):
            result = _delete_custom_preset_file("NoSuchPreset")
        self.assertFalse(result)

    def test_load_skips_malformed_json(self) -> None:
        (self._dir / "bad.json").write_text("not json at all", encoding="utf-8")
        with mock.patch(
            "app.operator_console.theme.theme_engine.CUSTOM_THEMES_DIR", self._dir
        ):
            loaded = _load_custom_presets()
        self.assertEqual(len(loaded), 0)

    def test_load_empty_dir(self) -> None:
        with mock.patch(
            "app.operator_console.theme.theme_engine.CUSTOM_THEMES_DIR",
            self._dir / "nonexistent",
        ):
            loaded = _load_custom_presets()
        self.assertEqual(len(loaded), 0)

    def test_load_hydrates_legacy_partial_custom_preset(self) -> None:
        legacy = {
            "name": "Legacy Custom",
            "colors": {"accent": "#123456"},
        }
        (self._dir / "legacy.json").write_text(
            json.dumps(legacy),
            encoding="utf-8",
        )
        with mock.patch(
            "app.operator_console.theme.theme_engine.CUSTOM_THEMES_DIR", self._dir
        ):
            loaded = _load_custom_presets()

        self.assertEqual(loaded["Legacy Custom"].colors["accent"], "#123456")
        self.assertEqual(
            loaded["Legacy Custom"].colors["toolbar_bg"],
            BUILTIN_PRESETS["Codex"].colors["toolbar_bg"],
        )


class ParseQssToColorsTests(unittest.TestCase):
    """QSS stylesheet → semantic color extraction."""

    def test_extracts_background_colors(self) -> None:
        qss = """
        QMainWindow { background-color: #0a0a0a; }
        QWidget { background-color: #111111; }
        QFrame { background: #222222; }
        """
        colors = parse_qss_to_colors(qss)
        self.assertEqual(colors.get("bg_top"), "#0a0a0a")
        self.assertEqual(colors.get("bg_bottom"), "#111111")
        self.assertEqual(colors.get("panel"), "#222222")

    def test_extracts_text_colors(self) -> None:
        qss = """
        QLabel { color: #ffffff; }
        QPlainTextEdit { color: #aaaaaa; }
        """
        colors = parse_qss_to_colors(qss)
        self.assertEqual(colors.get("text"), "#ffffff")
        self.assertEqual(colors.get("text_muted"), "#aaaaaa")

    def test_extracts_border_colors(self) -> None:
        qss = """
        QFrame { border-color: #333333; }
        QWidget { border: 1px solid #444444; }
        """
        colors = parse_qss_to_colors(qss)
        self.assertEqual(colors.get("border"), "#333333")
        # The second border value extraction depends on regex matching
        # "border" property with the color pattern
        self.assertIn("border", colors)

    def test_empty_qss_returns_empty(self) -> None:
        self.assertEqual(parse_qss_to_colors(""), {})

    def test_no_color_properties_returns_empty(self) -> None:
        qss = "QWidget { font-size: 12px; padding: 4px; }"
        self.assertEqual(parse_qss_to_colors(qss), {})


class ThemeEngineStubTests(unittest.TestCase):
    """Test ThemeEngine without PyQt6 — verify the stub path works."""

    def test_stub_engine_is_importable(self) -> None:
        from app.operator_console.theme.theme_engine import ThemeEngine, get_engine
        # Even if PyQt6 is missing, we get back an object
        self.assertIsNotNone(ThemeEngine)


@unittest.skipUnless(theme_engine_module._PYQT_AVAILABLE, "PyQt6 is not installed")
class ThemeEngineSelectionTests(unittest.TestCase):
    def test_apply_builtin_theme_tracks_builtin_selection(self) -> None:
        engine = theme_engine_module.ThemeEngine()

        engine.apply_builtin_theme("claude")

        self.assertEqual(engine.current_theme, "Claude")
        self.assertEqual(engine.current_theme_id, "claude")
        self.assertEqual(
            engine.get_active_selection(),
            ActiveThemeSelection(
                kind="builtin",
                display_name="Claude",
                theme_id="claude",
            ),
        )

    def test_theme_edits_drop_builtin_theme_id_and_become_draft(self) -> None:
        engine = theme_engine_module.ThemeEngine()
        original_accent = BUILTIN_PRESETS_BY_ID["codex"].colors["accent"]
        updated_accent = "#123456" if original_accent != "#123456" else "#654321"

        engine.apply_builtin_theme("codex")
        engine.set_color("accent", updated_accent)

        self.assertIsNone(engine.current_theme_id)
        self.assertEqual(
            engine.get_active_selection(),
            ActiveThemeSelection(
                kind="draft",
                display_name="Custom",
                theme_id=None,
            ),
        )

    def test_save_custom_preset_promotes_saved_name_to_active_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            theme_engine_module,
            "CUSTOM_THEMES_DIR",
            Path(tmpdir),
        ):
            engine = theme_engine_module.ThemeEngine()
            engine.set_color("accent", "#123456")

            engine.save_custom_preset("Night Shift")

            self.assertEqual(engine.current_theme, "Night Shift")
            self.assertIsNone(engine.current_theme_id)
            self.assertEqual(
                engine.get_active_selection(),
                ActiveThemeSelection(
                    kind="custom",
                    display_name="Night Shift",
                    theme_id=None,
                ),
            )

    def test_import_from_overlay_text_applies_builtin_base_theme_with_summary(self) -> None:
        engine = theme_engine_module.ThemeEngine()

        ok = engine.import_from_overlay_text(
            """{
                "version": 4,
                "profile": "ops",
                "base_theme": "dracula",
                "components": {"overlay_border": "rounded"}
            }"""
        )

        self.assertTrue(ok)
        self.assertEqual(engine.current_theme, "Dracula")
        self.assertEqual(engine.current_theme_id, "dracula")
        self.assertIn("Not yet mapped", engine.last_overlay_import_summary() or "")

    def test_export_overlay_theme_file_renders_canonical_toml(self) -> None:
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("codex")

        rendered = engine.export_overlay_theme_file()

        self.assertIsNotNone(rendered)
        assert rendered is not None
        self.assertIn("[meta]", rendered)
        self.assertIn('name = "Codex"', rendered)
        self.assertIn('base_theme = "codex"', rendered)

    def test_export_overlay_style_pack_json_renders_canonical_payload(self) -> None:
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("dracula")

        rendered = engine.export_overlay_style_pack_json()

        self.assertIsNotNone(rendered)
        assert rendered is not None
        payload = json.loads(rendered)
        self.assertEqual(payload["version"], 4)
        self.assertEqual(payload["profile"], "dracula")
        self.assertEqual(payload["base_theme"], "dracula")

    def test_export_overlay_theme_file_blocks_custom_desktop_edits(self) -> None:
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("codex")
        engine.set_color("accent", "#123456")

        rendered = engine.export_overlay_theme_file()

        self.assertIsNone(rendered)
        self.assertIn("unavailable", engine.overlay_export_status().lower())
        self.assertIn("Current desktop-only edits", engine.overlay_theme_file_preview())

    def test_export_overlay_theme_file_allows_exact_custom_copy_of_builtin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            theme_engine_module,
            "CUSTOM_THEMES_DIR",
            Path(tmpdir),
        ):
            engine = theme_engine_module.ThemeEngine()
            engine.apply_builtin_theme("codex")
            engine.save_custom_preset("Night Ops")

            rendered = engine.export_overlay_theme_file()

        self.assertIsNotNone(rendered)
        assert rendered is not None
        self.assertIn('name = "Night Ops"', rendered)
        self.assertIn('base_theme = "codex"', rendered)


if __name__ == "__main__":
    unittest.main()
