//! Theme picker overlay.
//!
//! Displays available themes and allows selecting by number.

use crate::theme::{Theme, ThemeColors};

/// Theme options with labels.
pub const THEME_OPTIONS: &[(&str, &str)] = &[
    ("coral", "Default coral"),
    ("catppuccin", "Pastel dark"),
    ("dracula", "High contrast"),
    ("nord", "Arctic blue"),
    ("ansi", "ANSI 16-color"),
    ("none", "No color"),
];

pub fn format_theme_picker(theme: Theme, width: usize) -> String {
    let colors = theme.colors();
    let mut lines = Vec::new();
    let content_width = width.clamp(34, 54);

    lines.push(format_box_top(&colors, content_width));
    lines.push(format_title_line(
        &colors,
        "Codex Voice - Themes",
        content_width,
    ));
    lines.push(format_separator(&colors, content_width));

    for (idx, (name, desc)) in THEME_OPTIONS.iter().enumerate() {
        let label = format!("{}. {}", idx + 1, name);
        lines.push(format_option_line(&colors, &label, desc, content_width));
    }

    lines.push(format_separator(&colors, content_width));
    lines.push(format_title_line(
        &colors,
        "Press 1-6 to select • Esc to close",
        content_width,
    ));
    lines.push(format_box_bottom(&colors, content_width));

    lines.join("\n")
}

fn format_box_top(colors: &ThemeColors, width: usize) -> String {
    format!("{}┌{}┐{}", colors.info, "─".repeat(width + 2), colors.reset)
}

fn format_box_bottom(colors: &ThemeColors, width: usize) -> String {
    format!("{}└{}┘{}", colors.info, "─".repeat(width + 2), colors.reset)
}

fn format_separator(colors: &ThemeColors, width: usize) -> String {
    format!("{}├{}┤{}", colors.info, "─".repeat(width + 2), colors.reset)
}

fn format_title_line(colors: &ThemeColors, title: &str, width: usize) -> String {
    let padding = width.saturating_sub(title.len());
    let left_pad = padding / 2;
    let right_pad = padding - left_pad;
    format!(
        "{}│{} {}{}{} {}│{}",
        colors.info,
        colors.reset,
        " ".repeat(left_pad),
        title,
        " ".repeat(right_pad),
        colors.info,
        colors.reset
    )
}

fn format_option_line(colors: &ThemeColors, label: &str, desc: &str, width: usize) -> String {
    let label_width = 14;
    let desc_width = width.saturating_sub(label_width + 3);
    let label_padded = format!("{:<width$}", label, width = label_width);
    let desc_truncated: String = desc.chars().take(desc_width).collect();
    let desc_padded = format!("{:<width$}", desc_truncated, width = desc_width);

    format!(
        "{}│{} {}{}{}   {} {}│{}",
        colors.info,
        colors.reset,
        colors.success,
        label_padded,
        colors.reset,
        desc_padded,
        colors.info,
        colors.reset
    )
}

pub fn theme_picker_height() -> usize {
    3 + THEME_OPTIONS.len() + 3
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn theme_picker_contains_options() {
        let output = format_theme_picker(Theme::Coral, 60);
        assert!(output.contains("1. coral"));
        assert!(output.contains("6. none"));
    }

    #[test]
    fn theme_picker_has_borders() {
        let output = format_theme_picker(Theme::Coral, 60);
        assert!(output.contains("┌"));
        assert!(output.contains("└"));
        assert!(output.contains("│"));
    }

    #[test]
    fn theme_picker_height_positive() {
        assert!(theme_picker_height() > 5);
    }
}
