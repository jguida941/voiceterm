"""Theme engine for the Operator Console with persistence and undo/redo."""

from __future__ import annotations

import json
from pathlib import Path

from .theme_overlay_sync import (
    export_overlay_style_pack_json,
    export_overlay_theme_file,
    import_overlay_state_file,
    import_overlay_state_text,
    overlay_export_status,
    overlay_theme_file_preview,
    suggested_overlay_style_pack_file_name,
    suggested_overlay_theme_file_name,
)
from .theme_state import (
    ActiveThemeSelection,
    BUILTIN_PRESETS,
    BUILTIN_PRESET_NAME_BY_ID,
    BUILTIN_PRESETS_BY_ID,
    COLOR_CATEGORIES,
    ThemeState,
    _builtin_presets,
)
from .theme_storage import (
    delete_custom_preset_file,
    load_custom_presets,
    parse_qss_to_colors,
    save_custom_preset,
)
from .theme_tokens import TOKEN_CATEGORIES

try:
    from PyQt6.QtCore import QObject, pyqtSignal
    from PyQt6.QtWidgets import QApplication

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False
    QObject = object


CUSTOM_THEMES_DIR = Path.home() / ".voiceterm" / "themes"


def _load_custom_presets() -> dict[str, ThemeState]:
    return load_custom_presets(CUSTOM_THEMES_DIR)


def _save_custom_preset(state: ThemeState) -> None:
    save_custom_preset(state, CUSTOM_THEMES_DIR)


def _delete_custom_preset_file(name: str) -> bool:
    return delete_custom_preset_file(name, CUSTOM_THEMES_DIR)


