//! Shared cyclic-index helpers for menu/button/theme navigation.

/// Compute the next index in a circular list.
#[must_use]
pub(crate) fn cycle_index(current_idx: usize, len: usize, direction: i32) -> usize {
    if len == 0 {
        return 0;
    }
    let len_i64 = i64::try_from(len).unwrap_or(1);
    let current_i64 = i64::try_from(current_idx).unwrap_or(0);
    let next_i64 = (current_i64 + i64::from(direction)).rem_euclid(len_i64);
    usize::try_from(next_i64).unwrap_or(0)
}

/// Pick the next value in a circular option list.
#[must_use]
pub(crate) fn cycle_option<T>(options: &[T], current: T, direction: i32) -> T
where
    T: Copy + PartialEq,
{
    if options.is_empty() {
        return current;
    }
    let current_idx = options
        .iter()
        .position(|item| *item == current)
        .unwrap_or(0);
    let next_idx = cycle_index(current_idx, options.len(), direction);
    options[next_idx]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cycle_index_wraps_forward_and_backward() {
        assert_eq!(cycle_index(0, 3, 1), 1);
        assert_eq!(cycle_index(2, 3, 1), 0);
        assert_eq!(cycle_index(0, 3, -1), 2);
    }

    #[test]
    fn cycle_index_handles_empty() {
        assert_eq!(cycle_index(4, 0, 1), 0);
    }

    #[test]
    fn cycle_option_uses_current_when_not_found() {
        let options = [10, 20, 30];
        assert_eq!(cycle_option(&options, 99, 1), 20);
    }
}
