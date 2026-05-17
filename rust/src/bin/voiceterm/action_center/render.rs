//! Overlay rendering for the Action Center (MP-234).

use std::time::Instant;

use crate::dev_command::{ActionCategory, DevPanelState};
use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top,
    framed_content_line, truncate_display,
};
use crate::theme::{overlay_close_symbol, overlay_separator, Theme, ThemeColors};

pub(crate) const ACTION_CENTER_VISIBLE_ROWS: usize = 8;
const RESULT_ROWS: usize = 3;
pub(crate) const ACTION_CENTER_ENTRY_START_ROW: usize = 4;

pub(crate) fn action_center_overlay_height() -> usize {
    7 + ACTION_CENTER_VISIBLE_ROWS + RESULT_ROWS
}

pub(crate) fn action_center_overlay_width(terminal_cols: usize) -> usize {
    terminal_cols.clamp(40, 96)
}

pub(crate) fn action_center_footer(colors: &ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    format!("[{close}] close {sep} Enter run {sep} P profile {sep} X cancel {sep} B memory")
}

fn category_badge(category: ActionCategory) -> &'static str {
    match category {
        ActionCategory::ReadOnly => "[R]",
        ActionCategory::Mutating => "[M]",
        ActionCategory::OperatorApproval => "[!]",
    }
}

fn row_color(colors: &ThemeColors, is_pending: bool, is_selected: bool) -> &str {
    if is_pending {
        colors.warning
    } else if is_selected {
        colors.info
    } else {
        ""
    }
}

fn status_suffix(state: &DevPanelState, index: usize) -> String {
    let Some(entry) = state.catalog().get(index) else {
        return String::new();
    };
    let Some(command) = entry.dev_command() else {
        return String::new();
    };
    format!(" {}", state.status_for(command, Instant::now()))
}

fn render_result_pane(
    colors: &ThemeColors,
    borders: &crate::theme::BorderSet,
    inner: usize,
    state: &DevPanelState,
) -> Vec<String> {
    let mut lines = Vec::new();
    lines.push(framed_content_line(
        colors,
        borders,
        inner,
        &format!(
            " Profile: {}  |  Status: {}",
            state.execution_profile().label(),
            state.active_summary(Instant::now())
        ),
        colors.info,
    ));

    if let Some(completion) = state.last_completion() {
        lines.push(framed_content_line(
            colors,
            borders,
            inner,
            &format!(
                " Last: {} {} ({}ms)",
                completion.command.label(),
                completion.status.label(),
                completion.duration_ms
            ),
            colors.dim,
        ));
        lines.push(framed_content_line(
            colors,
            borders,
            inner,
            &format!("   {}", state.last_summary()),
            colors.dim,
        ));
    } else {
        lines.push(framed_content_line(
            colors,
            borders,
            inner,
            " No action results yet",
            colors.dim,
        ));
        lines.push(framed_content_line(colors, borders, inner, "", ""));
    }
    lines
}

/// Format the Action Center overlay for display.
pub(crate) fn format_action_center_overlay(
    state: &DevPanelState,
    theme: Theme,
    terminal_cols: usize,
) -> String {
    let mut colors = theme.colors();
    colors.borders = crate::theme::resolved_overlay_border_set(theme);
    let borders = &colors.borders;
    let width = action_center_overlay_width(terminal_cols);
    let inner = width.saturating_sub(2);
    let mut lines = Vec::new();

    lines.push(frame_top(&colors, borders, width));
    lines.push(centered_title_line(
        &colors,
        borders,
        "Action Center",
        width,
    ));
    lines.push(frame_separator(&colors, borders, width));

    let entries = state.catalog().entries();
    let total = entries.len();
    let selected = state.selected_index();
    let scroll_offset = selected.saturating_sub(ACTION_CENTER_VISIBLE_ROWS.saturating_sub(1));
    let visible_end = (scroll_offset + ACTION_CENTER_VISIBLE_ROWS).min(total);
    let visible_slice = &entries[scroll_offset..visible_end];

    for (display_idx, action) in visible_slice.iter().enumerate() {
        let abs_idx = scroll_offset + display_idx;
        let is_selected = abs_idx == selected;
        let is_pending = state.pending_confirmation_index() == Some(abs_idx);
        let marker = if is_pending {
            "!"
        } else if is_selected {
            ">"
        } else {
            " "
        };
        let badge = category_badge(action.category());
        let status = status_suffix(state, abs_idx);
        let prefix = format!("{marker} {badge} ");
        let budget = inner.saturating_sub(display_width(&prefix) + display_width(&status));
        let label = truncate_display(action.label(), budget);
        let content = format!("{prefix}{label}{status}");
        lines.push(framed_content_line(
            &colors,
            borders,
            inner,
            &content,
            row_color(&colors, is_pending, is_selected),
        ));
    }
    let rendered = visible_end.saturating_sub(scroll_offset);
    for _ in rendered..ACTION_CENTER_VISIBLE_ROWS {
        lines.push(framed_content_line(&colors, borders, inner, "", ""));
    }

    lines.push(frame_separator(&colors, borders, width));
    lines.extend(render_result_pane(&colors, borders, inner, state));
    lines.push(frame_separator(&colors, borders, width));
    lines.push(centered_title_line(
        &colors,
        borders,
        &action_center_footer(&colors),
        width,
    ));
    lines.push(frame_bottom(&colors, borders, width));

    lines.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dev_command::DevPanelState;

    #[test]
    fn overlay_height_is_consistent() {
        assert!(action_center_overlay_height() > 10);
    }

    #[test]
    fn renders_builtin_actions() {
        let state = DevPanelState::default();
        let output = format_action_center_overlay(&state, Theme::None, 120);
        assert!(output.contains("Action Center"));
        assert!(output.contains("status"));
    }

    #[test]
    fn pending_approval_shows_exclamation_marker() {
        let mut state = DevPanelState::default();
        state.select_index(6);
        state.request_confirmation_at(6);
        let output = format_action_center_overlay(&state, Theme::None, 120);
        assert!(output.contains("!"));
    }
}
