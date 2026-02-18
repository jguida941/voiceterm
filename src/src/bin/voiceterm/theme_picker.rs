//! Theme picker overlay that lets users switch palettes without restarting sessions.
//!
//! Displays available themes and allows selecting by number.
//! Now shows a visual preview of each theme's unique style.

use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{
    filled_indicator, overlay_close_symbol, overlay_move_hint, overlay_separator, Theme,
    ThemeColors,
};

/// Theme options with labels and descriptions.
pub const THEME_OPTIONS: &[(Theme, &str, &str)] = &[
    (Theme::ChatGpt, "chatgpt", "Emerald green (ChatGPT)"),
    (Theme::Claude, "claude", "Warm neutrals (Anthropic)"),
    (Theme::Codex, "codex", "Cool blue (Codex-style)"),
    (Theme::Coral, "coral", "Default red accents"),
    (Theme::Catppuccin, "catppuccin", "Pastel elegance"),
    (Theme::Dracula, "dracula", "Bold high contrast"),
    (Theme::Nord, "nord", "Rounded arctic blue"),
    (Theme::TokyoNight, "tokyonight", "Elegant purple/blue"),
    (Theme::Gruvbox, "gruvbox", "Warm retro earthy"),
    (Theme::Ansi, "ansi", "16-color compatible"),
    (Theme::None, "none", "No color styling"),
];

pub const THEME_PICKER_OPTION_START_ROW: usize = 4;

#[must_use]
pub fn theme_picker_footer(colors: &ThemeColors, locked_theme: Option<Theme>) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    if let Some(theme) = locked_theme {
        return format!("[{close}] close {sep} Theme locked: {theme}");
    }
    let move_hint = overlay_move_hint(colors.glyph_set);
    format!("[{close}] close {sep} {move_hint} move {sep} Enter select")
}

pub fn theme_picker_inner_width_for_terminal(width: usize) -> usize {
    width.clamp(40, 60)
}

pub fn theme_picker_total_width_for_terminal(width: usize) -> usize {
    theme_picker_inner_width_for_terminal(width).saturating_add(2)
}

pub fn format_theme_picker(
    current_theme: Theme,
    selected_idx: usize,
    width: usize,
    locked_theme: Option<Theme>,
) -> String {
    let display_theme = locked_theme.unwrap_or(current_theme);
    let colors = display_theme.colors();
    let borders = &colors.borders;
    let show_theme_preview = display_theme != Theme::None;
    let is_locked = locked_theme.is_some();
    let mut lines = Vec::new();
    let total_width = theme_picker_total_width_for_terminal(width);
    let inner_width = total_width.saturating_sub(2);

    lines.push(frame_top(&colors, borders, total_width));
    lines.push(centered_title_line(
        &colors,
        borders,
        "VoiceTerm - Themes",
        total_width,
    ));
    lines.push(frame_separator(&colors, borders, total_width));

    // Theme options with visual preview
    for (idx, (theme, name, desc)) in THEME_OPTIONS.iter().enumerate() {
        let theme_colors = theme.colors();
        let is_current = *theme == display_theme;
        let is_selected = idx == selected_idx;
        let row_dimmed = is_locked && !is_current;
        let marker = if is_locked {
            if is_current {
                "*"
            } else {
                " "
            }
        } else if is_selected {
            ">"
        } else if is_current {
            "*"
        } else {
            " "
        };
        lines.push(format_option_line_with_preview(
            &colors,
            borders,
            &theme_colors,
            idx + 1,
            name,
            desc,
            marker,
            inner_width,
            show_theme_preview,
            row_dimmed,
        ));
    }

    lines.push(frame_separator(&colors, borders, total_width));

    // Footer with clickable close button
    let footer = theme_picker_footer(&colors, locked_theme);
    lines.push(centered_title_line(&colors, borders, &footer, total_width));

    lines.push(frame_bottom(&colors, borders, total_width));

    lines.join("\n")
}

use crate::theme::BorderSet;

