//! Shared selection helpers for Theme Studio page lists.

/// Move selection one row up, stopping at zero.
pub(crate) fn select_prev(selected: &mut usize) {
    *selected = selected.saturating_sub(1);
}

/// Move selection one row down, stopping at the last row.
pub(crate) fn select_next(selected: &mut usize, item_count: usize) {
    if item_count == 0 {
        *selected = 0;
        return;
    }
    let max = item_count.saturating_sub(1);
    if *selected < max {
        *selected += 1;
    }
}

#[cfg(test)]
mod tests {
    use super::{select_next, select_prev};

    #[test]
    fn select_prev_stops_at_zero() {
        let mut selected = 0usize;
        select_prev(&mut selected);
        assert_eq!(selected, 0);

        selected = 3;
        select_prev(&mut selected);
        assert_eq!(selected, 2);
    }

    #[test]
    fn select_next_stops_at_max() {
        let mut selected = 0usize;
        select_next(&mut selected, 3);
        assert_eq!(selected, 1);
        select_next(&mut selected, 3);
        assert_eq!(selected, 2);
        select_next(&mut selected, 3);
        assert_eq!(selected, 2);
    }

    #[test]
    fn select_next_handles_empty_lists() {
        let mut selected = 4usize;
        select_next(&mut selected, 0);
        assert_eq!(selected, 0);
    }
}