if _PYQT_AVAILABLE:

    class ThemeEngine(QObject):
        """Central theme engine with undo/redo, presets, and persistence."""

        theme_changed = pyqtSignal()

        _MAX_UNDO = 50

        def __init__(self, parent: QObject | None = None) -> None:
            super().__init__(parent)
            self._state = BUILTIN_PRESETS["Codex"].copy()
            self._custom_presets = _load_custom_presets()
            self._undo_stack: list[ThemeState] = []
            self._redo_stack: list[ThemeState] = []
            self._apply_enabled = True
            self._last_overlay_import_summary: str | None = None

        @property
        def current_theme(self) -> str:
            return self._state.name

        @property
        def current_theme_id(self) -> str | None:
            return self._state.theme_id

        def get_state(self) -> ThemeState:
            return self._state.copy()

        def get_active_selection(self) -> ActiveThemeSelection:
            if self._state.theme_id is not None:
                return ActiveThemeSelection(
                    kind="builtin",
                    display_name=self._state.name,
                    theme_id=self._state.theme_id,
                )
            if self._state.name == "Custom":
                return ActiveThemeSelection(
                    kind="draft",
                    display_name=self._state.name,
                    theme_id=None,
                )
            return ActiveThemeSelection(
                kind="custom",
                display_name=self._state.name,
                theme_id=None,
            )

        def get_colors(self) -> dict[str, str]:
            return dict(self._state.colors)

        def get_tokens(self) -> dict[str, str]:
            return dict(self._state.tokens)

        def get_preset_names(self) -> list[str]:
            names = list(BUILTIN_PRESETS.keys())
            for name in sorted(self._custom_presets.keys()):
                if name not in names:
                    names.append(name)
            return names

        def last_overlay_import_summary(self) -> str | None:
            return self._last_overlay_import_summary

        def overlay_export_status(self) -> str:
            return overlay_export_status(self._state)

        def overlay_theme_file_preview(self) -> str:
            return overlay_theme_file_preview(self._state)

        def export_overlay_theme_file(self) -> str | None:
            return export_overlay_theme_file(self._state)

        def export_overlay_style_pack_json(self) -> str | None:
            return export_overlay_style_pack_json(self._state)

        def suggested_overlay_theme_file_name(self) -> str:
            return suggested_overlay_theme_file_name(self._state)

        def suggested_overlay_style_pack_file_name(self) -> str:
            return suggested_overlay_style_pack_file_name(self._state)

        def apply_theme(self, name: str, *, save: bool = True) -> None:
            preset = BUILTIN_PRESETS.get(name) or self._custom_presets.get(name)
            if preset is None or self._state == preset:
                return
            self._push_undo()
            self._state = preset.copy()
            self._apply_and_notify()

        def apply_builtin_theme(self, theme_id: str) -> None:
            preset = BUILTIN_PRESETS_BY_ID.get(theme_id)
            if preset is None or self._state == preset:
                return
            self._push_undo()
            self._state = preset.copy()
            self._apply_and_notify()

        def save_custom_preset(self, name: str) -> None:
            state = self._state.copy()
            state.name = name
            state.theme_id = None
            self._custom_presets[name] = state.copy()
            _save_custom_preset(state)
            if self._state != state:
                self._push_undo()
                self._state = state.copy()
                self._apply_and_notify()

        def delete_custom_preset(self, name: str) -> bool:
            if name in BUILTIN_PRESETS:
                return False
            self._custom_presets.pop(name, None)
            return _delete_custom_preset_file(name)

        def set_color(self, key: str, value: str) -> None:
            if self._state.colors.get(key) == value:
                return
            self._push_undo()
            self._state.colors[key] = value
            self._state.name = "Custom"
            self._state.theme_id = None
            self._apply_and_notify()

        def set_token(self, key: str, value: str | int) -> None:
            rendered = str(value)
            if self._state.tokens.get(key) == rendered:
                return
            self._push_undo()
            self._state.tokens[key] = rendered
            self._state.name = "Custom"
            self._state.theme_id = None
            self._apply_and_notify()

        def can_undo(self) -> bool:
            return bool(self._undo_stack)

        def can_redo(self) -> bool:
            return bool(self._redo_stack)

        def undo(self) -> bool:
            if not self._undo_stack:
                return False
            self._redo_stack.append(self._state.copy())
            self._state = self._undo_stack.pop()
            self._apply_and_notify()
            return True

        def redo(self) -> bool:
            if not self._redo_stack:
                return False
            self._undo_stack.append(self._state.copy())
            self._state = self._redo_stack.pop()
            self._apply_and_notify()
            return True

        def _push_undo(self) -> None:
            self._undo_stack.append(self._state.copy())
            if len(self._undo_stack) > self._MAX_UNDO:
                self._undo_stack.pop(0)
            self._redo_stack.clear()

        def import_from_json(self, json_text: str) -> bool:
            try:
                data = json.loads(json_text)
            except (json.JSONDecodeError, TypeError):
                return False
            if not isinstance(data.get("colors"), dict):
                return False
            self._push_undo()
            imported = ThemeState.from_dict(data)
            base = BUILTIN_PRESETS["Codex"].copy()
            base.colors.update(imported.colors)
            base.tokens.update(imported.tokens)
            base.name = imported.name
            base.theme_id = None
            self._state = base
            self._apply_and_notify()
            return True

        def import_from_file(self, path: str) -> bool:
            try:
                text = Path(path).read_text(encoding="utf-8")
            except OSError:
                return False
            return self.import_from_json(text)

        def export_to_file(self, path: str) -> None:
            Path(path).write_text(
                json.dumps(self._state.to_dict(), indent=2),
                encoding="utf-8",
            )

        def export_json(self) -> str:
            return json.dumps(self._state.to_dict(), indent=2)

        def import_from_qss(self, qss: str, name: str = "Imported QSS") -> bool:
            colors = parse_qss_to_colors(qss)
            if not colors:
                return False
            self._push_undo()
            base = BUILTIN_PRESETS["Codex"].copy()
            base.colors.update(colors)
            base.name = name
            base.theme_id = None
            self._state = base
            self._apply_and_notify()
            return True

        def import_from_overlay_text(
            self,
            text: str,
            *,
            source_name: str | None = None,
        ) -> bool:
            applied = import_overlay_state_text(text, source_name=source_name)
            if applied is None:
                return False
            self._push_undo()
            self._state = applied.state
            self._last_overlay_import_summary = applied.summary
            self._apply_and_notify()
            return True

        def import_from_overlay_file(self, path: str) -> bool:
            applied = import_overlay_state_file(path)
            if applied is None:
                return False
            self._push_undo()
            self._state = applied.state
            self._last_overlay_import_summary = applied.summary
            self._apply_and_notify()
            return True

        def generate_stylesheet(self) -> str:
            from .stylesheet import build_operator_console_stylesheet_from_colors

            return build_operator_console_stylesheet_from_colors(
                self._state.colors,
                self._state.tokens,
            )

        def save_current(self) -> None:
            config = CUSTOM_THEMES_DIR / "_last_theme.json"
            CUSTOM_THEMES_DIR.mkdir(parents=True, exist_ok=True)
            config.write_text(
                json.dumps(self._state.to_dict(), indent=2),
                encoding="utf-8",
            )

        def load_saved(self) -> bool:
            config = CUSTOM_THEMES_DIR / "_last_theme.json"
            if not config.exists():
                return False
            try:
                data = json.loads(config.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, TypeError):
                return False
            state = ThemeState.from_dict(data)
            if not state.colors:
                return False
            self._state = state
            self._apply_and_notify()
            return True

        def set_apply_enabled(self, enabled: bool) -> None:
            self._apply_enabled = enabled
            if enabled:
                app = QApplication.instance()
                if app is not None:
                    app.setStyleSheet(self.generate_stylesheet())
            self.theme_changed.emit()

        def _apply_and_notify(self) -> None:
            if self._apply_enabled:
                app = QApplication.instance()
                if app is not None:
                    app.setStyleSheet(self.generate_stylesheet())
            self.theme_changed.emit()


    _engine_instance: ThemeEngine | None = None

    def get_engine() -> ThemeEngine:
        """Return the global ThemeEngine singleton."""

        global _engine_instance
        if _engine_instance is None:
            _engine_instance = ThemeEngine()
        return _engine_instance

else:

    class ThemeEngine:  # type: ignore[no-redef]
        """Stub when PyQt6 is not installed."""

        pass

    def get_engine() -> ThemeEngine:
        return ThemeEngine()
