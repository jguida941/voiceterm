//! Transcript history storage and search so users can browse and replay past voice captures.

use std::collections::VecDeque;
use std::time::Instant;

use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{overlay_close_symbol, overlay_separator, Theme, ThemeColors};

/// Maximum number of history entries retained.
pub(crate) const MAX_HISTORY_ENTRIES: usize = 300;

const MAX_STREAM_LINE_BYTES: usize = 1024;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum HistorySource {
    Transcript,
    UserInput,
    AssistantOutput,
}

impl HistorySource {
    fn short_label(self) -> &'static str {
        match self {
            Self::Transcript => "mic",
            Self::UserInput => "you",
            Self::AssistantOutput => "ai",
        }
    }

    pub(crate) fn replayable(self) -> bool {
        !matches!(self, Self::AssistantOutput)
    }
}

/// A single history entry.
#[derive(Debug, Clone)]
pub(crate) struct HistoryEntry {
    /// Captured text.
    pub(crate) text: String,
    /// Entry source.
    pub(crate) source: HistorySource,
    /// Capture timestamp (retained for future time-based UI).
    #[allow(dead_code)]
    pub(crate) captured_at: Instant,
    /// Sequential index (1-based).
    pub(crate) sequence: u32,
}

impl HistoryEntry {
    pub(crate) fn replayable(&self) -> bool {
        self.source.replayable()
    }
}

/// Bounded history with search support.
#[derive(Debug)]
pub(crate) struct TranscriptHistory {
    entries: VecDeque<HistoryEntry>,
    next_sequence: u32,
    pending_user_line: String,
    pending_user_line_truncated: bool,
    pending_assistant_line: String,
    pending_assistant_line_truncated: bool,
}

impl TranscriptHistory {
    pub(crate) fn new() -> Self {
        Self {
            entries: VecDeque::with_capacity(MAX_HISTORY_ENTRIES),
            next_sequence: 1,
            pending_user_line: String::new(),
            pending_user_line_truncated: false,
            pending_assistant_line: String::new(),
            pending_assistant_line_truncated: false,
        }
    }

    /// Record a new voice transcript.
    pub(crate) fn push(&mut self, text: String) {
        self.push_with_source(text, HistorySource::Transcript);
    }

    fn push_with_source(&mut self, text: String, source: HistorySource) {
        if text.trim().is_empty() {
            return;
        }
        if self.entries.len() >= MAX_HISTORY_ENTRIES {
            self.entries.pop_front();
        }
        let entry = HistoryEntry {
            text,
            source,
            captured_at: Instant::now(),
            sequence: self.next_sequence,
        };
        self.next_sequence = self.next_sequence.wrapping_add(1);
        self.entries.push_back(entry);
    }

    /// Ingest PTY input bytes and capture newline-delimited user messages.
    pub(crate) fn ingest_user_input_bytes(&mut self, bytes: &[u8]) {
        if bytes.is_empty() || bytes.contains(&0x1b) {
            return;
        }

        for &b in bytes {
            match b {
                b'\r' | b'\n' => self.flush_pending_user_line(),
                0x7f | 0x08 => {
                    self.pending_user_line.pop();
                }
                b'\t' => self.push_user_char(' '),
                _ if b.is_ascii_control() => {}
                _ => self.push_user_char(b as char),
            }
        }
    }

    /// Ingest PTY output bytes and capture newline-delimited backend lines.
    pub(crate) fn ingest_backend_output_bytes(&mut self, bytes: &[u8]) {
        if bytes.is_empty() {
            return;
        }

        let cleaned = voiceterm::codex::sanitize_pty_output(bytes);
        if cleaned.is_empty() {
            return;
        }

        for ch in cleaned.chars() {
            match ch {
                '\n' => self.flush_pending_assistant_line(),
                '\r' => {}
                _ if ch.is_control() => {}
                _ => self.push_assistant_char(ch),
            }
        }
    }

    /// Flush any currently buffered stream lines into history.
    pub(crate) fn flush_pending_stream_lines(&mut self) {
        self.flush_pending_user_line();
        self.flush_pending_assistant_line();
    }

    /// Return the number of stored entries.
    #[allow(dead_code)]
    pub(crate) fn len(&self) -> usize {
        self.entries.len()
    }

    /// Return true when no entries are stored.
    pub(crate) fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Get an entry by index (0 = oldest).
    pub(crate) fn get(&self, index: usize) -> Option<&HistoryEntry> {
        self.entries.get(index)
    }

