"""Navigation QSS: top tabs, monitor tabs, and sidebar nav."""

from __future__ import annotations

def qss_navigation(color: dict[str, str], token: dict[str, str]) -> str:
    return f"""
    /* Top-level nav: flatter editor/workbench tabs */
    QTabWidget#NavTabs {{
        background: {color["bg_top"]};
    }}

    QTabWidget#NavTabs::pane {{
        background: {color["bg_top"]};
        border: none;
        border-top: 1px solid {color["border_soft"]};
        top: -1px;
    }}

    QTabBar#NavTabBar {{
        background: {color["bg_top"]};
    }}

    QTabBar#NavTabBar::tab {{
        background: transparent;
        color: {color["text_dim"]};
        border: none;
        border-bottom: 2px solid transparent;
        padding: {token["padding_small"]}px {token["padding"]}px;
        margin-right: 4px;
        font-weight: 500;
        font-size: {token["font_size_small"]}px;
        min-width: 0px;
    }}

    QTabBar#NavTabBar::tab:selected {{
        background: transparent;
        color: {color["text"]};
        border-bottom-color: {color["accent"]};
        font-weight: 600;
    }}

    QTabBar#NavTabBar::tab:hover:!selected {{
        background: {color["panel_surface"]};
        color: {color["text"]};
    }}

    /* Monitor sub-tabs: flatter document tabs */
    QTabWidget#HelpTabs::pane,
    QTabWidget#MonitorTabs::pane {{
        background: {color["panel"]};
        border: 1px solid {color["border_soft"]};
        border-radius: {token["border_radius"]}px;
        border-top-left-radius: 0px;
        padding: {token["padding_small"]}px;
    }}

    QTabBar#MonitorTabBar {{
        background: transparent;
    }}

    QTabBar#MonitorTabBar::tab {{
        background: {color["panel_surface"]};
        color: {color["text_dim"]};
        border: 1px solid {color["border_soft"]};
        border-bottom: none;
        border-top-left-radius: {token["border_radius"]}px;
        border-top-right-radius: {token["border_radius"]}px;
        padding: {token["padding_small"]}px {token["padding"]}px;
        margin-right: 1px;
        font-weight: 500;
        font-size: {token["font_size_small"]}px;
        min-width: 72px;
    }}

    QTabBar#MonitorTabBar::tab:selected {{
        background: {color["panel"]};
        color: {color["text"]};
        border-color: {color["border_soft"]};
    }}

    QTabBar#MonitorTabBar::tab:hover:!selected {{
        background: {color["panel_inset"]};
        color: {color["text"]};
    }}

    /* Sidebar layout: nav list */
    QFrame#SidebarNav {{
        background: {color["panel"]};
        border: 1px solid {color["border_soft"]};
        border-radius: {token["border_radius"]}px;
    }}

    QListWidget#SidebarNavList {{
        background: transparent;
        border: none;
        font-size: {token["font_size_small"]}px;
        padding: 4px;
    }}

    QListWidget#SidebarNavList::item {{
        padding: {token["padding"]}px {token["padding"]}px;
        border-radius: {token["border_radius"]}px;
        color: {color["text_muted"]};
        font-weight: 500;
    }}

    QListWidget#SidebarNavList::item:selected {{
        background: {color["sidebar_selected_bg"]};
        color: {color["text"]};
        font-weight: 600;
    }}

    QListWidget#SidebarNavList::item:hover:!selected {{
        background: {color["panel_surface"]};
        color: {color["text"]};
    }}
    """
