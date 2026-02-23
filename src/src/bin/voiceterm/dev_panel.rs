//! Guarded Dev panel overlay that surfaces in-session developer stats.

use std::path::Path;
use std::time::Instant;

use voiceterm::devtools::DevModeSnapshot;

use crate::dev_command::{DevCommandKind, DevPanelCommandState};
use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{
    overlay_close_symbol, overlay_separator, resolved_overlay_border_set, Theme, ThemeColors,
};

const DEV_PANEL_MIN_WIDTH: usize = 52;
const DEV_PANEL_MAX_WIDTH: usize = 92;

#[must_use]
pub fn dev_panel_footer(colors: &ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    format!("[{close}] close {sep} Enter run {sep} X cancel")
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
    commands: &DevPanelCommandState,
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

    let now = Instant::now();
    let mut lines = vec![
        frame_top(&colors, borders, content_width),
        centered_title_line(&colors, borders, "VoiceTerm - Dev Tools", content_width),
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
        section_line(&colors, "Dev tools", content_width),
        value_line(
            &colors,
            "Controls",
            "Up/Down select | Enter run | X cancel",
            content_width,
        ),
    ];

    for index in 0..DevCommandKind::ALL.len() {
        lines.push(command_line(&colors, commands, index, content_width, now));
    }

    lines.push(value_line(
        &colors,
        "Active",
        &commands.active_summary(now),
        content_width,
    ));
    lines.push(value_line(
        &colors,
        "Last",
        &commands.last_summary(),
        content_width,
    ));
    lines.push(frame_separator(&colors, borders, content_width));
    lines.push(centered_title_line(
        &colors,
        borders,
        &dev_panel_footer(&colors),
        content_width,
    ));
    lines.push(frame_bottom(&colors, borders, content_width));
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

fn command_line(
    colors: &ThemeColors,
    commands: &DevPanelCommandState,
    index: usize,
    width: usize,
    now: Instant,
) -> String {
    let command = DevCommandKind::ALL[index];
    let marker = if commands.selected_command() == command {
        ">"
    } else {
        " "
    };
    let label = format!("{marker} [{}] {}", index + 1, command.label());
    let status = commands.status_for(command, now);
    value_line(colors, &label, &status, width)
}

pub fn dev_panel_height() -> usize {
    // 23 fixed chrome lines (frame/title/separators/sections/stat rows/footer)
    // plus one command row per DevCommandKind variant.
    23 + DevCommandKind::ALL.len()
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use super::*;

    #[test]
    fn format_dev_panel_contains_guard_metrics_and_dev_tools() {
        let command_state = DevPanelCommandState::default();
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
            &command_state,
            96,
        );

        assert!(panel.contains("Dev Tools"));
        assert!(panel.contains("Guard mode"));
        assert!(panel.contains("Transcript events"));
        assert!(panel.contains("240 ms"));
        assert!(panel.contains("[1] status"));
    }

    #[test]
    fn format_dev_panel_line_count_matches_height() {
        let command_state = DevPanelCommandState::default();
        let panel = format_dev_panel(Theme::Codex, None, false, None, &command_state, 96);
        assert_eq!(panel.lines().count(), dev_panel_height());
    }
}
