//! Transcript history storage and search so users can browse and replay past voice captures.
//!
//! Overlay rendering lives in the `render` submodule (MP-265 decomposition).

mod render;

pub(crate) use render::{
    format_transcript_history_overlay, transcript_history_overlay_footer,
    transcript_history_overlay_height, transcript_history_overlay_inner_width,
    transcript_history_overlay_width, transcript_history_visible_rows,
    TRANSCRIPT_HISTORY_ENTRY_START_ROW,
};

use std::collections::VecDeque;
use std::time::Instant;

use crate::stream_line_buffer::StreamLineBuffer;

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
    pending_user_line: StreamLineBuffer,
    pending_assistant_line: StreamLineBuffer,
}

impl TranscriptHistory {
    pub(crate) fn new() -> Self {
        Self {
            entries: VecDeque::with_capacity(MAX_HISTORY_ENTRIES),
            next_sequence: 1,
            pending_user_line: StreamLineBuffer::new(MAX_STREAM_LINE_BYTES),
            pending_assistant_line: StreamLineBuffer::new(MAX_STREAM_LINE_BYTES),
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
                    self.pending_user_line.pop_char();
                }
                b'\t' => self.pending_user_line.push_char(' '),
                _ if b.is_ascii_control() => {}
                _ => self.pending_user_line.push_char(b as char),
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
                _ => self.pending_assistant_line.push_char(ch),
            }
        }
    }

    /// Flush any currently buffered stream lines into history.
    pub(crate) fn flush_pending_stream_lines(&mut self) {
        self.flush_pending_user_line();
        self.flush_pending_assistant_line();
    }

    /// Return the number of stored entries.
    #[cfg(test)]
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
    #[cfg(test)]
    pub(crate) fn all_newest_first(&self) -> Vec<usize> {
        (0..self.entries.len()).rev().collect()
    }

    fn flush_pending_user_line(&mut self) {
        let Some(line) = self.pending_user_line.take_line() else {
            return;
        };
        self.push_with_source(line, HistorySource::UserInput);
    }

    fn flush_pending_assistant_line(&mut self) {
        let Some(line) = self.pending_assistant_line.take_line() else {
            return;
        };
        self.push_with_source(line, HistorySource::AssistantOutput);
    }
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::overlay_frame::display_width;
    use crate::theme::Theme;

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
        // 9 chrome rows + 7 visible rows + 2 preview rows = 18
        assert_eq!(transcript_history_overlay_height(), 18);
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
