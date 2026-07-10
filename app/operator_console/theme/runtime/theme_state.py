"""Theme state models and builtin preset registry for the Operator Console."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..colors import ALL_THEME_SEEDS, _build_semantic_colors
from ..config.theme_components import default_component_settings
from ..config.theme_motion import default_motion_settings
from ..config.theme_tokens import default_theme_tokens

COLOR_CATEGORIES: dict[str, list[str]] = {
    "Backgrounds": [
        "bg_top",
        "bg_bottom",
        "panel",
        "panel_alt",
        "panel_elevated",
        "panel_inset",
        "panel_surface",
        "panel_surface_alt",
    ],
    "Text": ["text", "text_muted", "text_dim"],
    "Borders": [
        "border",
        "border_soft",
        "menu_border_subtle",
        "card_border",
        "card_hover_border",
        "input_border",
        "splitter",
        "splitter_hover",
    ],
    "Accent": ["accent", "accent_soft", "accent_deep"],
    "Alerts": ["warning", "danger"],
    "Selection": ["selection_bg", "selection_text"],
    "Headers": ["header_from", "header_mid", "header_to"],
    "Toolbar": ["toolbar_bg"],
    "Buttons": [
        "button_primary_bg",
        "button_primary_border",
        "button_warning_bg",
        "button_warning_border",
        "button_danger_bg",
        "button_danger_border",
    ],
    "Button Gradients": [
        "button_gradient_top",
        "button_gradient_bottom",
        "button_hover_top",
        "button_hover_bottom",
        "button_primary_gradient_top",
        "button_primary_gradient_bottom",
        "button_warning_gradient_top",
        "button_warning_gradient_bottom",
        "button_danger_gradient_top",
        "button_danger_gradient_bottom",
    ],
    "Scrollbar": [
        "scrollbar_handle_start",
        "scrollbar_handle_stop",
        "scrollbar_handle_hover_start",
        "scrollbar_handle_hover_stop",
    ],
    "Status Dots": ["status_active", "status_warning", "status_stale", "status_idle"],
    "Sidebar": ["sidebar_selected_bg", "badge_bg", "badge_border"],
    "Effects": ["hover_overlay", "scrollbar_track_bg"],
    "Risk Badges": [
        "risk_high_bg",
        "risk_high_fg",
        "risk_medium_bg",
        "risk_medium_fg",
        "risk_low_bg",
        "risk_low_fg",
        "risk_unknown_bg",
        "risk_unknown_fg",
    ],
}


@dataclass
class ThemeState:
    """Complete editable theme state."""

    name: str = "Custom"
    theme_id: str | None = None
    colors: dict[str, str] = field(default_factory=dict)
    tokens: dict[str, str] = field(default_factory=default_theme_tokens)
    components: dict[str, str] = field(default_factory=default_component_settings)
    motion: dict[str, str] = field(default_factory=default_motion_settings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "theme_id": self.theme_id,
            "colors": dict(self.colors),
            "tokens": dict(self.tokens),
            "components": dict(self.components),
            "motion": dict(self.motion),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ThemeState:
        raw_tokens = data.get("tokens") or data.get("metrics") or {}
        tokens = default_theme_tokens()
        if isinstance(raw_tokens, dict):
            tokens.update({key: str(value) for key, value in raw_tokens.items()})
        raw_components = data.get("components") or data.get("component_styles") or {}
        components = default_component_settings()
        if isinstance(raw_components, dict):
            components.update({key: str(value) for key, value in raw_components.items()})
        raw_motion = data.get("motion") or data.get("animations") or {}
        motion = default_motion_settings()
        if isinstance(raw_motion, dict):
            motion.update({key: str(value) for key, value in raw_motion.items()})
        name = str(data.get("name", "Custom"))
        colors = _hydrate_legacy_colors(
            name=name,
            theme_id=data.get("theme_id"),
            raw_colors=data.get("colors", {}),
        )
        theme_id = _infer_builtin_theme_id(
            name=name,
            theme_id=data.get("theme_id"),
            colors=colors,
            tokens=tokens,
            components=components,
            motion=motion,
        )
        return cls(
            name=name,
            theme_id=theme_id,
            colors=colors,
            tokens=tokens,
            components=components,
            motion=motion,
        )

    def copy(self) -> ThemeState:
        return ThemeState(
            name=self.name,
            theme_id=self.theme_id,
            colors=dict(self.colors),
            tokens=dict(self.tokens),
            components=dict(self.components),
            motion=dict(self.motion),
        )


@dataclass(frozen=True)
class ActiveThemeSelection:
    """Explicit description of the active app/editor theme selection."""

    kind: str
    display_name: str
    theme_id: str | None


def _builtin_presets() -> dict[str, ThemeState]:
    """Build preset ThemeStates from the existing ThemeSeed registry."""

    presets: dict[str, ThemeState] = {}
    for seed in ALL_THEME_SEEDS:
        presets[seed.display_name] = ThemeState(
            name=seed.display_name,
            theme_id=seed.theme_id,
            colors=_build_semantic_colors(seed),
            tokens=default_theme_tokens(),
            components=default_component_settings(),
            motion=default_motion_settings(),
        )
    return presets


BUILTIN_PRESETS = _builtin_presets()
BUILTIN_PRESET_NAME_BY_ID = {
    seed.theme_id: seed.display_name for seed in ALL_THEME_SEEDS
}
BUILTIN_PRESET_ID_BY_NAME = {
    display_name: theme_id
    for theme_id, display_name in BUILTIN_PRESET_NAME_BY_ID.items()
}
BUILTIN_PRESETS_BY_ID = {
    theme_id: BUILTIN_PRESETS[display_name]
    for theme_id, display_name in BUILTIN_PRESET_NAME_BY_ID.items()
}


def _resolve_theme_hydration_base(
    *,
    name: str,
    theme_id: object,
) -> ThemeState | None:
    if isinstance(theme_id, str):
        preset = BUILTIN_PRESETS_BY_ID.get(theme_id)
        if preset is not None:
            return preset

    preset = BUILTIN_PRESETS.get(name)
    if preset is not None:
        return preset

    return BUILTIN_PRESETS.get("Codex")


def _hydrate_legacy_colors(
    *,
    name: str,
    theme_id: object,
    raw_colors: object,
) -> dict[str, str]:
    if not isinstance(raw_colors, dict):
        return {}

    colors = {str(key): str(value) for key, value in raw_colors.items()}
    if not colors:
        return {}

    base = _resolve_theme_hydration_base(name=name, theme_id=theme_id)
    if base is None:
        return colors

    hydrated = dict(base.colors)
    hydrated.update(colors)
    return hydrated


def _infer_builtin_theme_id(
    *,
    name: str,
    theme_id: object,
    colors: dict[str, str],
    tokens: dict[str, str],
    components: dict[str, str],
    motion: dict[str, str],
) -> str | None:
    if isinstance(theme_id, str) and theme_id in BUILTIN_PRESETS_BY_ID:
        return theme_id

    builtin_theme_id = BUILTIN_PRESET_ID_BY_NAME.get(name)
    if builtin_theme_id is None:
        return None

    builtin = BUILTIN_PRESETS_BY_ID[builtin_theme_id]
    if (
        colors == builtin.colors
        and tokens == builtin.tokens
        and components == builtin.components
        and motion == builtin.motion
    ):
        return builtin_theme_id
    return None


def _match_exact_builtin_theme_id(
    *,
    colors: dict[str, str],
    tokens: dict[str, str],
    components: dict[str, str],
    motion: dict[str, str],
) -> str | None:
    for theme_id, preset in BUILTIN_PRESETS_BY_ID.items():
        if (
            colors == preset.colors
            and tokens == preset.tokens
            and components == preset.components
            and motion == preset.motion
        ):
            return theme_id
    return None
