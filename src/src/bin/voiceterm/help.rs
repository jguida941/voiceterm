//! Help overlay that documents keyboard shortcuts directly in the terminal UI.

use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{overlay_close_symbol, overlay_separator, Theme, ThemeColors};

/// Keyboard shortcut definition.
pub struct Shortcut {
    /// Key combination (e.g., "Ctrl+R")
    pub key: &'static str,
    /// Description of what it does
    pub description: &'static str,
}

const RECORDING_SHORTCUTS: &[Shortcut] = &[
    Shortcut {
        key: "Ctrl+R",
        description: "Trigger capture (voice or image mode)",
    },
    Shortcut {
        key: "Ctrl+E",
        description: "Finalize capture (stage text only, no send)",
    },
];

const MODE_SHORTCUTS: &[Shortcut] = &[
    Shortcut {
        key: "Ctrl+V",
        description: "Toggle auto-voice mode",
    },
    Shortcut {
        key: "Ctrl+T",
        description: "Toggle send mode (auto/insert)",
    },
];

const APPEARANCE_SHORTCUTS: &[Shortcut] = &[
    Shortcut {
        key: "Ctrl+Y",
        description: "Theme Studio",
    },
    Shortcut {
        key: "Ctrl+G",
        description: "Quick theme cycle",
    },
    Shortcut {
        key: "Ctrl+U",
        description: "Cycle HUD style (full/min/hidden)",
    },
];

const SENSITIVITY_SHORTCUTS: &[Shortcut] = &[
    Shortcut {
        key: "Ctrl+]",
        description: "Less sensitive (+5 dB)",
    },
    Shortcut {
        key: "Ctrl+\\",
        description: "More sensitive (-5 dB)",
    },
    Shortcut {
        key: "Ctrl+/",
        description: "More sensitive (-5 dB)",
    },
];

const NAVIGATION_SHORTCUTS: &[Shortcut] = &[
    Shortcut {
        key: "?",
        description: "Show help",
    },
    Shortcut {
        key: "Ctrl+O",
        description: "Settings (persisted to config.toml)",
    },
    Shortcut {
        key: "Ctrl+H",
        description: "History (transcripts + chat lines)",
    },
    Shortcut {
        key: "Ctrl+N",
        description: "History (notifications)",
    },
    Shortcut {
        key: "Enter",
        description: "Send prompt",
    },
    Shortcut {
        key: "Ctrl+C",
        description: "Cancel / Forward to CLI",
    },
    Shortcut {
        key: "Ctrl+Q",
        description: "Exit VoiceTerm",
    },
];

const SHORTCUT_SECTIONS: &[(&str, &[Shortcut])] = &[
    ("Recording", RECORDING_SHORTCUTS),
    ("Mode", MODE_SHORTCUTS),
    ("Appearance", APPEARANCE_SHORTCUTS),
    ("Sensitivity", SENSITIVITY_SHORTCUTS),
    ("Navigation", NAVIGATION_SHORTCUTS),
];

const DOCS_URL: &str = "https://github.com/jguida941/voiceterm/blob/master/README.md";
const TROUBLESHOOTING_URL: &str =
    "https://github.com/jguida941/voiceterm/blob/master/guides/TROUBLESHOOTING.md";

#[must_use]
pub fn help_overlay_footer(colors: &ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    format!("[{close}] close {sep} ^O settings")
}

pub fn help_overlay_width_for_terminal(width: usize) -> usize {
    width.clamp(30, 50)
}

pub fn help_overlay_inner_width_for_terminal(width: usize) -> usize {
    help_overlay_width_for_terminal(width).saturating_sub(2)
}