    /// Search entries whose text contains the query (case-insensitive).
    /// Returns indices into the entries deque in newest-first order.
    pub(crate) fn search(&self, query: &str) -> Vec<usize> {
        if query.is_empty() {
            return (0..self.entries.len()).rev().collect();
        }
        let lower_query = query.to_ascii_lowercase();
        self.entries
            .iter()
            .enumerate()
            .rev()
            .filter(|(_, entry)| entry.text.to_ascii_lowercase().contains(&lower_query))
            .map(|(idx, _)| idx)
            .collect()
    }

    /// Return all entries in newest-first order.
    #[allow(dead_code)]
    pub(crate) fn all_newest_first(&self) -> Vec<usize> {
        (0..self.entries.len()).rev().collect()
    }

    fn push_user_char(&mut self, ch: char) {
        if self.pending_user_line.len() < MAX_STREAM_LINE_BYTES {
            self.pending_user_line.push(ch);
        } else {
            self.pending_user_line_truncated = true;
        }
    }

    fn push_assistant_char(&mut self, ch: char) {
        if self.pending_assistant_line.len() < MAX_STREAM_LINE_BYTES {
            self.pending_assistant_line.push(ch);
        } else {
            self.pending_assistant_line_truncated = true;
        }
    }

    fn flush_pending_user_line(&mut self) {
        let Some(line) = take_stream_line(
            &mut self.pending_user_line,
            &mut self.pending_user_line_truncated,
        ) else {
            return;
        };
        self.push_with_source(line, HistorySource::UserInput);
    }

    fn flush_pending_assistant_line(&mut self) {
        let Some(line) = take_stream_line(
            &mut self.pending_assistant_line,
            &mut self.pending_assistant_line_truncated,
        ) else {
            return;
        };
        self.push_with_source(line, HistorySource::AssistantOutput);
    }
}

fn take_stream_line(buffer: &mut String, truncated: &mut bool) -> Option<String> {
    let trimmed = buffer.trim();
    if trimmed.is_empty() {
        buffer.clear();
        *truncated = false;
        return None;
    }

    let mut line = trimmed.to_string();
    if *truncated {
        line.push_str(" ...");
    }
    buffer.clear();
    *truncated = false;
    Some(line)
}

/// Overlay state for browsing history.
#[derive(Debug)]
pub(crate) struct TranscriptHistoryState {
    /// Current search query (empty = show all).
    pub(crate) search_query: String,
    /// Filtered result indices (into TranscriptHistory.entries).
    pub(crate) filtered_indices: Vec<usize>,
    /// Currently selected row in the filtered list.
    pub(crate) selected: usize,
    /// Scroll offset for the visible window.
    pub(crate) scroll_offset: usize,
}

impl TranscriptHistoryState {
    pub(crate) fn new() -> Self {
        Self {
            search_query: String::new(),
            filtered_indices: Vec::new(),
            selected: 0,
            scroll_offset: 0,
        }
    }

    /// Refresh the filtered indices from the history based on the current query.
    pub(crate) fn refresh_filter(&mut self, history: &TranscriptHistory) {
        self.filtered_indices = history.search(&self.search_query);
        self.selected = 0;
        self.scroll_offset = 0;
    }

    /// Move selection up.
    pub(crate) fn move_up(&mut self) {
        if self.selected > 0 {
            self.selected -= 1;
            if self.selected < self.scroll_offset {
                self.scroll_offset = self.selected;
            }
        }
    }

    /// Move selection down.
    pub(crate) fn move_down(&mut self) {
        let max = self.filtered_indices.len().saturating_sub(1);
        if self.selected < max {
            self.selected += 1;
        }
    }

    /// Ensure scroll offset keeps the selected item visible for a given viewport.
    pub(crate) fn clamp_scroll(&mut self, visible_rows: usize) {
        if visible_rows == 0 {
            return;
        }
        if self.selected >= self.scroll_offset + visible_rows {
            self.scroll_offset = self.selected.saturating_sub(visible_rows.saturating_sub(1));
        }
        if self.selected < self.scroll_offset {
            self.scroll_offset = self.selected;
        }
    }

    /// Get the entry index of the currently selected item, if any.
    pub(crate) fn selected_entry_index(&self) -> Option<usize> {
        self.filtered_indices.get(self.selected).copied()
    }

    /// Append a character to the search query and re-filter.
    pub(crate) fn push_search_char(&mut self, ch: char, history: &TranscriptHistory) {
        self.search_query.push(ch);
        self.refresh_filter(history);
    }

