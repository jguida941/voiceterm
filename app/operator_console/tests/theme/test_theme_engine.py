"""Tests for the theme engine: ThemeState, presets, QSS parsing, and persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.operator_console.theme.runtime import theme_engine as theme_engine_module
from app.operator_console.theme.stylesheet import (
    build_operator_console_stylesheet_from_colors,
)
from app.operator_console.theme.runtime.theme_engine import (
    ActiveThemeSelection,
    BUILTIN_PRESETS,
    BUILTIN_PRESETS_BY_ID,
    COLOR_CATEGORIES,
    TOKEN_CATEGORIES,
    ThemeState,
    _builtin_presets,
    parse_qss_to_colors,
)
from app.operator_console.theme.runtime.theme_storage import (
    delete_custom_preset_file,
    load_custom_presets,
    save_custom_preset,
)
from app.operator_console.theme.config.theme_components import default_component_settings
from app.operator_console.theme.config.theme_motion import default_motion_settings
from app.operator_console.theme.config.theme_tokens import default_theme_tokens


class ThemeStateTests(unittest.TestCase):
    """ThemeState dataclass serialization and copy."""

    def test_to_dict_roundtrip(self) -> None:
        state = ThemeState(
            name="Test",
            colors={"accent": "#ff0000", "bg_top": "#111"},
            components={"button_style": "outline"},
            motion={"page_transition": "none"},
        )
        data = state.to_dict()
        restored = ThemeState.from_dict(data)
        self.assertEqual(restored.name, "Test")
        self.assertEqual(restored.colors["accent"], state.colors["accent"])
        self.assertEqual(restored.colors["bg_top"], state.colors["bg_top"])
        self.assertIn("toolbar_bg", restored.colors)
        self.assertEqual(restored.components["button_style"], "outline")
        self.assertEqual(restored.motion["page_transition"], "none")

    def test_from_dict_defaults(self) -> None:
        state = ThemeState.from_dict({})
        self.assertEqual(state.name, "Custom")
        self.assertEqual(state.colors, {})
        self.assertEqual(state.tokens, default_theme_tokens())
        self.assertEqual(state.components, default_component_settings())
        self.assertEqual(state.motion, default_motion_settings())

    def test_copy_is_independent(self) -> None:
        original = ThemeState(name="A", colors={"accent": "#ff0000"})
        copied = original.copy()
        copied.colors["accent"] = "#00ff00"
        copied.name = "B"
        copied.tokens["font_size"] = "18"
        copied.components["button_style"] = "outline"
        copied.motion["page_transition"] = "none"
        self.assertEqual(original.colors["accent"], "#ff0000")
        self.assertEqual(original.name, "A")
        self.assertEqual(original.tokens["font_size"], default_theme_tokens()["font_size"])
        self.assertEqual(
            original.components["button_style"],
            default_component_settings()["button_style"],
        )
        self.assertEqual(
            original.motion["page_transition"],
            default_motion_settings()["page_transition"],
        )

    def test_from_dict_accepts_legacy_metrics_key(self) -> None:
        state = ThemeState.from_dict(
            {
                "name": "Legacy",
                "colors": {"accent": "#123456"},
                "metrics": {"font_size": 18},
                "component_styles": {"button_style": "outline"},
                "animations": {"page_transition": "none"},
            }
        )

        self.assertEqual(state.colors["accent"], "#123456")
        self.assertEqual(state.tokens["font_size"], "18")
        self.assertEqual(state.components["button_style"], "outline")
        self.assertEqual(state.motion["page_transition"], "none")

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
        state = ThemeState(
            name="MyPreset",
            colors={"accent": "#abcdef"},
            components={"button_style": "outline"},
            motion={"page_transition": "none"},
        )
        save_custom_preset(state, self._dir)
        loaded = load_custom_presets(self._dir)
        self.assertIn("MyPreset", loaded)
        self.assertEqual(loaded["MyPreset"].colors["accent"], "#abcdef")
        self.assertEqual(loaded["MyPreset"].components["button_style"], "outline")
        self.assertEqual(loaded["MyPreset"].motion["page_transition"], "none")

    def test_delete_returns_true_on_success(self) -> None:
        state = ThemeState(name="ToDelete", colors={"bg_top": "#000"})
        save_custom_preset(state, self._dir)
        result = delete_custom_preset_file("ToDelete", self._dir)
        self.assertTrue(result)

    def test_delete_returns_false_when_missing(self) -> None:
        result = delete_custom_preset_file("NoSuchPreset", self._dir)
        self.assertFalse(result)

    def test_load_skips_malformed_json(self) -> None:
        (self._dir / "bad.json").write_text("not json at all", encoding="utf-8")
        loaded = load_custom_presets(self._dir)
        self.assertEqual(len(loaded), 0)

    def test_load_empty_dir(self) -> None:
        loaded = load_custom_presets(self._dir / "nonexistent")
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
        loaded = load_custom_presets(self._dir)

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
        from app.operator_console.theme.runtime.theme_engine import ThemeEngine, get_engine
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

    def test_component_and_motion_edits_drop_builtin_theme_id(self) -> None:
        engine = theme_engine_module.ThemeEngine()

        engine.apply_builtin_theme("codex")
        engine.set_component("button_style", "outline")
        engine.set_motion("page_transition", "none")

        self.assertIsNone(engine.current_theme_id)
        self.assertEqual(engine.get_components()["button_style"], "outline")
        self.assertEqual(engine.get_motion()["page_transition"], "none")

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

    def test_save_current_and_load_saved_preserve_component_motion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            theme_engine_module,
            "CUSTOM_THEMES_DIR",
            Path(tmpdir),
        ):
            engine = theme_engine_module.ThemeEngine()
            engine.set_component("button_style", "outline")
            engine.set_motion("page_transition", "none")
            engine.save_current()

            restored = theme_engine_module.ThemeEngine()
            self.assertTrue(restored.load_saved())
            self.assertEqual(restored.get_components()["button_style"], "outline")
            self.assertEqual(restored.get_motion()["page_transition"], "none")

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

    def test_import_from_json_accepts_component_only_payload(self) -> None:
        engine = theme_engine_module.ThemeEngine()

        ok = engine.import_from_json(
            """{
                "name": "Outline Ops",
                "components": {"button_style": "outline"},
                "motion": {"page_transition": "none"}
            }"""
        )

        self.assertTrue(ok)
        self.assertEqual(engine.get_components()["button_style"], "outline")
        self.assertEqual(engine.get_motion()["page_transition"], "none")

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

    def test_export_overlay_theme_file_blocks_component_only_edits(self) -> None:
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("codex")
        engine.set_component("button_style", "outline")

        rendered = engine.export_overlay_theme_file()

        self.assertIsNone(rendered)
        self.assertIn("unavailable", engine.overlay_export_status().lower())

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

    def test_partial_component_import_preserves_active_theme_tokens(self) -> None:
        """Importing only components should keep the active theme's colors."""
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("dracula")
        dracula_bg = engine.get_colors()["bg_top"]

        ok = engine.import_from_json(
            '{"components": {"button_style": "outline"}}'
        )

        self.assertTrue(ok)
        self.assertEqual(engine.get_components()["button_style"], "outline")
        self.assertEqual(
            engine.get_colors()["bg_top"],
            dracula_bg,
            "Partial import must not reset colors to Codex base",
        )

    def test_partial_motion_import_preserves_active_theme_tokens_and_components(self) -> None:
        """Importing only motion should keep existing colors and components."""
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("dracula")
        dracula_bg = engine.get_colors()["bg_top"]
        original_button = engine.get_components()["button_style"]

        ok = engine.import_from_json(
            '{"motion": {"page_transition": "none"}}'
        )

        self.assertTrue(ok)
        self.assertEqual(engine.get_motion()["page_transition"], "none")
        self.assertEqual(engine.get_colors()["bg_top"], dracula_bg)
        self.assertEqual(
            engine.get_components()["button_style"], original_button
        )

    def test_full_import_with_colors_still_works(self) -> None:
        """Full import (with colors) should apply the new palette."""
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("dracula")

        ok = engine.import_from_json(json.dumps({
            "name": "Full Override",
            "colors": {"accent": "#ff0000", "bg_top": "#000000"},
            "tokens": {"font_size": "18"},
        }))

        self.assertTrue(ok)
        self.assertEqual(engine.get_colors()["accent"], "#ff0000")
        self.assertEqual(engine.get_colors()["bg_top"], "#000000")
        self.assertEqual(engine.get_tokens()["font_size"], "18")

    def test_partial_import_drops_identity_on_component_change(self) -> None:
        """Partial import that changes components must drop builtin identity."""
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("dracula")
        self.assertEqual(engine.current_theme_id, "dracula")

        ok = engine.import_from_json(
            '{"components": {"button_style": "outline"}}'
        )

        self.assertTrue(ok)
        self.assertIsNone(
            engine.current_theme_id,
            "Builtin identity must be cleared when partial import diverges",
        )
        self.assertEqual(engine.current_theme, "Custom")

    def test_partial_import_preserves_untouched_component_subfields(self) -> None:
        """Only the imported keys should change; untouched subfields survive."""
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("codex")
        engine.set_component("toolbar_button_style", "ghost")
        engine.set_component("monitor_tab_style", "pill")

        ok = engine.import_from_json(
            '{"components": {"button_style": "outline"}}'
        )

        self.assertTrue(ok)
        self.assertEqual(engine.get_components()["button_style"], "outline")
        self.assertEqual(
            engine.get_components()["toolbar_button_style"], "ghost",
            "Untouched component subfield must survive partial import",
        )
        self.assertEqual(
            engine.get_components()["monitor_tab_style"], "pill",
            "Untouched component subfield must survive partial import",
        )

    def test_partial_import_preserves_untouched_token_subfields(self) -> None:
        """Partial token import must only update provided keys."""
        engine = theme_engine_module.ThemeEngine()
        engine.set_token("font_size", "20")
        engine.set_token("border_radius", "10")

        ok = engine.import_from_json(
            '{"tokens": {"font_size": "16"}}'
        )

        self.assertTrue(ok)
        self.assertEqual(engine.get_tokens()["font_size"], "16")
        self.assertEqual(
            engine.get_tokens()["border_radius"], "10",
            "Untouched token must survive partial import",
        )

    def test_partial_import_preserves_untouched_motion_subfields(self) -> None:
        """Partial motion import must only update provided keys."""
        engine = theme_engine_module.ThemeEngine()
        engine.set_motion("page_transition", "none")
        engine.set_motion("hover_emphasis", "strong")

        ok = engine.import_from_json(
            '{"motion": {"page_transition": "fade"}}'
        )

        self.assertTrue(ok)
        self.assertEqual(engine.get_motion()["page_transition"], "fade")
        self.assertEqual(
            engine.get_motion()["hover_emphasis"], "strong",
            "Untouched motion must survive partial import",
        )

    def test_named_partial_import_uses_provided_name(self) -> None:
        """Named partial import should use the provided name."""
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("dracula")

        ok = engine.import_from_json(
            '{"name": "Outline Ops", "components": {"button_style": "outline"}}'
        )

        self.assertTrue(ok)
        self.assertEqual(engine.current_theme, "Outline Ops")
        self.assertIsNone(engine.current_theme_id)

    def test_export_blocks_after_partial_import_diverges(self) -> None:
        """Export must block after partial import drops builtin identity."""
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("dracula")

        engine.import_from_json(
            '{"components": {"button_style": "outline"}}'
        )

        self.assertIsNone(engine.export_overlay_theme_file())
        self.assertIn("unavailable", engine.overlay_export_status().lower())

    def test_partial_noop_import_preserves_identity(self) -> None:
        """Importing a value identical to the active builtin keeps identity."""
        engine = theme_engine_module.ThemeEngine()
        engine.apply_builtin_theme("codex")
        default_button = default_component_settings()["button_style"]

        ok = engine.import_from_json(
            json.dumps({"components": {"button_style": default_button}})
        )

        self.assertTrue(ok)
        self.assertEqual(engine.current_theme_id, "codex")
        self.assertEqual(engine.current_theme, "Codex")


if __name__ == "__main__":
    unittest.main()
