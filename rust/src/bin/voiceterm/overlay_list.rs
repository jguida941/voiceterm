//! Shared selection/scroll helpers for list-style overlays.

pub(crate) fn move_selection_up(selected: &mut usize, scroll_offset: &mut usize) {
    if *selected > 0 {
        *selected -= 1;
        if *selected < *scroll_offset {
            *scroll_offset = *selected;
        }
    }
}

pub(crate) fn move_selection_down(selected: &mut usize, item_count: usize) {
    let max = item_count.saturating_sub(1);
    if *selected < max {
        *selected += 1;
    }
}

pub(crate) fn clamp_scroll(selected: usize, scroll_offset: &mut usize, visible_rows: usize) {
    if visible_rows == 0 {
        return;
    }
    if selected >= *scroll_offset + visible_rows {
        *scroll_offset = selected.saturating_sub(visible_rows.saturating_sub(1));
    }
    if selected < *scroll_offset {
        *scroll_offset = selected;
    }
}
