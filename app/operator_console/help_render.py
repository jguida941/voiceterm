"""Themed terminal help for the Operator Console launcher."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .launch_support import manual_module_launch_command, preferred_launcher_command
from .theme import DEFAULT_THEME_ID, available_theme_ids, resolve_theme

MIN_HELP_WIDTH = 78
MAX_HELP_WIDTH = 112
DEFAULT_HELP_WIDTH = 96
FLAG_COL_WIDTH = 26
THEME_ID_COL_WIDTH = 12


@dataclass(frozen=True)
class OptionHelp:
    """Small help-row descriptor for launcher options."""

    flag: str
    description: str


@dataclass(frozen=True)
class ThemeHelp:
    """Visible help metadata for a named Operator Console theme."""

    summary: str
    reference_label: str | None = None
    reference_url: str | None = None


OPTIONS = (
    OptionHelp("-h, --help", "Show themed launcher help and exit."),
    OptionHelp("--dev-log", "Persist repo-visible diagnostics."),
    OptionHelp(
        "--log-dir PATH",
        "Override the repo-relative diagnostics root.",
    ),
    OptionHelp("--theme NAME", "Choose the console palette."),
    OptionHelp("--layout MODE", "Open directly into a layout mode."),
    OptionHelp("--ensure-pyqt6", "Install PyQt6 before launch if missing."),
)

THEME_HELP: dict[str, ThemeHelp] = {
    "coral": ThemeHelp("Warm coral accents."),
    "claude": ThemeHelp("Warm neutral palette."),
    "codex": ThemeHelp("Cool blue neutral default."),
    "chatgpt": ThemeHelp("Emerald-forward palette."),
    "catppuccin": ThemeHelp(
        "Pastel Mocha-inspired dark palette.",
        reference_label="Palette",
        reference_url="https://github.com/catppuccin/catppuccin",
    ),
    "dracula": ThemeHelp(
        "High-contrast purple/cyan palette.",
        reference_label="Site",
        reference_url="https://draculatheme.com",
    ),
    "nord": ThemeHelp(
        "Arctic blue-gray palette.",
        reference_label="Site",
        reference_url="https://www.nordtheme.com",
    ),
    "tokyonight": ThemeHelp(
        "Blue/purple night palette.",
        reference_label="Repo",
        reference_url="https://github.com/enkia/tokyo-night-vscode-theme",
    ),
    "gruvbox": ThemeHelp(
        "Warm retro earthy palette.",
        reference_label="Repo",
        reference_url="https://github.com/morhetz/gruvbox",
    ),
    "ansi": ThemeHelp("Safe 16-color mode for basic terminals."),
    "none": ThemeHelp("Muted neutral palette."),
    "minimal": ThemeHelp("Quiet low-distraction preset."),
}


def render_operator_console_help(
    theme_id: str | None = None,
    *,
    width: int | None = None,
    repo_root: Path | None = None,
) -> str:
    """Return themed terminal help for ``app.operator_console.run``."""
    theme = resolve_theme(theme_id or DEFAULT_THEME_ID)
    colors = theme.colors
    use_color = theme.theme_id != "none" and "NO_COLOR" not in os.environ
    border_color = _ansi_fg(colors["border"]) if use_color else ""
    accent_color = _ansi_fg(colors["accent"]) if use_color else ""
    accent_soft_color = _ansi_fg(colors["accent_soft"]) if use_color else ""
    warning_color = _ansi_fg(colors["warning"]) if use_color else ""
    text_color = _ansi_fg(colors["text"]) if use_color else ""
    muted_color = _ansi_fg(colors["text_muted"]) if use_color else ""
    dim_color = _ansi_fg(colors["text_dim"]) if use_color else ""
    reset = "\x1b[0m" if use_color else ""

    resolved_width = _resolved_width(width)
    inner_width = resolved_width - 2
    root = repo_root or Path(__file__).resolve().parents[2]

    lines = [
        _frame_top(resolved_width, border_color, reset),
        _frame_line(
            _styled("VoiceTerm Operator Console", accent_color, reset),
            "VoiceTerm Operator Console",
            inner_width,
            border_color,
            reset,
        ),
        _frame_line(
            _styled("Themed launcher help", muted_color, reset),
            "Themed launcher help",
            inner_width,
            border_color,
            reset,
        ),
        _frame_separator(resolved_width, border_color, reset),
    ]

    usage_rows = (
        f"Usage: {preferred_launcher_command()} [OPTIONS]",
        f"Alt:   {manual_module_launch_command()} [OPTIONS]",
        f"Theme: {theme.display_name} ({theme.theme_id})",
    )
    for row in usage_rows:
        lines.append(
            _frame_line(
                _styled(row, text_color, reset),
                row,
                inner_width,
                border_color,
                reset,
            )
        )

    lines.append(_frame_separator(resolved_width, border_color, reset))
    lines.append(_section_line("Options", inner_width, border_color, accent_soft_color, reset))
    for option in OPTIONS:
        flag_cell = option.flag.ljust(FLAG_COL_WIDTH)
        rendered = (
            f"{_styled('> ', warning_color, reset)}"
            f"{_styled(flag_cell, accent_color, reset)}"
            f"{_styled(option.description, muted_color, reset)}"
        )
        visible = f"> {flag_cell}{option.description}"
        lines.append(_frame_line(rendered, visible, inner_width, border_color, reset))

    lines.append(_frame_separator(resolved_width, border_color, reset))
    lines.append(_section_line("Themes", inner_width, border_color, accent_soft_color, reset))
    for theme_key in available_theme_ids():
        theme_label = resolve_theme(theme_key).display_name
        meta = THEME_HELP.get(
            theme_key,
            ThemeHelp(f"{theme_label} gallery palette."),
        )
        label_prefix = "* " if theme_key == theme.theme_id else "  "
        left = f"{label_prefix}{theme_key.ljust(THEME_ID_COL_WIDTH)}"
        summary = meta.summary
        link_visible = ""
        rendered_summary = summary
        if meta.reference_label and meta.reference_url:
            link_visible = f" [{meta.reference_label}]"
            rendered_summary = f"{summary} {_osc8_link(f'[{meta.reference_label}]', meta.reference_url)}"
        rendered = (
            f"{_styled(left, accent_color if theme_key == theme.theme_id else text_color, reset)}"
            f"{_styled(f'{theme_label}: ', text_color, reset)}"
            f"{_styled(rendered_summary, muted_color, reset)}"
        )
        visible = f"{left}{theme_label}: {summary}{link_visible}"
        lines.append(_frame_line(rendered, visible, inner_width, border_color, reset))

    lines.append(_frame_separator(resolved_width, border_color, reset))
    lines.append(_section_line("Resources", inner_width, border_color, accent_soft_color, reset))
    resource_rows = (
        (
            "Guide",
            "[Operator Console README]",
            (root / "app/operator_console/README.md").as_uri(),
        ),
        (
            "State Map",
            "[state/README.md]",
            (root / "app/operator_console/state/README.md").as_uri(),
        ),
        (
            "View Map",
            "[views/README.md]",
            (root / "app/operator_console/views/README.md").as_uri(),
        ),
        (
            "Theme Map",
            "[theme/README.md]",
            (root / "app/operator_console/theme/README.md").as_uri(),
        ),
        (
            "Test Map",
            "[tests/README.md]",
            (root / "app/operator_console/tests/README.md").as_uri(),
        ),
        (
            "Agent Rules",
            "[AGENTS.md]",
            (root / "app/operator_console/AGENTS.md").as_uri(),
        ),
        (
            "Launcher",
            "[operator_console.sh]",
            (root / "scripts/operator_console.sh").as_uri(),
        ),
        (
            "Plan",
            "[MP-359 operator_console.md]",
            (root / "dev/active/operator_console.md").as_uri(),
        ),
    )
    for label, link_label, url in resource_rows:
        prefix = f"{label}: "
        rendered = f"{_styled(prefix, text_color, reset)}{_osc8_link(link_label, url)}"
        visible = f"{prefix}{link_label}"
        lines.append(_frame_line(rendered, visible, inner_width, border_color, reset))

    lines.append(_frame_separator(resolved_width, border_color, reset))
    footer = "Tip: use --theme <name> --help to preview another launcher palette."
    lines.append(
        _frame_line(
            _styled(footer, dim_color, reset),
            footer,
            inner_width,
            border_color,
            reset,
        )
    )
    lines.append(_frame_bottom(resolved_width, border_color, reset))
    return "\n".join(lines)


def _resolved_width(width: int | None) -> int:
    if width is not None:
        return max(MIN_HELP_WIDTH, min(MAX_HELP_WIDTH, width))
    return max(
        MIN_HELP_WIDTH,
        min(MAX_HELP_WIDTH, shutil.get_terminal_size((DEFAULT_HELP_WIDTH, 24)).columns),
    )


def _ansi_fg(hex_color: str) -> str:
    red, green, blue = _hex_to_rgb(hex_color)
    return f"\x1b[38;2;{red};{green};{blue}m"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"expected #RRGGBB color, got {hex_color!r}")
    return tuple(int(value[index : index + 2], 16) for index in range(0, 6, 2))


def _frame_top(width: int, border_color: str, reset: str) -> str:
    return f"{border_color}┌{'─' * (width - 2)}┐{reset}"


def _frame_separator(width: int, border_color: str, reset: str) -> str:
    return f"{border_color}├{'─' * (width - 2)}┤{reset}"


def _frame_bottom(width: int, border_color: str, reset: str) -> str:
    return f"{border_color}└{'─' * (width - 2)}┘{reset}"


def _frame_line(
    rendered: str,
    visible: str,
    inner_width: int,
    border_color: str,
    reset: str,
) -> str:
    clipped_visible = visible[:inner_width]
    padding = " " * max(0, inner_width - len(clipped_visible))
    if len(visible) > inner_width:
        rendered = rendered[:inner_width]
    return f"{border_color}│{reset}{rendered}{padding}{border_color}│{reset}"


def _section_line(
    title: str,
    inner_width: int,
    border_color: str,
    section_color: str,
    reset: str,
) -> str:
    rendered = _styled(title, section_color, reset)
    return _frame_line(rendered, title, inner_width, border_color, reset)


def _styled(text: str, color: str, reset: str) -> str:
    if not color:
        return text
    return f"{color}{text}{reset}"


def _osc8_link(label: str, url: str) -> str:
    return f"\x1b]8;;{url}\x1b\\{label}\x1b]8;;\x1b\\"