/// Format the help overlay as a string.
pub fn format_help_overlay(theme: Theme, width: usize) -> String {
    let colors = theme.colors();
    let borders = &colors.borders;
    let mut lines = Vec::new();

    let content_width = help_overlay_width_for_terminal(width);

    lines.push(frame_top(&colors, borders, content_width));
    lines.push(centered_title_line(
        &colors,
        borders,
        "VoiceTerm - Shortcuts",
        content_width,
    ));
    lines.push(frame_separator(&colors, borders, content_width));

    for (idx, (title, shortcuts)) in SHORTCUT_SECTIONS.iter().enumerate() {
        lines.push(format_section_line(&colors, title, content_width));
        for shortcut in *shortcuts {
            lines.push(format_shortcut_line(&colors, shortcut, content_width));
        }
        if idx + 1 < SHORTCUT_SECTIONS.len() {
            lines.push(frame_separator(&colors, borders, content_width));
        }
    }

    lines.push(frame_separator(&colors, borders, content_width));
    lines.push(format_section_line(&colors, "Resources", content_width));
    lines.push(format_resource_link_line(
        &colors,
        "Docs",
        "README",
        DOCS_URL,
        content_width,
    ));
    lines.push(format_resource_link_line(
        &colors,
        "Troubleshooting",
        "Guide",
        TROUBLESHOOTING_URL,
        content_width,
    ));
    lines.push(frame_separator(&colors, borders, content_width));
    let footer = help_overlay_footer(&colors);
    lines.push(centered_title_line(
        &colors,
        borders,
        &footer,
        content_width,
    ));
    lines.push(frame_bottom(&colors, borders, content_width));

    lines.join("\n")
}

