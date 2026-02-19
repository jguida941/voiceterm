//! Transcript history storage and search so users can browse and replay past voice captures.

use std::collections::VecDeque;
use std::time::Instant;

use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{overlay_close_symbol, overlay_separator, Theme, ThemeColors};

/// Maximum number of transcript entries retained in history.
pub(crate) const MAX_HISTORY_ENTRIES: usize = 100;

/// A single transcript history entry.
#[derive(Debug, Clone)]
pub(crate) struct HistoryEntry {
    /// The transcript text that was captured.
    pub(crate) text: String,
    /// When this transcript was captured (retained for future time-based display).
    #[allow(dead_code)]
    pub(crate) captured_at: Instant,
    /// Sequential index (1-based) for display.
    pub(crate) sequence: u32,
}

/// Bounded transcript history with search support.
#[derive(Debug)]
pub(crate) struct TranscriptHistory {
    entries: VecDeque<HistoryEntry>,
    next_sequence: u32,
}

impl TranscriptHistory {
    pub(crate) fn new() -> Self {
        Self {
            entries: VecDeque::with_capacity(MAX_HISTORY_ENTRIES),
            next_sequence: 1,
        }
    }

    /// Record a new transcript in history.
    pub(crate) fn push(&mut self, text: String) {
        if text.trim().is_empty() {
            return;
        }
        if self.entries.len() >= MAX_HISTORY_ENTRIES {
            self.entries.pop_front();
        }
        let entry = HistoryEntry {
            text,
            captured_at: Instant::now(),
            sequence: self.next_sequence,
        };
        self.next_sequence = self.next_sequence.wrapping_add(1);
        self.entries.push_back(entry);
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
}

/// Overlay state for browsing transcript history.
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

/// Number of visible transcript rows in the overlay (excluding chrome).
const VISIBLE_ROWS: usize = 8;

/// Height of the transcript history overlay (fixed).
pub(crate) fn transcript_history_overlay_height() -> usize {
    // top + title + separator + search row + separator + VISIBLE_ROWS + separator + footer + bottom
    5 + VISIBLE_ROWS + 3
}

pub(crate) fn transcript_history_overlay_width(terminal_cols: usize) -> usize {
    terminal_cols.clamp(30, 60)
}

pub(crate) fn transcript_history_overlay_inner_width(terminal_cols: usize) -> usize {
    transcript_history_overlay_width(terminal_cols).saturating_sub(2)
}

pub(crate) fn transcript_history_overlay_footer(colors: &ThemeColors) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    format!("[{close}] close {sep} Enter replay")
}

/// Visible transcript rows count for scroll calculations.
pub(crate) fn transcript_history_visible_rows() -> usize {
    VISIBLE_ROWS
}

/// Row offset where transcript entries start (1-based from overlay top).
pub(crate) const TRANSCRIPT_HISTORY_ENTRY_START_ROW: usize = 6;

