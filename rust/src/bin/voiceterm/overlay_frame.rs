//! Shared overlay frame helpers so help/settings/theme overlays stay consistent.

use crate::theme::{BorderSet, ThemeColors};
use unicode_width::{UnicodeWidthChar, UnicodeWidthStr};

#[must_use]
pub(crate) fn display_width(text: &str) -> usize {
    UnicodeWidthStr::width(text)
}

#[must_use]
pub(crate) fn truncate_display(text: &str, max_width: usize) -> String {
    if max_width == 0 {
        return String::new();
    }

    let mut out = String::new();
    let mut used = 0usize;
    for ch in text.chars() {
        let w = UnicodeWidthChar::width(ch).unwrap_or(0);
        if used + w > max_width {
            break;
        }
        used += w;
        out.push(ch);
    }
    out
}

#[must_use]
pub(crate) fn frame_top(colors: &ThemeColors, borders: &BorderSet, width: usize) -> String {
    frame_line(
        colors,
        borders.horizontal,
        borders.top_left,
        borders.top_right,
        width,
    )
}

#[must_use]
pub(crate) fn frame_bottom(colors: &ThemeColors, borders: &BorderSet, width: usize) -> String {
    frame_line(
        colors,
        borders.horizontal,
        borders.bottom_left,
        borders.bottom_right,
        width,
    )
}

#[must_use]
pub(crate) fn frame_separator(colors: &ThemeColors, borders: &BorderSet, width: usize) -> String {
    frame_line(
        colors,
        borders.horizontal,
        borders.t_left,
        borders.t_right,
        width,
    )
}

#[must_use]
fn frame_line(
    colors: &ThemeColors,
    horizontal: char,
    left_corner: char,
    right_corner: char,
    width: usize,
) -> String {
    let inner_width = width.saturating_sub(2);
    let inner: String = std::iter::repeat(horizontal).take(inner_width).collect();
    format!(
        "{}{}{}{}{}",
        colors.border, left_corner, inner, right_corner, colors.reset
    )
}

#[must_use]
pub(crate) fn centered_title_line(
    colors: &ThemeColors,
    borders: &BorderSet,
    title: &str,
    width: usize,
) -> String {
    let inner_width = width.saturating_sub(2);
    let title_width = display_width(title);
    let padding = inner_width.saturating_sub(title_width);
    let left_pad = padding / 2;
    let right_pad = padding - left_pad;
    format!(
        "{}{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        " ".repeat(left_pad),
        title,
        " ".repeat(right_pad),
        colors.border,
        borders.vertical,
        colors.reset
    )
}
