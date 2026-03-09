//! Actions page of the dev panel overlay — session stats, guard state, and the
//! devctl command catalog.

use std::path::Path;
use std::time::Instant;

use voiceterm::devtools::DevModeSnapshot;

use super::{panel_width, value_line};
use crate::dev_command::DevPanelState;
use crate::overlay_frame::{
    centered_title_line, frame_bottom, frame_separator, frame_top, section_line,
};
use crate::theme::{overlay_close_symbol, overlay_separator, resolved_overlay_border_set, Theme};

#[must_use]
pub fn dev_panel_footer(colors: &crate::theme::ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    format!("[{close}] close {sep} Enter run {sep} X cancel {sep} P profile {sep} Tab next")
}

pub fn format_dev_panel(
    theme: Theme,
    stats: Option<DevModeSnapshot>,
    dev_log_enabled: bool,
    dev_path: Option<&Path>,
    commands: &DevPanelState,
    width: usize,
) -> String {
    let mut colors = theme.colors();
    colors.borders = resolved_overlay_border_set(theme);
    let borders = &colors.borders;
    let content_width = panel_width(width);
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
        centered_title_line(&colors, borders, "VoiceTerm - Actions", content_width),
        frame_separator(&colors, borders, content_width),
        section_line(&colors, "Guard", content_width),
        value_line(&colors, "Guard mode", "ON (--dev)", content_width),
        value_line(
            &colors,
            "Exec profile",
            commands.execution_profile().label(),
            content_width,
        ),
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
            "1-9 select | Up/Down move | Enter run | X cancel",
            content_width,
        ),
    ];

    for index in 0..commands.catalog().len() {
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

fn command_line(
    colors: &crate::theme::ThemeColors,
    commands: &DevPanelState,
    index: usize,
    width: usize,
    now: Instant,
) -> String {
    let entry = &commands.catalog().entries()[index];
    let marker = if commands.selected_index() == index {
        ">"
    } else {
        " "
    };
    let cat = entry.category().marker();
    let label = format!("{marker} [{cat}{}] {}", index + 1, entry.label());
    let status = entry
        .dev_command()
        .map(|cmd| commands.status_for(cmd, now))
        .unwrap_or_else(|| "n/a".to_string());
    value_line(colors, &label, &status, width)
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use voiceterm::devtools::DevModeSnapshot;

    use crate::dev_command::DevPanelState;
    use crate::dev_panel::dev_panel_height;
    use crate::theme::Theme;

    use super::*;

    #[test]
    fn format_dev_panel_contains_guard_metrics_and_dev_tools() {
        let command_state = DevPanelState::default();
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

        assert!(panel.contains("Actions"));
        assert!(panel.contains("Guard mode"));
        assert!(panel.contains("Transcript events"));
        assert!(panel.contains("240 ms"));
        assert!(panel.contains("[R1] status"));
        assert!(panel.contains("Exec profile"));
        assert!(panel.contains("Guarded"));
    }

    #[test]
    fn format_dev_panel_line_count_matches_height() {
        let command_state = DevPanelState::default();
        let panel = format_dev_panel(Theme::Codex, None, false, None, &command_state, 96);
        assert_eq!(panel.lines().count(), dev_panel_height());
    }
}