/// Format the transcript history overlay for display.
pub(crate) fn format_transcript_history_overlay(
    history: &TranscriptHistory,
    state: &TranscriptHistoryState,
    theme: Theme,
    terminal_cols: usize,
) -> String {
    let colors = theme.colors();
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

    // Search row
    let search_label = if state.search_query.is_empty() {
        format!(" {}Search: (type to filter){}", colors.dim, colors.reset)
    } else {
        format!(
            " {}Search:{} {}",
            colors.dim, colors.reset, state.search_query
        )
    };
    let search_clipped = truncate_display(&search_label, inner);
    let search_pad = " ".repeat(inner.saturating_sub(display_width(&search_clipped)));
    lines.push(format!(
        "{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        search_clipped,
        search_pad,
        colors.border,
        borders.vertical,
        colors.reset
    ));
    lines.push(frame_separator(&colors, borders, width));

    // Transcript entries
    let total = state.filtered_indices.len();
    if total == 0 {
        let msg = if history.is_empty() {
            "No transcripts yet"
        } else {
            "No matches"
        };
        let empty_line = format!(" {}{}{}", colors.dim, msg, colors.reset);
        let empty_clipped = truncate_display(&empty_line, inner);
        let empty_pad = " ".repeat(inner.saturating_sub(display_width(&empty_clipped)));
        lines.push(format!(
            "{}{}{}{}{}{}{}{}",
            colors.border,
            borders.vertical,
            colors.reset,
            empty_clipped,
            empty_pad,
            colors.border,
            borders.vertical,
            colors.reset
        ));
        // Fill remaining rows with blanks
        for _ in 1..VISIBLE_ROWS {
            let blank_pad = " ".repeat(inner);
            lines.push(format!(
                "{}{}{}{}{}{}{}",
                colors.border,
                borders.vertical,
                colors.reset,
                blank_pad,
                colors.border,
                borders.vertical,
                colors.reset
            ));
        }
    } else {
        let visible_end = (state.scroll_offset + VISIBLE_ROWS).min(total);
        let visible_slice = &state.filtered_indices[state.scroll_offset..visible_end];
        for (display_idx, &entry_idx) in visible_slice.iter().enumerate() {
            let abs_idx = state.scroll_offset + display_idx;
            let is_selected = abs_idx == state.selected;
            if let Some(entry) = history.get(entry_idx) {
                let prefix = if is_selected {
                    format!("{}>{}", colors.info, colors.reset)
                } else {
                    " ".to_string()
                };
                let seq_label = format!("#{}", entry.sequence);
                let text_budget =
                    inner.saturating_sub(display_width(&prefix) + display_width(&seq_label) + 2);
                let text_preview = truncate_display(entry.text.trim(), text_budget);
                let content = format!("{}{} {}", prefix, seq_label, text_preview);
                let content_clipped = truncate_display(&content, inner);
                let pad = " ".repeat(inner.saturating_sub(display_width(&content_clipped)));
                let row_color = if is_selected { colors.info } else { "" };
                let row_reset = if is_selected { colors.reset } else { "" };
                lines.push(format!(
                    "{}{}{}{}{}{}{}{}{}{}",
                    colors.border,
                    borders.vertical,
                    row_color,
                    colors.reset,
                    content_clipped,
                    pad,
                    row_reset,
                    colors.border,
                    borders.vertical,
                    colors.reset
                ));
            }
        }
        // Fill remaining visible rows
        let rendered = visible_end - state.scroll_offset;
        for _ in rendered..VISIBLE_ROWS {
            let blank_pad = " ".repeat(inner);
            lines.push(format!(
                "{}{}{}{}{}{}{}",
                colors.border,
                borders.vertical,
                colors.reset,
                blank_pad,
                colors.border,
                borders.vertical,
                colors.reset
            ));
        }
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
        for i in 0..MAX_HISTORY_ENTRIES + 10 {
            history.push(format!("entry {i}"));
        }
        assert_eq!(history.len(), MAX_HISTORY_ENTRIES);
        // Oldest entries should have been dropped
        let first = history.get(0).unwrap();
        assert!(first.text.starts_with("entry 10"));
    }

    #[test]
    fn history_sequence_increments() {
        let mut history = TranscriptHistory::new();
        history.push("one".to_string());
        history.push("two".to_string());
        assert_eq!(history.get(0).unwrap().sequence, 1);
        assert_eq!(history.get(1).unwrap().sequence, 2);
    }

    #[test]
    fn search_returns_newest_first() {
        let mut history = TranscriptHistory::new();
        history.push("alpha".to_string());
        history.push("beta".to_string());
        history.push("alpha two".to_string());
        let results = history.search("alpha");
        assert_eq!(results.len(), 2);
        // Newest first: index 2 before index 0
        assert_eq!(results[0], 2);
        assert_eq!(results[1], 0);
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
    }

    #[test]
    fn all_newest_first_order() {
        let mut history = TranscriptHistory::new();
        history.push("a".to_string());
        history.push("b".to_string());
        history.push("c".to_string());
        let indices = history.all_newest_first();
        assert_eq!(indices, vec![2, 1, 0]);
    }

    #[test]
    fn state_move_up_down() {
        let mut state = TranscriptHistoryState::new();
        state.filtered_indices = vec![2, 1, 0];
        assert_eq!(state.selected, 0);
        state.move_down();
        assert_eq!(state.selected, 1);
        state.move_down();
        assert_eq!(state.selected, 2);
        state.move_down(); // should not go past end
        assert_eq!(state.selected, 2);
        state.move_up();
        assert_eq!(state.selected, 1);
        state.move_up();
        assert_eq!(state.selected, 0);
        state.move_up(); // should not go negative
        assert_eq!(state.selected, 0);
    }

    #[test]
    fn state_clamp_scroll() {
        let mut state = TranscriptHistoryState::new();
        state.filtered_indices = (0..20).collect();
        state.selected = 15;
        state.scroll_offset = 0;
        state.clamp_scroll(5);
        assert_eq!(state.scroll_offset, 11); // 15 - (5-1) = 11
    }

    #[test]
    fn state_clamp_scroll_zero_visible() {
        let mut state = TranscriptHistoryState::new();
        state.filtered_indices = (0..5).collect();
        state.selected = 3;
        state.scroll_offset = 0;
        state.clamp_scroll(0);
        // No change when visible is 0
        assert_eq!(state.scroll_offset, 0);
    }

    #[test]
    fn state_selected_entry_index() {
        let mut state = TranscriptHistoryState::new();
        state.filtered_indices = vec![5, 3, 1];
        state.selected = 1;
        assert_eq!(state.selected_entry_index(), Some(3));
    }

    #[test]
    fn state_selected_entry_index_empty() {
        let state = TranscriptHistoryState::new();
        assert_eq!(state.selected_entry_index(), None);
    }

    #[test]
    fn state_push_and_pop_search_char() {
        let mut history = TranscriptHistory::new();
        history.push("hello".to_string());
        history.push("world".to_string());
        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);
        assert_eq!(state.filtered_indices.len(), 2);

        state.push_search_char('w', &history);
        assert_eq!(state.search_query, "w");
        assert_eq!(state.filtered_indices.len(), 1);

        state.pop_search_char(&history);
        assert_eq!(state.search_query, "");
        assert_eq!(state.filtered_indices.len(), 2);
    }

    #[test]
    fn overlay_height_matches_formula() {
        assert_eq!(transcript_history_overlay_height(), 5 + VISIBLE_ROWS + 3);
    }

    #[test]
    fn overlay_width_clamps() {
        assert_eq!(transcript_history_overlay_width(20), 30);
        assert_eq!(transcript_history_overlay_width(100), 60);
        assert_eq!(transcript_history_overlay_width(45), 45);
    }

    #[test]
    fn format_overlay_empty_history() {
        let history = TranscriptHistory::new();
        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 80);
        assert!(output.contains("No transcripts yet"));
    }

    #[test]
    fn format_overlay_with_entries() {
        let mut history = TranscriptHistory::new();
        history.push("test transcript one".to_string());
        history.push("test transcript two".to_string());
        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 80);
        assert!(output.contains("#1"));
        assert!(output.contains("#2"));
        assert!(output.contains("Transcript History"));
    }

    #[test]
    fn format_overlay_line_count_matches_height() {
        let history = TranscriptHistory::new();
        let mut state = TranscriptHistoryState::new();
        state.refresh_filter(&history);
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 80);
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
        assert_eq!(state.filtered_indices.len(), 2);
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 80);
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
        assert!(state.filtered_indices.is_empty());
        let output = format_transcript_history_overlay(&history, &state, Theme::None, 80);
        assert!(output.contains("No matches"));
    }

    #[test]
    fn footer_respects_glyph_set() {
        let mut colors = Theme::None.colors();
        colors.glyph_set = crate::theme::GlyphSet::Ascii;
        let footer = transcript_history_overlay_footer(&colors);
        assert!(footer.contains("[x] close"));
        assert!(footer.contains("Enter replay"));
    }
}
