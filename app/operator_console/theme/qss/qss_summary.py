"""Summary QSS: KPI cards, summary cards, and role badges."""

from __future__ import annotations

from ..config.style_resolver import (
    resolved_border_width,
    resolved_radius,
    theme_choice,
)


def qss_summary(
    color: dict[str, str],
    token: dict[str, str],
    components: dict[str, str],
    motion: dict[str, str],
) -> str:
    del motion
    radius = resolved_radius(token, components)
    border_width = resolved_border_width(token, components)
    surface_style = theme_choice(components, "surface_style", "layered")
    summary_background = color["panel_surface"]
    if surface_style == "flat":
        summary_background = color["panel"]
    elif surface_style == "terminal":
        summary_background = color["panel_inset"]
    return f"""
    QFrame#KPICard,
    QFrame#AgentSummaryCard {{
        background: {summary_background};
        border: {border_width}px solid {color["card_border"]};
        border-radius: {radius}px;
    }}

    QLabel#KPIValue {{
        font-size: {token["font_size_h2"]}px;
        font-weight: 700;
        color: {color["text"]};
        background: transparent;
    }}

    QLabel#KPILabel {{
        font-size: {token["font_size_small"]}px;
        font-weight: 500;
        color: {color["text_dim"]};
        background: transparent;
        letter-spacing: 0.3px;
    }}

    QLabel#CardAgentName {{
        font-size: {token["font_size_large"]}px;
        font-weight: 700;
        color: {color["text"]};
        background: transparent;
    }}

    QLabel#RoleBadge {{
        color: {color["text_muted"]};
        background: {color["panel_inset"]};
        border: {border_width}px solid {color["border_soft"]};
        border-radius: {radius}px;
        padding: {token["padding_small"]}px {token["padding"]}px;
        font-size: {token["font_size_small"]}px;
        font-weight: 600;
    }}

    QLabel#CardLaneLabel {{
        color: {color["text_muted"]};
        font-size: {token["font_size"]}px;
        background: transparent;
    }}

    QLabel#CardStatusLabel {{
        color: {color["text"]};
        font-size: {token["font_size"]}px;
        font-weight: 600;
        background: transparent;
    }}

    QLabel#CardDetailLabel {{
        color: {color["text_muted"]};
        font-size: {token["font_size_small"]}px;
        background: transparent;
    }}

    QLabel[digestMode="true"] {{
        color: {color["text"]};
        font-family: "SF Mono", "Menlo", "Consolas", monospace;
        font-size: {token["font_size_small"]}px;
        letter-spacing: 0.2px;
    }}
    """
