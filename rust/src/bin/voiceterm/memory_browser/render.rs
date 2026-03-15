//! Overlay rendering for the Memory Browser (MP-233).

use crate::memory::types::MemoryEvent;
use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top,
    framed_content_line, truncate_display,
};
use crate::theme::{overlay_close_symbol, overlay_separator, Theme, ThemeColors};

use super::{MemoryBrowserState, BROWSER_VISIBLE_ROWS};

const DETAIL_ROWS: usize = 3;
pub(crate) const MEMORY_BROWSER_ENTRY_START_ROW: usize = 7;

pub(crate) fn memory_browser_overlay_height() -> usize {
    // top + title + separator + search + filter + separator + rows + separator + detail + separator + footer + bottom
    10 + BROWSER_VISIBLE_ROWS + DETAIL_ROWS
}

pub(crate) fn memory_browser_overlay_width(terminal_cols: usize) -> usize {
    terminal_cols.clamp(40, 100)
}

pub(crate) fn memory_browser_footer(colors: &ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    format!("[{close}] close {sep} Up/Down browse {sep} F filter {sep} A actions")
}

fn event_type_label(event: &MemoryEvent) -> &'static str {
    use crate::memory::types::EventType;
    match event.event_type {
        EventType::ChatTurn => "chat",
        EventType::VoiceTranscript => "voice",
        EventType::CommandIntent => "intent",
        EventType::CommandRun => "cmd",
        EventType::FileChange => "file",
        EventType::TestResult => "test",
        EventType::Decision => "decide",
        EventType::Handoff => "hand",
        EventType::Summary => "sum",
    }
}

fn search_row(
    colors: &ThemeColors,
    borders: &crate::theme::BorderSet,
    inner: usize,
    state: &MemoryBrowserState,
) -> String {
    let (search_text, search_color) = if state.search_query.is_empty() {
        (" Search: (type to filter)".to_string(), colors.dim)
    } else {
        (format!(" Search: {}", state.search_query), "")
    };
    framed_content_line(colors, borders, inner, &search_text, search_color)
}

fn filter_row(
    colors: &ThemeColors,
    borders: &crate::theme::BorderSet,
    inner: usize,
    state: &MemoryBrowserState,
) -> String {
    let filter_text = format!(" Filter: [{}]  (F to cycle)", state.filter.label());
    framed_content_line(colors, borders, inner, &filter_text, colors.dim)
}

fn render_event_rows(
    colors: &ThemeColors,
    borders: &crate::theme::BorderSet,
    inner: usize,
    state: &MemoryBrowserState,
    events: &[&MemoryEvent],
) -> Vec<String> {
    if events.is_empty() {
        return empty_event_rows(colors, borders, inner, state);
    }

    let visible_end = (state.scroll_offset + BROWSER_VISIBLE_ROWS).min(events.len());
    let visible_slice = &events[state.scroll_offset..visible_end];
    let mut rows = Vec::with_capacity(BROWSER_VISIBLE_ROWS);
    for (display_idx, event) in visible_slice.iter().enumerate() {
        let abs_idx = state.scroll_offset + display_idx;
        rows.push(event_row(
            colors,
            borders,
            inner,
            event,
            abs_idx == state.selected,
        ));
    }
    while rows.len() < BROWSER_VISIBLE_ROWS {
        rows.push(framed_content_line(colors, borders, inner, "", ""));
    }
    rows
}

fn empty_event_rows(
    colors: &ThemeColors,
    borders: &crate::theme::BorderSet,
    inner: usize,
    state: &MemoryBrowserState,
) -> Vec<String> {
    let msg = if state.search_query.is_empty() {
        "No memory events captured yet"
    } else {
        "No matching events"
    };
    let mut rows = vec![framed_content_line(
        colors,
        borders,
        inner,
        &format!(" {msg}"),
        colors.dim,
    )];
    while rows.len() < BROWSER_VISIBLE_ROWS {
        rows.push(framed_content_line(colors, borders, inner, "", ""));
    }
    rows
}

