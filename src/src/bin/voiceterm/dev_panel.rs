//! Guarded Dev panel overlay that surfaces in-session developer stats.

use std::path::Path;

use voiceterm::devtools::DevModeSnapshot;

use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{
    overlay_close_symbol, overlay_separator, resolved_overlay_border_set, Theme, ThemeColors,
};

const DEV_PANEL_MIN_WIDTH: usize = 44;
const DEV_PANEL_MAX_WIDTH: usize = 74;

#[must_use]
pub fn dev_panel_footer(colors: &ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    format!("[{close}] close {sep} Ctrl+D toggle")
}

pub fn dev_panel_width_for_terminal(width: usize) -> usize {
    width.clamp(DEV_PANEL_MIN_WIDTH, DEV_PANEL_MAX_WIDTH)
}

pub fn dev_panel_inner_width_for_terminal(width: usize) -> usize {
    dev_panel_width_for_terminal(width).saturating_sub(2)
}

pub fn format_dev_panel(
    theme: Theme,
    stats: Option<DevModeSnapshot>,
    dev_log_enabled: bool,
    dev_path: Option<&Path>,
    width: usize,
) -> String {
    let mut colors = theme.colors();
    colors.borders = resolved_overlay_border_set(theme);
    let borders = &colors.borders;
    let content_width = dev_panel_width_for_terminal(width);
    let snapshot = stats.unwrap_or(DevModeSnapshot {
        transcript_count: 0,
        empty_count: 0,
        error_count: 0,
        total_words: 0,
        avg_latency_ms: None,
        buffered_events: 0,
    });
    let dev_logging = if dev_log_enabled { "ON" } else { "OFF" };
    let dev_root = if dev_log_enabled {
        dev_path
            .map(|value| value.display().to_string())
            .unwrap_or_else(|| "<default> ~/.voiceterm/dev".to_string())
    } else {
        "disabled".to_string()
    };
    let avg_latency = snapshot
        .avg_latency_ms
        .map(|value| format!("{value} ms"))
        .unwrap_or_else(|| "n/a".to_string());

    let lines = vec![
        frame_top(&colors, borders, content_width),
        centered_title_line(&colors, borders, "VoiceTerm - Dev Panel", content_width),
        frame_separator(&colors, borders, content_width),
        section_line(&colors, "Guard", content_width),
        value_line(&colors, "Guard mode", "ON (--dev)", content_width),
        value_line(&colors, "Dev logging", dev_logging, content_width),
        value_line(&colors, "Log root", &dev_root, content_width),
        frame_separator(&colors, borders, content_width),
        section_line(&colors, "Session stats", content_width),
        value_line(
            &colors,
            "Transcript events",
            &snapshot.transcript_count.to_string(),
            content_width,
        ),
        value_line(
            &colors,
            "Empty events",
            &snapshot.empty_count.to_string(),
            content_width,
        ),
        value_line(
            &colors,
            "Error events",
            &snapshot.error_count.to_string(),
            content_width,
        ),
        value_line(
            &colors,
            "Total words",
            &snapshot.total_words.to_string(),
            content_width,
        ),
        value_line(&colors, "Avg latency", &avg_latency, content_width),
        value_line(
            &colors,
            "Buffered events",
            &snapshot.buffered_events.to_string(),
            content_width,
        ),
        frame_separator(&colors, borders, content_width),
        centered_title_line(&colors, borders, &dev_panel_footer(&colors), content_width),
        frame_bottom(&colors, borders, content_width),
    ];
    lines.join("\n")
}

fn section_line(colors: &ThemeColors, title: &str, width: usize) -> String {
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

fn value_line(colors: &ThemeColors, label: &str, value: &str, width: usize) -> String {
    let borders = &colors.borders;
    let inner_width = width.saturating_sub(2);
    let label_width = 17;
    let value_width = inner_width.saturating_sub(label_width + 3);
    let prefix = format!(" {:<label_width$} ", label, label_width = label_width);
    let value = truncate_display(value, value_width);
    let value_pad = " ".repeat(value_width.saturating_sub(display_width(&value)));
    format!(
        "{}{}{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.info,
        prefix,
        colors.reset,
        value,
        value_pad,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

pub fn dev_panel_height() -> usize {
    18
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use super::*;

    #[test]
    fn format_dev_panel_contains_guard_and_metrics() {
        let panel = format_dev_panel(
            Theme::Coral,
            Some(DevModeSnapshot {
                transcript_count: 3,
                empty_count: 1,
                error_count: 2,
                total_words: 18,
                avg_latency_ms: Some(240),
                buffered_events: 6,
            }),
            true,
            Some(Path::new("/tmp/dev")),
            80,
        );

        assert!(panel.contains("Dev Panel"));
        assert!(panel.contains("Guard mode"));
        assert!(panel.contains("Transcript events"));
        assert!(panel.contains("240 ms"));
        assert!(panel.contains("Ctrl+D"));
    }

    #[test]
    fn format_dev_panel_line_count_matches_height() {
        let panel = format_dev_panel(Theme::Codex, None, false, None, 80);
        assert_eq!(panel.lines().count(), dev_panel_height());
    }
}
