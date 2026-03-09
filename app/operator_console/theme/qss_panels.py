"""Panel QSS: lane cards, KV rows, section headers, data display."""

from __future__ import annotations


def qss_panels(color: dict[str, str], token: dict[str, str]) -> str:
    return (
        _editor_surface_rules(color, token)
        + _lane_panel_rules(color, token)
        + _approval_panel_rules(color, token)
        + _detail_dialog_rules(color, token)
    )


def _editor_surface_rules(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""
    QDialog#ThemeEditorDialog {{
        background: {color["bg_top"]};
    }}

    QDialog#OperatorHelpDialog {{
        background: {color["bg_top"]};
    }}

    QTextBrowser#HelpBrowser {{
        background: {color["panel_inset"]};
        color: {color["text"]};
        border: 1px solid {color["border_soft"]};
        border-radius: {token["border_radius"]}px;
        font-family: {token["font_family"]};
        font-size: {token["font_size"]}px;
    }}

    QFrame#ThemeEditorSidebar {{
        background: {color["panel"]};
        border: 1px solid {color["card_border"]};
        border-radius: {token["border_radius_large"]}px;
    }}

    QListWidget#ThemeEditorNav {{
        background: transparent;
        border: none;
        padding: {token["padding_small"]}px;
        font-size: {token["font_size"]}px;
    }}

    QListWidget#ThemeEditorNav::item {{
        padding: {token["padding"]}px {token["padding_large"]}px;
        border-radius: {token["border_radius"]}px;
        color: {color["text_muted"]};
    }}

    QListWidget#ThemeEditorNav::item:selected {{
        background: {color["sidebar_selected_bg"]};
        color: {color["accent"]};
        font-weight: 600;
    }}

    QListWidget#ThemeEditorNav::item:hover:!selected {{
        background: {color["button_gradient_top"]};
        color: {color["text"]};
    }}

    QGroupBox[editorSection="true"] {{
        background: {color["panel"]};
        border: 1px solid {color["card_border"]};
        border-radius: {token["border_radius_large"]}px;
        margin-top: 16px;
        padding: {token["padding_large"]}px;
        font-size: {token["font_size_h3"]}px;
        font-weight: 600;
    }}

    QGroupBox[editorSection="true"]::title {{
        subcontrol-origin: margin;
        left: {token["padding"]}px;
        padding: 0 {token["padding_small"]}px;
        color: {color["text"]};
    }}

    QLabel#StatusIndicator {{
        background: {color["status_idle"]};
        border-radius: 7px;
        border: none;
    }}

    QLabel#StatusIndicator[statusLevel="active"] {{
        background: {color["status_active"]};
    }}

    QLabel#StatusIndicator[statusLevel="warning"] {{
        background: {color["status_warning"]};
    }}

    QLabel#StatusIndicator[statusLevel="stale"] {{
        background: {color["status_stale"]};
    }}

    QLabel#StatusIndicator[statusLevel="idle"] {{
        background: {color["status_idle"]};
    }}

    QLabel#LaneAgentName {{
        font-size: {token["font_size_h2"]}px;
        font-weight: 700;
        color: {color["text"]};
        background: transparent;
    }}

    QLabel#LaneRoleLabel {{
        font-size: {token["font_size_small"]}px;
        font-weight: 400;
        color: {color["text_dim"]};
        background: transparent;
    }}
    """


def _lane_panel_rules(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""

    QFrame#LaneCard {{
        background: {color["panel"]};
        border: 1px solid {color["card_border"]};
        border-radius: {token["border_radius"]}px;
    }}

    QFrame#LaneCard:hover {{
        border-color: {color["card_hover_border"]};
    }}

    QWidget#CompactButtonGrid {{
        background: transparent;
    }}

    QLabel#SectionHeaderLabel {{
        font-size: {token["font_size_small"]}px;
        font-weight: 600;
        color: {color["text_muted"]};
        background: transparent;
    }}

    QLabel#KVLabel {{
        color: {color["text_dim"]};
        font-size: {token["font_size_small"]}px;
        font-weight: 600;
        background: transparent;
        letter-spacing: 0.4px;
        text-transform: uppercase;
    }}

    QLabel#KVValue {{
        color: {color["text"]};
        font-size: {token["font_size"]}px;
        background: transparent;
    }}

    QFrame#KVRow {{
        background: {color["panel_surface"]};
        border: 1px solid transparent;
        border-radius: {token["border_radius_small"]}px;
        padding: {token["padding_small"]}px {token["padding_small"]}px;
    }}

    QFrame#KVRow:hover {{
        background: {color["panel_surface_alt"]};
        border-color: {color["border_soft"]};
    }}

    QWidget#KVContainer,
    QWidget#PanelScrollViewport,
    QScrollArea#PanelScrollArea {{
        background: transparent;
        border-radius: 12px;
        border: none;
    }}

    QPlainTextEdit#PanelRawText {{
        background: {color["panel_inset"]};
        border: 1px solid {color["card_border"]};
        border-radius: {token["border_radius"]}px;
        padding: {token["padding_small"]}px {token["padding"]}px;
        font-family: "SF Mono", "Menlo", "Consolas", monospace;
        font-size: {token["font_size"]}px;
    }}

    QFrame#BottomPanel {{
        background: transparent;
    }}
    """


