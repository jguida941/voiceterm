"""Theme helpers for the optional PyQt6 Operator Console.

The desktop console should not drift into its own styling island. This module
keeps one semantic theme builder and feeds it with overlay-aligned theme seeds
so the PyQt surface stays visually consistent with the Rust overlay themes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperatorConsoleTheme:
    """Resolved named palette used to skin the desktop Operator Console."""

    theme_id: str
    display_name: str
    colors: dict[str, str]


@dataclass(frozen=True)
class ThemeSeed:
    """Small overlay-aligned input set from which semantic UI colors are derived."""

    theme_id: str
    display_name: str
    base_bg: str
    border: str
    accent: str
    accent_soft: str
    warning: str
    danger: str
    text: str
    text_muted: str
    text_dim: str


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"expected #RRGGBB color, got {hex_color!r}")
    return tuple(int(value[index : index + 2], 16) for index in range(0, 6, 2))


def _rgb_to_hex(red: int, green: int, blue: int) -> str:
    return f"#{red:02x}{green:02x}{blue:02x}"


def _mix(color_a: str, color_b: str, ratio: float) -> str:
    """Blend two colors with *ratio* describing how much of *color_b* to use."""
    red_a, green_a, blue_a = _hex_to_rgb(color_a)
    red_b, green_b, blue_b = _hex_to_rgb(color_b)
    clamped_ratio = max(0.0, min(1.0, ratio))
    return _rgb_to_hex(
        int(red_a * (1.0 - clamped_ratio) + red_b * clamped_ratio),
        int(green_a * (1.0 - clamped_ratio) + green_b * clamped_ratio),
        int(blue_a * (1.0 - clamped_ratio) + blue_b * clamped_ratio),
    )


def _rgba(hex_color: str, alpha: int) -> str:
    red, green, blue = _hex_to_rgb(hex_color)
    return f"rgba({red}, {green}, {blue}, {alpha})"


def pick_contrasting_color(
    background_color: str,
    *,
    dark: str,
    light: str,
) -> str:
    """Choose the more legible endpoint color for a solid swatch background."""
    red, green, blue = _hex_to_rgb(background_color)
    luminance = 0.299 * red + 0.587 * green + 0.114 * blue
    return dark if luminance > 128 else light


def _build_semantic_colors(seed: ThemeSeed) -> dict[str, str]:
    """Expand a small seed into the full semantic palette used by the UI."""
    black = "#000000"
    white = "#ffffff"
    bg_top = _mix(seed.base_bg, black, 0.24)
    bg_bottom = _mix(seed.base_bg, black, 0.10)
    panel = _mix(seed.base_bg, black, 0.06)
    panel_alt = _mix(seed.base_bg, seed.border, 0.14)
    panel_elevated = _mix(seed.base_bg, seed.accent, 0.18)
    panel_inset = _mix(seed.base_bg, black, 0.38)
    panel_surface = _mix(seed.base_bg, black, 0.18)
    panel_surface_alt = _mix(panel_surface, seed.border, 0.18)
    accent_deep = _mix(seed.base_bg, seed.accent, 0.46)
    splitter = _mix(seed.base_bg, seed.border, 0.36)
    splitter_hover = _mix(seed.base_bg, seed.accent, 0.54)
    selection_bg = _mix(seed.base_bg, seed.accent, 0.38)
    header_from = _rgba(_mix(seed.base_bg, seed.border, 0.18), 246)
    header_mid = _rgba(_mix(seed.base_bg, seed.accent, 0.26), 236)
    header_to = _rgba(_mix(seed.base_bg, seed.accent_soft, 0.18), 228)
    button_primary_bg = _mix(panel, seed.accent, 0.22)
    button_primary_border = _mix(panel, seed.accent, 0.38)
    button_warning_bg = _mix(panel, seed.warning, 0.22)
    button_warning_border = _mix(panel, seed.warning, 0.38)
    button_danger_bg = _mix(panel, seed.danger, 0.22)
    button_danger_border = _mix(panel, seed.danger, 0.38)
    scrollbar_handle_start = _mix(panel_surface, seed.accent, 0.34)
    scrollbar_handle_stop = _mix(panel_surface, seed.border, 0.48)
    scrollbar_handle_hover_start = _mix(panel_surface, seed.accent, 0.56)
    scrollbar_handle_hover_stop = _mix(panel_surface, seed.accent_soft, 0.50)
    sidebar_selected_bg = _mix(panel, seed.accent, 0.15)
    badge_bg = _mix(panel, seed.accent, 0.16)
    badge_border = _mix(panel, seed.accent, 0.28)
    risk_high_bg = _mix(panel, seed.danger, 0.18)
    risk_medium_bg = _mix(panel, seed.warning, 0.18)
    risk_low_bg = _mix(panel, seed.accent_soft, 0.18)
    risk_unknown_bg = _mix(panel, seed.border, 0.18)

    # Professional button gradient stops (subtle top-to-bottom depth)
    button_gradient_top = _mix(panel_surface, white, 0.07)
    button_gradient_bottom = panel_surface
    button_hover_top = _mix(panel_surface, white, 0.13)
    button_hover_bottom = _mix(panel_surface, white, 0.04)
    button_primary_gradient_top = _mix(panel, seed.accent, 0.30)
    button_primary_gradient_bottom = _mix(panel, seed.accent, 0.18)
    button_warning_gradient_top = _mix(panel, seed.warning, 0.30)
    button_warning_gradient_bottom = _mix(panel, seed.warning, 0.18)
    button_danger_gradient_top = _mix(panel, seed.danger, 0.30)
    button_danger_gradient_bottom = _mix(panel, seed.danger, 0.18)
    hover_overlay = _rgba(_mix(panel_surface, white, 0.18), 235)
    menu_border_subtle = _rgba(_mix(seed.base_bg, seed.border, 0.18), 210)
    scrollbar_track_bg = _rgba(_mix(seed.base_bg, black, 0.22), 210)

    # Card chrome (replacing hardcoded rgba values)
    card_border = _mix(seed.base_bg, seed.border, 0.14)
    card_hover_border = _mix(seed.base_bg, seed.accent, 0.24)
    input_border = _mix(seed.base_bg, seed.border, 0.10)
    toolbar_bg = _mix(seed.base_bg, black, 0.30)

    return {
        "bg_top": bg_top,
        "bg_bottom": bg_bottom,
        "header_from": header_from,
        "header_mid": header_mid,
        "header_to": header_to,
        "panel": panel,
        "panel_alt": panel_alt,
        "panel_elevated": panel_elevated,
        "panel_inset": panel_inset,
        "panel_surface": panel_surface,
        "panel_surface_alt": panel_surface_alt,
        "border": seed.border,
        "border_soft": _mix(seed.base_bg, seed.border, 0.28),
        "accent": seed.accent,
        "accent_soft": seed.accent_soft,
        "accent_deep": accent_deep,
        "warning": seed.warning,
        "danger": seed.danger,
        "text": seed.text,
        "text_muted": seed.text_muted,
        "text_dim": seed.text_dim,
        "selection_bg": selection_bg,
        "selection_text": white if _mix(selection_bg, black, 0.5) != selection_bg else seed.text,
        "splitter": splitter,
        "splitter_hover": splitter_hover,
        "button_primary_bg": button_primary_bg,
        "button_primary_border": button_primary_border,
        "button_warning_bg": button_warning_bg,
        "button_warning_border": button_warning_border,
        "button_danger_bg": button_danger_bg,
        "button_danger_border": button_danger_border,
        "button_gradient_top": button_gradient_top,
        "button_gradient_bottom": button_gradient_bottom,
        "button_hover_top": button_hover_top,
        "button_hover_bottom": button_hover_bottom,
        "button_primary_gradient_top": button_primary_gradient_top,
        "button_primary_gradient_bottom": button_primary_gradient_bottom,
        "button_warning_gradient_top": button_warning_gradient_top,
        "button_warning_gradient_bottom": button_warning_gradient_bottom,
        "button_danger_gradient_top": button_danger_gradient_top,
        "button_danger_gradient_bottom": button_danger_gradient_bottom,
        "hover_overlay": hover_overlay,
        "menu_border_subtle": menu_border_subtle,
        "scrollbar_track_bg": scrollbar_track_bg,
        "card_border": card_border,
        "card_hover_border": card_hover_border,
        "input_border": input_border,
        "toolbar_bg": toolbar_bg,
        "scrollbar_handle_start": scrollbar_handle_start,
        "scrollbar_handle_stop": scrollbar_handle_stop,
        "scrollbar_handle_hover_start": scrollbar_handle_hover_start,
        "scrollbar_handle_hover_stop": scrollbar_handle_hover_stop,
        "sidebar_selected_bg": sidebar_selected_bg,
        "status_active": seed.accent_soft,
        "status_warning": seed.warning,
        "status_stale": seed.danger,
        "status_idle": seed.text_dim,
        "badge_bg": badge_bg,
        "badge_border": badge_border,
        "risk_high_bg": risk_high_bg,
        "risk_high_fg": seed.danger,
        "risk_medium_bg": risk_medium_bg,
        "risk_medium_fg": seed.warning,
        "risk_low_bg": risk_low_bg,
        "risk_low_fg": seed.accent_soft,
        "risk_unknown_bg": risk_unknown_bg,
        "risk_unknown_fg": seed.text_muted,
    }


def _theme(seed: ThemeSeed) -> OperatorConsoleTheme:
    return OperatorConsoleTheme(
        theme_id=seed.theme_id,
        display_name=seed.display_name,
        colors=_build_semantic_colors(seed),
    )


THEME_SEEDS = (
    ThemeSeed(
        theme_id="coral",
        display_name="Coral",
        base_bg="#1d1314",
        border="#ff6b6b",
        accent="#ff6b6b",
        accent_soft="#59a9ff",
        warning="#ffd166",
        danger="#ff6b6b",
        text="#fff4f1",
        text_muted="#f0d4cc",
        text_dim="#be978f",
    ),
    ThemeSeed(
        theme_id="claude",
        display_name="Claude",
        base_bg="#1b1714",
        border="#b0aea5",
        accent="#d97757",
        accent_soft="#6a9bcc",
        warning="#d97757",
        danger="#d97757",
        text="#f6efe8",
        text_muted="#ddd2c7",
        text_dim="#b0aea5",
    ),
    ThemeSeed(
        theme_id="codex",
        display_name="Codex",
        base_bg="#081420",
        border="#5cb8ff",
        accent="#5cb8ff",
        accent_soft="#4ade80",
        warning="#fbbf24",
        danger="#f87171",
        text="#f0f6fc",
        text_muted="#8b9eb0",
        text_dim="#5a7080",
    ),
    ThemeSeed(
        theme_id="chatgpt",
        display_name="ChatGPT",
        base_bg="#0f1715",
        border="#10a37f",
        accent="#10a37f",
        accent_soft="#3b82f6",
        warning="#f4be5c",
        danger="#ff6b6b",
        text="#ecfff8",
        text_muted="#c9e6dc",
        text_dim="#6b7280",
    ),
    ThemeSeed(
        theme_id="catppuccin",
        display_name="Catppuccin",
        base_bg="#1e1e2e",
        border="#b4befe",
        accent="#89b4fa",
        accent_soft="#a6e3a1",
        warning="#fab387",
        danger="#f38ba8",
        text="#f5e0dc",
        text_muted="#cdd6f4",
        text_dim="#6c7086",
    ),
    ThemeSeed(
        theme_id="dracula",
        display_name="Dracula",
        base_bg="#282a36",
        border="#bd93f9",
        accent="#8be9fd",
        accent_soft="#50fa7b",
        warning="#ffb86c",
        danger="#ff5555",
        text="#f8f8f2",
        text_muted="#d3d7e8",
        text_dim="#6272a4",
    ),
    ThemeSeed(
        theme_id="nord",
        display_name="Nord",
        base_bg="#2e3440",
        border="#88c0d0",
        accent="#88c0d0",
        accent_soft="#a3be8c",
        warning="#d08770",
        danger="#bf616a",
        text="#eceff4",
        text_muted="#d8dee9",
        text_dim="#4c566a",
    ),
    ThemeSeed(
        theme_id="tokyonight",
        display_name="Tokyo Night",
        base_bg="#1a1b26",
        border="#bb9af7",
        accent="#7aa2f7",
        accent_soft="#9ece6a",
        warning="#ff9e64",
        danger="#f7768e",
        text="#c0caf5",
        text_muted="#a9b1d6",
        text_dim="#565f89",
    ),
    ThemeSeed(
        theme_id="gruvbox",
        display_name="Gruvbox",
        base_bg="#282828",
        border="#fabd2f",
        accent="#83a598",
        accent_soft="#b8bb26",
        warning="#fe8019",
        danger="#fb4934",
        text="#ebdbb2",
        text_muted="#d5c4a1",
        text_dim="#928374",
    ),
    ThemeSeed(
        theme_id="ansi",
        display_name="ANSI",
        base_bg="#1b1b1b",
        border="#d7d7d7",
        accent="#7fdde8",
        accent_soft="#92cf7b",
        warning="#e7c76b",
        danger="#e07a7a",
        text="#f4f4f4",
        text_muted="#cccccc",
        text_dim="#7a7a7a",
    ),
    ThemeSeed(
        theme_id="none",
        display_name="None",
        base_bg="#151719",
        border="#a7afb5",
        accent="#d3d7da",
        accent_soft="#9da7af",
        warning="#e0b870",
        danger="#dd8a8a",
        text="#f5f7f8",
        text_muted="#c7d0d6",
        text_dim="#92a0a8",
    ),
    ThemeSeed(
        theme_id="minimal",
        display_name="Minimal",
        base_bg="#111315",
        border="#8fa3b0",
        accent="#d6dde3",
        accent_soft="#8fa3b0",
        warning="#e0b870",
        danger="#dd8a8a",
        text="#f5f7f8",
        text_muted="#c7d0d6",
        text_dim="#92a0a8",
    ),
)

from .runtime.theme_gallery import GALLERY_SEEDS

ALL_THEME_SEEDS: tuple[ThemeSeed, ...] = THEME_SEEDS + GALLERY_SEEDS

THEMES: dict[str, OperatorConsoleTheme] = {
    seed.theme_id: _theme(seed) for seed in ALL_THEME_SEEDS
}

DEFAULT_THEME_ID = "codex"


def available_theme_ids() -> tuple[str, ...]:
    """Return the supported theme ids in their intended UI order."""
    return tuple(seed.theme_id for seed in THEME_SEEDS)


def resolve_theme(theme_id: str | None) -> OperatorConsoleTheme:
    """Return a known theme, falling back to the default theme."""
    if theme_id is None:
        return THEMES[DEFAULT_THEME_ID]
    return THEMES.get(theme_id.lower(), THEMES[DEFAULT_THEME_ID])