#[allow(clippy::too_many_arguments)]
fn format_option_line_with_preview(
    colors: &ThemeColors,
    borders: &BorderSet,
    theme_colors: &ThemeColors,
    num: usize,
    name: &str,
    desc: &str,
    marker: &str,
    inner_width: usize,
    show_theme_preview: bool,
    row_dimmed: bool,
) -> String {
    // Label: "1. coral"
    let label = format!("{}. {}", num, name);
    let label_col = 14;
    let label_padded = format!("{:<width$}", label, width = label_col);

    // Calculate remaining space for description
    // Layout: indicator(1) + space(1) + marker(1) + space(1) + label(14) + space(1) = 19 fixed
    let fixed_visible = 19;
    let desc_col = inner_width.saturating_sub(fixed_visible);
    let desc_clipped = truncate_display(desc, desc_col);
    let desc_padded = format!(
        "{desc_clipped}{}",
        " ".repeat(desc_col.saturating_sub(display_width(&desc_clipped)))
    );
    let (preview_color, preview_icon) = if show_theme_preview && !row_dimmed {
        (
            theme_colors.recording,
            filled_indicator(theme_colors.indicator_auto),
        )
    } else {
        ("", " ")
    };
    let row_style = if row_dimmed { colors.dim } else { "" };
    let row_style_reset = if row_dimmed { colors.reset } else { "" };

    // Build the row: exactly inner_width visible characters between borders
    // "{indicator} {marker} {label} {desc}" = 1+1+1+1+14+1+desc_col = 19+desc_col = inner_width
    format!(
        "{}{}{}{}{}{}{} {} {} {}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        row_style,
        preview_color,
        preview_icon,
        colors.reset,
        marker,
        label_padded,
        desc_padded,
        row_style_reset,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

pub fn theme_picker_height() -> usize {
    // Top border + title + separator + options + separator + footer + bottom border
    1 + 1 + 1 + THEME_OPTIONS.len() + 1 + 1 + 1
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fnv1a64(input: &str) -> u64 {
        let mut hash: u64 = 0xcbf29ce484222325;
        for byte in input.as_bytes() {
            hash ^= u64::from(*byte);
            hash = hash.wrapping_mul(0x100000001b3);
        }
        hash
    }

    #[test]
    fn theme_picker_contains_options() {
        let output = format_theme_picker(Theme::Coral, 0, 60, None);
        assert!(output.contains("1. chatgpt"));
        assert!(output.contains("11. none")); // 11 themes total now
    }

    #[test]
    fn theme_picker_has_borders() {
        let output = format_theme_picker(Theme::Coral, 0, 60, None);
        // Uses theme-specific borders
        let colors = Theme::Coral.colors();
        assert!(output.contains(colors.borders.top_left));
        assert!(output.contains(colors.borders.bottom_left));
        assert!(output.contains(colors.borders.vertical));
    }

    #[test]
    fn theme_picker_shows_current_theme() {
        let output = format_theme_picker(Theme::Dracula, 5, 60, None);
        // Should have marker for current theme (Dracula = option 6)
        assert!(output.contains(">"));
        assert!(output.contains("6. dracula"));
    }

    #[test]
    fn theme_picker_height_positive() {
        assert!(theme_picker_height() > 5);
    }

    #[test]
    fn theme_picker_none_theme_uses_neutral_preview_rows() {
        let output = format_theme_picker(Theme::None, 10, 60, None);
        assert!(!output.contains("\x1b["));
        assert!(!output.contains("◉"));
        assert!(!output.contains("⏺"));
        assert!(output.contains("11. none"));
    }

    #[test]
    fn theme_picker_snapshot_matrix_is_stable() {
        let cases = [
            (
                "none_w40_sel0",
                Theme::None,
                0usize,
                40usize,
                0x1789_6796_2829_cf6e,
            ),
            (
                "none_w60_sel10",
                Theme::None,
                10usize,
                60usize,
                0xb7db_fe92_fcec_9020,
            ),
            (
                "codex_w60_sel2",
                Theme::Codex,
                2usize,
                60usize,
                0x0c3a_0d6b_ed78_dbfa,
            ),
        ];

        let mut snapshot_lines = Vec::new();
        let mut mismatches = Vec::new();

        for (name, theme, selected_idx, width, expected) in cases {
            let rendered = format_theme_picker(theme, selected_idx, width, None);
            let actual = fnv1a64(&rendered);
            snapshot_lines.push(format!("{name}={actual:#018x}"));
            if actual != expected {
                mismatches.push(name);
            }
        }

        if !mismatches.is_empty() {
            panic!(
                "theme-picker snapshot mismatch: {}\n{}",
                mismatches.join(", "),
                snapshot_lines.join("\n")
            );
        }
    }

    #[test]
    fn theme_picker_footer_respects_ascii_glyph_set() {
        let mut colors = Theme::None.colors();
        colors.glyph_set = crate::theme::GlyphSet::Ascii;
        assert_eq!(
            theme_picker_footer(&colors, None),
            "[x] close | up/down move | Enter select"
        );
    }

    #[test]
    fn theme_picker_footer_reports_style_pack_lock() {
        let mut colors = Theme::None.colors();
        colors.glyph_set = crate::theme::GlyphSet::Ascii;
        assert_eq!(
            theme_picker_footer(&colors, Some(Theme::Codex)),
            "[x] close | Theme locked: codex"
        );
    }

    #[test]
    fn theme_picker_lock_disables_non_current_markers() {
        let output = format_theme_picker(Theme::Coral, 0, 60, Some(Theme::Codex));
        assert!(output.contains("Theme locked: codex"));
        assert!(output.contains("* 3. codex"));
        assert!(!output.contains("> 1. chatgpt"));
    }
}
