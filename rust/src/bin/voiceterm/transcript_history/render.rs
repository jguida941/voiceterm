//! Overlay rendering for the transcript history browser.
//!
//! Extracted from `transcript_history.rs` (MP-265 module decomposition).

use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{overlay_close_symbol, overlay_separator, Theme, ThemeColors};

use super::{TranscriptHistory, TranscriptHistoryState};

/// Number of visible history rows in the overlay (excluding chrome).
const VISIBLE_ROWS: usize = 7;
const PREVIEW_ROWS: usize = 2;

/// Height of the transcript history overlay.
pub(crate) fn transcript_history_overlay_height() -> usize {
    // top + title + separator + search + separator + rows + separator + preview + separator + footer + bottom
    9 + VISIBLE_ROWS + PREVIEW_ROWS
}

pub(crate) fn transcript_history_overlay_width(terminal_cols: usize) -> usize {
    terminal_cols.clamp(40, 96)
}

pub(crate) fn transcript_history_overlay_inner_width(terminal_cols: usize) -> usize {
    transcript_history_overlay_width(terminal_cols).saturating_sub(2)
}

pub(crate) fn transcript_history_overlay_footer(colors: &ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    format!("[{close}] close {sep} Enter replay {sep} Up/Down browse")
}

pub(crate) fn transcript_history_visible_rows() -> usize {
    VISIBLE_ROWS
}

/// Row offset where list entries start (1-based from overlay top).
pub(crate) const TRANSCRIPT_HISTORY_ENTRY_START_ROW: usize = 6;

fn framed_overlay_row(
    colors: &ThemeColors,
    borders: &crate::theme::BorderSet,
    inner_width: usize,
    content: &str,
    content_color: &str,
) -> String {
    let clipped = truncate_display(content, inner_width);
    let pad = " ".repeat(inner_width.saturating_sub(display_width(&clipped)));
    let body_plain = format!("{clipped}{pad}");
    let body = if content_color.is_empty() {
        body_plain
    } else {
        format!("{content_color}{body_plain}{}", colors.reset)
    };

    format!(
        "{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        body,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

fn wrap_display_lines(text: &str, max_width: usize, max_lines: usize) -> Vec<String> {
    if max_lines == 0 {
        return Vec::new();
    }
    if max_width == 0 {
        return vec![String::new(); max_lines];
    }

    let mut lines = Vec::with_capacity(max_lines);
    let mut remainder = text.trim();
    while lines.len() < max_lines {
        if remainder.is_empty() {
            lines.push(String::new());
            continue;
        }

        let chunk = truncate_display(remainder, max_width);
        let chunk_len = chunk.len();
        lines.push(chunk);

        if chunk_len >= remainder.len() {
            remainder = "";
            continue;
        }
        remainder = remainder[chunk_len..].trim_start();
    }

    lines
}

/// Format the transcript history overlay for display.
pub(crate) fn format_transcript_history_overlay(
    history: &TranscriptHistory,
    state: &TranscriptHistoryState,
    theme: Theme,
    terminal_cols: usize,
) -> String {
    let mut colors = theme.colors();
    colors.borders = crate::theme::resolved_overlay_border_set(theme);
    let borders = &colors.borders;
    let width = transcript_history_overlay_width(terminal_cols);
    let inner = width.saturating_sub(2);
    let mut lines = Vec::new();

    lines.push(frame_top(&colors, borders, width));
    lines.push(centered_title_line(
        &colors,
        borders,
        "Transcript History",
        width,
    ));
    lines.push(frame_separator(&colors, borders, width));

    let (search_text, search_color) = if state.search_query.is_empty() {
        (" Search: (type to filter)".to_string(), colors.dim)
    } else {
        (format!(" Search: {}", state.search_query), "")
    };
    lines.push(framed_overlay_row(
        &colors,
        borders,
        inner,
        &search_text,
        search_color,
    ));
    lines.push(frame_separator(&colors, borders, width));

    let total = state.filtered_indices.len();
    if total == 0 {
        let msg = if history.is_empty() {
            "No transcripts yet"
        } else {
            "No matches"
        };
        lines.push(framed_overlay_row(
            &colors,
            borders,
            inner,
            &format!(" {msg}"),
            colors.dim,
        ));
        for _ in 1..VISIBLE_ROWS {
            lines.push(framed_overlay_row(&colors, borders, inner, "", ""));
        }
    } else {
        let visible_end = (state.scroll_offset + VISIBLE_ROWS).min(total);
        let visible_slice = &state.filtered_indices[state.scroll_offset..visible_end];
        for (display_idx, &entry_idx) in visible_slice.iter().enumerate() {
            let abs_idx = state.scroll_offset + display_idx;
            let is_selected = abs_idx == state.selected;
            if let Some(entry) = history.get(entry_idx) {
                let marker = if is_selected { ">" } else { " " };
                let prefix = format!("{marker}[{}] ", entry.source.short_label());
                let text_budget = inner.saturating_sub(display_width(&prefix));
                let text_preview = truncate_display(entry.text.trim(), text_budget);
                let content = format!("{prefix}{text_preview}");
                let row_color = if is_selected { colors.info } else { "" };
                lines.push(framed_overlay_row(
                    &colors, borders, inner, &content, row_color,
                ));
            }
        }
        let rendered = visible_end - state.scroll_offset;
        for _ in rendered..VISIBLE_ROWS {
            lines.push(framed_overlay_row(&colors, borders, inner, "", ""));
        }
    }

    lines.push(frame_separator(&colors, borders, width));

    let preview_seed = state
        .selected_entry_index()
        .and_then(|idx| history.get(idx))
        .map(|entry| {
            format!(
                " Preview [{} #{}]: {}",
                entry.source.short_label(),
                entry.sequence,
                entry.text.trim()
            )
        })
        .unwrap_or_else(|| {
            if total == 0 {
                " Preview: no entries".to_string()
            } else {
                " Preview: select an entry".to_string()
            }
        });
    for line in wrap_display_lines(&preview_seed, inner, PREVIEW_ROWS) {
        lines.push(framed_overlay_row(
            &colors, borders, inner, &line, colors.dim,
        ));
    }

    lines.push(frame_separator(&colors, borders, width));
    let footer = transcript_history_overlay_footer(&colors);
    lines.push(centered_title_line(&colors, borders, &footer, width));
    lines.push(frame_bottom(&colors, borders, width));

    lines.join("\n")
}
