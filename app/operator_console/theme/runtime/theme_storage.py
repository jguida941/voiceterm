"""Persistence and QSS-import helpers for Operator Console themes."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .theme_state import BUILTIN_PRESETS, ThemeState


def load_custom_presets(theme_dir: Path) -> dict[str, ThemeState]:
    presets: dict[str, ThemeState] = {}
    if not theme_dir.exists():
        return presets
    for path in sorted(theme_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            state = ThemeState.from_dict(data)
            presets[state.name] = state
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return presets


def save_custom_preset(state: ThemeState, theme_dir: Path) -> None:
    theme_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\-]", "_", state.name)
    path = theme_dir / f"{safe_name}.json"
    path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def delete_custom_preset_file(name: str, theme_dir: Path) -> bool:
    if not theme_dir.exists():
        return False
    safe_name = re.sub(r"[^\w\-]", "_", name)
    path = theme_dir / f"{safe_name}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def parse_qss_to_colors(qss: str) -> dict[str, str]:
    color_pattern = r"(#[0-9A-Fa-f]{3,8}|rgba?\s*\([^)]+\))"
    prop_pattern = r"([a-zA-Z-]+)\s*:\s*([^;{}]+);"

    bg_colors: list[str] = []
    text_colors: list[str] = []
    border_colors: list[str] = []
    all_colors: list[str] = []

    for match in re.finditer(prop_pattern, qss):
        prop = match.group(1).strip().lower()
        value = match.group(2).strip()
        color_match = re.search(color_pattern, value)
        if not color_match:
            continue
        color_val = color_match.group(1)

        if prop in ("background-color", "background"):
            if color_val not in bg_colors:
                bg_colors.append(color_val)
        elif prop == "color":
            if color_val not in text_colors:
                text_colors.append(color_val)
        elif prop in ("border-color", "border"):
            if color_val not in border_colors:
                border_colors.append(color_val)

    for match in re.finditer(color_pattern, qss):
        candidate = match.group(1)
        if candidate not in all_colors:
            all_colors.append(candidate)

    colors: dict[str, str] = {}
    bg_keys = ["bg_top", "bg_bottom", "panel", "panel_alt", "panel_surface"]
    for index, color_value in enumerate(bg_colors[: len(bg_keys)]):
        colors[bg_keys[index]] = color_value

    text_keys = ["text", "text_muted", "text_dim"]
    for index, color_value in enumerate(text_colors[: len(text_keys)]):
        colors[text_keys[index]] = color_value

    border_keys = ["border", "border_soft"]
    for index, color_value in enumerate(border_colors[: len(border_keys)]):
        colors[border_keys[index]] = color_value

    assigned = set(colors.values())
    for color_value in all_colors:
        if color_value in assigned:
            continue
        try:
            from PyQt6.QtGui import QColor

            qt_color = QColor(color_value)
            if qt_color.isValid() and qt_color.saturation() > 100:
                colors["accent"] = qt_color.name()
                break
        except ImportError:
            break

    if colors:
        hydrated = BUILTIN_PRESETS["Codex"].copy()
        hydrated.colors.update(colors)
        return hydrated.colors
    return colors
