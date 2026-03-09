"""Summary QSS: KPI cards, summary cards, and role badges."""

from __future__ import annotations

def qss_summary(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""
    QFrame#KPICard,
    QFrame#AgentSummaryCard {{
        background: {color["panel_surface"]};
        border: 1px solid {color["card_border"]};
        border-radius: {token["border_radius"]}px;
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
        border: 1px solid {color["border_soft"]};
        border-radius: {token["border_radius"]}px;
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