def _approval_panel_rules(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""
    /* ── Approval Queue Panel ──────────────────────────────── */

    QLabel#ApprovalCountBadge {{
        background: {color["accent"]};
        color: {color["bg_top"]};
        font-size: 11px;
        font-weight: 700;
        border-radius: 12px;
    }}

    QListWidget#ApprovalList {{
        background: {color["bg_top"]};
        border: 1px solid {color["border_soft"]};
        border-radius: {token["border_radius"]}px;
        padding: {token["padding_small"]}px;
        font-size: {token["font_size"]}px;
        color: {color["text"]};
    }}

    QListWidget#ApprovalList::item {{
        padding: {token["padding"]}px {token["padding_large"]}px;
        border-radius: {token["border_radius"]}px;
    }}

    QListWidget#ApprovalList::item:selected {{
        background: {color["accent"]};
        color: {color["bg_top"]};
    }}

    QFrame#ApprovalDetailPane {{
        background: {color["panel_inset"]};
        border: 1px solid {color["border_soft"]};
        border-radius: {token["border_radius"]}px;
    }}

    QLabel#ApprovalDetailHeader {{
        font-size: {token["font_size_large"]}px;
        font-weight: 600;
        color: {color["text"]};
        background: transparent;
    }}

    QLabel#ApprovalFlowLabel {{
        font-size: {token["font_size"]}px;
        color: {color["accent"]};
        background: transparent;
    }}

    QLabel#ApprovalActionLabel {{
        font-size: {token["font_size"]}px;
        color: {color["text_dim"]};
        background: transparent;
    }}

    QLabel#ApprovalRiskIndicator {{
        background: {color["risk_unknown_bg"]};
        color: {color["risk_unknown_fg"]};
        border-radius: {token["border_radius_small"]}px;
        padding: {token["padding_small"]}px {token["padding"]}px;
        font-weight: 600;
    }}

    QLabel#ApprovalRiskIndicator[riskLevel="high"] {{
        background: {color["risk_high_bg"]};
        color: {color["risk_high_fg"]};
    }}

    QLabel#ApprovalRiskIndicator[riskLevel="medium"] {{
        background: {color["risk_medium_bg"]};
        color: {color["risk_medium_fg"]};
    }}

    QLabel#ApprovalRiskIndicator[riskLevel="low"] {{
        background: {color["risk_low_bg"]};
        color: {color["risk_low_fg"]};
    }}

    QLabel#ApprovalBodyText {{
        font-size: {token["font_size"]}px;
        color: {color["text_muted"]};
        background: transparent;
    }}

    QLabel#ApprovalModeHint {{
        font-size: {token["font_size_small"]}px;
        color: {color["text_dim"]};
        background: transparent;
    }}

    QLabel#ApprovalEvidenceLabel {{
        font-size: {token["font_size_small"]}px;
        color: {color["text_dim"]};
        background: transparent;
    }}
    """


def _detail_dialog_rules(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""
    /* ── Collapsible KV Row Chevron ───────────────────────── */

    QLabel#KVChevron {{
        color: {color["text_dim"]};
        font-size: {token["font_size_small"]}px;
        background: transparent;
    }}

    /* ── Card Detail Button ───────────────────────────────── */

    QPushButton#CardDetailButton {{
        background: transparent;
        border: 1px solid {color["card_border"]};
        border-radius: {token["border_radius_large"]}px;
        color: {color["text_dim"]};
        font-size: {token["font_size_large"]}px;
        font-weight: 600;
    }}

    QPushButton#CardDetailButton:hover {{
        background: {color["button_hover_top"]};
        color: {color["text"]};
    }}

    /* ── Agent Detail Dialog ──────────────────────────────── */

    QDialog#AgentDetailDialog {{
        background: {color["bg_top"]};
    }}

    QLabel#DetailAgentName {{
        font-size: {token["font_size_h1"]}px;
        font-weight: 700;
        color: {color["text"]};
        background: transparent;
    }}

    QLabel#DetailRoleLabel {{
        font-size: {token["font_size_large"]}px;
        font-weight: 400;
        color: {color["text_dim"]};
        background: transparent;
    }}

    QLabel#DetailStatusBadge {{
        font-size: {token["font_size_small"]}px;
        font-weight: 700;
        color: {color["accent"]};
        background: {color["button_gradient_top"]};
        border-radius: {token["border_radius_small"]}px;
        padding: {token["padding_small"]}px {token["padding"]}px;
    }}

    QLabel#DetailLaneTitle {{
        font-size: {token["font_size"]}px;
        color: {color["text_muted"]};
        background: transparent;
    }}

    QPlainTextEdit#DiffView {{
        background: {color["panel_inset"]};
        font-family: {token["font_family_mono"]};
        font-size: {token["font_size"]}px;
    }}
    """
