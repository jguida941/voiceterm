//! Status-string sanitization so control characters never corrupt terminal output.

use unicode_width::UnicodeWidthChar;

pub(super) fn sanitize_status(text: &str) -> String {
    text.chars()
        .map(|ch| if ch.is_control() { ' ' } else { ch })
        .collect()
}

pub(super) fn status_text_display_width(text: &str) -> usize {
    text.chars()
        .map(|ch| UnicodeWidthChar::width(ch).unwrap_or(0))
        .sum()
}

pub(super) fn truncate_status(text: &str, max_display_width: usize) -> String {
    if max_display_width == 0 {
        return String::new();
    }
    let mut result = String::new();
    let mut width = 0usize;

    for ch in text.chars() {
        let ch_width = UnicodeWidthChar::width(ch).unwrap_or(0);
        if width.saturating_add(ch_width) > max_display_width {
            break;
        }
        result.push(ch);
        width = width.saturating_add(ch_width);
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn status_helpers_sanitize_and_truncate() {
        let sanitized = sanitize_status("ok\t界bad\n");
        assert_eq!(sanitized, "ok 界bad ");
        assert_eq!(sanitize_status("ok界🙂"), "ok界🙂");
        assert_eq!(status_text_display_width("abc"), 3);
        assert_eq!(status_text_display_width("界"), 2);
        assert_eq!(truncate_status("hello", 0), "");
        assert_eq!(truncate_status("hello", 2), "he");
        assert_eq!(truncate_status("A界B", 2), "A");
        assert_eq!(truncate_status("A界B", 3), "A界");
    }
}
