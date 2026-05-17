//! Memory Browser overlay state and filter logic (MP-233).
//!
//! Rendering lives in the `render` submodule.

pub(crate) mod render;

use crate::memory::types::{EventType, MemoryEvent};
use crate::overlay_list;

/// Filter categories for the Memory Browser.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum MemoryFilter {
    All,
    Decisions,
    Commands,
    ChatTurns,
    Voice,
    Files,
    Tests,
}

impl MemoryFilter {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::All => "All",
            Self::Decisions => "Decisions",
            Self::Commands => "Commands",
            Self::ChatTurns => "Chat",
            Self::Voice => "Voice",
            Self::Files => "Files",
            Self::Tests => "Tests",
        }
    }

    pub(crate) fn cycle(self) -> Self {
        match self {
            Self::All => Self::Decisions,
            Self::Decisions => Self::Commands,
            Self::Commands => Self::ChatTurns,
            Self::ChatTurns => Self::Voice,
            Self::Voice => Self::Files,
            Self::Files => Self::Tests,
            Self::Tests => Self::All,
        }
    }

    /// Check if an event passes this filter.
    pub(crate) fn matches(self, event: &MemoryEvent) -> bool {
        match self {
            Self::All => true,
            Self::Decisions => event.event_type == EventType::Decision,
            Self::Commands => matches!(
                event.event_type,
                EventType::CommandRun | EventType::CommandIntent
            ),
            Self::ChatTurns => event.event_type == EventType::ChatTurn,
            Self::Voice => event.event_type == EventType::VoiceTranscript,
            Self::Files => event.event_type == EventType::FileChange,
            Self::Tests => event.event_type == EventType::TestResult,
        }
    }
}

/// Number of visible event rows in the browser overlay.
pub(crate) const BROWSER_VISIBLE_ROWS: usize = 8;

/// Overlay state for browsing memory events.
#[derive(Debug)]
pub(crate) struct MemoryBrowserState {
    /// Current search query (empty = show all).
    pub(crate) search_query: String,
    /// Active event type filter.
    pub(crate) filter: MemoryFilter,
    /// Currently selected row in the visible list.
    pub(crate) selected: usize,
    /// Scroll offset for the visible window.
    pub(crate) scroll_offset: usize,
    /// Whether the detail pane is expanded for the selected event.
    pub(crate) detail_expanded: bool,
    /// Cached count of filtered results (updated on refresh).
    pub(crate) filtered_count: usize,
}

impl MemoryBrowserState {
    pub(crate) fn new() -> Self {
        Self {
            search_query: String::new(),
            filter: MemoryFilter::All,
            selected: 0,
            scroll_offset: 0,
            detail_expanded: false,
            filtered_count: 0,
        }
    }

    /// Move selection up.
    pub(crate) fn move_up(&mut self) {
        overlay_list::move_selection_up(&mut self.selected, &mut self.scroll_offset);
    }

    /// Move selection down.
    pub(crate) fn move_down(&mut self) {
        overlay_list::move_selection_down(&mut self.selected, self.filtered_count);
    }

    /// Ensure scroll offset keeps the selected item visible.
    pub(crate) fn clamp_scroll(&mut self, visible_rows: usize) {
        overlay_list::clamp_scroll(self.selected, &mut self.scroll_offset, visible_rows);
    }

    /// Cycle to the next event type filter and reset selection.
    pub(crate) fn cycle_filter(&mut self) {
        self.filter = self.filter.cycle();
        self.selected = 0;
        self.scroll_offset = 0;
    }

    /// Toggle the detail expansion pane.
    pub(crate) fn toggle_detail(&mut self) {
        self.detail_expanded = !self.detail_expanded;
    }

    /// Append a character to the search query.
    pub(crate) fn push_search_char(&mut self, ch: char) {
        self.search_query.push(ch);
        self.selected = 0;
        self.scroll_offset = 0;
    }

    /// Remove the last character from the search query.
    pub(crate) fn pop_search_char(&mut self) {
        self.search_query.pop();
        self.selected = 0;
        self.scroll_offset = 0;
    }

    /// Update the cached filtered count from a fresh query result.
    pub(crate) fn set_filtered_count(&mut self, count: usize) {
        self.filtered_count = count;
        if self.selected >= count && count > 0 {
            self.selected = count - 1;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn filter_cycle_is_complete() {
        let start = MemoryFilter::All;
        let mut f = start;
        for _ in 0..7 {
            f = f.cycle();
        }
        assert_eq!(f, MemoryFilter::All);
    }

    #[test]
    fn browser_state_navigation() {
        let mut state = MemoryBrowserState::new();
        state.set_filtered_count(5);

        state.move_down();
        assert_eq!(state.selected, 1);

        state.move_down();
        state.move_down();
        state.move_down();
        assert_eq!(state.selected, 4);

        // Cannot go past max.
        state.move_down();
        assert_eq!(state.selected, 4);

        state.move_up();
        assert_eq!(state.selected, 3);
    }

    #[test]
    fn browser_state_clamp_scroll() {
        let mut state = MemoryBrowserState::new();
        state.set_filtered_count(20);
        state.selected = 10;
        state.scroll_offset = 0;

        state.clamp_scroll(5);
        assert_eq!(state.scroll_offset, 6);
    }

    #[test]
    fn cycle_filter_resets_selection() {
        let mut state = MemoryBrowserState::new();
        state.set_filtered_count(10);
        state.selected = 5;
        state.cycle_filter();
        assert_eq!(state.selected, 0);
        assert_eq!(state.filter, MemoryFilter::Decisions);
    }

    #[test]
    fn push_pop_search_resets_selection() {
        let mut state = MemoryBrowserState::new();
        state.set_filtered_count(10);
        state.selected = 5;
        state.push_search_char('r');
        assert_eq!(state.selected, 0);
        assert_eq!(state.search_query, "r");

        state.pop_search_char();
        assert_eq!(state.search_query, "");
    }
}