    /// Remove the last character from the search query and re-filter.
    pub(crate) fn pop_search_char(&mut self, history: &TranscriptHistory) {
        self.search_query.pop();
        self.refresh_filter(history);
    }
}

// --- Overlay rendering ---

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

#[cfg(test)]
mod tests {
    use super::*;

    fn strip_ansi(input: &str) -> String {
        let mut out = String::with_capacity(input.len());
        let mut in_escape = false;
        for ch in input.chars() {
            if ch == '\x1b' {
                in_escape = true;
                continue;
            }
            if in_escape {
                if ch == 'm' {
                    in_escape = false;
                }
                continue;
            }
            out.push(ch);
        }
        out
    }

    #[test]
    fn history_push_and_len() {
        let mut history = TranscriptHistory::new();
        assert!(history.is_empty());
        history.push("hello world".to_string());
        assert_eq!(history.len(), 1);
        assert!(!history.is_empty());
    }

    #[test]
    fn history_ignores_blank_text() {
        let mut history = TranscriptHistory::new();
        history.push("   ".to_string());
        history.push("".to_string());
        assert!(history.is_empty());
    }

    #[test]
    fn history_bounds_at_max() {
        let mut history = TranscriptHistory::new();
        for i in 0..(MAX_HISTORY_ENTRIES + 20) {
            history.push(format!("entry {i}"));
        }
        assert_eq!(history.len(), MAX_HISTORY_ENTRIES);
        assert!(history
            .get(0)
            .unwrap_or_else(|| panic!("missing oldest after cap"))
            .text
            .contains("entry 20"));
    }

    #[test]
    fn history_sequence_increments() {
        let mut history = TranscriptHistory::new();
        history.push("one".to_string());
        history.push("two".to_string());
        assert_eq!(
            history.get(0).unwrap_or_else(|| panic!("entry")).sequence,
            1
        );
        assert_eq!(
            history.get(1).unwrap_or_else(|| panic!("entry")).sequence,
            2
        );
    }

    #[test]
    fn search_returns_newest_first() {
        let mut history = TranscriptHistory::new();
        history.push("alpha".to_string());
        history.push("beta".to_string());
        history.push("alpha two".to_string());

        let results = history.search("alpha");
        assert_eq!(results.len(), 2);
        assert!(history
            .get(results[0])
            .unwrap_or_else(|| panic!("entry"))
            .text
            .contains("alpha two"));
        assert!(history
            .get(results[1])
            .unwrap_or_else(|| panic!("entry"))
            .text
            .contains("alpha"));
    }

    #[test]
    fn search_case_insensitive() {
        let mut history = TranscriptHistory::new();
        history.push("Hello World".to_string());
        let results = history.search("hello");
        assert_eq!(results.len(), 1);
    }

    #[test]
    fn search_empty_query_returns_all() {
        let mut history = TranscriptHistory::new();
        history.push("one".to_string());
        history.push("two".to_string());
        let results = history.search("");
        assert_eq!(results.len(), 2);
        assert_eq!(results[0], 1);
        assert_eq!(results[1], 0);
    }

    #[test]
    fn state_move_and_scroll() {
        let mut history = TranscriptHistory::new();
        history.push("a".to_string());
        history.push("b".to_string());
        history.push("c".to_string());

        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);
        assert_eq!(state.selected, 0);

        state.move_down();
        assert_eq!(state.selected, 1);
        state.move_down();
        assert_eq!(state.selected, 2);
        state.move_down();
        assert_eq!(state.selected, 2);