fn format_section_line(colors: &ThemeColors, title: &str, width: usize) -> String {
    let borders = &colors.borders;
    let inner_width = width.saturating_sub(2);
    let heading = format!(" {title}");
    let clipped = truncate_display(&heading, inner_width);
    let pad = " ".repeat(inner_width.saturating_sub(display_width(&clipped)));
    format!(
        "{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.dim,
        clipped,
        pad,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

fn format_shortcut_line(colors: &ThemeColors, shortcut: &Shortcut, width: usize) -> String {
    let borders = &colors.borders;
    let inner_width = width.saturating_sub(2);
    let key_width = 10;
    let desc_width = inner_width.saturating_sub(key_width + 4);
    let key_padded = format!("{:>width$}", shortcut.key, width = key_width);
    let desc_clipped = truncate_display(shortcut.description, desc_width);
    let desc_pad = " ".repeat(desc_width.saturating_sub(display_width(&desc_clipped)));

    format!(
        "{}{}{}  {}{}{}  {}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        colors.info,
        key_padded,
        colors.reset,
        desc_clipped,
        desc_pad,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

fn osc8_link(label: &str, url: &str) -> String {
    format!("\x1b]8;;{url}\x1b\\{label}\x1b]8;;\x1b\\")
}

fn format_resource_link_line(
    colors: &ThemeColors,
    label: &str,
    link_label: &str,
    url: &str,
    width: usize,
) -> String {
    let borders = &colors.borders;
    let inner_width = width.saturating_sub(2);
    let prefix = format!(" {label}: ");
    let visible_link = format!("[{link_label}]");
    let visible = format!("{prefix}{visible_link}");
    let visible_clipped = truncate_display(&visible, inner_width);
    let clipped_width = display_width(&visible_clipped);
    let padding = " ".repeat(inner_width.saturating_sub(clipped_width));

    let rendered = if display_width(&visible) > inner_width {
        visible_clipped
    } else {
        let linked = osc8_link(&visible_link, url);
        format!("{prefix}{linked}")
    };

    format!(
        "{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        rendered,
        padding,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

/// Calculate the height of the help overlay.
pub fn help_overlay_height() -> usize {
    let section_rows: usize = SHORTCUT_SECTIONS
        .iter()
        .map(|(_, shortcuts)| 1 + shortcuts.len())
        .sum();
    let inter_section_separators = SHORTCUT_SECTIONS.len().saturating_sub(1);

    // top + title + initial separator + section rows + separators
    // + resources separator + resources header + two resource lines
    // + footer separator + footer + bottom
    3 + section_rows + inter_section_separators + 7
}

/// Calculate the width of the help overlay.
#[allow(dead_code)]
pub fn help_overlay_width() -> usize {
    54 // Fixed width for consistent display
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shortcuts_defined_in_sections() {
        assert!(!SHORTCUT_SECTIONS.is_empty());
        assert!(SHORTCUT_SECTIONS.len() >= 5);
    }

    #[test]
    fn format_help_overlay_contains_shortcuts_and_sections() {
        let help = format_help_overlay(Theme::Coral, 60);
        assert!(help.contains("Recording"));
        assert!(help.contains("Ctrl+R"));
        assert!(help.contains("Mode"));
        assert!(help.contains("Ctrl+V"));
        assert!(help.contains("Navigation"));
        assert!(help.contains("?"));
        assert!(help.contains("Ctrl+N"));
        assert!(help.contains("Resources"));
        assert!(help.contains("Docs:"));
        assert!(help.contains("Troubleshooting:"));
    }

    #[test]
    fn format_help_overlay_line_count_matches_documented_height() {
        let help = format_help_overlay(Theme::Coral, 60);
        assert_eq!(help.lines().count(), help_overlay_height());
    }

    #[test]
    fn format_help_overlay_has_borders() {
        let help = format_help_overlay(Theme::Coral, 60);
        assert!(help.contains("┌"));
        assert!(help.contains("└"));
        assert!(help.contains("│"));
    }

    #[test]
    fn help_overlay_dimensions() {
        assert!(help_overlay_height() > 5);
        assert!(help_overlay_width() > 30);
    }

    #[test]
    fn help_overlay_size_helpers_use_expected_clamps() {
        assert_eq!(help_overlay_width_for_terminal(10), 30);
        assert_eq!(help_overlay_width_for_terminal(60), 50);
        assert_eq!(help_overlay_inner_width_for_terminal(10), 28);
        assert_eq!(help_overlay_inner_width_for_terminal(60), 48);
    }

    #[test]
    fn format_shortcut_line_respects_calculated_description_width() {
        let colors = Theme::None.colors();
        let line = format_shortcut_line(
            &colors,
            &Shortcut {
                key: "K",
                description: "1234567890ABCDEFGHIJ",
            },
            30,
        );
        assert_eq!(display_width(&line), 30);
        assert!(line.contains("1234567890ABCD"));
        assert!(!line.contains("1234567890ABCDE"));
    }

    #[test]
    fn help_overlay_height_matches_documented_formula() {
        let section_rows: usize = SHORTCUT_SECTIONS
            .iter()
            .map(|(_, shortcuts)| 1 + shortcuts.len())
            .sum();
        let inter_section_separators = SHORTCUT_SECTIONS.len().saturating_sub(1);
        assert_eq!(
            help_overlay_height(),
            3 + section_rows + inter_section_separators + 7
        );
    }

    #[test]
    fn format_help_overlay_no_color() {
        let help = format_help_overlay(Theme::None, 60);
        assert!(help.contains("Ctrl+R"));
        // Should not have ANSI color codes (only box drawing)
        assert!(!help.contains("\x1b[9"));
    }

    #[test]
    fn format_help_overlay_includes_clickable_resource_links() {
        let help = format_help_overlay(Theme::None, 60);
        assert!(help.contains("\x1b]8;;https://github.com/jguida941/voiceterm/blob/master/README.md\x1b\\[README]\x1b]8;;\x1b\\"));
        assert!(help.contains("\x1b]8;;https://github.com/jguida941/voiceterm/blob/master/guides/TROUBLESHOOTING.md\x1b\\[Guide]\x1b]8;;\x1b\\"));
    }

    #[test]
    fn format_resource_link_line_uses_osc8_when_visible_width_exactly_fits() {
        let colors = Theme::None.colors();
        let line = format_resource_link_line(&colors, "D", "R", DOCS_URL, 9);
        assert!(line.contains("\x1b]8;;"));
        assert!(line.contains("[R]"));
    }

    #[test]
    fn format_resource_link_line_omits_osc8_when_visible_width_overflows() {
        let colors = Theme::None.colors();
        let line = format_resource_link_line(&colors, "D", "R", DOCS_URL, 8);
        assert!(!line.contains("\x1b]8;;"));
        assert!(line.contains(" D: "));
    }

    #[test]
    fn help_overlay_footer_respects_ascii_glyph_set() {
        let mut colors = Theme::None.colors();
        colors.glyph_set = crate::theme::GlyphSet::Ascii;
        assert_eq!(help_overlay_footer(&colors), "[x] close | ^O settings");
    }
}
