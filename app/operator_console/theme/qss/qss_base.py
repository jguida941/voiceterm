"""Base QSS: window backgrounds, typography, toolbar, status bar."""

from __future__ import annotations

from ..config.style_resolver import (
    resolved_border_width,
    resolved_radius,
    theme_choice,
)


def qss_base(
    color: dict[str, str],
    token: dict[str, str],
    components: dict[str, str],
    motion: dict[str, str],
) -> str:
    del motion
    radius = resolved_radius(token, components)
    radius_small = resolved_radius(token, components, size="small")
    border_width = resolved_border_width(token, components)
    surface_style = theme_choice(components, "surface_style", "layered")
    toolbar_bg = color["toolbar_bg"]
    if surface_style == "flat":
        toolbar_bg = color["panel_surface"]
    elif surface_style == "terminal":
        toolbar_bg = color["panel_inset"]
    return f"""
    QMainWindow {{
        background: {color["bg_top"]};
    }}

    QWidget {{
        color: {color["text"]};
        font-family: {token["font_family"]};
        font-size: {token["font_size"]}px;
        background: transparent;
    }}

    QWidget#RootWidget {{
        background: {color["bg_top"]};
    }}

    QFrame#Toolbar {{
        background: {toolbar_bg};
        border: {border_width}px solid {color["border_soft"]};
        border-radius: {radius}px;
        min-height: {token["toolbar_height"]}px;
    }}

    QLabel {{
        background: transparent;
        color: {color["text"]};
    }}

    QLabel#ToolbarTitle {{
        font-size: {token["font_size_large"]}px;
        font-weight: 700;
        color: {color["text"]};
        letter-spacing: -0.2px;
    }}

    QLabel#ToolbarAgentLabel {{
        font-size: {token["font_size_small"]}px;
        font-weight: 600;
        color: {color["text_muted"]};
    }}

    QLabel#ProviderBadge {{
        color: {color["text"]};
        background: {color["badge_bg"]};
        border: {border_width}px solid {color["badge_border"]};
        border-radius: {radius}px;
        padding: {token["padding_small"]}px {token["padding"]}px;
        font-size: {token["font_size_small"]}px;
        font-weight: 700;
        letter-spacing: 0.4px;
        min-width: 24px;
    }}

    QLabel#ProviderBadge[providerId="codex"] {{
        color: {color["accent"]};
    }}

    QLabel#ProviderBadge[providerId="claude"] {{
        color: {color["warning"]};
    }}

    QLabel#ProviderBadge[providerId="operator"] {{
        color: {color["text_muted"]};
    }}

    QLabel#ToolbarSettingLabel {{
        font-size: {token["font_size_small"]}px;
        color: {color["text_dim"]};
    }}

    QLabel#MutedLabel {{
        color: {color["text_dim"]};
        font-size: {token["font_size_small"]}px;
    }}

    QStatusBar {{
        background: {color["panel_inset"]};
        color: {color["text_muted"]};
        border-top: {border_width}px solid {color["border_soft"]};
    }}

    QMenuBar {{
        background: {color["bg_top"]};
        color: {color["text_muted"]};
        border-bottom: {border_width}px solid {color["menu_border_subtle"]};
    }}

    QMenuBar::item {{
        background: transparent;
        padding: {token["padding_small"]}px {token["padding_large"]}px;
        border-radius: {radius_small}px;
    }}

    QMenuBar::item:selected {{
        background: {color["hover_overlay"]};
        color: {color["text"]};
    }}

    QMenu {{
        background: {color["panel_surface"]};
        color: {color["text"]};
        border: {border_width}px solid {color["border_soft"]};
        border-radius: {radius}px;
        padding: {token["padding_small"]}px;
    }}

    QMenu::item {{
        padding: {token["padding_small"]}px {token["padding_large"]}px;
        border-radius: {radius_small}px;
    }}

    QMenu::item:selected {{
        background: {color["selection_bg"]};
        color: {color["selection_text"]};
    }}

    QToolTip {{
        background: {color["panel_inset"]};
        color: {color["text"]};
        border: {border_width}px solid {color["border_soft"]};
        border-radius: {radius_small}px;
        padding: {token["padding_small"]}px {token["padding"]}px;
    }}

    QSplitter::handle {{
        background: {color["splitter"]};
        border-radius: {radius_small}px;
        margin: 2px;
    }}

    QSplitter::handle:hover {{
        background: {color["splitter_hover"]};
    }}
    """