fn event_row(
    colors: &ThemeColors,
    borders: &crate::theme::BorderSet,
    inner: usize,
    event: &MemoryEvent,
    is_selected: bool,
) -> String {
    let marker = if is_selected { ">" } else { " " };
    let prefix = format!("{marker}[{}] ", event_type_label(event));
    let text_budget = inner.saturating_sub(display_width(&prefix));
    let text_preview = truncate_display(event.text.trim(), text_budget);
    let content = format!("{prefix}{text_preview}");
    let row_color = if is_selected { colors.info } else { "" };
    framed_content_line(colors, borders, inner, &content, row_color)
}

fn render_detail_rows(
    colors: &ThemeColors,
    borders: &crate::theme::BorderSet,
    inner: usize,
    state: &MemoryBrowserState,
    events: &[&MemoryEvent],
) -> Vec<String> {
    let Some(event) = state
        .detail_expanded
        .then(|| events.get(state.selected))
        .flatten()
    else {
        return detail_hint_rows(colors, borders, inner, events.is_empty());
    };

    vec![
        framed_content_line(
            colors,
            borders,
            inner,
            &format!(" Topics: {}", detail_value(&event.topic_tags)),
            colors.dim,
        ),
        framed_content_line(
            colors,
            borders,
            inner,
            &format!(" Entities: {}", detail_value(&event.entities)),
            colors.dim,
        ),
        framed_content_line(
            colors,
            borders,
            inner,
            &format!(
                " Tasks: {}  Importance: {:.1}",
                detail_value(&event.task_refs),
                event.importance
            ),
            colors.dim,
        ),
    ]
}

fn detail_hint_rows(
    colors: &ThemeColors,
    borders: &crate::theme::BorderSet,
    inner: usize,
    is_empty: bool,
) -> Vec<String> {
    let detail_hint = if is_empty {
        " No event selected"
    } else {
        " Tab expand details  |  Enter inject text"
    };
    let mut rows = vec![framed_content_line(
        colors,
        borders,
        inner,
        detail_hint,
        colors.dim,
    )];
    while rows.len() < DETAIL_ROWS {
        rows.push(framed_content_line(colors, borders, inner, "", ""));
    }
    rows
}

fn detail_value(values: &[String]) -> String {
    if values.is_empty() {
        "none".to_string()
    } else {
        values.join(", ")
    }
}

/// Format the Memory Browser overlay for display.
pub(crate) fn format_memory_browser_overlay(
    state: &MemoryBrowserState,
    events: &[&MemoryEvent],
    theme: Theme,
    terminal_cols: usize,
) -> String {
    let mut colors = theme.colors();
    colors.borders = crate::theme::resolved_overlay_border_set(theme);
    let borders = &colors.borders;
    let width = memory_browser_overlay_width(terminal_cols);
    let inner = width.saturating_sub(2);
    let mut lines = vec![
        frame_top(&colors, borders, width),
        centered_title_line(&colors, borders, "Memory Browser", width),
        frame_separator(&colors, borders, width),
        search_row(&colors, borders, inner, state),
        filter_row(&colors, borders, inner, state),
        frame_separator(&colors, borders, width),
    ];
    lines.extend(render_event_rows(&colors, borders, inner, state, events));
    lines.push(frame_separator(&colors, borders, width));
    lines.extend(render_detail_rows(&colors, borders, inner, state, events));
    lines.push(frame_separator(&colors, borders, width));
    lines.push(centered_title_line(
        &colors,
        borders,
        &memory_browser_footer(&colors),
        width,
    ));
    lines.push(frame_bottom(&colors, borders, width));

    lines.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::memory_browser::MemoryBrowserState;

    #[test]
    fn overlay_height_is_consistent() {
        assert!(memory_browser_overlay_height() > 10);
    }

    #[test]
    fn empty_browser_renders() {
        let state = MemoryBrowserState::new();
        let events: Vec<&MemoryEvent> = vec![];
        let output = format_memory_browser_overlay(&state, &events, Theme::None, 120);
        assert!(output.contains("Memory Browser"));
        assert!(output.contains("No memory events"));
    }
}
