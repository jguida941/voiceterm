"""Navigation QSS: top tabs, monitor tabs, and sidebar nav."""

from __future__ import annotations

from ..config.style_resolver import (
    resolved_border_width,
    resolved_radius,
    theme_choice,
)


def qss_navigation(
    color: dict[str, str],
    token: dict[str, str],
    components: dict[str, str],
    motion: dict[str, str],
) -> str:
    del motion
    radius = resolved_radius(token, components)
    border_width = resolved_border_width(token, components)
    nav_tab_style = theme_choice(components, "nav_tab_style", "underline")
    monitor_tab_style = theme_choice(components, "monitor_tab_style", "boxed")

    nav_tab_rule = f"""
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
    """
    if nav_tab_style == "pill":
        nav_tab_rule = f"""
        QTabBar#NavTabBar::tab {{
            background: {color["panel_surface"]};
            color: {color["text_muted"]};
            border: {border_width}px solid {color["border_soft"]};
            border-radius: {radius}px;
            padding: {token["padding_small"]}px {token["padding"]}px;
            margin-right: 6px;
            font-weight: 600;
            font-size: {token["font_size_small"]}px;
            min-width: 0px;
        }}

        QTabBar#NavTabBar::tab:selected {{
            background: {color["selection_bg"]};
            color: {color["selection_text"]};
            border-color: {color["accent"]};
        }}

        QTabBar#NavTabBar::tab:hover:!selected {{
            background: {color["panel_surface_alt"]};
            color: {color["text"]};
        }}
        """
    elif nav_tab_style == "boxed":
        nav_tab_rule = f"""
        QTabBar#NavTabBar::tab {{
            background: {color["panel_surface"]};
            color: {color["text_dim"]};
            border: {border_width}px solid {color["border_soft"]};
            border-bottom: {border_width}px solid {color["border_soft"]};
            border-top-left-radius: {radius}px;
            border-top-right-radius: {radius}px;
            padding: {token["padding_small"]}px {token["padding"]}px;
            margin-right: 1px;
            font-weight: 600;
            font-size: {token["font_size_small"]}px;
            min-width: 0px;
        }}

        QTabBar#NavTabBar::tab:selected {{
            background: {color["panel_surface_alt"]};
            color: {color["text"]};
            border-color: {color["accent"]};
        }}

        QTabBar#NavTabBar::tab:hover:!selected {{
            background: {color["panel_inset"]};
            color: {color["text"]};
        }}
        """

    monitor_tab_rule = f"""
    QTabBar#MonitorTabBar::tab {{
        background: {color["panel_surface"]};
        color: {color["text_dim"]};
        border: {border_width}px solid {color["border_soft"]};
        border-bottom: none;
        border-top-left-radius: {radius}px;
        border-top-right-radius: {radius}px;
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
    """
    if monitor_tab_style == "pill":
        monitor_tab_rule = f"""
        QTabBar#MonitorTabBar::tab {{
            background: {color["panel_surface"]};
            color: {color["text_dim"]};
            border: {border_width}px solid {color["border_soft"]};
            border-radius: {radius}px;
            padding: {token["padding_small"]}px {token["padding"]}px;
            margin-right: 6px;
            font-weight: 600;
            font-size: {token["font_size_small"]}px;
            min-width: 72px;
        }}

        QTabBar#MonitorTabBar::tab:selected {{
            background: {color["selection_bg"]};
            color: {color["selection_text"]};
            border-color: {color["accent"]};
        }}

        QTabBar#MonitorTabBar::tab:hover:!selected {{
            background: {color["panel_surface_alt"]};
            color: {color["text"]};
        }}
        """
    elif monitor_tab_style == "underline":
        monitor_tab_rule = f"""
        QTabBar#MonitorTabBar::tab {{
            background: transparent;
            color: {color["text_dim"]};
            border: none;
            border-bottom: 2px solid transparent;
            padding: {token["padding_small"]}px {token["padding"]}px;
            margin-right: 6px;
            font-weight: 600;
            font-size: {token["font_size_small"]}px;
            min-width: 72px;
        }}

        QTabBar#MonitorTabBar::tab:selected {{
            color: {color["text"]};
            border-bottom-color: {color["accent"]};
        }}

        QTabBar#MonitorTabBar::tab:hover:!selected {{
            background: {color["hover_overlay"]};
            color: {color["text"]};
        }}
        """

    return f"""
    /* Top-level nav: flatter editor/workbench tabs */
    QTabWidget#NavTabs {{
        background: {color["bg_top"]};
    }}

    QTabWidget#NavTabs::pane {{
        background: {color["bg_top"]};
        border: none;
        border-top: {border_width}px solid {color["border_soft"]};
        top: -1px;
    }}

    QTabBar#NavTabBar {{
        background: {color["bg_top"]};
    }}

{nav_tab_rule}

    /* Monitor sub-tabs: flatter document tabs */
    QTabWidget#HelpTabs::pane,
    QTabWidget#MonitorTabs::pane {{
        background: {color["panel"]};
        border: {border_width}px solid {color["border_soft"]};
        border-radius: {radius}px;
        border-top-left-radius: 0px;
        padding: {token["padding_small"]}px;
    }}

    QTabBar#MonitorTabBar {{
        background: transparent;
    }}

{monitor_tab_rule}

    /* Sidebar layout: nav list */
    QFrame#SidebarNav {{
        background: {color["panel"]};
        border: {border_width}px solid {color["border_soft"]};
        border-radius: {radius}px;
    }}

    QListWidget#SidebarNavList {{
        background: transparent;
        border: none;
        font-size: {token["font_size_small"]}px;
        padding: 4px;
    }}

    QListWidget#SidebarNavList::item {{
        padding: {token["padding"]}px {token["padding"]}px;
        border-radius: {radius}px;
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
