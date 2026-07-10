"""Standalone file I/O operations for theme import/export dialogs.

Each function takes the ThemeEngine and a parent QWidget so that file
dialogs and message boxes can be shown without coupling to any particular
dialog class.
"""

from __future__ import annotations

from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QFileDialog,
        QInputDialog,
        QMessageBox,
        QWidget,
    )

    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False

if _PYQT_AVAILABLE:
    from ..runtime.theme_engine import ThemeEngine


def import_json_file(engine: ThemeEngine, parent: QWidget) -> bool:
    """Show an open-file dialog and import a JSON theme into *engine*."""
    filename, _ = QFileDialog.getOpenFileName(
        parent,
        "Import Theme",
        "",
        "JSON Files (*.json);;All Files (*.*)",
    )
    if not filename:
        return False
    if not engine.import_from_file(filename):
        QMessageBox.warning(parent, "Import Failed", "Could not load theme JSON.")
        return False
    engine.save_current()
    return True


def export_json_file(engine: ThemeEngine, parent: QWidget) -> bool:
    """Show a save-file dialog and export the current theme as JSON."""
    filename, _ = QFileDialog.getSaveFileName(
        parent,
        "Export Theme (JSON)",
        "",
        "JSON Files (*.json);;All Files (*.*)",
    )
    if not filename:
        return False
    engine.export_to_file(filename)
    return True


def export_qss_file(engine: ThemeEngine, parent: QWidget) -> bool:
    """Show a save-file dialog and export the generated QSS stylesheet."""
    filename, _ = QFileDialog.getSaveFileName(
        parent,
        "Export Theme (QSS)",
        "",
        "Qt Stylesheets (*.qss);;All Files (*.*)",
    )
    if not filename:
        return False
    Path(filename).write_text(engine.generate_stylesheet(), encoding="utf-8")
    return True


def export_overlay_theme_file(engine: ThemeEngine, parent: QWidget) -> bool:
    """Export canonical overlay theme-file TOML via a save dialog."""
    content = engine.export_overlay_theme_file()
    if content is None:
        QMessageBox.information(
            parent,
            "Export Unavailable",
            engine.overlay_export_status(),
        )
        return False
    filename, _ = QFileDialog.getSaveFileName(
        parent,
        "Export VoiceTerm Theme File",
        engine.suggested_overlay_theme_file_name(),
        "TOML Files (*.toml);;All Files (*.*)",
    )
    if not filename:
        return False
    Path(filename).write_text(content, encoding="utf-8")
    return True


def export_overlay_style_pack(engine: ThemeEngine, parent: QWidget) -> bool:
    """Export canonical overlay style-pack JSON via a save dialog."""
    content = engine.export_overlay_style_pack_json()
    if content is None:
        QMessageBox.information(
            parent,
            "Export Unavailable",
            engine.overlay_export_status(),
        )
        return False
    filename, _ = QFileDialog.getSaveFileName(
        parent,
        "Export VoiceTerm Style-Pack JSON",
        engine.suggested_overlay_style_pack_file_name(),
        "JSON Files (*.json);;All Files (*.*)",
    )
    if not filename:
        return False
    Path(filename).write_text(content, encoding="utf-8")
    return True


def import_overlay_file(engine: ThemeEngine, parent: QWidget) -> bool:
    """Show an open-file dialog and import overlay metadata into *engine*."""
    filename, _ = QFileDialog.getOpenFileName(
        parent,
        "Import VoiceTerm Overlay Metadata",
        "",
        "Overlay Metadata (*.json *.toml);;JSON Files (*.json);;TOML Files (*.toml);;All Files (*.*)",
    )
    if not filename:
        return False
    if not engine.import_from_overlay_file(filename):
        QMessageBox.warning(
            parent,
            "Import Failed",
            "Could not parse overlay metadata.\n\n"
            "Accepted read-path inputs are canonical style-pack JSON and "
            "theme-file TOML metadata with a valid base_theme.",
        )
        return False
    engine.save_current()
    return True


def apply_pasted_json(engine: ThemeEngine, parent: QWidget, text: str) -> bool:
    """Validate and apply a pasted JSON theme string."""
    if not text.strip():
        QMessageBox.warning(parent, "Empty Input", "Please paste a JSON theme first.")
        return False
    if not engine.import_from_json(text):
        QMessageBox.warning(
            parent,
            "Invalid JSON",
            "Could not parse the JSON theme.\n\nInclude at least one of: colors, tokens, components, or motion.",
        )
        return False
    engine.save_current()
    return True


def apply_pasted_qss(engine: ThemeEngine, parent: QWidget, text: str) -> bool:
    """Validate and apply a pasted QSS stylesheet string."""
    if not text.strip():
        QMessageBox.warning(
            parent,
            "Empty Input",
            "Please paste a QSS stylesheet first.",
        )
        return False
    if not engine.import_from_qss(text):
        QMessageBox.warning(
            parent,
            "Parse Failed",
            "Could not parse the QSS stylesheet.",
        )
        return False
    engine.save_current()
    return True


def save_qss_as_preset(engine: ThemeEngine, parent: QWidget, text: str) -> bool:
    """Import QSS, prompt for a preset name, and save it."""
    if not text.strip():
        QMessageBox.warning(
            parent,
            "Empty Input",
            "Please paste a QSS stylesheet first.",
        )
        return False
    name, ok = QInputDialog.getText(parent, "Save QSS as Preset", "Preset name:")
    if not ok or not name.strip():
        return False
    if not engine.import_from_qss(text, name.strip()):
        QMessageBox.warning(
            parent,
            "Parse Failed",
            "Could not parse the QSS stylesheet.",
        )
        return False
    engine.save_custom_preset(name.strip())
    engine.save_current()
    return True


def apply_overlay_text(engine: ThemeEngine, parent: QWidget, text: str) -> bool:
    """Validate and apply pasted overlay metadata text."""
    if not text.strip():
        QMessageBox.warning(
            parent,
            "Empty Input",
            "Please paste overlay metadata first.",
        )
        return False
    if not engine.import_from_overlay_text(text):
        QMessageBox.warning(
            parent,
            "Parse Failed",
            "Could not parse overlay metadata.\n\n"
            "Accepted read-path inputs are canonical style-pack JSON and "
            "theme-file TOML metadata with a valid base_theme.",
        )
        return False
    engine.save_current()
    return True