        state.move_up();
        assert_eq!(state.selected, 1);
    }

    #[test]
    fn state_clamp_scroll_keeps_selection_visible() {
        let mut state = TranscriptHistoryState::new();
        state.filtered_indices = (0..10).collect();
        state.selected = 5;
        state.scroll_offset = 0;

        state.clamp_scroll(4);
        assert_eq!(state.scroll_offset, 2);

        state.selected = 1;
        state.clamp_scroll(4);
        assert_eq!(state.scroll_offset, 1);
    }

    #[test]
    fn state_selected_entry_index_returns_none_when_empty() {
        let state = TranscriptHistoryState::new();
        assert!(state.selected_entry_index().is_none());
    }

    #[test]
    fn state_push_and_pop_search_char() {
        let mut history = TranscriptHistory::new();
        history.push("hello".to_string());
        history.push("world".to_string());

        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);

        state.push_search_char('w', &history);
        assert_eq!(state.search_query, "w");
        assert_eq!(state.filtered_indices.len(), 1);

        state.pop_search_char(&history);
        assert_eq!(state.search_query, "");
        assert_eq!(state.filtered_indices.len(), 2);
    }

    #[test]
    fn overlay_height_matches_formula() {
        assert_eq!(
            transcript_history_overlay_height(),
            9 + VISIBLE_ROWS + PREVIEW_ROWS
        );
    }

    #[test]
    fn overlay_width_clamps() {
        assert_eq!(transcript_history_overlay_width(20), 40);
        assert_eq!(transcript_history_overlay_width(140), 96);
        assert_eq!(transcript_history_overlay_width(45), 45);
    }

    #[test]
    fn format_overlay_empty_history() {
        let history = TranscriptHistory::new();
        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 120);
        assert!(output.contains("No transcripts yet"));
        assert!(output.contains("Preview: no entries"));
    }

    #[test]
    fn format_overlay_with_entries_shows_source_tags() {
        let mut history = TranscriptHistory::new();
        history.push("test transcript one".to_string());
        history.push("test transcript two".to_string());
        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 120);
        assert!(output.contains("Transcript History"));
        assert!(output.contains("[mic]"));
    }

    #[test]
    fn format_overlay_line_count_matches_height() {
        let history = TranscriptHistory::new();
        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 120);
        assert_eq!(output.lines().count(), transcript_history_overlay_height());
    }

    #[test]
    fn format_overlay_with_search_filter() {
        let mut history = TranscriptHistory::new();
        history.push("alpha one".to_string());
        history.push("beta two".to_string());
        history.push("alpha three".to_string());
        let mut state = TranscriptHistoryState::new();
        state.search_query = "alpha".to_string();
        state.refresh_filter(&history);
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 120);
        assert!(output.contains("alpha"));
        assert!(!output.contains("No matches"));
    }

    #[test]
    fn format_overlay_no_matches_message() {
        let mut history = TranscriptHistory::new();
        history.push("hello world".to_string());
        let mut state = TranscriptHistoryState::new();
        state.search_query = "zzz".to_string();
        state.refresh_filter(&history);
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 120);
        assert!(output.contains("No matches"));
    }

    #[test]
    fn format_overlay_rows_keep_full_width_with_ansi_theme() {
        let history = TranscriptHistory::new();
        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);
        let terminal_cols = 120;
        let width = transcript_history_overlay_width(terminal_cols);
        let output =
            format_transcript_history_overlay(&history, &state, Theme::Codex, terminal_cols);

        for line in output.lines() {
            let visible = strip_ansi(line);
            assert_eq!(display_width(&visible), width);
        }
    }

    #[test]
    fn ingest_user_input_bytes_records_sent_lines() {
        let mut history = TranscriptHistory::new();
        history.ingest_user_input_bytes(b"implement feature\r");

        let newest = history
            .all_newest_first()
            .first()
            .copied()
            .unwrap_or_else(|| panic!("missing user entry"));
        let entry = history.get(newest).unwrap_or_else(|| panic!("entry"));
        assert_eq!(entry.source, HistorySource::UserInput);
        assert_eq!(entry.text, "implement feature");
    }

    #[test]
    fn ingest_user_input_bytes_ignores_escape_sequences() {
        let mut history = TranscriptHistory::new();
        history.ingest_user_input_bytes(b"\x1b[0[I");
        history.flush_pending_stream_lines();
        assert!(history.is_empty());
    }

    #[test]
    fn ingest_backend_output_bytes_records_lines() {
        let mut history = TranscriptHistory::new();
        history.ingest_backend_output_bytes(b"assistant output line\n");

        let newest = history
            .all_newest_first()
            .first()
            .copied()
            .unwrap_or_else(|| panic!("missing assistant entry"));
        let entry = history.get(newest).unwrap_or_else(|| panic!("entry"));
        assert_eq!(entry.source, HistorySource::AssistantOutput);
        assert_eq!(entry.text, "assistant output line");
    }

    #[test]
    fn assistant_entries_are_not_replayable() {
        let mut history = TranscriptHistory::new();
        history.ingest_backend_output_bytes(b"assistant output line\n");
        let newest = history
            .all_newest_first()
            .first()
            .copied()
            .unwrap_or_else(|| panic!("missing assistant entry"));
        let entry = history.get(newest).unwrap_or_else(|| panic!("entry"));
        assert!(!entry.replayable());
    }
}
